#!/usr/bin/env python3
"""
Main Training Script for RL Power Control
==========================================

Trains DQN agent for NTN power control with full pipeline:
- Environment setup
- Agent creation
- Training loop
- Evaluation vs baseline
- Model saving
- Results visualization

Usage:
    python train_rl_power.py --episodes 500 --batch-size 64

Author: RL Specialist
Date: 2025-11-17
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ntn_env import NTNPowerEnvironment
from dqn_agent import DQNAgent
from trainer import Trainer
from evaluator import Evaluator, RuleBasedBaseline


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Train RL Power Control Agent')

    # Training parameters
    parser.add_argument('--episodes', type=int, default=500,
                       help='Number of training episodes (default: 500)')
    parser.add_argument('--batch-size', type=int, default=64,
                       help='Batch size for training (default: 64)')
    parser.add_argument('--lr', type=float, default=0.0001,
                       help='Learning rate (default: 0.0001)')
    parser.add_argument('--gamma', type=float, default=0.99,
                       help='Discount factor (default: 0.99)')
    parser.add_argument('--epsilon-start', type=float, default=1.0,
                       help='Initial epsilon (default: 1.0)')
    parser.add_argument('--epsilon-end', type=float, default=0.1,
                       help='Final epsilon (default: 0.1)')
    parser.add_argument('--epsilon-decay', type=float, default=0.995,
                       help='Epsilon decay rate (default: 0.995)')

    # Environment parameters
    parser.add_argument('--episode-length', type=int, default=300,
                       help='Episode length in steps (default: 300)')
    parser.add_argument('--target-rsrp', type=float, default=-85.0,
                       help='Target RSRP in dBm (default: -85.0)')
    parser.add_argument('--rsrp-threshold', type=float, default=-90.0,
                       help='RSRP threshold in dBm (default: -90.0)')

    # Evaluation
    parser.add_argument('--eval-episodes', type=int, default=100,
                       help='Number of evaluation episodes (default: 100)')
    parser.add_argument('--eval-frequency', type=int, default=50,
                       help='Evaluate every N episodes (default: 50)')

    # Checkpointing
    parser.add_argument('--checkpoint-freq', type=int, default=100,
                       help='Save checkpoint every N episodes (default: 100)')
    parser.add_argument('--save-dir', type=str, default='./rl_power_models',
                       help='Directory to save models (default: ./rl_power_models)')

    # Misc
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')
    parser.add_argument('--verbose', action='store_true', default=True,
                       help='Verbose output')

    return parser.parse_args()


def main():
    """Main training pipeline"""
    # Parse arguments
    args = parse_args()

    print("\n" + "="*80)
    print("RL-based Power Control for NTN - Training Pipeline")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nConfiguration:")
    for arg, value in vars(args).items():
        print(f"  {arg}: {value}")
    print("="*80 + "\n")

    # Create save directory
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Save configuration
    config_path = save_dir / 'training_config.json'
    with open(config_path, 'w') as f:
        json.dump(vars(args), f, indent=2)
    print(f"Configuration saved to {config_path}\n")

    # Create environment
    print("Creating environment...")
    env_config = {
        'episode_length': args.episode_length,
        'target_rsrp_dbm': args.target_rsrp,
        'rsrp_threshold_dbm': args.rsrp_threshold,
        # Use environment defaults for realistic LEO satellite power (46 dBm)
        # and antenna gains (45 dB combined). No overrides needed.
        'power_penalty_weight': 0.01,
        'rsrp_violation_penalty': 100.0
    }
    env = NTNPowerEnvironment(config=env_config)
    print(f"Environment created: {env.observation_space.shape[0]}-D state, "
          f"{env.action_space.n} actions\n")

    # Create agent
    print("Creating DQN agent...")
    agent_config = {
        'state_dim': env.observation_space.shape[0],
        'action_dim': env.action_space.n,
        'hidden_dims': [128, 128, 64],
        'lr': args.lr,
        'gamma': args.gamma,
        'epsilon_start': args.epsilon_start,
        'epsilon_end': args.epsilon_end,
        'epsilon_decay': args.epsilon_decay,
        'target_update_freq': 100,
        'buffer_capacity': 10000
    }
    agent = DQNAgent(agent_config)
    print()

    # Create trainer
    print("Creating trainer...")
    trainer_config = {
        'num_episodes': args.episodes,
        'batch_size': args.batch_size,
        'eval_frequency': args.eval_frequency,
        'num_eval_episodes': 10,
        'checkpoint_frequency': args.checkpoint_freq,
        'save_dir': str(save_dir),
        'verbose': args.verbose,
        'early_stopping': False
    }
    trainer = Trainer(env, agent, trainer_config)
    print()

    # Train agent
    print("Starting training...")
    print("="*80)
    history = trainer.train()

    # Training complete
    print("\n" + "="*80)
    print("Training Summary")
    print("="*80)
    metrics = trainer.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    print("="*80 + "\n")

    # Evaluation
    print("\n" + "="*80)
    print("Final Evaluation vs Baseline")
    print("="*80 + "\n")

    # Create evaluator
    evaluator = Evaluator(env, agent)

    # Compare with baseline
    baseline = RuleBasedBaseline(target_rsrp=args.target_rsrp)
    comparison = evaluator.compare_with_baseline(baseline, num_episodes=args.eval_episodes)

    # Save comparison results
    comparison_path = save_dir / 'evaluation_comparison.json'
    with open(comparison_path, 'w') as f:
        json.dump(comparison, f, indent=2, default=lambda x: float(x) if hasattr(x, 'dtype') else x)
    print(f"\nComparison results saved to {comparison_path}")

    # Generate plots
    print("\nGenerating evaluation plots...")
    evaluator.plot_results(num_episodes=args.eval_episodes, save_dir=save_dir)

    # Final summary
    print("\n" + "="*80)
    print("Training Complete!")
    print("="*80)
    print(f"\nKey Results:")
    print(f"  Power Savings: {comparison['power_savings_percent']:.2f}%")
    print(f"  RL RSRP Violation Rate: {comparison['rl_results']['rsrp_violation_rate']*100:.2f}%")
    print(f"  Baseline RSRP Violation Rate: {comparison['baseline_results']['rsrp_violation_rate']*100:.2f}%")
    print(f"  Statistical Significance (p-value): {comparison['statistical_test']['p_value']:.6f}")

    if comparison['power_savings_percent'] > 0 and comparison['statistical_test']['significant']:
        print(f"\n  SUCCESS: RL policy achieves {comparison['power_savings_percent']:.2f}% power savings")
        print(f"           with statistical significance (p < 0.05)")
    elif comparison['power_savings_percent'] > 0:
        print(f"\n  PARTIAL SUCCESS: RL policy achieves {comparison['power_savings_percent']:.2f}% power savings")
        print(f"                   but not statistically significant (p = {comparison['statistical_test']['p_value']:.3f})")
    else:
        print(f"\n  NOTE: RL policy did not achieve power savings in this run")
        print(f"        Consider training longer or tuning hyperparameters")

    print(f"\nAll results saved to: {save_dir}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
