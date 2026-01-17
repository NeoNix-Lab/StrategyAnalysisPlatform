
import sys
import os
import uuid
import json

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'packages', 'quant_shared', 'src')))

from quant_shared.models.models import MlRewardFunction
from quant_shared.models.connection import get_db

def create_function():
    db_gen = get_db()
    session = next(db_gen)

    # 1. Define FSM Logic (Transition Matrix)
    # Simple strategy: 
    # FLAT -> BUY -> LONG
    # LONG -> SELL -> FLAT
    # SHORT -> COVER -> FLAT (Optional, keeping it simple for now)
    
    transition_matrix = {
        "FLAT": {
            "BUY": {"next_state": "LONG", "effect": "NONE", "update_price": True},
            "SELL": {"next_state": "SHORT", "effect": "NONE", "update_price": True}
        },
        "LONG": {
            "SELL": {"next_state": "FLAT", "effect": "CLOSE_POS", "update_price": False},
            "HOLD": {"next_state": "LONG", "effect": "NONE", "update_price": False}
        },
        "SHORT": {
            "BUY": {"next_state": "FLAT", "effect": "CLOSE_SHORT", "update_price": False},
            "HOLD": {"next_state": "SHORT", "effect": "NONE", "update_price": False}
        }
    }

    # 2. Define Reward Python Code
    # Uses 'Price' and Ichimoku features found in dataset
    reward_code = """
def calculate_reward(env, action):
    # env.data is the current row (dict-like)
    # env.position is the current status index (0=FLAT, 1=LONG, 2=SHORT)
    
    current_price = env.data.get('Price', 0.0)
    
    # Example Logic: Ichimoku Trend Following
    # Span A > Span B => Bullish
    span_a = env.data.get('Span_A_Fast', 0.0)
    span_b = env.data.get('Span_B_Fast', 0.0)
    
    is_bullish = span_a > span_b
    is_bearish = span_a < span_b
    
    reward = 0.0
    
    # 1. Alignment Reward (State matches Trend)
    if env.position == env.status.LONG and is_bullish:
        reward += 0.1
    elif env.position == env.status.SHORT and is_bearish:
        reward += 0.1
        
    # 2. PnL Reward (Unrealized)
    # env.unrealized_pnl is calculated automatically by FSM/Env
    # Add a fraction of PnL to guide agent
    if env.unrealized_pnl > 0:
        reward += (env.unrealized_pnl / env.initial_balance) * 10.0
        
    return reward
"""

    # 3. Construct Metadata with Compatibility Requirements
    metadata = {
        "action_labels": ["HOLD", "BUY", "SELL"],
        "status_labels": ["FLAT", "LONG", "SHORT"],
        "execution_params": {
            "transition_matrix": transition_matrix,
            "price_column": "Price"
        },
        # Explicit Definition of Required Features for Compatibility Check
        "required_features": ["Price", "Span_A_Fast", "Span_B_Fast"]
    }

    fn_name = "Ichimoku Trend Follower (Demo)"
    
    # Check if exists to avoid duplicates
    existing = session.query(MlRewardFunction).filter_by(name=fn_name).first()
    if existing:
        print(f"Function '{fn_name}' already exists. Updating...")
        existing.code = reward_code
        existing.metadata_json = metadata
        existing.description = "Demo function checking Span A/B crossover and PnL."
    else:
        new_fn = MlRewardFunction(
            function_id=str(uuid.uuid4()),
            name=fn_name,
            description="Demo function checking Span A/B crossover and PnL.",
            code=reward_code,
            metadata_json=metadata
        )
        session.add(new_fn)
        print(f"Creating new function '{fn_name}'...")

    session.commit()
    print("Function saved successfully.")

if __name__ == "__main__":
    create_function()
