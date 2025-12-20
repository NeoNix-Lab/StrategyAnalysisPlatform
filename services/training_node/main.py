import logging
import uuid
import sys
import os
import shutil
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import tensorflow as tf

# Ensure src is in path if needed, though relative imports should work if package is structured right.
# For simplicity with uvicorn running from services/training_node:
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.models import CustomDQNModel, LayersType
from src.core.environment import EnvFlex
from src.core.trainer import Trainer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrainingNode")

app = FastAPI(title="Training Node Service", version="1.0.0")

# --- Pydantic Models ---

class LayerConfig(BaseModel):
    type: str # 'input', 'hidden', 'output'
    layer: Dict[str, Any] # Keras config: { "type": "Dense", "params": {...} }

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

class DataPoint(BaseModel):
    # Flexible key-value pairs representing a row of data
    # In practice, receiving huge datasets via JSON is bad. 
    # Better to receive a Reference ID or URL.
    # For MVP/PoC, we accept a list of dicts.
    timestamp: int
    data: Dict[str, float]

class TrainingRequest(BaseModel):
    run_id: str
    model_architecture: List[LayerConfig]
    training_params: TrainingConfig
    data: List[Dict[str, float]] # List of rows (flat dicts)
    # In real prod, 'data' would be replaced by data_url or dataset_id

class TrainingResponse(BaseModel):
    job_id: str
    status: str

# --- In-Memory Job Store ---
jobs = {}

# --- Background Task ---

def run_training_job(job_id: str, request: TrainingRequest):
    try:
        jobs[job_id]['status'] = 'RUNNING'
        logger.info(f"Starting job {job_id}")

        # 1. Prepare Data
        df = pd.DataFrame(request.data)
        if df.empty:
            raise ValueError("Training data is empty")
        
        # Ensure we just have numeric columns for features
        # If 'timestamp' or non-numeric cols exist, drop them or handle them.
        # For this PoC, we assume all columns passed are features.
        
        # 2. Setup Environment
        # Define a simple reward function (example: change in close price relative to action)
        # In real usage, this should be configurable or injected.
        # For now, we use a default simple PnL-like reward.
        
        def default_reward_fn(obs, action):
            # obs is (window_size, features)
            # This is a stub. Real reward needs logic knowing 'Close' or 'Price' column index.
            # We assume the last column is 'close' for this simple default, or 0.
            # Or we just return random for connectivity test if we don't know the schema.
            return np.random.randn() # Placeholder

        env = EnvFlex(
            data=df,
            window_size=request.training_params.window_size,
            reward_fn=default_reward_fn,
            action_labels=['HOLD', 'BUY', 'SELL'], # Default actions
            status_labels=['FLAT', 'LONG', 'SHORT'], # Default statuses
            initial_balance=100000
        )

        # 3. Build Model
        # Convert Pydantic models to dicts
        arch_config = [l.model_dump() for l in request.model_architecture]
        
        model = CustomDQNModel(
            architecture_config=arch_config,
            input_shape=request.training_params.window_size,
            name=f"Model_{job_id}"
        )
        
        # 4. Optimizer & Loss
        optimizer = tf.keras.optimizers.Adam(learning_rate=request.training_params.learning_rate)
        loss_fn = tf.keras.losses.Huber()

        # 5. Trainer
        log_dir = os.path.join("logs", job_id)
        trainer = Trainer(
            env=env,
            main_network=model,
            optimizer=optimizer,
            loss_fn=loss_fn,
            gamma=request.training_params.gamma,
            tau=request.training_params.tau,
            epsilon_start=request.training_params.epsilon_start,
            epsilon_end=request.training_params.epsilon_end,
            epsilon_decay_steps=request.training_params.epsilon_decay_steps,
            log_dir=log_dir,
            training_name=request.run_id,
            epochs=request.training_params.epochs,
        )

        # 6. Run Training
        # We use mode='batch' or 'step'
        trainer.train(
            num_episodes=request.training_params.epochs, # Using epochs as episodes for simplicity
            batch_size=request.training_params.batch_size
        )

        jobs[job_id]['status'] = 'COMPLETED'
        jobs[job_id]['result_path'] = log_dir
        logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        jobs[job_id]['status'] = 'FAILED'
        jobs[job_id]['error'] = str(e)


# --- Endpoints ---

@app.post("/train", response_model=TrainingResponse)
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "run_id": request.run_id,
        "status": "PENDING"
    }
    
    background_tasks.add_task(run_training_job, job_id, request)
    
    return TrainingResponse(job_id=job_id, status="PENDING")

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/health")
async def health_check():
    return {"status": "ok", "tf_version": tf.__version__}
