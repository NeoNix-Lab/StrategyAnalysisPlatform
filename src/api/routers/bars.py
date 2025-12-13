from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database.connection import get_db
from src.database.models import Bar, RunSeries
from src.api.schemas import BarResponse 
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[BarResponse])
def read_bars(
    run_id: str,
    symbol: str, 
    timeframe: str,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    # Find Series
    series = db.query(RunSeries).filter(
        RunSeries.run_id == run_id,
        RunSeries.symbol == symbol,
        RunSeries.timeframe == timeframe
    ).first()

    if not series:
        return []

    query = db.query(Bar).filter(Bar.series_id == series.series_id)
    
    if start_utc:
        query = query.filter(Bar.ts_utc >= start_utc)
    if end_utc:
        query = query.filter(Bar.ts_utc <= end_utc)
        
    bars = query.order_by(Bar.ts_utc.asc()).limit(limit).all()
    return bars
