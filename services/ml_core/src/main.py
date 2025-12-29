from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
import logging
from quant_shared.models.connection import init_db, get_db
from .runner import TrainingRunner

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_core")

app = FastAPI(title="ML Training Microservice")

@app.on_event("startup")
def on_startup():
    init_db()

class TrainingJobRequest(BaseModel):
    run_id: str
    config: Dict[str, Any]

@app.post("/train")
def start_training_job(job: TrainingJobRequest, background_tasks: BackgroundTasks):
    """
    Accepts a training job and runs it in background.
    """
    logger.info(f"Received training job for Run {job.run_id}")
    
    # We need a fresh session for the background thread
    db_gen = get_db()
    db = next(db_gen)
    
    runner = TrainingRunner(db)
    background_tasks.add_task(runner.start_training_run, job.run_id, job.config)
    
    return {"status": "ok", "message": "Training started"}

@app.get("/status/{run_id}")
def get_status(run_id: str):
    return {"status": "unknown", "run_id": run_id}

@app.post("/stop/{run_id}")
def stop_training(run_id: str):
    # TODO: Implement a registry of active runners to stop specific ones
    return {"status": "not_implemented"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
