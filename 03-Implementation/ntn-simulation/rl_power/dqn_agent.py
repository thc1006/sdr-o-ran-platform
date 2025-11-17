#!/usr/bin/env python3
"""
Deep Q-Network (DQN) Agent for NTN Power Control
=================================================

Implementation of DQN with:
- Experience replay buffer
- Target network
- Epsilon-greedy exploration
- Huber loss
- Adam optimizer

Author: RL Specialist
Date: 2025-11-17
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path


class DQNNetwork(nn.Module):
    """
    Deep Q-Network neural network

    Architecture: 3 hidden layers [128, 128, 64] with ReLU activation
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: List[int] = [128, 128, 64]
    ):
        """
        Initialize DQN network

        Args:
            state_dim: Dimension of state space
            action_dim: Dimension of action space
            hidden_dims: List of hidden layer dimensions
        """
        super(DQNNetwork, self).__init__()

        # Build network layers
        layers = []
        input_dim = state_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ReLU())
            input_dim = hidden_dim

        # Output layer
        layers.append(nn.Linear(input_dim, action_dim))

        self.network = nn.Sequential(*layers)

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, module):
        """Initialize network weights"""
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.constant_(module.bias, 0.0)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            state: Input state tensor

        Returns:
            Q-values for each action
        """
        return self.network(state)


class ReplayBuffer:
    """
    Experience replay buffer for DQN

    Stores transitions (state, action, reward, next_state, done)
    and samples random mini-batches for training.
    """

    def __init__(self, capacity: int = 10000):
        """
        Initialize replay buffer

        Args:
            capacity: Maximum number of transitions to store
        """
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Add transition to buffer"""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> Tuple[np.ndarray, ...]:
        """
        Sample random batch

        Args:
            batch_size: Number of transitions to sample

        Returns:
            Batch of (states, actions, rewards, next_states, dones)
        """
        if len(self.buffer) < batch_size:
            raise ValueError(f"Buffer has only {len(self.buffer)} samples, need {batch_size}")

        batch = random.sample(self.buffer, batch_size)

        states, actions, rewards, next_states, dones = zip(*batch)

        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32)
        )

    def __len__(self) -> int:
        """Return current buffer size"""
        return len(self.buffer)

    def clear(self):
        """Clear buffer"""
        self.buffer.clear()


