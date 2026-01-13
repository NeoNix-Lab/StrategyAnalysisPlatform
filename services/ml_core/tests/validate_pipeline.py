
import logging
import numpy as np
import pandas as pd
import tensorflow as tf
import os
import shutil

from src.core.environment import EnvFlex
from src.core.models import CustomDQNModel
from src.core.trainer import Trainer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger("ML_VALIDATION")

def generate_dummy_data(n_rows=1000):
    logger.info(f"Generating {n_rows} rows of dummy market data...")
    dates = pd.date_range(start='2024-01-01', periods=n_rows, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(n_rows).cumsum() + 100,
        'high': np.random.randn(n_rows).cumsum() + 105,
        'low': np.random.randn(n_rows).cumsum() + 95,
        'close': np.random.randn(n_rows).cumsum() + 100,
    })
    # Add scalar columns often used in features
    df['volume'] = np.random.randint(100, 1000, n_rows)
    df['rsi'] = np.random.uniform(0, 100, n_rows)
    df['macd'] = np.random.randn(n_rows)
    
    logger.info("Data generation complete.")
    print(df.head(15))
    return df

def mock_execution_fn(env, action):
    """
    Simulated Execution Logic (The 'Physics').
    Updates: _current_status, entry_price, current_balance.
    """
    # Standard: Action 0=HOLD, 1=BUY, 2=SELL
    status = env._current_status
    price = env.data.iloc[env.current_step]['close']
    
    # Simple State Machine
    if status == 0: # FLAT
        if action == 1: # BUY
            env._current_status = 1
            env.entry_price = price
            env.current_balance -= 1.0 # Fee
        elif action == 2: # SHORT
            env._current_status = 2
            env.entry_price = price
            env.current_balance -= 1.0 # Fee
            
    elif status == 1: # LONG
        if action == 2: # SELL (Close)
            pnl_pct = (price - env.entry_price) / env.entry_price
            profit = env.current_balance * pnl_pct
            env.current_balance += profit
            env._current_status = 0
            env.entry_price = 0.0

    elif status == 2: # SHORT
        if action == 1: # BUY (Cover)
            pnl_pct = (env.entry_price - price) / env.entry_price
            profit = env.current_balance * pnl_pct
            env.current_balance += profit
            env._current_status = 0
            env.entry_price = 0.0

def mock_reward_fn(env, action):
    """
    Simulated Reward Logic.
    """
    # Random placeholder reward
    return float(np.random.normal(0, 1))

def validate_pipeline():
    logger.info("=== STARTING REAL ML PIPELINE VALIDATION (Real TF) ===")
    
    # 0. Cleanup previous logs
    if os.path.exists("./logs_validation"):
        shutil.rmtree("./logs_validation")

    # 1. Data Preparation
    df = generate_dummy_data()
    # EnvFlex expects numeric data for observations. Drop non-numeric.
    if 'timestamp' in df.columns: 
        df = df.drop(columns=['timestamp'])

    # 2. Configuration
    window_size = 10
    action_labels = ["HOLD", "BUY", "SELL"]
    status_labels = ["FLAT", "LONG", "SHORT"]
    
    # 3. Environment Initialization
    logger.info("Initializing EnvFlex...")
    env = EnvFlex(
        data=df,
        window_size=window_size,
        reward_fn=mock_reward_fn,
        execution_fn=mock_execution_fn,
        action_labels=action_labels,
        status_labels=status_labels,
        initial_balance=10000.0,
        fees=1.0
    )
    
    obs = env.reset()
    logger.info(f"Env Reset. Observation shape: {obs.shape}")
    assert obs.shape[0] == window_size
    
    # 4. Model Construction
    logger.info("Constructing CustomDQNModel (STRESS TEST MODE)...")
    # Architecture Definition - Increased for CPU Load
    model_config = [
        {"type": "Dense", "units": 512, "activation": "relu"},
        {"type": "Dense", "units": 256, "activation": "relu"},
        {"type": "Dense", "units": 128, "activation": "relu"},
        {"type": "Dense", "units": len(action_labels), "activation": "linear"}
    ]
    
    model = CustomDQNModel(
        architecture_config=model_config,
        input_shape=window_size,
        name="RealValidationModel"
    )
    
    # Build the model by passing a dummy input (Standard Keras practice)
    # The CustomDQNModel auto-builds layers in init, but Keras builds graph on first call
    dummy_input = np.zeros((1, window_size, obs.shape[1]))
    model(dummy_input) 
    model.summary(print_fn=logger.info)

    # 5. Trainer Initialization
    logger.info("Initializing Trainer...")
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    loss_fn = tf.keras.losses.MeanSquaredError()
    
    trainer = Trainer(
        env=env,
        main_network=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        gamma=0.99,
        tau=0.005,
        epsilon_start=1.0,
        epsilon_end=0.1, 
        epsilon_decay_steps=500,
        log_dir="./logs_validation",
        training_name="ValidationRun",
        epochs=1,
        replay_capacity=5000,
        log_every_steps=100
    )
    
    # 6. Execution Loop
    logger.info("Starting Training Loop (5 Episodes, BS=1024)...")
    try:
        trainer.train(num_episodes=5, batch_size=1024)
        logger.info("=== VALIDATION COMPLETE: SUCCESS ===")
    except Exception as e:
        logger.error("Validation Failed during training loop.", exc_info=True)
        raise e

if __name__ == "__main__":
    validate_pipeline()
