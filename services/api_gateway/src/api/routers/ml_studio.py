from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import ast
import os
import httpx
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, validator
from api.log_store import get_logs
import logging

from quant_shared.models.connection import get_db
from quant_shared.models.models import (
    MlTrainingSession, MlModelArchitecture, MlRewardFunction, 
    MlTrainingProcess, MlIteration
)

router = APIRouter()
logger = logging.getLogger("ml_studio")

def _format_dataset_name(dataset: Optional[Any]) -> str:
    if not dataset:
        return "Unknown Dataset"
    symbol = getattr(dataset, "symbol", None)
    timeframe = getattr(dataset, "timeframe", None)
    if not symbol or not timeframe:
        sources = dataset.sources_json if hasattr(dataset, "sources_json") else None
        if isinstance(sources, list) and sources:
            source = sources[0] if isinstance(sources[0], dict) else {}
            symbol = symbol or source.get("symbol")
            timeframe = timeframe or source.get("timeframe")
    if symbol and timeframe:
        return f"{dataset.name} ({symbol} {timeframe})"
    return dataset.name

class ValidateRewardRequest(BaseModel):
    code: str
    dataset_id: str
    metadata_json: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    model_id: str
    name: str
    description: Optional[str] = None
    layers_json: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True

class ModelCreate(BaseModel):
    name: str
    layers_json: Optional[Any] = None
    description: Optional[str] = None