class DQNAgent:
    """
    DQN Agent for NTN Power Control

    Implements Deep Q-Learning with experience replay and target network.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DQN agent

        Args:
            config: Configuration dictionary with hyperparameters
        """
        self.state_dim = config['state_dim']
        self.action_dim = config['action_dim']
        self.hidden_dims = config.get('hidden_dims', [128, 128, 64])
        self.lr = config.get('lr', 0.0001)
        self.gamma = config.get('gamma', 0.99)
        self.epsilon = config.get('epsilon_start', 1.0)
        self.epsilon_end = config.get('epsilon_end', 0.1)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.target_update_freq = config.get('target_update_freq', 100)
        self.buffer_capacity = config.get('buffer_capacity', 10000)

        # Device (CPU or GPU)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Create policy and target networks
        self.policy_net = DQNNetwork(
            self.state_dim,
            self.action_dim,
            self.hidden_dims
        ).to(self.device)

        self.target_net = DQNNetwork(
            self.state_dim,
            self.action_dim,
            self.hidden_dims
        ).to(self.device)

        # Initialize target network with policy network weights
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Target network is always in eval mode

        # Optimizer (Adam)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.lr)

        # Loss function (Huber loss for stability)
        self.criterion = nn.SmoothL1Loss()

        # Replay buffer
        self.replay_buffer = ReplayBuffer(capacity=self.buffer_capacity)

        # Training step counter
        self.training_step = 0

        print(f"[DQN Agent] Initialized on {self.device}")
        print(f"  State dim: {self.state_dim}, Action dim: {self.action_dim}")
        print(f"  Hidden dims: {self.hidden_dims}")
        print(f"  Learning rate: {self.lr}, Gamma: {self.gamma}")
        print(f"  Epsilon: {self.epsilon} -> {self.epsilon_end} (decay: {self.epsilon_decay})")

    def select_action(self, state: np.ndarray, explore: bool = True) -> int:
        """
        Select action using epsilon-greedy policy

        Args:
            state: Current state
            explore: Whether to use epsilon-greedy exploration

        Returns:
            Selected action index
        """
        if explore and random.random() < self.epsilon:
            # Explore: random action
            return random.randint(0, self.action_dim - 1)
        else:
            # Exploit: best action according to Q-network
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax(dim=1).item()

    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store transition in replay buffer"""
        self.replay_buffer.push(state, action, reward, next_state, done)

    def update(self, batch_size: int = 64) -> Optional[float]:
        """
        Update Q-network using mini-batch from replay buffer

        Args:
            batch_size: Mini-batch size

        Returns:
            Loss value if update performed, None otherwise
        """
        if len(self.replay_buffer) < batch_size:
            return None

        # Sample mini-batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(batch_size)

        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        # Compute current Q-values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Compute target Q-values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(dim=1)[0]
            target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

        # Compute loss
        loss = self.criterion(current_q_values, target_q_values)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()

        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=10.0)

        self.optimizer.step()

        self.training_step += 1

        return loss.item()

    def update_target_network(self):
        """Update target network with policy network weights"""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        """Decay epsilon for exploration"""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        """
        Get Q-values for a state

        Args:
            state: Input state

        Returns:
            Q-values for all actions
        """
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.cpu().numpy()[0]

    def save(self, path: Path):
        """
        Save model checkpoint

        Args:
            path: Path to save checkpoint
        """
        checkpoint = {
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step,
            'config': {
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'hidden_dims': self.hidden_dims,
                'lr': self.lr,
                'gamma': self.gamma,
                'epsilon_end': self.epsilon_end,
                'epsilon_decay': self.epsilon_decay
            }
        }

        torch.save(checkpoint, path)
        print(f"[DQN Agent] Model saved to {path}")

    def load(self, path: Path):
        """
        Load model checkpoint

        Args:
            path: Path to load checkpoint from
        """
        checkpoint = torch.load(path, map_location=self.device)

        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.training_step = checkpoint['training_step']

        print(f"[DQN Agent] Model loaded from {path}")
        print(f"  Training step: {self.training_step}, Epsilon: {self.epsilon:.4f}")

    def train(self):
        """Set network to training mode"""
        self.policy_net.train()

    def eval(self):
        """Set network to evaluation mode"""
        self.policy_net.eval()


# Test function
def test_dqn_agent():
    """Test DQN agent basic functionality"""
    print("Testing DQN Agent")
    print("=" * 50)

    config = {
        'state_dim': 5,
        'action_dim': 5,
        'hidden_dims': [128, 128, 64],
        'lr': 0.001,
        'gamma': 0.99,
        'epsilon_start': 1.0,
        'epsilon_end': 0.1,
        'epsilon_decay': 0.995,
        'target_update_freq': 10,
        'buffer_capacity': 1000
    }

    agent = DQNAgent(config)

    # Test action selection
    state = np.random.randn(5)
    action = agent.select_action(state)
    print(f"\nSelected action: {action}")

    # Test Q-values
    q_values = agent.get_q_values(state)
    print(f"Q-values: {q_values}")

    # Add some experiences
    print("\nAdding experiences to replay buffer...")
    for _ in range(100):
        state = np.random.randn(5)
        action = random.randint(0, 4)
        reward = np.random.randn()
        next_state = np.random.randn(5)
        done = False

        agent.store_transition(state, action, reward, next_state, done)

    print(f"Buffer size: {len(agent.replay_buffer)}")

    # Test update
    print("\nTraining...")
    for _ in range(10):
        loss = agent.update(batch_size=32)
        if loss is not None:
            print(f"  Loss: {loss:.4f}")

    # Test epsilon decay
    initial_epsilon = agent.epsilon
    agent.decay_epsilon()
    print(f"\nEpsilon: {initial_epsilon:.4f} -> {agent.epsilon:.4f}")

    print("\nDQN Agent test completed!")


if __name__ == '__main__':
    test_dqn_agent()
