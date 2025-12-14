from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.database.connection import get_db
from src.database.models import StrategyRun
from src.api.schemas import StrategyRunResponse

router = APIRouter()

@router.get("/{run_id}", response_model=StrategyRunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # [NEW] Calculate metrics on the fly and update DB if missing or stale
    # For now, we always recalculate to ensure freshness (can optimize later)
    from src.database.models import Execution, Order
    from src.quantlab.metrics import MetricsEngine
    
    executions = db.query(Execution).filter(Execution.run_id == run_id).all()
    orders = db.query(Order).filter(Order.run_id == run_id).all()
    
    # Use reconstruction logic
    if executions and orders:
        metrics = MetricsEngine.reconstruct_and_calculate(executions, orders)
        run.metrics_json = metrics
        db.commit() # Save computed metrics
        db.refresh(run)

    return run

@router.get("/instance/{instance_id}", response_model=List[StrategyRunResponse])
def get_runs_by_instance(instance_id: str, db: Session = Depends(get_db)):
    return db.query(StrategyRun).filter(StrategyRun.instance_id == instance_id).all()

@router.post("/{run_id}/stop", response_model=StrategyRunResponse)
def stop_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    from datetime import datetime
    from src.database.models import RunStatus
    
    run.status = RunStatus.COMPLETED
    run.end_utc = datetime.utcnow()
    
    db.commit()
    db.refresh(run)
    return run

@router.get("/{run_id}/trades", response_model=List[dict])
def get_run_trades(run_id: str, db: Session = Depends(get_db)):
    """
    Returns the list of trades for a run.
    Prioritizes persistent 'trades' table. Fallback to on-the-fly reconstruction.
    """
    from src.database.models import Execution, Order, Trade
    from src.quantlab.metrics import MetricsEngine
    
    # 1. Try fetching from DB
    db_trades = db.query(Trade).filter(Trade.run_id == run_id).all()
    if db_trades:
        # Convert to list of dicts/schema
        return [
            {
                "trade_id": t.trade_id,
                "symbol": t.symbol,
                "side": t.side.name if hasattr(t.side, 'name') else str(t.side),
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl_net": t.pnl_net,
                "quantity": t.quantity,
                "duration_seconds": t.duration_seconds
            }
            for t in db_trades
        ]
    
    # 2. Fallback: On-the-fly reconstruction
    executions = db.query(Execution).filter(Execution.run_id == run_id).all()
    orders = db.query(Order).filter(Order.run_id == run_id).all()
    
    if executions and orders:
        return MetricsEngine.reconstruct_trades(executions, orders)
    return []
