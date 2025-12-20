from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import Execution
from typing import List
from pydantic import BaseModel

router = APIRouter()

class SetupStats(BaseModel):
    setup: str
    count: int
    win_rate: float
    profit_factor: float
    avg_trade: float
    total_pnl: float

@router.get("/setup-analysis", response_model=List[SetupStats])
def get_setup_analysis(strategy_id: str = "DEMO_STRAT", db: Session = Depends(get_db)):
    """
    Temporarily disabled or heavily simplified because 'setup_tag' and 'pnl_net' 
    do not exist directly on Execution. This needs a full rewrite associated 
    with the new 'Analytics' module that reconstructs trades.
    """
    return []

    # Legacy Logic commented out until 'Trades' are reconstructed:
    # trades = db.query(Trade).filter(Trade.strategy_id == strategy_id).all()
    # ...
