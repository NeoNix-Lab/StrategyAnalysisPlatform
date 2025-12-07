from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.connection import get_db
from src.database.models import Strategy, StrategyRun

router = APIRouter()

# Pydantic Models
class StrategyRunResponse(BaseModel):
    run_id: str
    strategy_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    parameters: Optional[dict] = None # JSON object
    
    class Config:
        from_attributes = True

class StrategyResponse(BaseModel):
    strategy_id: str
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[StrategyResponse])
def read_strategies(db: Session = Depends(get_db)):
    strategies = db.query(Strategy).all()
    return strategies

@router.get("/{strategy_id}/runs", response_model=List[StrategyRunResponse])
def read_strategy_runs(strategy_id: str, db: Session = Depends(get_db)):
    runs = db.query(StrategyRun).filter(StrategyRun.strategy_id == strategy_id).order_by(StrategyRun.start_time.desc()).all()
    return runs
