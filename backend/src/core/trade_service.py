from sqlalchemy.orm import Session
from src.database.models import Trade, Execution, Order, Side, StrategyRun, StrategyInstance, MarketSeries, MarketBar
from src.quantlab.metrics import MetricsEngine
from src.quantlab.regime import RegimeDetector
import pandas as pd
import uuid

class TradeService:
    def __init__(self, db: Session):
        self.db = db

    def rebuild_trades_for_run(self, run_id: str):
        """
        Fetches all executions/orders for a run, reconstructs trades, 
        and updates the 'trades' table. 
        Note: This is a full rebuild (idempotency required).
        """
        # 1. Fetch data
        executions = self.db.query(Execution).filter(Execution.run_id == run_id).all()
        orders = self.db.query(Order).filter(Order.run_id == run_id).all()
        
        # 2. Reconstruct (using existing MetricsEngine logic)
        # Returns list of dicts
        trade_dicts = MetricsEngine.reconstruct_trades(executions, orders)
        
        # 3. Persist
        # Strategy: Delete existing trades for this run? Or Upsert?
        # For simplicity in this step: Delete all run trades and re-insert.
        self.db.query(Trade).filter(Trade.run_id == run_id).delete()
        
        # --- Pre-calculate Regime Data (Optimization) ---
        df_regime = pd.DataFrame()
        try:
            # Get Instance Info
            run_info = self.db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
            if run_info and run_info.instance_id:
                instance = self.db.query(StrategyInstance).filter(StrategyInstance.instance_id == run_info.instance_id).first()
                if instance and instance.symbol and instance.timeframe:
                    # Find Market Series
                    # We try to find a matching series. If multiple, take first. 
                    # Assuming standard provider preference isn't critical here, just need data.
                    m_series = self.db.query(MarketSeries).filter(
                        MarketSeries.symbol == instance.symbol,
                        MarketSeries.timeframe == instance.timeframe
                    ).first()
                    
                    if m_series:
                        # Load Bars
                        bars_query = self.db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id).order_by(MarketBar.ts_utc.asc())
                        df_bars = pd.read_sql(bars_query.statement, self.db.bind)
                        
                        if not df_bars.empty:
                            if 'ts_utc' in df_bars.columns:
                                df_bars['ts_utc'] = pd.to_datetime(df_bars['ts_utc'])
                            
                            df_regime = RegimeDetector.calculate_regime(df_bars)
                            if not df_regime.empty and 'ts_utc' in df_regime.columns:
                                df_regime = df_regime.sort_values('ts_utc')
        except Exception as e:
            print(f"Warning: Failed to calculate regime for run {run_id}: {e}")


        
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
        
        # 4. Trigger Analysis (New Architecture)
        from src.services.analytics import AnalyticsRouter
        from src.database.models import StrategyRun, Strategy
        
        router = AnalyticsRouter(self.db)
        
        # Fetch strategy type
        run = self.db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
        strategy_type = 'DEFAULT'
        if run and run.instance and run.instance.strategy_id:
            strategy = self.db.query(Strategy).filter(Strategy.strategy_id == run.instance.strategy_id).first()
            
            sType = getattr(strategy, 'type', None)
            if strategy and sType:
                strategy_type = sType
        
        # Calculate P0/P1 metrics
        metrics = router.route_analysis(run_id=run_id, strategy_type=strategy_type)
        
        # Update Run
        if run:
            run.metrics_json = metrics
            self.db.commit()

        # Optional: Trigger per-trade analysis (P2: MAE/MFE)
        # This could be slow for thousands of trades, so maybe only do it for recent/active ones
        # or offload to background task. For now, we'll skip or do a lightweight loop.
        # Trigger per-trade analysis (P2: MAE/MFE)
        # Use pre-collected IDs to avoid stale session objects
        for tid in trade_ids:
             router.calculate_trade_metrics(trade_id=tid, strategy_type=strategy_type)

        return len(new_trade_objs)
