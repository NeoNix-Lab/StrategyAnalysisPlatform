# -*- coding: utf-8 -*-
"""
Trainer module for DQN training with EnvFlex, replay buffer, and model management.
Optimized for Graph Execution via @tf.function.
"""
import os
import time
import logging
from typing import Optional, Tuple, Dict, Any, List, Callable

import numpy as np
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.optimizers import Optimizer
from tensorflow.keras.losses import Loss
# from tensorflow.keras.callbacks import TensorBoard, ModelCheckpoint

from .environment import EnvFlex
from .models import CustomDQNModel
# We need ReplayBuffer. We can inline it or create a file. 
# ReplayBuffer is small, I will implement a basic one here to keep files self-contained 
# or I should check if I should create replay_buffer.py. 
# The original has it in a separate file. I'll create a simple inner class or import it.
# Let's verify if I should create replay_buffer.py. Yes, cleaner.
# For now, I'll assume I'll create `replay_buffer.py` next.
from .replay_buffer import ReplayBuffer

class Trainer:
    """
    Deep Q-Network trainer integrating EnvFlex environment, replay buffer,
    epsilon-greedy policy, soft target updates, and model persistence.
    """

    def __init__(
            self,
            env: EnvFlex,
            main_network: CustomDQNModel,
            optimizer: Optimizer,
            loss_fn: Loss,
            gamma: float,
            tau: float,
            epsilon_start: float,
            epsilon_end: float,
            epsilon_decay_steps: int,
            log_dir: str,
            training_name: str,
            epochs: int = 1,
            replay_capacity: int = 30000,
            log_every_steps: int = 2000,
    ):
        self.env = env
        
        # Legacy Refactor: Extract standard Keras model for training stability
        # We keep the custom object for metadata/saving, but train the internal keras model.
        self.custom_model_ref = main_network
        # Initialize with dummy input to build graph with the env feature dimension
        feature_count = self.env.observation_space.shape[1]
        dummy_input = np.zeros((1, main_network.window_size, feature_count))
        self.main_network = main_network.extract_standard_keras_model(shape=dummy_input)
        
        # Clone for target network
        self.target_network = tf.keras.models.clone_model(self.main_network)
        self.target_network.set_weights(self.main_network.get_weights())

        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.gamma = gamma
        self.tau = tau

        # Epsilon-greedy schedule
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = (epsilon_start - epsilon_end) / max(epsilon_decay_steps, 1)

        # Training parameters
        self.epochs = epochs
        self.replay_buffer = ReplayBuffer(capacity=replay_capacity)
        self.log_every_steps = max(int(log_every_steps), 0)

        # Paths and logging
        timestamp = time.time()
        date_str = time.strftime('%Y%m%d_%H%M%S', time.localtime(timestamp))
        self.base_path = os.path.join(log_dir, f"{training_name}_{date_str}")
        os.makedirs(self.base_path, exist_ok=True)
        self.logger = self._setup_logger(self.base_path)

    def _setup_logger(self, path: str) -> logging.Logger:
        logger = logging.getLogger(f"ml_core.trainer.{id(self)}")
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(os.path.join(path, 'training.log'))
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(fh)
        return logger

    def compile_networks(self) -> None:
        self.main_network.compile(optimizer=self.optimizer, loss=self.loss_fn)
        self.target_network.compile(optimizer=self.optimizer, loss=self.loss_fn)

    def save_model(self, path: Optional[str] = None) -> None:
        save_path = path or os.path.join(self.base_path, 'model.h5')
        self.main_network.save(save_path)
        self.logger.info(f"Model saved to {save_path}")

    def load_model(self, path: str) -> None:
        loaded = tf.keras.models.load_model(path)
        self.main_network.set_weights(loaded.get_weights())
        self.target_network.set_weights(loaded.get_weights())
        self.logger.info(f"Model loaded from {path}")

    def train(self, num_episodes: int, batch_size: int, mode: str = 'batch', is_inference: bool = False, price_column: str = "close", stop_signal: Optional[Callable[[], bool]] = None) -> List[Dict[str, Any]]:
        # Ensure network is compiled (safeguard)
        if not hasattr(self.main_network, 'optimizer') or not self.main_network.optimizer:
            self.compile_networks()

        all_history = []

        for ep in range(num_episodes):
            if stop_signal and stop_signal():
                self.logger.info("Training interrupted by stop signal.")
                break

            episode_path = os.path.join(self.base_path, f"episode_{ep}")
            os.makedirs(episode_path, exist_ok=True)
            self.logger.info(
                "Episode %s start | window=%s features=%s epsilon=%.4f inference=%s",
                ep,
                self.env.window_size,
                self.env.observation_space.shape[1],
                self.epsilon,
                is_inference
            )
            
            # Reset Env
            obs = self.env.reset()
            episode_reward = 0.0
            done = False
            
            # For logging stats
            step_count = 0
            
            while not done:
                if stop_signal and stop_signal():
                    self.logger.info("Training interrupted during episode step.")
                    # Force exit cleanly
                    break

                action = self.epsilon_greedy_action(obs)
                
                next_obs, reward, done, info = self.env.step(action)
                episode_reward += reward

                if not is_inference:
                    self.replay_buffer.push(obs, action, reward, next_obs, done)
                    
                    # Learning step
                    bs = 1 if mode == 'step' else batch_size
                    if len(self.replay_buffer) >= bs:
                        batch = self.replay_buffer.sample(bs)
                        if batch:
                            self._learn_from_batch(batch)
                
                # OPTIMIZATION: Logic removed. We rely on EnvFlex internal logging.
                # History is batch-retrieved at end of episode.

                obs = next_obs
                step_count += 1

                if self.log_every_steps > 0 and step_count % self.log_every_steps == 0:
                    avg_reward = episode_reward / max(step_count, 1)
                    self.logger.info(
                        "Episode %s progress | step=%s avg_reward=%.4f epsilon=%.4f",
                        ep,
                        step_count,
                        avg_reward,
                        self.epsilon
                    )

            # End of episode
            self.logger.info(f"Episode {ep} finished. Steps: {step_count} Reward: {episode_reward:.2f} Epsilon: {self.epsilon:.4f}")
            
            if is_inference:
                # Optimized Retrieval
                episode_history = self.env.get_inference_log(price_column=price_column)
                all_history.extend(episode_history)

        # Save final model after all episodes (only if Training)
        if not is_inference:
            self.save_model()
            
        return all_history

    def epsilon_greedy_action(self, state: np.ndarray) -> int:
        if np.random.rand() < self.epsilon:
            action = int(self.env.action_space.sample())
        else:
            # OPTIMIZED: Use __call__ instead of .predict() to avoid overhead
            state_tensor = tf.convert_to_tensor(state[np.newaxis, ...], dtype=tf.float32)
            q_vals = self.main_network(state_tensor, training=False)[0]
            
            # Handle sequence output: (Time, Actions) -> take last step
            if len(q_vals.shape) == 2:
                q_vals = q_vals[-1]
                
            # Convert to numpy if needed, or tf.argmax
            action = int(tf.argmax(q_vals).numpy())
        
        # Decay epsilon
        self.epsilon = max(self.epsilon - self.epsilon_decay, self.epsilon_end)
        return action

    @tf.function
    def _learn_from_batch(self, batch: Tuple[Any, ...]) -> None:
        """
        Execute a training step using a batch of transitions.
        decorated with @tf.function for Graph Execution (Performance Optimization).
        """
        states, actions, rewards, next_states, dones = batch
        
        # Ensure inputs are tensors (usually automatic, but good for safety if passed from numpy)
        # tf.function handles numpy inputs by converting them to tensors automatically.

        # 1. Expand dimensions for broadcasting
        # We use tf.expand_dims instead of np.expand_dims
        if len(rewards.shape) == 1:
            rewards = tf.expand_dims(rewards, axis=1) # (BS, 1)

        dones_float = tf.cast(dones, tf.float32)
        term = 1.0 - dones_float
        _term = tf.expand_dims(term, axis=1) # (BS, 1)

        # 2. Compute Target Q-Values
        # Use __call__ instead of .predict() for Graph compatibility and speed
        target_preds = self.target_network(next_states, training=False)
        
        if len(target_preds.shape) == 3:
            target_preds = target_preds[:, -1, :]
            
        # Use tf.reduce_max instead of np.max
        max_q_next = tf.reduce_max(target_preds, axis=1, keepdims=True) # (BS, 1)

        # Q_target = r + gamma * max(Q(s')) * (1 - done)
        targets = rewards + (self.gamma * max_q_next * _term)

        # 3. Gradient Update
        with tf.GradientTape() as tape:
            preds = self.main_network(states, training=True)
            if len(preds.shape) == 3:
                preds = preds[:, -1, :]
            
            # Masking to get Q(s, a)
            # Ensure n_actions is available. self.env is a py_object, so accessing it inside graph 
            # might cause retracing if it changes, or we should treat n_actions as a constant.
            # Ideally self.env.n_actions is int.
            masks = tf.one_hot(actions, self.env.n_actions)
            q_action = tf.reduce_sum(preds * masks, axis=1, keepdims=True)
            
            loss = self.loss_fn(targets, q_action)
            
        grads = tape.gradient(loss, self.main_network.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.main_network.trainable_variables))

        # Soft update target network (Graph-compatible loop)
        for t, m in zip(self.target_network.trainable_variables, self.main_network.trainable_variables):
             t.assign(self.tau * m + (1 - self.tau) * t)
