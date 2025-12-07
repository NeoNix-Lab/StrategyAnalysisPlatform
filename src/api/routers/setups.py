from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.connection import get_db
from src.database.models import Trade
from typing import Dict, List
from pydantic import BaseModel

router = APIRouter()

class SetupStats(BaseModel):
    setup: str
    count: int
    win_rate: float
    profit_factor: float
    avg_trade: float
    total_pnl: float

@router.get("/setup-analysis", response_model=List[SetupStats])
def get_setup_analysis(strategy_id: str = "DEMO_STRAT", db: Session = Depends(get_db)):
    """
    Analizza performance per setup/pattern di trading.
    """
    trades = db.query(Trade).filter(Trade.strategy_id == strategy_id).all()
    
    if not trades:
        return []
    
    # Raggruppa per setup_tag
    setup_groups = {}
    for trade in trades:
        tag = trade.setup_tag or "Untagged"
        if tag not in setup_groups:
            setup_groups[tag] = []
        setup_groups[tag].append(trade)
    
    # Calcola metriche per ogni setup
    results = []
    for setup, setup_trades in setup_groups.items():
        total = len(setup_trades)
        wins = [t for t in setup_trades if t.pnl_net > 0]
        losses = [t for t in setup_trades if t.pnl_net <= 0]
        
        total_win = sum(t.pnl_net for t in wins)
        total_loss = abs(sum(t.pnl_net for t in losses))
        
        win_rate = (len(wins) / total * 100) if total > 0 else 0
        profit_factor = (total_win / total_loss) if total_loss > 0 else (total_win if total_win > 0 else 0)
        avg_trade = sum(t.pnl_net for t in setup_trades) / total if total > 0 else 0
        total_pnl = sum(t.pnl_net for t in setup_trades)
        
        results.append(SetupStats(
            setup=setup,
            count=total,
            win_rate=round(win_rate, 2),
            profit_factor=round(profit_factor, 2),
            avg_trade=round(avg_trade, 2),
            total_pnl=round(total_pnl, 2)
        ))
    
    # Ordina per total_pnl decrescente
    results.sort(key=lambda x: x.total_pnl, reverse=True)
    
    return results

class TagUpdate(BaseModel):
    trade_id: str
    setup_tag: str

@router.post("/tag-trade")
def tag_trade(update: TagUpdate, db: Session = Depends(get_db)):
    """
    Aggiorna il tag di un trade.
    """
    trade = db.query(Trade).filter(Trade.trade_id == update.trade_id).first()
    if not trade:
        return {"error": "Trade not found"}
    
    trade.setup_tag = update.setup_tag
    db.commit()
    
    return {"success": True, "trade_id": update.trade_id, "setup_tag": update.setup_tag}
