import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os

router = APIRouter(
    prefix="/training",
    tags=["Training Service"]
)

# Should be loaded from env
TRAINING_SERVICE_URL = os.getenv("TRAINING_SERVICE_URL", "http://localhost:5000")

class TrainingJob(BaseModel):
    model_name: str
    epochs: int
    learning_rate: float
    dataset_id: str

@router.post("/start")
async def start_training(job: TrainingJob):
    async with httpx.AsyncClient() as client:
        try:
            # Proxy request to Microservice
            response = await client.post(f"{TRAINING_SERVICE_URL}/train", json=job.dict())
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Training Service unavailable")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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