class FunctionResponse(BaseModel):
    function_id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    
    @validator('metadata_json', pre=True)
    def validate_metadata(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return {}
        return v
    
    class Config:
        from_attributes = True

class FunctionCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class ProcessResponse(BaseModel):
    process_id: str
    name: str
    description: Optional[str] = None
    epochs: Optional[int] = None
    learning_rate: Optional[float] = None
    batch_size: Optional[int] = None
    window_size: Optional[int] = None
    epsilon_start: Optional[float] = None
    epsilon_end: Optional[float] = None
    epsilon_decay: Optional[float] = None
    gamma: Optional[float] = None
    tau: Optional[float] = None
    optimizer: Optional[str] = None
    loss: Optional[str] = None
    fees: Optional[float] = None
    
    class Config:
        from_attributes = True

class ProcessCreate(BaseModel):
    name: str
    description: Optional[str] = None
    gamma: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tau: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    epsilon_start: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    epsilon_end: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    epsilon_decay: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    epochs: Optional[int] = Field(default=None, gt=0)
    batch_size: Optional[int] = Field(default=None, gt=0)
    learning_rate: Optional[float] = Field(default=None, gt=0.0)
    window_size: Optional[int] = Field(default=None, gt=0)
    optimizer: Optional[str] = "Adam"
    loss: Optional[str] = "huber"
    fees: Optional[float] = Field(default=0.0, ge=0.0)

class SessionResponse(BaseModel):
    session_id: str
    name: str
    status: str
    created_utc: datetime
    
    # Relationships
    model_id: Optional[str] = None
    process_id: Optional[str] = None
    function_id: Optional[str] = None
    
    model: Optional[ModelResponse] = None
    process: Optional[ProcessResponse] = None
    function: Optional[FunctionResponse] = None
    iterations: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    name: str
    function_id: Optional[str] = None
    model_id: Optional[str] = None
    process_id: Optional[str] = None

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

class IterationLoggingConfig(BaseModel):
    log_every_steps: int = 2000


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
    from quant_shared.models.models import Dataset, RunSeries, RunSeriesBar, RunSeriesRunLink, MlDatasetSample

    def parse_json_like(value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                try:
                    return ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    return None
        return value

    def normalize_sources(raw_sources: Any) -> Optional[List[Dict[str, Any]]]:
        if raw_sources is None:
            return None
        sources = parse_json_like(raw_sources)
        if isinstance(sources, dict):
            sources = [sources]
        if not isinstance(sources, list):
            return None
        normalized = [s for s in sources if isinstance(s, dict)]
        return normalized or None

    def pick_price(obs: Dict[str, Any]) -> float:
        for key in ("close", "Price", "price"):
            val = obs.get(key)
            if isinstance(val, (int, float)):
                return float(val)
        for val in obs.values():
            if isinstance(val, (int, float)):
                return float(val)
        return 1.0

    try:
        # 1. Fetch Dataset & Sample Data
        ds = db.query(Dataset).filter(Dataset.dataset_id == req.dataset_id).first()
        if not ds:
            return {"valid": False, "error": "Dataset not found"}

        sources = normalize_sources(ds.sources_json)
        if not sources:
            return {"valid": False, "error": "Dataset has no valid sources defined"}

        source = sources[0]
        obs = None

        sample = db.query(MlDatasetSample).filter(
            MlDatasetSample.dataset_id == req.dataset_id
        ).order_by(MlDatasetSample.sample_id.desc()).first()
        if sample:
            parsed_features = parse_json_like(sample.features_json)
            if isinstance(parsed_features, dict):
                obs = parsed_features

        if obs is None:
            bar_data = None
            series_query = db.query(RunSeries).filter(
                RunSeries.symbol == source.get("symbol"),
                RunSeries.timeframe == source.get("timeframe")
            )
            if source.get("run_id"):
                series_query = series_query.join(RunSeriesRunLink).filter(
                    RunSeriesRunLink.run_id == source.get("run_id")
                )
            series = series_query.first()
            if series:
                bar = db.query(RunSeriesBar).filter(
                    RunSeriesBar.series_id == series.series_id
                ).order_by(RunSeriesBar.ts_utc.desc()).first()
                if bar:
                    bar_data = bar

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
            pick_price(obs),
            action_labels=meta.get("action_labels"),
            status_labels=meta.get("status_labels")
        )

        local_scope = {"obs": obs, "env": mock_env}

        try:
            exec(req.code, {}, local_scope)
            result = None

            if "calculate_reward" in local_scope and callable(local_scope["calculate_reward"]):
                test_action = 1
                if hasattr(mock_env.actions, 'BUY'):
                    test_action = mock_env.actions.BUY
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
    except Exception as e:
        return {"valid": False, "error": f"Validation error: {e}"}

# --- Endpoints: Models, Processes, Sessions ---

@router.get("/models", response_model=List[ModelResponse])
def get_models(db: Session = Depends(get_db)):
    return db.query(MlModelArchitecture).all()

@router.get("/models/{mid}", response_model=ModelResponse)
def get_model(mid: str, db: Session = Depends(get_db)):
    obj = db.query(MlModelArchitecture).filter(MlModelArchitecture.model_id == mid).first()
    if not obj: raise HTTPException(404, "Model not found")
    return obj

@router.post("/models", response_model=ModelResponse)
def create_or_update_model(req: ModelCreate, db: Session = Depends(get_db)):
    layers = req.layers_json
    if isinstance(layers, str):
        try:
            layers = json.loads(layers)
        except json.JSONDecodeError:
            try:
                layers = ast.literal_eval(layers)
            except (ValueError, SyntaxError):
                layers = None
    if layers is not None and not isinstance(layers, list):
        raise HTTPException(400, "layers_json must be a list of layer configs")

    existing = db.query(MlModelArchitecture).filter(MlModelArchitecture.name == req.name).first()
    if existing:
        existing.layers_json = layers or []
        existing.description = req.description
        db.commit()
        db.refresh(existing)
        return existing

    new_obj = MlModelArchitecture(
        model_id=str(uuid.uuid4()),
        name=req.name,
        layers_json=layers or [],
        description=req.description
    )
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj

@router.get("/processes", response_model=List[ProcessResponse])
def get_processes(db: Session = Depends(get_db)):
    return db.query(MlTrainingProcess).all()

@router.get("/processes/{pid}", response_model=ProcessResponse)
def get_process(pid: str, db: Session = Depends(get_db)):
    obj = db.query(MlTrainingProcess).filter(MlTrainingProcess.process_id == pid).first()
    if not obj: raise HTTPException(404, "Process not found")
    return obj

@router.post("/processes", response_model=ProcessResponse)
def create_or_update_process(req: ProcessCreate, db: Session = Depends(get_db)):
    existing = db.query(MlTrainingProcess).filter(MlTrainingProcess.name == req.name).first()
    if existing:
        for field, value in req.dict(exclude_unset=True).items():
            if field == "name":
                continue
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    new_obj = MlTrainingProcess(
        process_id=str(uuid.uuid4()),
        name=req.name,
        description=req.description,
        gamma=req.gamma,
        tau=req.tau,
        epsilon_start=req.epsilon_start,
        epsilon_end=req.epsilon_end,
        epsilon_decay=req.epsilon_decay,
        epochs=req.epochs,
        batch_size=req.batch_size,
        learning_rate=req.learning_rate,
        window_size=req.window_size,
        optimizer=req.optimizer,
        loss=req.loss,
        fees=req.fees
    )
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj

@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(db: Session = Depends(get_db)):
    from quant_shared.models.models import Dataset

    sessions = db.query(MlTrainingSession).all()
    response_items = []
    for obj in sessions:
        iterations_data = []
        if obj.iterations:
            for iteration in obj.iterations:
                dataset = db.query(Dataset).filter(Dataset.dataset_id == iteration.dataset_id).first()
                iterations_data.append({
                    "iteration_id": iteration.iteration_id,
                    "dataset_id": iteration.dataset_id,
                    "dataset_name": _format_dataset_name(dataset),
                    "name": iteration.name,
                    "status": iteration.status,
                    "start_utc": iteration.start_utc,
                    "end_utc": iteration.end_utc,
                    "metrics_json": iteration.metrics_json,
                    "split_config_json": iteration.split_config_json
                })

        response_items.append({
            "session_id": obj.session_id,
            "name": obj.name,
            "status": obj.status,
            "created_utc": obj.created_utc,
            "model_id": obj.model_id,
            "process_id": obj.process_id,
            "function_id": obj.function_id,
            "model": obj.model,
            "process": obj.process,
            "function": obj.function,
            "iterations": iterations_data
        })

    return response_items

@router.get("/sessions/{sid}", response_model=SessionResponse)
def get_session(sid: str, db: Session = Depends(get_db)):
    from quant_shared.models.models import Dataset
    
    obj = db.query(MlTrainingSession).filter(MlTrainingSession.session_id == sid).first()
    if not obj: raise HTTPException(404, "Session not found")
    
    # Get iterations with dataset names
    iterations_data = []
    if obj.iterations:
        for iteration in obj.iterations:
                dataset = db.query(Dataset).filter(Dataset.dataset_id == iteration.dataset_id).first()
                iterations_data.append({
                    "iteration_id": iteration.iteration_id,
                    "dataset_id": iteration.dataset_id,
                    "dataset_name": _format_dataset_name(dataset),
                    "name": iteration.name,
                    "status": iteration.status,
                    "start_utc": iteration.start_utc,
                    "end_utc": iteration.end_utc,
                "metrics_json": iteration.metrics_json,
                "split_config_json": iteration.split_config_json
            })
    
    # Convert to dict and add iterations
    response_dict = {
        "session_id": obj.session_id,
        "name": obj.name,
        "status": obj.status,
        "created_utc": obj.created_utc,
        "model_id": obj.model_id,
        "process_id": obj.process_id,
        "function_id": obj.function_id,
        "model": obj.model,
        "process": obj.process,
        "function": obj.function,
        "iterations": iterations_data
    }
    
    return response_dict

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

@router.get("/iterations/{iid}", response_model=IterationResponse)
def get_iteration(iid: str, db: Session = Depends(get_db)):
    obj = db.query(MlIteration).filter(MlIteration.iteration_id == iid).first()
    if not obj:
        raise HTTPException(404, "Iteration not found")
    ml_core_url = os.getenv("ML_CORE_URL", "http://localhost:5000")
    try:
        res = httpx.get(f"{ml_core_url}/status/{iid}", timeout=2.0)
        if res.status_code == 200:
            remote_status = res.json().get("status")
            if remote_status and remote_status != "unknown" and remote_status != obj.status:
                obj.status = remote_status
                if remote_status in ("COMPLETED", "FAILED", "CANCELLED"):
                    if not obj.end_utc:
                        obj.end_utc = datetime.utcnow()
                db.commit()
    except httpx.HTTPError:
        pass
    return obj

@router.post("/iterations/{iid}/run")
def run_iteration(iid: str, db: Session = Depends(get_db)):
    def parse_json_like(value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                try:
                    return ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    return None
        return value

    iteration = db.query(MlIteration).filter(MlIteration.iteration_id == iid).first()
    if not iteration:
        raise HTTPException(404, "Iteration not found")

    session = db.query(MlTrainingSession).filter(
        MlTrainingSession.session_id == iteration.session_id
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")

    process = None
    if session.process_id:
        process = db.query(MlTrainingProcess).filter(
            MlTrainingProcess.process_id == session.process_id
        ).first()

    model = None
    if session.model_id:
        model = db.query(MlModelArchitecture).filter(
            MlModelArchitecture.model_id == session.model_id
        ).first()

    reward_fn = None
    if session.function_id:
        reward_fn = db.query(MlRewardFunction).filter(
            MlRewardFunction.function_id == session.function_id
        ).first()

    training_params: Dict[str, Any] = {}
    if process:
        training_params.update({
            "gamma": process.gamma,
            "tau": process.tau,
            "epsilon_start": process.epsilon_start,
            "epsilon_end": process.epsilon_end,
            "epsilon_decay_steps": None,
            "epochs": process.epochs,
            "batch_size": process.batch_size,
            "learning_rate": process.learning_rate,
            "learning_rate": process.learning_rate,
            "window_size": process.window_size,
            "optimizer": process.optimizer,
            "loss": process.loss,
            "fees": process.fees
        })

    if reward_fn:
        training_params["reward_code"] = reward_fn.code
        if reward_fn.metadata_json:
            meta = parse_json_like(reward_fn.metadata_json)
            if isinstance(meta, dict):
                if meta.get("action_labels"):
                    training_params["action_labels"] = meta.get("action_labels")
                if meta.get("status_labels"):
                    training_params["status_labels"] = meta.get("status_labels")
                if meta.get("execution_params"):
                    training_params["execution_params"] = meta.get("execution_params")

    model_arch = []
    if model and model.layers_json is not None:
        parsed_layers = parse_json_like(model.layers_json)
        if isinstance(parsed_layers, list):
            model_arch = parsed_layers

    config = {
        "dataset_id": iteration.dataset_id,
        "training_params": training_params,
        "model_architecture": model_arch
    }

    ml_core_url = os.getenv("ML_CORE_URL", "http://localhost:5000")
    try:
        response = httpx.post(
            f"{ml_core_url}/train",
            json={"run_id": iteration.iteration_id, "config": config},
            timeout=10.0
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        iteration.status = "FAILED"
        db.commit()
        raise HTTPException(502, f"ML Core training start failed: {e}")

    logger.info("Training dispatch sent for iteration %s", iteration.iteration_id)
    iteration.status = "RUNNING"
    iteration.start_utc = datetime.utcnow()
    db.commit()

    return {"status": "RUNNING", "iteration_id": iteration.iteration_id}

@router.post("/iterations/{iid}/stop")
def stop_iteration(iid: str, db: Session = Depends(get_db)):
    iteration = db.query(MlIteration).filter(MlIteration.iteration_id == iid).first()
    if not iteration:
        raise HTTPException(404, "Iteration not found")

    ml_core_url = os.getenv("ML_CORE_URL", "http://localhost:5000")
    try:
        httpx.post(f"{ml_core_url}/stop/{iid}", timeout=5.0)
    except httpx.HTTPError:
        pass

    iteration.status = "CANCELLED"
    iteration.end_utc = datetime.utcnow()
    db.commit()
    return {"status": "CANCELLED", "iteration_id": iteration.iteration_id}

@router.post("/iterations/{iid}/logging")
def update_iteration_logging(iid: str, config: IterationLoggingConfig):
    ml_core_url = os.getenv("ML_CORE_URL", "http://localhost:5000")
    try:
        response = httpx.post(
            f"{ml_core_url}/runs/{iid}/logging",
            json=config.dict(),
            timeout=5.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"ML Core logging update failed: {e}")

@router.get("/iterations/{iid}/logs")
def get_iteration_logs(iid: str, limit: int = 500):
    entries = get_logs(filter_term=iid, limit=limit)
    return [f"{e.get('timestamp')} [{e.get('level')}] {e.get('message')}" for e in entries]
