from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
import logging
from quant_shared.models.connection import init_db, get_db
try:
    from .runner import TrainingRunner
except ImportError:
    from runner import TrainingRunner

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_core")

app = FastAPI(title="ML Training Microservice")
JOB_STATUS: Dict[str, str] = {}
RUNNERS: Dict[str, TrainingRunner] = {}

@app.on_event("startup")
def on_startup():
    init_db()
    # Configure logging to API Gateway
    from quant_shared.utils.logger import setup_remote_logging
    # Assuming API Gateway is reachable at http://localhost:8000 inside the shared network or localhost if running locally
    # Ideally this URL comes from env
    import os
    gateway_url = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
    setup_remote_logging("ml_core", gateway_url, "ml_core")
    logger.info("ML Core service started and logging remotely")

class TrainingJobRequest(BaseModel):
    run_id: str
    config: Dict[str, Any]

class LoggingConfigRequest(BaseModel):
    log_every_steps: int = 2000

@app.post("/train")
def start_training_job(job: TrainingJobRequest, background_tasks: BackgroundTasks):
    """
    Accepts a training job and runs it in background.
    """
    logger.info(f"Received training job for Run {job.run_id}")
    
    # We need a fresh session for the background thread
    db_gen = get_db()
    db = next(db_gen)
    
    def set_status(run_id: str, status: str):
        JOB_STATUS[run_id] = status

    JOB_STATUS[job.run_id] = "PENDING"
    runner = TrainingRunner(db, status_cb=set_status)
    RUNNERS[job.run_id] = runner
    background_tasks.add_task(runner.start_training_run, job.run_id, job.config)
    
    return {"status": "PENDING", "job_id": job.run_id, "message": "Training started"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/status/{run_id}")
def get_status(run_id: str):
    return {"status": JOB_STATUS.get(run_id, "unknown"), "run_id": run_id}

@app.post("/stop/{run_id}")
def stop_training(run_id: str):
    runner = RUNNERS.get(run_id)
    if runner:
        runner.stop()
    JOB_STATUS[run_id] = "CANCELLED"
    return {"status": JOB_STATUS[run_id], "run_id": run_id}

@app.post("/runs/{run_id}/logging")
def update_logging(run_id: str, config: LoggingConfigRequest):
    runner = RUNNERS.get(run_id)
    if not runner:
        raise HTTPException(404, "Run not found")
    updated = runner.set_log_every_steps(config.log_every_steps)
    return {"status": "ok", "run_id": run_id, "log_every_steps": updated}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
