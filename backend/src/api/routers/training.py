import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import pandas as pd
import json

from src.database.connection import get_db
from src.database.models import StrategyRun, StrategyInstance, MarketSeries, MarketBar

router = APIRouter(
    tags=["Training Service"]
)

# Should be loaded from env
TRAINING_SERVICE_URL = os.getenv("TRAINING_SERVICE_URL", "http://localhost:5000")

# --- Schemas ---
# Match Training Node Schemas
class LayerConfig(BaseModel):
    type: str # 'input', 'hidden', 'output'
    layer: Dict[str, Any]

class TrainingConfig(BaseModel):
    batch_size: int = 32
    epochs: int = 10
    gamma: float = 0.99
    tau: float = 0.005
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay_steps: int = 1000
    learning_rate: float = 0.001
    window_size: int = 10

class StartTrainingRequest(BaseModel):
    dataset_id: str
    model_architecture: List[LayerConfig]
    training_params: TrainingConfig

@router.post("/start")
async def start_training(request: StartTrainingRequest, db: Session = Depends(get_db)):
    """
    Orchestrates the training job:
    1. Fetches data for the given dataset_id from DB.
    2. Constructs the payload.
    3. Proxies to Training Node.
    """
    # 1. Fetch Dataset
    from src.database.models import Dataset
    dataset = db.query(Dataset).get(request.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    sources = dataset.sources_json
    if not sources:
        raise HTTPException(status_code=400, detail="Dataset has no sources")

    all_data = []

    # 2. Iterate Sources and Accumulate Data
    for src in sources:
        run_id = src.get("run_id")
        symbol = src.get("symbol")
        timeframe = src.get("timeframe")

        if not symbol or not timeframe:
            # Try to fetch from Run if missing in JSON (redundancy)
            run = db.query(StrategyRun).get(run_id)
            if run and run.instance:
                symbol = run.instance.symbol
                timeframe = run.instance.timeframe
        
        if not symbol or not timeframe:
            print(f"Skipping source {run_id}: Missing symbol/timeframe")
            continue

        # Find Market Series
        m_series = db.query(MarketSeries).filter(
            MarketSeries.symbol == symbol,
            MarketSeries.timeframe == timeframe
        ).first()

        if not m_series:
             # Skip or error? Warn and skip for robustness.
             print(f"Warning: Market data not found for {symbol} {timeframe}")
             continue

        # Load Bars
        # Optional: Apply time range filter if dataset supports it (future)
        stmt = db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id).order_by(MarketBar.ts_utc.asc()).statement
        df_bars = pd.read_sql(stmt, db.connection())

        if df_bars.empty:
             continue

        keep_cols = ['open', 'high', 'low', 'close', 'volume']
        # Ensure cols exist
        available_cols = [c for c in keep_cols if c in df_bars.columns]
        
        df_clean = df_bars[available_cols].copy()
        
        # Add to accumulator
        # We might want to add a 'reset' flag or similar if the env supports it, 
        # but for now we just concat.
        all_data.extend(df_clean.to_dict(orient='records'))

    if not all_data:
        raise HTTPException(status_code=400, detail="No data could be fetched for this dataset")

    # 3. Construct Proxy Payload
    # We use dataset_id as the run_id for the microservice context
    proxy_payload = {
        "run_id": request.dataset_id, 
        "model_architecture": [l.dict() for l in request.model_architecture],
        "training_params": request.training_params.dict(),
        "data": all_data 
    }
    
    # 4. Send
    async with httpx.AsyncClient() as client:
        try:
            # high timeout for large datasets
            response = await client.post(f"{TRAINING_SERVICE_URL}/train", json=proxy_payload, timeout=60.0)
            response.raise_for_status()
            
            result = response.json()
            # result contains {"job_id": "...", "status": "PENDING"}
            return result
            
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Training Service unavailable")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Training Service timeout (data too large?)")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Proxy Error: {str(e)}")

@router.get("/status/{job_id}")
async def check_status(job_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{TRAINING_SERVICE_URL}/status/{job_id}")
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Training Service unavailable")
        except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))
