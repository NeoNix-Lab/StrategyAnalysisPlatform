
import unittest
import pandas as pd
import numpy as np
import sys
import os

# Adjust path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.environment import EnvFlex
from core.fsm_execution import FSMExecutionEngine
from core.dynamic_loader import DynamicRewardLoader

class TestDynamicEnv(unittest.TestCase):
    def setUp(self):
        # Create dummy data
        self.data = pd.DataFrame({
            "close": [100, 101, 102, 103, 104, 105, 100, 95],
            "open":  [100, 100, 101, 102, 103, 104, 101, 96],
            "high":  [101, 102, 103, 104, 105, 106, 102, 97],
            "low":   [99,  100, 101, 102, 103, 104, 99,  94],
            "volume": [10, 10, 10, 10, 10, 10, 10, 10]
        })
        self.action_labels = ["HOLD", "BUY", "SELL"]
        self.status_labels = ["FLAT", "LONG", "SHORT"]
        
        # Define FSM Matrix: Simple Flip-Flop
        # FLAT + BUY -> LONG
        # LONG + SELL -> FLAT
        self.fsm_matrix = {
            "FLAT": {
                "BUY": {"next_state": "LONG", "effect": "NONE", "update_price": True}
            },
            "LONG": {
                "SELL": {"next_state": "FLAT", "effect": "CLOSE_POS", "update_price": False}
            }
        }
        
        # Define Reward Code: +1 if LONG, else 0
        self.reward_code = """
def calculate_reward(env, action):
    # env.position is alias for status
    if env.position == env.status.LONG:
        return 1.0
    return 0.0
"""
        self.execution_fn = FSMExecutionEngine(
            self.fsm_matrix, self.action_labels, self.status_labels, price_column="close"
        )
        self.reward_fn = DynamicRewardLoader.load_reward_function(
            self.reward_code, self.action_labels, self.status_labels
        )
        
        self.env = EnvFlex(
            data=self.data,
            window_size=2,
            reward_fn=self.reward_fn,
            execution_fn=self.execution_fn,
            action_labels=self.action_labels,
            status_labels=self.status_labels,
            fees=0.0
        )

    def test_dynamic_flow(self):
        obs = self.env.reset()
        self.assertEqual(self.env.position, 0) # FLAT
        
        # Step 1: BUY -> Should go LONG
        # Action BUY is index 1
        obs, reward, done, info = self.env.step(1)
        
        self.assertEqual(self.env.position, 1) # LONG
        self.assertEqual(reward, 1.0) # Reward function says 1.0 if LONG
        self.assertEqual(self.env.entry_price, 102.0) # Close at index 2 (window_size=2 start) => 100, 101 are past. Current is 102?
        # flexible: Env current step starts at window_size. 
        # reset sets current_step = 2.
        # step(1) uses data at index 2. Close is 102.
        
        # Step 2: HOLD -> Should stay LONG
        obs, reward, done, info = self.env.step(0)
        self.assertEqual(self.env.position, 1)
        self.assertEqual(reward, 1.0)
        
        # Step 3: SELL -> Should go FLAT and Realize PnL
        # Current data at index 4 (104). Entry was 102. Profit should be 2.
        start_balance = self.env.balance
        obs, reward, done, info = self.env.step(2)
        
        self.assertEqual(self.env.position, 0) # FLAT
        self.assertEqual(reward, 0.0) # Not LONG anymore
        
        # Check Balance update
        pnl = (104 - 102) * 1.0 # Default qty 1.0 logic in FSM
        self.assertAlmostEqual(self.env.balance, start_balance + pnl)

if __name__ == '__main__':
    unittest.main()
