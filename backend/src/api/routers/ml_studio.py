from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
import os
import json
import pandas as pd
import numpy as np

from ...database.connection import get_db
from ...database import models
from ...database.models import Dataset, RunSeries, Bar, MarketSeries, MarketBar
from ...training_node.runner import TrainingRunner

router = APIRouter(prefix="/ml/studio", tags=["ml-studio"])

# --- Schemas ---

class ValidateRewardRequest(BaseModel):
    code: str
    dataset_id: str
    metadata_json: Optional[Dict[str, Any]] = None


class RewardFunctionCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

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

@router.post("/functions/validate")
def validate_reward(req: ValidateRewardRequest, db: Session = Depends(get_db)):
    """
    Dry-run a reward function against a sample row from the selected dataset.
    """
    from ...database.models import Dataset, RunSeries, Bar, MarketSeries, MarketBar

    # 1. Fetch Dataset & Sample Data
    ds = db.query(Dataset).get(req.dataset_id)
    if not ds: return {"valid": False, "error": "Dataset not found"}

    if not ds.sources_json or len(ds.sources_json) == 0:
         return {"valid": False, "error": "Dataset has no sources defined"}

    source = ds.sources_json[0]

    # Helper to get bar
    bar_data = None

    # Try RunSeries
    series = db.query(RunSeries).filter(
        RunSeries.run_id == source.get("run_id"),
        RunSeries.symbol == source.get("symbol"),
        RunSeries.timeframe == source.get("timeframe")
    ).first()

    if series:
        bar = db.query(Bar).filter(Bar.series_id == series.series_id).order_by(Bar.ts_utc.desc()).first()
        if bar: bar_data = bar

    if not bar_data:
        m_series = db.query(MarketSeries).filter(
            MarketSeries.symbol == source.get("symbol"),
            MarketSeries.timeframe == source.get("timeframe")
        ).first()
        if m_series:
             bar = db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id).order_by(MarketBar.ts_utc.desc()).first()
             if bar: bar_data = bar

    if not bar_data:
        return {"valid": False, "error": "No data found in dataset source"}

    # 2. Construct 'obs'
    obs = {
        "open": getattr(bar_data, 'open', 0),
        "high": getattr(bar_data, 'high', 0),
        "low": getattr(bar_data, 'low', 0),
        "close": getattr(bar_data, 'close', 0),
        "volume": getattr(bar_data, 'volume', 0),
    }

    # 3. Execute Code
    class MockEnv:
        def __init__(self, current_price, action_labels=None, status_labels=None):
            self.position = 1 # Default to LONG for testing
            self.entry_price = current_price * 0.99 # Mock 1% profit
            self.qty = 1.0
            self.current_balance = 10000.0
            self.balance = 10000.0 # Match EnvFlex alias
            self.unrealized_pnl = (current_price - self.entry_price) * self.qty
            self.pnl = self.unrealized_pnl
            self.position_size = 1 # Signed size (+1, -1, 0)
            self.fees = 0.0
            self.last_reward = 0.0
            self.current_step = 0
            self.window_size = 10
            
            # --- Data Parity with EnvFlex ---
            # Create a mock DataFrame with 1 row but correct columns
            self.data = pd.DataFrame([obs])
            self.observation_dataframe = self.data.copy()
            # Add helper columns usually present in EnvFlex
            self.observation_dataframe['balance'] = self.balance
            self.observation_dataframe['action'] = 0
            self.observation_dataframe['reward'] = 0
            self.observation_dataframe['position_status'] = 1
            
            # Namespace Injection
            self.action_labels = action_labels or ["HOLD", "BUY", "SELL"]
            self.status_labels = status_labels or ["FLAT", "LONG", "SHORT"]
            
            # Create Enum-like objects dynamically
            class Namespace: pass
            
            self.actions = Namespace()
            for idx, label in enumerate(self.action_labels):
                setattr(self.actions, label.upper(), idx)
                
            self.status = Namespace()
            for idx, label in enumerate(self.status_labels):
                setattr(self.status, label.upper(), idx)
        
        # Removed property pnl as it is now assigned in init for simplicity, 
        # or kept if we want dynamic update (but mock is static snapshot)

    # Extract metadata from request
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
        
        # 1. Check for function-based definition (Standard)
        if "calculate_reward" in local_scope and callable(local_scope["calculate_reward"]):
            # Default test action: Try BUY (1) or HOLD (0) from actions namespace if available, else 1
            test_action = 1
            if hasattr(mock_env, 'actions'):
                if hasattr(mock_env.actions, 'BUY'): test_action = mock_env.actions.BUY
                elif hasattr(mock_env.actions, 'HOLD'): test_action = mock_env.actions.HOLD
            
            # Call the user's function
            result = local_scope["calculate_reward"](mock_env, test_action)
            
        # 2. Check for script-based definition (Legacy)
        elif "reward" in local_scope:
            result = local_scope["reward"]
            
        if result is not None:
            try:
                float_res = float(result)
                return {
                    "valid": True, 
                    "result": float_res,
                    "env_state": {
                        "pos": mock_env.position,
                        "pnl": mock_env.unrealized_pnl
                    }
                }
            except:
                return {"valid": False, "error": f"Result is not a number: {type(result)}"}
        else:
             return {"valid": False, "error": "Code must define 'def calculate_reward(env, action):' or assign 'reward' variable"}
             
    except Exception as e:
        return {"valid": False, "error": str(e)}

