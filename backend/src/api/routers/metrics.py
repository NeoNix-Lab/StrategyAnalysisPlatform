from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.services.analytics import StandardAnalyzer

router = APIRouter()

@router.get("/run/{run_id}")
def get_run_metrics(run_id: str, db: Session = Depends(get_db)):
    """
    Get aggregated metrics (PnL, Drawdown, Equity Curve) for a specific run.
    """
    analyzer = StandardAnalyzer(db)
    try:
        metrics = analyzer.calculate_portfolio_metrics(run_id=run_id)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/{strategy_id}")
def get_strategy_metrics(strategy_id: str, db: Session = Depends(get_db)):
    """
    Get aggregated metrics for an entire strategy (across all runs or instances).
    """
    analyzer = StandardAnalyzer(db)
    try:
        metrics = analyzer.calculate_portfolio_metrics(strategy_id=strategy_id)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import List
from pydantic import BaseModel

class CompareRequest(BaseModel):
    run_ids: List[str]

@router.post("/compare")
def compare_runs(request: CompareRequest, db: Session = Depends(get_db)):
    """
    Get aggregated metrics for multiple runs for comparison.
    """
    analyzer = StandardAnalyzer(db)
    results = []
    
    # Optimization: Could change StandardAnalyzer to accept list, 
    # but individual queries are fine for 2-10 runs.
    for run_id in request.run_ids:
        try:
            metrics = analyzer.calculate_portfolio_metrics(run_id=run_id)
            # Add run_id to response for easier mapping frontend-side
            metrics["run_id"] = run_id 
            results.append(metrics)
        except Exception as e:
            # Don't fail entire batch, just log/skip
            print(f"Error calculating metrics for {run_id}: {e}")
            results.append({"run_id": run_id, "error": str(e)})
            
    return results
