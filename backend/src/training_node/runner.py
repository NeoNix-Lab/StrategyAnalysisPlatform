
import time
import json
import os
import numpy as np
import traceback
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import (
    MlIteration, MlTrainingSession, MlTrainingProcess, 
    MlModelArchitecture, MlRewardFunction
)
from .environment import EnvFlex
from .replay_buffer import ReplayBuffer
from .utils import load_dataset_as_dataframe, build_keras_model, get_reward_function

# Check TensorFlow availability
try:
    import tensorflow as tf
except ImportError:
    tf = None
# tf = None

class TrainingRunner:
    def __init__(self, db: Session, iteration_id: str):
        self.db = db
        self.iteration_id = iteration_id
        self.iteration = db.query(MlIteration).get(iteration_id)
        if not self.iteration:
            raise ValueError(f"Iteration {iteration_id} not found")
            
        self.session_config = self.iteration.session
        if not self.session_config:
            raise ValueError("Iteration has no linked Session")
            
        self.process = self.session_config.process
        self.model_arch = self.session_config.model
        self.reward_func_record = self.session_config.function
        
        # Runtime State
        self.env = None
        self.main_network = None
        self.target_network = None
        self.replay_buffer = None
        self.epsilon = self.process.epsilon_start
        
        # Logging
        self.logs = []
        self.log_dir = os.path.join(os.getcwd(), "logs", "ml")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{self.iteration_id}.log")

        # Artifacts
        self.artifact_dir = os.path.join(os.getcwd(), "models", "ml_artifacts")
        os.makedirs(self.artifact_dir, exist_ok=True)
        
    def log(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"{timestamp} - {message}"
        print(f"[Run {self.iteration_id}] {message}")
        
        # Write to file
        with open(self.log_path, "a") as f:
            f.write(log_entry + "\n")
            f.flush()
        
        # Keep a few in memory for status updates if needed
        self.logs.append(log_entry)
        if len(self.logs) > 100:
            self.logs.pop(0)

    def run(self):
        """
        Executes the full training lifecycle.
        """
        try:
            self._start_run()
            self._setup_environment()
            self._build_agent()
            self._training_loop()
            self._finish_run(status="COMPLETED")
        except Exception as e:
            tb_str = traceback.format_exc()
            self.log(f"CRITICAL ERROR: {str(e)}")
            self.log(f"Traceback:\n{tb_str}")
            self._finish_run(status="FAILED", error_msg=str(e) + "\n" + tb_str)
            raise e

    def _start_run(self):
        self.log("Starting Training Run...")
        self.log(f"[VERBOSE] Run ID: {self.iteration_id}")
        self.log(f"[VERBOSE] Python: {sys.executable}")
        self.log(f"[VERBOSE] Version: {sys.version}")
        self.log(f"[VERBOSE] Process Configuration: {self.process.name}")
        self.log(f"[VERBOSE] Model Architecture: {self.model_arch.name}")
        
        self.iteration.status = "RUNNING"
        self.iteration.start_utc = datetime.utcnow()
        self.db.commit()

        # [NEW] If Test Mode (Backtest), ensure we have a StrategyRun structure for the Analyst
        # Check if we are in test mode (need access to split_config early, or check it here)
        split_config = self.iteration.split_config_json or {}
        if split_config.get("test_only", False):
            self._ensure_strategy_run_structure()

    def _ensure_strategy_run_structure(self):
        """
        Creates Strategy -> Instance -> Run hierarchy so Analyst can see metrics/trades.
        Uses iteration_id as the run_id.
        """
        from src.database.models import Strategy, StrategyInstance, StrategyRun, RunType, RunStatus
        import uuid
        
        # 1. Ensure "ML Models" Strategy exists
        strat = self.db.query(Strategy).filter(Strategy.name == "ML Models").first()
        if not strat:
            strat = Strategy(
                strategy_id=str(uuid.uuid4()),
                name="ML Models",
                notes="Container for ML Training/Inference runs"
            )
            self.db.add(strat)
            self.db.flush()
            
        # 2. Ensure Instance exists for this Session (or Process/Model combo)
        # We use the Session Name as the Instance Name
        instance_name = self.session_config.name
        instance = self.db.query(StrategyInstance).filter(
            StrategyInstance.strategy_id == strat.strategy_id,
            StrategyInstance.instance_name == instance_name
        ).first()
        
        if not instance:
            instance = StrategyInstance(
                instance_id=str(uuid.uuid4()),
                strategy_id=strat.strategy_id,
                instance_name=instance_name,
                parameters_json={},
                symbol="MULTI", # Unknown until data loaded? Or generic.
                timeframe="N/A"
            )
            self.db.add(instance)
            self.db.flush()
            
        # 3. Create StrategyRun (if not exists - iteration_id is the key)
        # Note: iteration_id is used as run_id
        run_obj = self.db.query(StrategyRun).get(self.iteration.iteration_id)
        if not run_obj:
            run_obj = StrategyRun(
                run_id=self.iteration.iteration_id, # Link ML Iteration to Strategy Run 1:1
                instance_id=instance.instance_id,
                run_type=RunType.BACKTEST,
                status=RunStatus.RUNNING,
                start_utc=datetime.utcnow(),
                metrics_json={}
            )
            self.db.add(run_obj)
            self.db.commit()
            self.log(f"Created StrategyRun for Analyst Integration (RunID: {self.iteration.iteration_id})")

    def _setup_environment(self):
        self.log("Loading Dataset...")
        df_data = load_dataset_as_dataframe(self.db, self.iteration.dataset_id)
        self.log(f"[VERBOSE] Dataset Loaded. Shape: {df_data.shape}")
        self.log(f"[VERBOSE] Columns: {list(df_data.columns)}")
        
        # [NEW] Dataset Splitting Logic
        split_config = self.iteration.split_config_json or {}
        is_test_mode = split_config.get("test_only", False)
        
        if is_test_mode:
             self.log(f"Test Mode: Using full dataset for inference ({len(df_data)} rows).")
        else:
             # Training: Slice by train_ratio
             train_ratio = split_config.get("train", 0.7)
             cutoff = int(len(df_data) * train_ratio)
             self.log(f"Training Mode: Using first {train_ratio*100:.1f}% of data ({cutoff} rows).")
             df_data = df_data.iloc[:cutoff].copy()

        self.log("Compiling Reward Function...")
        reward_fn = get_reward_function(self.db, self.reward_func_record.function_id)
        
        self.log("Initializing Environment...")
        
        # Extract metadata for custom namespaces
        rf_meta = self.reward_func_record.metadata_json or {}
        action_labels = rf_meta.get("action_labels")
        status_labels = rf_meta.get("status_labels")
        
        self.env = EnvFlex(
            df_data=df_data,
            reward_function=reward_fn,
            window_size=self.process.window_size,
            fees=0.01, # Could be config
            initial_balance=100000.0, # Could be config
            action_labels=action_labels,
            status_labels=status_labels
        )
        self.log(f"Environment Ready. Data Steps: {len(df_data)}")
        self.log(f"[VERBOSE] Observation Space: {self.env.observation_space.shape}")
        self.log(f"[VERBOSE] Action Space: {self.env.action_space.n}")
        if action_labels: self.log(f"[VERBOSE] Action Labels: {action_labels}")

    def _build_agent(self):
        if not tf:
            self.log("WARNING: TensorFlow not installed. Simulation Mode.")
            return

        self.log("Building Neural Networks...")
        input_shape = self.env.observation_space.shape
        layers_config = self.model_arch.layers_json
        
        self.log(f"[VERBOSE] Input Shape: {input_shape}")
        self.log(f"[VERBOSE] Layer Config: {json.dumps(layers_config)}")
        
        self.main_network = build_keras_model(layers_config, input_shape)
        # Compile model
        optimizer_name = "adam" # Default or from extensions
        loss_fn = "mse" # Default
        
        self.main_network.compile(optimizer=optimizer_name, loss=loss_fn)
        
        # Check for pre-trained weights
        split_config = self.iteration.split_config_json or {}
        # Explicit check for test mode to enforce loading
        is_test_mode = split_config.get("test_only", False)
        
        load_source_id = split_config.get("load_from_iteration_id")
        source_path = split_config.get("source_model_path")

        if load_source_id and source_path:
            self.log(f"Attempting to load weights from: {source_path}")
            
            # Resolve absolute path if just a filename is stored
            if not os.path.isabs(source_path):
                # Assume it's in our artifact bucket
                source_path = os.path.join(self.artifact_dir, os.path.basename(source_path))

            try:
                if os.path.exists(source_path):
                    self.main_network.load_weights(source_path)
                    self.log(f"Weights loaded successfully from {source_path}")
                else:
                    msg = f"Source model file not found at {source_path}"
                    if is_test_mode:
                        self.log(f"CRITICAL: {msg}. Aborting Test because model is missing.")
                        raise FileNotFoundError(msg)
                    else:
                         self.log(f"WARNING: {msg}. Starting training from scratch.")
            except Exception as e:
                self.log(f"ERROR loading weights: {e}")
                if is_test_mode:
                    raise e
        
        # Target Network
        self.target_network = tf.keras.models.clone_model(self.main_network)
        self.target_network.set_weights(self.main_network.get_weights())
        
        self.log("[VERBOSE] Models compiled (Main & Target)")
        self.replay_buffer = ReplayBuffer(capacity=50000) # Configurable?
        self.log(f"[VERBOSE] Replay Buffer Initialized (Capacity: 50000)")

    def _training_loop(self):
        from src.database.models import Trade, Side, StrategyRun, RunStatus
        import uuid

        # Check test mode
        split_config = self.iteration.split_config_json or {}
        is_test_mode = split_config.get("test_only", False)
        
        epochs = self.process.epochs
        batch_size = self.process.batch_size
        gamma = self.process.gamma
        tau = self.process.tau

        if is_test_mode:
            self.epsilon = 0.0
            self.process.epsilon_end = 0.0
            self.log("[TEST MODE] Epsilon set to 0. Training disabled.")
            epochs = 1 # Single pass for evaluation default
        
        self.log(f"Starting {'Testing' if is_test_mode else 'Training'} Loop for {epochs} episodes...")
        self.log(f"[VERBOSE] Parameters: Gamma={gamma}, Tau={tau}, Batch={batch_size}, Epsilon={self.epsilon}")
        
        # Metrics History
        history = []
        
        for episode in range(epochs):
            state = self.env.reset()
            # Reshape state for Keras input (1, window, features)
            state = np.expand_dims(state, axis=0) 
            
            done = False
            total_reward = 0
            step_count = 0
            episode_loss = 0
            train_steps = 0
            
            # [Test Mode] Trade Tracking State
            open_position = None # {entry_price, entry_step, side, qty}
            
            while not done:
                # 1. Action Selection (Epsilon Greedy)
                if tf and np.random.rand() < self.epsilon:
                    action = np.random.randint(self.env.action_space.n)
                elif tf:
                    q_values = self.main_network.predict(state, verbose=0)
                    action = np.argmax(q_values[0])
                else:
                    action = np.random.randint(3) # Simulation

                # Capture State BEFORE Step
                prev_pos_idx = self.env.position
                prev_step_idx = self.env.current_step # This index matches df_data index for timestamps? 
                
                # 2. Step
                next_state_raw, reward, done, _ = self.env.step(action)
                next_state = np.expand_dims(next_state_raw, axis=0)
                
                # Check for Position Change (Trade Event)
                if is_test_mode:
                    curr_pos_idx = self.env.position
                    
                    # Logic 1: Opened a Position (Flat -> Long/Short)
                    if prev_pos_idx == 0 and curr_pos_idx != 0:
                        open_position = {
                            "entry_price": self.env.entry_price,
                            "entry_step": prev_step_idx, # The step where decision was made
                            "side": Side.BUY if curr_pos_idx == 1 else Side.SELL, 
                            "qty": self.env.qty,
                            "ts": getattr(self.env.observation_dataframe.iloc[prev_step_idx], 'ts_utc', datetime.utcnow())
                        }
                    
                    # Logic 2: Closed a Position (Long/Short -> Flat)
                    elif prev_pos_idx != 0 and curr_pos_idx == 0:
                        if open_position:
                            exit_price = self.env.data.at[prev_step_idx, 'close'] # Close at current step price?
                            # Re-verify logic: env.step updates current_step. 
                            # If action closed it, it executed at price of 'prev_step_idx' (current bar).
                            
                            # Calculate PnL
                            pnl = 0
                            if open_position['side'] == Side.BUY:
                                pnl = (exit_price - open_position['entry_price']) * open_position['qty']
                            else:
                                pnl = (open_position['entry_price'] - exit_price) * open_position['qty']
                                
                            # Save Trade
                            try:
                                t = Trade(
                                    trade_id=str(uuid.uuid4()),
                                    run_id=self.iteration.iteration_id,
                                    symbol="N/A", # Need symbol from Env or Dataset!
                                    side=open_position['side'],
                                    entry_time=open_position['ts'], # Use TS from DF
                                    exit_time=getattr(self.env.observation_dataframe.iloc[prev_step_idx], 'ts_utc', datetime.utcnow()),
                                    entry_price=open_position['entry_price'],
                                    exit_price=exit_price,
                                    quantity=open_position['qty'],
                                    pnl_net=pnl,
                                    pnl_gross=pnl,
                                    commission=0.0
                                )
                                self.db.add(t)
                                self.db.commit() # Commit trade
                            except Exception as te:
                                self.log(f"Error saving trade: {te}")
                            
                            open_position = None

                    # Logic 3: Reversal (Long -> Short or Short -> Long)
                    # Not handled in simple env logic usually (goes to flat first), but good to keep in mind.

                # [DEBUG] Log first 10 steps
                if step_count < 10:
                     self.log(f"[DEBUG] Step {step_count} | Action: {action} ({['HOLD','BUY','SELL'][action]}) | Pos: {self.env.position} | Reward: {reward:.4f}")

                total_reward += reward
                
                # 3. Store Experience
                if self.replay_buffer:
                    self.replay_buffer.push(state, action, reward, next_state, done)
                
                state = next_state
                step_count += 1
                
                # 4. Train
                if not is_test_mode and tf and self.replay_buffer and len(self.replay_buffer) > batch_size:
                    loss = self._train_step(batch_size, gamma)
                    if loss is not None:
                        episode_loss += loss
                        train_steps += 1
            
            # Force Close Open Position at End of Episode
            if is_test_mode and open_position:
                # Use last known price
                last_step_idx = self.env.current_step - 1
                try:
                    exit_price = self.env.data.at[last_step_idx, 'close']
                except:
                    # Fallback if index issue
                    exit_price = open_position['entry_price'] 
                
                # Calculate PnL
                pnl = 0
                if open_position['side'] == Side.BUY:
                    pnl = (exit_price - open_position['entry_price']) * open_position['qty']
                else:
                    pnl = (open_position['entry_price'] - exit_price) * open_position['qty']
                
                # Save Trade
                try:
                    t = Trade(
                        trade_id=str(uuid.uuid4()),
                        run_id=self.iteration.iteration_id,
                        symbol="Backtest", # Placeholder
                        side=open_position['side'],
                        entry_time=open_position['ts'],
                        exit_time=datetime.utcnow(), # Or dataset end time
                        entry_price=open_position['entry_price'],
                        exit_price=exit_price,
                        quantity=open_position['qty'],
                        pnl_net=pnl,
                        pnl_gross=pnl,
                        commission=0.0,
                        extra_json={"note": "Force Closed at End of Backtest"}
                    )
                    self.db.add(t)
                    self.db.commit()
                    self.log(f"Force closed remaining position. PnL: {pnl:.2f}")
                except Exception as te:
                    self.log(f"Error saving force-close trade: {te}")

            # End of Episode
            avg_loss = episode_loss / train_steps if train_steps > 0 else 0
            
            if (episode + 1) % 10 == 0:
                 self.log(f"Episode {episode+1}/{epochs} | Reward: {total_reward:.2f} | Loss: {avg_loss:.4f} | Epsilon: {self.epsilon:.4f}")
            else:
                 self.log(f"[VERBOSE] Episode {episode+1} Done. Reward: {total_reward:.2f}")
            
            # Decay Epsilon
            if not is_test_mode and self.epsilon > self.process.epsilon_end:
                self.epsilon *= self.process.epsilon_decay
                
            metrics_entry = {
                "epoch": episode + 1,
                "reward": float(total_reward),
                "loss": float(avg_loss),
                "epsilon": float(self.epsilon),
                "balance": float(total_reward) 
            }
            history.append(metrics_entry)
            self._update_metrics(history)
            
            if self._check_cancellation():
                self.log("Training cancelled by user.")
                self._finish_run(status="CANCELLED")
                return

        # If Test Mode, Mark StrategyRun as COMPLETED
        if is_test_mode:
            strat_run = self.db.query(StrategyRun).get(self.iteration.iteration_id)
            if strat_run:
                strat_run.status = RunStatus.COMPLETED
                strat_run.end_utc = datetime.utcnow()
                self.db.commit()

    def _check_cancellation(self) -> bool:
        """
        Checks if the iteration status has been changed to CANCELLING.
        Refreshes the iteration object from DB.
        """
        self.db.refresh(self.iteration)
        if self.iteration.status == "CANCELLING":
            return True
        return False

    def _update_metrics(self, history: list):
        """
        Updates the iteration metrics in the database.
        """
        try:
            # We overwrite the JSON with the full history + current summary
            current_metrics = {
                "history": history,
                "final": history[-1] if history else {}
            }
            self.iteration.metrics_json = current_metrics
            self.db.commit()
        except Exception as e:
            self.log(f"Error updating metrics: {e}")

    def _train_step(self, batch_size, gamma):
        if not tf: return None
        
        batch = self.replay_buffer.sample(batch_size)
        if not batch: return None
        
        states, actions, rewards, next_states, dones = batch
        # Fix shapes if needed. sample returns stacked numpy arrays.
        # states shape: (batch, 1, window, features) ? We need (batch, window, features)
        states = np.squeeze(states, axis=1)
        next_states = np.squeeze(next_states, axis=1)

        # DDQN Style or simple DQN
        q_next = self.target_network.predict(next_states, verbose=0)
        max_q_next = np.max(q_next, axis=1)
        
        targets = rewards + (1 - dones) * gamma * max_q_next
        
        # Create full target matrix
        q_values = self.main_network.predict(states, verbose=0)
        
        # We need to compute loss. Keras train_on_batch returns scalar loss.
        # We need to construct target vector for the specific actions taken
        
        # This is a bit inefficient with Keras high level API for DQN but works.
        # Better: use GradientTape for custom training loop.
        # For MVP: We update the Q-values for the taken actions to the target
        
        # Update q_values with targets
        batch_indices = np.arange(batch_size)
        q_values[batch_indices, actions] = targets
        
        loss = self.main_network.train_on_batch(states, q_values)
        return float(loss)
        
        # Update only the Q-value for the taken action
        indices = np.arange(batch_size)
        q_values[indices, actions] = targets
        
        self.main_network.fit(states, q_values, verbose=0, epochs=1)
        
        # Soft Update Target
        self._update_target_network(self.process.tau)

    def _update_target_network(self, tau):
        weights = self.main_network.get_weights()
        target_weights = self.target_network.get_weights()
        for i in range(len(target_weights)):
            target_weights[i] = tau * weights[i] + (1 - tau) * target_weights[i]
        self.target_network.set_weights(target_weights)
        # self.log(f"[VERBOSE] Soft Target Update (Tau={tau})") # Too frequent if every step?
        # Maybe log only if tau is 1.0 (Hard update) or just skip for soft updates to avoid spam.
        if tau == 1.0:
            self.log("[VERBOSE] Hard Target Network Update")



    def _finish_run(self, status, error_msg=None):
        self.iteration.status = status
        self.iteration.end_utc = datetime.utcnow()
        if error_msg:
            metrics = self.iteration.metrics_json or {}
            metrics["error"] = error_msg
            self.iteration.metrics_json = metrics
            
        # Save Model Artifact
        if status == "COMPLETED" and self.main_network:
            filename = f"model_{self.iteration_id}.h5"
            full_path = os.path.join(self.artifact_dir, filename)
            
            try:
                self.main_network.save(full_path)
                self.iteration.model_artifact_path = filename # Store relative filename or absolute?
                # Probably better to store just filename if we always re-construct self.artifact_dir
                self.log(f"Model saved to {full_path}")
            except Exception as e:
                self.log(f"Error saving model: {e}")

        self.db.commit()
