
from typing import Any, Callable, Dict
import numpy as np

# We assume EnvFlex is passed as 'env'.
# Since we can't easily type hint circularly, we use Any or dynamic typing.

class StrategyLibrary:
    """
    A collection of static methods defining Execution and Reward logic.
    In a future iteration, this could be a class registry or loaded from plugins.
    """

    # --- EXECUTION LOGIC (The "Physics" / Appendix) ---
    
    @staticmethod
    def _get_price(env, default: float = 0.0) -> float:
        row = getattr(env, "data", None)
        if row is not None:
            if hasattr(row, "get"):
                val = row.get("close")
                if val is None:
                    val = row.get("price")
                if val is not None:
                    try:
                        return float(val)
                    except (TypeError, ValueError):
                        pass
            if hasattr(row, "__getitem__"):
                try:
                    return float(row["close"])
                except Exception:
                    pass

        dataset = getattr(env, "dataset", None)
        step = getattr(env, "current_step", None)
        if dataset is not None and step is not None:
            try:
                return float(dataset.at[step, "close"])
            except Exception:
                pass

        return float(default)

    @staticmethod
    def simple_long_short_execution(env, action: int):
        """
        Standard execution logic for FLAT, LONG, SHORT.
        Updates balance, keeps track of entry price and position status.
        
        Action Map Assuming:
        0: HOLD / WAIT
        1: BUY (Enter Long) / COVER
        2: SELL (Enter Short) / CLOSE
        
        Status Map:
        0: FLAT
        1: LONG
        2: SHORT
        """
        # Read current market data
        # Assuming Dataframe has 'close'
        current_price = StrategyLibrary._get_price(env, default=0.0)
        
        status = env._current_status
        fees = env.fees
        
        # NOTE: This logic assumes simplified action space where:
        # If FLAT: 1 -> LONG, 2 -> SHORT
        # If LONG: 2 -> FLAT (Close), 1 -> HOLD/ADD (simplified to Hold)
        # If SHORT: 1 -> FLAT (Close), 2 -> HOLD/ADD (simplified to Hold)
        # We can refine this mapping based on `action_labels` but for now we hardcode standard behavior.

        new_status = status
        
        if status == 0: # FLAT
            if action == 1: # GO LONG
                env._current_status = 1
                env.entry_price = current_price
                env.current_balance -= fees
            elif action == 2: # GO SHORT
                env._current_status = 2
                env.entry_price = current_price
                env.current_balance -= fees
        
        elif status == 1: # LONG
            if action == 2: # SELL (Close Long)
                pnl_pct = (current_price - env.entry_price) / env.entry_price
                # Profit = Invested * PnL
                # Simplified: We assume fixed trade size = 1 unit or we track PnL on balance directly?
                # For RL usually we track PnL on a hypothetical capital chunk or Full Balance.
                # Let's assume we invest 100% of current balance (Compounding) or Fixed Amount?
                # Let's use simple logic: PnL is applied to balance (assuming 1 unit leverage effectively or tracking points)
                # BETTER: Balance += InvestedAmount * PnL.
                # If we don't have Quantity, we can simulate generic performance.
                # Let's assume we bet 1000$ per trade or full balance.
                # Let's go with "Point based" balance for simplicity often used in simple Gyms:
                # Balance += (PriceDiff) - Fees? No, percentages are better.
                
                # Implementation: Apply % PnL to current balance.
                profit = env.current_balance * pnl_pct
                env.current_balance += profit - fees
                
                env._current_status = 0
                env.entry_price = 0
                
        elif status == 2: # SHORT
            if action == 1: # BUY (Cover Short)
                pnl_pct = (env.entry_price - current_price) / env.entry_price
                profit = env.current_balance * pnl_pct
                env.current_balance += profit - fees
                
                env._current_status = 0
                env.entry_price = 0

    # --- REWARD LOGIC (The "Judge") ---

    @staticmethod
    def simple_pnl_reward(env, action: int) -> float:
        """
        Calculates reward based on Realized PnL (on close) and small Unrealized PnL (for holding).
        """
        current_price = StrategyLibrary._get_price(env, default=0.0)
        status = env._current_status
        reward = 0.0
        
        # Check if we just closed a position (status changed could be tracked, 
        # but here we look at previous step status vs current? 
        # env.step calling execution_fn FIRST updates the status. 
        # So we have lost 'previous status'.
        # However, EnvFlex logic: Execution updates status. 
        # If we are FLAT now, but we WERE LONG, we realized PnL.
        
        # Alternative: Calculate reward based on Portfolio Value Delta.
        # This is the most robust RL metric: Reward = log(Vt / Vt-1)
        
        # We need previous balance. Env doesn't store previous balance in a variable explicitly accessible here easily
        # except via df history.
        
        prev_idx = env.current_step - 1
        prev_balance = env.df.at[prev_idx, 'balance'] if prev_idx >= 0 else env.initial_balance
        
        # Calculate change in Net Worth
        # Net Worth = Cash + Unrealized PnL
        
        def getIdelPnL(s, entry, curr):
            if s == 0: return 0.0
            if s == 1: return (curr - entry) / entry
            if s == 2: return (entry - curr) / entry
            return 0.0

        # Current Net Worth
        unrealized_pnl_pct = getIdelPnL(status, env.entry_price, current_price)
        # We assume invested amount is whole balance for this calc or fixed?
        # To be consistent with execution:
        # If we are in position, our "Equity" fluctuates.
        # If Execution fn updates balance ONLY on close, then 'env.current_balance' is CASH.
        
        # Equity = Cash + (Cash * UnrealizedPnL) roughly
        current_equity = env.current_balance * (1 + unrealized_pnl_pct)
        
        # Previous Equity
        # We'd need to reconstruct previous state.
        # This highlights why often Execution and Reward are tightly coupled or Reward needs more helper vars.
        
        # SIMPLER APPROACH for this iteration:
        # Reward = Realized PnL (if just closed) + Step Reward (small pnl if holding)
        
        # If we are FLAT (0) and we rely on 'current_balance' changes:
        delta_cash = env.current_balance - prev_balance
        if delta_cash != 0:
             # We realized something
             reward += delta_cash / prev_balance # % Return
        
        # Add unrealized component for shaping
        if status != 0:
            reward += unrealized_pnl_pct * 0.1 # Small factor to encourage holding winning trades
            
        return float(reward)

