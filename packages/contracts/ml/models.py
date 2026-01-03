from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class MlRewardFunction(BaseModel):
    function_id: str
    name: str
    code: str
    description: Optional[str] = None
    created_utc: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class MlTrainingSession(BaseModel):
    session_id: str
    name: str
    function_id: Optional[str] = None
    model_id: Optional[str] = None
    process_id: Optional[str] = None
    status: str = "PLANNED"
    created_utc: datetime

class MlIteration(BaseModel):
    iteration_id: str
    session_id: str
    dataset_id: str
    name: Optional[str] = None
    split_config_json: Optional[Dict[str, Any]] = None
    status: str = "PENDING"
    metrics_json: Optional[Dict[str, Any]] = None
    model_artifact_path: Optional[str] = None
    logs_json: Optional[Dict[str, Any]] = None
    start_utc: Optional[datetime] = None
    end_utc: Optional[datetime] = None

class TrainingJobRequest(BaseModel):
    run_id: str
    config: Dict[str, Any]
