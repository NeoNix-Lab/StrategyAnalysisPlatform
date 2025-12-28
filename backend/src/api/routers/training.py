import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import pandas as pd
import json

from src.database.connection import get_db
from src.database.models import StrategyRun, StrategyInstance, MarketSeries, MarketBar, MlIteration, MlTrainingSession, MlTrainingProcess, MlModelArchitecture, Dataset
from src.training_node.job_manager import job_manager

router = APIRouter(
    tags=["Training Service"]
)

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
    Starts a training job using the local JobManager (Multiprocessing).
    """
    # 1. Validation
    dataset = db.query(Dataset).get(request.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 2. Create DB Records (Session, Process, Model, Iteration)
    # This replaces the need for the "Proxy Payload" since we share the DB.
    
    # 2a. Process Config
    process = MlTrainingProcess(
        process_id=f"proc_{int(pd.Timestamp.utcnow().timestamp())}",
        name=f"Process {request.dataset_id[:8]}",
        batch_size=request.training_params.batch_size,
        epochs=request.training_params.epochs,
        gamma=request.training_params.gamma,
        tau=request.training_params.tau,
        epsilon_start=request.training_params.epsilon_start,
        epsilon_end=request.training_params.epsilon_end,
        learning_rate=request.training_params.learning_rate,
        window_size=request.training_params.window_size
    )
    db.add(process)
    
    # 2b. Model Architecture
    model = MlModelArchitecture(
        model_id=f"arch_{int(pd.Timestamp.utcnow().timestamp())}",
        name="Custom Arch",
        layers_json=[l.dict() for l in request.model_architecture]
    )
    db.add(model)
    
    # 2c. Session
    session = MlTrainingSession(
        session_id=f"sess_{int(pd.Timestamp.utcnow().timestamp())}",
        name=f"Session {pd.Timestamp.utcnow()}",
        model=model,
        process=process,
        status="ACTIVE"
    )
    db.add(session)
    
    # 2d. Iteration (The actual run)
    iteration_id = f"iter_{int(pd.Timestamp.utcnow().timestamp())}"
    iteration = MlIteration(
        iteration_id=iteration_id,
        session=session,
        dataset_id=dataset.dataset_id,
        name="Iteration 1",
        status="PENDING",
        split_config_json={"train_ratio": 0.8}, # Default
        start_utc=pd.Timestamp.utcnow()
    )
    db.add(iteration)
    db.commit()
    
    # 3. Start Job via Manager
    try:
        pid = job_manager.start_job(iteration_id)
        return {"job_id": iteration_id, "pid": pid, "status": "PENDING"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def check_status(job_id: str, db: Session = Depends(get_db)):
    # Check DB first for truth
    iteration = db.query(MlIteration).get(job_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Check Process Manager for liveness
    manager_status = job_manager.get_job_status(job_id)
    
    # If DB says RUNNING but Manager says STOPPED, it might have crashed without updating DB
    # or it finished very quickly.
    # We trust DB status if it's COMPLETED or FAILED.
    # If DB is RUNNING and Manager is STOPPED, we might need to flag it? 
    # For now strict return.
    
    return {
        "job_id": job_id,
        "status": iteration.status,
        "process_status": manager_status,
        "metrics": iteration.metrics_json,
        "logs": [] # Frontend uses file polling usually, or we could tail memory logs
    }

@router.post("/stop/{job_id}")
async def stop_training(job_id: str, db: Session = Depends(get_db)):
    # 1. Check DB
    iteration = db.query(MlIteration).get(job_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # 2. Update DB to help runner exit gracefully
    iteration.status = "CANCELLING"
    db.commit()
    
    # 3. Force Kill via Manager
    was_running = job_manager.stop_job(job_id)
    
    return {"status": "CANCELED", "was_running": was_running}

