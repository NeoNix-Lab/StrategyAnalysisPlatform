from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from quant_shared.models.connection import get_db
from quant_shared.models.models import Dataset
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sources_json: List[Dict[str, Any]]
    feature_config_json: Optional[List[str]] = None

class DatasetResponse(BaseModel):
    dataset_id: str
    name: str
    description: Optional[str] = None
    created_utc: datetime
    sources_json: Optional[List[Dict[str, Any]]] = None
    feature_config_json: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[DatasetResponse])
def get_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.created_utc.desc()).all()

@router.post("/", response_model=DatasetResponse)
def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    new_dataset = Dataset(
        dataset_id=str(uuid.uuid4()),
        name=dataset.name,
        description=dataset.description,
        sources_json=dataset.sources_json,
        feature_config_json=dataset.feature_config_json,
        created_utc=datetime.utcnow()
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    return new_dataset

class DatasetSampleCreate(BaseModel):
    timestamp_utc: Optional[datetime] = None
    group_id: Optional[str] = None
    step_index: Optional[int] = None
    features_json: Dict[str, Any]
    targets_json: Optional[Dict[str, Any]] = None

@router.post("/{dataset_id}/samples")
def upload_samples(dataset_id: str, samples: List[DatasetSampleCreate], db: Session = Depends(get_db)):
    """
    Bulk upload of concrete data samples.
    """
    from quant_shared.models.models import MlDatasetSample
    
    # Verify dataset exists
    ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Bulk insert
    db_samples = [
        MlDatasetSample(
            dataset_id=dataset_id,
            timestamp_utc=s.timestamp_utc,
            group_id=s.group_id,
            step_index=s.step_index,
            features_json=s.features_json,
            targets_json=s.targets_json
        ) for s in samples
    ]
    
    db.add_all(db_samples)
    db.commit()
    
    return {"status": "ok", "count": len(samples)}

@router.post("/{dataset_id}/materialize")
def materialize_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """
    Converts 'sources_json' (MarketSeries pointers) into concrete 'MlDatasetSample' rows.
    """
    from quant_shared.models.models import MlDatasetSample, MarketSeries, MarketBar
    
    ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if not ds.sources_json:
        raise HTTPException(status_code=400, detail="No sources defined")
        
    # Simple Materialization Logic: Take OHLCV from MarketBars -> Features
    count = 0
    for source in ds.sources_json:
        symbol = source.get("symbol")
        timeframe = source.get("timeframe")
        
        # Find series
        ms = db.query(MarketSeries).filter(
            MarketSeries.symbol == symbol,
            MarketSeries.timeframe == timeframe
        ).first()
        
        if ms:
            bars = db.query(MarketBar).filter(MarketBar.series_id == ms.series_id).all()
            
            # Convert to samples
            samples = []
            for i, bar in enumerate(bars):
                samples.append(MlDatasetSample(
                    dataset_id=dataset_id,
                    timestamp_utc=bar.ts_utc,
                    group_id=symbol, # Group by symbol
                    step_index=i,
                    features_json={
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume
                    }
                ))
            
            db.add_all(samples)
            count += len(samples)
            
    db.commit()
    db.commit()
    return {"status": "ok", "materialized_count": count}

class DatasetSampleResponse(BaseModel):
    sample_id: int
    timestamp_utc: Optional[datetime]
    group_id: Optional[str]
    step_index: Optional[int]
    features_json: Dict[str, Any]
    targets_json: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

@router.get("/{dataset_id}/samples", response_model=List[DatasetSampleResponse])
def get_dataset_samples(dataset_id: str, limit: int = 50, db: Session = Depends(get_db)):
    from quant_shared.models.models import MlDatasetSample
    return db.query(MlDatasetSample).filter(
        MlDatasetSample.dataset_id == dataset_id
    ).order_by(MlDatasetSample.sample_id.asc()).limit(limit).all()
