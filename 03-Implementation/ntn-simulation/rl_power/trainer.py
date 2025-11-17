#!/usr/bin/env python3
"""
Training Pipeline for DQN Power Control
========================================

Implements training loop with:
- Episode management
- Checkpoint saving
- TensorBoard logging
- Progress tracking
- Evaluation

Author: RL Specialist
Date: 2025-11-17
"""

import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class Trainer:
    """
    DQN Training Pipeline

    Manages training loop, checkpointing, and evaluation.
    """

    def __init__(self, env, agent, config: Dict[str, Any]):
        """
        Initialize trainer

        Args:
            env: NTN power control environment
            agent: DQN agent
            config: Training configuration
        """
        self.env = env
        self.agent = agent
        self.config = config

        # Training parameters
        self.num_episodes = config.get('num_episodes', 1000)
        self.batch_size = config.get('batch_size', 64)
        self.eval_frequency = config.get('eval_frequency', 50)
        self.num_eval_episodes = config.get('num_eval_episodes', 10)
        self.checkpoint_frequency = config.get('checkpoint_frequency', 100)
        self.save_dir = Path(config.get('save_dir', './rl_power_models'))
        self.verbose = config.get('verbose', True)

        # Early stopping
        self.early_stopping = config.get('early_stopping', False)
        self.patience = config.get('patience', 50)
        self.min_improvement = config.get('min_improvement', 1.0)

        # Create save directory
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # Training history
        self.history = {
            'episode_rewards': [],
            'episode_lengths': [],
            'losses': [],
            'eval_rewards': [],
            'eval_episodes': [],
            'epsilon_values': [],
            'training_time': 0.0
        }

        # Best model tracking
        self.best_eval_reward = -float('inf')
        self.episodes_without_improvement = 0

        print(f"[Trainer] Initialized")
        print(f"  Episodes: {self.num_episodes}")
        print(f"  Batch size: {self.batch_size}")
        print(f"  Save directory: {self.save_dir}")

    def run_episode(self, train: bool = True) -> Tuple[float, int]:
        """
        Run single episode

        Args:
            train: Whether to train agent during episode

        Returns:
            episode_reward: Total reward for episode
            episode_length: Number of steps in episode
        """
        obs, _ = self.env.reset()
        episode_reward = 0.0
        episode_length = 0

        while True:
            # Select action
            action = self.agent.select_action(obs, explore=train)

            # Take step
            next_obs, reward, terminated, truncated, info = self.env.step(action)

            episode_reward += reward
            episode_length += 1

            if train:
                # Store transition
                self.agent.store_transition(obs, action, reward, next_obs, terminated or truncated)

                # Update agent
                if len(self.agent.replay_buffer) >= self.batch_size:
                    loss = self.agent.update(self.batch_size)
                    if loss is not None:
                        self.history['losses'].append(loss)

                    # Update target network periodically
                    if self.agent.training_step % self.agent.target_update_freq == 0:
                        self.agent.update_target_network()

            obs = next_obs

            if terminated or truncated:
                break

        return episode_reward, episode_length

    def evaluate(self, num_episodes: int = None) -> Dict[str, float]:
        """
        Evaluate current policy

        Args:
            num_episodes: Number of evaluation episodes

        Returns:
            Evaluation metrics
        """
        if num_episodes is None:
            num_episodes = self.num_eval_episodes

        self.agent.eval()

        eval_rewards = []
        eval_lengths = []

        for _ in range(num_episodes):
            reward, length = self.run_episode(train=False)
            eval_rewards.append(reward)
            eval_lengths.append(length)

        self.agent.train()

        return {
            'mean_reward': np.mean(eval_rewards),
            'std_reward': np.std(eval_rewards),
            'min_reward': np.min(eval_rewards),
            'max_reward': np.max(eval_rewards),
            'mean_length': np.mean(eval_lengths)
        }

    def train(self) -> Dict[str, Any]:
        """
        Main training loop

        Returns:
            Training history
        """
        print(f"\n{'='*70}")
        print(f"Starting Training - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        start_time = time.time()

        for episode in range(1, self.num_episodes + 1):
            # Run training episode
            episode_reward, episode_length = self.run_episode(train=True)

            # Record metrics
            self.history['episode_rewards'].append(episode_reward)
            self.history['episode_lengths'].append(episode_length)
            self.history['epsilon_values'].append(self.agent.epsilon)

            # Decay epsilon
            self.agent.decay_epsilon()

            # Print progress
            if self.verbose and episode % 10 == 0:
                recent_rewards = self.history['episode_rewards'][-10:]
                recent_losses = self.history['losses'][-100:] if self.history['losses'] else [0]
                print(f"Episode {episode:4d} | "
                      f"Reward: {episode_reward:7.2f} | "
                      f"Avg Reward (10): {np.mean(recent_rewards):7.2f} | "
                      f"Loss: {np.mean(recent_losses):7.4f} | "
                      f"Epsilon: {self.agent.epsilon:.4f} | "
                      f"Buffer: {len(self.agent.replay_buffer)}")

            # Evaluate periodically
            if episode % self.eval_frequency == 0:
                eval_metrics = self.evaluate()
                self.history['eval_rewards'].append(eval_metrics['mean_reward'])
                self.history['eval_episodes'].append(episode)

                print(f"\n{'='*70}")
                print(f"Evaluation at Episode {episode}")
                print(f"{'='*70}")
                print(f"Mean Reward: {eval_metrics['mean_reward']:.2f} ± {eval_metrics['std_reward']:.2f}")
                print(f"Min/Max: {eval_metrics['min_reward']:.2f} / {eval_metrics['max_reward']:.2f}")
                print(f"Mean Length: {eval_metrics['mean_length']:.1f}")
                print(f"{'='*70}\n")

                # Save best model
                if eval_metrics['mean_reward'] > self.best_eval_reward:
                    improvement = eval_metrics['mean_reward'] - self.best_eval_reward
                    self.best_eval_reward = eval_metrics['mean_reward']
                    self.episodes_without_improvement = 0

                    # Save best model
                    best_model_path = self.save_dir / 'best_model.pth'
                    self.agent.save(best_model_path)
                    print(f"New best model saved! Improvement: {improvement:.2f}\n")
                else:
                    self.episodes_without_improvement += self.eval_frequency

                # Early stopping check
                if self.early_stopping:
                    if self.episodes_without_improvement >= self.patience:
                        print(f"Early stopping: No improvement for {self.patience} episodes")
                        break

            # Save checkpoint
            if episode % self.checkpoint_frequency == 0:
                checkpoint_path = self.save_dir / f'checkpoint_{episode}.pth'
                self.agent.save(checkpoint_path)

        # Training complete
        training_time = time.time() - start_time
        self.history['training_time'] = training_time

        print(f"\n{'='*70}")
        print(f"Training Complete!")
        print(f"{'='*70}")
        print(f"Total episodes: {len(self.history['episode_rewards'])}")
        print(f"Training time: {training_time:.1f} seconds ({training_time/60:.1f} minutes)")
        print(f"Best eval reward: {self.best_eval_reward:.2f}")
        print(f"{'='*70}\n")

        # Save final model
        final_model_path = self.save_dir / 'final_model.pth'
        self.agent.save(final_model_path)

        # Save training history
        history_path = self.save_dir / 'training_history.json'
        self._save_history(history_path)

        return self.history

    def _save_history(self, path: Path):
        """Save training history to JSON"""
        # Convert numpy types to native Python types
        history_serializable = {}
        for key, value in self.history.items():
            if isinstance(value, list):
                history_serializable[key] = [float(v) if isinstance(v, (np.floating, np.integer)) else v
                                             for v in value]
            else:
                history_serializable[key] = float(value) if isinstance(value, (np.floating, np.integer)) else value

        with open(path, 'w') as f:
            json.dump(history_serializable, f, indent=2)

        print(f"Training history saved to {path}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get training metrics summary"""
        if not self.history['episode_rewards']:
            return {}

        return {
            'total_episodes': len(self.history['episode_rewards']),
            'final_avg_reward': np.mean(self.history['episode_rewards'][-100:]),
            'best_eval_reward': self.best_eval_reward,
            'final_epsilon': self.agent.epsilon,
            'training_time': self.history['training_time'],
            'total_training_steps': self.agent.training_step
        }


# Test function
def test_trainer():
    """Test trainer with small training run"""
    print("Testing Trainer")
    print("=" * 50)

    from rl_power.ntn_env import NTNPowerEnvironment
    from rl_power.dqn_agent import DQNAgent

    # Create environment
    env = NTNPowerEnvironment()

    # Create agent
    agent_config = {
        'state_dim': 5,
        'action_dim': 5,
        'hidden_dims': [64, 64],  # Smaller for testing
        'lr': 0.001,
        'gamma': 0.99,
        'epsilon_start': 1.0,
        'epsilon_end': 0.1,
        'epsilon_decay': 0.99,
        'target_update_freq': 10,
        'buffer_capacity': 1000
    }
    agent = DQNAgent(agent_config)

    # Create trainer
    trainer_config = {
        'num_episodes': 20,
        'batch_size': 32,
        'eval_frequency': 10,
        'num_eval_episodes': 3,
        'checkpoint_frequency': 10,
        'save_dir': './test_models',
        'verbose': True
    }
    trainer = Trainer(env, agent, trainer_config)

    # Train
    history = trainer.train()

    print("\nTraining metrics:")
    metrics = trainer.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    print("\nTrainer test completed!")


if __name__ == '__main__':
    test_trainer()
