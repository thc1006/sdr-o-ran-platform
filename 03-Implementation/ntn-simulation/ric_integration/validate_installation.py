#!/usr/bin/env python3
"""
Quick validation script for RIC integration installation
Tests basic functionality without full E2 connection
"""

import sys
import os

base_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'e2_ntn_extension'))

print("="*60)
print("RIC INTEGRATION VALIDATION")
print("="*60)

# Test 1: Import E2SM-NTN
print("\n[1] Testing E2SM-NTN import...")
try:
    from e2sm_ntn import E2SM_NTN, NTNControlMessage
    print("    ✓ E2SM-NTN imported successfully")
    print(f"    RAN Function ID: {E2SM_NTN.RAN_FUNCTION_ID}")
    print(f"    Version: {E2SM_NTN.VERSION}")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 2: Import E2AP Messages
print("\n[2] Testing E2AP message handlers...")
try:
    from ric_integration.e2ap_messages import (
        E2SetupRequest, E2SetupResponse,
        RICSubscriptionRequest, RICIndication,
        RICControlRequest, E2APMessageFactory
    )
    print("    ✓ E2AP messages imported successfully")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Import E2 Termination
print("\n[3] Testing E2 Termination Point...")
try:
    from ric_integration.e2_termination import E2TerminationPoint, E2ConnectionConfig
    print("    ✓ E2 Termination Point imported successfully")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 4: Import xApp Deployer
print("\n[4] Testing xApp Deployer...")
try:
    from ric_integration.xapp_deployer import XAppDeployer, XAppConfig
    print("    ✓ xApp Deployer imported successfully")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 5: Create E2SM-NTN instance
print("\n[5] Creating E2SM-NTN instance...")
try:
    e2sm = E2SM_NTN(encoding='json')
    print(f"    ✓ E2SM-NTN created (encoding: {e2sm.get_encoding_type()})")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 6: Test Indication Message Creation
print("\n[6] Testing indication message creation...")
try:
    ntn_metrics = {
        "ue_id": "UE-TEST-001",
        "satellite_state": {
            "satellite_id": "STARLINK-1234",
            "orbit_type": "LEO",
            "beam_id": 1,
            "elevation_angle": 45.0,
            "azimuth_angle": 180.0,
            "slant_range_km": 850.0,
            "satellite_velocity": 7.5,
            "angular_velocity": -0.5,
            "carrier_frequency_ghz": 2.1
        },
        "measurements": {
            "rsrp": -85.0,
            "rsrq": -12.0,
            "sinr": 15.0,
            "bler": 0.01,
            "tx_power_dbm": 23.0,
            "throughput_dl_mbps": 100.0,
            "throughput_ul_mbps": 20.0,
            "packet_loss_rate": 0.005
        }
    }

    header, message = e2sm.create_indication_message(
        ue_id=ntn_metrics["ue_id"],
        satellite_state=ntn_metrics["satellite_state"],
        ue_measurements=ntn_metrics["measurements"]
    )

    print(f"    ✓ Indication created (header: {len(header)} bytes, message: {len(message)} bytes)")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 7: Test E2AP Message Encoding
print("\n[7] Testing E2AP message encoding...")
try:
    from ric_integration.e2ap_messages import RANFunctionDefinition

    ran_func = RANFunctionDefinition(
        ran_function_id=E2SM_NTN.RAN_FUNCTION_ID,
        ran_function_revision=1,
        ran_function_oid=E2SM_NTN.RAN_FUNCTION_OID,
        ran_function_description=e2sm.get_ran_function_definition()
    )

    setup_req = E2SetupRequest(
        global_e2_node_id="TEST-NODE-001",
        ran_functions=[ran_func]
    )

    encoded = setup_req.encode()
    print(f"    ✓ E2 Setup Request encoded ({len(encoded)} bytes)")

    # Decode it back
    decoded = E2SetupRequest.decode(encoded)
    print(f"    ✓ E2 Setup Request decoded (node: {decoded.global_e2_node_id})")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 8: Check SCTP Support
print("\n[8] Checking SCTP support...")
try:
    import socket
    if hasattr(socket, 'IPPROTO_SCTP'):
        print("    ✓ SCTP protocol available")
    else:
        print("    ⚠ SCTP not available (will use TCP fallback)")
except Exception as e:
    print(f"    ✗ Failed: {e}")

# Test 9: Check Prerequisites
print("\n[9] Checking prerequisites...")
try:
    import asyncio
    print("    ✓ asyncio available")
    import json
    print("    ✓ json available")
    import numpy
    print("    ✓ numpy available")
except Exception as e:
    print(f"    ⚠ Some prerequisites missing: {e}")

print("\n" + "="*60)
print("VALIDATION COMPLETE")
print("="*60)
print("\n✓ All core components validated successfully!")
print("\nNext steps:")
print("  1. Deploy O-RAN SC RIC (optional) or use simulated RIC")
print("  2. Run integration test: python3 test_ric_integration.py")
print("  3. Run benchmarks: python3 benchmark_ric.py")
print("  4. See RIC-INTEGRATION-GUIDE.md for full documentation")
print("="*60)
