from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from quant_shared.models.connection import get_db
from quant_shared.models.models import Strategy, StrategyInstance, User, Role
from quant_shared.schemas.schemas import StrategyResponse, StrategyInstanceResponse
from src.auth import service
from fastapi import HTTPException

router = APIRouter()

@router.get("/", response_model=List[StrategyResponse])
def read_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    query = db.query(Strategy)
    if current_user.role != Role.ADMIN:
        query = query.filter(Strategy.user_id == current_user.user_id)
    return query.all()

@router.get("/{strategy_id}", response_model=StrategyResponse)
def read_strategy(
    strategy_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    obj = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
    if not obj: raise HTTPException(404, "Strategy not found")
    if obj.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(403, "Not allowed")
    return obj

@router.get("/{strategy_id}/instances", response_model=List[StrategyInstanceResponse])
def read_strategy_instances(
    strategy_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    # Verify strategy ownership first
    strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
    if not strategy:
        raise HTTPException(404, "Strategy not found")
    if strategy.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(403, "Not allowed")
        
    return db.query(StrategyInstance).filter(StrategyInstance.strategy_id == strategy_id).all()
