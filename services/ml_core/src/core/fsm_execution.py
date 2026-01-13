from typing import List, Dict, Any, Optional

class FSMExecutionEngine:
    """
    Executes trading logic based on a Finite State Machine (FSM) Transition Matrix.
    Used to standardize execution across Training and Live environments.
    """
    def __init__(self, transition_matrix: Dict[str, Dict[str, Any]], action_labels: List[str], status_labels: List[str], price_column: str = "close"):
        """
        Args:
            transition_matrix: Nested dict {current_status: {action_label: {next_state, effect, update_price}}}
            action_labels: List of action names (index matches RL action)
            status_labels: List of status names (index matches RL state)
            price_column: Column name to use for price data (default: "close")
        """
        self.transition_matrix = transition_matrix
        self.action_labels = action_labels
        self.status_labels = status_labels
        self.price_column = price_column
        
        # Reverse lookup for speed
        self.status_map = {label: idx for idx, label in enumerate(status_labels)}
        self.action_map = {label: idx for idx, label in enumerate(action_labels)}

    def __call__(self, env, action_idx: int):
        """
        Refactored execution logic matching EnvFlex contract.
        
        Args:
            env: The EnvFlex instance (must expose .current_status, .entry_price, .current_balance, .fees)
            action_idx: The integer action chosen by the agent
        """
        # 1. Resolve Labels
        current_status_idx = env.current_status
        current_status_label = self.status_labels[current_status_idx]
        
        action_label = self.action_labels[action_idx]
        
        # 2. Get Current Price safely using configured column
        # env.data is the current row (dict-like)
        try:
            current_price = float(env.data.get(self.price_column, 0.0))
            if current_price == 0.0 and 'close' in env.data:
                 # Fallback
                 current_price = float(env.data['close'])
        except Exception:
            current_price = 0.0
            
        fees = getattr(env, 'fees', 0.0)

        # 3. Lookup Transition
        # Default to staying in same state if undefined
        state_transitions = self.transition_matrix.get(current_status_label, {})
        transition = state_transitions.get(action_label)
        
        # PnL Calculation Helpers
        def calc_pnl(entry, exit, size=1.0, short=False):
            if short:
                return (entry - exit) * size
            return (exit - entry) * size
            
        if not transition:
            # No transition -> No Op, but MUST update Unrealized PnL
            next_state_idx = current_status_idx
            effect = "NONE"
            update_price = False
        else:
            next_state_label = transition.get("next_state", current_status_label)
            effect = transition.get("effect", "NONE")
            update_price = transition.get("update_price", False)
            next_state_idx = self.status_map.get(next_state_label, current_status_idx)
        
        # 4. Apply Side Effects logic
        if effect == "APPLY_FEE":
            env.current_balance -= fees

        elif effect == "CLOSE_POS":
            # Realize PnL for Long
            qty = getattr(env, 'qty', 1.0)
            entry = env.entry_price
            
            gross_pnl = calc_pnl(entry, current_price, qty, short=False)
            env.current_balance += gross_pnl - fees
            # Reset
            env.qty = 0.0
            env.entry_price = 0.0

        elif effect == "CLOSE_SHORT":
            # Realize PnL for Short
            qty = getattr(env, 'qty', 1.0)
            entry = env.entry_price
            
            gross_pnl = calc_pnl(entry, current_price, qty, short=True)
            env.current_balance += gross_pnl - fees
            env.qty = 0.0
            env.entry_price = 0.0
            
        # 5. STATE UPDATE
        env.current_status = next_state_idx
        
        # 6. PRICE UPDATE
        if update_price:
            env.entry_price = current_price
            if getattr(env, 'qty', 0.0) == 0.0:
                env.qty = 1.0
                
        # 7. UNREALIZED PnL UPDATE (Moved from EnvFlex)
        # Calculate based on NEW status and NEW price (or current price if held)
        # Note: If we JUST closed, pnl is 0. If we effectively opened/held, calculate.
        if env.qty > 0 and env.entry_price > 0:
             # Heuristic: Status 1 is usually LONG, 2 is SHORT. 
             # Relies on labels? Better: Check if index maps to LONG/SHORT labels.
             # Simplified: Assume > 0 is open. Direction check via labels.
             current_label = self.status_labels[env.current_status]
             
             if "SHORT" in current_label.upper():
                  env.unrealized_pnl = calc_pnl(env.entry_price, current_price, env.qty, short=True)
             else:
                  env.unrealized_pnl = calc_pnl(env.entry_price, current_price, env.qty, short=False)
        else:
             env.unrealized_pnl = 0.0
