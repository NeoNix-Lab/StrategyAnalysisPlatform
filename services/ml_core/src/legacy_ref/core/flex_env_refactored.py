# -*- coding: utf-8 -*-
"""
Gym environment for time-series decision-making with injected reward function.
"""

# TODO: definire altri stati interni come equity, pnl, trade_count
# TODO: inizializzare pienamente tutti gli stati nello __init__
# TODO: preferire custom Exception (NotInitializedError)
# TODO: usare assert in step() per garantire stato valido prima dell’uso
# TODO: aggiungere logging con modulo logging o callback specifici RL
# TODO: inserire metriche extra (drawdown, trade_count, pnl) in info
# TODO: implementare test unitari con pytest / unittest:
#       - test balance property prima di reset lancia NotInitializedError
#       - test reset() inizializza stati
#       - test step() aggiorna balance, reward, obs corretti
# TODO: se userai SB3/SB3, creare callback per loggare balance/position su TensorBoard
# TODO: validare che obs restituito rispetti observation_space.contains()
# TODO: considerare extractor o wrapper custom se in futuro aggiungi input extra al modello
# TODO: se espandi a Dict obs space, aggiornare network input_shape o usare wrapper appropriate


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
            data (pd.DataFrame): Full historical dataset (rows × features).
            window_size (int): Number of past timesteps in each observation.
            reward_fn (Callable[[np.ndarray, int], float]): Function(state_window, action_index) -> reward.
            action_labels (List[str]): Labels or keys for discrete actions.
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

        # Action space configured with provided labels
        self.status_labels = status_labels
        self.n_status = len(status_labels)
        self.status_space = spaces.Discrete(self.n_status)

        # Observation: sliding window of features
        obs_shape = (self.window_size, len(self.data.columns))
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=obs_shape,
            dtype=np.float32
        )

        self.current_step: int = self.window_size

        # Variabili Immutate
        self.last_qty_both = 0
        self.fees = fees
        self.current_step = 0
        self.done = False
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.additional_columns = additional_columns

        self.Obseravtion_DataFrame = self._set_df_obs()

    @property
    def current_status(self):
        try:
            return self.Obseravtion_DataFrame[self.current_step, "position_status"]
        except Exception as ex:
            raise ex

    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.

        Returns:
            np.ndarray: Initial observation window.
        """
        self.current_step = self.window_size
        return self._get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one time-step within the environment.

        Args:
            action (int): Index of the action to take.

        Returns:
            next_obs (np.ndarray): Next state window.
            reward (float): Reward from injected reward function.
            done (bool): Whether the episode is complete.
            info (dict): Additional info including action label and step index.
        """
        obs = self._get_observation()
        reward = self.reward_fn(obs, action)
        action_label = self.action_labels[action]

        # Advance step
        self.current_step += 1
        self.done = self.current_step >= len(self.data)
        next_obs = self._get_observation() if not self.done else np.zeros_like(obs)

        info = {
            'action_label': action_label,
            'step': self.current_step,
            'balance': self.current_balance,
            'position status': self.current_status
        }
        return next_obs, reward, self.done, info

    def _get_observation(self) -> np.ndarray:
        """
        Get the current sliding window observation.

        Returns:
            np.ndarray: Array shape (window_size, n_features).
        """
        start = self.current_step - self.window_size
        end = self.current_step
        window = self.data.iloc[start:end][self.data.columns].values
        return window.astype(np.float32)

    def encode_status(self, status_label: str):
        """
       Map an action label to its integer index.

       Args:
           status_label (str): Label corresponding to a status.

       Returns:
           int: Status index in the status space.
       """
        return self.status_labels.index(status_label)

    def decode_status(self, status: int):
        return self.status_space.

    def encode_action(self, action_label: str) -> int:
        """
        Map an action label to its integer index.

        Args:
            action_label (str): Label corresponding to an action.

        Returns:
            int: Action index in the action space.
        """
        return self.action_labels.index(action_label)

    def count_actions(self) -> Dict[str, int]:
        """
        Count the frequency of each action taken so far.

        Returns:
            Dict[str, int]: Mapping from action label to count.
        """
        # Placeholder: implement tracking in step if needed
        return {label: 0 for label in self.action_labels}

    def update_window_size(self, new_size: int) -> None:
        """
        Update the window size for observations.

        Args:
            new_size (int): New number of timesteps per observation.
        """
        self.window_size = new_size
        obs_shape = (self.window_size, len(self.data.columns))
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=obs_shape,
            dtype=np.float32
        )

    def render(self, mode: str = 'human') -> None:
        """
        Render the environment. No-op by default.

        Args:
            mode (str): Mode of rendering.
        """
        pass

    def close(self) -> None:
        """
        Perform any cleanup. No-op by default.
        """
        pass

    def _set_df_obs(self):
        lenght = len(self.data.iloc[:,0])

        self.Obseravtion_DataFrame = copy.deepcopy(self.data)

        if len(self.additional_columns) > 0:
            for i in range(len(self.additional_columns)):

                new_df = pd.DataFrame({
                    f'{self.additional_columns[i]}' : np.zeros(lenght)})

                self.Obseravtion_DataFrame = pd.concat([self.Obseravtion_DataFrame, new_df], axis=1)


        classic_DF = pd.DataFrame({
            'step': np.zeros(lenght),
            'balance': np.zeros(lenght),
            'action': np.zeros(lenght),
            'reword': np.zeros(lenght),
            'position_status': np.zeros(lenght)})

        return pd.concat([self.Obseravtion_DataFrame, classic_DF], axis=1)