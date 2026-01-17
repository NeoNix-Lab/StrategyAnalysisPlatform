import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Shared Models
from quant_shared.models.models import (
    MlIteration, Dataset, MlDatasetSample, Strategy, StrategyInstance,
    StrategyRun, Trade, Execution, RunSeries, RunSeriesRunLink,
    Side, RunStatus, RunType, Order, OrderStatus, OrderType
)

logger = logging.getLogger(__name__)

def _safe_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value

def _parse_iso_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None

def _timeframe_to_seconds(timeframe: Optional[str]) -> Optional[int]:
    if not timeframe or not isinstance(timeframe, str):
        return None
    tf = timeframe.strip().lower()
    if len(tf) < 2:
        return None
    unit = tf[-1]
    try:
        value = int(tf[:-1])
    except ValueError:
        return None
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400
    return None

class ArtifactReconstructor:
    def __init__(self, db: Session):
        self.db = db

    def reconstruct_from_iteration(self, iteration_id: str) -> Optional[StrategyRun]:
        """
        Reads the inference history of an ML Iteration and generates a StrategyRun
        populated with Trades, Orders, and Executions.
        """
        logger.info(f"Starting reconstruction for Iteration {iteration_id}")
        
        # 1. Fetch Iteration
        iteration = self.db.query(MlIteration).filter(MlIteration.iteration_id == iteration_id).first()
        if not iteration:
            raise ValueError(f"Iteration {iteration_id} not found")
            
        if str(iteration.status).upper() != "COMPLETED":
             raise ValueError(f"Iteration {iteration_id} is not COMPLETED (Status: {iteration.status})")

        metrics = iteration.metrics_json or {}
        if isinstance(metrics, str):
            parsed = _safe_json(metrics)
            if isinstance(parsed, dict):
                metrics = parsed
            else:
                logger.warning(f"Failed to parse metrics_json for {iteration_id}")
                metrics = {}
        if not isinstance(metrics, dict):
            metrics = {}

        history_path = metrics.get("inference_history_path")
        
        if not history_path or not os.path.exists(history_path):
            raise ValueError(f"Inference history file not found at {history_path}. Metrics: {metrics}")

        # 2. Load Metadata (Dataset -> Symbol/Timeframe)
        dataset = self.db.query(Dataset).filter(Dataset.dataset_id == iteration.dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {iteration.dataset_id} not found")

        # Try to infer symbol/timeframe from sources_json or config
        sources = dataset.sources_json or []
        sources = _safe_json(sources) or sources
        if isinstance(sources, dict):
            sources = [sources]
        if not isinstance(sources, list):
            sources = []

        symbol = None
        timeframe = None
        source_run_id = None
        source_series_id = None

        first_source = next((s for s in sources if isinstance(s, dict)), None)
        if first_source:
            symbol = first_source.get("symbol") or None
            timeframe = first_source.get("timeframe") or None
            source_run_id = first_source.get("run_id") or None
            source_series_id = first_source.get("series_id") or None

        # 3. Ensure Strategy + Instance (required by StrategyRun schema)
        strategy = (
            self.db.query(Strategy)
            .filter(Strategy.name == "ML Backtest", Strategy.vendor == "ML Studio")
            .first()
        )
        if not strategy:
            strategy = Strategy(
                strategy_id=str(uuid.uuid4()),
                name="ML Backtest",
                version="1.0",
                vendor="ML Studio",
                parameters_json=[]
            )
            self.db.add(strategy)

        instance_id = f"ml_iter_{iteration_id}"
        instance = (
            self.db.query(StrategyInstance)
            .filter(StrategyInstance.instance_id == instance_id)
            .first()
        )

        instance_params = {
            "iteration_id": iteration_id,
            "session_id": iteration.session_id,
            "dataset_id": iteration.dataset_id
        }
        if iteration.split_config_json:
            instance_params["split_config"] = iteration.split_config_json

        instance_name = f"ML Iteration {iteration.name or iteration_id}"
        symbols_json = [symbol] if symbol else []

        if not instance:
            instance = StrategyInstance(
                instance_id=instance_id,
                strategy_id=strategy.strategy_id,
                instance_name=instance_name,
                parameters_json=instance_params,
                symbols_json=symbols_json,
                timeframe=timeframe
            )
            self.db.add(instance)
        else:
            instance.strategy_id = strategy.strategy_id
            instance.instance_name = instance_name
            instance.parameters_json = instance_params
            instance.symbols_json = symbols_json
            if timeframe:
                instance.timeframe = timeframe

        # 4. Create Strategy Run
        backtest_run_id = f"backtest_{iteration_id}"
        
        # Check if exists and delete (Manual Cascade)
        existing = self.db.query(StrategyRun).filter(StrategyRun.run_id == backtest_run_id).first()
        if existing:
            logger.info(f"Deleting existing backtest run {backtest_run_id}")
            # Delete related objects manually if cascade is not set in DB
            self.db.query(Trade).filter(Trade.run_id == backtest_run_id).delete()
            self.db.query(Order).filter(Order.run_id == backtest_run_id).delete()
            self.db.query(Execution).filter(Execution.run_id == backtest_run_id).delete()
            self.db.query(RunSeriesRunLink).filter(RunSeriesRunLink.run_id == backtest_run_id).delete()
            self.db.delete(existing)
            self.db.flush()

        strat_run = None
        strat_run = StrategyRun(
            run_id=backtest_run_id,
            instance_id=instance.instance_id,
            run_type=RunType.BACKTEST,
            status=RunStatus.RUNNING,
            start_utc=datetime.utcnow(), # Placeholder, will update from history
            metrics_json={
                "source_iteration": iteration_id,
                "dataset_id": iteration.dataset_id,
                "split_config": iteration.split_config_json,
                "inference_history_path": history_path
            }
        )
        self.db.add(strat_run)
        self.db.flush()

        # Link RunSeries if the dataset references one
        series_ids = set()
        if source_series_id:
            series_ids.add(source_series_id)
        if source_run_id:
            linked_series = (
                self.db.query(RunSeriesRunLink.series_id)
                .filter(RunSeriesRunLink.run_id == source_run_id)
                .all()
            )
            for (sid,) in linked_series:
                series_ids.add(sid)
        if symbol and timeframe:
            series = (
                self.db.query(RunSeries)
                .filter(RunSeries.symbol == symbol, RunSeries.timeframe == timeframe)
                .first()
            )
            if series:
                series_ids.add(series.series_id)
        for sid in series_ids:
            self.db.add(RunSeriesRunLink(series_id=sid, run_id=backtest_run_id))
        
        try:
            # 5. Load History
            with open(history_path, 'r') as f:
                history = json.load(f)
                
            if not history:
                 logger.warning("History is empty.")
                 strat_run.status = RunStatus.COMPLETED
                 strat_run.end_utc = datetime.utcnow()
                 self.db.commit()
                 return strat_run

            # 6. Process History
            open_trade = None
            trades_count = 0
            order_count = 0

            first_ts = None
            last_ts = None
            last_price = None
            prev_status = 0 # Assume 0 is Flat/Null

            has_explicit_ts = any(
                (record.get("timestamp") or record.get("ts_utc") or record.get("time"))
                for record in history
            )
            fallback_ts = None
            if not has_explicit_ts:
                try:
                    samples = (
                        self.db.query(MlDatasetSample.timestamp_utc)
                        .filter(MlDatasetSample.dataset_id == iteration.dataset_id)
                        .order_by(MlDatasetSample.sample_id.asc())
                        .all()
                    )
                    fallback_ts = [row[0] for row in samples]
                    if not any(fallback_ts):
                        fallback_ts = None
                except Exception:
                    fallback_ts = None

            base_time = iteration.start_utc or dataset.created_utc or datetime.utcnow()
            step_seconds = _timeframe_to_seconds(timeframe) or 60

            def resolve_ts(record: Dict[str, Any], index: int) -> datetime:
                ts = _parse_iso_ts(record.get("timestamp") or record.get("ts_utc") or record.get("time"))
                if ts is None and fallback_ts and index < len(fallback_ts):
                    ts = fallback_ts[index]
                if ts is None:
                    ts = base_time + timedelta(seconds=index * step_seconds)
                return ts

            def status_to_side(status_value: int) -> Side:
                if status_value == 2 or status_value < 0:
                    return Side.SELL
                return Side.BUY

            def open_position(side: Side, ts: datetime, price: float) -> None:
                nonlocal open_trade, order_count
                order_count += 1
                entry_order = Order(
                    order_id=f"{backtest_run_id}_entry_{order_count}",
                    run_id=backtest_run_id,
                    symbol=symbol or "UNKNOWN",
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=1.0,
                    price=price,
                    status=OrderStatus.FILLED,
                    submit_utc=ts,
                    update_utc=ts
                )
                self.db.add(entry_order)

                open_trade = {
                    "entry_time": ts,
                    "entry_price": price,
                    "side": side
                }

            def close_position(ts: datetime, price: float) -> None:
                nonlocal open_trade, trades_count, order_count
                if not open_trade:
                    return
                trades_count += 1
                side = open_trade["side"]
                entry_price = open_trade["entry_price"]
                entry_time = open_trade["entry_time"]
                pnl = price - entry_price if side == Side.BUY else entry_price - price

                trade = Trade(
                    trade_id=f"{backtest_run_id}_tr_{trades_count}",
                    run_id=backtest_run_id,
                    symbol=symbol or "UNKNOWN",
                    side=side,
                    entry_time=entry_time,
                    exit_time=ts,
                    entry_price=entry_price,
                    exit_price=price,
                    quantity=1.0,
                    pnl_net=pnl,
                    pnl_gross=pnl,
                    commission=0.0,
                    duration_seconds=(ts - entry_time).total_seconds()
                )
                self.db.add(trade)

                order_count += 1
                exit_order = Order(
                    order_id=f"{backtest_run_id}_exit_{order_count}",
                    run_id=backtest_run_id,
                    symbol=symbol or "UNKNOWN",
                    side=Side.SELL if side == Side.BUY else Side.BUY,
                    order_type=OrderType.MARKET,
                    quantity=1.0,
                    price=price,
                    status=OrderStatus.FILLED,
                    submit_utc=ts,
                    update_utc=ts
                )
                self.db.add(exit_order)

                open_trade = None

            for i, record in enumerate(history):
                ts = resolve_ts(record, i)
                price = record.get("price")
                if price is None:
                    continue
                try:
                    price = float(price)
                except (TypeError, ValueError):
                    continue

                status_value = record.get("position_status", record.get("status", 0))
                try:
                    status = int(status_value)
                except (TypeError, ValueError):
                    status = 0

                if first_ts is None:
                    first_ts = ts
                last_ts = ts
                last_price = price

                if status != prev_status:
                    if prev_status == 0 and status != 0:
                        open_position(status_to_side(status), ts, price)
                    elif prev_status != 0 and status == 0:
                        close_position(ts, price)
                    else:
                        # Reversal or unexpected transition: close then reopen
                        close_position(ts, price)
                        open_position(status_to_side(status), ts, price)

                prev_status = status

            if open_trade and last_ts and last_price is not None:
                close_position(last_ts, last_price)

            self.db.commit()

            # Update Run Stats
            strat_run.start_utc = first_ts or datetime.utcnow()
            strat_run.end_utc = last_ts or datetime.utcnow()
            strat_run.status = RunStatus.COMPLETED
            self.db.commit()

            logger.info(f"Reconstruction complete. Generated {trades_count} trades. Run ID: {backtest_run_id}")
            return strat_run
            
        except Exception as e:
            logger.error(f"Reconstruction failed: {e}", exc_info=True)
            if strat_run:
                strat_run.status = RunStatus.FAILED
                error_payload = strat_run.metrics_json if isinstance(strat_run.metrics_json, dict) else {}
                error_payload["reconstruction_error"] = str(e)
                strat_run.metrics_json = error_payload
                try:
                    self.db.commit()
                except:
                    self.db.rollback()
            raise
