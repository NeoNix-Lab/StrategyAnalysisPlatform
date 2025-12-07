import numpy as np
import pandas as pd
from typing import List, Dict

class MonteCarloSimulator:
    """
    Esegue stress test sui trade tramite simulazione Monte Carlo.
    """
    
    def __init__(self, trades_pnl: List[float]):
        self.trades = np.array(trades_pnl)
    
    def run_simulation(self, n_simulations: int = 1000, equity_start: float = 10000) -> Dict:
        """
        Esegue n_simulations mescolando l'ordine dei trade.
        Restituisce statistiche su Max Drawdown e Final Equity.
        """
        if len(self.trades) == 0:
            return {}
            
        final_equities = []
        max_drawdowns = []
        equity_curves = []
        
        for _ in range(n_simulations):
            # Shuffle dei trade
            shuffled_trades = np.random.permutation(self.trades)
            
            # Calcolo equity curve
            equity_curve = np.concatenate(([equity_start], equity_start + np.cumsum(shuffled_trades)))
            equity_curves.append(equity_curve)
            
            # Final Equity
            final_equities.append(equity_curve[-1])
            
            # Max Drawdown
            peaks = np.maximum.accumulate(equity_curve)
            drawdowns = (equity_curve - peaks)
            max_dd = np.min(drawdowns)
            max_drawdowns.append(max_dd)
        
        # Calcolo percentili equity curves per confidence bands
        equity_curves_array = np.array(equity_curves)
        percentile_5 = np.percentile(equity_curves_array, 5, axis=0)
        percentile_25 = np.percentile(equity_curves_array, 25, axis=0)
        percentile_50 = np.percentile(equity_curves_array, 50, axis=0)
        percentile_75 = np.percentile(equity_curves_array, 75, axis=0)
        percentile_95 = np.percentile(equity_curves_array, 95, axis=0)
            
        return {
            "worst_case_drawdown": float(np.percentile(max_drawdowns, 5)),
            "average_drawdown": float(np.mean(max_drawdowns)),
            "best_case_drawdown": float(np.percentile(max_drawdowns, 95)),
            "median_final_equity": float(np.median(final_equities)),
            "var_95": float(np.percentile(final_equities, 5)),
            "var_99": float(np.percentile(final_equities, 1)),
            "cvar_95": float(np.mean([eq for eq in final_equities if eq <= np.percentile(final_equities, 5)])),
            "equity_distribution": {
                "p5": percentile_5.tolist(),
                "p25": percentile_25.tolist(),
                "p50": percentile_50.tolist(),
                "p75": percentile_75.tolist(),
                "p95": percentile_95.tolist()
            },
            "final_equity_histogram": {
                "values": final_equities,
                "mean": float(np.mean(final_equities)),
                "std": float(np.std(final_equities))
            }
        }

class StressTestScenarios:
    """
    Applica scenari di stress ai trade.
    """
    
    @staticmethod
    def apply_commission_stress(trades_pnl: List[float], commission_increase: float = 2.0) -> List[float]:
        """
        Simula raddoppio (o altro fattore) delle commissioni.
        Assume che ogni trade abbia una commissione media.
        """
        avg_commission = 2.0  # Stima commissione media per trade
        return [pnl - (avg_commission * (commission_increase - 1)) for pnl in trades_pnl]
    
    @staticmethod
    def apply_slippage_stress(trades_pnl: List[float], slippage_ticks: int = 1, tick_value: float = 1.0) -> List[float]:
        """
        Simula slippage aggiuntivo su ogni trade.
        """
        slippage_cost = slippage_ticks * tick_value
        return [pnl - slippage_cost for pnl in trades_pnl]
    
    @staticmethod
    def remove_best_trades(trades_pnl: List[float], percentage: float = 0.1) -> List[float]:
        """
        Rimuove i migliori X% trade (worst case scenario).
        """
        trades_sorted = sorted(trades_pnl, reverse=True)
        n_to_remove = int(len(trades_sorted) * percentage)
        return trades_sorted[n_to_remove:]
    
    @staticmethod
    def run_all_scenarios(trades_pnl: List[float]) -> Dict:
        """
        Esegue tutti gli scenari di stress e restituisce i risultati.
        """
        base_pnl = sum(trades_pnl)
        
        # Scenario 1: Commissioni raddoppiate
        comm_2x = StressTestScenarios.apply_commission_stress(trades_pnl, 2.0)
        
        # Scenario 2: Slippage +1 tick
        slip_1t = StressTestScenarios.apply_slippage_stress(trades_pnl, 1, 1.0)
        
        # Scenario 3: Slippage +2 tick
        slip_2t = StressTestScenarios.apply_slippage_stress(trades_pnl, 2, 1.0)
        
        # Scenario 4: Rimozione best 10% trade
        no_best_10 = StressTestScenarios.remove_best_trades(trades_pnl, 0.1)
        
        return {
            "base": {
                "net_pnl": float(base_pnl),
                "trade_count": len(trades_pnl)
            },
            "commission_2x": {
                "net_pnl": float(sum(comm_2x)),
                "impact": float(sum(comm_2x) - base_pnl)
            },
            "slippage_1tick": {
                "net_pnl": float(sum(slip_1t)),
                "impact": float(sum(slip_1t) - base_pnl)
            },
            "slippage_2tick": {
                "net_pnl": float(sum(slip_2t)),
                "impact": float(sum(slip_2t) - base_pnl)
            },
            "remove_best_10pct": {
                "net_pnl": float(sum(no_best_10)),
                "impact": float(sum(no_best_10) - base_pnl),
                "trades_removed": len(trades_pnl) - len(no_best_10)
            }
        }
