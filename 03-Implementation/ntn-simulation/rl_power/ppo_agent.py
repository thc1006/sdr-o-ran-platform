#!/usr/bin/env python3
"""
Proximal Policy Optimization (PPO) Agent for NTN Power Control
===============================================================

Actor-Critic PPO with:
- Shared base network + separate actor/critic heads
- Generalized Advantage Estimation (GAE, lambda=0.95)
- Clipped surrogate objective (epsilon=0.2)
- Entropy bonus for exploration
- Gradient norm clipping
- Discrete action space (5 actions: -3,-1,0,+1,+3 dBm)

Reference: Schulman et al., "Proximal Policy Optimization Algorithms", 2017.

Author: thc1006
Date: 2026-04-05
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path


class ActorCriticNetwork(nn.Module):
    """
    Shared-trunk Actor-Critic network for discrete action spaces.

    Architecture:
        Input  -> [128] -> [128] -> [64]  (shared trunk)
                                      |-> actor  [64 -> action_dim]  (softmax)
                                      |-> critic [64 -> 1]           (linear)
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [128, 128, 64]):
        super(ActorCriticNetwork, self).__init__()

        # Shared trunk
        trunk_layers = []
        in_dim = state_dim
        for h in hidden_dims:
            trunk_layers.append(nn.Linear(in_dim, h))
            trunk_layers.append(nn.Tanh())   # Tanh recommended for PPO
            in_dim = h
        self.trunk = nn.Sequential(*trunk_layers)

        # Actor head: policy logits
        self.actor_head = nn.Linear(in_dim, action_dim)

        # Critic head: state value V(s)
        self.critic_head = nn.Linear(in_dim, 1)

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
            nn.init.constant_(module.bias, 0.0)
        # Use smaller gain for output heads
        nn.init.orthogonal_(self.actor_head.weight, gain=0.01)
        nn.init.orthogonal_(self.critic_head.weight, gain=1.0)

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns (logits, value) for the given state.
        """
        features = self.trunk(state)
        logits = self.actor_head(features)
        value = self.critic_head(features).squeeze(-1)
        return logits, value

    def get_action_and_value(self, state: torch.Tensor, action: Optional[torch.Tensor] = None):
        """
        Sample (or evaluate) an action and compute log_prob + entropy.

        Returns: (action, log_prob, entropy, value)
        """
        logits, value = self.forward(state)
        dist = Categorical(logits=logits)
        if action is None:
            action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        return action, log_prob, entropy, value


class RolloutBuffer:
    """
    On-policy rollout buffer. Collects fixed-length trajectories,
    then computes GAE advantages and returns for PPO update.
    """

    def __init__(self, n_steps: int, state_dim: int, gamma: float = 0.99, gae_lambda: float = 0.95):
        self.n_steps = n_steps
        self.state_dim = state_dim
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.reset()

    def reset(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []
        self.pos = 0

    def add(self, state, action, reward, value, log_prob, done):
        self.states.append(state.copy())
        self.actions.append(int(action))
        self.rewards.append(float(reward))
        self.values.append(float(value))
        self.log_probs.append(float(log_prob))
        self.dones.append(float(done))
        self.pos += 1

    def compute_advantages(self, last_value: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        GAE-lambda advantage estimation.
        Returns (advantages, returns) both shape (n_steps,).
        """
        rewards = np.array(self.rewards, dtype=np.float32)
        values = np.array(self.values, dtype=np.float32)
        dones = np.array(self.dones, dtype=np.float32)

        advantages = np.zeros(self.pos, dtype=np.float32)
        last_gae = 0.0
        for t in reversed(range(self.pos)):
            next_val = last_value if t == self.pos - 1 else values[t + 1]
            next_done = 0.0 if t == self.pos - 1 else dones[t + 1]
            delta = rewards[t] + self.gamma * next_val * (1.0 - next_done) - values[t]
            last_gae = delta + self.gamma * self.gae_lambda * (1.0 - dones[t]) * last_gae
            advantages[t] = last_gae

        returns = advantages + values[:self.pos]
        return advantages, returns

    def get_tensors(self, last_value: float, device: torch.device):
        """
        Compute advantages/returns, normalise advantages, return tensors.
        """
        advantages, returns = self.compute_advantages(last_value)

        # Normalise advantages (zero mean, unit std) for stable gradients
        adv_mean, adv_std = advantages.mean(), advantages.std() + 1e-8
        advantages = (advantages - adv_mean) / adv_std

        states_t   = torch.FloatTensor(np.array(self.states[:self.pos])).to(device)
        actions_t  = torch.LongTensor(np.array(self.actions[:self.pos])).to(device)
        log_probs_t = torch.FloatTensor(np.array(self.log_probs[:self.pos])).to(device)
        advantages_t = torch.FloatTensor(advantages).to(device)
        returns_t   = torch.FloatTensor(returns).to(device)

        return states_t, actions_t, log_probs_t, advantages_t, returns_t

    def is_full(self) -> bool:
        return self.pos >= self.n_steps


