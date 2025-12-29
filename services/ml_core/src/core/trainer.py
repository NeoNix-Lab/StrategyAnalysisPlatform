# -*- coding: utf-8 -*-
"""
Trainer module for DQN training with EnvFlex, replay buffer, and model management.
"""
import os
import time
import logging
from typing import Optional, Tuple, Dict, Any, List

import numpy as np
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.optimizers import Optimizer
from tensorflow.keras.losses import Loss
# from tensorflow.keras.callbacks import TensorBoard, ModelCheckpoint

from .environment import EnvFlex
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
            main_network: Model,
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
    ):
        self.env = env
        self.main_network = main_network
        self.target_network = tf.keras.models.clone_model(main_network)
        self.target_network.set_weights(main_network.get_weights())

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

        # Paths and logging
        timestamp = time.time()
        date_str = time.strftime('%Y%m%d_%H%M%S', time.localtime(timestamp))
        self.base_path = os.path.join(log_dir, f"{training_name}_{date_str}")
        os.makedirs(self.base_path, exist_ok=True)
        self.logger = self._setup_logger(self.base_path)

    def _setup_logger(self, path: str) -> logging.Logger:
        logger = logging.getLogger(f"Trainer_{id(self)}")
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
        # Using .keras format is recommended for Keras 3, but .h5 is legacy compatible.
        self.main_network.save(save_path)
        self.logger.info(f"Model saved to {save_path}")

    def load_model(self, path: str) -> None:
        loaded = tf.keras.models.load_model(path)
        self.main_network.set_weights(loaded.get_weights())
        self.target_network.set_weights(loaded.get_weights())
        self.logger.info(f"Model loaded from {path}")

    def train(self, num_episodes: int, batch_size: int, mode: str = 'batch') -> None:
        # Ensure network is compiled (safeguard)
        if not self.main_network.optimizer:
            self.compile_networks()

        for ep in range(num_episodes):
            episode_path = os.path.join(self.base_path, f"episode_{ep}")
            os.makedirs(episode_path, exist_ok=True)
            
            # Reset Env
            obs = self.env.reset()
            episode_reward = 0.0
            done = False
            
            # For logging stats
            step_count = 0

            while not done:
                action = self.epsilon_greedy_action(obs)
                next_obs, reward, done, info = self.env.step(action)
                episode_reward += reward

                self.replay_buffer.push(obs, action, reward, next_obs, done)
                
                # Learning step
                bs = 1 if mode == 'step' else batch_size
                if len(self.replay_buffer) >= bs:
                    batch = self.replay_buffer.sample(bs)
                    if batch:
                        self._learn_from_batch(batch)

                obs = next_obs
                step_count += 1

            # End of episode
            self.logger.info(f"Episode {ep} finished. Steps: {step_count} Reward: {episode_reward:.2f} Epsilon: {self.epsilon:.4f}")
            # Save model at end of episode
            self.save_model(os.path.join(episode_path, 'model.h5'))

    def epsilon_greedy_action(self, state: np.ndarray) -> int:
        if np.random.rand() < self.epsilon:
            action = self.env.action_space.sample()
        else:
            q_vals = self.main_network.predict(state[np.newaxis, ...], verbose=0)[0]
            action = int(np.argmax(q_vals))
        
        # Decay epsilon
        self.epsilon = max(self.epsilon - self.epsilon_decay, self.epsilon_end)
        return action

    def _learn_from_batch(self, batch: Tuple[np.ndarray, ...]) -> None:
        states, actions, rewards, next_states, dones = batch
        
        # Compute targets
        target_q = self.target_network.predict(next_states, verbose=0)
        max_q = np.max(target_q, axis=1)
        # Q_target = r + gamma * max(Q(s', a')) * (1 - done)
        targets = rewards + self.gamma * max_q * (1 - dones.astype(np.float32))

        # Gradient update
        with tf.GradientTape() as tape:
            preds = self.main_network(states, training=True)
            # Gather Q-values for the taken actions
            # One-hot encoding actions to mask outputs
            masks = tf.one_hot(actions, self.env.action_space.n)
            q_vals = tf.reduce_sum(preds * masks, axis=1)
            
            loss = self.loss_fn(targets, q_vals)
            
        grads = tape.gradient(loss, self.main_network.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.main_network.trainable_variables))

        # Soft update target network
        tw = self.target_network.get_weights()
        mw = self.main_network.get_weights()
        new_weights = [self.tau * m + (1 - self.tau) * t for t, m in zip(tw, mw)]
        self.target_network.set_weights(new_weights)
