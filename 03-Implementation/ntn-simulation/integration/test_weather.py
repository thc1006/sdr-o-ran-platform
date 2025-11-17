#!/usr/bin/env python3
"""
Integration Tests for ITU-R P.618 Weather Integration
======================================================

Test-Driven Development: Define EXPECTED API first.

Expected API:
- ITUR_P618_RainAttenuation()
- calculate_rain_attenuation(...) -> float (NOT RainAttenuationResult object)

The validation script expects a float/numeric value, not a custom object.

Author: Software Integration Specialist
Date: 2025-11-17
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import time


class TestWeatherInitialization:
    """Test ITU-R P.618 weather model initialization"""

    def test_initialization(self):
        """Test basic initialization"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        assert weather is not None


class TestRainAttenuationCalculation:
    """Test rain attenuation calculation API"""

    def test_calculate_rain_attenuation_returns_numeric(self):
        """Test that calculate_rain_attenuation returns a numeric value (EXPECTED API)"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        # Call with parameters from validation script
        result = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=2.0,
            elevation_angle=30.0
        )

        # EXPECTED: Should return a numeric value (float or int)
        # NOT a RainAttenuationResult object
        assert isinstance(result, (float, int)), \
            f"Expected numeric type, got {type(result)}"

        # Should be comparable with numbers
        assert 0 <= result <= 50, f"Attenuation {result} dB out of range"

    def test_calculate_rain_attenuation_validation_format(self):
        """Test using exact format from week2_validation.py"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        # Exact call from validation script
        atten = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=2.0,
            elevation_angle=30.0
        )

        # Validation script uses: assert 0 <= atten <= 50
        # This requires atten to be numeric, not an object
        assert 0 <= atten <= 50, "Attenuation out of range"

    def test_calculation_performance(self):
        """Test that calculation is fast enough (< 10ms)"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        start = time.perf_counter()
        atten = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=2.0,
            elevation_angle=30.0
        )
        calc_time_ms = (time.perf_counter() - start) * 1000

        assert calc_time_ms < 10, f"Calculation too slow: {calc_time_ms:.3f} ms"
        assert isinstance(atten, (float, int))


class TestRainAttenuationValueRanges:
    """Test rain attenuation value ranges"""

    def test_low_frequency_low_attenuation(self):
        """Test that low frequency (2 GHz) has low attenuation"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        atten = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=2.0,  # S-band (low frequency)
            elevation_angle=60.0  # High elevation
        )

        # At 2 GHz, rain attenuation should be relatively low
        assert 0 <= atten <= 5, f"2 GHz attenuation {atten} dB too high"

    def test_high_frequency_higher_attenuation(self):
        """Test that high frequency has higher attenuation"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        atten_ka = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=20.0,  # Ka-band (high frequency)
            elevation_angle=30.0
        )

        atten_s = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=2.0,  # S-band
            elevation_angle=30.0
        )

        # Ka-band should have higher attenuation than S-band
        assert atten_ka > atten_s, \
            f"Ka-band ({atten_ka} dB) should have higher attenuation than S-band ({atten_s} dB)"

    def test_low_elevation_higher_attenuation(self):
        """Test that low elevation has higher attenuation"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        atten_low = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=10.0,
            elevation_angle=10.0  # Low elevation (longer path)
        )

        atten_high = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=10.0,
            elevation_angle=60.0  # High elevation (shorter path)
        )

        # Low elevation should have higher attenuation (longer path through rain)
        assert atten_low > atten_high, \
            f"Low elevation ({atten_low} dB) should have higher attenuation than high elevation ({atten_high} dB)"


class TestWeatherAPICompatibility:
    """Test compatibility with different return types"""

    def test_handle_both_float_and_object_return(self):
        """Test that we can handle both float and RainAttenuationResult returns"""
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        weather = ITUR_P618_RainAttenuation()

        result = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=2.0,
            elevation_angle=30.0
        )

        # If it returns an object, it should have exceeded_0_01_percent attribute
        if hasattr(result, 'exceeded_0_01_percent'):
            atten = result.exceeded_0_01_percent
            assert isinstance(atten, (float, int))
            assert 0 <= atten <= 50
        else:
            # Should be numeric
            assert isinstance(result, (float, int))
            assert 0 <= result <= 50


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
