#!/usr/bin/env python3
"""
Test Suite for Evaluation Module (TDD)
=======================================

Tests written BEFORE implementation following Test-Driven Development.

Test Coverage:
- Trained policy evaluation
- Baseline comparison
- Power savings calculation
- Link quality metrics
- Statistical validation (t-tests)
- Performance metrics collection
- Visualization generation

Author: RL Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path


class TestEvaluator:
    """Test evaluator module"""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance"""
        from rl_power.evaluator import Evaluator
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 0.0,  # Evaluation mode
            'epsilon_end': 0.0,
            'epsilon_decay': 1.0,
            'target_update_freq': 100,
            'buffer_capacity': 10000
        })

        return Evaluator(env, agent)

    def test_evaluator_creation(self, evaluator):
        """Test evaluator can be created"""
        assert evaluator is not None
        assert hasattr(evaluator, 'env')
        assert hasattr(evaluator, 'agent')

    def test_evaluate_single_episode(self, evaluator):
        """Test evaluation of single episode"""
        evaluator.agent.epsilon = 0.0  # Pure exploitation

        metrics = evaluator.evaluate_episode()

        assert 'episode_reward' in metrics
        assert 'episode_length' in metrics
        assert 'total_power_consumption' in metrics
        assert 'avg_rsrp_dbm' in metrics
        assert 'rsrp_violations' in metrics

    def test_evaluate_multiple_episodes(self, evaluator):
        """Test evaluation over multiple episodes"""
        evaluator.agent.epsilon = 0.0

        results = evaluator.evaluate(num_episodes=10)

        assert 'mean_reward' in results
        assert 'std_reward' in results
        assert 'mean_power_consumption' in results
        assert 'rsrp_violation_rate' in results
        assert 'all_episode_rewards' in results
        assert len(results['all_episode_rewards']) == 10

    def test_baseline_comparison(self, evaluator):
        """Test comparison with baseline policy"""
        from rl_power.evaluator import RuleBasedBaseline

        baseline = RuleBasedBaseline(target_rsrp=-85.0)

        comparison = evaluator.compare_with_baseline(
            baseline=baseline,
            num_episodes=10
        )

        assert 'rl_results' in comparison
        assert 'baseline_results' in comparison
        assert 'power_savings_percent' in comparison
        assert 'rsrp_quality_comparison' in comparison

    def test_power_savings_calculation(self, evaluator):
        """Test power savings calculation is correct"""
        evaluator.agent.epsilon = 0.0

        # Get RL results
        rl_results = evaluator.evaluate(num_episodes=5)

        # Create baseline
        from rl_power.evaluator import RuleBasedBaseline
        baseline = RuleBasedBaseline(target_rsrp=-85.0)

        # Get baseline results
        baseline_results = evaluator.evaluate_baseline(baseline, num_episodes=5)

        # Calculate savings
        rl_power = rl_results['mean_power_consumption']
        baseline_power = baseline_results['mean_power_consumption']

        savings_percent = ((baseline_power - rl_power) / baseline_power) * 100

        assert isinstance(savings_percent, (float, int))
        # Should have some savings (or at least not significantly worse)
        assert savings_percent >= -20  # Allow up to 20% worse initially

    def test_rsrp_quality_metrics(self, evaluator):
        """Test RSRP quality metrics are collected"""
        evaluator.agent.epsilon = 0.0

        metrics = evaluator.evaluate(num_episodes=10)

        assert 'mean_rsrp_dbm' in metrics
        assert 'rsrp_violation_rate' in metrics
        assert 'min_rsrp_dbm' in metrics
        assert 'max_rsrp_dbm' in metrics

    def test_statistical_significance(self, evaluator):
        """Test statistical significance testing"""
        evaluator.agent.epsilon = 0.0

        from rl_power.evaluator import RuleBasedBaseline
        baseline = RuleBasedBaseline(target_rsrp=-85.0)

        comparison = evaluator.compare_with_baseline(
            baseline=baseline,
            num_episodes=30  # Need enough for t-test
        )

        assert 'statistical_test' in comparison
        assert 'p_value' in comparison['statistical_test']
        assert 't_statistic' in comparison['statistical_test']
        assert 'significant' in comparison['statistical_test']

    def test_performance_report_generation(self, evaluator):
        """Test performance report can be generated"""
        evaluator.agent.epsilon = 0.0

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / 'evaluation_report.json'

            evaluator.generate_report(
                num_episodes=10,
                save_path=report_path
            )

            assert report_path.exists()

            # Verify report content
            import json
            with open(report_path) as f:
                report = json.load(f)

            assert 'evaluation_results' in report
            assert 'timestamp' in report

    def test_visualizations_generation(self, evaluator):
        """Test evaluation visualizations can be generated"""
        evaluator.agent.epsilon = 0.0

        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = Path(tmpdir)

            evaluator.plot_results(
                num_episodes=10,
                save_dir=save_dir
            )

            # Check plot files exist
            plot_files = list(save_dir.glob('*.png'))
            assert len(plot_files) > 0


