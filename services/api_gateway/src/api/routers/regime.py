from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from quant_shared.analytics.standard_analyzer import StandardAnalyzer
from quant_shared.core.trade_service import TradeService
from quant_shared.models.connection import get_db
from quant_shared.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _serialize_response(run_id: str, strategy_id: Optional[str], regime_payload: dict, trade_count: int, tags_updated: int) -> dict:
    return {
        "run_id": run_id,
        "strategy_id": strategy_id,
        "trade_count": trade_count,
        "tags_updated": tags_updated,
        "regime_performance": regime_payload
    }


@router.get("/{run_id}")
def get_regime_performance(run_id: str, request: Request, strategy_id: Optional[str] = None, db: Session = Depends(get_db)):
    trace_id = request.headers.get("X-Trace-Id", "unknown")
    analyzer = StandardAnalyzer(db)

    try:
        payload = analyzer.calculate_regime_performance(strategy_id=strategy_id, run_id=run_id)
        logger.info(f"[{trace_id}] Regime data served for run {run_id}")
        return _serialize_response(run_id, strategy_id, payload, 0, 0)
    except Exception as exc:
        logger.error(f"[{trace_id}] Failed to calculate regime performance for run {run_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to calculate regime metrics")


@router.post("/{run_id}/rebuild")
def rebuild_regime(run_id: str, request: Request, strategy_id: Optional[str] = None, db: Session = Depends(get_db)):
    trace_id = request.headers.get("X-Trace-Id", "unknown")
    service = TradeService(db)
    analyzer = StandardAnalyzer(db)

    trade_count = service.count_trades_for_run(run_id)
    if trade_count == 0:
        logger.warning(f"[{trace_id}] No trades found for run {run_id}; skipping regime rebuild.")
        raise HTTPException(status_code=404, detail="No trades to analyze")

    tags_updated = service.ensure_regime_tags(run_id)

    try:
        payload = analyzer.calculate_regime_performance(strategy_id=strategy_id, run_id=run_id)
        logger.info(f"[{trace_id}] Rebuilt regime for run {run_id} (tags updated={tags_updated})")
        return _serialize_response(run_id, strategy_id, payload, trade_count, tags_updated)
    except Exception as exc:
        logger.error(f"[{trace_id}] Failed rebuild for run {run_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Regime rebuild failed")
