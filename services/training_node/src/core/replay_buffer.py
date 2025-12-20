import numpy as np
import random
from typing import Tuple

class ReplayBuffer:
    """
    Experience Replay Buffer for storing transitions (s, a, r, s', d).
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = []
        self.position = 0

    def push(self, state, action, reward, next_state, done):
        """Saves a transition."""
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> Tuple[np.ndarray, ...]:
        batch = random.sample(self.buffer, batch_size)
        
        state, action, reward, next_state, done = map(np.stack, zip(*batch))
        return (
            state.astype(np.float32),
            action.astype(np.int32),
            reward.astype(np.float32),
            next_state.astype(np.float32),
            done.astype(bool)
        )

    def __len__(self):
        return len(self.buffer)
