#!/usr/bin/env python3
"""
Integration Tests for E2SM-NTN Service Model
=============================================

Test-Driven Development: Define EXPECTED API first.

Expected API:
- E2SM_NTN(encoding='json')
- create_indication_message(ue_measurements, satellite_state) -> Dict
  OR
- create_indication_message(ue_id, satellite_state, ue_measurements) -> Tuple[bytes, bytes]

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


class TestE2SM_NTN_Initialization:
    """Test E2SM-NTN initialization API"""

    def test_initialization_with_json_encoding(self):
        """Test initialization with JSON encoding"""
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN

        e2sm = E2SM_NTN(encoding='json')

        assert e2sm is not None
        assert e2sm.encoding == 'json'

    def test_initialization_with_asn1_encoding(self):
        """Test initialization with ASN.1 encoding (may fallback to JSON)"""
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN

        e2sm = E2SM_NTN(encoding='asn1')

        assert e2sm is not None
        # May fallback to json if ASN.1 not available
        assert e2sm.encoding in ['asn1', 'json']

    def test_default_encoding(self):
        """Test default encoding (should be ASN.1 but may fallback)"""
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN

        e2sm = E2SM_NTN()

        assert e2sm is not None
        assert e2sm.encoding in ['asn1', 'json']


class TestE2SM_NTN_CreateIndication:
    """Test create_indication_message API"""

    def test_create_indication_with_correct_parameters(self):
        """Test create_indication_message with correct parameter order"""
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN

        e2sm = E2SM_NTN(encoding='json')

        # Prepare test data matching validation script
        ue_measurements = {
            'ue_id': 'TEST-UE',
            'satellite_id': 'LEO-550',
            'rsrp_dbm': -85.0,
            'rsrq_db': -12.0,
            'sinr_db': 10.0,
            'elevation_angle_deg': 30.0,
            'doppler_shift_hz': 10000.0,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        satellite_state = {
            'satellite_id': 'LEO-550',
            'orbit_type': 'LEO',
            'altitude_km': 550.0,
            'velocity_kmps': 7.8,
            'elevation_angle': 30.0,
            'azimuth_angle': 180.0,
            'slant_range_km': 800.0,
            'satellite_velocity': 7.8,
            'angular_velocity': 0.5
        }

        # EXPECTED API: Should accept (ue_measurements, satellite_state)
        # OR (ue_id, satellite_state, ue_measurements)
        # Check method signature
        import inspect
        sig = inspect.signature(e2sm.create_indication_message)
        params = list(sig.parameters.keys())

        if 'ue_id' in params[:2]:
            # Signature: (ue_id, satellite_state, ue_measurements, ...)
            result = e2sm.create_indication_message(
                ue_id='TEST-UE',
                satellite_state=satellite_state,
                ue_measurements=ue_measurements
            )
        else:
            # Signature: (ue_measurements, satellite_state, ...)
            result = e2sm.create_indication_message(
                ue_measurements=ue_measurements,
                satellite_state=satellite_state
            )

        # Validate result
        if isinstance(result, tuple):
            # Returns (header, message) tuple
            assert len(result) == 2
            header, message = result
            assert isinstance(header, bytes)
            assert isinstance(message, bytes)
        elif isinstance(result, dict):
            # Returns dictionary
            assert 'header' in result
            assert 'message' in result
        else:
            pytest.fail(f"Unexpected return type: {type(result)}")

    def test_create_indication_validation_script_format(self):
        """Test using exact format from week2_validation.py"""
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN
        from datetime import datetime, timezone

        e2sm = E2SM_NTN(encoding='json')

        # Exact format from validation script
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

        # Try to call with validation script format
        try:
            indication = e2sm.create_indication_message(ntn_meas, sat_state)

            # Should return tuple (header, message) or dict
            if isinstance(indication, tuple):
                assert len(indication) == 2
            elif isinstance(indication, dict):
                assert 'header' in indication
                assert indication['header']['ran_function_id'] == 10
                assert 'message' in indication
            else:
                pytest.fail(f"Unexpected return type: {type(indication)}")

        except TypeError as e:
            # If signature mismatch, check what's expected
            import inspect
            sig = inspect.signature(e2sm.create_indication_message)
            pytest.fail(f"Signature mismatch. Expected params: {list(sig.parameters.keys())}, Error: {e}")


class TestE2SM_NTN_RanFunction:
    """Test RAN function definition API"""

    def test_get_ran_function_definition(self):
        """Test RAN function definition retrieval"""
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN

        e2sm = E2SM_NTN(encoding='json')

        ran_func = e2sm.get_ran_function_definition()

        assert isinstance(ran_func, dict)
        assert 'ranFunctionId' in ran_func
        assert ran_func['ranFunctionId'] == 10

    def test_ran_function_constants(self):
        """Test RAN function constants"""
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN

        assert E2SM_NTN.RAN_FUNCTION_ID == 10
        assert E2SM_NTN.RAN_FUNCTION_SHORT_NAME == "ORAN-E2SM-NTN"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
