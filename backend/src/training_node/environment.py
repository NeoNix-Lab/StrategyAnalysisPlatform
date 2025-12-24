
import gym
from gym import spaces
import numpy as np
import pandas as pd
import copy
from typing import Callable, List, Tuple, Any

class EnvFlex(gym.Env):
    """
    Evolved Environment for RL Trading.
    Ported from `rl_rnn_core` and adapted for StrategyAnalysisPlatform.
    
    This environment operates on a pre-loaded Pandas DataFrame containing market data
    and features. It simulates a trading process by stepping through the DataFrame.
    """
    
    def __init__(self, 
                 df_data: pd.DataFrame, 
                 reward_function: Callable[[Any, int], None], 
                 window_size: int = 20, 
                 fees: float = 0.01, 
                 initial_balance: float = 100000.0,
                 action_labels: List[str] = None,
                 status_labels: List[str] = None):
        
        super(EnvFlex, self).__init__()
        
        self.data = df_data.reset_index(drop=True)
        self.reward_function = reward_function
        self.window_size = window_size
        self.fees = fees
        self.initial_balance = initial_balance
        
        # Namespace Injection
        self.action_labels = action_labels or ["HOLD", "BUY", "SELL"]
        self.status_labels = status_labels or ["FLAT", "LONG", "SHORT"]
        
        # Create Enum-like objects dynamically
        class Namespace: pass
        
        self.actions = Namespace()
        for idx, label in enumerate(self.action_labels):
            setattr(self.actions, label.upper(), idx)
            
        self.status = Namespace()
        for idx, label in enumerate(self.status_labels):
            setattr(self.status, label.upper(), idx)
        
        # State Variables
        self.current_step = 0
        self.current_balance = initial_balance
        self.done = False
        
        # Trading State
        self.qty = 1.0 # Default fixed quantity for ML training
        self.entry_price = 0.0
        self.position_size = 0 # Signed size (+1, -1, 0)
        
        # Tracking
        self.last_action_name = 'wait' # 0=wait, 1=long, 2=short
        self.last_position_status = 'flat' # flat, long, short
        self.last_reward = 0.0
        
        self.window = pd.DataFrame() 
        self.observation_dataframe = pd.DataFrame() 
        
        # Action Space: 0=Wait, 1=Long, 2=Short
        self.action_space = spaces.Discrete(3)
        
        # Observation Space
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        n_features = len(numeric_cols) + 5 
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(window_size, n_features), dtype=np.float32)

        self.reset()

    @property
    def position(self):
        """Returns the current position status index (0=Flat, 1=Long, 2=Short)."""
        return self._position_idx
        
    @property
    def unrealized_pnl(self):
        """Calculates unrealized PnL based on current close price."""
        if self._position_idx == 0:
            return 0.0
            
        current_price = self.data.at[self.current_step, 'close']
        if self._position_idx == 1: # Long
            return (current_price - self.entry_price) * self.qty
        elif self._position_idx == 2: # Short
            return (self.entry_price - current_price) * self.qty
        return 0.0

    @property
    def balance(self):
        """Alias for current_balance to match Frontend UI hints."""
        return self.current_balance

    @property
    def pnl(self):
        """Alias for unrealized_pnl."""
        return self.unrealized_pnl

    def reset(self):
        """Resets the environment."""
        self.current_step = 0
        self.current_balance = self.initial_balance
        self.done = False
        self.last_action_name = 'wait'
        self._position_idx = 0 
        self.last_reward = 0.0
        
        self.entry_price = 0.0
        self.position_size = 0
        
        # Initialize Observation DataFrame
        self.observation_dataframe = self.data.copy()
        n_rows = len(self.observation_dataframe)
        self.observation_dataframe['step'] = np.arange(n_rows)
        self.observation_dataframe['balance'] = np.full(n_rows, self.initial_balance)
        self.observation_dataframe['action'] = np.zeros(n_rows) 
        self.observation_dataframe['reward'] = np.zeros(n_rows)
        self.observation_dataframe['position_status'] = np.zeros(n_rows)
        
        self.current_step = self.window_size 
        self._update_window()
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        if self.done:
            return self._get_state(), 0.0, True, {}
        
        # 1. Map Action
        action_name = self._decode_action(action)
        self.last_action_name = action_name
        current_price = self.data.at[self.current_step, 'close']
        
        # 2. Update Position Logic (Simplified State Machine)
        # 0=WAIT/FLAT, 1=LONG, 2=SHORT
        
        # If we are FLAT
        if self._position_idx == 0:
            if action == 1: # Open Long
                self._position_idx = 1
                self.entry_price = current_price
                self.position_size = 1
            elif action == 2: # Open Short
                self._position_idx = 2
                self.entry_price = current_price
                self.position_size = -1
                
        # If we are LONG
        elif self._position_idx == 1:
            if action == 2: # Close Long / Reverse Short?
                # For simplicity in this env, Action 2 closes position. 
                # Or we can treat it as "Switch to Short". Let's say it Closes for now to match classic simple RL.
                # Actually, standard is usually: 0=Hold, 1=Buy, 2=Sell.
                # If Long + Sell -> Flat.
                # If Long + Buy -> Add? (Ignore for simple env)
                self._position_idx = 0
                self.entry_price = 0.0
                self.position_size = 0
                
        # If we are SHORT
        elif self._position_idx == 2:
            if action == 1: # Buy to Cover
                self._position_idx = 0
                self.entry_price = 0.0
                self.position_size = 0

        # Note: The above is a very subtle "Mode". 
        # Often RL uses: 0=Neutral/Hold, 1=Long, 2=Short directly forcing the state?
        # Let's stick to the previous implementation which seemed to Force State:
        # "if action == 1: self._position_idx = 1"
        # The user's code implies: if action==1 (BUY) -> if position==0 -> Open Long.
        # Let's revert to the Direct Mapping because it's what the environment.py did originally.
        # Original: if action == 1: pos=1. if action==2: pos=2.
        # But we need to track entry_price!
        
        old_position = self._position_idx
        if action == 1: # Want to be LONG
            if old_position != 1:
                self._position_idx = 1
                self.entry_price = current_price # New Entry (or Reversal)
        elif action == 2: # Want to be SHORT
            if old_position != 2:
                self._position_idx = 2
                self.entry_price = current_price
        # Action 0 = Hold whatever we have.
        
        # 3. Calculate Reward
        try:
            # [DEBUG] Inspect what code is actually running
            # import inspect
            # print(f"[DEBUG CODE] {inspect.getsource(self.reward_function)}")
            
            self.reward_function(self, action)
        except AttributeError as e:
            print(f"Reward Function Error: {e}")
            raise e
        
        # 4. Check Termination
        if self.current_step >= len(self.data) - 1:
            self.done = True
        
        # 5. Record State
        idx = self.current_step
        self.observation_dataframe.at[idx, 'balance'] = self.current_balance
        self.observation_dataframe.at[idx, 'action'] = action
        self.observation_dataframe.at[idx, 'reward'] = self.last_reward
        self.observation_dataframe.at[idx, 'position_status'] = self._position_idx

        # 6. Advance
        self.current_step += 1
        self._update_window()
        
        return self._get_state(), self.last_reward, self.done, {}

    def _update_window(self):
        """Updates the sliding window of data."""
        if self.current_step < self.window_size:
            return
            
        start = self.current_step - self.window_size
        end = self.current_step
        self.window = self.observation_dataframe.iloc[start:end]

    def _get_state(self):
        """Returns the current state (window) as a numpy array."""
        # Ensure we only return numeric data
        return self.window.select_dtypes(include=[np.number]).values

    def _decode_action(self, action_id):
        if action_id == 0: return 'wait'
        if action_id == 1: return 'long'
        if action_id == 2: return 'short'
        return 'wait'

    def render(self, mode='human'):
        pass
