from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
from pydantic import BaseModel

from quant_shared.models.connection import get_db
from quant_shared.models.models import (
    MlTrainingSession, MlModelArchitecture, MlRewardFunction, 
    MlTrainingProcess, MlIteration
)

router = APIRouter()

class ValidateRewardRequest(BaseModel):
    code: str
    dataset_id: str
    metadata_json: Optional[Dict[str, Any]] = None

class FunctionCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    session_id: str
    name: str
    status: str
    created_utc: datetime
    
    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    name: str
    function_id: Optional[str] = None
    model_id: Optional[str] = None
    process_id: Optional[str] = None

class ModelResponse(BaseModel):
    model_id: str
    name: str
    description: Optional[str] = None
    layers_json: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True

class FunctionResponse(BaseModel):
    function_id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ProcessResponse(BaseModel):
    process_id: str
    name: str
    description: Optional[str] = None
    epochs: Optional[int] = None
    learning_rate: Optional[float] = None
    
    class Config:
        from_attributes = True

class IterationCreate(BaseModel):
    session_id: str
    dataset_id: str
    name: Optional[str] = 'Initial Run'
    split_config: Optional[dict] = None

class IterationResponse(BaseModel):
    iteration_id: str
    session_id: str
    dataset_id: str
    status: str
    
    class Config:
        from_attributes = True

# --- Endpoints: Reward Functions ---

@router.get("/functions", response_model=List[FunctionResponse])
def get_functions(db: Session = Depends(get_db)):
    return db.query(MlRewardFunction).all()

@router.get("/functions/{fid}", response_model=FunctionResponse)
def get_function(fid: str, db: Session = Depends(get_db)):
    obj = db.query(MlRewardFunction).filter(MlRewardFunction.function_id == fid).first()
    if not obj: raise HTTPException(404, "Function not found")
    return obj

@router.post("/functions", response_model=FunctionResponse)
def create_or_update_function(req: FunctionCreate, db: Session = Depends(get_db)):
    # Simple UPSERT based on name for now, or match existing
    existing = db.query(MlRewardFunction).filter(MlRewardFunction.name == req.name).first()
    if existing:
        existing.code = req.code
        existing.description = req.description
        existing.metadata_json = req.metadata_json or {}
        db.commit()
        db.refresh(existing)
        return existing
    
    new_obj = MlRewardFunction(
        function_id=str(uuid.uuid4()),
        name=req.name,
        code=req.code,
        description=req.description,
        metadata_json=req.metadata_json or {}
    )
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj

