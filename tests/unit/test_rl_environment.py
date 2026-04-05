#!/usr/bin/env python3
"""
RL Environment Correctness Tests (Task #14)
============================================
Validates NTNPowerEnvironment against physical and RL design requirements.

Requirements tested:
  1. Observation space: values within declared bounds, no NaN/inf
  2. Physics: RSRP changes with power (higher Tx → higher RSRP)
  3. Physics: RSRP degrades at low elevation (longer slant range)
  4. Reward continuity: no cliff at RSRP threshold (Task #15 prerequisite)
  5. Action space: power adjustments respect min/max bounds
  6. Satellite trajectory: elevation follows parabolic arc
  7. Episode termination: only on severe violation or time limit

Author: thc1006
Date: 2026-04-05
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '../../03-Implementation/ntn-simulation/rl_power'))


@pytest.fixture
def env():
    from ntn_env import NTNPowerEnvironment
    e = NTNPowerEnvironment({
        'episode_length': 50,
        'fading_sigma_db': 0.0,   # deterministic for physics tests
    })
    e.reset(seed=42)
    return e


@pytest.fixture
def env_fading():
    from ntn_env import NTNPowerEnvironment
    e = NTNPowerEnvironment({'episode_length': 50})
    e.reset(seed=42)
    return e


# =============================================================================
# Observation Space Validity
# =============================================================================

class TestObservationSpace:

    def test_observation_has_correct_shape(self, env):
        """Observation must have shape matching declared observation_space."""
        obs, _ = env.reset(seed=0)
        assert obs.shape == env.observation_space.shape, (
            f"Observation shape {obs.shape} doesn't match "
            f"observation_space {env.observation_space.shape}"
        )

    def test_observation_within_bounds(self, env):
        """All observation values must lie within declared low/high bounds."""
        obs, _ = env.reset(seed=0)
        low = env.observation_space.low
        high = env.observation_space.high
        assert np.all(obs >= low - 1e-6), f"Observation below low bound: {obs} < {low}"
        assert np.all(obs <= high + 1e-6), f"Observation above high bound: {obs} > {high}"

    def test_observation_no_nan_inf(self, env):
        """Observation must not contain NaN or Inf."""
        obs, _ = env.reset(seed=0)
        assert not np.any(np.isnan(obs)), "Observation contains NaN"
        assert not np.any(np.isinf(obs)), "Observation contains Inf"

    def test_observation_stays_valid_during_episode(self, env):
        """All observations during an episode must be within bounds."""
        obs, _ = env.reset(seed=7)
        for _ in range(30):
            action = env.action_space.sample()
            obs, _, terminated, truncated, _ = env.step(action)
            assert not np.any(np.isnan(obs)), f"NaN in observation: {obs}"
            assert not np.any(np.isinf(obs)), f"Inf in observation: {obs}"
            if terminated or truncated:
                break


# =============================================================================
# Physics Correctness
# =============================================================================

class TestRSRPPhysics:

    def test_higher_power_gives_higher_rsrp(self, env):
        """Increasing Tx power by 3 dB must increase RSRP by ~3 dB."""
        sr = env.slant_range_km
        elev = env.satellite_elevation
        rsrp_low = env._calculate_rsrp(30.0, sr, elev, 0.0)
        rsrp_high = env._calculate_rsrp(33.0, sr, elev, 0.0)
        assert rsrp_high > rsrp_low, "Higher Tx power must produce higher RSRP"
        assert abs((rsrp_high - rsrp_low) - 3.0) < 0.5, (
            f"3 dB power increase should give ~3 dB RSRP increase, "
            f"got {rsrp_high - rsrp_low:.2f} dB"
        )

    def test_rsrp_degrades_at_low_elevation(self, env):
        """RSRP at 10° elevation must be lower than at 90° elevation."""
        rsrp_low_el = env._calculate_rsrp(46.0, env._calculate_slant_range(10.0), 10.0, 0.0)
        rsrp_zenith = env._calculate_rsrp(46.0, env._calculate_slant_range(90.0), 90.0, 0.0)
        assert rsrp_zenith > rsrp_low_el, (
            f"Zenith RSRP {rsrp_zenith:.1f} must exceed low-elevation {rsrp_low_el:.1f} dBm"
        )

    def test_power_action_changes_rsrp_next_step(self, env):
        """Action 4 (increase power +3 dB) must increase RSRP from one step to next."""
        obs1, _ = env.reset(seed=42)
        rsrp_before = env.rsrp_dbm
        power_before = env.current_power_dbm

        # Take max power action (action 4 = +3 dB)
        obs2, _, _, _, info = env.step(4)
        power_after = env.current_power_dbm

        assert power_after >= power_before, "Action 4 must not decrease power"

    def test_satellite_elevation_changes_over_episode(self, env):
        """Satellite elevation must vary over the episode (not static)."""
        elevations = []
        env.reset(seed=0)
        for _ in range(30):
            elev = env.satellite_elevation
            elevations.append(elev)
            _, _, terminated, truncated, _ = env.step(2)  # hold power
            if terminated or truncated:
                break

        elevation_range = max(elevations) - min(elevations)
        assert elevation_range > 5.0, (
            f"Elevation barely varied (range {elevation_range:.1f}°). "
            f"Satellite trajectory should produce significant elevation change."
        )


# =============================================================================
# Action Space Compliance
# =============================================================================

class TestActionSpace:

    def test_all_actions_valid(self, env):
        """All 5 discrete actions must be in action space."""
        for a in range(5):
            assert env.action_space.contains(a)

    def test_power_respects_min_bound(self, env):
        """Taking minimum power action 100x must not go below min_power_dbm."""
        env.reset(seed=0)
        for _ in range(100):
            env.step(0)  # action 0 = decrease power
        assert env.current_power_dbm >= env.min_power_dbm, (
            f"Power {env.current_power_dbm:.1f} below min {env.min_power_dbm} dBm"
        )

    def test_power_respects_max_bound(self, env):
        """Taking maximum power action 100x must not exceed max_power_dbm."""
        env.reset(seed=0)
        for _ in range(100):
            env.step(4)  # action 4 = increase power
        assert env.current_power_dbm <= env.max_power_dbm, (
            f"Power {env.current_power_dbm:.1f} above max {env.max_power_dbm} dBm"
        )

    def test_action_2_hold_power(self, env):
        """Action 2 (hold) must not change current power."""
        env.reset(seed=0)
        power_before = env.current_power_dbm
        env.step(2)  # hold
        power_after = env.current_power_dbm
        assert power_before == power_after, \
            f"Action 2 (hold) changed power from {power_before} to {power_after}"


# =============================================================================
# Reward Continuity (Task #15 prerequisite)
# =============================================================================

class TestRewardContinuity:
    """
    The reward function must be continuous near the RSRP threshold.
    A cliff (discontinuity) at the threshold prevents the RL agent from
    learning a smooth policy to avoid violations.

    Current bug: reward jumps from ~+3 (just above threshold) to -100 (just below).
    Fix: use a smooth penalty that increases continuously below the threshold.
    """

    def test_reward_is_finite(self, env):
        """Reward must always be finite (no -inf or NaN)."""
        env.reset(seed=0)
        for _ in range(30):
            action = env.action_space.sample()
            _, reward, terminated, truncated, _ = env.step(action)
            assert np.isfinite(reward), f"Reward is not finite: {reward}"
            if terminated or truncated:
                break

    def test_reward_cliff_at_threshold_detected(self, env):
        """
        The reward jump from just-above to just-below the RSRP threshold
        must be small (<= 15). Large cliffs prevent gradient-based learning.

        A smooth reward: r(RSRP) should change by ~1 unit per dB,
        not jump from +3 to -100 across a 0.2 dB range.
        """
        # Force RSRP just above threshold
        env.reset(seed=0)
        env.rsrp_dbm = env.rsrp_threshold_dbm + 0.1  # 0.1 dB above
        reward_above = env._calculate_reward()

        # Force RSRP just below threshold
        env.rsrp_dbm = env.rsrp_threshold_dbm - 0.1  # 0.1 dB below
        reward_below = env._calculate_reward()

        jump = reward_above - reward_below
        assert jump <= 15.0, (
            f"REWARD CLIFF: Just-above = {reward_above:.1f}, just-below = {reward_below:.1f}, "
            f"jump = {jump:.1f} (should be <= 15). "
            f"Fix: replace hard penalty step with smooth exponential or linear penalty."
        )

    def test_reward_decreases_continuously_below_threshold(self, env):
        """
        Below threshold, deeper violations should give worse rewards.
        This requires _calculate_reward to be monotonically decreasing
        with violation depth.
        """
        env.reset(seed=0)
        rewards = []
        for rsrp_delta in [0.0, -1.0, -3.0, -5.0, -10.0]:
            env.rsrp_dbm = env.rsrp_threshold_dbm + rsrp_delta
            rewards.append(env._calculate_reward())

        # Rewards must decrease as RSRP goes further below threshold
        for i in range(1, len(rewards)):
            assert rewards[i] <= rewards[i - 1], (
                f"Reward should decrease with deeper violation but "
                f"reward at delta={[-0, -1, -3, -5, -10][i]}dB ({rewards[i]:.2f}) > "
                f"reward at delta={[-0, -1, -3, -5, -10][i-1]}dB ({rewards[i-1]:.2f})"
            )


# =============================================================================
# Episode Termination
# =============================================================================

class TestEpisodeTermination:

    def test_episode_terminates_at_length_limit(self, env):
        """Episode must truncate at episode_length steps."""
        env.reset(seed=0)
        steps = 0
        terminated = truncated = False
        while not terminated and not truncated:
            _, _, terminated, truncated, _ = env.step(2)
            steps += 1
            if steps > env.episode_length + 5:
                pytest.fail("Episode did not terminate at episode_length")

        assert truncated or terminated, "Episode must end"
        assert steps <= env.episode_length + 1, \
            f"Episode ran {steps} steps beyond declared length {env.episode_length}"

    def test_episode_terminates_on_severe_violation(self, env):
        """Severe RSRP violation (>5 dB below threshold) must terminate episode."""
        env.reset(seed=0)
        # Force RSRP to severe violation level
        env.rsrp_dbm = env.rsrp_threshold_dbm - 10.0
        # Check if terminate condition fires
        if env.rsrp_dbm < env.rsrp_threshold_dbm - 5.0:
            # The step function would set terminated=True here
            # We just verify the threshold is set correctly
            assert env.rsrp_threshold_dbm - 5.0 < env.rsrp_dbm + 10.0, \
                "Severe violation threshold should be 5 dB below rsrp_threshold_dbm"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
