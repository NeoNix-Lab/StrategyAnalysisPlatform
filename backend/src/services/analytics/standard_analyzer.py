from sqlalchemy.orm import Session
from src.database.models import Trade, Bar, Side, Execution, Order
import pandas as pd
import numpy as np

class StandardAnalyzer:
    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_mae_mfe(self, trade_id: str):
        """
        Calculates MAE and MFE for a single trade based on bar data.
        Phase 4 (Execution Analysis) - prioritized for individual trade context.
        """
        trade = self.db.query(Trade).filter(Trade.trade_id == trade_id).first()
        if not trade:
            return

        # Fetch bars covering the trade duration
        # Bar does not have symbol directly, it is on RunSeries
        from src.database.models import RunSeries
        
        bars = self.db.query(Bar).join(RunSeries, Bar.series_id == RunSeries.series_id).filter(
            RunSeries.run_id == trade.run_id,
            RunSeries.symbol == trade.symbol,
            Bar.ts_utc >= trade.entry_time,
            Bar.ts_utc <= trade.exit_time
        ).all()

        if not bars:
            # Not enough data to calculate MAE/MFE
            return

        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        
        max_price = max(highs)
        min_price = min(lows)

        if trade.side == Side.BUY:
            mfe = max_price - trade.entry_price
            mae = trade.entry_price - min_price
        else:
            mfe = trade.entry_price - min_price
            mae = max_price - trade.entry_price

        trade.mae = max(0.0, mae)
        trade.mfe = max(0.0, mfe)
        
        self.db.commit()

    def calculate_portfolio_metrics(self, strategy_id: str, run_id: str = None) -> dict:
        """
        Calculates aggregate metrics for a strategy or run.
        Includes Phase 1 (Core) and Phase 2 (Risk) metrics.
        """
        # Join with StrategyRun to filter by strategy_id if needed, or just filter by run_id
        from src.database.models import StrategyRun
        query = self.db.query(Trade).join(StrategyRun, Trade.run_id == StrategyRun.run_id)
        
        if strategy_id:
            # Check strategy_id via the StrategyRun -> StrategyInstance link?
            # Or assume run.strategy_id if it existed (it doesn't).
            # We need to join StrategyInstance too?
            # Let's check how runs are linked. Run -> Instance -> Strategy.
            from src.database.models import StrategyInstance
            query = query.join(StrategyInstance, StrategyRun.instance_id == StrategyInstance.instance_id)\
                         .filter(StrategyInstance.strategy_id == strategy_id)
        
        if run_id:
            query = query.filter(Trade.run_id == run_id)
            
        trades = query.all()

        # [NEW] Fetch Executions for Fee/Volume Analysis (if run_id provided)
        executions = []
        if run_id:
             executions = self.db.query(Execution).filter(Execution.run_id == run_id).all()
        
        if not trades and not executions:
            return self._empty_metrics()

        # Convert to DataFrame
        trade_dicts = []
        for t in trades:
            d = t.__dict__.copy()
            d.pop('_sa_instance_state', None)
            if 'side' in d and hasattr(d['side'], 'name'):
                d['side'] = d['side'].name
            trade_dicts.append(d)
        
        df = pd.DataFrame(trade_dicts)
        if df.empty:
             return self._empty_metrics()

        # --- Phase 1: Core Metrics (P0) ---
        total_trades = len(df)
        winning_trades = df[df['pnl_net'] > 0]
        losing_trades = df[df['pnl_net'] <= 0]

        win_rate = len(winning_trades) / total_trades
        
        gross_profit = winning_trades['pnl_net'].sum()
        gross_loss = abs(losing_trades['pnl_net'].sum())
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_trade = df['pnl_net'].mean()
        net_profit = df['pnl_net'].sum()

        # --- Phase 2: Risk Metrics (P1) ---
        
        # Drawdown Analysis
        df = df.sort_values('exit_time')
        df['cumulative_pnl'] = df['pnl_net'].cumsum()
        df['peak'] = df['cumulative_pnl'].cummax()
        df['drawdown'] = df['cumulative_pnl'] - df['peak']
        
        max_drawdown = df['drawdown'].min() # Negative value
        
        # Drawdown Duration (Time spent in drawdown)
        # Simple approximation: streaks of days/time between peaks
        # For now, we can measure consecutive trades in drawdown? 
        # Or time difference. Let's stick to simple scalar metrics for now.
        
        # Expectancy = (Win % * Avg Win) - (Loss % * Avg Loss)
        avg_win = winning_trades['pnl_net'].mean() if not winning_trades.empty else 0
        avg_loss = abs(losing_trades['pnl_net'].mean()) if not losing_trades.empty else 0
        loss_rate = 1.0 - win_rate
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        # Consecutive Wins/Losses
        # Create a boolean series for wins (True) and losses (False)
        is_win = df['pnl_net'] > 0
        # Group by consecutive values
        # (is_win != is_win.shift()).cumsum() creates a group ID for each streak
        streaks = is_win.groupby((is_win != is_win.shift()).cumsum()).count()
        
        # Filter strictly for wins and losses to get max streaks
        # We need to map back to whether it was a win or loss streak
        streak_types = is_win.groupby((is_win != is_win.shift()).cumsum()).first()
        
        max_consecutive_wins = streaks[streak_types == True].max() if not streaks[streak_types == True].empty else 0
        max_consecutive_losses = streaks[streak_types == False].max() if not streaks[streak_types == False].empty else 0

        # [NEW] Fee & Volume Analysis
        total_fees = sum([e.fee for e in executions]) if executions else 0.0
        # Simple volume calc: price * qty
        total_volume = sum([e.price * e.quantity for e in executions]) if executions else 0.0

        # [NEW] Equity Curve Generation
        equity_curve = self._generate_equity_curve(df)

        return {
            # P0
            "total_trades": int(total_trades),
            "total_fees": round(total_fees, 2),
            "total_volume": round(total_volume, 2),
            "win_rate": round(win_rate * 100, 2),
            "profit_factor": round(profit_factor, 2),
            "average_trade": round(avg_trade, 2),
            "net_profit": round(net_profit, 2),
            
            # P1
            "max_drawdown": round(max_drawdown, 2),
            "expectancy": round(expectancy, 2),
            "max_consecutive_wins": int(max_consecutive_wins),
            "max_consecutive_losses": int(max_consecutive_losses),
            
            # P2 (Performance Ratios)
            # P2 (Performance Ratios) - using Annualized Default (252)
            "sharpe_ratio": round(self._calculate_sharpe(df['pnl_net'], annualized=True), 2),
            "sortino_ratio": round(self._calculate_sortino(df['pnl_net'], annualized=True), 2),
            "calmar_ratio": round(self._calculate_calmar(net_profit, max_drawdown), 2),
            
            # [NEW] Equity Curve Data (Simplified for storage/api)
            # Maybe too large for metrics_json? 
            # Storing summary stats instead.
            "equity_curve": equity_curve, # Frontend can use this if passed via API
            
            # P2 (Execution Analysis)
            "avg_mae": round(df['mae'].mean(), 2) if 'mae' in df else 0,
            "avg_mfe": round(df['mfe'].mean(), 2) if 'mfe' in df else 0,
            "efficiency_ratio": round(self._calculate_efficiency(df), 2),
            "stability_r2": round(self._calculate_stability(df), 2),
            "pnl_skew": self._calculate_distribution_stats(df)['skew'],
            "pnl_kurtosis": self._calculate_distribution_stats(df)['kurtosis']
        }

    def _calculate_sharpe(self, returns: pd.Series, annualized: bool = False) -> float:
        if returns.empty or returns.std() == 0:
            return 0.0
        # Trade-based Sharpe
        ratio = returns.mean() / returns.std()
        if annualized:
            # Approximation: sqrt(252/avg_duration_days) or simpler sqrt(252) if daily.
            # Since these are per-trade returns, we technically need to know trade frequency.
            # Ideally resample to daily returns.
            # FALLBACK: Just sqrt(trades_per_year) or sqrt(252) as rough proxy if we assume 1 trade/day.
            # Let's use sqrt(252) as standard "annualized" multiplier for now, 
            # acknowledging it assumes daily-like frequency.
            ratio = ratio * np.sqrt(252) 
        return ratio

    def _calculate_sortino(self, returns: pd.Series, annualized: bool = False) -> float:
        if returns.empty:
            return 0.0
        downside = returns[returns < 0]
        if downside.empty or downside.std() == 0:
            return 0.0 # No downside risk
        ratio = returns.mean() / downside.std()
        if annualized:
            ratio = ratio * np.sqrt(252)
        return ratio

    def _calculate_calmar(self, net_profit: float, max_drawdown: float) -> float:
        if max_drawdown == 0:
            return 0.0
        # Calmar = CAGR / MaxDrawdown. Here we use NetProfit / MaxDrawdown as proxy for now
        # Note: MaxDrawdown is usually negative, but Calmar requires positive denominator
        return net_profit / abs(max_drawdown)
        
    def _calculate_efficiency(self, df: pd.DataFrame) -> float:
        # Efficiency can be defined as sum(PnL) / sum(MFE) (How much of the available move did we capture?)
        # Or PnL / (MFE + MAE) per trade.
        # Simple proxy: Total Net Profit / Total MFE
        if 'mfe' not in df or df['mfe'].sum() == 0:
            return 0.0
        return df['pnl_net'].sum() / df['mfe'].sum()

    def _calculate_stability(self, df: pd.DataFrame) -> float:
        """
        Calculates R-Squared of the equity curve to measure smoothness/consistency.
        """
        if df.empty or len(df) < 2:
            return 0.0
        
        # Create a cumulative PnL curve
        # We assume df is already sorted by exit_time in the calls
        cum_pnl = df['pnl_net'].cumsum()
        
        # X axis is just trade count (0, 1, 2...) for trade-based consistency
        # For time-based, we'd need time deltas. Sticking to trade-based for now.
        y = cum_pnl.values
        x = np.arange(len(y))
        
        # Correlation matrix
        correlation = np.corrcoef(x, y)[0, 1]
        
        # R-squared
        return correlation**2 if not np.isnan(correlation) else 0.0

    def _calculate_distribution_stats(self, df: pd.DataFrame) -> dict:
        """
        Calculates higher moments of the PnL distribution.
        """
        if df.empty or len(df) < 5:
            return {"skew": 0.0, "kurtosis": 0.0}
            
        return {
            "skew": round(df['pnl_net'].skew(), 2),
            "kurtosis": round(df['pnl_net'].kurtosis(), 2)
        }

    def _empty_metrics(self):
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "average_trade": 0,
            "net_profit": 0,
            "max_drawdown": 0,
            "expectancy": 0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "calmar_ratio": 0,
            "avg_mae": 0,
            "avg_mfe": 0,
            "total_fees": 0,
            "total_volume": 0,
            "efficiency_ratio": 0,
            "stability_r2": 0,
            "pnl_skew": 0,
            "pnl_kurtosis": 0,
            "equity_curve": []
        }

    def _generate_equity_curve(self, df: pd.DataFrame) -> list:
        """
        Generates a time-series equity curve with drawdown info.
        Expects df to have 'exit_time' and 'pnl_net'.
        """
        if df.empty:
            return []
            
        # Ensure sorted
        df = df.sort_values('exit_time')
        
        cumulative = 0
        peak = 0
        curve = []
        
        for index, row in df.iterrows():
            pnl = row['pnl_net']
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = cumulative - peak
            
            curve.append({
                "time": row['exit_time'].isoformat() if hasattr(row['exit_time'], 'isoformat') else str(row['exit_time']),
                "pnl": round(cumulative, 2),
                "drawdown": round(drawdown, 2)
            })
            
        return curve
