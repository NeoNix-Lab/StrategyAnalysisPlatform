import logging
import random
import time
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime
from typing import Dict, Any, List, Optional

# Dependencies from Shared
from quant_shared.models.models import StrategyRun, StrategyInstance, Trade, Execution, Side, RunStatus
from quant_shared.schemas.schemas import StrategyRunCreate

# Local imports
from .core.environment import EnvFlex
from .core.trainer import Trainer
from .core.models import CustomDQNModel

logger = logging.getLogger(__name__)

class TrainingRunner:
    def __init__(self, db_session):
        self.db = db_session
        self.running = False

    def start_training_run(self, run_id: str, config: Dict[str, Any]):
        """
        Starts a high-performance RL training loop using EnvFlex and DQN Trainer.
        """
        logger.info(f"🚀 Initializing RL Training for Run {run_id}")
        self.running = True
        
        try:
            # 1. Configuration Extraction
            training_params = config.get("training_params", {})
            model_arch = config.get("model_architecture", [])
            raw_data = config.get("data", [])

            # 2. Data Preparation
            if not raw_data:
                logger.warning(f"No data provided for Run {run_id}. Using dummy dataset for connectivity test.")
                # Create dummy data if none provided (PoC fallback)
                raw_data = [
                    {"close": 100 + i + random.random(), "open": 100 + i, "high": 102 + i, "low": 98 + i, "volume": 1000}
                    for i in range(100)
                ]
            
            df = pd.DataFrame(raw_data)
            
            # 3. Environment Setup
            # Define a dynamic reward function based on config if provided, else default
            def default_reward_fn(obs, action):
                # Placeholder: simple price-action based reward if columns exist
                # obs shape: (window_size, features)
                return np.random.randn() * 0.1 

            env = EnvFlex(
                data=df,
                window_size=training_params.get("window_size", 10),
                reward_fn=default_reward_fn,
                action_labels=training_params.get("action_labels", ["HOLD", "BUY", "SELL"]),
                status_labels=training_params.get("status_labels", ["FLAT", "LONG", "SHORT"]),
                initial_balance=training_params.get("initial_balance", 10000)
            )

            # 4. Model Construction
            if not model_arch:
                # Default architecture if none provided
                model_arch = [
                    {"type": "input", "layer": {"type": "Dense", "params": {"units": 64, "activation": "relu"}}},
                    {"type": "hidden", "layer": {"type": "Dense", "params": {"units": 64, "activation": "relu"}}},
                    {"type": "output", "layer": {"type": "Dense", "params": {"units": 3}}} # Action space size
                ]

            model = CustomDQNModel(
                architecture_config=model_arch,
                input_shape=training_params.get("window_size", 10),
                name=f"DQN_Run_{run_id}"
            )

            # 5. Trainer Orchestration
            optimizer = tf.keras.optimizers.Adam(learning_rate=training_params.get("learning_rate", 0.001))
            loss_fn = tf.keras.losses.Huber()
            
            log_dir = os.path.join("logs", "training", run_id)
            trainer = Trainer(
                env=env,
                main_network=model,
                optimizer=optimizer,
                loss_fn=loss_fn,
                gamma=training_params.get("gamma", 0.99),
                tau=training_params.get("tau", 0.005),
                epsilon_start=training_params.get("epsilon_start", 1.0),
                epsilon_end=training_params.get("epsilon_end", 0.01),
                epsilon_decay_steps=training_params.get("epsilon_decay_steps", 1000),
                log_dir=log_dir,
                training_name=run_id,
                epochs=training_params.get("epochs", 5)
            )

            # 6. Execution
            logger.info(f"Starting actual training for {run_id}...")
            # We wrap the trainer call to allow interruption
            num_episodes = training_params.get("epochs", 5)
            batch_size = training_params.get("batch_size", 32)
            
            # Note: The trainer.train loop is self-contained. 
            # In a production env, we'd hook into step/episode callbacks for status updates.
            trainer.train(num_episodes=num_episodes, batch_size=batch_size)

            logger.info(f"✅ Training Completed for Run {run_id}")
            self._finalize_run(run_id, status=RunStatus.COMPLETED)

        except Exception as e:
            logger.error(f"❌ Training Failed for Run {run_id}: {e}", exc_info=True)
            self._finalize_run(run_id, status=RunStatus.FAILED)
        finally:
            self.running = False

    def _update_run_status(self, run_id: str, current_epoch: int, total_epochs: int):
        run = self.db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
        if run:
            run.extra_json = {"progress": f"{current_epoch}/{total_epochs}"}
            self.db.commit()

    def _finalize_run(self, run_id: str, status: RunStatus = RunStatus.COMPLETED):
        run = self.db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
        if run:
            run.status = status
            run.end_utc = datetime.utcnow()
            self.db.commit()

    def stop(self):
        self.running = False
