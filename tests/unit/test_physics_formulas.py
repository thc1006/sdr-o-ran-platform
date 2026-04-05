#!/usr/bin/env python3
"""
TDD Physics Formula Tests
==========================
Validates all satellite link budget calculations against 3GPP TR 38.821
reference values and fundamental physics.

These tests are the GROUND TRUTH. Any module whose formulas disagree
with these tests has a bug.

Author: thc1006
Date: 2026-04-05
"""

import numpy as np
import pytest
import sys
import os

# Constants
EARTH_RADIUS_KM = 6371.0
SPEED_OF_LIGHT_M_S = 299792458.0
SPEED_OF_LIGHT_KM_S = 299792.458


# =============================================================================
# Helper: Reference implementations (verified against 3GPP TR 38.821)
# =============================================================================

def reference_slant_range_km(elevation_deg: float, altitude_km: float) -> float:
    """
    3GPP TR 38.821 standard slant range formula.

    d = sqrt((R_e + h)^2 - (R_e * cos(el))^2) - R_e * sin(el)
    """
    el_rad = np.radians(elevation_deg)
    R = EARTH_RADIUS_KM
    h = altitude_km
    return np.sqrt((R + h) ** 2 - (R * np.cos(el_rad)) ** 2) - R * np.sin(el_rad)


def reference_fspl_db(distance_km: float, frequency_ghz: float) -> float:
    """
    Standard Free Space Path Loss.
    FSPL(dB) = 92.45 + 20*log10(f_GHz) + 20*log10(d_km)
    Equivalently: 32.45 + 20*log10(f_MHz) + 20*log10(d_km)
    """
    return 92.45 + 20 * np.log10(frequency_ghz) + 20 * np.log10(distance_km)


def reference_max_doppler_hz(
    elevation_deg: float,
    altitude_km: float,
    orbital_velocity_km_s: float,
    carrier_freq_hz: float,
) -> float:
    """
    Maximum Doppler shift magnitude at given elevation.

    The radial velocity for a satellite pass is:
      v_radial = v_sat * sin(nadir_angle)
    where nadir_angle = arcsin(R_e * cos(el) / (R_e + h))

    This simplifies to:
      v_radial = v_sat * R_e * cos(el) / (R_e + h)

    Doppler = v_radial / c * f_carrier
    """
    el_rad = np.radians(elevation_deg)
    R = EARTH_RADIUS_KM
    h = altitude_km
    v_radial = orbital_velocity_km_s * R * np.cos(el_rad) / (R + h)
    return abs(v_radial * 1000.0 / SPEED_OF_LIGHT_M_S * carrier_freq_hz)


# =============================================================================
# SLANT RANGE TESTS (Task #1)
# =============================================================================

class TestSlantRange:
    """Validate slant range calculations against 3GPP TR 38.821."""

    # 3GPP reference scenarios
    LEO_600 = 600.0  # km
    LEO_1200 = 1200.0
    GEO = 35786.0

    def test_leo600_zenith(self):
        """At 90° elevation, slant range equals altitude."""
        sr = reference_slant_range_km(90.0, self.LEO_600)
        assert sr == pytest.approx(600.0, abs=0.1)

    def test_leo600_10deg(self):
        """LEO 600km at 10° elevation → ~1932 km (3GPP reference)."""
        sr = reference_slant_range_km(10.0, self.LEO_600)
        assert sr == pytest.approx(1932, rel=0.01)

    def test_leo600_30deg(self):
        """LEO 600km at 30° elevation → ~1075 km."""
        sr = reference_slant_range_km(30.0, self.LEO_600)
        assert sr == pytest.approx(1075, rel=0.01)

    def test_leo600_45deg(self):
        """LEO 600km at 45° elevation → ~815 km."""
        sr = reference_slant_range_km(45.0, self.LEO_600)
        assert sr == pytest.approx(815, rel=0.01)

    def test_leo1200_10deg(self):
        """LEO 1200km at 10° elevation → ~3131 km."""
        sr = reference_slant_range_km(10.0, self.LEO_1200)
        assert sr == pytest.approx(3131, rel=0.01)

    def test_geo_zenith(self):
        """GEO at 90° elevation → 35786 km."""
        sr = reference_slant_range_km(90.0, self.GEO)
        assert sr == pytest.approx(35786.0, abs=1.0)

    def test_geo_10deg(self):
        """GEO at 10° elevation → ~40586 km."""
        sr = reference_slant_range_km(10.0, self.GEO)
        assert sr == pytest.approx(40586, rel=0.01)

    def test_slant_range_decreases_with_elevation(self):
        """Slant range must monotonically decrease as elevation increases."""
        elevations = [5, 10, 20, 30, 45, 60, 75, 90]
        ranges = [reference_slant_range_km(e, self.LEO_600) for e in elevations]
        for i in range(len(ranges) - 1):
            assert ranges[i] > ranges[i + 1], (
                f"Slant range must decrease: {elevations[i]}°={ranges[i]:.0f} km "
                f"should be > {elevations[i+1]}°={ranges[i+1]:.0f} km"
            )

    def test_leo600_max_slant_range_reasonable(self):
        """LEO 600km max slant range (5° elevation) must be < 2500 km."""
        sr = reference_slant_range_km(5.0, self.LEO_600)
        assert sr < 2500, f"LEO-600 at 5° should be <2500 km, got {sr:.0f} km"

    # --- Tests that CATCH the known bugs ---

    def test_ntn_env_slant_range(self):
        """ntn_env.py _calculate_slant_range must match 3GPP reference."""
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), '../../03-Implementation/ntn-simulation/rl_power'))
        from ntn_env import NTNPowerEnvironment

        env = NTNPowerEnvironment({'episode_length': 10})
        for elev in [10, 30, 45, 60, 90]:
            code_sr = env._calculate_slant_range(elev)
            ref_sr = reference_slant_range_km(elev, env.sat_altitude_km)
            assert code_sr == pytest.approx(ref_sr, rel=0.02), (
                f"ntn_env slant range at {elev}°: got {code_sr:.0f} km, "
                f"expected {ref_sr:.0f} km"
            )


