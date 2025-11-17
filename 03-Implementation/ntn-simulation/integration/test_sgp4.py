#!/usr/bin/env python3
"""
Integration Tests for SGP4 Orbit Propagator
============================================

Test-Driven Development: Define EXPECTED API first.

Expected API:
- SGP4Propagator() - parameterless initialization
- load_tle(tle1, tle2) - load TLE data after initialization
- get_ground_track(user_lat, user_lon, user_alt, timestamp) -> Dict

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


class TestSGP4Initialization:
    """Test SGP4 propagator initialization API"""

    def test_parameterless_initialization(self):
        """Test initialization without parameters (EXPECTED API)"""
        from orbit_propagation.sgp4_propagator import SGP4Propagator

        # EXPECTED: Should support parameterless initialization
        sgp4 = SGP4Propagator()

        assert sgp4 is not None
        # Should have load_tle method
        assert hasattr(sgp4, 'load_tle')

    def test_initialization_with_tle_data(self):
        """Test initialization with TLE data object"""
        from orbit_propagation.sgp4_propagator import SGP4Propagator
        from orbit_propagation.tle_manager import TLEData
        from datetime import datetime

        # Create TLE data
        tle_data = TLEData(
            satellite_id='STARLINK-TEST',
            norad_id='44713',
            line1='1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999',
            line2='2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456',
            epoch=datetime.now(timezone.utc),
            constellation='STARLINK'
        )

        sgp4 = SGP4Propagator(tle_data)

        assert sgp4 is not None
        assert sgp4.satellite_id == 'STARLINK-TEST'


class TestSGP4LoadTLE:
    """Test load_tle method API"""

    def test_load_tle_from_strings(self):
        """Test loading TLE from string lines"""
        from orbit_propagation.sgp4_propagator import SGP4Propagator

        sgp4 = SGP4Propagator()

        # Sample TLE
        tle1 = '1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999'
        tle2 = '2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456'

        # EXPECTED: Should have load_tle method
        sgp4.load_tle(tle1, tle2)

        assert sgp4.satellite is not None
        # Verify TLE was loaded correctly
        assert sgp4.satellite.error == 0


class TestSGP4GroundTrack:
    """Test get_ground_track method API"""

    def test_get_ground_track_basic(self):
        """Test basic ground track calculation"""
        from orbit_propagation.sgp4_propagator import SGP4Propagator
        from datetime import datetime, timezone

        sgp4 = SGP4Propagator()

        tle1 = '1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999'
        tle2 = '2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456'

        sgp4.load_tle(tle1, tle2)

        # Get ground track for Taipei
        geometry = sgp4.get_ground_track(
            user_lat=25.033,
            user_lon=121.565,
            user_alt=0.0,
            timestamp=datetime.now(timezone.utc)
        )

        assert isinstance(geometry, dict)
        assert 'elevation_deg' in geometry
        assert 'azimuth_deg' in geometry
        assert 'slant_range_km' in geometry
        assert 'doppler_shift_hz' in geometry

    def test_get_ground_track_validation_format(self):
        """Test using exact format from week2_validation.py"""
        from orbit_propagation.sgp4_propagator import SGP4Propagator
        from datetime import datetime, timezone

        sgp4 = SGP4Propagator()

        tle1 = '1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999'
        tle2 = '2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456'

        sgp4.load_tle(tle1, tle2)

        # Exact call from validation script
        geometry = sgp4.get_ground_track(
            user_lat=25.033,
            user_lon=121.565,
            timestamp=datetime.now(timezone.utc)
        )

        assert 'elevation_deg' in geometry
        assert 'azimuth_deg' in geometry
        assert 'slant_range_km' in geometry
        assert 0 <= geometry['azimuth_deg'] <= 360

    def test_ground_track_output_ranges(self):
        """Test ground track output value ranges"""
        from orbit_propagation.sgp4_propagator import SGP4Propagator
        from datetime import datetime, timezone

        sgp4 = SGP4Propagator()

        tle1 = '1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999'
        tle2 = '2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456'

        sgp4.load_tle(tle1, tle2)

        geometry = sgp4.get_ground_track(25.033, 121.565, 0.0, datetime.now(timezone.utc))

        # Validate ranges
        assert -90 <= geometry['elevation_deg'] <= 90
        assert 0 <= geometry['azimuth_deg'] <= 360
        assert geometry['slant_range_km'] > 0
        # LEO Doppler should be reasonable
        assert abs(geometry['doppler_shift_hz']) < 100000  # < 100 kHz


class TestSGP4Propagation:
    """Test low-level propagation methods"""

    def test_propagate_method(self):
        """Test propagate method returns position and velocity"""
        from orbit_propagation.sgp4_propagator import SGP4Propagator
        from orbit_propagation.tle_manager import TLEData
        from datetime import datetime, timezone
        import numpy as np

        tle_data = TLEData(
            satellite_id='TEST',
            norad_id='44713',
            line1='1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999',
            line2='2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456',
            epoch=datetime.now(timezone.utc),
            constellation='TEST'
        )

        sgp4 = SGP4Propagator(tle_data)

        pos_eci, vel_eci = sgp4.propagate(datetime.now(timezone.utc))

        assert isinstance(pos_eci, np.ndarray)
        assert isinstance(vel_eci, np.ndarray)
        assert pos_eci.shape == (3,)
        assert vel_eci.shape == (3,)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
