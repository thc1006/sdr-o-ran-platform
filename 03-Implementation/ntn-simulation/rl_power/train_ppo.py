#!/usr/bin/env python3
"""
PPO Training Script for NTN Power Control
==========================================

Trains a PPO (Actor-Critic) agent on NTNPowerEnvironment and evaluates
against the rule-based baseline.  Results saved to ./rl_power_models_ppo/
for direct comparison with DQN v1.

Usage:
    python train_ppo.py --episodes 500

Author: thc1006
Date: 2026-04-05
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from ntn_env import NTNPowerEnvironment
from ppo_agent import PPOAgent
from evaluator import Evaluator, RuleBasedBaseline


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description='PPO Training for NTN Power Control')

    p.add_argument('--episodes',       type=int,   default=500)
    p.add_argument('--episode-length', type=int,   default=300)
    p.add_argument('--lr',             type=float, default=3e-4)
    p.add_argument('--gamma',          type=float, default=0.99)
    p.add_argument('--gae-lambda',     type=float, default=0.95)
    p.add_argument('--clip-epsilon',   type=float, default=0.2)
    p.add_argument('--n-steps',        type=int,   default=300,
                   help='Rollout length (default=episode_length=300)')
    p.add_argument('--n-epochs',       type=int,   default=10,
                   help='PPO update epochs per rollout')
    p.add_argument('--batch-size',     type=int,   default=64)
    p.add_argument('--ent-coef',       type=float, default=0.01)
    p.add_argument('--vf-coef',        type=float, default=0.5)
    p.add_argument('--eval-episodes',  type=int,   default=100)
    p.add_argument('--eval-frequency', type=int,   default=50)
    p.add_argument('--save-dir',       type=str,   default='./rl_power_models_ppo')
    p.add_argument('--target-rsrp',    type=float, default=-85.0)
    p.add_argument('--rsrp-threshold', type=float, default=-90.0)
    p.add_argument('--seed',           type=int,   default=42)
    return p.parse_args()


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train(args):
    np.random.seed(args.seed)

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # --- Environment --------------------------------------------------------
    env = NTNPowerEnvironment(config={
        'episode_length': args.episode_length,
        'target_rsrp_dbm': args.target_rsrp,
        'rsrp_threshold_dbm': args.rsrp_threshold,
        'power_penalty_weight': 0.01,
    })
    obs_dim = env.observation_space.shape[0]
    act_dim = env.action_space.n

    print(f"Environment: {obs_dim}-D obs, {act_dim} actions, "
          f"episode_length={args.episode_length}")

    # --- Agent --------------------------------------------------------------
    agent = PPOAgent({
        'state_dim':    obs_dim,
        'action_dim':   act_dim,
        'hidden_dims':  [128, 128, 64],
        'lr':           args.lr,
        'gamma':        args.gamma,
        'gae_lambda':   args.gae_lambda,
        'clip_epsilon': args.clip_epsilon,
        'n_steps':      args.n_steps,
        'n_epochs':     args.n_epochs,
        'batch_size':   args.batch_size,
        'ent_coef':     args.ent_coef,
        'vf_coef':      args.vf_coef,
    })

    # --- Tracking -----------------------------------------------------------
    episode_rewards = []
    recent_rewards  = []     # sliding window for display
    best_mean_reward = -np.inf

    print("\n" + "="*70)
    print("PPO Training Started")
    print("="*70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    global_step = 0
    obs, _ = env.reset(seed=args.seed)
    episode_reward = 0.0
    episode_count  = 0

    while episode_count < args.episodes:
        # --- Collect one rollout (args.n_steps steps) ---------------------
        agent.train()
        for _ in range(args.n_steps):
            action, log_prob, value = agent.select_action_with_info(obs)
            next_obs, reward, terminated, truncated, _ = env.step(action)

            done = terminated or truncated
            agent.store_transition(obs, action, reward, value, log_prob, float(done))
            obs = next_obs
            episode_reward += reward
            global_step += 1

            if done:
                episode_rewards.append(episode_reward)
                recent_rewards.append(episode_reward)
                if len(recent_rewards) > 20:
                    recent_rewards.pop(0)
                episode_count += 1
                episode_reward = 0.0
                obs, _ = env.reset()

                # Progress printout
                if episode_count % 50 == 0 or episode_count == 1:
                    mean_r = np.mean(recent_rewards) if recent_rewards else 0.0
                    print(f"  Ep {episode_count:4d}/{args.episodes}  "
                          f"reward(last20)={mean_r:7.2f}  "
                          f"steps={global_step}")

                # Periodic eval
                if episode_count % args.eval_frequency == 0:
                    agent.eval()
                    evaluator = Evaluator(env, agent)
                    quick = evaluator.evaluate(num_episodes=10)
                    agent.train()
                    obs, _ = env.reset(seed=args.seed + episode_count)
                    episode_reward = 0.0
                    print(f"  [Eval @ ep {episode_count}]  "
                          f"mean_reward={quick['mean_reward']:.2f}  "
                          f"violation={quick['rsrp_violation_rate']*100:.1f}%  "
                          f"power={quick['mean_power_dbm']:.1f} dBm")

                if episode_count >= args.episodes:
                    break

        # --- PPO update on collected rollout --------------------------------
        loss_info = agent.update(last_state=obs)

        # Save best model
        cur_mean = np.mean(recent_rewards) if recent_rewards else -np.inf
        if cur_mean > best_mean_reward and len(recent_rewards) >= 5:
            best_mean_reward = cur_mean
            agent.save(save_dir / 'best_model.pt')

    # Save final model
    agent.save(save_dir / 'final_model.pt')

    # Save training rewards
    with open(save_dir / 'training_rewards.json', 'w') as f:
        json.dump({'episode_rewards': episode_rewards}, f, indent=2)

    print(f"\nTraining complete.  Total steps: {global_step}  "
          f"Best mean reward: {best_mean_reward:.2f}")
    return agent, episode_rewards


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    print("\n" + "="*70)
    print("PPO Power Control — NTN Environment")
    print("="*70)
    for k, v in vars(args).items():
        print(f"  {k}: {v}")
    print("="*70 + "\n")

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    with open(save_dir / 'config.json', 'w') as f:
        json.dump(vars(args), f, indent=2)

    agent, train_rewards = train(args)

    # --- Final evaluation vs baseline ----------------------------------------
    print("\n" + "="*70)
    print("Final Evaluation vs Rule-Based Baseline")
    print("="*70)

    env = NTNPowerEnvironment(config={
        'episode_length': args.episode_length,
        'target_rsrp_dbm': args.target_rsrp,
        'rsrp_threshold_dbm': args.rsrp_threshold,
        'power_penalty_weight': 0.01,
    })

    agent.eval()
    evaluator = Evaluator(env, agent)
    baseline  = RuleBasedBaseline(target_rsrp=args.target_rsrp)
    comparison = evaluator.compare_with_baseline(baseline, num_episodes=args.eval_episodes)

    comparison_path = save_dir / 'evaluation_comparison.json'
    with open(comparison_path, 'w') as f:
        json.dump(comparison, f, indent=2,
                  default=lambda x: float(x) if hasattr(x, 'dtype') else x)
    print(f"\nComparison saved to {comparison_path}")

    # --- Summary -------------------------------------------------------------
    print("\n" + "="*70)
    print("PPO Results Summary")
    print("="*70)
    rl = comparison['rl_results']
    bl = comparison['baseline_results']
    print(f"  PPO mean reward       : {rl['mean_reward']:.2f} ± {rl['std_reward']:.2f}")
    print(f"  PPO mean power        : {rl['mean_power_dbm']:.2f} dBm")
    print(f"  PPO mean RSRP         : {rl['mean_rsrp_dbm']:.2f} dBm")
    print(f"  PPO violation rate    : {rl['rsrp_violation_rate']*100:.2f}%")
    print()
    print(f"  Baseline mean power   : {bl['mean_power_dbm']:.2f} dBm")
    print(f"  Baseline mean RSRP    : {bl['mean_rsrp_dbm']:.2f} dBm")
    print(f"  Baseline violation    : {bl['rsrp_violation_rate']*100:.2f}%")
    print()
    print(f"  p-value               : {comparison['statistical_test']['p_value']:.3e}")
    print(f"  Significant           : {comparison['statistical_test']['significant']}")
    print("="*70)

    # Compare against DQN v1 if available
    dqn_path = Path('./models/run_corrected_v1/evaluation_comparison.json')
    if dqn_path.exists():
        with open(dqn_path) as f:
            dqn_cmp = json.load(f)
        dqn_rl = dqn_cmp['rl_results']
        print("\nDQN v1 vs PPO comparison:")
        print(f"  DQN  violation rate : {dqn_rl['rsrp_violation_rate']*100:.2f}%")
        print(f"  PPO  violation rate : {rl['rsrp_violation_rate']*100:.2f}%")
        print(f"  DQN  mean power     : {dqn_rl['mean_power_dbm']:.2f} dBm")
        print(f"  PPO  mean power     : {rl['mean_power_dbm']:.2f} dBm")
        print(f"  DQN  mean reward    : {dqn_rl['mean_reward']:.2f}")
        print(f"  PPO  mean reward    : {rl['mean_reward']:.2f}")

    print(f"\nAll results saved to: {save_dir}")


if __name__ == '__main__':
    main()
