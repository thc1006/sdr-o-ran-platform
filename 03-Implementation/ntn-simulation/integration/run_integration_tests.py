#!/usr/bin/env python3
"""
Integration Test Runner (without pytest dependency)
====================================================

Runs all integration tests and reports API mismatches.

Author: Software Integration Specialist
Date: 2025-11-17
"""

import sys
import os
from pathlib import Path
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = []
        self.failed = []
        self.errors = []

    def add_pass(self, test_name):
        self.passed.append(test_name)

    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))

    def add_error(self, test_name, error):
        self.errors.append((test_name, error))


def run_test_class(test_class, result):
    """Run all test methods in a class"""
    instance = test_class()

    for attr_name in dir(instance):
        if attr_name.startswith('test_'):
            test_name = f"{test_class.__name__}.{attr_name}"
            try:
                method = getattr(instance, attr_name)
                method()
                result.add_pass(test_name)
                print(f"  {GREEN}✓{RESET} {test_name}")
            except AssertionError as e:
                result.add_fail(test_name, str(e))
                print(f"  {RED}✗{RESET} {test_name}")
                print(f"    {YELLOW}AssertionError: {e}{RESET}")
            except Exception as e:
                result.add_error(test_name, str(e))
                print(f"  {RED}✗{RESET} {test_name}")
                print(f"    {RED}Error: {e}{RESET}")
                # Print abbreviated traceback
                exc_type, exc_value, exc_tb = sys.exc_info()
                tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
                # Print just the relevant part
                for line in tb_lines[-3:]:
                    print(f"    {line.strip()}")


