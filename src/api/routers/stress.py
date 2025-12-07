from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.models import Trade
from src.quantlab.stress_test import MonteCarloSimulator, StressTestScenarios

router = APIRouter()

@router.get("/montecarlo")
def run_monte_carlo(strategy_id: str = "DEMO_STRAT", n_simulations: int = 1000, db: Session = Depends(get_db)):
    """
    Esegue simulazione Monte Carlo sui trade.
    """
    trades = db.query(Trade).filter(Trade.strategy_id == strategy_id).all()
    
    if not trades:
        return {"error": "No trades found"}
    
    trades_pnl = [t.pnl_net for t in trades]
    
    simulator = MonteCarloSimulator(trades_pnl)
    results = simulator.run_simulation(n_simulations=n_simulations)
    
    return results

@router.get("/stress-scenarios")
def run_stress_scenarios(strategy_id: str = "DEMO_STRAT", db: Session = Depends(get_db)):
    """
    Esegue scenari di stress test.
    """
    trades = db.query(Trade).filter(Trade.strategy_id == strategy_id).all()
    
    if not trades:
        return {"error": "No trades found"}
    
    trades_pnl = [t.pnl_net for t in trades]
    
    results = StressTestScenarios.run_all_scenarios(trades_pnl)
    
    return results
