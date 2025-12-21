
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
        
        # Tracking
        self.last_action_name = 'wait' # 0=wait, 1=long, 2=short
        self.last_position_status = 'flat' # flat, long, short
        self.last_reward = 0.0
        
        self.window = pd.DataFrame() # The current observation window
        self.observation_dataframe = pd.DataFrame() # Full history of the episode
        
        # Action Space: 0=Wait, 1=Long, 2=Short
        self.action_space = spaces.Discrete(3)
        
        # Observation Space: Defined dynamically based on dataframe columns
        # We'll use a Box space for now, assuming normalized features
        n_features = len(self.data.columns) + 5 # features + internal stateCols
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(window_size, n_features), dtype=np.float32)

        self.reset()

    @property
    def position(self):
        """
        Returns the current position status index.
        Matches env.status constants (e.g. FLAT=0, LONG=1, SHORT=2).
        """
        return self._position_idx

    def reset(self):
        """Resets the environment to the beginning of the episode."""
        self.current_step = 0
        self.current_balance = self.initial_balance
        self.done = False
        self.last_action_name = 'wait'
        self._position_idx = 0 # 0=FLAT default
        self.last_reward = 0.0
        
        # Initialize Observation DataFrame
        # We keep a copy of data and append state columns
        self.observation_dataframe = self.data.copy()
        
        # Append discrete state columns initialized to 0
        n_rows = len(self.observation_dataframe)
        self.observation_dataframe['step'] = np.arange(n_rows)
        self.observation_dataframe['balance'] = np.full(n_rows, self.initial_balance)
        self.observation_dataframe['action'] = np.zeros(n_rows) # encoded
        self.observation_dataframe['reward'] = np.zeros(n_rows)
        self.observation_dataframe['position_status'] = np.zeros(n_rows) # encoded
        
        # Initialize the first window (padding with first row if needed, or starting at window_size)
        # For simplicity in this port, we start at window_size
        self.current_step = self.window_size 
        
        self._update_window()
        
        return self._get_state()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Executes one step in the environment.
        action: 0=Wait, 1=Buy/Long, 2=Sell/Short
        """
        if self.done:
            return self._get_state(), 0.0, True, {}
        
        # 1. Map Action to internal state
        action_name = self._decode_action(action)
        self.last_action_name = action_name
        
        # 2. Update Position Status based on Action (Simplified logic)
        # Assumes Actions: 0=HOLD, 1=LONG, 2=SHORT
        # Assumes Status: 0=FLAT, 1=LONG, 2=SHORT
        if action == 1: # Long
            self._position_idx = 1
        elif action == 2: # Short
            self._position_idx = 2
        elif action == 0: # Wait/Hold
             pass 

        # 3. Calculate Reward using the injected strategy
        # The strategy function is responsible for updating self.last_reward
        # and potentially modifying self.current_balance or done status
        try:
            self.reward_function(self, action)
        except AttributeError as e:
            # Fallback/Helpful error
            print(f"Reward Function Error: {e}")
            raise e
        
        # 4. Check Termination
        if self.current_step >= len(self.data) - 1:
            self.done = True
        
        # 5. Record State in Observation DataFrame
        idx = self.current_step
        self.observation_dataframe.at[idx, 'balance'] = self.current_balance
        self.observation_dataframe.at[idx, 'action'] = action
        self.observation_dataframe.at[idx, 'reward'] = self.last_reward
        self.observation_dataframe.at[idx, 'position_status'] = self._position_idx

        # 6. Advance Step
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
