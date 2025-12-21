
import uuid
import json
from src.database.connection import SessionLocal, init_db
from src.database.models import MlRewardFunction, MlModelArchitecture, MlTrainingProcess

def seed():
    init_db()
    db = SessionLocal()
    
    # 1. Reward Functions
    rewards = [
        {
            "name": "PnL Optimized",
            "description": "Rewards positive PnL and penalizes drawdowns.",
            "code": """
def calculate_reward(env, action):
    # Retrieve last PnL from environment
    # This is a sample logic
    pnl = env.last_reward # Assuming env provides step pnl here or we calculate it
    
    # Simple PnL reward
    reward = pnl
    
    # Penalize holding too long if flat? No.
    # Penalize drawdowns
    if pnl < 0:
        reward *= 1.5 
        
    env.last_reward = reward
"""
        },
        {
            "name": "Sharpe Ratio Proxy",
            "description": "Optimizes for risk-adjusted returns.",
            "code": """
def calculate_reward(env, action):
    # Placeholder for Sharpe logic
    pnl = env.last_reward
    volatility = 1.0 # Need rolling volatility from env
    
    if volatility == 0:
        reward = pnl
    else:
        reward = pnl / volatility
        
    env.last_reward = reward
"""
        }
    ]

    for r in rewards:
        obj = MlRewardFunction(
            function_id=str(uuid.uuid4()),
            name=r["name"],
            description=r["description"],
            code=r["code"]
        )
        db.add(obj)

    # 2. Model Architectures
    architectures = [
        {
            "name": "DQN (Dense)",
            "description": "Simple fully connected network for basic RL.",
            "layers": [
                {"type": "Dense", "units": 64, "activation": "relu"},
                {"type": "Dense", "units": 64, "activation": "relu"},
                {"type": "Dense", "units": 3, "activation": "linear"} # Action space output
            ]
        },
        {
            "name": "LSTM-DQN",
            "description": "Recurrent network for time-series memory.",
            "layers": [
                {"type": "LSTM", "units": 64, "return_sequences": False},
                {"type": "Dense", "units": 32, "activation": "relu"},
                {"type": "Dense", "units": 3, "activation": "linear"}
            ]
        }
    ]

    for a in architectures:
        obj = MlModelArchitecture(
            model_id=str(uuid.uuid4()),
            name=a["name"],
            description=a["description"],
            layers_json=a["layers"]
        )
        db.add(obj)

    # 3. Training Processes
    processes = [
        {
            "name": "Fast Experiment",
            "description": "Quick training with aggressive exploration decay.",
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 0.001,
            "epsilon_start": 1.0,
            "epsilon_end": 0.01,
            "epsilon_decay": 0.9,
            "window_size": 10
        },
        {
            "name": "Deep Learning (Long)",
            "description": "Slow decay, many epochs for stable convergence.",
            "epochs": 100,
            "batch_size": 64,
            "learning_rate": 0.0001,
            "epsilon_start": 1.0,
            "epsilon_end": 0.05,
            "epsilon_decay": 0.99,
            "window_size": 20
        }
    ]

    for p in processes:
        obj = MlTrainingProcess(
            process_id=str(uuid.uuid4()),
            **p
        )
        db.add(obj)

    db.commit()
    print("Seeding ML Studio Complete.")
    db.close()

if __name__ == "__main__":
    seed()
