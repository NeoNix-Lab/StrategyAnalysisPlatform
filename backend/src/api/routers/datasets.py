from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime
import uuid
import json

from src.database.connection import get_db
from src.database.models import Dataset

router = APIRouter()

# --- Schemas ---

class UpdateDatasetRequest(BaseModel):
    feature_config: List[str]

class PreviewRequest(BaseModel):
    limit: int = 100
    offset: int = 0


class CreateDatasetRequest(BaseModel):
    name: str
    description: Optional[str] = None
    sources: List[Dict[str, Any]] # e.g. [{"run_id": "...", "start_time": "..."}]
    feature_config: Optional[List[str]] = None # List of feature columns to include

class DatasetResponse(BaseModel):
    dataset_id: str
    name: str
    description: Optional[str]
    created_utc: datetime
    sources: List[Dict[str, Any]]
    feature_config: Optional[List[str]]

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.post("/", response_model=DatasetResponse)
def create_dataset(request: CreateDatasetRequest, db: Session = Depends(get_db)):
    """Create a new dataset configuration."""
    
    # Validation usually happens here (e.g. check if runs exist), skipping for MVP
    
    new_dataset = Dataset(
        dataset_id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        sources_json=request.sources, # List of dicts automatically handled by JSON column (if configured) or needs manual json.dumps?
                                      # SQLAlchemy JSON type handles python objects directly.
        feature_config_json=request.feature_config
    )
    
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    # Map back to response
    return DatasetResponse(
        dataset_id=new_dataset.dataset_id,
        name=new_dataset.name,
        description=new_dataset.description,
        created_utc=new_dataset.created_utc,
        sources=new_dataset.sources_json,
        feature_config=new_dataset.feature_config_json
    )

@router.get("/", response_model=List[DatasetResponse])
def list_datasets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all available datasets."""
    datasets = db.query(Dataset).order_by(Dataset.created_utc.desc()).offset(skip).limit(limit).all()
    
    results = []
    for ds in datasets:
        results.append(DatasetResponse(
            dataset_id=ds.dataset_id,
            name=ds.name,
            description=ds.description,
            created_utc=ds.created_utc,
            sources=ds.sources_json or [],
            feature_config=ds.feature_config_json or []
        ))
    return results

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get a specific dataset."""
    ds = db.query(Dataset).get(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    return DatasetResponse(
        dataset_id=ds.dataset_id,
        name=ds.name,
        description=ds.description,
        created_utc=ds.created_utc,
        sources=ds.sources_json or [],
        feature_config=ds.feature_config_json or []
    )

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(Dataset).get(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    db.delete(ds)
    db.delete(ds)
    db.commit()
    return {"status": "success", "message": "Dataset deleted"}

@router.patch("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(dataset_id: str, req: UpdateDatasetRequest, db: Session = Depends(get_db)):
    ds = db.query(Dataset).get(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    ds.feature_config_json = req.feature_config
    db.commit()
    db.refresh(ds)
    
    return DatasetResponse(
        dataset_id=ds.dataset_id,
        name=ds.name,
        description=ds.description,
        created_utc=ds.created_utc,
        sources=ds.sources_json or [],
        feature_config=ds.feature_config_json or []
    )

@router.post("/{dataset_id}/preview")
def preview_dataset(dataset_id: str, req: PreviewRequest, db: Session = Depends(get_db)):
    ds = db.query(Dataset).get(dataset_id)
    if not ds: raise HTTPException(404, "Dataset not found")
    
    if not ds.sources_json or len(ds.sources_json) == 0:
        return {"columns": [], "data": []}
        
    # Use first source to sample data
    source = ds.sources_json[0]
    run_id = source.get("run_id")
    symbol = source.get("symbol")
    timeframe = source.get("timeframe")
    
    # Logic similar to bars.py but simpler for preview
    from src.database.models import RunSeries, Bar, MarketSeries, MarketBar
    
    # 1. Try RunSeries (Strategy Data)
    query = None
    model_class = None
    
    if run_id:
        series_query = db.query(RunSeries).filter(RunSeries.run_id == run_id)
        if symbol: series_query = series_query.filter(RunSeries.symbol == symbol)
        if timeframe: series_query = series_query.filter(RunSeries.timeframe == timeframe)
        series = series_query.first()
        
        if series:
            query = db.query(Bar).filter(Bar.series_id == series.series_id)
            model_class = Bar

    # 2. Try MarketSeries (Fallback)
    if not query and symbol and timeframe:
         m_series = db.query(MarketSeries).filter(
            MarketSeries.symbol == symbol,
            MarketSeries.timeframe == timeframe
        ).first()
         if m_series:
             query = db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id)
             model_class = MarketBar
             
    if not query:
        return {"columns": [], "data": [], "message": "No data found for source"}
    
    # Order by latest
    bars = query.order_by(model_class.ts_utc.desc()).offset(req.offset).limit(req.limit).all()
    
    # Format for frontend grid
    if not bars: return {"columns": [], "data": []}
    
    # Infer columns from first bar object + custom logic if needed
    # Default columns for Bar/MarketBar
    base_cols = ["ts_utc", "open", "high", "low", "close", "volume"]
    
    data = []
    for b in bars:
        row = {c: getattr(b, c) for c in base_cols}
        data.append(row)
        
    return {"columns": base_cols, "data": data}
