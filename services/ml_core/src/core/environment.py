# -*- coding: utf-8 -*-
"""
Gym environment for time-series decision-making with injected reward function.
Refactored for Training Node Microservice (no DB dependency).
"""

import gym
from gym import spaces
import numpy as np
import pandas as pd
from typing import Callable, List, Optional, Tuple, Dict
import copy

class EnvFlex(gym.Env):
    """
    Flexible Gym environment wrapping a pandas DataFrame for custom RL tasks.

    Observations are sliding windows over the DataFrame's features.
    The reward function is injected at initialization to allow architectural flexibility.
    """
    metadata = {'render.modes': ['human']}

    def __init__(
            self,
            data: pd.DataFrame,
            window_size: int,
            reward_fn: Callable,
            execution_fn: Callable,
            action_labels: List[str],
            status_labels: List[str],
            fees=0,
            initial_balance=100000,
            additional_columns = []
    ):
        """
        Initialize the EnvFlex environment.

        Args:
            data (pd.DataFrame): Full historical dataset (rows x features).
            window_size (int): Number of past timesteps in each observation.
            reward_fn (Callable[[EnvFlex, int], float]): Function to calculate reward based on updated state.
            execution_fn (Callable[[EnvFlex, int], None]): Function to execute trade logic and update state.
            action_labels (List[str]): Labels or keys for discrete actions.
            status_labels (List[str]): Labels for status.
            fees (float): Transaction fees.
            initial_balance (float): Starting capital.
            additional_columns (List[str]): Extra columns to include/track.
        """
    def __init__(
            self,
            data: pd.DataFrame,
            window_size: int,
            reward_fn: Callable,
            execution_fn: Callable,
            action_labels: List[str],
            status_labels: List[str],
            fees=0,
            initial_balance=100000,
            additional_columns = [],
            force_exit_map: Optional[dict] = None
    ):
        """
        Initialize the EnvFlex environment.

        Args:
            data (pd.DataFrame): Full historical dataset (rows x features).
            window_size (int): Number of past timesteps in each observation.
            reward_fn (Callable[[EnvFlex, int], float]): Function to calculate reward based on updated state.
            execution_fn (Callable[[EnvFlex, int], None]): Function to execute trade logic and update state.
            action_labels (List[str]): Labels or keys for discrete actions.
            status_labels (List[str]): Labels for status.
            fees (float): Transaction fees.
            initial_balance (float): Starting capital.
            additional_columns (List[str]): Extra columns to include/track.
        """
        super().__init__()
        self.dataset = data.reset_index(drop=True) # Rename to dataset
        self.window_size = window_size
        self.reward_fn = reward_fn
        self.execution_fn = execution_fn

        # Action space configured with provided labels
        self.action_labels = action_labels
        self.n_actions = len(action_labels)
        self.action_space = spaces.Discrete(self.n_actions)

        # Status space
        self.status_labels = status_labels
        self.n_status = len(status_labels)
        self.status_space = spaces.Discrete(self.n_status)

        self.additional_columns = additional_columns
        self.initial_balance = initial_balance
        self.fees = fees
        self.force_exit_map = force_exit_map or {} # Store map
        
        # State Tracking Variables (Mutable by execution_fn)
        self.current_balance = initial_balance
        self.entry_price = 0.0
        self._current_status = 0 # Internal integer status (0=Flat, 1=Long, etc.)
        self.qty = 0.0           # New: Track Quantity
        self.unrealized_pnl = 0.0 # New: Track Unrealized PnL
        
        # Prepare dataframes:
        self.feature_df, self.df = self._prepare_dataframes()
        
        # Observation space
        obs_shape = (self.window_size, len(self.feature_df.columns))
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=obs_shape,
            dtype=np.float32
        )

        self.current_step: int = self.window_size
        self.done = False

    # --- Contract Properties (Aliases) ---
    
    @property
    def data(self):
        """
        Contract: env.data should return the current observation row/dict.
        """
        try:
            return self.dataset.iloc[self.current_step]
        except IndexError:
            return {}

    @property
    def current_status(self):
        """Read-only property for backward compatibility / external access."""
        return self._current_status
    
    @current_status.setter
    def current_status(self, value):
        """Allow setting status directly."""
        self._current_status = value

    @property
    def position(self):
        """Alias matching API Validation MockEnv."""
        return self._current_status
    
    @position.setter
    def position(self, value):
        self._current_status = value

    @property
    def balance(self):
        """Alias matching API Validation MockEnv."""
        return self.current_balance

    @balance.setter
    def balance(self, value):
        self.current_balance = value

    # --- Data Access ---
    
    @property
    def data_row(self):
        """Legacy alias if needed"""
        return self.data

    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.
        """
        self.current_step = self.window_size
        self.current_balance = self.initial_balance
        self.entry_price = 0.0
        self._current_status = 0
        self.qty = 0.0
        self.unrealized_pnl = 0.0
        self.done = False
        return self._get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one time-step within the environment.
        """
        action_label = self.action_labels[action]

        # 1. REWARD PHASE (The "Judge") - MOVED BEFORE EXECUTION
        # User Request: Reward based on Pre-Update state and Current Data
        try:
            reward = self.reward_fn(self, action)
        except Exception as e:
            # print(f"Reward calc error: {e}")
            reward = 0.0

        # 2. EXECUTION PHASE (The "Physics")
        # Update internal state (balance, status, entry_price) based on action
        try:
            # Inject dynamic namespaces if not present
            if not hasattr(self, 'data_accessor_injected'):
                pass 
                
            self.execution_fn(self, action)
        except Exception as e:
            print(f"Execution Logic Error: {e}")

        # 3. OBSERVATION PHASE
        # Get obs for the NEXT step (conceptually), or just current window
        obs = self._get_observation()

        # 5. LOGGING PHASE
        # Record state to DataFrame history
        if self.current_step < len(self.df):
            self.df.at[self.current_step, 'action'] = action
            self.df.at[self.current_step, 'reword'] = reward
            self.df.at[self.current_step, 'balance'] = self.current_balance
            self.df.at[self.current_step, 'position_status'] = self._current_status
           
            
            # Optional: Log entry price if column exists
            if 'entry_price' in self.df.columns:
                 self.df.at[self.current_step, 'entry_price'] = self.entry_price

        # Advance step
        self.current_step += 1
        self.done = self.current_step >= len(self.df)
        
        # Force Exit Logic at Episode End
        if self.done and self.force_exit_map:
            # Check if current status has a forced exit action
            exit_action = self.force_exit_map.get(self._current_status)
            if exit_action is not None:
                try:
                    # Execute the forced action (e.g., Close Position)
                    # We do NOT calculate reward here for the agent's updated policy (it's too late),
                    # but we DO execution to realize PnL for logging/metrics.
                    self.execution_fn(self, exit_action)
                    
                    # Optional: Log this final "cleanup" step? 
                    # If we want to see the closure in logs, we might need a virtual extra step 
                    # or just update the last step's stats (balance/status) in place.
                    # Current decision: Update internal state so it reflects in final metrics (Total PnL).
                except Exception as e:
                    print(f"Force Exit Error: {e}")

        if not self.done:
            next_obs = self._get_observation()
        else:
            next_obs = np.zeros(self.observation_space.shape, dtype=np.float32)

        # Optimization: Return the actual DF row (converted to dict)
        # This contains both features and logged state (action, balance, etc.)
        info = {}
        try:
             # We use current_step (already incremented)
             if self.current_step < len(self.df):
                 info = self.df.iloc[self.current_step].to_dict()
                 
        except Exception:
             pass
        
        return next_obs, reward, self.done, info

    def get_inference_log(self, price_column: str = "close") -> list:
        """
        Efficiently retrieve the reconstruction history from the internal DataFrame.
        This avoids manual collection in the Trainer loop.
        """
        # Columns to export
        target_cols = [
            "timestamp", 
            price_column, 
            "step", "action", "reword", "balance", 
            "position_status", "entry_price"
        ]
        
        # Ensure columns exist
        final_cols = []
        rename_map = {}
        
        for col in target_cols:
            if col in self.df.columns:
                final_cols.append(col)
                if col == price_column: 
                    rename_map[col] = "price"
                if col == "reword":
                    rename_map[col] = "reward"
            # REMOVED: Silent fallback to "close". 
            # We respect the User's choice. If 'price_column' is missing, 
            # the specialized 'price' field will be missing in the log, 
            # alerting the user to a config error rather than hiding it.
            
        # Filter rows up to current_step
        valid_range = self.df.iloc[:self.current_step + 1]
        
        # Export to records
        records = valid_range[final_cols].rename(columns=rename_map).to_dict(orient="records")
        
        # Feature: Support Index as Timestamp if column is missing
        if "timestamp" not in final_cols:
            import pandas as pd
            if isinstance(self.df.index, pd.DatetimeIndex):
                # Inject index as timestamp
                # Since we sliced valid_range, the index is preserved
                valid_indices = valid_range.index
                for i, rec in enumerate(records):
                    rec["timestamp"] = valid_indices[i].isoformat()
        
        return records

    def _get_observation(self) -> np.ndarray:
        """
        Get the current sliding window observation.
        Returns a VIEW of the pre-allocated numpy array to save memory.
        """
        start = self.current_step - self.window_size
        end = self.current_step
        
        # Ensure we don't go out of bounds (should happen only at start if not handled)
        if start < 0:
             # Padding if needed (though we start at window_size usually)
             padding = np.zeros((abs(start), self.data_array.shape[1]), dtype=np.float32)
             # Use a slice that doesn't go below 0
             actual = self.data_array[0:end]
             return np.concatenate([padding, actual], axis=0)
            
        # Return a view (slice) of the big array
        return self.data_array[start:end]

    def _prepare_dataframes(self):
        """
        Prepare the internal DataFrames and pre-convert to Float32 Numpy Array.
        """
        base_df = self.dataset.copy()
        length = len(base_df)

        if self.additional_columns:
            for col in self.additional_columns:
                base_df[col] = np.zeros(length)
        
        # Keep DF for debugging/metadata if needed, but use Array for core RL loop
        self.feature_df = base_df.copy() # Legacy support if needed
        
        # OPTIMIZATION: Convert entire feature set to Float32 Array once.
        # This prevents creating new copies in _get_observation
        self.data_array = base_df.values.astype(np.float32)
        
        df = base_df.copy()

        # Add tracking columns
        df['step'] = np.zeros(length)
        df['balance'] = np.zeros(length)
        df['action'] = np.zeros(length)
        df['reword'] = np.zeros(length)
        df['position_status'] = np.zeros(length)
        df['entry_price'] = np.zeros(length) # Helpful for debugging

        return self.feature_df, df
