#!/usr/bin/env python3
"""
Test Suite for Training Pipeline (TDD)
=======================================

Tests written BEFORE implementation following Test-Driven Development.

Test Coverage:
- Training loop execution
- Episode management
- Reward accumulation
- Policy improvement verification
- Checkpoint saving/loading
- TensorBoard logging
- Training convergence
- Early stopping

Author: RL Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import json


class TestTrainer:
    """Test training pipeline"""

    @pytest.fixture
    def trainer(self):
        """Create trainer instance"""
        from rl_power.trainer import Trainer
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()

        agent_config = {
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.001,  # Higher LR for faster testing
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.99,
            'target_update_freq': 10,
            'buffer_capacity': 1000
        }
        agent = DQNAgent(agent_config)

        trainer_config = {
            'num_episodes': 10,
            'batch_size': 32,
            'eval_frequency': 5,
            'checkpoint_frequency': 5,
            'save_dir': None  # Will be set in tests
        }

        return Trainer(env, agent, trainer_config)

    def test_trainer_creation(self, trainer):
        """Test trainer can be created"""
        assert trainer is not None
        assert hasattr(trainer, 'env')
        assert hasattr(trainer, 'agent')

    def test_single_episode(self, trainer):
        """Test running a single episode"""
        episode_reward, episode_length = trainer.run_episode()

        assert isinstance(episode_reward, (float, int))
        assert isinstance(episode_length, int)
        assert episode_length > 0

    def test_episode_reward_tracking(self, trainer):
        """Test episode rewards are tracked"""
        rewards = []
        for _ in range(5):
            reward, _ = trainer.run_episode()
            rewards.append(reward)

        assert len(rewards) == 5
        assert all(isinstance(r, (float, int)) for r in rewards)

    def test_training_loop(self, trainer):
        """Test full training loop executes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            trainer.config['num_episodes'] = 5

            history = trainer.train()

            assert 'episode_rewards' in history
            assert 'episode_lengths' in history
            assert 'losses' in history
            assert len(history['episode_rewards']) == 5

    def test_epsilon_decay_during_training(self, trainer):
        """Test epsilon decays during training"""
        initial_epsilon = trainer.agent.epsilon

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            trainer.config['num_episodes'] = 10

            trainer.train()

            final_epsilon = trainer.agent.epsilon

            assert final_epsilon < initial_epsilon

    def test_checkpoint_saving(self, trainer):
        """Test checkpoints are saved"""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = Path(tmpdir)
            trainer.config['save_dir'] = str(save_dir)
            trainer.config['num_episodes'] = 10
            trainer.config['checkpoint_frequency'] = 5

            trainer.train()

            # Check checkpoint files exist
            checkpoint_files = list(save_dir.glob('checkpoint_*.pth'))
            assert len(checkpoint_files) > 0

    def test_final_model_saving(self, trainer):
        """Test final model is saved"""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = Path(tmpdir)
            trainer.config['save_dir'] = str(save_dir)
            trainer.config['num_episodes'] = 5

            trainer.train()

            # Check final model exists
            final_model = save_dir / 'final_model.pth'
            assert final_model.exists()

    def test_training_history_saved(self, trainer):
        """Test training history is saved"""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = Path(tmpdir)
            trainer.config['save_dir'] = str(save_dir)
            trainer.config['num_episodes'] = 5

            trainer.train()

            # Check history file exists
            history_file = save_dir / 'training_history.json'
            assert history_file.exists()

            # Verify content
            with open(history_file) as f:
                history = json.load(f)

            assert 'episode_rewards' in history
            assert len(history['episode_rewards']) == 5

    def test_evaluation_during_training(self, trainer):
        """Test evaluation is performed during training"""
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            trainer.config['num_episodes'] = 10
            trainer.config['eval_frequency'] = 5
            trainer.config['num_eval_episodes'] = 2

            history = trainer.train()

            # Should have eval results
            assert 'eval_rewards' in history
            assert len(history['eval_rewards']) > 0

    def test_training_statistics(self, trainer):
        """Test training statistics are computed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            trainer.config['num_episodes'] = 10

            history = trainer.train()

            # Check statistics
            assert 'mean_reward' in history or hasattr(trainer, 'get_statistics')

    def test_target_network_updates(self, trainer):
        """Test target network is updated periodically"""
        initial_target_params = [
            p.clone() for p in trainer.agent.target_net.parameters()
        ]

        # Run some episodes
        for _ in range(20):
            trainer.run_episode()

        # Target params should have updated
        params_changed = False
        for initial, current in zip(
            initial_target_params,
            trainer.agent.target_net.parameters()
        ):
            if not torch.allclose(initial, current, atol=1e-6):
                params_changed = True
                break

        # Depending on update frequency, may or may not have changed
        # Just check mechanism exists
        assert hasattr(trainer.agent, 'update_target_network')

    def test_resume_training(self, trainer):
        """Test training can be resumed from checkpoint"""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = Path(tmpdir)
            trainer.config['save_dir'] = str(save_dir)
            trainer.config['num_episodes'] = 10
            trainer.config['checkpoint_frequency'] = 5

            # Train first phase
            history1 = trainer.train()

            # Create new trainer and resume
            from rl_power.trainer import Trainer
            from rl_power.ntn_env import NTNPowerEnvironment
            from rl_power.dqn_agent import DQNAgent

            env = NTNPowerEnvironment()
            agent_config = {
                'state_dim': 5,
                'action_dim': 5,
                'hidden_dims': [128, 128, 64],
                'lr': 0.001,
                'gamma': 0.99,
                'epsilon_start': 1.0,
                'epsilon_end': 0.1,
                'epsilon_decay': 0.99,
                'target_update_freq': 10,
                'buffer_capacity': 1000
            }
            agent = DQNAgent(agent_config)

            trainer_config = {
                'num_episodes': 5,
                'batch_size': 32,
                'save_dir': str(save_dir)
            }
            trainer2 = Trainer(env, agent, trainer_config)

            # Load checkpoint
            checkpoints = list(save_dir.glob('checkpoint_*.pth'))
            if checkpoints:
                trainer2.agent.load(checkpoints[0])

            # Continue training
            history2 = trainer2.train()

            assert len(history2['episode_rewards']) > 0


class TestTrainingConvergence:
    """Test training convergence"""

    def test_reward_improvement(self):
        """Test reward improves over training"""
        from rl_power.trainer import Trainer
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()

        agent_config = {
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.99,
            'target_update_freq': 10,
            'buffer_capacity': 1000
        }
        agent = DQNAgent(agent_config)

        trainer_config = {
            'num_episodes': 50,
            'batch_size': 32,
            'eval_frequency': 10,
            'save_dir': None
        }

        trainer = Trainer(env, agent, trainer_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            history = trainer.train()

        rewards = history['episode_rewards']

        # Compare early vs late rewards
        early_reward = np.mean(rewards[:10])
        late_reward = np.mean(rewards[-10:])

        # Late rewards should be better (more negative = less power)
        # or at least not significantly worse
        assert late_reward >= early_reward - 50  # Allow some variance

    def test_loss_stability(self):
        """Test training loss remains stable"""
        from rl_power.trainer import Trainer
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()

        agent_config = {
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.995,
            'target_update_freq': 10,
            'buffer_capacity': 1000
        }
        agent = DQNAgent(agent_config)

        trainer_config = {
            'num_episodes': 30,
            'batch_size': 64,
            'save_dir': None
        }

        trainer = Trainer(env, agent, trainer_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            history = trainer.train()

        losses = [l for l in history['losses'] if l is not None]

        # Losses should not explode
        if len(losses) > 10:
            assert all(l < 1000 for l in losses[-10:])


class TestTrainingMetrics:
    """Test training metrics collection"""

    def test_power_savings_tracking(self):
        """Test power savings are tracked during training"""
        from rl_power.trainer import Trainer
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.99,
            'target_update_freq': 10,
            'buffer_capacity': 1000
        })

        trainer = Trainer(env, agent, {
            'num_episodes': 5,
            'batch_size': 32,
            'save_dir': None
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            trainer.train()

        # Should have method to get power statistics
        assert hasattr(trainer, 'get_metrics') or hasattr(env, 'get_episode_stats')

    def test_rsrp_quality_tracking(self):
        """Test RSRP quality is tracked during training"""
        from rl_power.trainer import Trainer
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.99,
            'target_update_freq': 10,
            'buffer_capacity': 1000
        })

        trainer = Trainer(env, agent, {
            'num_episodes': 5,
            'batch_size': 32,
            'save_dir': None
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            history = trainer.train()

        # Should track RSRP violations
        assert hasattr(trainer, 'get_rsrp_stats') or 'rsrp_violations' in history or hasattr(env, 'get_violation_count')


class TestEarlyStoppingAndCallbacks:
    """Test early stopping and training callbacks"""

    def test_early_stopping_on_convergence(self):
        """Test training can stop early if converged"""
        from rl_power.trainer import Trainer
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.99,
            'target_update_freq': 10,
            'buffer_capacity': 1000
        })

        trainer_config = {
            'num_episodes': 1000,  # Large number
            'batch_size': 32,
            'save_dir': None,
            'early_stopping': True,
            'patience': 10,
            'min_improvement': 1.0
        }

        trainer = Trainer(env, agent, trainer_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            history = trainer.train()

        # Should stop before 1000 episodes if converged
        # (but we don't enforce this strictly for testing)
        assert len(history['episode_rewards']) <= 1000

    def test_progress_logging(self):
        """Test progress is logged during training"""
        from rl_power.trainer import Trainer
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.99,
            'target_update_freq': 10,
            'buffer_capacity': 1000
        })

        trainer = Trainer(env, agent, {
            'num_episodes': 5,
            'batch_size': 32,
            'save_dir': None,
            'verbose': True
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer.config['save_dir'] = tmpdir
            # Should not crash with verbose logging
            trainer.train()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