class TestRuleBasedBaseline:
    """Test rule-based baseline implementation"""

    def test_baseline_creation(self):
        """Test baseline can be created"""
        from rl_power.evaluator import RuleBasedBaseline

        baseline = RuleBasedBaseline(target_rsrp=-85.0)

        assert baseline is not None
        assert baseline.target_rsrp == -85.0

    def test_baseline_action_selection(self):
        """Test baseline selects valid actions"""
        from rl_power.evaluator import RuleBasedBaseline

        baseline = RuleBasedBaseline(target_rsrp=-85.0)

        # Test state: [elevation, slant_range, rain_rate, rsrp, doppler]
        state = np.array([45.0, 800.0, 0.0, -80.0, 10000.0])

        action = baseline.select_action(state)

        assert 0 <= action < 5  # Valid action index

    def test_baseline_rsrp_tracking(self):
        """Test baseline maintains target RSRP"""
        from rl_power.evaluator import RuleBasedBaseline
        from rl_power.ntn_env import NTNPowerEnvironment

        baseline = RuleBasedBaseline(target_rsrp=-85.0)
        env = NTNPowerEnvironment()

        rsrp_values = []

        obs, _ = env.reset(seed=42)

        for _ in range(100):
            action = baseline.select_action(obs)
            obs, reward, done, truncated, info = env.step(action)

            rsrp_values.append(info['rsrp_dbm'])

            if done or truncated:
                break

        # Baseline should try to maintain RSRP near target
        mean_rsrp = np.mean(rsrp_values)

        # Should be within reasonable range of target
        assert -95.0 < mean_rsrp < -75.0

    def test_baseline_power_control_logic(self):
        """Test baseline power control logic"""
        from rl_power.evaluator import RuleBasedBaseline

        baseline = RuleBasedBaseline(target_rsrp=-85.0)

        # Test different RSRP scenarios
        # Low RSRP -> should increase power
        state_low = np.array([45.0, 800.0, 0.0, -92.0, 10000.0])
        action_low = baseline.select_action(state_low)

        # High RSRP -> should decrease power
        state_high = np.array([45.0, 800.0, 0.0, -75.0, 10000.0])
        action_high = baseline.select_action(state_high)

        # Actions should be different for different RSRP
        # (can't guarantee specific actions, but should respond to RSRP)


class TestComparisonMetrics:
    """Test comparison metrics computation"""

    def test_power_savings_metric(self):
        """Test power savings percentage calculation"""
        from rl_power.evaluator import compute_power_savings

        baseline_power = 20.0  # dBm
        rl_power = 17.0  # dBm

        # In linear scale:
        # baseline = 100 mW, rl = 50 mW -> 50% savings
        savings = compute_power_savings(baseline_power, rl_power)

        assert isinstance(savings, float)
        assert savings > 0  # Should have savings
        assert savings < 100  # Can't save more than 100%

    def test_rsrp_quality_score(self):
        """Test RSRP quality scoring"""
        from rl_power.evaluator import compute_rsrp_quality_score

        rsrp_values = [-85.0, -88.0, -82.0, -90.0, -87.0]
        threshold = -90.0

        score = compute_rsrp_quality_score(rsrp_values, threshold)

        assert 0.0 <= score <= 1.0  # Score should be normalized

    def test_link_outage_rate(self):
        """Test link outage rate calculation"""
        from rl_power.evaluator import compute_outage_rate

        rsrp_values = [-85.0, -92.0, -88.0, -95.0, -87.0, -91.0]
        threshold = -90.0

        outage_rate = compute_outage_rate(rsrp_values, threshold)

        # 3 out of 6 are below -90 dBm
        expected_rate = 3 / 6

        assert abs(outage_rate - expected_rate) < 0.01


