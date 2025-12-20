from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

from ...database.connection import get_db
from ...database import models

router = APIRouter(prefix="/ml/studio", tags=["ml-studio"])

# --- Schemas ---

class RewardFunctionCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class ModelArchitectureCreate(BaseModel):
    name: str
    layers_json: List[Dict[str, Any]]
    description: Optional[str] = None

class TrainingProcessCreate(BaseModel):
    name: str
    gamma: float = 0.99
    tau: float = 0.005
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 0.001
    window_size: int = 10
    description: Optional[str] = None

class TrainingSessionCreate(BaseModel):
    name: str
    function_id: Optional[str]
    model_id: Optional[str]
    process_id: Optional[str]

class IterationCreate(BaseModel):
    session_id: str
    dataset_id: str
    name: Optional[str] = None
    split_config: Dict[str, float] = {"train": 0.7, "test": 0.2, "work": 0.1}

# --- Endpoints: Reward Functions ---

@router.post("/functions", response_model=Dict)
def create_function(req: RewardFunctionCreate, db: Session = Depends(get_db)):
    obj = models.MlRewardFunction(
        function_id=str(uuid.uuid4()),
        name=req.name,
        code=req.code,
        description=req.description
    )
    db.add(obj)
    db.commit()
    return {"function_id": obj.function_id, "name": obj.name}

@router.get("/functions", response_model=List[Dict])
def list_functions(db: Session = Depends(get_db)):
    funcs = db.query(models.MlRewardFunction).all()
    return [{"function_id": f.function_id, "name": f.name, "description": f.description} for f in funcs]

@router.get("/functions/{fid}")
def get_function(fid: str, db: Session = Depends(get_db)):
    obj = db.query(models.MlRewardFunction).filter(models.MlRewardFunction.function_id == fid).first()
    if not obj: raise HTTPException(404, "Function not found")
    return {"function_id": obj.function_id, "name": obj.name, "code": obj.code, "description": obj.description}

# --- Endpoints: Model Architectures ---

@router.post("/models", response_model=Dict)
def create_model(req: ModelArchitectureCreate, db: Session = Depends(get_db)):
    obj = models.MlModelArchitecture(
        model_id=str(uuid.uuid4()),
        name=req.name,
        layers_json=req.layers_json,
        description=req.description
    )
    db.add(obj)
    db.commit()
    return {"model_id": obj.model_id, "name": obj.name}

@router.get("/models", response_model=List[Dict])
def list_models(db: Session = Depends(get_db)):
    objs = db.query(models.MlModelArchitecture).all()
    return [{"model_id": m.model_id, "name": m.name, "description": m.description} for m in objs]

@router.get("/models/{mid}")
def get_model(mid: str, db: Session = Depends(get_db)):
    obj = db.query(models.MlModelArchitecture).filter(models.MlModelArchitecture.model_id == mid).first()
    if not obj: raise HTTPException(404, "Model not found")
    return {"model_id": obj.model_id, "name": obj.name, "layers_json": obj.layers_json, "description": obj.description}

# --- Endpoints: Processes ---

@router.post("/processes", response_model=Dict)
def create_process(req: TrainingProcessCreate, db: Session = Depends(get_db)):
    obj = models.MlTrainingProcess(
        process_id=str(uuid.uuid4()),
        **req.dict()
    )
    db.add(obj)
    db.commit()
    return {"process_id": obj.process_id, "name": obj.name}

@router.get("/processes", response_model=List[Dict])
def list_processes(db: Session = Depends(get_db)):
    objs = db.query(models.MlTrainingProcess).all()
    return [{"process_id": p.process_id, "name": p.name, "epochs": p.epochs, "lr": p.learning_rate} for p in objs]

@router.get("/processes/{pid}")
def get_process(pid: str, db: Session = Depends(get_db)):
    obj = db.query(models.MlTrainingProcess).filter(models.MlTrainingProcess.process_id == pid).first()
    if not obj: raise HTTPException(404, "Process not found")
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

