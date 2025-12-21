
import pytest
import pandas as pd
import numpy as np
from src.training_node.environment import EnvFlex
from src.training_node.replay_buffer import ReplayBuffer
from src.training_node.utils import build_keras_model

# --- Fixtures ---

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "close": np.random.rand(100),
        "open": np.random.rand(100),
        "volume": np.random.rand(100)
    })

def dummy_reward(env, action):
    env.last_reward = 1.0

# --- Tests ---

def test_environment_initialization(sample_data):
    env = EnvFlex(sample_data, dummy_reward, window_size=10)
    state = env.reset()
    
    # State should include original cols + 5 status cols
    # (close, open, volume) + (step, balance, action, reward, pos_status) = 8
    expected_features = 3 + 5
    
    assert state.shape == (10, expected_features)
    assert env.current_step == 10

def test_environment_step(sample_data):
    env = EnvFlex(sample_data, dummy_reward, window_size=10)
    env.reset()
    
    # Action 1 = Long
    next_state, reward, done, _ = env.step(1)
    
    assert not done
    assert reward == 1.0
    assert env.last_action_name == "long"
    assert env.observation_dataframe.iloc[10]["action"] == 1
    
    # Check window sliding
    assert env.current_step == 11
    assert next_state.shape == (10, 8)

def test_replay_buffer():
    buffer = ReplayBuffer(capacity=100)
    
    # Push data
    state = np.zeros((10, 8))
    next_state = np.zeros((10, 8))
    buffer.push(state, 1, 0.5, next_state, False)
    
    assert len(buffer) == 1
    
    # Sample
    batch = buffer.sample(1)
    states, actions, rewards, _, _ = batch
    
    assert states.shape == (1, 10, 8)
    assert actions[0] == 1
    assert rewards[0] == 0.5

def test_build_keras_model():
    # Only run if TF installed
    try:
        import tensorflow as tf
    except ImportError:
        pytest.skip("TensorFlow not available")
        
    config = [
        {"type": "Dense", "units": 10, "activation": "relu"},
        {"type": "Dense", "units": 3}
    ]
    input_shape = (10, 8)
    
    model = build_keras_model(config, input_shape)
    assert isinstance(model, tf.keras.Model)
    assert len(model.layers) >= 3 # Input + 2 Dense
