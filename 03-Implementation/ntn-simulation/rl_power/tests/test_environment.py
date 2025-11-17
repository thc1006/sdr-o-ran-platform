#!/usr/bin/env python3
"""
Test Suite for NTN Power Control Environment (TDD)
====================================================

Tests written BEFORE implementation following Test-Driven Development.

Test Coverage:
- Environment initialization and reset
- State space representation and bounds
- Action space validation
- Step function and state transitions
- Reward calculation logic
- Episode termination conditions
- Invalid action handling
- State normalization

Author: RL Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import gymnasium as gym
from typing import Dict, Tuple, Any


class TestNTNPowerEnvironment:
    """Test suite for NTN Power Control Gym Environment"""

    @pytest.fixture
    def env(self):
        """Create environment instance for testing"""
        # This will fail initially - that's the point of TDD!
        from rl_power.ntn_env import NTNPowerEnvironment
        return NTNPowerEnvironment()

    @pytest.fixture
    def env_with_config(self):
        """Create environment with custom config"""
        from rl_power.ntn_env import NTNPowerEnvironment
        config = {
            'max_episodes': 500,
            'episode_length': 300,
            'initial_power_dbm': 20.0,
            'target_rsrp_dbm': -85.0,
            'rsrp_threshold_dbm': -90.0,
            'power_penalty_weight': 0.01,
            'rsrp_violation_penalty': 100.0
        }
        return NTNPowerEnvironment(config=config)

    def test_environment_creation(self, env):
        """Test environment can be created"""
        assert env is not None
        assert isinstance(env, gym.Env)

    def test_observation_space(self, env):
        """Test observation space is correctly defined"""
        # State: [elevation_angle, slant_range, rain_rate, current_rsrp, doppler_shift]
        # Expected: 5-dimensional continuous space
        assert env.observation_space.shape == (5,)
        assert isinstance(env.observation_space, gym.spaces.Box)

        # Check bounds are reasonable
        assert env.observation_space.low[0] >= 0.0  # elevation >= 0
        assert env.observation_space.high[0] <= 90.0  # elevation <= 90
        assert env.observation_space.low[1] > 0  # slant_range > 0
        assert env.observation_space.low[3] <= -50.0  # RSRP can be very low
        assert env.observation_space.high[3] >= -30.0  # RSRP can be high

    def test_action_space(self, env):
        """Test action space is discrete with correct actions"""
        # Actions: [-3dB, -1dB, 0dB, +1dB, +3dB]
        # Expected: 5 discrete actions
        assert isinstance(env.action_space, gym.spaces.Discrete)
        assert env.action_space.n == 5

    def test_action_to_power_mapping(self, env):
        """Test action index maps to correct power adjustment"""
        # Assuming mapping: 0->-3dB, 1->-1dB, 2->0dB, 3->+1dB, 4->+3dB
        expected_adjustments = [-3.0, -1.0, 0.0, 1.0, 3.0]

        for action_idx, expected_adj in enumerate(expected_adjustments):
            adjustment = env._action_to_power_adjustment(action_idx)
            assert abs(adjustment - expected_adj) < 0.01

    def test_reset(self, env):
        """Test environment reset returns valid initial state"""
        obs, info = env.reset()

        # Check observation shape
        assert obs.shape == (5,)

        # Check observation values are within bounds
        assert env.observation_space.contains(obs)

        # Check info dict
        assert isinstance(info, dict)
        assert 'episode' in info
        assert 'step' in info
        assert info['step'] == 0

    def test_reset_reproducibility(self, env):
        """Test reset with seed produces reproducible initial states"""
        obs1, _ = env.reset(seed=42)
        obs2, _ = env.reset(seed=42)

        np.testing.assert_array_almost_equal(obs1, obs2)

    def test_step_returns_correct_tuple(self, env):
        """Test step returns (obs, reward, terminated, truncated, info)"""
        env.reset()
        action = env.action_space.sample()

        result = env.step(action)

        assert len(result) == 5
        obs, reward, terminated, truncated, info = result

        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, (float, np.floating))
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_step_observation_bounds(self, env):
        """Test step returns observations within valid bounds"""
        env.reset()

        for _ in range(10):
            action = env.action_space.sample()
            obs, _, done, truncated, _ = env.step(action)

            assert env.observation_space.contains(obs)

            if done or truncated:
                break

    def test_reward_calculation_good_rsrp(self, env):
        """Test reward when RSRP is above threshold"""
        env.reset()

        # Set state where RSRP is good (> -90 dBm)
        # Action: no power change (index 2)
        action = 2  # 0 dB adjustment

        obs, reward, _, _, info = env.step(action)

        # With good RSRP, reward should be negative power consumption
        # (we want to minimize power)
        assert reward <= 0  # Negative because we penalize power usage
        assert 'power_consumption' in info

    def test_reward_calculation_bad_rsrp(self, env):
        """Test penalty when RSRP drops below threshold"""
        env.reset(seed=42)

        # Take multiple steps reducing power to potentially degrade RSRP
        total_penalty = 0
        for _ in range(50):
            action = 0  # -3dB (reduce power)
            obs, reward, done, truncated, info = env.step(action)

            if info.get('rsrp_dbm', -80) < -90:
                # When RSRP < -90 dBm, should get large penalty
                assert reward < -50  # Large negative penalty
                total_penalty += reward
                break

            if done or truncated:
                break

    def test_power_limits(self, env):
        """Test power is constrained to min/max limits"""
        env.reset()

        # Try to increase power many times
        for _ in range(20):
            action = 4  # +3dB
            obs, reward, done, truncated, info = env.step(action)

            assert info['current_power_dbm'] <= env.max_power_dbm

            if done or truncated:
                break

        # Reset and try to decrease power many times
        env.reset()
        for _ in range(20):
            action = 0  # -3dB
            obs, reward, done, truncated, info = env.step(action)

            assert info['current_power_dbm'] >= env.min_power_dbm

            if done or truncated:
                break

    def test_episode_length_truncation(self, env):
        """Test episode truncates after max steps"""
        env.reset()

        max_steps = env.episode_length
        step_count = 0

        for step in range(max_steps + 10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            step_count += 1

            if truncated:
                # Should truncate at or before max_steps
                assert step_count <= max_steps
                break

            if terminated:
                break

        # Should have truncated by max_steps
        assert step_count <= max_steps

    def test_rsrp_violation_termination(self, env):
        """Test episode terminates on severe RSRP violation"""
        env.reset()

        # Continuously reduce power to cause RSRP violation
        for _ in range(100):
            action = 0  # -3dB
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated:
                # Should terminate when RSRP too low
                assert info.get('rsrp_dbm', -80) < env.rsrp_threshold_dbm - 5
                assert 'termination_reason' in info
                break

    def test_state_transitions_realistic(self, env):
        """Test state transitions follow realistic channel dynamics"""
        obs, _ = env.reset(seed=42)

        prev_obs = obs.copy()

        for _ in range(10):
            action = 2  # No power change
            obs, _, done, truncated, _ = env.step(action)

            # Check state changes are continuous (no jumps)
            # Elevation angle shouldn't change drastically in 1 second
            assert abs(obs[0] - prev_obs[0]) < 5.0  # < 5 degrees per step

            # Slant range shouldn't change drastically
            slant_range_change_km = abs(obs[1] - prev_obs[1])
            assert slant_range_change_km < 50.0  # < 50 km per second

            prev_obs = obs.copy()

            if done or truncated:
                break

    def test_rain_attenuation_effect(self, env):
        """Test rain attenuation affects RSRP appropriately"""
        # Reset with seed for reproducibility
        obs, _ = env.reset(seed=123)
        initial_rsrp_idx = 3  # RSRP is 4th element

        # Record RSRP progression
        rsrp_values = [obs[initial_rsrp_idx]]

        for _ in range(20):
            action = 2  # No power change
            obs, _, done, truncated, info = env.step(action)
            rsrp_values.append(obs[initial_rsrp_idx])

            # When rain_rate > 0, RSRP should be affected
            if obs[2] > 0:  # rain_rate is 3rd element
                # Can't guarantee degradation due to other factors,
                # but environment should track rain effect
                assert 'rain_attenuation_db' in info

            if done or truncated:
                break

    def test_doppler_shift_realistic(self, env):
        """Test Doppler shift values are realistic for LEO"""
        env.reset()

        for _ in range(10):
            action = env.action_space.sample()
            obs, _, done, truncated, _ = env.step(action)

            doppler_shift = obs[4]  # 5th element

            # LEO Doppler shift should be within ±50 kHz for 2 GHz carrier
            assert abs(doppler_shift) < 50000  # Hz

            if done or truncated:
                break

    def test_info_dict_completeness(self, env):
        """Test info dict contains all required fields"""
        env.reset()
        action = 2
        _, _, _, _, info = env.step(action)

        required_fields = [
            'step',
            'episode',
            'current_power_dbm',
            'rsrp_dbm',
            'power_consumption',
            'elevation_angle',
            'slant_range_km',
            'rain_rate_mm_h'
        ]

        for field in required_fields:
            assert field in info, f"Missing required field: {field}"

    def test_render_mode(self, env):
        """Test environment supports render mode"""
        # Environment should support render for debugging
        assert hasattr(env, 'render')

    def test_close(self, env):
        """Test environment can be closed properly"""
        env.reset()
        env.step(env.action_space.sample())
        env.close()
        # Should not raise exception

    def test_seed_setting(self, env):
        """Test setting seed affects randomness"""
        obs1, _ = env.reset(seed=42)

        # Take same actions
        actions = [1, 2, 3, 1, 0]
        states1 = []
        for action in actions:
            obs, _, done, truncated, _ = env.step(action)
            states1.append(obs.copy())
            if done or truncated:
                break

        # Reset with same seed
        obs2, _ = env.reset(seed=42)
        states2 = []
        for action in actions:
            obs, _, done, truncated, _ = env.step(action)
            states2.append(obs.copy())
            if done or truncated:
                break

        # Should produce same trajectory
        assert len(states1) == len(states2)
        for s1, s2 in zip(states1, states2):
            np.testing.assert_array_almost_equal(s1, s2, decimal=5)

    def test_custom_config(self, env_with_config):
        """Test environment respects custom configuration"""
        env = env_with_config

        assert env.episode_length == 300
        assert env.initial_power_dbm == 20.0
        assert env.target_rsrp_dbm == -85.0

    def test_reward_shaping_power_penalty(self, env):
        """Test power consumption contributes to reward"""
        env.reset()

        # High power action
        action_high = 4  # +3dB
        _, reward_high, _, _, info_high = env.step(action_high)
        power_high = info_high['current_power_dbm']

        env.reset(seed=42)

        # Low power action
        action_low = 0  # -3dB
        _, reward_low, _, _, info_low = env.step(action_low)
        power_low = info_low['current_power_dbm']

        # With same RSRP quality, lower power should get better reward
        # (assuming both maintain RSRP > threshold)
        if info_high.get('rsrp_dbm', -80) > -90 and info_low.get('rsrp_dbm', -80) > -90:
            assert power_low < power_high

    def test_parallel_environments(self):
        """Test multiple environments can run in parallel"""
        from rl_power.ntn_env import NTNPowerEnvironment

        envs = [NTNPowerEnvironment() for _ in range(4)]

        # Reset all
        for env in envs:
            env.reset(seed=42)

        # Step all
        for env in envs:
            env.step(env.action_space.sample())

        # Close all
        for env in envs:
            env.close()

    def test_gym_check(self, env):
        """Test environment passes gymnasium check"""
        # This will run gymnasium's internal validation
        from gymnasium.utils.env_checker import check_env
        check_env(env, skip_render_check=True)


class TestNTNPowerEnvironmentEdgeCases:
    """Test edge cases and error handling"""

    def test_invalid_action(self):
        """Test handling of invalid action indices"""
        from rl_power.ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment()
        env.reset()

        # Action out of bounds should raise error or be handled
        with pytest.raises((ValueError, AssertionError, IndexError)):
            env.step(10)  # Invalid action

    def test_step_before_reset(self):
        """Test stepping before reset raises error"""
        from rl_power.ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment()

        with pytest.raises((RuntimeError, AssertionError)):
            env.step(0)

    def test_negative_seed(self):
        """Test negative seed is handled"""
        from rl_power.ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment()

        # Should handle negative seed (convert to valid)
        obs, _ = env.reset(seed=-1)
        assert obs is not None

    def test_extreme_rain_rate(self):
        """Test environment handles extreme rain rates"""
        from rl_power.ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment()
        env.reset()

        # Simulate many steps - should encounter varying rain
        for _ in range(100):
            action = 2
            obs, _, done, truncated, _ = env.step(action)

            rain_rate = obs[2]
            # Rain rate should be non-negative
            assert rain_rate >= 0

            if done or truncated:
                break


class TestNTNPowerEnvironmentMetrics:
    """Test environment metrics and statistics"""

    def test_episode_statistics(self):
        """Test environment tracks episode statistics"""
        from rl_power.ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment()
        env.reset()

        total_reward = 0
        steps = 0

        for _ in range(100):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward
            steps += 1

            if done or truncated:
                break

        # Environment should provide episode summary
        assert hasattr(env, 'get_episode_stats') or 'episode_reward' in info

    def test_power_efficiency_tracking(self):
        """Test environment tracks power efficiency"""
        from rl_power.ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment()
        env.reset()

        for _ in range(50):
            action = env.action_space.sample()
            _, _, done, truncated, info = env.step(action)

            # Should track cumulative power consumption
            assert 'power_consumption' in info

            if done or truncated:
                break

    def test_rsrp_violation_tracking(self):
        """Test environment tracks RSRP violations"""
        from rl_power.ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment()
        env.reset()

        # Force power down to cause violations
        violations = 0
        for _ in range(100):
            action = 0  # -3dB
            _, _, done, truncated, info = env.step(action)

            if info.get('rsrp_dbm', -80) < -90:
                violations += 1

            if done or truncated:
                break

        # Should have tracked violations
        assert hasattr(env, 'get_violation_count') or 'rsrp_violations' in info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