# --- Endpoints: Sessions ---

@router.post("/sessions", response_model=Dict)
def create_session(req: TrainingSessionCreate, db: Session = Depends(get_db)):
    obj = models.MlTrainingSession(
        session_id=str(uuid.uuid4()),
        name=req.name,
        function_id=req.function_id,
        model_id=req.model_id,
        process_id=req.process_id,
        status="PLANNED"
    )
    db.add(obj)
    db.commit()
    return {"session_id": obj.session_id, "name": obj.name}

@router.get("/sessions", response_model=List[Dict])
def list_sessions(db: Session = Depends(get_db)):
    objs = db.query(models.MlTrainingSession).all()
    # Simple list, maybe expand relationships if needed
    return [{"session_id": s.session_id, "name": s.name, "status": s.status, "created_utc": s.created_utc} for s in objs]

@router.get("/sessions/{sid}")
def get_session(sid: str, db: Session = Depends(get_db)):
    obj = db.query(models.MlTrainingSession).filter(models.MlTrainingSession.session_id == sid).first()
    if not obj: raise HTTPException(404, "Session not found")
    
    return {
        "session_id": obj.session_id,
        "name": obj.name,
        "status": obj.status,
        "function": {"name": obj.function.name, "id": obj.function_id} if obj.function else None,
        "model": {"name": obj.model.name, "id": obj.model_id} if obj.model else None,
        "process": {"name": obj.process.name, "id": obj.process_id} if obj.process else None,
        "iterations": [
            {
                "iteration_id": i.iteration_id,
                "dataset_id": i.dataset_id,
                "dataset_name": i.dataset.name if i.dataset else "Unknown",
                "status": i.status,
                "created_utc": i.start_utc # Approximation
            } for i in obj.iterations
        ]
    }

# --- Endpoints: Iterations ---

@router.post("/iterations", response_model=Dict)
def create_iteration(req: IterationCreate, db: Session = Depends(get_db)):
    # Verify session and dataset exist
    sess = db.query(models.MlTrainingSession).filter(models.MlTrainingSession.session_id == req.session_id).first()
    if not sess: raise HTTPException(404, "Session not found")
    
    ds = db.query(models.Dataset).filter(models.Dataset.dataset_id == req.dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")
    
    obj = models.MlIteration(
        iteration_id=str(uuid.uuid4()),
        session_id=req.session_id,
        dataset_id=req.dataset_id,
        name=req.name or f"Iter-{sess.name}-{datetime.utcnow().strftime('%H%M')}",
        split_config_json=req.split_config,
        status="PENDING"
    )
    db.add(obj)
    db.commit()
    return {"iteration_id": obj.iteration_id, "name": obj.name, "status": obj.status}

@router.get("/iterations/{iid}/run")
def run_iteration(iid: str, db: Session = Depends(get_db)):
    """
    Trigger the actual training for an iteration.
    This effectively replaces the old /training/start endpoint logic but uses the defined entities.
    """
    iter_obj = db.query(models.MlIteration).filter(models.MlIteration.iteration_id == iid).first()
    if not iter_obj: raise HTTPException(404, "Iteration not found")
    
    session_obj = iter_obj.session
    if not session_obj.function or not session_obj.model or not session_obj.process:
         raise HTTPException(400, "Session is incomplete (missing function, model, or process)")
         
    # Here we would construct the payload and call the Training Node Microservice
    # For now, we update status to mimic start
    iter_obj.status = "RUNNING"
    iter_obj.start_utc = datetime.utcnow()
    db.commit()
    
    # TODO: Call microservice with:
    # - Architecture: session_obj.model.layers_json
    # - Hyperparams: session_obj.process.*
    # - Reward Function: session_obj.function.code
    # - Data: iter_obj.dataset_id + split_config
    
    return {"status": "RUNNING", "iteration_id": iid}

