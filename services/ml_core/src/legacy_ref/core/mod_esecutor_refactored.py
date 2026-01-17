# -*- coding: utf-8 -*-
"""
Trainer module for DQN training with EnvFlex, replay buffer, and model management.
"""
import os
import time
import logging
from typing import Optional, Tuple, Dict, Any, List

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.optimizers import Optimizer
from tensorflow.keras.losses import Loss

from .flex_env_refactored import EnvFlex
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
            #callbacks: Optional[List[Callback]] = None
    ):
        """
        Initialize the Trainer.

        Args:
            env (EnvFlex): Gym-like environment instance.
            main_network (Model): Primary Q-network model.
            optimizer (Optimizer): Optimizer for training.
            loss_fn (Loss): Loss function for Q-learning.
            gamma (float): Discount factor.
            tau (float): Soft update interpolation factor.
            epsilon_start (float): Initial exploration rate.
            epsilon_end (float): Minimum exploration rate.
            epsilon_decay_steps (int): Steps over which epsilon decays.
            log_dir (str): Base directory for logs and saved models.
            training_name (str): Subfolder name for this training run.
            epochs (int): Epochs per batch update.
            replay_capacity (int): Max capacity for replay buffer.
            callbacks (List[Callback], optional): Keras callbacks to use.
        """
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

        # TODO : handle tensorboard and callbacks
        # Callbacks for model training
        #self.callbacks = callbacks or []
        # Always include checkpoint and tensorboard
        #self._add_default_callbacks()

    def _setup_logger(self, path: str) -> logging.Logger:
        """
        Create and configure a file logger.

        Args:
            path (str): Directory where log file will be stored.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(f"Trainer_{id(self)}")
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(os.path.join(path, 'training.log'))
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(fh)
        return logger

    #def _add_default_callbacks(self) -> None:
    #    """
    #    Add default TensorBoard and ModelCheckpoint callbacks.
    #    """
    #    tb_path = os.path.join(self.base_path, 'tensorboard')
    #    os.makedirs(tb_path, exist_ok=True)
    #    self.callbacks.append(TensorBoard(log_dir=tb_path))
    #    ckpt_path = os.path.join(self.base_path, 'checkpoints', 'model_{epoch:02d}.h5')
    #    os.makedirs(os.path.dirname(ckpt_path), exist_ok=True)
    #    self.callbacks.append(ModelCheckpoint(filepath=ckpt_path, save_weights_only=False))

    def compile_networks(self) -> None:
        """
        Compile both main and target Q-networks with optimizer and loss function.
        """
        self.main_network.compile(optimizer=self.optimizer, loss=self.loss_fn)
        self.target_network.compile(optimizer=self.optimizer, loss=self.loss_fn)

    def save_model(self, path: Optional[str] = None) -> None:
        """
        Save the main network model to H5 file.

        Args:
            path (str, optional): Full path for saving; defaults to base_path/model.h5.
        """
        save_path = path or os.path.join(self.base_path, 'model.h5')
        self.main_network.save(save_path)
        self.logger.info(f"Model saved to {save_path}")

    def load_model(self, path: str) -> None:
        """
        Load a saved model into the main and target networks.

        Args:
            path (str): Path to the saved model file.
        """
        loaded = tf.keras.models.load_model(path)
        self.main_network.set_weights(loaded.get_weights())
        self.target_network.set_weights(loaded.get_weights())
        self.logger.info(f"Model loaded from {path}")

    def train(
            self,
            num_episodes: int,
            batch_size: int,
            mode: str = 'batch'
    ) -> None:
        """
        Execute training loop over episodes.

        Args:
            num_episodes (int): Number of episodes to train.
            batch_size (int): Size for replay sampling.
            mode (str): 'batch' or 'step' learning mode.
        """
        # Ensure network is compiled
        self.compile_network()

        for ep in range(num_episodes):
            episode_path = os.path.join(self.base_path, f"episode_{ep}")
            os.makedirs(episode_path, exist_ok=True)
            state = self.env.reset()
            episode_reward = 0.0
            done = False
            experiences = []

            while not done:
                action = self.epsilon_greedy_action(state)
                next_state, reward, done, info = self.env.step(action)
                episode_reward += reward

                self.replay_buffer.push(state, action, reward, next_state, done)
                experiences.append((state, action, reward, next_state, done))

                bs = 1 if mode == 'step' else batch_size
                batch = self.replay_buffer.sample(bs)
                if batch:
                    self._learn_from_batch(batch)

                state = next_state

            # End of episode
            self.logger.info(f"Episode {ep} reward: {episode_reward}")
            # Save model at end of episode
            self.save_model(os.path.join(episode_path, 'model.h5'))

    def epsilon_greedy_action(self, state: np.ndarray) -> int:
        """
        Choose an action using epsilon-greedy policy.
        """
        if np.random.rand() < self.epsilon:
            action = self.env.action_space.sample()
        else:
            q_vals = self.main_network.predict(state[np.newaxis, ...], verbose=0)[0]
            action = int(np.argmax(q_vals))
        self.epsilon = max(self.epsilon - self.epsilon_decay, self.epsilon_end)
        return action

    def _learn_from_batch(self, batch: Tuple[np.ndarray, ...]) -> None:
        """
        Perform learning step from a batch of experiences.
        """
        states, actions, rewards, next_states, dones = batch
        # Compute targets
        target_q = self.target_network.predict(next_states, verbose=0)
        max_q = np.max(target_q, axis=1)
        targets = rewards + self.gamma * max_q * (1 - dones.astype(np.float32))

        # Gradient update
        with tf.GradientTape() as tape:
            preds = self.main_network(states, training=True)
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

    def test_existing_model(
            self,
            model_path: str,
            data: pd.DataFrame
    ) -> List[np.ndarray]:
        """
        Test a saved model on new data.

        Args:
            model_path (str): Path to .h5 model file.
            data (pd.DataFrame): New dataset to set in environment.

        Returns:
            List[np.ndarray]: States observed during test rollout.
        """
        self.load_model(model_path)
        self.env.data = data.reset_index(drop=True)
        state = self.env.reset()
        done = False
        results = []
        while not done:
            q_vals = self.main_network.predict(state[np.newaxis, ...], verbose=0)[0]
            action = int(np.argmax(q_vals))
            state, _, done, _ = self.env.step(action)
            results.append(state)
        return results