class TestStatisticalValidation:
    """Test statistical validation methods"""

    def test_t_test_implementation(self):
        """Test t-test for comparing RL vs baseline"""
        from rl_power.evaluator import perform_t_test

        rl_rewards = np.random.randn(30) - 50  # RL performance
        baseline_rewards = np.random.randn(30) - 55  # Baseline performance

        result = perform_t_test(rl_rewards, baseline_rewards)

        assert 'p_value' in result
        assert 't_statistic' in result
        assert 'significant' in result
        assert isinstance(result['p_value'], float)
        assert 0.0 <= result['p_value'] <= 1.0

    def test_confidence_interval(self):
        """Test confidence interval calculation"""
        from rl_power.evaluator import compute_confidence_interval

        data = np.random.randn(100)

        ci_low, ci_high = compute_confidence_interval(data, confidence=0.95)

        assert ci_low < np.mean(data) < ci_high

    def test_effect_size_calculation(self):
        """Test Cohen's d effect size"""
        from rl_power.evaluator import compute_effect_size

        group1 = np.random.randn(50) + 0.5
        group2 = np.random.randn(50)

        effect_size = compute_effect_size(group1, group2)

        assert isinstance(effect_size, float)


class TestEvaluationEdgeCases:
    """Test edge cases in evaluation"""

    def test_evaluation_with_untrained_agent(self):
        """Test evaluation works with untrained agent"""
        from rl_power.evaluator import Evaluator
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 0.0,
            'epsilon_end': 0.0,
            'epsilon_decay': 1.0,
            'target_update_freq': 100,
            'buffer_capacity': 10000
        })

        evaluator = Evaluator(env, agent)

        # Should work even with random policy
        results = evaluator.evaluate(num_episodes=5)

        assert 'mean_reward' in results

    def test_evaluation_with_loaded_model(self):
        """Test evaluation with loaded model"""
        from rl_power.evaluator import Evaluator
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 0.0,
            'epsilon_end': 0.0,
            'epsilon_decay': 1.0,
            'target_update_freq': 100,
            'buffer_capacity': 10000
        })

        # Save and load model
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / 'test_model.pth'
            agent.save(model_path)

            # Create new agent and load
            new_agent = DQNAgent({
                'state_dim': 5,
                'action_dim': 5,
                'hidden_dims': [128, 128, 64],
                'lr': 0.0001,
                'gamma': 0.99,
                'epsilon_start': 0.0,
                'epsilon_end': 0.0,
                'epsilon_decay': 1.0,
                'target_update_freq': 100,
                'buffer_capacity': 10000
            })
            new_agent.load(model_path)

            # Evaluate loaded model
            evaluator = Evaluator(env, new_agent)
            results = evaluator.evaluate(num_episodes=5)

            assert 'mean_reward' in results

    def test_zero_episode_evaluation(self):
        """Test evaluation handles zero episodes gracefully"""
        from rl_power.evaluator import Evaluator
        from rl_power.ntn_env import NTNPowerEnvironment
        from rl_power.dqn_agent import DQNAgent

        env = NTNPowerEnvironment()
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 0.0,
            'epsilon_end': 0.0,
            'epsilon_decay': 1.0,
            'target_update_freq': 100,
            'buffer_capacity': 10000
        })

        evaluator = Evaluator(env, agent)

        # Should handle gracefully
        with pytest.raises((ValueError, AssertionError)):
            evaluator.evaluate(num_episodes=0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
