import os
import sys
import json
import uuid
import logging
from datetime import datetime

# Add paths to sys.path
PROJECT_ROOT = "d:/Documents/Active/StrategyAnalysisPlatform/Main"
sys.path.append(os.path.join(PROJECT_ROOT, "packages/quant_shared/src"))
sys.path.append(os.path.join(PROJECT_ROOT, "services/ml_core/src"))

from quant_shared.models.connection import get_db, init_db, DB_PATH
from quant_shared.models.models import (
    User, MlRewardFunction, MlModelArchitecture, MlTrainingProcess, 
    MlTrainingSession, Dataset
)
from sqlalchemy.orm import Session

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_EMAIL = "debug_login_user@example.com"

# --- CONFIGURATIONS ---

REWARD_FUNCTION_CODE = """
def calculate_reward(env, action):
    # Retrieve current status from env
    # Env has .status namespace injected: FLAT, LONG, SHORT
    # Action labels injected: HOLD, BUY, SELL
    
    current_price = env.data.at[env.current_step, 'close']
    status = env._current_status
    
    reward = 0.0
    
    # 1. Calculate Unrealized PnL % if in position
    pnl_pct = 0.0
    if status == env.status.LONG:
        pnl_pct = (current_price - env.entry_price) / env.entry_price
    elif status == env.status.SHORT:
        pnl_pct = (env.entry_price - current_price) / env.entry_price
        
    # 2. Base Reward: Change in Net Worth (if we track balance correctly)
    # Simplified: Reward is PnL % if holding, realized PnL if closing.
    
    # Check if we just closed a trade?
    # Hard to detect "just closed" without history in this simple fn, 
    # but 'runner.py' loop executes action THEN calls reward.
    # If action was SELL (Close Long) -> Status is now FLAT.
    # But we need to know what prompt the closure.
    
    # Let's rely on Pure PnL attribution.
    # Reward = Change in Equity Curve.
    # Since we don't have easy access to prev_equity here without state,
    # stick to simple "Holding Good Position" reward.
    
    reward += pnl_pct * 0.1 # Small constant reward for being right
    
    # 3. Penalize Drawdown (Risk Aversion)
    if pnl_pct < -0.02: # If losing more than 2%
        reward -= 0.05 # Penalty
        
    # 4. Action Penalty (Transaction Costs)
    # If action was BUY or SELL (entered/exited), penalize slightly
    if action in [env.actions.BUY, env.actions.SELL]:
         reward -= 0.001 
         
    return float(reward)
"""

MODEL_LAYERS = [
    # Input Layer: Flatten the (Window, Features) matrix to 1D vector
    {"type": "input", "layer": {"type": "Flatten", "params": {"input_shape": [16, 7]}}},
    {"type": "hidden", "layer": {"type": "Dense", "params": {"units": 128, "activation": "relu"}}},
    {"type": "hidden", "layer": {"type": "Dropout", "params": {"rate": 0.2}}},
    {"type": "hidden", "layer": {"type": "Dense", "params": {"units": 128, "activation": "relu"}}},
    {"type": "hidden", "layer": {"type": "Dropout", "params": {"rate": 0.2}}},
    {"type": "hidden", "layer": {"type": "Dense", "params": {"units": 64, "activation": "relu"}}},
    # Output layer is appended automatically by runner based on action space
]