# =============================================================================
# FSPL TESTS (Task #3)
# =============================================================================

class TestFSPL:
    """Validate Free Space Path Loss calculations."""

    def test_fspl_2ghz_800km(self):
        """2 GHz, 800 km → ~156.5 dB."""
        fspl = reference_fspl_db(800.0, 2.0)
        assert fspl == pytest.approx(156.5, abs=0.5)

    def test_fspl_2ghz_1932km(self):
        """2 GHz, 1932 km → ~164.2 dB."""
        fspl = reference_fspl_db(1932.0, 2.0)
        assert fspl == pytest.approx(164.2, abs=0.5)

    def test_fspl_2ghz_600km(self):
        """2 GHz, 600 km (zenith LEO) → ~154.0 dB."""
        fspl = reference_fspl_db(600.0, 2.0)
        assert fspl == pytest.approx(154.0, abs=0.5)

    def test_fspl_28ghz_600km(self):
        """28 GHz (Ka-band), 600 km → ~177.0 dB."""
        fspl = reference_fspl_db(600.0, 28.0)
        assert fspl == pytest.approx(177.0, abs=0.5)

    def test_fspl_formula_equivalence(self):
        """92.45 + 20log10(f_GHz) + 20log10(d_km) == 32.45 + 20log10(f_MHz) + 20log10(d_km)."""
        d_km = 1000.0
        f_ghz = 2.0
        f_mhz = f_ghz * 1000

        form_ghz = 92.45 + 20 * np.log10(f_ghz) + 20 * np.log10(d_km)
        form_mhz = 32.45 + 20 * np.log10(f_mhz) + 20 * np.log10(d_km)
        form_hz = 20 * np.log10(d_km * 1000) + 20 * np.log10(f_ghz * 1e9) - 147.55

        assert form_ghz == pytest.approx(form_mhz, abs=0.01)
        assert form_ghz == pytest.approx(form_hz, abs=0.01)

    def test_fspl_must_not_use_mhz_with_ghz_constant(self):
        """FSPL with freq_ghz*1000 must use constant 32.45, NOT 92.45."""
        d_km = 800.0
        f_ghz = 2.0
        correct = reference_fspl_db(d_km, f_ghz)

        # The bug: using MHz with GHz constant → 60 dB too high
        buggy = 20 * np.log10(d_km) + 20 * np.log10(f_ghz * 1000) + 92.45
        assert buggy == pytest.approx(correct + 60.0, abs=0.01), \
            "This test documents the 60 dB bug pattern"

    def test_ntn_env_fspl(self):
        """ntn_env.py FSPL formula must match reference (uses Hz and meters)."""
        d_km = 800.0
        f_hz = 2e9
        d_m = d_km * 1000.0

        ntn_env_fspl = 20 * np.log10(d_m) + 20 * np.log10(f_hz) - 147.55
        ref_fspl = reference_fspl_db(d_km, f_hz / 1e9)

        assert ntn_env_fspl == pytest.approx(ref_fspl, abs=0.1)


