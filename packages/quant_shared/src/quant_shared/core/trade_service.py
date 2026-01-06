from sqlalchemy.orm import Session
from quant_shared.models.models import Trade, Execution, Order, Side
# Local imports inside methods to assume no circular deps
from quant_shared.quantlab.metrics import MetricsEngine
from quant_shared.quantlab.regime import RegimeDetector
import pandas as pd
import uuid

from quant_shared.utils.logger import get_logger

logger = get_logger(__name__)

class TradeService:
    def __init__(self, db: Session):
        self.db = db

    def _get_regime_df(self, run_id: str) -> pd.DataFrame:
        """
        Helper to fetch market data and calculate regime for a run.
        """
        try:
            from quant_shared.models.models import StrategyRun, StrategyInstance, RunSeries, RunSeriesRunLink, RunSeriesBar
            
            # Use get() for primary key
            run = self.db.query(StrategyRun).get(run_id)
            if not run or not run.instance_id:
                return pd.DataFrame()

            # Access via relationship or query
            instance = run.instance
            if not instance:
                 instance = self.db.query(StrategyInstance).get(run.instance_id)

            if not instance:
                return pd.DataFrame()

            symbol = getattr(instance, 'symbol', None)
            if not symbol:
                symbols_list = getattr(instance, 'symbols_json', None)
                if symbols_list and isinstance(symbols_list, list):
                    symbol = symbols_list[0]
                elif symbols_list:
                    symbol = symbols_list

            timeframe = instance.timeframe

            if not symbol or not timeframe:
                return pd.DataFrame()

            series = (
                self.db.query(RunSeries)
                .join(RunSeriesRunLink, RunSeries.series_id == RunSeriesRunLink.series_id)
                .filter(
                    RunSeriesRunLink.run_id == run_id,
                    RunSeries.symbol == symbol,
                    RunSeries.timeframe == timeframe,
                )
                .first()
            )

            if not series:
                return pd.DataFrame()
            
            # Load Bars
            # Use statement and connection for pandas
            stmt = self.db.query(RunSeriesBar).filter(RunSeriesBar.series_id == series.series_id).order_by(RunSeriesBar.ts_utc.asc()).statement
            df_bars = pd.read_sql(stmt, self.db.connection())
            
            if df_bars.empty:
                return pd.DataFrame()

            if 'ts_utc' in df_bars.columns:
                df_bars['ts_utc'] = pd.to_datetime(df_bars['ts_utc'])
            
            df_regime = RegimeDetector.calculate_regime(df_bars)
            if not df_regime.empty and 'ts_utc' in df_regime.columns:
                return df_regime.sort_values('ts_utc')

            return pd.DataFrame()

        except Exception:
            logger.warning(f"Failed to calculate regime for run {run_id}", exc_info=True)
            return pd.DataFrame()

    def rebuild_trades_for_run(self, run_id: str):
        """
        Fetches all executions/orders for a run, reconstructs trades, 
        and updates the 'trades' table. 
        Note: This is a full rebuild (idempotency required).
        """
        # 1. Fetch data
        execution_query = self.db.query(Execution).filter(Execution.run_id == run_id)
        order_query = self.db.query(Order).filter(Order.run_id == run_id)
        executions = execution_query.all()
        orders = order_query.all()
        logger.info(f"Rebuilding trades for run {run_id}")
        logger.debug(f"Run {run_id} - executions={len(executions)} orders={len(orders)}")
        
        # 2. Reconstruct (using existing MetricsEngine logic)
        # Returns list of dicts
        trade_dicts = MetricsEngine.reconstruct_trades(executions, orders)
        if not trade_dicts:
            logger.warning(f"No trades reconstructed for run {run_id} (executions={len(executions)}, orders={len(orders)})")
            return 0
        # 3. Persist
        # Strategy: Delete existing trades for this run? Or Upsert?
        # For simplicity in this step: Delete all run trades and re-insert.
        self.db.query(Trade).filter(Trade.run_id == run_id).delete()
        
        # --- Pre-calculate Regime Data (Optimization) ---
        df_regime = self._get_regime_df(run_id)
        
        new_trade_objs = []
        for t_dict in trade_dicts:
            # t_dict has: 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'quantity', 
            # 'pnl_net', 'pnl_gross', 'side', 'commission', 'duration_seconds'
            
            # Map Side string/enum
            side_val = t_dict.get('side')
            if isinstance(side_val, str):
                side_enum = Side[side_val] 
            else:
                side_enum = side_val

            # Regime Lookup
            r_trend = None
            r_vol = None
            if not df_regime.empty and 'ts_utc' in df_regime.columns:
                try:
                    # Find index where bar_time <= entry_time
                    # searchsorted returns index where item should be inserted to maintain order. 
                    # side='right' -> > entry_time. subtract 1 to get <= entry_time.
                    idx = df_regime['ts_utc'].searchsorted(t_dict['entry_time'], side='right') - 1
                    if idx >= 0:
                        regime_row = df_regime.iloc[idx]
                        # Check if timestamp is reasonably close? (e.g. within timeframe * 2)
                        # For now assume if it's the latest bar before entry, it's valid context.
                        r_trend = regime_row.get('regime_trend')
                        r_vol = regime_row.get('regime_volatility')
                except Exception:
                    pass

            trade = Trade(
                trade_id=str(uuid.uuid4()),
                run_id=run_id,
                symbol=t_dict.get('symbol', 'UNKNOWN'), # MetricsEngine logic needs to ensure symbol is present
                side=side_enum,
                entry_time=t_dict['entry_time'],
                exit_time=t_dict['exit_time'],
                entry_price=t_dict['entry_price'],
                exit_price=t_dict['exit_price'],
                quantity=t_dict['quantity'],
                pnl_net=t_dict['pnl_net'],
                pnl_gross=t_dict.get('pnl_gross', 0.0),
                commission=t_dict.get('commission', 0.0),
                duration_seconds=t_dict.get('duration_seconds', 0.0),
                regime_trend=r_trend,
                regime_volatility=r_vol,
                extra_json={}
            )
            new_trade_objs.append(trade)
            
        # Collect IDs before commit to ensure we have them
        trade_ids = [t.trade_id for t in new_trade_objs]
        
        self.db.add_all(new_trade_objs)
        self.db.commit()
        logger.info(f"Stored {len(new_trade_objs)} trade records for run {run_id}")
        
        analytics_router = None
        strategy_type = 'DEFAULT'
        try:
            from quant_shared.analytics.analytics_router import AnalyticsRouter
            from quant_shared.models.models import StrategyRun, Strategy
            
            analytics_router = AnalyticsRouter(self.db)
            
            # Fetch strategy type
            run = self.db.query(StrategyRun).get(run_id)
            if run and run.instance:
                associated_strategy = run.instance.strategy
                s_type = getattr(associated_strategy, 'type', None)
                if s_type:
                    strategy_type = s_type
            
            metrics = analytics_router.route_analysis(run_id=run_id, strategy_type=strategy_type)
            
            if run:
                run.metrics_json = metrics
                self.db.commit()
        except Exception as e:
            logger.warning(f"Analysis failed during rebuild for run {run_id}: {e}", exc_info=True)



        if analytics_router and trade_ids:
            for tid in trade_ids:
                try:
                    analytics_router.calculate_trade_metrics(trade_id=tid, strategy_type=strategy_type)
                except Exception:
                    pass

        return len(new_trade_objs)

    def count_trades_for_run(self, run_id: str) -> int:
        return self.db.query(Trade).filter(Trade.run_id == run_id).count()

    def ensure_regime_tags(self, run_id: str) -> int:
        trades = self.db.query(Trade).filter(Trade.run_id == run_id).all()
        if not trades:
            return 0

        missing = [t for t in trades if not t.regime_trend or not t.regime_volatility]
        logger.debug(f"Run {run_id} has {len(trades)} trades and {len(missing)} missing regime tags")
        if not missing:
            return 0

        df_regime = self._get_regime_df(run_id)
        if df_regime.empty or 'ts_utc' not in df_regime.columns:
            logger.warning(f"Run {run_id} missing regime data to tag {len(missing)} trades")
            return 0

        df_regime = df_regime.sort_values('ts_utc')
        updates = 0
        for trade in missing:
            subset = df_regime[df_regime['ts_utc'] <= trade.entry_time]
            if subset.empty:
                continue

            regime_row = subset.iloc[-1]
            r_trend = regime_row.get('regime_trend')
            r_vol = regime_row.get('regime_volatility')

            updated = False
            if r_trend and not trade.regime_trend:
                trade.regime_trend = r_trend
                updated = True
            if r_vol and not trade.regime_volatility:
                trade.regime_volatility = r_vol
                updated = True
            if updated:
                updates += 1

        if updates > 0:
            self.db.commit()

        return updates