@router.post("/functions", response_model=Dict)
def create_function(req: RewardFunctionCreate, db: Session = Depends(get_db)):
    obj = models.MlRewardFunction(
        function_id=str(uuid.uuid4()),
        name=req.name,
        code=req.code,
        description=req.description,
        metadata_json=req.metadata_json or {}
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
    return {
        "function_id": obj.function_id, 
        "name": obj.name, 
        "code": obj.code, 
        "description": obj.description,
        "metadata_json": obj.metadata_json
    }

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
    return [
        {
            "session_id": s.session_id, 
            "name": s.name, 
            "status": s.status, 
            "created_at": s.created_utc, # Alignment with frontend
            "algorithm": s.model.name if s.model else "Unknown",
            "dataset_name": s.iterations[-1].dataset.name if s.iterations and s.iterations[-1].dataset else "N/A"
        } 
        for s in objs
    ]

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

@router.get("/iterations/{iid}")
def get_iteration(iid: str, db: Session = Depends(get_db)):
    obj = db.query(models.MlIteration).filter(models.MlIteration.iteration_id == iid).first()
    if not obj: raise HTTPException(404, "Iteration not found")
    
    return {
        "iteration_id": obj.iteration_id,
        "session_id": obj.session_id,
        "dataset_id": obj.dataset_id,
        "name": obj.name,
        "status": obj.status,
        "split_config": obj.split_config_json,
        "metrics_json": obj.metrics_json,
        "start_utc": obj.start_utc,
        "end_utc": obj.end_utc,
        "dataset_name": obj.dataset.name if obj.dataset else "Unknown"
    }

@router.get("/iterations/{iid}/run")
def run_iteration(iid: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger the actual training for an iteration.
    This effectively replaces the old /training/start endpoint logic but uses the defined entities.
    """
    iter_obj = db.query(models.MlIteration).filter(models.MlIteration.iteration_id == iid).first()
    if not iter_obj: raise HTTPException(404, "Iteration not found")
    
    session_obj = iter_obj.session
    if not session_obj.function or not session_obj.model or not session_obj.process:
         raise HTTPException(400, "Session is incomplete (missing function, model, or process)")
         
    # Mark as QUEUED immediately
    iter_obj.status = "QUEUED"
    db.commit()
    
    # Add to background tasks
    background_tasks.add_task(background_training_wrapper, iid)
    
    return {"status": "QUEUED", "iteration_id": iid}

def background_training_wrapper(iteration_id: str):
    """
    Wrapper to run training in a separate thread with its own DB session.
    """
    from ...database.connection import SessionLocal
    
    db = SessionLocal()
    try:
        runner = TrainingRunner(db, iteration_id)
        # Use a longer timeout or specific logic if needed
        runner.run()
    except Exception as e:
        import traceback
        import json
        from ...database.models import MlIteration
        
        print(f"Background Training Failed: {e}")
        # Capture critical failure in DB if not already handled
        try:
            iter_obj = db.query(MlIteration).filter(MlIteration.iteration_id == iteration_id).first()
            if iter_obj:
                iter_obj.status = "FAILED"
                tb_str = traceback.format_exc()
                
                # Update metrics
                metrics = iter_obj.metrics_json or {}
                if isinstance(metrics, str): metrics = json.loads(metrics)
                metrics["error"] = f"Startup Failed: {str(e)}\n{tb_str}"
                iter_obj.metrics_json = metrics
                
                # Update logs
                logs = []
                if iter_obj.logs_json:
                    try:
                        logs = json.loads(iter_obj.logs_json) if isinstance(iter_obj.logs_json, str) else iter_obj.logs_json
                    except: pass
                
                logs.append(f"CRITICAL SYSTEM ERROR: {str(e)}")
                logs.append(tb_str)
                iter_obj.logs_json = json.dumps(logs)
                
                db.commit()
        except Exception as db_e:
            print(f"Failed to write error to DB: {db_e}")
    finally:
        db.close()

@router.post("/iterations/{iid}/stop")
def stop_iteration(iid: str, db: Session = Depends(get_db)):
    """
    Signals a running iteration to stop gracefully.
    """
    iter_obj = db.query(models.MlIteration).filter(models.MlIteration.iteration_id == iid).first()
    if not iter_obj: raise HTTPException(404, "Iteration not found")
    
    if iter_obj.status not in ["RUNNING", "QUEUED", "PENDING"]:
        # Already stopped or finished, just return status
        return {"status": iter_obj.status, "message": "Iteration is not running"}
        
    iter_obj.status = "CANCELLING"
    db.commit()
    
    return {"status": "CANCELLING", "iteration_id": iid}


@router.get("/iterations/{iid}/logs")
def get_iteration_logs(iid: str, db: Session = Depends(get_db)):
    """
    Fetches logs for a specific iteration from the file system.
    """
    iter_obj = db.query(models.MlIteration).filter(models.MlIteration.iteration_id == iid).first()
    if not iter_obj: 
        raise HTTPException(404, "Iteration not found")
    
    log_path = os.path.join(os.getcwd(), "logs", "ml", f"{iid}.log")
    
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                # For now, return all lines. In future, implement tailing/offsets.
                lines = f.readlines()
                return [line.strip() for line in lines]
        except Exception as e:
            return [f"SYSTEM: Error reading log file: {str(e)}"]
    
    # Fallback to DB logs (e.g. for startup errors)
    if iter_obj.logs_json:
        try:
            return json.loads(iter_obj.logs_json) if isinstance(iter_obj.logs_json, str) else iter_obj.logs_json
        except:
            return [str(iter_obj.logs_json)]
            
    return []

# --- Endpoints: Inference / Registry ---

@router.get("/trained-models", response_model=List[Dict])
def list_trained_models(db: Session = Depends(get_db)):
    """
    Returns a list of iterations that are COMPLETED and have a valid model artifact.
    """
    # Filter for COMPLETED and where model_artifact_path is not null
    # Note: SQLite checks might be simple
    iters = db.query(models.MlIteration).filter(
        models.MlIteration.status == "COMPLETED",
        models.MlIteration.model_artifact_path != None
    ).order_by(models.MlIteration.end_utc.desc()).all()
    
    results = []
    for i in iters:
        metrics = i.metrics_json or {}
        results.append({
            "iteration_id": i.iteration_id,
            "name": i.name,
            "session_name": i.session.name if i.session else "Unknown",
            "algorithm": i.session.model.name if i.session and i.session.model else "Unknown",
            "dataset": i.dataset.name if i.dataset else "Unknown",
            "metrics": metrics,
            "created_utc": i.start_utc
        })
    return results

class TestRunCreate(BaseModel):
    source_iteration_id: str
    target_dataset_id: str

@router.post("/test", response_model=Dict)
def create_test_run(req: TestRunCreate, db: Session = Depends(get_db)):
    """
    Creates a new Iteration configured for Inference/Testing.
    It links to the same Session as the source, but marks it to load weights from the source.
    """
    source_iter = db.query(models.MlIteration).get(req.source_iteration_id)
    if not source_iter: raise HTTPException(404, "Source iteration not found")
    
    session = source_iter.session
    if not session: raise HTTPException(400, "Source iteration has no session")
    
    # Create new iteration
    new_iter_id = str(uuid.uuid4())
    new_name = f"Test-{source_iter.name}-{datetime.utcnow().strftime('%H%M')}"
    
    # We use split_config_json to pass the instruction to the Runner
    config = {
        "test_only": True,
        "load_from_iteration_id": source_iter.iteration_id,
        "source_model_path": source_iter.model_artifact_path
    }
    
    obj = models.MlIteration(
        iteration_id=new_iter_id,
        session_id=session.session_id,
        dataset_id=req.target_dataset_id,
        name=new_name,
        split_config_json=config, # Runner will look here
        status="PENDING"
    )
    
    db.add(obj)
    db.commit()
    
    return {
        "iteration_id": obj.iteration_id,
        "session_id": obj.session_id,
        "name": obj.name,
        "status": obj.status
    }
