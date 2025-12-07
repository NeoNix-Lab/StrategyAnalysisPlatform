from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.database.connection import get_db
from src.database.models import Experiment, ExperimentRun
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

# Pydantic Models
class ExperimentCreate(BaseModel):
    name: str
    description: str = None
    base_config: Dict[str, Any] = {}

class ExperimentRunCreate(BaseModel):
    experiment_id: str
    parameters: Dict[str, Any]
    metrics: Dict[str, Any] = {}

class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    description: str = None
    created_at: datetime
    base_config: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True

class ExperimentRunResponse(BaseModel):
    run_id: str
    experiment_id: str
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Endpoints
@router.post("/experiments", response_model=ExperimentResponse)
def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    """Crea un nuovo esperimento"""
    exp_id = str(uuid.uuid4())
    db_experiment = Experiment(
        experiment_id=exp_id,
        name=experiment.name,
        description=experiment.description,
        base_config=experiment.base_config
    )
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment

@router.get("/experiments", response_model=List[ExperimentResponse])
def list_experiments(db: Session = Depends(get_db)):
    """Lista tutti gli esperimenti"""
    return db.query(Experiment).all()

@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    """Ottieni dettagli di un esperimento"""
    exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

@router.post("/experiments/runs", response_model=ExperimentRunResponse)
def create_run(run: ExperimentRunCreate, db: Session = Depends(get_db)):
    """Crea un nuovo run per un esperimento"""
    run_id = str(uuid.uuid4())
    db_run = ExperimentRun(
        run_id=run_id,
        experiment_id=run.experiment_id,
        parameters=run.parameters,
        metrics=run.metrics
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

@router.get("/experiments/{experiment_id}/runs", response_model=List[ExperimentRunResponse])
def get_experiment_runs(experiment_id: str, db: Session = Depends(get_db)):
    """Ottieni tutti i run di un esperimento"""
    return db.query(ExperimentRun).filter(ExperimentRun.experiment_id == experiment_id).all()

@router.get("/experiments/runs/{run_id}", response_model=ExperimentRunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Ottieni dettagli di un run specifico"""
    run = db.query(ExperimentRun).filter(ExperimentRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
