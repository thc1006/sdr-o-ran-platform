#!/usr/bin/env python3
"""
Test Suite for DQN Agent (TDD)
===============================

Tests written BEFORE implementation following Test-Driven Development.

Test Coverage:
- Neural network architecture
- Experience replay buffer operations
- Epsilon-greedy exploration
- Q-value prediction and updates
- Target network synchronization
- Model saving and loading
- Training stability
- Gradient flow

Author: RL Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import torch
import tempfile
import os
from pathlib import Path


class TestDQNNetwork:
    """Test DQN neural network architecture"""

    @pytest.fixture
    def network(self):
        """Create DQN network instance"""
        from rl_power.dqn_agent import DQNNetwork
        state_dim = 5
        action_dim = 5
        hidden_dims = [128, 128, 64]
        return DQNNetwork(state_dim, action_dim, hidden_dims)

    def test_network_creation(self, network):
        """Test network can be instantiated"""
        assert network is not None
        assert isinstance(network, torch.nn.Module)

    def test_network_architecture(self, network):
        """Test network has correct architecture"""
        # Should have 3 hidden layers + output layer
        layers = [m for m in network.modules() if isinstance(m, torch.nn.Linear)]
        assert len(layers) >= 3  # At least 3 linear layers

    def test_forward_pass_shape(self, network):
        """Test forward pass returns correct output shape"""
        batch_size = 32
        state_dim = 5
        action_dim = 5

        states = torch.randn(batch_size, state_dim)
        q_values = network(states)

        assert q_values.shape == (batch_size, action_dim)

    def test_forward_pass_single_state(self, network):
        """Test forward pass with single state"""
        state = torch.randn(5)
        q_values = network(state.unsqueeze(0))

        assert q_values.shape == (1, 5)

    def test_output_values_finite(self, network):
        """Test network outputs are finite"""
        states = torch.randn(10, 5)
        q_values = network(states)

        assert torch.isfinite(q_values).all()

    def test_gradient_flow(self, network):
        """Test gradients flow through network"""
        states = torch.randn(32, 5, requires_grad=True)
        q_values = network(states)
        loss = q_values.mean()
        loss.backward()

        # Check gradients exist
        has_grad = False
        for param in network.parameters():
            if param.grad is not None:
                has_grad = True
                break

        assert has_grad, "No gradients computed"

    def test_parameter_initialization(self, network):
        """Test parameters are properly initialized"""
        for param in network.parameters():
            # Check no NaN or Inf
            assert torch.isfinite(param).all()
            # Check not all zeros
            assert not torch.allclose(param, torch.zeros_like(param))


class TestReplayBuffer:
    """Test experience replay buffer"""

    @pytest.fixture
    def buffer(self):
        """Create replay buffer instance"""
        from rl_power.dqn_agent import ReplayBuffer
        return ReplayBuffer(capacity=1000)

    def test_buffer_creation(self, buffer):
        """Test buffer can be created"""
        assert buffer is not None
        assert buffer.capacity == 1000

    def test_buffer_push(self, buffer):
        """Test adding experiences to buffer"""
        state = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        action = 2
        reward = -0.5
        next_state = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        done = False

        buffer.push(state, action, reward, next_state, done)

        assert len(buffer) == 1

    def test_buffer_capacity(self, buffer):
        """Test buffer respects capacity limit"""
        capacity = buffer.capacity

        # Add more than capacity
        for i in range(capacity + 100):
            state = np.random.randn(5)
            buffer.push(state, 0, 0.0, state, False)

        assert len(buffer) == capacity

    def test_buffer_sample(self, buffer):
        """Test sampling from buffer"""
        # Add some experiences
        for i in range(100):
            state = np.random.randn(5)
            buffer.push(state, i % 5, -1.0, state, False)

        # Sample batch
        batch = buffer.sample(32)

        assert len(batch) == 5  # (states, actions, rewards, next_states, dones)
        states, actions, rewards, next_states, dones = batch

        assert states.shape == (32, 5)
        assert actions.shape == (32,)
        assert rewards.shape == (32,)
        assert next_states.shape == (32, 5)
        assert dones.shape == (32,)

    def test_buffer_sample_smaller_than_batch(self, buffer):
        """Test sampling when buffer has fewer samples than batch size"""
        # Add only 10 samples
        for i in range(10):
            state = np.random.randn(5)
            buffer.push(state, 0, 0.0, state, False)

        # Try to sample 32
        with pytest.raises((ValueError, AssertionError)):
            buffer.sample(32)

    def test_buffer_sample_randomness(self, buffer):
        """Test samples are random"""
        for i in range(100):
            state = np.array([float(i)] * 5)
            buffer.push(state, i % 5, float(i), state, False)

        batch1 = buffer.sample(32)
        batch2 = buffer.sample(32)

        # Batches should be different (with high probability)
        states1, _, _, _, _ = batch1
        states2, _, _, _, _ = batch2

        assert not np.array_equal(states1, states2)

    def test_buffer_clear(self, buffer):
        """Test buffer can be cleared"""
        for i in range(50):
            state = np.random.randn(5)
            buffer.push(state, 0, 0.0, state, False)

        assert len(buffer) > 0

        if hasattr(buffer, 'clear'):
            buffer.clear()
            assert len(buffer) == 0


class TestDQNAgent:
    """Test DQN agent"""

    @pytest.fixture
    def agent(self):
        """Create DQN agent instance"""
        from rl_power.dqn_agent import DQNAgent
        config = {
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.995,
            'target_update_freq': 100,
            'buffer_capacity': 10000
        }
        return DQNAgent(config)

    def test_agent_creation(self, agent):
        """Test agent can be created"""
        assert agent is not None
        assert hasattr(agent, 'policy_net')
        assert hasattr(agent, 'target_net')
        assert hasattr(agent, 'replay_buffer')

    def test_target_network_initialization(self, agent):
        """Test target network is initialized same as policy network"""
        for target_param, policy_param in zip(
            agent.target_net.parameters(),
            agent.policy_net.parameters()
        ):
            assert torch.allclose(target_param, policy_param)

    def test_select_action_exploration(self, agent):
        """Test action selection during exploration"""
        state = np.random.randn(5)

        # With epsilon=1.0, should explore (random actions)
        agent.epsilon = 1.0

        actions = []
        for _ in range(100):
            action = agent.select_action(state)
            actions.append(action)

        # Should see variety of actions
        unique_actions = len(set(actions))
        assert unique_actions > 1  # More than one action selected

    def test_select_action_exploitation(self, agent):
        """Test action selection during exploitation"""
        state = np.random.randn(5)

        # With epsilon=0.0, should exploit (greedy)
        agent.epsilon = 0.0

        actions = []
        for _ in range(10):
            action = agent.select_action(state)
            actions.append(action)

        # Should select same action consistently
        assert len(set(actions)) == 1

    def test_select_action_valid_range(self, agent):
        """Test selected actions are in valid range"""
        state = np.random.randn(5)

        for _ in range(100):
            action = agent.select_action(state)
            assert 0 <= action < 5  # Valid action index

    def test_store_transition(self, agent):
        """Test storing transitions in replay buffer"""
        state = np.random.randn(5)
        action = 2
        reward = -1.0
        next_state = np.random.randn(5)
        done = False

        initial_buffer_size = len(agent.replay_buffer)
        agent.store_transition(state, action, reward, next_state, done)

        assert len(agent.replay_buffer) == initial_buffer_size + 1

    def test_update_no_sufficient_samples(self, agent):
        """Test update does nothing when insufficient samples"""
        # Add only a few samples
        for _ in range(10):
            state = np.random.randn(5)
            agent.store_transition(state, 0, 0.0, state, False)

        # Should not crash with small buffer
        loss = agent.update(batch_size=64)
        assert loss is None or loss == 0.0

    def test_update_with_sufficient_samples(self, agent):
        """Test update computes loss and updates network"""
        # Fill buffer
        for _ in range(200):
            state = np.random.randn(5)
            action = np.random.randint(0, 5)
            reward = np.random.randn()
            next_state = np.random.randn(5)
            done = np.random.random() < 0.1

            agent.store_transition(state, action, reward, next_state, done)

        # Get initial parameters
        initial_params = [p.clone() for p in agent.policy_net.parameters()]

        # Perform update
        loss = agent.update(batch_size=64)

        assert loss is not None
        assert loss >= 0  # Loss should be non-negative

        # Parameters should change
        params_changed = False
        for initial, current in zip(initial_params, agent.policy_net.parameters()):
            if not torch.allclose(initial, current, atol=1e-6):
                params_changed = True
                break

        assert params_changed, "Network parameters did not update"

    def test_target_network_update(self, agent):
        """Test target network is updated from policy network"""
        # Train policy network a bit
        for _ in range(200):
            state = np.random.randn(5)
            agent.store_transition(state, 0, -1.0, state, False)

        for _ in range(10):
            agent.update(batch_size=64)

        # Get policy params before target update
        policy_params_before = [p.clone() for p in agent.policy_net.parameters()]
        target_params_before = [p.clone() for p in agent.target_net.parameters()]

        # Networks should be different now
        params_differ = False
        for p_param, t_param in zip(policy_params_before, target_params_before):
            if not torch.allclose(p_param, t_param, atol=1e-6):
                params_differ = True
                break

        assert params_differ, "Policy and target networks should differ before update"

        # Update target network
        agent.update_target_network()

        # Now they should be the same
        for target_param, policy_param in zip(
            agent.target_net.parameters(),
            agent.policy_net.parameters()
        ):
            assert torch.allclose(target_param, policy_param)

    def test_epsilon_decay(self, agent):
        """Test epsilon decays over time"""
        initial_epsilon = agent.epsilon

        for _ in range(100):
            agent.decay_epsilon()

        final_epsilon = agent.epsilon

        assert final_epsilon < initial_epsilon
        assert final_epsilon >= agent.epsilon_end

    def test_epsilon_minimum(self, agent):
        """Test epsilon doesn't go below minimum"""
        # Decay many times
        for _ in range(10000):
            agent.decay_epsilon()

        assert agent.epsilon >= agent.epsilon_end

    def test_save_and_load_model(self, agent):
        """Test model can be saved and loaded"""
        # Train a bit to make params unique
        for _ in range(100):
            state = np.random.randn(5)
            agent.store_transition(state, 0, -1.0, state, False)

        for _ in range(10):
            agent.update(batch_size=64)

        # Save model
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_model.pth"
            agent.save(save_path)

            assert save_path.exists()

            # Create new agent
            from rl_power.dqn_agent import DQNAgent
            config = {
                'state_dim': 5,
                'action_dim': 5,
                'hidden_dims': [128, 128, 64],
                'lr': 0.0001,
                'gamma': 0.99,
                'epsilon_start': 1.0,
                'epsilon_end': 0.1,
                'epsilon_decay': 0.995,
                'target_update_freq': 100,
                'buffer_capacity': 10000
            }
            new_agent = DQNAgent(config)

            # Load model
            new_agent.load(save_path)

            # Parameters should match
            for orig_param, loaded_param in zip(
                agent.policy_net.parameters(),
                new_agent.policy_net.parameters()
            ):
                assert torch.allclose(orig_param, loaded_param)

    def test_get_q_values(self, agent):
        """Test getting Q-values for a state"""
        state = np.random.randn(5)

        q_values = agent.get_q_values(state)

        assert len(q_values) == 5  # One Q-value per action
        assert all(np.isfinite(q_values))

    def test_training_mode_switch(self, agent):
        """Test switching between training and eval mode"""
        agent.train()
        assert agent.policy_net.training

        agent.eval()
        assert not agent.policy_net.training

    def test_device_placement(self, agent):
        """Test model is placed on correct device"""
        # Should work on CPU at minimum
        device = next(agent.policy_net.parameters()).device
        assert device.type in ['cpu', 'cuda']


