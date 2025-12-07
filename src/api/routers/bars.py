from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database.connection import get_db
from src.database.models import Bar
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class BarResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    class Config:
        from_attributes = True

@router.get("/", response_model=List[BarResponse])
def read_bars(
    symbol: str,
    timeframe: str = "1m",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    query = db.query(Bar).filter(
        Bar.symbol == symbol,
        Bar.timeframe == timeframe
    )
    
    if start_time:
        query = query.filter(Bar.timestamp >= start_time)
    if end_time:
        query = query.filter(Bar.timestamp <= end_time)
        
    # Ordiniamo per tempo
    bars = query.order_by(Bar.timestamp.asc()).limit(limit).all()
    return bars