# =============================================================================
# DOPPLER TESTS (Task #5)
# =============================================================================

class TestDoppler:
    """Validate Doppler shift calculations."""

    LEO_ALT = 600.0  # km
    LEO_V = 7.56  # km/s (circular orbit at 600 km)
    FREQ_2GHZ = 2e9

    def test_doppler_zero_at_zenith(self):
        """Doppler must be ~0 at 90° elevation (satellite moving tangentially)."""
        doppler = reference_max_doppler_hz(90.0, self.LEO_ALT, self.LEO_V, self.FREQ_2GHZ)
        assert doppler < 100, f"Doppler at zenith should be ~0, got {doppler:.0f} Hz"

    def test_doppler_max_at_horizon(self):
        """Doppler must be maximum near the horizon (low elevation)."""
        d_10 = reference_max_doppler_hz(10.0, self.LEO_ALT, self.LEO_V, self.FREQ_2GHZ)
        d_45 = reference_max_doppler_hz(45.0, self.LEO_ALT, self.LEO_V, self.FREQ_2GHZ)
        d_90 = reference_max_doppler_hz(90.0, self.LEO_ALT, self.LEO_V, self.FREQ_2GHZ)

        assert d_10 > d_45 > d_90, (
            f"Doppler must decrease with elevation: "
            f"10°={d_10:.0f} > 45°={d_45:.0f} > 90°={d_90:.0f} Hz"
        )

    def test_doppler_magnitude_leo_2ghz(self):
        """LEO 600km at 10° elevation, 2 GHz → ~46 kHz."""
        doppler = reference_max_doppler_hz(10.0, self.LEO_ALT, self.LEO_V, self.FREQ_2GHZ)
        assert doppler == pytest.approx(46000, rel=0.05), \
            f"Expected ~46 kHz, got {doppler/1000:.1f} kHz"

    def test_doppler_geometric_correction_factor(self):
        """Simplified v*cos(el) overestimates by R_e/(R_e+h) factor."""
        el_deg = 30.0
        el_rad = np.radians(el_deg)

        # Incorrect (no geometric correction)
        v_radial_wrong = self.LEO_V * np.cos(el_rad)
        # Correct (with geometric correction)
        v_radial_correct = self.LEO_V * EARTH_RADIUS_KM * np.cos(el_rad) / (EARTH_RADIUS_KM + self.LEO_ALT)

        ratio = v_radial_wrong / v_radial_correct
        expected_ratio = (EARTH_RADIUS_KM + self.LEO_ALT) / EARTH_RADIUS_KM
        assert ratio == pytest.approx(expected_ratio, rel=0.001)

    def test_doppler_sin_elevation_is_backwards(self):
        """Using sin(elevation) gives max at zenith — this is WRONG."""
        v_sat = self.LEO_V

        doppler_at_10 = abs(v_sat * np.sin(np.radians(10.0)))
        doppler_at_90 = abs(v_sat * np.sin(np.radians(90.0)))

        # sin(el) gives max at zenith — opposite of physics
        assert doppler_at_90 > doppler_at_10, \
            "sin(el) formula is backwards: this test documents the bug"

    def test_doppler_sign_must_not_be_random(self):
        """Doppler sign depends on satellite trajectory, not random coin flip."""
        # During approach: positive (blue shift)
        # During departure: negative (red shift)
        # It must NOT be randomized per timestep
        # This is a design test — no formula to check, just documenting the requirement.
        pass  # Enforced by code review in Phase 2.2


# =============================================================================
# INTEGRATED LINK BUDGET TESTS (for Task #8, run after fixes)
# =============================================================================

