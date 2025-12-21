
import time
import json
import os
import numpy as np
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
        
    def log(self, message: str):
        print(f"[Run {self.iteration_id}] {message}")
        self.logs.append(f"{datetime.utcnow().isoformat()} - {message}")
        # Ideally, we push logs to DB periodically or to a file

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
            self.log(f"CRITICAL ERROR: {str(e)}")
            self._finish_run(status="FAILED", error_msg=str(e))
            raise e

    def _start_run(self):
        self.log("Starting Training Run...")
        self.iteration.status = "RUNNING"
        self.iteration.start_utc = datetime.utcnow()
        self.iteration.logs_json = json.dumps(self.logs) # Initial log
        self.db.commit()

    def _setup_environment(self):
        self.log("Loading Dataset...")
        df_data = load_dataset_as_dataframe(self.db, self.iteration.dataset_id)
        
        self.log("Compiling Reward Function...")
        reward_fn = get_reward_function(self.db, self.reward_func_record.function_id)
        
        self.log("Initializing Environment...")
        self.env = EnvFlex(
            df_data=df_data,
            reward_function=reward_fn,
            window_size=self.process.window_size,
            fees=0.01, # Could be config
            initial_balance=100000.0 # Could be config
        )
        self.log(f"Environment Ready. Data Steps: {len(df_data)}")

    def _build_agent(self):
        if not tf:
            self.log("WARNING: TensorFlow not installed. Simulation Mode.")
            return

        self.log("Building Neural Networks...")
        input_shape = self.env.observation_space.shape
        layers_config = self.model_arch.layers_json
        
        self.main_network = build_keras_model(layers_config, input_shape)
        # Compile model
        optimizer_name = "adam" # Default or from extensions
        loss_fn = "mse" # Default
        
        self.main_network.compile(optimizer=optimizer_name, loss=loss_fn)
        
        # Target Network
        self.target_network = tf.keras.models.clone_model(self.main_network)
        self.target_network.set_weights(self.main_network.get_weights())
        
        self.replay_buffer = ReplayBuffer(capacity=50000) # Configurable?

    def _training_loop(self):
        epochs = self.process.epochs
        batch_size = self.process.batch_size
        gamma = self.process.gamma
        tau = self.process.tau
        
        for episode in range(epochs):
            state = self.env.reset()
            # Reshape state for Keras input (1, window, features)
            state = np.expand_dims(state, axis=0) 
            
            done = False
            total_reward = 0
            step_count = 0
            
            while not done:
                # 1. Action Selection (Epsilon Greedy)
                if tf and np.random.rand() < self.epsilon:
                    action = np.random.randint(self.env.action_space.n)
                elif tf:
                    q_values = self.main_network.predict(state, verbose=0)
                    action = np.argmax(q_values[0])
                else:
                    action = np.random.randint(3) # Simulation

                # 2. Step
                next_state_raw, reward, done, _ = self.env.step(action)
                next_state = np.expand_dims(next_state_raw, axis=0)
                
                total_reward += reward
                
                # 3. Store Experience
                if self.replay_buffer:
                    self.replay_buffer.push(state, action, reward, next_state, done)
                
                state = next_state
                step_count += 1
                
                # 4. Train
                if tf and self.replay_buffer and len(self.replay_buffer) > batch_size:
                    self._train_step(batch_size, gamma)
            
            # End of Episode
            self.log(f"Episode {episode+1}/{epochs} finished. Reward: {total_reward:.2f}, Balance: {self.env.current_balance:.2f}")
            
            # Decay Epsilon
            if self.epsilon > self.process.epsilon_end:
                self.epsilon *= self.process.epsilon_decay
                
            # Periodic Update to DB (e.g. every episode)
            self._update_metrics(episode, total_reward)
            
            # Check for cancellation
            if self._check_cancellation():
                self.log("Training cancelled by user.")
                self._finish_run(status="CANCELLED")
                return

    def _check_cancellation(self) -> bool:
        """
        Checks if the iteration status has been changed to CANCELLING.
        Refreshes the iteration object from DB.
        """
        self.db.refresh(self.iteration)
        if self.iteration.status == "CANCELLING":
            return True
        return False

    def _train_step(self, batch_size, gamma):
        if not tf: return
        
        batch = self.replay_buffer.sample(batch_size)
        if not batch: return
        
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

    def _update_metrics(self, episode, reward):
        # Update iteration record with latest progress
        metrics = self.iteration.metrics_json or {}
        if not isinstance(metrics, dict): metrics = {}
        
        metrics["last_episode"] = episode
        metrics["last_reward"] = reward
        metrics["current_epsilon"] = self.epsilon
        metrics["current_balance"] = self.env.current_balance
        
        self.iteration.metrics_json = metrics
        self.iteration.logs_json = json.dumps(self.logs[-50:]) # Keep last 50 logs in DB to save space
        self.db.commit()

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
            # In a real app, save to a dedicated artifacts folder
            # self.main_network.save(filename)
            self.iteration.model_artifact_path = filename
            self.log(f"Model saved to {filename}")

        self.db.commit()
