from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from quant_shared.models.connection import get_db
from quant_shared.models.models import StrategyRun
from quant_shared.schemas.schemas import StrategyRunResponse, StartRunRequest
from quant_shared.models.models import User, Role
from src.auth import service

router = APIRouter()

@router.get("/{run_id}", response_model=StrategyRunResponse)
def get_run(
    run_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    run = db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    # [TENANCY]
    if run.instance and run.instance.user_id != current_user.user_id and current_user.role != Role.ADMIN:
         # Fallback check if instance.user_id is None (legacy)? 
         # Or check strategy.user_id? 
         # For now, strict: if instance has user_id, check it. If not, maybe allow?
         # Safer to deny if not matching.
         if run.instance.user_id is not None:
             raise HTTPException(status_code=403, detail="Not allowed")

    # [NEW] Calculate metrics on the fly using Analytics Service
    # This aggregates existing trades (fast) vs rebuilding from executions (slow)
    from quant_shared.analytics.analytics_router import AnalyticsRouter
    from quant_shared.models.models import Strategy
    
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
    # Calculate and update
    try:
        metrics = router.route_analysis(run_id=run_id, strategy_type=strategy_type)
        run.metrics_json = metrics
        db.commit()
    except Exception as e:
        print(f"⚠️ Analytics failed for run {run_id}: {e}")
        # Continue without crashing, return run with existing metrics
    
    db.refresh(run)

    return run

@router.get("/instance/{instance_id}", response_model=List[StrategyRunResponse])
def get_runs_by_instance(
    instance_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    from quant_shared.models.models import StrategyInstance
    instance = db.query(StrategyInstance).filter(StrategyInstance.instance_id == instance_id).first()
    if not instance:
        raise HTTPException(404, "Instance not found")
    if instance.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(403, "Not allowed")
        
    return db.query(StrategyRun).filter(StrategyRun.instance_id == instance_id).all()

@router.post("/{run_id}/stop", response_model=StrategyRunResponse)
def stop_run(
    run_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    run = db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.instance.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(403, "Not allowed")
    
    from datetime import datetime
    from quant_shared.models.models import RunStatus
    
    run.status = RunStatus.COMPLETED
    run.end_utc = datetime.utcnow()
    
    db.commit()
    db.refresh(run)
    return run

@router.post("/start", response_model=StrategyRunResponse)
def start_run(
    request: StartRunRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    import uuid
    from datetime import datetime
    from quant_shared.models.models import StrategyInstance, StrategyRun, Strategy, RunStatus
    
    # 1. Check Strategy Exists
    strategy = db.query(Strategy).filter(Strategy.strategy_id == request.strategy_id).first()
    if not strategy:
        # Create dummy strategy if not exists for test/mvp purposes
        strategy = Strategy(
            strategy_id=request.strategy_id,
            name=f"Auto Created {request.strategy_id}",
            version="1.0",
            parameters_json=[],
            user_id=current_user.user_id 
        )
        db.add(strategy)
        db.commit()
    
    # Tenancy Check
    if strategy.user_id and strategy.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(403, "Access to strategy denied")

    # 2. Create Instance
    instance = StrategyInstance(
        instance_id=str(uuid.uuid4()),
        strategy_id=strategy.strategy_id,
        user_id=current_user.user_id,
        parameters_json=request.parameters_json,
        symbols_json=request.symbols_json,
        status="ACTIVE"
    )
    db.add(instance)
    
    # 3. Create Run
    run = StrategyRun(
        run_id=str(uuid.uuid4()),
        instance_id=instance.instance_id,
        start_utc=datetime.utcnow(),
        status=RunStatus.RUNNING,
        initial_capital=request.initial_capital
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

@router.get("/{run_id}/trades")
def get_run_trades(
    run_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    from quant_shared.models.models import Trade
    run = db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
    if not run: raise HTTPException(404, "Run not found")
    
    if run.instance.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(403, "Not allowed")
        
    return db.query(Trade).filter(Trade.run_id == run_id).all()

@router.get("/{run_id}/series")
def get_run_series(
    run_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    from quant_shared.models.models import RunSeries, RunSeriesRunLink
    
    run = db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
    if not run: raise HTTPException(404, "Run not found")
    
    if run.instance.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(403, "Not allowed")

    series = (
        db.query(RunSeries)
        .join(RunSeriesRunLink, RunSeries.series_id == RunSeriesRunLink.series_id)
        .filter(RunSeriesRunLink.run_id == run_id)
        .all()
    )
    
    return [
        {
            "series_id": s.series_id,
            "symbol": s.symbol,
            "timeframe": s.timeframe,
            "venue": s.venue,
            "provider": s.provider,
            "start_utc": s.start_utc,
            "end_utc": s.end_utc
        }
        for s in series
    ]