def test_channel_models():
    """Test OpenNTN Channel Models"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing: OpenNTN Channel Models{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    result = TestResult("Channel Models")

    try:
        from openNTN_integration import LEOChannelModel

        print(f"\n{YELLOW}Test: LEO Channel Model{RESET}")

        # Test 1: Initialization
        print(f"  Testing initialization...")
        leo = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550,
            scenario='urban'
        )
        print(f"  {GREEN}✓{RESET} Initialization successful")

        # Test 2: Link budget without rain_rate
        print(f"  Testing calculate_link_budget without rain_rate...")
        try:
            budget = leo.calculate_link_budget(elevation_angle=30.0)
            print(f"  {GREEN}✓{RESET} Works without rain_rate parameter")
        except TypeError as e:
            print(f"  {YELLOW}⚠{RESET} Needs rain_rate parameter: {e}")

        # Test 3: Link budget WITH rain_rate (EXPECTED API)
        print(f"  Testing calculate_link_budget WITH rain_rate...")
        try:
            budget = leo.calculate_link_budget(elevation_angle=30.0, rain_rate=0.0)
            print(f"  {GREEN}✓{RESET} API MISMATCH: Should accept rain_rate=0.0")
            result.add_pass("LEO.calculate_link_budget with rain_rate")
        except TypeError as e:
            print(f"  {RED}✗{RESET} API MISMATCH: calculate_link_budget() got unexpected keyword argument 'rain_rate'")
            result.add_fail("LEO.calculate_link_budget with rain_rate", str(e))

        # Test 4: Return value format
        budget = leo.calculate_link_budget(elevation_angle=30.0)
        path_loss_key = 'path_loss_db' if 'path_loss_db' in budget else 'free_space_path_loss_db'
        print(f"  Path loss key in result: '{path_loss_key}'")
        print(f"  All keys: {list(budget.keys())}")

    except Exception as e:
        print(f"  {RED}✗{RESET} Failed to import or test channel models: {e}")
        result.add_error("Channel Models", str(e))
        traceback.print_exc()

    return result


def test_e2sm_ntn():
    """Test E2SM-NTN Service Model"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing: E2SM-NTN Service Model{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    result = TestResult("E2SM-NTN")

    try:
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN
        from datetime import datetime, timezone
        import inspect

        print(f"\n{YELLOW}Test: E2SM-NTN Initialization{RESET}")
        e2sm = E2SM_NTN(encoding='json')
        print(f"  {GREEN}✓{RESET} Initialization successful")
        print(f"  Encoding: {e2sm.encoding}")

        print(f"\n{YELLOW}Test: create_indication_message API{RESET}")

        # Check method signature
        sig = inspect.signature(e2sm.create_indication_message)
        params = list(sig.parameters.keys())
        print(f"  Method signature: {sig}")
        print(f"  Parameters: {params}")

        # Prepare test data
        ntn_meas = {
            'ue_id': 'TEST-UE',
            'satellite_id': 'LEO-550',
            'rsrp_dbm': -85.0,
            'elevation_angle_deg': 30.0,
            'doppler_shift_hz': 10000.0,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        sat_state = {
            'satellite_id': 'LEO-550',
            'orbit_type': 'LEO',
            'altitude_km': 550.0,
            'velocity_kmps': 7.8
        }

        # Test call format from validation script
        print(f"  Testing validation script format...")
        try:
            indication = e2sm.create_indication_message(ntn_meas, sat_state)
            print(f"  {GREEN}✓{RESET} Works with (ue_measurements, satellite_state) format")
            print(f"  Return type: {type(indication)}")
            result.add_pass("E2SM_NTN.create_indication_message")
        except TypeError as e:
            print(f"  {RED}✗{RESET} API MISMATCH: {e}")
            print(f"  Expected: create_indication_message(ue_measurements, satellite_state)")
            print(f"  Got signature: {sig}")
            result.add_fail("E2SM_NTN.create_indication_message", str(e))

    except Exception as e:
        print(f"  {RED}✗{RESET} Failed to test E2SM-NTN: {e}")
        result.add_error("E2SM-NTN", str(e))
        traceback.print_exc()

    return result


def test_sgp4():
    """Test SGP4 Propagator"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing: SGP4 Orbit Propagator{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    result = TestResult("SGP4")

    try:
        from orbit_propagation.sgp4_propagator import SGP4Propagator
        from datetime import datetime, timezone
        import inspect

        print(f"\n{YELLOW}Test: SGP4 Initialization{RESET}")

        # Check __init__ signature
        sig = inspect.signature(SGP4Propagator.__init__)
        params = list(sig.parameters.keys())
        print(f"  __init__ signature: {sig}")
        print(f"  Parameters: {params}")

        # Test parameterless initialization
        print(f"  Testing parameterless initialization...")
        try:
            sgp4 = SGP4Propagator()
            print(f"  {GREEN}✓{RESET} Parameterless initialization works")
            result.add_pass("SGP4.parameterless_init")
        except TypeError as e:
            print(f"  {RED}✗{RESET} API MISMATCH: {e}")
            print(f"  Expected: SGP4Propagator() with no required parameters")
            result.add_fail("SGP4.parameterless_init", str(e))
            return result  # Can't continue without instance

        # Test load_tle method
        print(f"\n{YELLOW}Test: load_tle method{RESET}")
        if hasattr(sgp4, 'load_tle'):
            print(f"  {GREEN}✓{RESET} load_tle method exists")

            tle1 = '1 44713U 19074A   23001.50000000  .00001234  00000-0  12345-3 0  9999'
            tle2 = '2 44713  53.0000 180.0000 0001000   0.0000  90.0000 15.19000000123456'

            sgp4.load_tle(tle1, tle2)
            print(f"  {GREEN}✓{RESET} load_tle executed successfully")
            result.add_pass("SGP4.load_tle")
        else:
            print(f"  {RED}✗{RESET} API MISMATCH: load_tle method not found")
            result.add_fail("SGP4.load_tle", "Method not found")

        # Test get_ground_track
        print(f"\n{YELLOW}Test: get_ground_track method{RESET}")
        geometry = sgp4.get_ground_track(25.033, 121.565, 0.0, datetime.now(timezone.utc))
        print(f"  {GREEN}✓{RESET} get_ground_track works")
        print(f"  Keys: {list(geometry.keys())}")
        result.add_pass("SGP4.get_ground_track")

    except Exception as e:
        print(f"  {RED}✗{RESET} Failed to test SGP4: {e}")
        result.add_error("SGP4", str(e))
        traceback.print_exc()

    return result


def test_weather():
    """Test Weather Integration"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing: ITU-R P.618 Weather Integration{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    result = TestResult("Weather")

    try:
        from weather.itur_p618 import ITUR_P618_RainAttenuation

        print(f"\n{YELLOW}Test: Weather Initialization{RESET}")
        weather = ITUR_P618_RainAttenuation()
        print(f"  {GREEN}✓{RESET} Initialization successful")

        print(f"\n{YELLOW}Test: calculate_rain_attenuation return type{RESET}")
        atten = weather.calculate_rain_attenuation(
            latitude=25.033,
            longitude=121.565,
            frequency_ghz=2.0,
            elevation_angle=30.0
        )

        print(f"  Return type: {type(atten)}")
        print(f"  Return value: {atten}")

        # Check if it's numeric
        if isinstance(atten, (float, int)):
            print(f"  {GREEN}✓{RESET} Returns numeric value (float/int)")
            result.add_pass("Weather.returns_numeric")

            # Test comparison
            try:
                if 0 <= atten <= 50:
                    print(f"  {GREEN}✓{RESET} Value is comparable and in range")
                    result.add_pass("Weather.numeric_comparison")
            except TypeError as e:
                print(f"  {RED}✗{RESET} Comparison failed: {e}")
                result.add_fail("Weather.numeric_comparison", str(e))
        else:
            print(f"  {RED}✗{RESET} API MISMATCH: Returns {type(atten)}, expected float/int")
            print(f"  Validation script expects: 0 <= atten <= 50")

            # Check if it has exceeded_0_01_percent attribute
            if hasattr(atten, 'exceeded_0_01_percent'):
                print(f"  Found RainAttenuationResult object with exceeded_0_01_percent = {atten.exceeded_0_01_percent}")

            result.add_fail("Weather.returns_numeric", f"Returns {type(atten)} instead of float")

    except Exception as e:
        print(f"  {RED}✗{RESET} Failed to test weather: {e}")
        result.add_error("Weather", str(e))
        traceback.print_exc()

    return result


def test_asn1_module():
    """Test ASN.1 Module Structure"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing: ASN.1 Module Structure{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    result = TestResult("ASN.1")

    try:
        print(f"\n{YELLOW}Test: Import from e2_ntn_extension.asn1.asn1_codec{RESET}")
        try:
            from e2_ntn_extension.asn1.asn1_codec import E2SM_NTN_ASN1_Codec
            print(f"  {GREEN}✓{RESET} Import successful")
            result.add_pass("ASN1.import_path")
        except ImportError as e:
            print(f"  {RED}✗{RESET} API MISMATCH: {e}")
            print(f"  Expected: from e2_ntn_extension.asn1.asn1_codec import E2SM_NTN_ASN1_Codec")

            # Check if asn1 __init__.py exists
            asn1_init = Path(__file__).parent.parent / 'e2_ntn_extension' / 'asn1' / '__init__.py'
            print(f"  asn1/__init__.py exists: {asn1_init.exists()}")

            result.add_fail("ASN1.import_path", str(e))

    except Exception as e:
        print(f"  {RED}✗{RESET} Failed to test ASN.1: {e}")
        result.add_error("ASN.1", str(e))
        traceback.print_exc()

    return result


def test_optimizations():
    """Test Optimized Components"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing: Optimized Components{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    result = TestResult("Optimizations")

    try:
        from optimization.optimized_components import OptimizedSGP4Propagator
        import inspect

        print(f"\n{YELLOW}Test: OptimizedSGP4Propagator Initialization{RESET}")

        sig = inspect.signature(OptimizedSGP4Propagator.__init__)
        params = list(sig.parameters.keys())
        print(f"  __init__ signature: {sig}")

        try:
            opt_sgp4 = OptimizedSGP4Propagator()
            print(f"  {GREEN}✓{RESET} Parameterless initialization works")
            result.add_pass("OptimizedSGP4.parameterless_init")
        except TypeError as e:
            print(f"  {RED}✗{RESET} API MISMATCH: {e}")
            result.add_fail("OptimizedSGP4.parameterless_init", str(e))

    except Exception as e:
        print(f"  {RED}✗{RESET} Failed to test optimizations: {e}")
        result.add_error("Optimizations", str(e))
        traceback.print_exc()

    return result


def test_baseline():
    """Test Baseline Systems"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing: Baseline Systems{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    result = TestResult("Baseline")

    try:
        from baseline.reactive_system import ReactiveHandoverManager
        import inspect

        print(f"\n{YELLOW}Test: ReactiveHandoverManager Initialization{RESET}")

        sig = inspect.signature(ReactiveHandoverManager.__init__)
        params = list(sig.parameters.keys())
        print(f"  __init__ signature: {sig}")
        print(f"  Parameters: {params}")

        # Try with expected parameter name
        try:
            reactive = ReactiveHandoverManager(rsrp_threshold_dbm=-110.0)
            print(f"  {GREEN}✓{RESET} Initialization with rsrp_threshold_dbm works")
            result.add_pass("Reactive.rsrp_threshold_dbm")
        except TypeError as e:
            print(f"  {RED}✗{RESET} API MISMATCH: {e}")
            print(f"  Expected parameter: rsrp_threshold_dbm")
            print(f"  Available parameters: {params}")
            result.add_fail("Reactive.rsrp_threshold_dbm", str(e))

    except Exception as e:
        print(f"  {RED}✗{RESET} Failed to test baseline: {e}")
        result.add_error("Baseline", str(e))
        traceback.print_exc()

    return result


def print_summary(results):
    """Print test summary"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}API MISMATCH SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    total_passed = sum(len(r.passed) for r in results)
    total_failed = sum(len(r.failed) for r in results)
    total_errors = sum(len(r.errors) for r in results)
    total = total_passed + total_failed + total_errors

    for result in results:
        status = f"{GREEN}✓{RESET}" if not result.failed and not result.errors else f"{RED}✗{RESET}"
        print(f"\n{status} {result.name}:")
        print(f"  Passed: {len(result.passed)}")
        print(f"  Failed: {len(result.failed)}")
        print(f"  Errors: {len(result.errors)}")

        if result.failed:
            print(f"\n  {YELLOW}API Mismatches:{RESET}")
            for test_name, error in result.failed:
                print(f"    - {test_name}: {error}")

        if result.errors:
            print(f"\n  {RED}Errors:{RESET}")
            for test_name, error in result.errors:
                print(f"    - {test_name}: {error}")

    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TOTAL: {total_passed}/{total} tests passed ({total_passed/total*100:.1f}%){RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    return total_passed, total_failed, total_errors


def main():
    """Run all integration tests"""
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}NTN-O-RAN PLATFORM - API INTEGRATION TESTS{RESET}")
    print(f"{BLUE}Test-Driven Development: Identifying API Mismatches{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    results = []

    results.append(test_channel_models())
    results.append(test_e2sm_ntn())
    results.append(test_sgp4())
    results.append(test_weather())
    results.append(test_asn1_module())
    results.append(test_optimizations())
    results.append(test_baseline())

    passed, failed, errors = print_summary(results)

    if failed > 0 or errors > 0:
        print(f"\n{YELLOW}⚠ API MISMATCHES FOUND - Fixes required{RESET}")
        return 1
    else:
        print(f"\n{GREEN}✓ ALL APIS HARMONIZED{RESET}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