@router.post("/functions/validate")
def validate_reward(req: ValidateRewardRequest, db: Session = Depends(get_db)):
    from quant_shared.models.models import Dataset, Bar, MarketBar, RunSeries, MarketSeries
    
    # 1. Fetch Dataset & Sample Data
    ds = db.query(Dataset).filter(Dataset.dataset_id == req.dataset_id).first()
    if not ds: return {"valid": False, "error": "Dataset not found"}

    if not ds.sources_json or len(ds.sources_json) == 0:
         return {"valid": False, "error": "Dataset has no sources defined"}

    source = ds.sources_json[0]
    bar_data = None

    # Try Market Series first as it's common for generic datasets
    m_series = db.query(MarketSeries).filter(
        MarketSeries.symbol == source.get("symbol"),
        MarketSeries.timeframe == source.get("timeframe")
    ).first()
    if m_series:
         bar = db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id).order_by(MarketBar.ts_utc.desc()).first()
         if bar: bar_data = bar

    if not bar_data:
        # Fallback to Run Series
        series = db.query(RunSeries).filter(
            RunSeries.run_id == source.get("run_id"),
            RunSeries.symbol == source.get("symbol"),
            RunSeries.timeframe == source.get("timeframe")
        ).first()
        if series:
            bar = db.query(Bar).filter(Bar.series_id == series.series_id).order_by(Bar.ts_utc.desc()).first()
            if bar: bar_data = bar

    if not bar_data:
        # Final fallback: create local dummy if DB empty
        obs = {"open": 50000.0, "high": 50100.0, "low": 49900.0, "close": 50050.0, "volume": 10.5}
    else:
        obs = {
            "open": getattr(bar_data, 'open', 0),
            "high": getattr(bar_data, 'high', 0),
            "low": getattr(bar_data, 'low', 0),
            "close": getattr(bar_data, 'close', 0),
            "volume": getattr(bar_data, 'volume', 0),
        }

    # 2. Execute Code with MockEnv
    class MockEnv:
        def __init__(self, current_price, action_labels=None, status_labels=None):
            self.position = 1 # Default to LONG for testing
            self.entry_price = current_price * 0.99 
            self.qty = 1.0
            self.balance = 10000.0
            self.unrealized_pnl = (current_price - self.entry_price) * self.qty
            self.last_reward = 0.0
            
            self.data = pd.DataFrame([obs])
            self.action_labels = action_labels or ["HOLD", "BUY", "SELL"]
            self.status_labels = status_labels or ["FLAT", "LONG", "SHORT"]
            
            class Namespace: pass
            self.actions = Namespace()
            for idx, label in enumerate(self.action_labels):
                setattr(self.actions, label.upper(), idx)
            self.status = Namespace()
            for idx, label in enumerate(self.status_labels):
                setattr(self.status, label.upper(), idx)

    meta = req.metadata_json or {}
    mock_env = MockEnv(
        obs['close'], 
        action_labels=meta.get("action_labels"),
        status_labels=meta.get("status_labels")
    )
    
    local_scope = {"obs": obs, "env": mock_env}
    
    try:
        exec(req.code, {}, local_scope)
        result = None
        
        if "calculate_reward" in local_scope and callable(local_scope["calculate_reward"]):
            test_action = 1
            if hasattr(mock_env.actions, 'BUY'): test_action = mock_env.actions.BUY
            result = local_scope["calculate_reward"](mock_env, test_action)
        elif "reward" in local_scope:
            result = local_scope["reward"]
            
        if result is not None:
            return {
                "valid": True, 
                "result": float(result),
                "env_state": {"pos": mock_env.position, "pnl": mock_env.unrealized_pnl}
            }
        return {"valid": False, "error": "Code must define calculate_reward() or 'reward' variable"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

# --- Endpoints: Models, Processes, Sessions ---

@router.get("/models", response_model=List[ModelResponse])
def get_models(db: Session = Depends(get_db)):
    return db.query(MlModelArchitecture).all()

@router.get("/models/{mid}", response_model=ModelResponse)
def get_model(mid: str, db: Session = Depends(get_db)):
    obj = db.query(MlModelArchitecture).filter(MlModelArchitecture.model_id == mid).first()
    if not obj: raise HTTPException(404, "Model not found")
    return obj

@router.get("/processes", response_model=List[ProcessResponse])
def get_processes(db: Session = Depends(get_db)):
    return db.query(MlTrainingProcess).all()

@router.get("/processes/{pid}", response_model=ProcessResponse)
def get_process(pid: str, db: Session = Depends(get_db)):
    obj = db.query(MlTrainingProcess).filter(MlTrainingProcess.process_id == pid).first()
    if not obj: raise HTTPException(404, "Process not found")
    return obj

@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(db: Session = Depends(get_db)):
    return db.query(MlTrainingSession).all()

@router.get("/sessions/{sid}", response_model=SessionResponse)
def get_session(sid: str, db: Session = Depends(get_db)):
    obj = db.query(MlTrainingSession).filter(MlTrainingSession.session_id == sid).first()
    if not obj: raise HTTPException(404, "Session not found")
    return obj

@router.post("/sessions", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    new_session = MlTrainingSession(
        session_id=str(uuid.uuid4()),
        name=session.name,
        function_id=session.function_id,
        model_id=session.model_id,
        process_id=session.process_id,
        status="PLANNED"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.post("/iterations", response_model=IterationResponse)
def create_iteration(iteration: IterationCreate, db: Session = Depends(get_db)):
    new_iter = MlIteration(
        iteration_id=str(uuid.uuid4()),
        session_id=iteration.session_id,
        dataset_id=iteration.dataset_id,
        name=iteration.name,
        split_config_json=iteration.split_config,
        status="PENDING"
    )
    db.add(new_iter)
    db.commit()
    db.refresh(new_iter)
    return new_iter
