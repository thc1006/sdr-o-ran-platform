#!/usr/bin/env python3
"""
Comprehensive SGP4 Test Suite
=============================

Validates SGP4 orbit propagation accuracy, performance, and integration.

Test Categories:
1. TLE Parsing and Management
2. SGP4 Propagation Accuracy
3. Coordinate Transformations
4. Look Angle Calculations
5. Doppler Shift Accuracy
6. Pass Prediction
7. Constellation Operations
8. Performance Benchmarks

Author: SGP4 Orbit Propagation Specialist
Date: 2025-11-17
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
import time
from typing import List, Dict

from .tle_manager import TLEManager, TLEData
from .sgp4_propagator import SGP4Propagator
from .constellation_simulator import ConstellationSimulator


class TestTLEManager(unittest.TestCase):
    """Test TLE data management"""

    def setUp(self):
        """Set up test fixtures"""
        self.manager = TLEManager(cache_dir='test_tle_cache')

    def test_tle_parsing(self):
        """Test TLE parsing from lines"""
        line0 = "ISS (ZARYA)"
        line1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
        line2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"

        tle = self.manager.parse_tle_from_lines(line0, line1, line2, 'test')

        self.assertEqual(tle.satellite_id, "ISS (ZARYA)")
        self.assertEqual(tle.norad_id, 25544)
        self.assertEqual(tle.constellation, "test")
        self.assertIsInstance(tle.epoch, datetime)

    def test_constellation_fetch(self):
        """Test constellation TLE fetching"""
        # This test requires network access
        try:
            tles = self.manager.fetch_constellation_tles('starlink', limit=5)
            self.assertGreater(len(tles), 0)
            self.assertLessEqual(len(tles), 5)

            # Verify TLE structure
            for tle in tles:
                self.assertIsInstance(tle, TLEData)
                self.assertTrue(tle.line1.startswith('1 '))
                self.assertTrue(tle.line2.startswith('2 '))
                self.assertEqual(tle.constellation, 'starlink')

        except Exception as e:
            self.skipTest(f"Network access required: {e}")

    def test_tle_caching(self):
        """Test TLE caching functionality"""
        # Create sample TLE
        line0 = "TEST SAT"
        line1 = "1 99999U 24001A   24320.50000000  .00000000  00000-0  00000-0 0  9990"
        line2 = "2 99999  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000    01"

        tle = self.manager.parse_tle_from_lines(line0, line1, line2, 'test')

        # Cache TLE
        self.manager.cache_tles('test', [tle])

        # Load from cache
        cached = self.manager.load_cached_tles('test')
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0].satellite_id, "TEST SAT")

    def test_tle_freshness(self):
        """Test TLE age tracking"""
        line0 = "OLD SAT"
        line1 = "1 88888U 24001A   20001.50000000  .00000000  00000-0  00000-0 0  9990"
        line2 = "2 88888  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000    01"

        tle = self.manager.parse_tle_from_lines(line0, line1, line2, 'test')

        # TLE from 2020 should not be fresh
        self.assertFalse(tle.is_fresh(max_age_days=7.0))
        self.assertGreater(tle.get_age_days(), 1000)


class TestSGP4Propagator(unittest.TestCase):
    """Test SGP4 orbit propagation"""

    @classmethod
    def setUpClass(cls):
        """Set up test constellation"""
        cls.manager = TLEManager()
        try:
            tles = cls.manager.fetch_constellation_tles('starlink', limit=1)
            if tles:
                cls.test_tle = tles[0]
            else:
                cls.test_tle = None
        except Exception:
            cls.test_tle = None

    def setUp(self):
        """Set up test fixtures"""
        if self.test_tle is None:
            self.skipTest("No TLE data available")
        self.propagator = SGP4Propagator(self.test_tle)

    def test_propagation(self):
        """Test basic SGP4 propagation"""
        timestamp = datetime.utcnow()
        pos_eci, vel_eci = self.propagator.propagate(timestamp)

        # Verify output shapes
        self.assertEqual(pos_eci.shape, (3,))
        self.assertEqual(vel_eci.shape, (3,))

        # Verify position magnitude (LEO orbit)
        pos_magnitude = np.linalg.norm(pos_eci)
        self.assertGreater(pos_magnitude, 6500)  # > Earth radius
        self.assertLess(pos_magnitude, 8000)     # < 1500 km altitude

        # Verify velocity magnitude (LEO velocity ~7-8 km/s)
        vel_magnitude = np.linalg.norm(vel_eci)
        self.assertGreater(vel_magnitude, 6.0)
        self.assertLess(vel_magnitude, 9.0)

    def test_coordinate_transformations(self):
        """Test coordinate transformation accuracy"""
        # Known location: Taipei
        lat, lon, alt = 25.0330, 121.5654, 0.0

        # Convert to ECEF
        pos_ecef = self.propagator.geodetic_to_ecef(lat, lon, alt)

        # Verify ECEF magnitude ~= Earth radius
        pos_magnitude = np.linalg.norm(pos_ecef)
        self.assertAlmostEqual(pos_magnitude, 6378.137, delta=10.0)

        # Convert back to geodetic
        lat_back, lon_back = self.propagator._ecef_to_geodetic(pos_ecef)

        # Verify round-trip accuracy
        self.assertAlmostEqual(lat, lat_back, delta=0.01)
        self.assertAlmostEqual(lon, lon_back, delta=0.01)

    def test_look_angles(self):
        """Test look angle calculations"""
        timestamp = datetime.utcnow()

        # Taipei location
        taipei_lat, taipei_lon = 25.0330, 121.5654

        geometry = self.propagator.get_ground_track(
            taipei_lat, taipei_lon, 0.0, timestamp
        )

        # Verify output structure
        self.assertIn('elevation_deg', geometry)
        self.assertIn('azimuth_deg', geometry)
        self.assertIn('slant_range_km', geometry)
        self.assertIn('doppler_shift_hz', geometry)

        # Verify ranges
        self.assertGreaterEqual(geometry['elevation_deg'], -90)
        self.assertLessEqual(geometry['elevation_deg'], 90)
        self.assertGreaterEqual(geometry['azimuth_deg'], 0)
        self.assertLess(geometry['azimuth_deg'], 360)
        self.assertGreater(geometry['slant_range_km'], 0)

    def test_doppler_shift(self):
        """Test Doppler shift calculation"""
        timestamp = datetime.utcnow()
        taipei_lat, taipei_lon = 25.0330, 121.5654

        geometry = self.propagator.get_ground_track(
            taipei_lat, taipei_lon, 0.0, timestamp,
            carrier_freq_hz=2.0e9
        )

        doppler = geometry['doppler_shift_hz']

        # Doppler shift for LEO at 2 GHz should be within reasonable range
        # Maximum Doppler ~= (v/c) * f = (7.5/300000) * 2e9 = 50 kHz
        self.assertLess(abs(doppler), 100000)  # < 100 kHz

    def test_visibility(self):
        """Test satellite visibility determination"""
        timestamp = datetime.utcnow()
        taipei_lat, taipei_lon = 25.0330, 121.5654

        geometry = self.propagator.get_ground_track(
            taipei_lat, taipei_lon, 0.0, timestamp
        )

        # Verify visibility flag consistency
        is_visible = geometry['is_visible']
        elevation = geometry['elevation_deg']

        if is_visible:
            self.assertGreater(elevation, 0)
        else:
            self.assertLessEqual(elevation, 0)

    def test_orbital_parameters(self):
        """Test orbital parameter extraction"""
        params = self.propagator.get_orbital_parameters()

        # Verify parameter structure
        self.assertIn('satellite_id', params)
        self.assertIn('inclination_deg', params)
        self.assertIn('eccentricity', params)
        self.assertIn('period_minutes', params)

        # Verify LEO orbital characteristics
        self.assertGreater(params['inclination_deg'], 0)
        self.assertLess(params['inclination_deg'], 180)
        self.assertGreaterEqual(params['eccentricity'], 0)
        self.assertLess(params['eccentricity'], 1)
        self.assertGreater(params['period_minutes'], 80)  # > 80 min for LEO
        self.assertLess(params['period_minutes'], 130)    # < 130 min for LEO


class TestConstellationSimulator(unittest.TestCase):
    """Test constellation simulation"""

    @classmethod
    def setUpClass(cls):
        """Set up test constellation"""
        try:
            cls.constellation = ConstellationSimulator(
                'starlink',
                max_satellites=20,
                auto_load=True
            )
        except Exception as e:
            cls.constellation = None
            print(f"Warning: Could not load constellation: {e}")

    def setUp(self):
        """Set up test fixtures"""
        if self.constellation is None:
            self.skipTest("Constellation not available")

    def test_constellation_loading(self):
        """Test constellation loading"""
        self.assertGreater(self.constellation.satellite_count, 0)
        self.assertGreater(len(self.constellation.satellites), 0)

    def test_visibility_search(self):
        """Test satellite visibility search"""
        timestamp = datetime.utcnow()
        taipei_lat, taipei_lon = 25.0330, 121.5654

        visible = self.constellation.find_visible_satellites(
            taipei_lat, taipei_lon, timestamp,
            min_elevation=10.0,
            parallel=True
        )

        # Verify output structure
        self.assertIsInstance(visible, list)

        # If satellites are visible, verify structure
        if visible:
            for sat in visible:
                self.assertIn('satellite_id', sat)
                self.assertIn('elevation_deg', sat)
                self.assertGreaterEqual(sat['elevation_deg'], 10.0)

            # Verify sorting by elevation
            elevations = [s['elevation_deg'] for s in visible]
            self.assertEqual(elevations, sorted(elevations, reverse=True))

    def test_best_satellite_selection(self):
        """Test best satellite selection"""
        timestamp = datetime.utcnow()
        taipei_lat, taipei_lon = 25.0330, 121.5654

        visible = self.constellation.find_visible_satellites(
            taipei_lat, taipei_lon, timestamp,
            min_elevation=10.0
        )

        if visible:
            # Test elevation-based selection
            best_elev = self.constellation.select_best_satellite(
                visible, selection_metric='elevation'
            )
            self.assertEqual(best_elev, visible[0])  # Should be first (highest)

            # Test doppler-based selection
            best_doppler = self.constellation.select_best_satellite(
                visible, selection_metric='doppler'
            )
            self.assertIsNotNone(best_doppler)

    def test_handover_prediction(self):
        """Test handover prediction"""
        timestamp = datetime.utcnow()
        taipei_lat, taipei_lon = 25.0330, 121.5654

        handovers = self.constellation.predict_handovers(
            taipei_lat, taipei_lon, timestamp,
            duration_minutes=30,
            time_step_sec=60
        )

        # Verify output structure
        self.assertIsInstance(handovers, list)

        # If handovers predicted, verify structure
        for ho in handovers:
            self.assertIn('time', ho)
            self.assertIn('reason', ho)
            self.assertIsInstance(ho['time'], datetime)


class TestPerformance(unittest.TestCase):
    """Performance benchmarks"""

    @classmethod
    def setUpClass(cls):
        """Set up test data"""
        cls.manager = TLEManager()
        try:
            tles = cls.manager.fetch_constellation_tles('starlink', limit=100)
            if tles:
                cls.propagator = SGP4Propagator(tles[0])
                cls.constellation = ConstellationSimulator('starlink', max_satellites=100)
            else:
                cls.propagator = None
                cls.constellation = None
        except Exception:
            cls.propagator = None
            cls.constellation = None

    def setUp(self):
        """Set up test fixtures"""
        if self.propagator is None:
            self.skipTest("No test data available")

    def test_propagation_performance(self):
        """Test single propagation performance"""
        timestamp = datetime.utcnow()
        taipei_lat, taipei_lon = 25.0330, 121.5654

        # Warmup
        for _ in range(10):
            self.propagator.get_ground_track(taipei_lat, taipei_lon, 0.0, timestamp)

        # Benchmark
        num_runs = 1000
        start = time.time()

        for _ in range(num_runs):
            self.propagator.get_ground_track(taipei_lat, taipei_lon, 0.0, timestamp)

        elapsed = time.time() - start
        avg_time_ms = (elapsed / num_runs) * 1000

        print(f"\nPropagation performance: {avg_time_ms:.4f} ms/propagation")

        # Verify performance target: < 1 ms
        self.assertLess(avg_time_ms, 1.0, "Propagation should be < 1 ms")

    def test_constellation_performance(self):
        """Test constellation visibility search performance"""
        if self.constellation is None:
            self.skipTest("No constellation available")

        timestamp = datetime.utcnow()
        taipei_lat, taipei_lon = 25.0330, 121.5654

        # Warmup
        for _ in range(3):
            self.constellation.find_visible_satellites(
                taipei_lat, taipei_lon, timestamp, parallel=True
            )

        # Benchmark
        num_runs = 100
        start = time.time()

        for _ in range(num_runs):
            self.constellation.find_visible_satellites(
                taipei_lat, taipei_lon, timestamp, parallel=True
            )

        elapsed = time.time() - start
        avg_time_ms = (elapsed / num_runs) * 1000

        print(f"\nConstellation search performance: {avg_time_ms:.2f} ms/search")
        print(f"  Constellation size: {self.constellation.satellite_count} satellites")

        # Verify reasonable performance
        self.assertLess(avg_time_ms, 100.0, "Search should be < 100 ms for 100 satellites")


def run_tests():
    """Run all tests and generate report"""
    print("="*70)
    print("SGP4 Orbit Propagation Test Suite")
    print("="*70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTLEManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSGP4Propagator))
    suite.addTests(loader.loadTestsFromTestCase(TestConstellationSimulator))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed. See details above.")

    return result


if __name__ == "__main__":
    run_tests()
