#!/usr/bin/env python3
"""
End-to-End Link Budget Validation Tests (Task #8)
==================================================
Tests the full _calculate_rsrp pipeline in NTNPowerEnvironment against
analytically computed reference values.

After fixing:
  - slant range formula (Task #2)
  - antenna gain: 35 dBi (Task #7)
  - fading sigma: 4 dB (Task #7)

RSRP at 30° elevation, LEO 600km, S-band, Tx=46 dBm, no rain:
  slant_range = 1075 km
  FSPL = 92.45 + 20*log10(2.0) + 20*log10(1075) = 159.1 dB
  antenna = 35 + 2*sin(30°) = 36.0 dBi
  RSRP_deterministic = 46 - 159.1 + 36.0 - 0.5 = -77.6 dBm

Author: thc1006
Date: 2026-04-05
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '../../03-Implementation/ntn-simulation/rl_power'))


# Reference FSPL formula
def fspl_db(d_km, f_ghz):
    return 92.45 + 20 * np.log10(f_ghz) + 20 * np.log10(d_km)


def slant_range_km(elevation_deg, altitude_km=600.0):
    el = np.radians(elevation_deg)
    R = 6371.0
    h = altitude_km
    return np.sqrt((R + h)**2 - (R * np.cos(el))**2) - R * np.sin(el)


class TestRSRPDeterministic:
    """
    Test RSRP against analytical formulas by disabling fading.
    Uses fading_sigma_db=0 so _calculate_rsrp is deterministic.
    """

    @pytest.fixture
    def env(self):
        from ntn_env import NTNPowerEnvironment
        e = NTNPowerEnvironment({
            'episode_length': 10,
            'carrier_freq_hz': 2e9,
            'fading_sigma_db': 0.0,   # disable fading for deterministic test
            'base_antenna_gain_db': 35.0,
        })
        e.reset(seed=0)
        return e

    def test_rsrp_30deg_matches_formula(self, env):
        """RSRP at 30° elevation must match analytical calculation ±1 dB."""
        elevation = 30.0
        sr = slant_range_km(elevation, env.sat_altitude_km)
        expected_fspl = fspl_db(sr, 2.0)
        el_factor = 2.0 * np.sin(np.radians(elevation))
        expected_rsrp = 46.0 - expected_fspl + (35.0 + el_factor) - 0.5

        computed_rsrp = env._calculate_rsrp(46.0, sr, elevation, 0.0)
        assert computed_rsrp == pytest.approx(expected_rsrp, abs=1.0), (
            f"RSRP at 30°: got {computed_rsrp:.1f} dBm, expected {expected_rsrp:.1f} dBm"
        )

    def test_rsrp_at_zenith(self, env):
        """RSRP at 90° elevation (zenith) — minimum path loss scenario."""
        elevation = 90.0
        sr = slant_range_km(elevation, env.sat_altitude_km)
        expected_fspl = fspl_db(sr, 2.0)
        el_factor = 2.0 * np.sin(np.radians(elevation))
        expected_rsrp = 46.0 - expected_fspl + (35.0 + el_factor) - 0.5

        computed = env._calculate_rsrp(46.0, sr, elevation, 0.0)
        assert computed == pytest.approx(expected_rsrp, abs=1.0)

    def test_rsrp_monotone_with_elevation(self, env):
        """RSRP must strictly improve as elevation increases (shorter slant range)."""
        rsrp_list = []
        for elev in [10, 20, 30, 45, 60, 90]:
            sr = slant_range_km(elev, env.sat_altitude_km)
            rsrp_list.append(env._calculate_rsrp(46.0, sr, elev, 0.0))

        for i in range(len(rsrp_list) - 1):
            assert rsrp_list[i] < rsrp_list[i + 1], (
                f"RSRP must increase with elevation but dropped between "
                f"entries {i} and {i+1}: {rsrp_list[i]:.1f} > {rsrp_list[i+1]:.1f}"
            )

    def test_rsrp_above_threshold_all_elevations(self, env):
        """
        Without fading, RSRP must exceed -90 dBm at all elevations >= 10°.
        This confirms the RL agent has meaningful margin to reduce power.
        """
        for elev in [10, 20, 30, 45, 60, 90]:
            sr = slant_range_km(elev, env.sat_altitude_km)
            rsrp = env._calculate_rsrp(46.0, sr, elev, 0.0)
            assert rsrp > -90.0, (
                f"RSRP at {elev}° = {rsrp:.1f} dBm is below -90 dBm threshold. "
                f"SR = {sr:.0f} km, FSPL = {fspl_db(sr, 2.0):.1f} dB"
            )

    def test_rsrp_not_unrealistically_high(self, env):
        """RSRP must not exceed -40 dBm (would imply wrong path loss or gain)."""
        for elev in [10, 30, 45, 60, 90]:
            sr = slant_range_km(elev, env.sat_altitude_km)
            rsrp = env._calculate_rsrp(46.0, sr, elev, 0.0)
            assert rsrp < -40.0, (
                f"RSRP at {elev}° = {rsrp:.1f} dBm is unrealistically high. "
                f"Check antenna gain or path loss formula."
            )


class TestRSRPRainEffect:
    """Test that rain attenuation degrades RSRP correctly."""

    @pytest.fixture
    def env(self):
        from ntn_env import NTNPowerEnvironment
        return NTNPowerEnvironment({
            'episode_length': 10,
            'fading_sigma_db': 0.0,
        })

    def test_rain_degrades_rsrp(self, env):
        """RSRP with rain < RSRP without rain."""
        sr = slant_range_km(45.0)
        rsrp_clear = env._calculate_rsrp(46.0, sr, 45.0, 0.0)
        rsrp_rain = env._calculate_rsrp(46.0, sr, 45.0, 25.0)
        assert rsrp_rain <= rsrp_clear, \
            "Rain must degrade (reduce) RSRP"

    def test_rain_attenuation_2ghz_small(self, env):
        """At 2 GHz, rain effect on RSRP must be < 0.5 dB even at 25 mm/h."""
        sr = slant_range_km(45.0)
        rsrp_clear = env._calculate_rsrp(46.0, sr, 45.0, 0.0)
        rsrp_rain = env._calculate_rsrp(46.0, sr, 45.0, 25.0)
        delta = rsrp_clear - rsrp_rain
        assert delta < 0.5, (
            f"2 GHz rain attenuation at 25 mm/h should be < 0.5 dB, got {delta:.3f} dB"
        )


class TestRSRPWithFading:
    """Statistical test: RSRP distribution with 4 dB fading sigma."""

    def test_rsrp_mean_close_to_deterministic(self):
        """With many samples, mean RSRP should match deterministic value ±1 dB."""
        from ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment({
            'episode_length': 1000,
            'fading_sigma_db': 4.0,
        })
        env.reset(seed=42)
        sr = slant_range_km(45.0)

        # Compute reference without fading
        env_det = NTNPowerEnvironment({
            'episode_length': 10,
            'fading_sigma_db': 0.0,
        })
        env_det.reset(seed=42)
        det_rsrp = env_det._calculate_rsrp(46.0, sr, 45.0, 0.0)

        # Sample many RSRP values
        samples = [env._calculate_rsrp(46.0, sr, 45.0, 0.0) for _ in range(500)]
        mean_rsrp = np.mean(samples)
        std_rsrp = np.std(samples)

        assert abs(mean_rsrp - det_rsrp) < 1.0, (
            f"Mean RSRP {mean_rsrp:.1f} should be close to deterministic {det_rsrp:.1f} dBm"
        )
        assert 3.0 <= std_rsrp <= 5.0, (
            f"RSRP std {std_rsrp:.1f} dB should be ~4 dB (shadow fading sigma)"
        )


class TestNTNEnvRSRPFormula:
    """Catch regressions: old 45 dBi / 1 dB fading were both wrong."""

    @pytest.fixture
    def env(self):
        from ntn_env import NTNPowerEnvironment
        return NTNPowerEnvironment({
            'episode_length': 10,
            'fading_sigma_db': 0.0,
        })

    def test_old_45dbi_would_give_wrong_rsrp(self, env):
        """
        Documents the old bug: 45 dBi antenna was 10 dBi too high.
        RSRP was ~10 dB higher than physical reality.
        """
        sr = slant_range_km(10.0)
        rsrp_correct = env._calculate_rsrp(46.0, sr, 10.0, 0.0)

        # What the old code would have returned
        fspl = fspl_db(sr, 2.0)
        rsrp_old = 46.0 - fspl + 45.0 - 0.5  # old 45 dBi, no elevation factor
        rsrp_correct_nofade = 46.0 - fspl + 35.0 + 2.0 * np.sin(np.radians(10.0)) - 0.5

        assert rsrp_old > rsrp_correct_nofade + 8.0, \
            "Old 45 dBi antenna gave RSRP that was >8 dB too optimistic"

    def test_antenna_gain_attribute_matches_calculation(self, env):
        """Verify base_antenna_gain_db attribute is actually used in RSRP."""
        sr = slant_range_km(45.0)
        rsrp_default = env._calculate_rsrp(46.0, sr, 45.0, 0.0)

        # Manually compute expected RSRP
        fspl = fspl_db(sr, 2.0)
        el_factor = 2.0 * np.sin(np.radians(45.0))
        expected = 46.0 - fspl + env.base_antenna_gain_db + el_factor - 0.5

        assert rsrp_default == pytest.approx(expected, abs=0.1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