class TestDQNTrainingStability:
    """Test DQN training stability"""

    def test_q_values_dont_explode(self):
        """Test Q-values remain bounded during training"""
        from rl_power.dqn_agent import DQNAgent

        config = {
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.995,
            'target_update_freq': 100,
            'buffer_capacity': 10000
        }
        agent = DQNAgent(config)

        # Simulate training
        for episode in range(50):
            for step in range(100):
                state = np.random.randn(5)
                action = agent.select_action(state)
                reward = np.random.randn()
                next_state = np.random.randn(5)
                done = step == 99

                agent.store_transition(state, action, reward, next_state, done)

                if len(agent.replay_buffer) > 64:
                    agent.update(batch_size=64)

            # Check Q-values are bounded
            test_state = np.random.randn(5)
            q_values = agent.get_q_values(test_state)

            assert all(np.isfinite(q_values))
            assert all(abs(q) < 1000 for q in q_values)  # Reasonable bound

    def test_loss_convergence(self):
        """Test loss decreases over training"""
        from rl_power.dqn_agent import DQNAgent

        config = {
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 1.0,
            'epsilon_end': 0.1,
            'epsilon_decay': 0.995,
            'target_update_freq': 100,
            'buffer_capacity': 10000
        }
        agent = DQNAgent(config)

        # Fill buffer with consistent experiences
        for _ in range(500):
            state = np.random.randn(5)
            action = 2  # Fixed action
            reward = -1.0  # Fixed reward
            next_state = state + np.random.randn(5) * 0.1
            done = False

            agent.store_transition(state, action, reward, next_state, done)

        # Train and track loss
        losses = []
        for _ in range(100):
            loss = agent.update(batch_size=64)
            if loss is not None:
                losses.append(loss)

        # Loss should generally decrease (or at least not increase)
        if len(losses) > 10:
            early_loss = np.mean(losses[:10])
            late_loss = np.mean(losses[-10:])

            # Late loss should be <= early loss (with some tolerance)
            assert late_loss <= early_loss * 1.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
