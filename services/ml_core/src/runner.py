import logging
import random
import time
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import copy

# Dependencies from Shared
from quant_shared.models.models import StrategyRun, StrategyInstance, Trade, Execution, Side, RunStatus, Dataset, MlDatasetSample, MlIteration
from quant_shared.schemas.schemas import StrategyRunCreate

# Local imports
try:
    from .core.environment import EnvFlex
    from .core.trainer import Trainer
    from .core.models import CustomDQNModel
    # Import data converter
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../api_gateway/src'))
    from etl.data_converter import DataConverter
except ImportError:
    from core.environment import EnvFlex
    from core.trainer import Trainer
    from core.models import CustomDQNModel
    # Import data converter
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../api_gateway/src'))
    from etl.data_converter import DataConverter

logger = logging.getLogger("ml_core.runner")

class TrainingRunner:
    def __init__(self, db_session, status_cb=None):
        self.db = db_session
        self.running = False
        self.status_cb = status_cb
        self.trainer = None
        self.log_every_steps = None

    def _set_status(self, run_id: str, status: str):
        if self.status_cb:
            try:
                self.status_cb(run_id, status)
            except Exception:
                pass

    def start_training_run(self, run_id: str, config: Dict[str, Any]):
        """
        Starts a high-performance RL training loop using EnvFlex and DQN Trainer.
        Supports multiple data sources: raw data, dataset_id, or file upload
        """
        logger.info(f"Initializing RL Training for Run {run_id}")
        self.running = True
        self._set_status(run_id, "RUNNING")
        
        try:
            # 1. Configuration Extraction
            training_params = config.get("training_params", {})
            if self.log_every_steps is not None:
                training_params["log_every_steps"] = self.log_every_steps
            model_arch = config.get("model_architecture", [])
            action_labels = training_params.get("action_labels", ["HOLD", "BUY", "SELL"])
            action_dim = len(action_labels)

            def _ensure_output_units(layers: List[Dict[str, Any]], units: int) -> List[Dict[str, Any]]:
                if not layers:
                    return layers
                safe_layers = copy.deepcopy(layers)
                last = safe_layers[-1]

                if "layer" in last:
                    layer_def = last.get("layer", {})
                    layer_type = layer_def.get("type")
                    params = layer_def.get("params", {}) or {}
                    if layer_type == "Dense":
                        if params.get("units") != units:
                            logger.warning(
                                "Overriding output Dense units from %s to %s for action space.",
                                params.get("units"),
                                units
                            )
                            params["units"] = units
                            params.setdefault("activation", "linear")
                            layer_def["params"] = params
                            last["layer"] = layer_def
                            safe_layers[-1] = last
                    else:
                        logger.warning("Appending Dense output layer with %s units.", units)
                        safe_layers.append({
                            "type": "output",
                            "layer": {"type": "Dense", "params": {"units": units, "activation": "linear"}}
                        })
                else:
                    layer_type = last.get("type")
                    if layer_type == "Dense":
                        if last.get("units") != units:
                            logger.warning(
                                "Overriding output Dense units from %s to %s for action space.",
                                last.get("units"),
                                units
                            )
                            last["units"] = units
                            last.setdefault("activation", "linear")
                            safe_layers[-1] = last
                    else:
                        logger.warning("Appending Dense output layer with %s units.", units)
                        safe_layers.append({"type": "Dense", "units": units, "activation": "linear"})
                return safe_layers
            
            # 2. Data Preparation - Multiple sources supported
            raw_data = None
            
            # Option 1: Direct raw data (legacy)
            if "data" in config:
                raw_data = config["data"]
                logger.info(f"Using direct raw data: {len(raw_data)} records")
            
            # Option 2: Dataset from database
            elif "dataset_id" in config:
                dataset_id = config["dataset_id"]
                raw_data = self._load_dataset_from_db(dataset_id)
                logger.info(f"Loaded dataset from DB: {dataset_id}, {len(raw_data)} records")
            
            # Option 3: File upload
            elif "file_path" in config:
                file_path = config["file_path"]
                file_config = config.get("file_config", {})
                raw_data = self._load_dataset_from_file(file_path, file_config)
                logger.info(f"Loaded dataset from file: {file_path}, {len(raw_data)} records")
            
            # Fallback to dummy data if no data source
            if not raw_data:
                logger.warning(f"No data provided for Run {run_id}. Using dummy dataset for connectivity test.")
                raw_data = [
                    {"close": 100 + i + random.random(), "open": 100 + i, "high": 102 + i, "low": 98 + i, "volume": 1000}
                    for i in range(100)
                ]
            
            df = pd.DataFrame(raw_data)
            
            # 3. Environment Setup (Refactored)
            # Define Execution and Reward functions
            # In the future, these can be selected via 'training_params' from the UI
            from core.strategies import StrategyLibrary
            
            # Dynamic Loading or Fallback
            reward_fn = None
            execution_fn = None
            
            # Check for Dynamic Reward Code
            reward_code = training_params.get("reward_code")
            if reward_code:
                try:
                    from core.dynamic_loader import DynamicRewardLoader
                    logger.info(f"Loading dynamic reward function for Run {run_id}")
                    # Note: We need action/status labels for namespace generation
                    # We pass them to loader.
                    reward_fn = DynamicRewardLoader.load_reward_function(
                        reward_code, 
                        action_labels=action_labels,
                        status_labels=training_params.get("status_labels", ["FLAT", "LONG", "SHORT"])
                    )
                except Exception as e:
                    logger.error(f"Failed to load dynamic reward: {e}")
                    reward_fn = None # Fallback

            if not reward_fn:
                logger.info("Using default simple_pnl_reward")
                reward_fn = StrategyLibrary.simple_pnl_reward

            # Check for FSM Execution Params
            execution_params = training_params.get("execution_params")
            if execution_params and "transition_matrix" in execution_params:
                try:
                    from core.fsm_execution import FSMExecutionEngine
                    logger.info(f"Loading FSM Execution Engine for Run {run_id}")
                    
                    status_labels = training_params.get("status_labels", ["FLAT", "LONG", "SHORT"])
                    transition_matrix = execution_params.get("transition_matrix", {})
                    price_column = execution_params.get("price_column", "close")
                    
                    engine = FSMExecutionEngine(
                        transition_matrix=transition_matrix,
                        action_labels=action_labels,
                        status_labels=status_labels,
                        price_column=price_column
                    )
                    execution_fn = engine
                except Exception as e:
                    logger.error(f"Failed to load FSM Engine: {e}")
                    execution_fn = None

            if not execution_fn:
                 logger.info("Using default simple_long_short_execution")
                 execution_fn = StrategyLibrary.simple_long_short_execution

            env = EnvFlex(
                data=df,
                window_size=training_params.get("window_size", 10),
                reward_fn=reward_fn,
                execution_fn=execution_fn,
                action_labels=action_labels,
                status_labels=training_params.get("status_labels", ["FLAT", "LONG", "SHORT"]),
                initial_balance=training_params.get("initial_balance", 10000),
                fees=training_params.get("fees", 0.0)
            )

            # 4. Model Construction
            if not model_arch:
                logger.warning(f"Using DEFAULT Model Architecture for Run {run_id}")
                # Default architecture if none provided
                model_arch = [
                    {"type": "input", "layer": {"type": "Dense", "params": {"units": 64, "activation": "relu"}}},
                    {"type": "hidden", "layer": {"type": "Dense", "params": {"units": 64, "activation": "relu"}}},
                    {"type": "output", "layer": {"type": "Dense", "params": {"units": len(action_labels)}}} # Action space size
                ]
            else:
                model_arch = _ensure_output_units(model_arch, action_dim)

            model = CustomDQNModel(
                architecture_config=model_arch,
                input_shape=training_params.get("window_size", 10),
                name=f"DQN_Run_{run_id}"
            )

            # 5. Trainer Orchestration
            # Dynamic Optimizer
            opt_name = training_params.get("optimizer", "Adam")
            lr = training_params.get("learning_rate", 0.001)
            try:
                # Attempt to get optimizer from Keras
                optimizer_cls = getattr(tf.keras.optimizers, opt_name)
                optimizer = optimizer_cls(learning_rate=lr)
            except Exception:
                logger.warning(f"Optimizer {opt_name} not found, falling back to Adam")
                optimizer = tf.keras.optimizers.Adam(learning_rate=lr)

            # Dynamic Loss
            loss_name = training_params.get("loss", "huber")
            try:
                # Handle snake_case vs CamelCase or specific aliases if needed
                if loss_name == "huber":
                    loss_fn = tf.keras.losses.Huber()
                else:
                    loss_fn = tf.keras.losses.get(loss_name)
            except Exception:
                logger.warning(f"Loss function {loss_name} not found, falling back to Huber")
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
                epsilon_decay_steps=training_params.get("epsilon_decay_steps") if training_params.get("epsilon_decay_steps") is not None else 1000,
                log_dir=log_dir,
                training_name=run_id,
                epochs=training_params.get("epochs", 5),
                log_every_steps=training_params.get("log_every_steps", 2000)
            )
            self.trainer = trainer

            # 6. Execution
            logger.info(f"Starting actual training for {run_id}...")
            # We wrap the trainer call to allow interruption
            num_episodes = training_params.get("epochs", 5)
            batch_size = training_params.get("batch_size", 32)
            
            # Note: The trainer.train loop is self-contained. 
            # In a production env, we'd hook into step/episode callbacks for status updates.
            trainer.train(num_episodes=num_episodes, batch_size=batch_size)

            logger.info(f"Training Completed for Run {run_id}")
            self._finalize_run(run_id, status=RunStatus.COMPLETED)
            self._set_status(run_id, "COMPLETED")

        except Exception as e:
            logger.error(f"Training Failed for Run {run_id}: {e}", exc_info=True)
            self._finalize_run(run_id, status=RunStatus.FAILED)
            self._set_status(run_id, "FAILED")
        finally:
            self.running = False

    def set_log_every_steps(self, steps: int) -> int:
        safe_steps = max(int(steps), 0)
        self.log_every_steps = safe_steps
        if self.trainer is not None:
            self.trainer.log_every_steps = safe_steps
            logger.info("Updated log_every_steps to %s", safe_steps)
        return safe_steps

    def _load_dataset_from_db(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Load dataset samples from database"""
        try:
            samples = self.db.query(MlDatasetSample).filter(
                MlDatasetSample.dataset_id == dataset_id
            ).order_by(MlDatasetSample.step_index.asc()).all()
            
            if not samples:
                raise ValueError(f"No samples found for dataset_id: {dataset_id}")
            
            # Convert to list of dictionaries
            data = []
            for sample in samples:
                row = sample.features_json.copy()
                row.update(sample.targets_json or {})
                if sample.timestamp_utc:
                    row['timestamp'] = sample.timestamp_utc.isoformat()
                if sample.group_id:
                    row['group_id'] = sample.group_id
                row['step_index'] = sample.step_index
                data.append(row)
            
            logger.info(f"Loaded {len(data)} samples from dataset {dataset_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading dataset from DB {dataset_id}: {e}")
            raise

    def _load_dataset_from_file(self, file_path: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load dataset from file using DataConverter"""
        try:
            converter = DataConverter()
            samples_data = converter.convert_from_file(file_path, config)
            
            # Convert MlDatasetSample format to training data format
            data = []
            for sample in samples_data:
                row = sample['features_json'].copy()
                row.update(sample['targets_json'] or {})
                if sample['timestamp_utc']:
                    row['timestamp'] = sample['timestamp_utc'].isoformat()
                if sample['group_id']:
                    row['group_id'] = sample['group_id']
                row['step_index'] = sample['step_index']
                data.append(row)
            
            logger.info(f"Loaded {len(data)} samples from file {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading dataset from file {file_path}: {e}")
            raise

    def _update_run_status(self, run_id: str, current_epoch: int, total_epochs: int):
        # Try StrategyRun
        run = self.db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
        if run:
            run.extra_json = {"progress": f"{current_epoch}/{total_epochs}"}
            self.db.commit()
            return
        
        # Try MlIteration
        iter_obj = self.db.query(MlIteration).filter(MlIteration.iteration_id == run_id).first()
        if iter_obj:
            # We can store progress in metrics_json or a new field?
            # MlIteration has metrics_json.
            metrics = iter_obj.metrics_json or {}
            metrics['progress'] = f"{current_epoch}/{total_epochs}"
            iter_obj.metrics_json = metrics
            self.db.commit()

    def _finalize_run(self, run_id: str, status: RunStatus = RunStatus.COMPLETED):
        # Try StrategyRun
        run = self.db.query(StrategyRun).filter(StrategyRun.run_id == run_id).first()
        if run:
            run.status = status
            run.end_utc = datetime.utcnow()
            self.db.commit()
            return

        # Try MlIteration
        iter_obj = self.db.query(MlIteration).filter(MlIteration.iteration_id == run_id).first()
        if iter_obj:
            # Map RunStatus enum to string if needed, or use as is if compatible
            iter_obj.status = status.value if hasattr(status, 'value') else status
            iter_obj.end_utc = datetime.utcnow()
            self.db.commit()

    def stop(self):
        self.running = False
