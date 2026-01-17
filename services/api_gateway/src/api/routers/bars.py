from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from quant_shared.models.connection import get_db
from quant_shared.models.models import RunSeries, RunSeriesBar, RunSeriesRunLink
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
    # Find the Series ID linked to this Run for the given Symbol/Timeframe
    # We join RunSeriesRunLink -> RunSeries
    
    # 1. Find the series definition
    # Note: A run might be linked to multiple series with same symbol/timeframe (e.g. different venues?)
    # For now, we take the first matching one.
    
    series = (
        db.query(RunSeries)
        .join(RunSeriesRunLink, RunSeries.series_id == RunSeriesRunLink.series_id)
        .filter(
            RunSeriesRunLink.run_id == run_id,
            RunSeries.symbol == symbol,
            RunSeries.timeframe == timeframe
        )
        .first()
    )

    if not series:
        return []

    # 2. Query Bars for that series
    query = db.query(RunSeriesBar).filter(RunSeriesBar.series_id == series.series_id)
    
    if start_utc:
        query = query.filter(RunSeriesBar.ts_utc >= start_utc)
    if end_utc:
        query = query.filter(RunSeriesBar.ts_utc <= end_utc)
        
    return query.order_by(RunSeriesBar.ts_utc.asc()).limit(limit).all()
