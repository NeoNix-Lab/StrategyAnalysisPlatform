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
