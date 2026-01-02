from sqlalchemy.orm import Session
from quant_shared.models.models import Trade, Bar, Side, Execution, Order
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
        from quant_shared.models.models import RunSeries
        
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
        from quant_shared.models.models import StrategyRun
        query = self.db.query(Trade).join(StrategyRun, Trade.run_id == StrategyRun.run_id)
        
        if strategy_id:
            # Check strategy_id via the StrategyRun -> StrategyInstance link?
            # Or assume run.strategy_id if it existed (it doesn't).
            # We need to join StrategyInstance too?
            # Let's check how runs are linked. Run -> Instance -> Strategy.
            from quant_shared.models.models import StrategyInstance
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

        # [NEW] Execution Metrics (Level 5)
        # We need Orders to compare against
        orders = []
        if run_id:
             orders = self.db.query(Order).filter(Order.run_id == run_id).all()
        
        # Calculate Latency & Fill Ratio
        latencies = []
        ordered_qty = 0.0
        executed_qty = 0.0
        
        # Create a map of orders for fast lookup
        order_map = {o.order_id: o for o in orders}
        
        for e in executions:
            executed_qty += e.quantity
            if e.order_id in order_map:
                o = order_map[e.order_id]
                # Latency
                if o.submit_utc and e.exec_utc:
                    latency = (e.exec_utc - o.submit_utc).total_seconds()
                    # Only positive latencies make sense, but clock skew might happen
                    if latency >= 0:
                        latencies.append(latency)
        
        # Sum ordered quantity
        # Be careful not to double count if we have partial fills?
        # Actually simplest is sum of all generic orders quantity vs sum of all executions quantity
        # But for fill ratio, we usually want (Filled / Requested).
        ordered_qty = sum([o.quantity for o in orders]) if orders else 0.0
        
        avg_fill_latency = np.mean(latencies) if latencies else 0.0
        fill_ratio = (executed_qty / ordered_qty) if ordered_qty > 0 else 0.0

        # [NEW] Equity Curve Generation
        try:
            equity_curve = self._generate_equity_curve(df)
        except Exception:
            equity_curve = []

        # Safe Metrics Calculation Helper
        def safe_calc(func, default=0.0):
            try:
                res = func()
                return res if not (pd.isna(res) or res is None) else default
            except Exception:
                return default

        return {
            # P0
            "total_trades": int(total_trades),
            "total_fees": round(total_fees, 2),
            "total_volume": round(total_volume, 2),
            # Level 5
            "avg_fill_latency": round(avg_fill_latency, 3), # seconds
            "fill_ratio": round(fill_ratio, 2), # % or ratio
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
            "sharpe_ratio": safe_calc(lambda: round(self._calculate_sharpe(df['pnl_net'], annualized=True), 2)),
            "sortino_ratio": safe_calc(lambda: round(self._calculate_sortino(df['pnl_net'], annualized=True), 2)),
            "calmar_ratio": safe_calc(lambda: round(self._calculate_calmar(net_profit, max_drawdown), 2)),
            
            # [NEW] Equity Curve Data
            "equity_curve": equity_curve,
            
            # P2 (Execution Analysis)
            "avg_mae": round(df['mae'].mean(), 2) if 'mae' in df and not df['mae'].isnull().all() else 0,
            "avg_mfe": round(df['mfe'].mean(), 2) if 'mfe' in df and not df['mfe'].isnull().all() else 0,
            "efficiency_ratio": safe_calc(lambda: round(self._calculate_efficiency(df), 2)),
            "stability_r2": safe_calc(lambda: round(self._calculate_stability(df), 2)),
            "pnl_skew": safe_calc(lambda: self._calculate_distribution_stats(df)['skew']),
            "pnl_kurtosis": safe_calc(lambda: self._calculate_distribution_stats(df)['kurtosis'])
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
        """
        Calculates Capture Efficiency: Total captured Move (Price*Qty) / Total Potential Move (MFE*Qty).
        This cancels out the contract multiplier, providing a correct efficiency ratio (0.0 to 1.0+).
        """
        if df.empty:
            return 0.0
            
        if 'mfe' not in df or 'quantity' not in df or 'entry_price' not in df or 'exit_price' not in df:
            return 0.0

        total_captured = 0.0
        total_potential = 0.0
        
        for _, t in df.iterrows():
            mfe = t.get('mfe', 0.0)
            if pd.isna(mfe) or mfe <= 0:
                continue
                
            qty = t.get('quantity', 0.0)
            if qty <= 0:
                continue

            entry = t.get('entry_price', 0.0)
            exit_p = t.get('exit_price', 0.0)
            side = str(t.get('side', 'BUY'))
            
            # Calculate Captured Price Delta
            if side == 'BUY':
                captured_delta = exit_p - entry
            else:
                captured_delta = entry - exit_p
            
            # Potential Price Delta (MFE) is already max favorable excursion from entry
            potential_delta = mfe
            
            total_captured += captured_delta * qty
            total_potential += potential_delta * qty
            
        if total_potential == 0:
            return 0.0
            
        return total_captured / total_potential

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
            "avg_fill_latency": 0,
            "fill_ratio": 0,
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
