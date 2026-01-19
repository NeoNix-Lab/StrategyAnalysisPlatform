
import sys
import os
import numpy as np
import tensorflow as tf
from unittest.mock import MagicMock

# Add ml_core to path
sys.path.append(os.path.abspath(r"d:\Documents\Active\StrategyAnalysisPlatform\Main\services\ml_core\src"))

from core.trainer import Trainer

# Mock classes
class MockEnv:
    def __init__(self):
        self.observation_space = MagicMock()
        self.observation_space.shape = (10, 5) # Window 10, 5 features
        self.action_space = MagicMock()
        self.action_space.n = 3
        self.action_space.sample.return_value = 0
        self.window_size = 10
        self.dataset = [1] * 100
        self.initial_balance = 1000
        self.current_balance = 1000
        self.n_actions = 3

    def reset(self):
        return np.zeros((10, 5))
    
    def step(self, action):
        return np.zeros((10, 5)), 1.0, False, {}
        
    def get_inference_log(self, price_column):
        return []

class MockModel:
    def __init__(self):
        self.window_size = 10
        self.optimizer = True
        self.trainable_variables = [tf.Variable([1.0])] # Need at least one var for gradient tape
    
    def __call__(self, inputs, training=False):
        # Return mock Q-values: (Batch, Actions)
        # inputs shape: (Batch, Window, Features)
        batch_size = tf.shape(inputs)[0]
        return tf.zeros((batch_size, 3))

    def extract_standard_keras_model(self, shape):
        return self
        
    def compile(self, optimizer, loss):
        pass
        
    def save(self, path):
        pass
        
    def set_weights(self, weights):
        pass
        
    def get_weights(self):
        return []

    def get_config(self):
        return {}
    
    @classmethod
    def from_config(cls, config):
        return cls()

def test_step_decay():
    print("Testing Step Decay...")
    env = MockEnv()
    model = MockModel()
    
    # Linear decay over 10 steps from 1.0 to 0.0
    # Decay per step = 0.1
    trainer = Trainer(
        env=env,
        main_network=model,
        optimizer=MagicMock(),
        loss_fn=MagicMock(),
        gamma=0.99,
        tau=0.01,
        epsilon_start=1.0,
        epsilon_end=0.0,
        epsilon_decay_steps=10,
        log_dir=".",
        training_name="test",
        decay_frequency='step'
    )
    
    initial_eps = trainer.epsilon
    trainer.epsilon_greedy_action(np.zeros((10, 5)))
    new_eps = trainer.epsilon
    
    print(f"Initial: {initial_eps}, After 1 step: {new_eps}")
    assert new_eps < initial_eps, "Epsilon should have decayed"
    expected = 1.0 - 0.1
    assert abs(new_eps - expected) < 0.0001, f"Expected {expected}, got {new_eps}"
    print("Step Decay Test Passed")

def test_episode_decay():
    print("\nTesting Episode Decay...")
    env = MockEnv()
    model = MockModel()
    
    # Linear decay over 10 steps (we assume these are 'episodes' in this context)
    trainer = Trainer(
        env=env,
        main_network=model,
        optimizer=MagicMock(),
        loss_fn=MagicMock(),
        gamma=0.99,
        tau=0.01,
        epsilon_start=1.0,
        epsilon_end=0.0,
        epsilon_decay_steps=10,
        log_dir=".",
        training_name="test",
        decay_frequency='episode'
    )
    
    # 1. Action should NOT decay epsilon
    trainer.epsilon_greedy_action(np.zeros((10, 5)))
    assert trainer.epsilon == 1.0, f"Epsilon should NOT decay on step in episode mode. Got {trainer.epsilon}"
    
    # 2. Simulate end of episode trigger
    trainer._decay_epsilon()
    
    assert trainer.epsilon < 1.0, "Epsilon SHOULD decay after episode end logic"
    print("Episode Decay Test Passed")

if __name__ == "__main__":
    try:
        test_step_decay()
        test_episode_decay()
        print("\nAll Tests Passed!")
    except Exception as e:
        print(f"\nTest Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
