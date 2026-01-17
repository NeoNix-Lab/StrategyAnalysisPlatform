"""
Replay buffer module for experience storage in reinforcement learning.
"""

import random
from collections import deque
from typing import Any, Deque, Optional, Tuple
import numpy as np


class ReplayBuffer:
    """
    Experience replay buffer for reinforcement learning agents.

    Stores tuples of (state, action, reward, next_state, done) up to a fixed capacity.
    Provides methods to add experiences and sample random batches.
    """

    def __init__(self, capacity: int) -> None:
        """
        Initialize the replay buffer.

        Args:
            capacity (int): Maximum number of experiences to store.
        """
        self.capacity: int = capacity
        self.buffer: Deque[Tuple[np.ndarray, Any, float, np.ndarray, bool]] = deque(maxlen=capacity)

    def push(
            self,
            state: np.ndarray,
            action: Any,
            reward: float,
            next_state: np.ndarray,
            done: bool
    ) -> None:
        """
        Add a new experience to the buffer.

        Args:
            state (np.ndarray): Observed state.
            action (Any): Action taken.
            reward (float): Reward received.
            next_state (np.ndarray): Next observed state.
            done (bool): Whether the episode terminated.
        """
        self.buffer.append((state, action, reward, next_state, done))

    def sample(
            self,
            batch_size: int
    ) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
        """
        Sample a random batch of experiences.

        Args:
            batch_size (int): Number of experiences to sample.

        Returns:
            Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
                A tuple containing (states, actions, rewards, next_states, dones),
                or None if there are fewer than batch_size experiences stored.
        """
        if len(self.buffer) < batch_size:
            return None

        indices = random.sample(range(len(self.buffer)), batch_size)
        batch = [self.buffer[i] for i in indices]

        states = np.stack([exp[0] for exp in batch])
        actions = np.array([exp[1] for exp in batch])
        rewards = np.array([exp[2] for exp in batch], dtype=np.float32)
        next_states = np.stack([exp[3] for exp in batch])
        dones = np.array([exp[4] for exp in batch], dtype=np.bool_)

        return states, actions, rewards, next_states, dones

    def __len__(self) -> int:
        """
        Return the current number of stored experiences.

        Returns:
            int: Number of experiences in the buffer.
        """
        return len(self.buffer)

    def clear(self) -> None:
        """
        Remove all experiences from the buffer.
        """
        self.buffer.clear()
