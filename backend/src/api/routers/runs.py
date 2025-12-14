from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.database.connection import get_db
from src.database.models import StrategyRun
from src.api.schemas import StrategyRunResponse, StartRunRequest

router = APIRouter()

@router.get("/{run_id}", response_model=StrategyRunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # [NEW] Calculate metrics on the fly using Analytics Service
    # This aggregates existing trades (fast) vs rebuilding from executions (slow)
    from src.services.analytics import AnalyticsRouter
    from src.database.models import Strategy
    
    router = AnalyticsRouter(db)
    
    # Determine strategy type
    strategy_type = 'DEFAULT'
    if run.instance and run.instance.strategy_id:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == run.instance.strategy_id).first()
        # Use getattr to be safe if 'type' column is missing in DB/Model
        sType = getattr(strategy, 'type', None)
        if strategy and sType:
            strategy_type = sType
            
    # Calculate and update
    metrics = router.route_analysis(run_id=run_id, strategy_type=strategy_type)
    run.metrics_json = metrics
    db.commit()
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

@router.post("/start", response_model=StrategyRunResponse)
def start_run(request: StartRunRequest, db: Session = Depends(get_db)):
    import uuid
    from datetime import datetime
    from src.database.models import StrategyInstance, StrategyRun, Strategy
    
    # 1. Check Strategy Exists
    strategy = db.query(Strategy).filter(Strategy.strategy_id == request.strategy_id).first()
    if not strategy:
        # Create dummy strategy if not exists for test/mvp purposes
        # Or raise error. Given "TEST_STRAT_INTEGRATION", likely need to create it.
        strategy = Strategy(
            strategy_id=request.strategy_id, 
            name=f"Auto Created {request.strategy_id}", 
            version="1.0"
        )
        db.add(strategy)
        db.flush()
        
    # 2. Create Instance
    instance_id = str(uuid.uuid4())
    # Extract symbol/timeframe from data_range if present
    symbol = request.data_range.get("symbol") if request.data_range else None
    timeframe = request.data_range.get("timeframe") if request.data_range else None
    
    instance = StrategyInstance(
        instance_id=instance_id,
        strategy_id=request.strategy_id,
        instance_name=f"Run {datetime.utcnow().isoformat()}",
        parameters_json=request.parameters,
        symbol=symbol,
        timeframe=timeframe
    )
    db.add(instance)
    
    # 3. Create Run
    run_id = str(uuid.uuid4())
    run = StrategyRun(
        run_id=run_id,
        instance_id=instance_id,
        run_type=request.run_type,
        start_utc=datetime.utcnow()
    )
    db.add(run)
    
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
