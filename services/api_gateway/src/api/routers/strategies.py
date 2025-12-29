from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from src.database.connection import get_db
from src.database.models import Strategy, StrategyInstance
from src.api.schemas import StrategyResponse, StrategyInstanceResponse

router = APIRouter()

@router.get("/", response_model=List[StrategyResponse])
def read_strategies(db: Session = Depends(get_db)):
    return db.query(Strategy).all()

@router.get("/{strategy_id}", response_model=StrategyResponse)
def read_strategy(strategy_id: str, db: Session = Depends(get_db)):
    return db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()

@router.get("/{strategy_id}/instances", response_model=List[StrategyInstanceResponse])
def read_strategy_instances(strategy_id: str, db: Session = Depends(get_db)):
    return db.query(StrategyInstance).filter(StrategyInstance.strategy_id == strategy_id).all()
