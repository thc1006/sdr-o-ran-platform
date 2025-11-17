#!/usr/bin/env python3
"""
Evaluation Module for RL Power Control
=======================================

Evaluates trained DQN policy and compares with baseline:
- Rule-based power control baseline
- Statistical significance testing
- Power savings calculation
- Link quality metrics
- Performance visualization

Author: RL Specialist
Date: 2025-11-17
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


class RuleBasedBaseline:
    """
    Rule-based Power Control Baseline

    Simple heuristic: adjust power to maintain RSRP near target.
    - If RSRP < target: increase power
    - If RSRP > target + margin: decrease power
    - Otherwise: maintain power
    """

    def __init__(self, target_rsrp: float = -85.0, tolerance: float = 3.0):
        """
        Initialize baseline

        Args:
            target_rsrp: Target RSRP to maintain (dBm)
            tolerance: RSRP tolerance (dB)
        """
        self.target_rsrp = target_rsrp
        self.tolerance = tolerance

    def select_action(self, state: np.ndarray) -> int:
        """
        Select action based on RSRP

        State: [elevation_angle, slant_range, rain_rate, current_rsrp, doppler_shift]

        Returns:
            Action index (0-4)
        """
        current_rsrp = state[3]

        rsrp_error = current_rsrp - self.target_rsrp

        # Simple proportional control
        if rsrp_error < -self.tolerance:
            # RSRP too low -> increase power significantly
            return 4  # +3 dB
        elif rsrp_error < -self.tolerance / 2:
            # RSRP slightly low -> increase power
            return 3  # +1 dB
        elif rsrp_error > self.tolerance:
            # RSRP too high -> decrease power significantly
            return 0  # -3 dB
        elif rsrp_error > self.tolerance / 2:
            # RSRP slightly high -> decrease power
            return 1  # -1 dB
        else:
            # RSRP acceptable -> maintain power
            return 2  # 0 dB


class Evaluator:
    """
    Evaluation module for RL power control

    Evaluates trained DQN agent and compares with baseline.
    """

    def __init__(self, env, agent):
        """
        Initialize evaluator

        Args:
            env: NTN power control environment
            agent: Trained DQN agent
        """
        self.env = env
        self.agent = agent

        # Set agent to evaluation mode
        self.agent.eval()
        self.agent.epsilon = 0.0  # No exploration during evaluation

    def evaluate_episode(self) -> Dict[str, Any]:
        """
        Evaluate single episode

        Returns:
            Episode metrics
        """
        obs, _ = self.env.reset()

        episode_reward = 0.0
        episode_length = 0
        total_power_consumption = 0.0
        rsrp_values = []
        power_values = []
        rsrp_violations = 0

        while True:
            action = self.agent.select_action(obs, explore=False)
            obs, reward, terminated, truncated, info = self.env.step(action)

            episode_reward += reward
            episode_length += 1
            total_power_consumption += info['power_consumption']
            rsrp_values.append(info['rsrp_dbm'])
            power_values.append(info['current_power_dbm'])

            if info['rsrp_dbm'] < self.env.rsrp_threshold_dbm:
                rsrp_violations += 1

            if terminated or truncated:
                break

        return {
            'episode_reward': episode_reward,
            'episode_length': episode_length,
            'total_power_consumption': total_power_consumption,
            'avg_power_dbm': np.mean(power_values),
            'avg_rsrp_dbm': np.mean(rsrp_values),
            'min_rsrp_dbm': np.min(rsrp_values),
            'max_rsrp_dbm': np.max(rsrp_values),
            'rsrp_violations': rsrp_violations,
            'rsrp_violation_rate': rsrp_violations / episode_length
        }

    def evaluate(self, num_episodes: int = 100) -> Dict[str, Any]:
        """
        Evaluate over multiple episodes

        Args:
            num_episodes: Number of episodes

        Returns:
            Aggregate metrics
        """
        print(f"\nEvaluating RL policy over {num_episodes} episodes...")

        all_metrics = []
        for ep in range(num_episodes):
            metrics = self.evaluate_episode()
            all_metrics.append(metrics)

            if (ep + 1) % 20 == 0:
                print(f"  Progress: {ep+1}/{num_episodes}")

        # Aggregate results
        results = {
            'num_episodes': num_episodes,
            'mean_reward': np.mean([m['episode_reward'] for m in all_metrics]),
            'std_reward': np.std([m['episode_reward'] for m in all_metrics]),
            'mean_power_consumption': np.mean([m['total_power_consumption'] for m in all_metrics]),
            'mean_power_dbm': np.mean([m['avg_power_dbm'] for m in all_metrics]),
            'mean_rsrp_dbm': np.mean([m['avg_rsrp_dbm'] for m in all_metrics]),
            'min_rsrp_dbm': np.min([m['min_rsrp_dbm'] for m in all_metrics]),
            'max_rsrp_dbm': np.max([m['max_rsrp_dbm'] for m in all_metrics]),
            'rsrp_violation_rate': np.mean([m['rsrp_violation_rate'] for m in all_metrics]),
            'all_episode_rewards': [m['episode_reward'] for m in all_metrics],
            'all_power_consumptions': [m['total_power_consumption'] for m in all_metrics]
        }

        print(f"\nRL Evaluation Results:")
        print(f"  Mean Reward: {results['mean_reward']:.2f} ± {results['std_reward']:.2f}")
        print(f"  Mean Power: {results['mean_power_dbm']:.2f} dBm")
        print(f"  Mean RSRP: {results['mean_rsrp_dbm']:.2f} dBm")
        print(f"  RSRP Violation Rate: {results['rsrp_violation_rate']*100:.2f}%")

        return results

    def evaluate_baseline(self, baseline: RuleBasedBaseline, num_episodes: int = 100) -> Dict[str, Any]:
        """
        Evaluate baseline policy

        Args:
            baseline: Baseline policy
            num_episodes: Number of episodes

        Returns:
            Aggregate metrics
        """
        print(f"\nEvaluating baseline policy over {num_episodes} episodes...")

        all_metrics = []
        for ep in range(num_episodes):
            obs, _ = self.env.reset()

            episode_reward = 0.0
            episode_length = 0
            total_power_consumption = 0.0
            rsrp_values = []
            power_values = []
            rsrp_violations = 0

            while True:
                action = baseline.select_action(obs)
                obs, reward, terminated, truncated, info = self.env.step(action)

                episode_reward += reward
                episode_length += 1
                total_power_consumption += info['power_consumption']
                rsrp_values.append(info['rsrp_dbm'])
                power_values.append(info['current_power_dbm'])

                if info['rsrp_dbm'] < self.env.rsrp_threshold_dbm:
                    rsrp_violations += 1

                if terminated or truncated:
                    break

            all_metrics.append({
                'episode_reward': episode_reward,
                'episode_length': episode_length,
                'total_power_consumption': total_power_consumption,
                'avg_power_dbm': np.mean(power_values),
                'avg_rsrp_dbm': np.mean(rsrp_values),
                'min_rsrp_dbm': np.min(rsrp_values),
                'rsrp_violations': rsrp_violations,
                'rsrp_violation_rate': rsrp_violations / episode_length
            })

            if (ep + 1) % 20 == 0:
                print(f"  Progress: {ep+1}/{num_episodes}")

        # Aggregate results
        results = {
            'num_episodes': num_episodes,
            'mean_reward': np.mean([m['episode_reward'] for m in all_metrics]),
            'std_reward': np.std([m['episode_reward'] for m in all_metrics]),
            'mean_power_consumption': np.mean([m['total_power_consumption'] for m in all_metrics]),
            'mean_power_dbm': np.mean([m['avg_power_dbm'] for m in all_metrics]),
            'mean_rsrp_dbm': np.mean([m['avg_rsrp_dbm'] for m in all_metrics]),
            'rsrp_violation_rate': np.mean([m['rsrp_violation_rate'] for m in all_metrics]),
            'all_episode_rewards': [m['episode_reward'] for m in all_metrics],
            'all_power_consumptions': [m['total_power_consumption'] for m in all_metrics]
        }

        print(f"\nBaseline Evaluation Results:")
        print(f"  Mean Reward: {results['mean_reward']:.2f} ± {results['std_reward']:.2f}")
        print(f"  Mean Power: {results['mean_power_dbm']:.2f} dBm")
        print(f"  Mean RSRP: {results['mean_rsrp_dbm']:.2f} dBm")
        print(f"  RSRP Violation Rate: {results['rsrp_violation_rate']*100:.2f}%")

        return results

    def compare_with_baseline(self, baseline: RuleBasedBaseline, num_episodes: int = 100) -> Dict[str, Any]:
        """
        Compare RL policy with baseline

        Args:
            baseline: Baseline policy
            num_episodes: Number of episodes

        Returns:
            Comparison results
        """
        print("\n" + "="*70)
        print("Comparing RL Policy with Baseline")
        print("="*70)

        # Evaluate both policies
        rl_results = self.evaluate(num_episodes)
        baseline_results = self.evaluate_baseline(baseline, num_episodes)

        # Calculate power savings
        power_savings_percent = compute_power_savings(
            baseline_results['mean_power_dbm'],
            rl_results['mean_power_dbm']
        )

        # Statistical significance test
        stat_test = perform_t_test(
            rl_results['all_power_consumptions'],
            baseline_results['all_power_consumptions']
        )

        comparison = {
            'rl_results': rl_results,
            'baseline_results': baseline_results,
            'power_savings_percent': power_savings_percent,
            'power_savings_mw': baseline_results['mean_power_consumption'] - rl_results['mean_power_consumption'],
            'rsrp_quality_comparison': {
                'rl_mean_rsrp': rl_results['mean_rsrp_dbm'],
                'baseline_mean_rsrp': baseline_results['mean_rsrp_dbm'],
                'rl_violation_rate': rl_results['rsrp_violation_rate'],
                'baseline_violation_rate': baseline_results['rsrp_violation_rate']
            },
            'statistical_test': stat_test
        }

        # Print comparison
        print("\n" + "="*70)
        print("Comparison Results")
        print("="*70)
        print(f"\nPower Consumption:")
        print(f"  RL Mean Power: {rl_results['mean_power_dbm']:.2f} dBm")
        print(f"  Baseline Mean Power: {baseline_results['mean_power_dbm']:.2f} dBm")
        print(f"  Power Savings: {power_savings_percent:.2f}%")

        print(f"\nLink Quality (RSRP):")
        print(f"  RL Mean RSRP: {rl_results['mean_rsrp_dbm']:.2f} dBm")
        print(f"  Baseline Mean RSRP: {baseline_results['mean_rsrp_dbm']:.2f} dBm")
        print(f"  RL Violation Rate: {rl_results['rsrp_violation_rate']*100:.2f}%")
        print(f"  Baseline Violation Rate: {baseline_results['rsrp_violation_rate']*100:.2f}%")

        print(f"\nStatistical Test (Power Consumption):")
        print(f"  t-statistic: {stat_test['t_statistic']:.4f}")
        print(f"  p-value: {stat_test['p_value']:.6f}")
        print(f"  Significant (p<0.05): {stat_test['significant']}")
        print("="*70 + "\n")

        return comparison

    def generate_report(self, num_episodes: int = 100, save_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate evaluation report

        Args:
            num_episodes: Number of evaluation episodes
            save_path: Path to save report

        Returns:
            Report dictionary
        """
        print("\nGenerating evaluation report...")

        # Evaluate RL policy
        rl_results = self.evaluate(num_episodes)

        # Create baseline and evaluate
        baseline = RuleBasedBaseline(target_rsrp=self.env.target_rsrp_dbm)
        baseline_results = self.evaluate_baseline(baseline, num_episodes)

        # Compare
        power_savings = compute_power_savings(
            baseline_results['mean_power_dbm'],
            rl_results['mean_power_dbm']
        )

        report = {
            'timestamp': str(np.datetime64('now')),
            'num_episodes': num_episodes,
            'evaluation_results': {
                'rl_policy': rl_results,
                'baseline_policy': baseline_results
            },
            'power_savings_percent': power_savings,
            'link_quality_maintained': rl_results['rsrp_violation_rate'] < 0.01
        }

        if save_path:
            with open(save_path, 'w') as f:
                # Convert numpy types for JSON
                json.dump(report, f, indent=2, default=lambda x: float(x) if isinstance(x, np.floating) else x)
            print(f"Report saved to {save_path}")

        return report

    def plot_results(self, num_episodes: int = 100, save_dir: Optional[Path] = None):
        """
        Plot evaluation results

        Args:
            num_episodes: Number of episodes
            save_dir: Directory to save plots
        """
        print("\nGenerating plots...")

        # Evaluate both policies
        rl_results = self.evaluate(num_episodes)
        baseline = RuleBasedBaseline(target_rsrp=self.env.target_rsrp_dbm)
        baseline_results = self.evaluate_baseline(baseline, num_episodes)

        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            # Plot 1: Power consumption comparison
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.boxplot([rl_results['all_power_consumptions'], baseline_results['all_power_consumptions']],
                      labels=['RL Policy', 'Baseline'])
            ax.set_ylabel('Power Consumption (mW)')
            ax.set_title('Power Consumption Comparison')
            ax.grid(True, alpha=0.3)
            plt.savefig(save_dir / 'power_comparison.png', dpi=150, bbox_inches='tight')
            plt.close()

            # Plot 2: Reward distribution
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist([rl_results['all_episode_rewards'], baseline_results['all_episode_rewards']],
                   label=['RL Policy', 'Baseline'], bins=30, alpha=0.7)
            ax.set_xlabel('Episode Reward')
            ax.set_ylabel('Frequency')
            ax.set_title('Reward Distribution')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.savefig(save_dir / 'reward_distribution.png', dpi=150, bbox_inches='tight')
            plt.close()

            print(f"Plots saved to {save_dir}")


