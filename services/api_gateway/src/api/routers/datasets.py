from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from quant_shared.models.connection import get_db
from quant_shared.models.models import Dataset, MlDatasetSample, User, Role
from src.auth import service
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
import logging
from pathlib import Path
import tempfile
import os

import os

# Import the data converter
from src.etl.data_converter import DataConverter

router = APIRouter()

class DatasetPreviewResponse(BaseModel):
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    total_columns: int
    filename: str
    tables: Optional[List[str]] = None

@router.post("/preview-upload", response_model=DatasetPreviewResponse)
async def preview_upload_file(
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
):
    """
    Preview a file before uploading to detect columns and structure.
    If SQLite and no table selected, returns list of tables.
    """
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    converter = DataConverter()
    if file_ext not in converter.supported_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {file_ext}. Supported: {converter.supported_formats}"
        )
    
    # Parse config
    preview_config = {"limit": 5}
    if config:
        try:
            user_config = json.loads(config)
            preview_config.update(user_config)
        except json.JSONDecodeError:
            pass

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Handle SQLite Table Listing
        if file_ext in ['sql', 'sqlite', 'db']:
            # If no table specified in config, list tables
            if not preview_config.get('table_name') and not preview_config.get('query'):
                tables = converter.get_sqlite_tables(temp_file_path)
                return {
                    "columns": [],
                    "sample_rows": [],
                    "total_columns": 0,
                    "filename": file.filename,
                    "tables": tables
                }
        
        # Convert file to samples with limit
        samples_data = converter.convert_from_file(temp_file_path, preview_config)
        
        if not samples_data:
            return {
                "columns": [],
                "sample_rows": [],
                "total_columns": 0,
                "filename": file.filename
            }
            
        # Extract columns from the first sample's structure
        # We look at features_json primarily, plus timestamp and targets
        first_sample = samples_data[0]
        columns = []
        if 'timestamp_utc' in first_sample and first_sample['timestamp_utc']:
            columns.append('timestamp_utc')
        
        # Add feature keys
        if isinstance(first_sample['features_json'], dict):
            columns.extend(first_sample['features_json'].keys())
            
        # Add target keys
        if first_sample.get('targets_json') and isinstance(first_sample['targets_json'], dict):
            columns.extend(first_sample['targets_json'].keys())
            
        return {
            "columns": columns,
            "sample_rows": samples_data,
            "total_columns": len(columns),
            "filename": file.filename
        }

    except Exception as e:
        logger.error(f"Error previewing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary file
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

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

@router.get("", response_model=List[DatasetResponse])
def get_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    query = db.query(Dataset)
    if current_user.role != Role.ADMIN:
        query = query.filter(Dataset.user_id == current_user.user_id)
    return query.order_by(Dataset.created_utc.desc()).all()

@router.post("", response_model=DatasetResponse)
def create_dataset(
    dataset: DatasetCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    new_dataset = Dataset(
        dataset_id=str(uuid.uuid4()),
        name=dataset.name,
        description=dataset.description,
        sources_json=dataset.sources_json,
        feature_config_json=dataset.feature_config_json,
        created_utc=datetime.utcnow(),
        user_id=current_user.user_id
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
def upload_samples(
    dataset_id: str, 
    samples: List[DatasetSampleCreate], 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    """
    Bulk upload of concrete data samples.
    """
    from quant_shared.models.models import MlDatasetSample
    
    # Verify dataset exists
    ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if ds.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")
        
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
def materialize_dataset(
    dataset_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    """
    Converts 'sources_json' (MarketSeries pointers) into concrete 'MlDatasetSample' rows.
    """
    from quant_shared.models.models import MlDatasetSample, MarketSeries, MarketBar
    
    ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if ds.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")
        
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
def get_dataset_samples(
    dataset_id: str, 
    limit: int = 50, 
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    from quant_shared.models.models import MlDatasetSample
    
    ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if ds.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")

    return db.query(MlDatasetSample).filter(
        MlDatasetSample.dataset_id == dataset_id
    ).order_by(MlDatasetSample.sample_id.asc()).limit(limit).all()

@router.post("/{dataset_id}/upload-file")
async def upload_file_to_dataset(
    dataset_id: str,
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    """
    Upload and convert a data file (CSV, JSON, SQL) to dataset samples
    """
    # Verify dataset exists
    ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if ds.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")
    
    # Parse configuration
    conversion_config = {}
    if config:
        try:
            conversion_config = json.loads(config)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON configuration")
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    converter = DataConverter()
    if file_ext not in converter.supported_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {file_ext}. Supported: {converter.supported_formats}"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Convert file to samples
        converter = DataConverter()
        samples_data = converter.convert_from_file(temp_file_path, conversion_config)
        
        # Validate samples
        converter.validate_samples(samples_data)
        
        # Convert to database objects
        db_samples = []
        for sample_data in samples_data:
            db_sample = MlDatasetSample(
                dataset_id=dataset_id,
                timestamp_utc=sample_data.get('timestamp_utc'),
                group_id=sample_data.get('group_id'),
                step_index=sample_data.get('step_index'),
                features_json=sample_data['features_json'],
                targets_json=sample_data.get('targets_json')
            )
            db_samples.append(db_sample)
        
        # Bulk insert
        db.add_all(db_samples)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Successfully uploaded and converted {len(db_samples)} samples",
            "samples_count": len(db_samples),
            "filename": file.filename,
            "format": file_ext
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary file
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

@router.post("/upload-file-create")
async def upload_file_and_create_dataset(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(service.get_current_active_user)
):
    """
    Create a new dataset and upload file data in one operation
    """
    # Parse configuration
    conversion_config = {}
    if config:
        try:
            conversion_config = json.loads(config)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON configuration")
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    converter = DataConverter()
    if file_ext not in converter.supported_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {file_ext}. Supported: {converter.supported_formats}"
        )
    
    try:

        
        # Check if dataset exists by name (Upsert Logic)
        existing_dataset = db.query(Dataset).filter(
            Dataset.name == name,
            Dataset.user_id == current_user.user_id
        ).first()
        
        if existing_dataset:
            # Update existing
            target_dataset = existing_dataset
            if description:
                target_dataset.description = description
            
            # Update config if provided
            if conversion_config.get('feature_columns'):
                target_dataset.feature_config_json = conversion_config.get('feature_columns')
                
            # Add/Update source info (append to list)
            new_source = {"source": "file_upload", "filename": file.filename, "format": file_ext, "uploaded_at": str(datetime.utcnow())}
            if not target_dataset.sources_json:
                target_dataset.sources_json = []
            target_dataset.sources_json = list(target_dataset.sources_json) + [new_source] # Ensure list mutation
            
            dataset_action = "updated"
            # Create new
            target_dataset = Dataset(
                dataset_id=str(uuid.uuid4()),
                name=name,
                description=description,
                sources_json=[{"source": "file_upload", "filename": file.filename, "format": file_ext, "uploaded_at": str(datetime.utcnow())}],
                feature_config_json=conversion_config.get('feature_columns'),
                created_utc=datetime.utcnow(),
                user_id=current_user.user_id
            )
            db.add(target_dataset)
            dataset_action = "created"
            
        db.flush()  # Get the ID without committing
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Convert file to samples
        samples_data = converter.convert_from_file(temp_file_path, conversion_config)
        
        # Validate samples
        converter.validate_samples(samples_data)
        
        # Convert to database objects
        db_samples = []
        for sample_data in samples_data:
            db_sample = MlDatasetSample(
                dataset_id=target_dataset.dataset_id,
                timestamp_utc=sample_data.get('timestamp_utc'),
                group_id=sample_data.get('group_id'),
                step_index=sample_data.get('step_index'),
                features_json=sample_data['features_json'],
                targets_json=sample_data.get('targets_json')
            )
            db_samples.append(db_sample)
        
        # Bulk insert
        db.add_all(db_samples)
        db.commit()
        
        return {
            "status": "success",
            "dataset_id": target_dataset.dataset_id,
            "action": dataset_action,
            "message": f"Successfully {dataset_action} dataset and uploaded {len(db_samples)} samples",
            "samples_count": len(db_samples),
            "filename": file.filename,
            "format": file_ext
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating dataset from file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary file
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