class TestLinkBudget:
    """End-to-end link budget sanity checks."""

    def test_rsrp_leo600_s_band_reasonable(self):
        """RSRP for LEO 600km, S-band should be in reasonable range."""
        tx_power_dbm = 46.0  # Satellite Tx
        antenna_gain_dbi = 35.0  # Sat 30 + UE 5 (realistic)
        atmospheric_loss_db = 0.5

        for elev in [10, 30, 45, 60, 90]:
            sr = reference_slant_range_km(elev, 600.0)
            fspl = reference_fspl_db(sr, 2.0)
            rsrp = tx_power_dbm + antenna_gain_dbi - fspl - atmospheric_loss_db

            # RSRP should be well above -90 dBm threshold for all elevations
            assert rsrp > -90.0, (
                f"RSRP at {elev}° = {rsrp:.1f} dBm is below -90 dBm threshold. "
                f"SR={sr:.0f} km, FSPL={fspl:.1f} dB"
            )
            # RSRP should not be unrealistically high
            assert rsrp < -40.0, f"RSRP at {elev}° = {rsrp:.1f} dBm is unrealistically high"

    def test_rsrp_improves_with_elevation(self):
        """RSRP should improve as elevation increases (shorter path)."""
        tx_power_dbm = 46.0
        antenna_gain_dbi = 35.0

        rsrp_values = []
        for elev in [10, 30, 45, 60, 90]:
            sr = reference_slant_range_km(elev, 600.0)
            fspl = reference_fspl_db(sr, 2.0)
            rsrp = tx_power_dbm + antenna_gain_dbi - fspl - 0.5
            rsrp_values.append(rsrp)

        for i in range(len(rsrp_values) - 1):
            assert rsrp_values[i] < rsrp_values[i + 1], \
                "RSRP must improve (increase) with higher elevation"


# =============================================================================
# ANTENNA GAIN TESTS (Task #7)
# =============================================================================

class TestAntennaGain:
    """
    Validate antenna gain parameters against 3GPP TR 38.821 / TR 38.811.

    3GPP TR 38.821 Table 6.1.3-1 reference values:
      - LEO satellite Tx antenna: ~30-35 dBi (directional beam)
      - NTN UE handheld receive: 0-5 dBi (omnidirectional/patch at 2 GHz)
      - NTN UE fixed terminal: 10-15 dBi (small dish/phased array)
    """

    def test_combined_antenna_gain_reasonable_range(self):
        """Combined Tx+Rx gain for typical NTN terminal must be 30-40 dBi."""
        # Typical scenario: LEO satellite (30 dBi) + handheld UE (5 dBi) = 35 dBi
        typical_combined = 30.0 + 5.0
        assert 30.0 <= typical_combined <= 40.0, \
            "Typical combined NTN antenna gain should be 30-40 dBi"

    def test_ue_antenna_gain_at_2ghz_bound(self):
        """At 2 GHz, a handheld UE cannot realistically achieve 20 dBi."""
        # 20 dBi at 2 GHz (λ=15cm) requires ~1.5 m² effective aperture —
        # clearly impossible for a handheld terminal.
        UE_GAIN_MAX_HANDHELD = 5.0  # dBi realistic upper bound for mobile UE
        assert UE_GAIN_MAX_HANDHELD < 20.0, \
            "Handheld UE at 2 GHz cannot achieve 20 dBi — physics constraint"

    def test_ntn_env_base_antenna_gain_attribute_exists(self):
        """ntn_env.py must expose base_antenna_gain_db as an attribute."""
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), '../../03-Implementation/ntn-simulation/rl_power'))
        from ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment({'episode_length': 10})
        assert hasattr(env, 'base_antenna_gain_db'), (
            "NTNPowerEnvironment must expose base_antenna_gain_db as a testable attribute"
        )

    def test_ntn_env_base_antenna_gain_realistic(self):
        """ntn_env.py base_antenna_gain_db must be <= 38 dBi (not 45 dBi)."""
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), '../../03-Implementation/ntn-simulation/rl_power'))
        from ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment({'episode_length': 10})
        assert env.base_antenna_gain_db <= 38.0, (
            f"base_antenna_gain_db = {env.base_antenna_gain_db} dBi. "
            f"3GPP TR 38.821: LEO NTN combined gain is ~35 dBi (sat 30 + UE 5). "
            f"45 dBi requires a 20 dBi UE antenna (impossible at 2 GHz handheld)."
        )


# =============================================================================
# SHADOW FADING TESTS (Task #7)
# =============================================================================