def setup_training(db: Session):
    logger.info(f"Target Database: {DB_PATH}")
    
    # 1. Get User
    user = db.query(User).filter(User.email == USER_EMAIL).first()
    if not user:
        logger.info(f"User {USER_EMAIL} not found. Creating...")
        user = User(
            user_id=str(uuid.uuid4()),
            email=USER_EMAIL,
            hashed_password="dummy_hash_for_debug",
            role="ADMIN"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    user_id = user.user_id
    logger.info(f"Using User ID: {user_id}")

    # 2. Insert Reward Function
    func_name = "PnL_With_Risk_Penalty"
    reward_fn = db.query(MlRewardFunction).filter(MlRewardFunction.name == func_name).first()
    if not reward_fn:
        reward_fn = MlRewardFunction(
            function_id=str(uuid.uuid4()),
            name=func_name,
            description="PnL based reward with penalty for >2% drawdown and transaction costs.",
            code=REWARD_FUNCTION_CODE,
            user_id=user_id,
            metadata_json={"type": "dynamic_python"}
        )
        db.add(reward_fn)
        logger.info(f"Created Reward Function: {func_name}")
    else:
        logger.info(f"Reward Function {func_name} already exists. Updating code.")
        reward_fn.code = REWARD_FUNCTION_CODE
    
    # 3. Insert Model Architecture
    model_name = "DQN_Dense_128_128_64"
    model_arch = db.query(MlModelArchitecture).filter(MlModelArchitecture.name == model_name).first()
    if not model_arch:
        model_arch = MlModelArchitecture(
            model_id=str(uuid.uuid4()),
            name=model_name,
            description="3-layer Dense network (128, 128, 64) with Dropout.",
            layers_json=MODEL_LAYERS,
            user_id=user_id
        )
        db.add(model_arch)
        logger.info(f"Created Model Architecture: {model_name}")
    else:
        logger.info(f"Model Architecture {model_name} already exists.")
        model_arch.layers_json = MODEL_LAYERS

    # 4. Insert Training Process
    process_name = "Standard_PPO_Config_v1" # Actually using DQN parameters in runner, but naming arbitrary
    # Runner uses: optimizer, loss, gamma, tau, epsilon_...
    process = db.query(MlTrainingProcess).filter(MlTrainingProcess.name == process_name).first()
    if not process:
        process = MlTrainingProcess(
            process_id=str(uuid.uuid4()),
            name=process_name,
            description="Standard config: Adam (lr=0.001), Huber Loss, Gamma=0.99.",
            optimizer="Adam",
            loss="Huber",
            learning_rate=0.001,
            batch_size=64,
            gamma=0.99,
            tau=0.005,
            epsilon_start=1.0,
            epsilon_end=0.01,
            epsilon_decay=0.995,
            epochs=50,
            window_size=16, # Context window
            user_id=user_id
        )
        db.add(process)
        logger.info(f"Created Training Process: {process_name}")
    else:
        logger.info(f"Training Process {process_name} already exists.")

    db.commit()

    # 5. Create Session (Recipe)
    session_name = "High_Prob_DQN_Training"
    session = db.query(MlTrainingSession).filter(MlTrainingSession.name == session_name).first()
    if not session:
        session = MlTrainingSession(
            session_id=str(uuid.uuid4()),
            name=session_name,
            function_id=reward_fn.function_id,
            model_id=model_arch.model_id,
            process_id=process.process_id,
            status="PLANNED",
            user_id=user_id
        )
        db.add(session)
        logger.info(f"Created Training Session: {session_name}")
    else:
        # Update links
        session.function_id = reward_fn.function_id
        session.model_id = model_arch.model_id
        session.process_id = process.process_id
        logger.info(f"Updated Training Session: {session_name}")

    db.commit()

    # 6. Generate Dataset JSON Structure
    # Based on MlDatasetSample and Runner logic
    dataset_structure = {
        "dataset_name": "Example_Training_Data",
        "description": "Required structure for ML training injection.",
        "config": {
            "window_size": process.window_size,
            "feature_columns": ["open", "high", "low", "close", "volume", "rsi", "macd"], # Example features
        },
        "sample_structure": {
            "group_id": "episode_identifier (string)",
            "step_index": "sequence_order (int)",
            "features_json": {
                "open": "float",
                "high": "float",
                "low": "float", 
                "close": "float",
                "volume": "float",
                "...": "other_features"
            },
            "targets_json": {
                "optional_label": "float" 
            },
            "timestamp_utc": "ISO8601 String"
        }
    }

    with open("dataset_structure.json", "w") as f:
        json.dump(dataset_structure, f, indent=4)
    
    logger.info("Generated dataset_structure.json")

if __name__ == "__main__":
    # Initialize DB (creates tables if missing, though they likely exist)
    init_db()
    
    # Run Setup
    db = next(get_db())
    try:
        setup_training(db)
    except Exception as e:
        logger.error(f"Setup Failed: {e}")
    finally:
        db.close()
