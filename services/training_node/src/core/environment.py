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
            reward_fn: Callable[[np.ndarray, int], float],
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
            reward_fn (Callable[[np.ndarray, int], float]): Function(state_window, action_index) -> reward.
            action_labels (List[str]): Labels or keys for discrete actions.
            status_labels (List[str]): Labels for status.
            feature_columns (List[str], optional): List of column names to use for observations; defaults to all.
        """
        super().__init__()
        self.data = data.reset_index(drop=True)
        self.window_size = window_size
        self.reward_fn = reward_fn

        # Action space configured with provided labels
        self.action_labels = action_labels
        self.n_actions = len(action_labels)
        self.action_space = spaces.Discrete(self.n_actions)

        # Status space
        self.status_labels = status_labels
        self.n_status = len(status_labels)
        self.status_space = spaces.Discrete(self.n_status)

        # Observation: sliding window of features
        # Note: We need to account for additional columns in the observation shape calculation
        # The constructor calls _set_df_obs which adds columns to self.Obseravtion_DataFrame.
        # However, _get_observation uses self.data.
        # Refactoring note: The original code had a confusion between self.data and self.Obseravtion_DataFrame.
        # _get_observation used self.data.iloc..., but _set_df_obs created self.Obseravtion_DataFrame.
        # We will unify this. self.df will be the working dataframe.
        
        self.additional_columns = additional_columns
        self.initial_balance = initial_balance
        self.fees = fees
        self.current_balance = initial_balance
        
        # Prepare the full DataFrame (features + tracked states)
        self.df = self._prepare_dataframe()
        
        # Observation space
        obs_shape = (self.window_size, len(self.df.columns))
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=obs_shape,
            dtype=np.float32
        )

        self.current_step: int = self.window_size
        self.last_qty_both = 0
        self.done = False

    @property
    def current_status(self):
        try:
            # Safe access to 'position_status' column if it exists
            if 'position_status' in self.df.columns:
                return self.df.at[self.current_step, "position_status"]
            return 0
        except Exception:
            return 0

    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.

        Returns:
            np.ndarray: Initial observation window.
        """
        self.current_step = self.window_size
        self.current_balance = self.initial_balance
        self.done = False
        return self._get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one time-step within the environment.
        """
        obs = self._get_observation()
        
        # Calculate Reward
        # Note: reward_fn might expect raw numpy array or something specific. 
        # In original code: reward = self.reward_fn(obs, action)
        try:
            reward = self.reward_fn(obs, action)
        except Exception as e:
            # Fallback if reward function fails (e.g. strict type checks)
            # print(f"Reward calc error: {e}")
            reward = 0.0

        action_label = self.action_labels[action]

        # Record action/reward in DF (optional, for debugging/analysis)
        if self.current_step < len(self.df):
            self.df.at[self.current_step, 'action'] = action
            self.df.at[self.current_step, 'reword'] = reward
            self.df.at[self.current_step, 'balance'] = self.current_balance

        # Advance step
        self.current_step += 1
        self.done = self.current_step >= len(self.df)
        
        if not self.done:
            next_obs = self._get_observation()
        else:
            next_obs = np.zeros(self.observation_space.shape, dtype=np.float32)

        info = {
            'action_label': action_label,
            'step': self.current_step,
            'balance': self.current_balance,
            'position_status': self.current_status
        }
        
        # Returning 4 values to maintain compatibility with existing Trainer code
        return next_obs, reward, self.done, info

    def _get_observation(self) -> np.ndarray:
        """
        Get the current sliding window observation.
        """
        start = self.current_step - self.window_size
        end = self.current_step
        # Ensure we don't go out of bounds
        if start < 0: 
            return np.zeros(self.observation_space.shape, dtype=np.float32)
            
        window = self.df.iloc[start:end].values
        return window.astype(np.float32)

    def _prepare_dataframe(self):
        """
        Prepare the internal DataFrame with additional columns for tracking.
        """
        df = self.data.copy()
        length = len(df)

        if self.additional_columns:
            for col in self.additional_columns:
                df[col] = np.zeros(length)

        # Add tracking columns
        df['step'] = np.zeros(length)
        df['balance'] = np.zeros(length)
        df['action'] = np.zeros(length)
        df['reword'] = np.zeros(length)
        df['position_status'] = np.zeros(length)
        
        return df