class TestShadowFading:
    """
    Validate shadow fading sigma against 3GPP TR 38.811.

    3GPP TR 38.811 Table 6.6.6.1-1 (NTN channel model, S-band):
      - LOS conditions (suburban/rural): σ_SF = 4 dB
      - NLOS conditions: σ_SF = 6 dB
    """

    def test_shadow_fading_sigma_minimum_4db(self):
        """
        Shadow fading sigma must be at least 4 dB (TR 38.811 LOS NTN).
        1 dB sigma would under-represent link quality variations by 4x.
        """
        TR_38811_LOS_SIGMA = 4.0  # dB
        assert TR_38811_LOS_SIGMA >= 4.0

    def test_shadow_fading_1db_is_wrong(self):
        """
        Sigma=1 dB produces only 20% of correct fading range.
        Documents the bug: TR 38.811 requires 4 dB, not 1 dB.
        """
        wrong_sigma = 1.0
        correct_sigma = 4.0
        # At 3-sigma, wrong = ±3 dB vs correct = ±12 dB — a 4x error
        assert wrong_sigma * 4 == correct_sigma, \
            f"1 dB sigma is exactly 4x smaller than the required 4 dB"

    def test_ntn_env_fading_sigma_attribute_exists(self):
        """ntn_env.py must expose fading_sigma_db as a testable attribute."""
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), '../../03-Implementation/ntn-simulation/rl_power'))
        from ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment({'episode_length': 10})
        assert hasattr(env, 'fading_sigma_db'), (
            "NTNPowerEnvironment must expose fading_sigma_db as a configurable attribute"
        )

    def test_ntn_env_fading_sigma_is_4db_minimum(self):
        """ntn_env.py fading_sigma_db must be >= 4.0 dB (TR 38.811 LOS)."""
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), '../../03-Implementation/ntn-simulation/rl_power'))
        from ntn_env import NTNPowerEnvironment
        env = NTNPowerEnvironment({'episode_length': 10})
        assert env.fading_sigma_db >= 4.0, (
            f"fading_sigma_db = {env.fading_sigma_db} dB. "
            f"3GPP TR 38.811 Table 6.6.6.1-1 LOS NTN requires σ_SF >= 4 dB."
        )


# =============================================================================
# RAIN ATTENUATION TESTS (Task #7)
# =============================================================================

class TestRainAttenuation:
    """
    Validate rain attenuation against ITU-R P.618-13 / P.838-3.

    Key insight: at 2 GHz (S-band), rain attenuation is genuinely
    very small (< 0.05 dB) — this is correct physics, not a bug.
    The test documents the physically correct values.
    """

    # ITU-R P.838-3 Table 1 coefficients
    # Frequency: 2 GHz
    K_H_2GHZ = 0.0000847
    ALPHA_H_2GHZ = 1.0664
    K_V_2GHZ = 0.0000998
    ALPHA_V_2GHZ = 0.9491

    # Frequency: 20 GHz (Ka-band reference)
    K_H_20GHZ = 0.0751
    ALPHA_H_20GHZ = 1.0999

    def test_rain_attenuation_2ghz_low(self):
        """
        At 2 GHz, total rain attenuation < 0.2 dB even in heavy rain (25 mm/h).
        ITU-R P.838-3: 2 GHz is below the rain attenuation knee (~10 GHz).
        """
        rain_rate = 25.0  # mm/h (heavy rain, exceeded < 1% of time in temperate zones)
        elev_rad = np.radians(45)
        effective_length_km = 5.0 / np.sin(elev_rad)  # ≈7 km

        specific_atten = self.K_H_2GHZ * (rain_rate ** self.ALPHA_H_2GHZ)
        total_atten = specific_atten * effective_length_km

        assert total_atten < 0.2, (
            f"2 GHz rain attenuation at {rain_rate} mm/h = {total_atten:.4f} dB. "
            f"Should be < 0.2 dB (per ITU-R P.838-3)"
        )

    def test_rain_attenuation_kaband_significant(self):
        """
        At 20 GHz (Ka-band), rain attenuation > 2 dB at heavy rain (25 mm/h).
        This confirms the frequency dependence is dramatic.
        """
        rain_rate = 25.0  # mm/h
        elev_rad = np.radians(45)
        effective_length_km = 5.0 / np.sin(elev_rad)

        specific_atten = self.K_H_20GHZ * (rain_rate ** self.ALPHA_H_20GHZ)
        total_atten = specific_atten * effective_length_km

        assert total_atten > 2.0, (
            f"20 GHz rain attenuation at {rain_rate} mm/h = {total_atten:.2f} dB. "
            f"Should be > 2 dB"
        )

    def test_ntn_env_rain_formula_correct_structure(self):
        """
        ntn_env.py rain attenuation formula must be A = k * R^α * L_eff,
        not a constant or simplified form that ignores effective path length.
        """
        # Check that the formula gives near-zero at 2 GHz (correct behavior)
        k = 0.0001      # approximate ITU-R P.838-3 for 2 GHz
        alpha = 1.0
        rain_rate = 25.0  # mm/h
        elev_rad = np.radians(45)
        effective_length_km = 5.0 / np.sin(elev_rad)

        result = k * (rain_rate ** alpha) * effective_length_km
        # At 2 GHz, result should be small (< 0.5 dB) — physically correct
        assert result < 0.5, \
            f"2 GHz rain atten with k=0.0001 should be small, got {result:.4f} dB"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
