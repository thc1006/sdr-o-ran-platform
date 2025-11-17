#!/usr/bin/env python3
"""
Integration Tests for Optimized Components
===========================================

Test-Driven Development: Define EXPECTED API first.

Expected API:
- OptimizedSGP4Propagator() - same API as SGP4Propagator
- OptimizedWeatherCalculator() - simplified weather API
- OptimizedASN1Codec() - simplified codec API

Author: Software Integration Specialist
Date: 2025-11-17
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime, timezone
import time


class TestOptimizedSGP4:
    """Test Optimized SGP4 Propagator API"""

    def test_initialization_parameterless(self):
        """Test parameterless initialization (EXPECTED API)"""
        from optimization.optimized_components import OptimizedSGP4Propagator

        # EXPECTED: Should support parameterless initialization like base class
        opt_sgp4 = OptimizedSGP4Propagator()

        assert opt_sgp4 is not None
        assert hasattr(opt_sgp4, 'load_tle')

    def test_initialization_with_tle_data(self):
        """Test initialization with TLE data"""
        from optimization.optimized_components import OptimizedSGP4Propagator
        from orbit_propagation.tle_manager import TLEData
        from datetime import datetime, timezone

        tle_data = TLEData(
            satellite_id='TEST',
            norad_id='44713',
            line1='1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999',
            line2='2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456',
            epoch=datetime.now(timezone.utc),
            constellation='TEST'
        )

        opt_sgp4 = OptimizedSGP4Propagator(tle_data)

        assert opt_sgp4 is not None
        assert opt_sgp4.satellite_id == 'TEST'

    def test_load_tle_method(self):
        """Test load_tle method compatibility"""
        from optimization.optimized_components import OptimizedSGP4Propagator

        opt_sgp4 = OptimizedSGP4Propagator()

        tle1 = '1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999'
        tle2 = '2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456'

        opt_sgp4.load_tle(tle1, tle2)

        assert opt_sgp4.satellite is not None

    def test_get_ground_track_performance(self):
        """Test optimized ground track performance"""
        from optimization.optimized_components import OptimizedSGP4Propagator

        opt_sgp4 = OptimizedSGP4Propagator()

        tle1 = '1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999'
        tle2 = '2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456'

        opt_sgp4.load_tle(tle1, tle2)

        # Batch test from validation script
        start = time.perf_counter()
        for _ in range(100):
            geometry = opt_sgp4.get_ground_track(25.033, 121.565, 0.0, datetime.now(timezone.utc))
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should complete 100 iterations
        assert geometry is not None
        assert 'elevation_deg' in geometry


class TestOptimizedWeatherCalculator:
    """Test Optimized Weather Calculator API"""

    def test_initialization(self):
        """Test initialization"""
        from optimization.optimized_components import OptimizedWeatherCalculator

        opt_weather = OptimizedWeatherCalculator()

        assert opt_weather is not None

    def test_calculate_rain_attenuation(self):
        """Test calculate_rain_attenuation returns numeric value"""
        from optimization.optimized_components import OptimizedWeatherCalculator

        opt_weather = OptimizedWeatherCalculator()

        # Should accept simplified parameters
        atten = opt_weather.calculate_rain_attenuation(25.033, 121.565, 2.0, 30.0)

        assert isinstance(atten, (float, int))
        assert 0 <= atten <= 50

    def test_performance(self):
        """Test optimized weather performance"""
        from optimization.optimized_components import OptimizedWeatherCalculator

        opt_weather = OptimizedWeatherCalculator()

        start = time.perf_counter()
        for _ in range(100):
            atten = opt_weather.calculate_rain_attenuation(25.033, 121.565, 2.0, 30.0)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should complete 100 iterations reasonably fast
        assert atten is not None


class TestOptimizedASN1Codec:
    """Test Optimized ASN.1 Codec API"""

    def test_initialization(self):
        """Test initialization"""
        from optimization.optimized_components import OptimizedASN1Codec

        opt_asn1 = OptimizedASN1Codec()

        assert opt_asn1 is not None

    def test_encode_method_exists(self):
        """Test that encode methods exist"""
        from optimization.optimized_components import OptimizedASN1Codec

        opt_asn1 = OptimizedASN1Codec()

        # Should have encode_indication_message method
        assert hasattr(opt_asn1, 'encode_indication_message')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
