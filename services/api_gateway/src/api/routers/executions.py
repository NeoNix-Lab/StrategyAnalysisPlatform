from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from src.database.connection import get_db
from src.database.models import Execution
from src.api.schemas import ExecutionResponse

router = APIRouter()

@router.get("/run/{run_id}", response_model=List[ExecutionResponse])
def get_executions_by_run(run_id: str, db: Session = Depends(get_db)):
    return db.query(Execution).filter(Execution.run_id == run_id).all()
