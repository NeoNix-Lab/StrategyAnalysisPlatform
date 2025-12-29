# tests/test_replay_buffer.py
import numpy as np
from training_node.core.replay_buffer import ReplayBuffer

def test_push_and_len():
    buffer = ReplayBuffer(capacity=5)
    sample = (np.zeros((3,)), 1, 0.5, np.ones((3,)), False)
    # fai push di 5 esperienze
    for _ in range(5):
        buffer.push(*sample)
    assert len(buffer) == 5

def test_sample_returns_batch():
    buffer = ReplayBuffer(capacity=10)
    sample = (np.zeros((2,)), 1, 0.2, np.ones((2,)), False)
    # riempi con 10 elementi
    for _ in range(10):
        buffer.push(*sample)
    batch = buffer.sample(batch_size=4)
    # batch dovrebbe essere una tupla di cinque array/ liste
    assert isinstance(batch, tuple) and len(batch) == 5
    assert len(batch[0]) == 4  # primo elemento: lista di 4 stati