class PPOAgent:
    """
    PPO Agent for NTN Power Control (discrete actions).
    """

    def __init__(self, config: Dict[str, Any]):
        self.state_dim   = config['state_dim']
        self.action_dim  = config['action_dim']
        self.hidden_dims = config.get('hidden_dims', [128, 128, 64])

        # PPO hyperparameters
        self.lr           = config.get('lr', 3e-4)
        self.gamma        = config.get('gamma', 0.99)
        self.gae_lambda   = config.get('gae_lambda', 0.95)
        self.clip_epsilon = config.get('clip_epsilon', 0.2)
        self.n_steps      = config.get('n_steps', 512)
        self.n_epochs     = config.get('n_epochs', 10)
        self.batch_size   = config.get('batch_size', 64)
        self.ent_coef     = config.get('ent_coef', 0.01)
        self.vf_coef      = config.get('vf_coef', 0.5)
        self.max_grad_norm = config.get('max_grad_norm', 0.5)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.network = ActorCriticNetwork(
            self.state_dim, self.action_dim, self.hidden_dims
        ).to(self.device)

        self.optimizer = optim.Adam(self.network.parameters(), lr=self.lr, eps=1e-5)

        self.buffer = RolloutBuffer(
            n_steps=self.n_steps,
            state_dim=self.state_dim,
            gamma=self.gamma,
            gae_lambda=self.gae_lambda,
        )

        self.training_step = 0
        self._in_train_mode = True

        print(f"[PPO Agent] Initialized on {self.device}")
        print(f"  State dim: {self.state_dim}, Action dim: {self.action_dim}")
        print(f"  n_steps={self.n_steps}, n_epochs={self.n_epochs}, batch={self.batch_size}")
        print(f"  lr={self.lr}, gamma={self.gamma}, lambda={self.gae_lambda}")
        print(f"  clip_eps={self.clip_epsilon}, ent_coef={self.ent_coef}")

    # ------------------------------------------------------------------
    # Action selection
    # ------------------------------------------------------------------

    @torch.no_grad()
    def select_action(self, state: np.ndarray, explore: bool = True) -> int:
        """
        Evaluator-compatible interface: returns a plain int action.
        explore=True  → sample from policy distribution
        explore=False → greedy argmax
        """
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        if explore:
            action_t, _, _, _ = self.network.get_action_and_value(state_t)
        else:
            logits, _ = self.network(state_t)
            action_t = logits.argmax(dim=-1)
        return int(action_t.item())

    @torch.no_grad()
    def select_action_with_info(self, state: np.ndarray) -> Tuple[int, float, float]:
        """
        Training interface: returns (action, log_prob, value) for rollout buffer.
        """
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        action_t, log_prob_t, _, value_t = self.network.get_action_and_value(state_t)
        return int(action_t.item()), float(log_prob_t.item()), float(value_t.item())

    # ------------------------------------------------------------------
    # Buffer management
    # ------------------------------------------------------------------

    def store_transition(self, state, action, reward, value, log_prob, done):
        self.buffer.add(state, action, reward, value, log_prob, done)

    def buffer_is_full(self) -> bool:
        return self.buffer.is_full()

    # ------------------------------------------------------------------
    # PPO update
    # ------------------------------------------------------------------

    @torch.no_grad()
    def _get_last_value(self, state: np.ndarray) -> float:
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        _, value = self.network(state_t)
        return float(value.item())

    def update(self, last_state: np.ndarray) -> Dict[str, float]:
        """
        Run K epochs of PPO update on the collected rollout.
        Clears the buffer at the end.

        Returns loss info dict.
        """
        last_value = self._get_last_value(last_state)
        states, actions, old_log_probs, advantages, returns = \
            self.buffer.get_tensors(last_value, self.device)

        n = states.shape[0]
        total_pg_loss = 0.0
        total_vf_loss = 0.0
        total_entropy = 0.0
        n_updates = 0

        for _ in range(self.n_epochs):
            # Shuffle indices for mini-batch sampling
            indices = torch.randperm(n)

            for start in range(0, n, self.batch_size):
                idx = indices[start:start + self.batch_size]

                mb_states   = states[idx]
                mb_actions  = actions[idx]
                mb_old_lp   = old_log_probs[idx]
                mb_adv      = advantages[idx]
                mb_returns  = returns[idx]

                # Forward pass
                _, new_log_probs, entropy, new_values = \
                    self.network.get_action_and_value(mb_states, mb_actions)

                # Ratio for clipping
                log_ratio = new_log_probs - mb_old_lp
                ratio = log_ratio.exp()

                # PPO clipped surrogate loss
                pg_loss1 = -mb_adv * ratio
                pg_loss2 = -mb_adv * torch.clamp(ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon)
                pg_loss  = torch.max(pg_loss1, pg_loss2).mean()

                # Value loss (clipped)
                vf_loss = 0.5 * ((new_values - mb_returns) ** 2).mean()

                # Entropy bonus (negative because we minimise)
                entropy_loss = -entropy.mean()

                loss = pg_loss + self.vf_coef * vf_loss + self.ent_coef * entropy_loss

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.network.parameters(), self.max_grad_norm)
                self.optimizer.step()

                total_pg_loss += pg_loss.item()
                total_vf_loss += vf_loss.item()
                total_entropy += (-entropy_loss.item())
                n_updates += 1

        self.training_step += 1
        self.buffer.reset()

        return {
            'pg_loss': total_pg_loss / max(n_updates, 1),
            'vf_loss': total_vf_loss / max(n_updates, 1),
            'entropy': total_entropy / max(n_updates, 1),
        }

    # ------------------------------------------------------------------
    # Checkpoint I/O
    # ------------------------------------------------------------------

    def save(self, path: Path):
        checkpoint = {
            'network_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'training_step': self.training_step,
            'config': {
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'hidden_dims': self.hidden_dims,
                'lr': self.lr,
                'gamma': self.gamma,
                'gae_lambda': self.gae_lambda,
                'clip_epsilon': self.clip_epsilon,
                'n_steps': self.n_steps,
                'n_epochs': self.n_epochs,
                'batch_size': self.batch_size,
            }
        }
        torch.save(checkpoint, path)
        print(f"[PPO Agent] Model saved to {path}")

    def load(self, path: Path):
        checkpoint = torch.load(path, map_location=self.device)
        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_step = checkpoint['training_step']
        print(f"[PPO Agent] Model loaded from {path}")

    # Compatibility shims so Evaluator can use PPOAgent like DQNAgent
    def train(self):
        self.network.train()
        self._in_train_mode = True

    def eval(self):
        self.network.eval()
        self._in_train_mode = False

    @property
    def epsilon(self):
        return 0.0  # PPO has no epsilon; greedy when evaluate

    @epsilon.setter
    def epsilon(self, value):
        pass  # ignored
