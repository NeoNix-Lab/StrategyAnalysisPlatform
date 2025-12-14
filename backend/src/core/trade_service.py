from sqlalchemy.orm import Session
from src.database.models import Trade, Execution, Order, Side
from src.quantlab.metrics import MetricsEngine
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
