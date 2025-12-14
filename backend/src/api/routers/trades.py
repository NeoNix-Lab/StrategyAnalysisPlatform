from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database.connection import get_db
from src.database.models import Trade
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Pydantic models for response
class TradeResponse(BaseModel):
    trade_id: str
    symbol: str
    side: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl_net: float
    mae: Optional[float] = None
    mfe: Optional[float] = None
    duration_seconds: Optional[float] = None
    regime_trend: Optional[str] = None
    regime_volatility: Optional[str] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def model_validate(cls, obj):
        """Custom validator to handle enum conversion"""
        if hasattr(obj, '__dict__'):
            data = obj.__dict__.copy()
            # Convert Side enum to string
            if 'side' in data and hasattr(data['side'], 'name'):
                data['side'] = data['side'].name
            return cls(**data)
        return super().model_validate(obj)

@router.get("/", response_model=List[TradeResponse])
def read_trades(
    skip: int = 0, 
    limit: int = 100, 
    strategy_id: Optional[str] = None, 
    run_id: Optional[str] = None,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Trade)
    
    if strategy_id:
        from src.database.models import StrategyRun, StrategyInstance
        query = query.join(StrategyRun, Trade.run_id == StrategyRun.run_id)\
                     .join(StrategyInstance, StrategyRun.instance_id == StrategyInstance.instance_id)\
                     .filter(StrategyInstance.strategy_id == strategy_id)
    if run_id:
        query = query.filter(Trade.run_id == run_id)
    if symbol:
        query = query.filter(Trade.symbol == symbol)
        
    trades = query.offset(skip).limit(limit).all()
    return [TradeResponse.model_validate(t) for t in trades]

@router.get("/stats")
def get_stats(strategy_id: str, run_id: Optional[str] = None, db: Session = Depends(get_db)):
    from src.services.analytics import AnalyticsRouter
    from src.database.models import Strategy
    
    router = AnalyticsRouter(db)
    
    # Determine strategy type
    strategy_type = 'DEFAULT'
    if strategy_id:
        strat = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        sType = getattr(strat, 'type', None)
        if strat and sType:
            strategy_type = sType
            
    return router.route_analysis(strategy_id=strategy_id, run_id=run_id, strategy_type=strategy_type)

@router.get("/{trade_id}", response_model=TradeResponse)
def read_trade(trade_id: str, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.trade_id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TradeResponse.model_validate(trade)
