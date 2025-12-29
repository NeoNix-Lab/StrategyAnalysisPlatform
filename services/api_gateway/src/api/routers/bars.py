from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from quant_shared.models.connection import get_db
from quant_shared.models.models import Bar, RunSeries
from quant_shared.schemas.schemas import BarResponse 
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
    # 1. Try Run-Specific Series (Legacy/Backtest specific)
    series = db.query(RunSeries).filter(
        RunSeries.run_id == run_id,
        RunSeries.symbol == symbol,
        RunSeries.timeframe == timeframe
    ).first()

    if series:
        query = db.query(Bar).filter(Bar.series_id == series.series_id)
        if start_utc:
            query = query.filter(Bar.ts_utc >= start_utc)
        if end_utc:
            query = query.filter(Bar.ts_utc <= end_utc)
        return query.order_by(Bar.ts_utc.asc()).limit(limit).all()

    # 2. Fallback to Shared Market Data
    from quant_shared.models.models import MarketSeries, MarketBar
    
    m_series = db.query(MarketSeries).filter(
        MarketSeries.symbol == symbol,
        MarketSeries.timeframe == timeframe
    ).first()
    
    if not m_series:
        return []
        
    query = db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id)
    
    if start_utc:
        query = query.filter(MarketBar.ts_utc >= start_utc)
    if end_utc:
        query = query.filter(MarketBar.ts_utc <= end_utc)
        
    return query.order_by(MarketBar.ts_utc.asc()).limit(limit).all()
