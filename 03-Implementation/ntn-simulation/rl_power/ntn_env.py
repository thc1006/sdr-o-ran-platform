#!/usr/bin/env python3
"""
NTN Power Control Environment (OpenAI Gym)
===========================================

Gymnasium-compatible environment for RL-based power control
in LEO satellite communications.

State Space (5D):
- Elevation angle (degrees): [5, 90]
- Slant range (km): [600, 2000]
- Rain rate (mm/h): [0, 150]
- Current RSRP (dBm): [-120, -30]
- Doppler shift (Hz): [-50000, 50000]

Action Space (Discrete, 5 actions):
- 0: -3 dB (reduce power significantly)
- 1: -1 dB (reduce power slightly)
- 2:  0 dB (maintain power)
- 3: +1 dB (increase power slightly)
- 4: +3 dB (increase power significantly)

Reward Function:
- reward = -power_consumption (if RSRP > threshold)
- reward = -100 (large penalty if RSRP < threshold)

Author: RL Specialist
Date: 2025-11-17
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Tuple, Any, Optional
import math


class NTNPowerEnvironment(gym.Env):
    """
    NTN Power Control Environment

    OpenAI Gym environment for training RL agents to optimize
    power consumption while maintaining link quality in LEO satellite links.
    """

    metadata = {'render_modes': ['human']}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NTN Power Control Environment

        Args:
            config: Configuration dictionary with environment parameters
        """
        super().__init__()

        # Configuration
        config = config or {}
        self.max_episodes = config.get('max_episodes', 1000)
        self.episode_length = config.get('episode_length', 300)  # 5 min @ 1 Hz
        self.initial_power_dbm = config.get('initial_power_dbm', 46.0)  # LEO satellite Tx power
        self.max_power_dbm = config.get('max_power_dbm', 49.0)  # Max satellite power
        self.min_power_dbm = config.get('min_power_dbm', 26.0)  # Min satellite power
        self.target_rsrp_dbm = config.get('target_rsrp_dbm', -85.0)
        self.rsrp_threshold_dbm = config.get('rsrp_threshold_dbm', -90.0)
        self.power_penalty_weight = config.get('power_penalty_weight', 0.01)
        self.rsrp_violation_penalty = config.get('rsrp_violation_penalty', 100.0)

        # Carrier frequency (2 GHz for S-band)
        self.carrier_freq_hz = config.get('carrier_freq_hz', 2e9)

        # ITU-R P.618 rain attenuation parameters (2 GHz, 45° elevation)
        self.rain_atten_k = 0.0001  # Specific attenuation coefficient
        self.rain_atten_alpha = 1.0  # Rain attenuation exponent

        # Define action space: 5 discrete power adjustments
        self.action_space = spaces.Discrete(5)

        # Action to power adjustment mapping (dB)
        self.action_to_adjustment = {
            0: -3.0,  # Reduce power significantly
            1: -1.0,  # Reduce power slightly
            2:  0.0,  # Maintain current power
            3:  1.0,  # Increase power slightly
            4:  3.0   # Increase power significantly
        }

        # Define observation space
        # [elevation_angle, slant_range, rain_rate, current_rsrp, doppler_shift]
        self.observation_space = spaces.Box(
            low=np.array([5.0, 600.0, 0.0, -120.0, -50000.0]),
            high=np.array([90.0, 2000.0, 150.0, -30.0, 50000.0]),
            dtype=np.float32
        )

        # Environment state
        self.current_step = 0
        self.current_episode = 0
        self.current_power_dbm = self.initial_power_dbm
        self.satellite_elevation = 45.0  # Initial elevation
        self.satellite_azimuth = 180.0
        self.slant_range_km = 800.0
        self.rain_rate_mm_h = 0.0
        self.doppler_shift_hz = 0.0
        self.rsrp_dbm = -85.0

        # Statistics tracking
        self.episode_reward = 0.0
        self.episode_power_consumption = 0.0
        self.rsrp_violations = 0
        self.total_steps = 0

        # Random number generator
        self.np_random = None

        # LEO satellite parameters
        self.sat_altitude_km = 600.0  # LEO altitude
        self.sat_velocity_km_s = 7.5  # Orbital velocity

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment to initial state

        Args:
            seed: Random seed for reproducibility
            options: Additional reset options

        Returns:
            observation: Initial observation
            info: Additional information dictionary
        """
        super().reset(seed=seed)

        # Initialize random number generator
        if seed is not None:
            self.np_random = np.random.RandomState(seed)
        else:
            if self.np_random is None:
                self.np_random = np.random.RandomState()

        # Reset counters
        self.current_step = 0
        self.current_episode += 1
        self.episode_reward = 0.0
        self.episode_power_consumption = 0.0
        self.rsrp_violations = 0

        # Reset power
        self.current_power_dbm = self.initial_power_dbm

        # Initialize satellite position (random pass)
        self.satellite_elevation = self.np_random.uniform(20.0, 70.0)
        self.satellite_azimuth = self.np_random.uniform(0.0, 360.0)

        # Calculate initial slant range
        self.slant_range_km = self._calculate_slant_range(self.satellite_elevation)

        # Initialize weather
        # Rain probability varies by elevation (lower elevation = more atmosphere)
        rain_prob = 0.1 * (1.0 - self.satellite_elevation / 90.0)
        if self.np_random.random() < rain_prob:
            self.rain_rate_mm_h = self.np_random.exponential(10.0)
        else:
            self.rain_rate_mm_h = 0.0

        # Calculate initial Doppler shift
        self.doppler_shift_hz = self._calculate_doppler_shift(
            self.satellite_elevation,
            self.satellite_azimuth
        )

        # Calculate initial RSRP
        self.rsrp_dbm = self._calculate_rsrp(
            self.current_power_dbm,
            self.slant_range_km,
            self.satellite_elevation,
            self.rain_rate_mm_h
        )

        # Get observation
        observation = self._get_observation()

        # Info dictionary
        info = {
            'episode': self.current_episode,
            'step': self.current_step,
            'current_power_dbm': self.current_power_dbm,
            'rsrp_dbm': self.rsrp_dbm,
            'elevation_angle': self.satellite_elevation,
            'slant_range_km': self.slant_range_km,
            'rain_rate_mm_h': self.rain_rate_mm_h
        }

        return observation, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one time step

        Args:
            action: Action index (0-4)

        Returns:
            observation: Next observation
            reward: Reward for this transition
            terminated: Whether episode is terminated
            truncated: Whether episode is truncated (time limit)
            info: Additional information
        """
        assert self.action_space.contains(action), f"Invalid action: {action}"

        self.current_step += 1
        self.total_steps += 1

        # Apply power adjustment
        power_adjustment_db = self._action_to_power_adjustment(action)
        old_power = self.current_power_dbm
        self.current_power_dbm = np.clip(
            self.current_power_dbm + power_adjustment_db,
            self.min_power_dbm,
            self.max_power_dbm
        )

        # Update satellite position (1 second time step)
        self._update_satellite_position()

        # Update weather conditions
        self._update_weather()

        # Calculate new RSRP
        self.rsrp_dbm = self._calculate_rsrp(
            self.current_power_dbm,
            self.slant_range_km,
            self.satellite_elevation,
            self.rain_rate_mm_h
        )

        # Calculate reward
        reward = self._calculate_reward()
        self.episode_reward += reward

        # Track power consumption
        power_consumption_mw = 10 ** (self.current_power_dbm / 10.0)
        self.episode_power_consumption += power_consumption_mw

        # Check termination conditions
        terminated = False
        truncated = False
        termination_reason = None

        # Severe RSRP violation -> terminate
        if self.rsrp_dbm < self.rsrp_threshold_dbm - 5.0:
            terminated = True
            termination_reason = "SEVERE_RSRP_VIOLATION"

        # Episode length limit -> truncate
        if self.current_step >= self.episode_length:
            truncated = True

        # Get observation
        observation = self._get_observation()

        # Info dictionary
        info = {
            'episode': self.current_episode,
            'step': self.current_step,
            'current_power_dbm': self.current_power_dbm,
            'power_adjustment_db': power_adjustment_db,
            'rsrp_dbm': self.rsrp_dbm,
            'power_consumption': power_consumption_mw,
            'elevation_angle': self.satellite_elevation,
            'slant_range_km': self.slant_range_km,
            'rain_rate_mm_h': self.rain_rate_mm_h,
            'rain_attenuation_db': self._calculate_rain_attenuation(self.rain_rate_mm_h),
            'doppler_shift_hz': self.doppler_shift_hz
        }

        if terminated:
            info['termination_reason'] = termination_reason

        if self.rsrp_dbm < self.rsrp_threshold_dbm:
            self.rsrp_violations += 1
            info['rsrp_violation'] = True

        return observation, reward, terminated, truncated, info

    def _action_to_power_adjustment(self, action: int) -> float:
        """Convert action index to power adjustment in dB"""
        return self.action_to_adjustment[action]

    def _get_observation(self) -> np.ndarray:
        """Get current observation"""
        return np.array([
            self.satellite_elevation,
            self.slant_range_km,
            self.rain_rate_mm_h,
            self.rsrp_dbm,
            self.doppler_shift_hz
        ], dtype=np.float32)

    def _calculate_rsrp(
        self,
        tx_power_dbm: float,
        slant_range_km: float,
        elevation_deg: float,
        rain_rate_mm_h: float
    ) -> float:
        """
        Calculate RSRP using simplified link budget

        RSRP = Tx_power - Path_loss - Rain_attenuation + Antenna_gain
        """
        # Free space path loss (Friis equation)
        distance_m = slant_range_km * 1000.0
        wavelength_m = 3e8 / self.carrier_freq_hz
        fspl_db = 20 * np.log10(distance_m) + 20 * np.log10(self.carrier_freq_hz) - 147.55

        # Rain attenuation
        rain_atten_db = self._calculate_rain_attenuation(rain_rate_mm_h)

        # Antenna gain (elevation-dependent)
        # Combined satellite antenna (25 dBi) + ground terminal (20 dBi) + elevation factor
        # Higher elevation = better antenna gain (multipath reduction)
        base_antenna_gain = 45.0  # Combined Tx + Rx antenna gains
        elevation_factor = 5.0 * np.sin(np.radians(elevation_deg))  # 0 to 5 dB
        antenna_gain_db = base_antenna_gain + elevation_factor

        # Atmospheric loss (simplified)
        atmospheric_loss_db = 0.5

        # Calculate RSRP
        rsrp = (tx_power_dbm - fspl_db - rain_atten_db +
                antenna_gain_db - atmospheric_loss_db)

        # Add small random variation (fading)
        rsrp += self.np_random.normal(0, 1.0)

        return rsrp

    def _calculate_rain_attenuation(self, rain_rate_mm_h: float) -> float:
        """
        Calculate rain attenuation using ITU-R P.618 model

        A = k * R^alpha * L_eff
        where L_eff is effective path length through rain
        """
        if rain_rate_mm_h <= 0:
            return 0.0

        # Effective path length through rain (depends on elevation)
        # Lower elevation = longer path through rain
        elevation_rad = np.radians(self.satellite_elevation)
        effective_length_km = 5.0 / np.sin(elevation_rad)  # Simplified

        # Specific attenuation (dB/km)
        specific_atten = self.rain_atten_k * (rain_rate_mm_h ** self.rain_atten_alpha)

        # Total attenuation
        rain_atten_db = specific_atten * effective_length_km

        return rain_atten_db

    def _calculate_slant_range(self, elevation_deg: float) -> float:
        """Calculate slant range from elevation angle"""
        elevation_rad = np.radians(elevation_deg)
        earth_radius_km = 6371.0

        # Law of cosines for slant range
        h = self.sat_altitude_km
        R_e = earth_radius_km

        # Slant range
        slant_range = np.sqrt(
            R_e**2 + (R_e + h)**2 - 2 * R_e * (R_e + h) * np.cos(np.pi/2 - elevation_rad)
        )

        return slant_range

    def _calculate_doppler_shift(self, elevation_deg: float, azimuth_deg: float) -> float:
        """
        Calculate Doppler shift for LEO satellite

        Doppler shift = (v/c) * f_carrier * cos(angle)
        """
        # Radial velocity component
        # Simplified: assume satellite moving horizontally relative to user
        elevation_rad = np.radians(elevation_deg)

        # Velocity component towards/away from user
        radial_velocity_km_s = self.sat_velocity_km_s * np.cos(elevation_rad)

        # Doppler shift (Hz)
        c_km_s = 299792.458  # Speed of light in km/s
        doppler_hz = (radial_velocity_km_s / c_km_s) * self.carrier_freq_hz

        # Add sign based on satellite motion direction
        # Simplified: random sign for approaching/receding
        if self.np_random.random() < 0.5:
            doppler_hz = -doppler_hz

        return doppler_hz

    def _update_satellite_position(self):
        """Update satellite position (1 second time step)"""
        # Satellite moves across sky
        # Simplified model: elevation follows parabolic trajectory

        # Angular velocity (degrees per second)
        # LEO satellite pass duration ~ 10 minutes for elevation > 20°
        angular_velocity_deg_s = 0.15  # degrees per second

        # Update elevation
        # Peak at middle of pass, descend towards end
        pass_progress = self.current_step / self.episode_length

        # Parabolic trajectory: peak at 50% of pass
        peak_elevation = self.satellite_elevation if self.current_step == 0 else 70.0
        self.satellite_elevation = peak_elevation * (1 - 4 * (pass_progress - 0.5)**2)

        # Clamp to valid range
        self.satellite_elevation = np.clip(self.satellite_elevation, 5.0, 90.0)

        # Update azimuth (satellite moves across sky)
        self.satellite_azimuth += angular_velocity_deg_s
        self.satellite_azimuth = self.satellite_azimuth % 360.0

        # Update slant range
        self.slant_range_km = self._calculate_slant_range(self.satellite_elevation)

        # Update Doppler shift
        self.doppler_shift_hz = self._calculate_doppler_shift(
            self.satellite_elevation,
            self.satellite_azimuth
        )

    def _update_weather(self):
        """Update weather conditions"""
        # Rain rate evolves over time (Markov process)
        if self.rain_rate_mm_h > 0:
            # Rain can intensify, weaken, or stop
            change = self.np_random.normal(0, 2.0)
            self.rain_rate_mm_h = max(0.0, self.rain_rate_mm_h + change)

            # Rain stops with probability
            if self.np_random.random() < 0.05:
                self.rain_rate_mm_h = 0.0
        else:
            # Rain can start
            if self.np_random.random() < 0.02:
                self.rain_rate_mm_h = self.np_random.exponential(10.0)

        # Clamp to valid range
        self.rain_rate_mm_h = np.clip(self.rain_rate_mm_h, 0.0, 150.0)

    def _calculate_reward(self) -> float:
        """
        Calculate reward for current state

        Improved reward design with shaped rewards:
        1. Strong penalty for RSRP violations (exponential)
        2. Reward for power efficiency (normalized by realistic satellite power)
        3. Bonus for optimal RSRP range (near target)
        4. Penalty for excessive margin (wasting power)
        """
        # RSRP violation handling (exponential penalty for severity)
        if self.rsrp_dbm < self.rsrp_threshold_dbm:
            # Violation severity in dB below threshold
            violation_db = self.rsrp_threshold_dbm - self.rsrp_dbm
            # Exponential penalty: small violations get moderate penalty, large violations get huge penalty
            violation_penalty = self.rsrp_violation_penalty * (1.0 + violation_db ** 2 / 100.0)
            return -violation_penalty

        # RSRP is acceptable - optimize for power efficiency
        # Normalize power penalty (satellite power is 26-49 dBm, so we scale accordingly)
        power_normalized = (self.current_power_dbm - self.min_power_dbm) / (self.max_power_dbm - self.min_power_dbm)
        power_penalty = 10.0 * power_normalized  # 0 to 10 range

        # RSRP margin analysis
        rsrp_margin = self.rsrp_dbm - self.rsrp_threshold_dbm  # dB above threshold
        target_margin = self.target_rsrp_dbm - self.rsrp_threshold_dbm  # Optimal: 5 dB

        # Efficiency bonus: reward being near target (not too much, not too little)
        margin_error = abs(rsrp_margin - target_margin)
        if margin_error < 2.0:
            # Within 2 dB of target: excellent
            efficiency_bonus = 5.0
        elif margin_error < 5.0:
            # Within 5 dB of target: good
            efficiency_bonus = 2.0
        elif rsrp_margin > target_margin + 10.0:
            # Excessive margin (>15 dB above threshold): wasting power
            efficiency_bonus = -2.0 * (rsrp_margin - target_margin - 10.0)
        else:
            # Acceptable but not optimal
            efficiency_bonus = 0.0

        # Total reward: minimize power, maximize efficiency
        reward = -power_penalty + efficiency_bonus

        return reward

    def render(self, mode='human'):
        """Render environment state"""
        if mode == 'human':
            print(f"\n=== Step {self.current_step} ===")
            print(f"Power: {self.current_power_dbm:.1f} dBm")
            print(f"RSRP: {self.rsrp_dbm:.1f} dBm (threshold: {self.rsrp_threshold_dbm} dBm)")
            print(f"Elevation: {self.satellite_elevation:.1f}°")
            print(f"Slant range: {self.slant_range_km:.1f} km")
            print(f"Rain rate: {self.rain_rate_mm_h:.1f} mm/h")
            print(f"Doppler: {self.doppler_shift_hz:.0f} Hz")

    def close(self):
        """Clean up environment"""
        pass

    def get_episode_stats(self) -> Dict[str, Any]:
        """Get statistics for current episode"""
        return {
            'episode': self.current_episode,
            'total_steps': self.current_step,
            'episode_reward': self.episode_reward,
            'episode_power_consumption': self.episode_power_consumption,
            'avg_power_consumption': self.episode_power_consumption / max(1, self.current_step),
            'rsrp_violations': self.rsrp_violations,
            'rsrp_violation_rate': self.rsrp_violations / max(1, self.current_step)
        }

    def get_violation_count(self) -> int:
        """Get number of RSRP violations in current episode"""
        return self.rsrp_violations


# Utility function for testing
def test_environment():
    """Test environment basic functionality"""
    env = NTNPowerEnvironment()

    print("Testing NTN Power Control Environment")
    print("=" * 50)

    obs, info = env.reset(seed=42)
    print(f"\nInitial observation: {obs}")
    print(f"Initial info: {info}")

    total_reward = 0
    for step in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        print(f"\nStep {step+1}:")
        print(f"  Action: {action} ({env._action_to_power_adjustment(action):+.1f} dB)")
        print(f"  Reward: {reward:.2f}")
        print(f"  RSRP: {info['rsrp_dbm']:.1f} dBm")
        print(f"  Power: {info['current_power_dbm']:.1f} dBm")

        if terminated or truncated:
            print(f"\nEpisode ended at step {step+1}")
            break

    print(f"\nTotal reward: {total_reward:.2f}")
    print(f"Episode stats: {env.get_episode_stats()}")

    env.close()


if __name__ == '__main__':
    test_environment()