# Utility functions

def compute_power_savings(baseline_power_dbm: float, rl_power_dbm: float) -> float:
    """
    Calculate power savings percentage

    Args:
        baseline_power_dbm: Baseline power in dBm
        rl_power_dbm: RL power in dBm

    Returns:
        Power savings percentage
    """
    # Convert dBm to linear (mW)
    baseline_mw = 10 ** (baseline_power_dbm / 10.0)
    rl_mw = 10 ** (rl_power_dbm / 10.0)

    savings_percent = ((baseline_mw - rl_mw) / baseline_mw) * 100

    return savings_percent


def compute_rsrp_quality_score(rsrp_values: List[float], threshold: float) -> float:
    """
    Compute RSRP quality score (fraction above threshold)

    Args:
        rsrp_values: List of RSRP values
        threshold: RSRP threshold

    Returns:
        Quality score (0-1)
    """
    above_threshold = sum(1 for rsrp in rsrp_values if rsrp >= threshold)
    return above_threshold / len(rsrp_values)


def compute_outage_rate(rsrp_values: List[float], threshold: float) -> float:
    """
    Compute link outage rate

    Args:
        rsrp_values: List of RSRP values
        threshold: RSRP threshold

    Returns:
        Outage rate (0-1)
    """
    below_threshold = sum(1 for rsrp in rsrp_values if rsrp < threshold)
    return below_threshold / len(rsrp_values)


def perform_t_test(group1: List[float], group2: List[float]) -> Dict[str, Any]:
    """
    Perform two-sample t-test

    Args:
        group1: First group (e.g., RL results)
        group2: Second group (e.g., baseline results)

    Returns:
        Test results
    """
    t_statistic, p_value = stats.ttest_ind(group1, group2)

    return {
        't_statistic': float(t_statistic),
        'p_value': float(p_value),
        'significant': p_value < 0.05
    }


def compute_confidence_interval(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Compute confidence interval

    Args:
        data: Data array
        confidence: Confidence level

    Returns:
        (lower_bound, upper_bound)
    """
    mean = np.mean(data)
    se = stats.sem(data)
    margin = se * stats.t.ppf((1 + confidence) / 2, len(data) - 1)

    return mean - margin, mean + margin


def compute_effect_size(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Compute Cohen's d effect size

    Args:
        group1: First group
        group2: Second group

    Returns:
        Effect size
    """
    mean1 = np.mean(group1)
    mean2 = np.mean(group2)
    pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std


if __name__ == '__main__':
    print("Evaluator module - import and use with trained agent")
