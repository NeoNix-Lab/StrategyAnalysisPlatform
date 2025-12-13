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
    return run

@router.get("/instance/{instance_id}", response_model=List[StrategyRunResponse])
def get_runs_by_instance(instance_id: str, db: Session = Depends(get_db)):
    return db.query(StrategyRun).filter(StrategyRun.instance_id == instance_id).all()
