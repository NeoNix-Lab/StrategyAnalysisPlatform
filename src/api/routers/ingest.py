from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
import shutil
import os
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.connection import SessionLocal, get_db
from src.etl.import_sqlite import SqliteImporter
from src.api.schemas import BarCreate, OrderCreate, ExecutionCreate
from src.database.models import Bar, Order, Execution
from src.core.trade_builder import TradeBuilder

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class StreamData(BaseModel):
    bars: List[BarCreate] = []
    orders: List[OrderCreate] = []
    executions: List[ExecutionCreate] = []

def process_sqlite_import(file_path: str):
    """
    Background task to process the imported SQLite file.
    """
    logger.info(f"Starting background import for {file_path}")
    db = SessionLocal()
    try:
        importer = SqliteImporter(db)
        affected = importer.import_file(file_path)
        logger.info(f"Background import finished for {file_path}")
        
        if affected:
            logger.info(f"Triggering trade reconstruction for {len(affected)} strategies...")
            builder = TradeBuilder(db)
            for strategy_id, symbol in affected:
                builder.reconstruct_trades(strategy_id, symbol)
            logger.info("Trade reconstruction completed.")
        
        # Optional: Move to processed folder or delete
        # os.remove(file_path) 
    except Exception as e:
        logger.error(f"Background import failed for {file_path}: {e}")
    finally:
        db.close()

@router.post("/upload")
async def upload_sqlite_export(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a SQLite export file from the strategy and trigger background ingestion.
    """
    if not file.filename.endswith(".sqlite") and not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Invalid file extension. Expected .sqlite or .db")

    # Generate a unique filename to avoid collisions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Trigger background task
    background_tasks.add_task(process_sqlite_import, file_path)

    return {
        "status": "accepted", 
        "message": "File uploaded successfully. Import started in background.",
        "filename": safe_filename
    }

@router.post("/stream")
async def stream_ingest(data: StreamData, db: Session = Depends(get_db)):
    """
    Real-time data ingestion endpoint.
    Accepts a batch of bars, orders, and executions.
    """
    try:
        # Process Bars
        for b in data.bars:
            # Convert Pydantic model to dict, handling any necessary conversions
            # Note: models.Bar expects datetime objects which Pydantic provides
            db_bar = Bar(**b.dict())
            db.merge(db_bar)
        
        # Process Orders
        for o in data.orders:
            # We need to map string enums to SQLAlchemy Enums if not handled automatically
            # Pydantic sends strings. SQLAlchemy Enum(Side) might expect strings or objects.
            # Usually SQLAlchemy handles string -> Enum mapping if configured.
            # Let's assume it works or we might need explicit mapping.
            # Given models.py uses Enum(Side), passing the enum member or string usually works.
            # But let's be safe: b.dict() returns values.
            
            # Since we defined Pydantic Enums as str, they are strings.
            # SQLAlchemy Enum usually works with strings if validate_strings=True (default).
            db_order = Order(**o.dict())
            db.merge(db_order)
            
        # Process Executions
        for e in data.executions:
            db_exec = Execution(**e.dict())
            db.merge(db_exec)
            
        db.commit()
        return {"status": "ok", "processed": {
            "bars": len(data.bars),
            "orders": len(data.orders),
            "executions": len(data.executions)
        }}
    except Exception as e:
        db.rollback()
        logger.error(f"Stream ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
