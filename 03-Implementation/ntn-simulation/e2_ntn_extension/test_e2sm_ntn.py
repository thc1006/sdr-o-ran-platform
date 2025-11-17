#!/usr/bin/env python3
"""
E2SM-NTN Test Scenarios
Comprehensive testing of E2SM-NTN service model and NTN-E2 bridge

Test Scenarios:
1. UE at low elevation (10°) - poor link quality
2. UE at optimal elevation (60°) - good link quality
3. Handover prediction - elevation approaching minimum
4. Power control recommendation
5. Multi-satellite scenario
"""

import sys
import os
import json
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from e2sm_ntn import (
    E2SM_NTN, OrbitType, NTNEventTrigger, NTNControlAction,
    NTNIndicationMessage, LinkBudget
)
from ntn_e2_bridge import NTN_E2_Bridge, UEContext


class TestResults:
    """Test results collector"""

    def __init__(self):
        self.results = []
        self.start_time = time.time()

    def add_result(
        self,
        scenario: str,
        test_name: str,
        passed: bool,
        details: Dict[str, Any],
        metrics: Dict[str, Any] = None
    ):
        """Add test result"""
        result = {
            "scenario": scenario,
            "test_name": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "metrics": metrics or {}
        }
        self.results.append(result)

        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}")

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        duration = time.time() - self.start_time

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "N/A",
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.now().isoformat()
        }

    def save_to_file(self, filename: str):
        """Save results to JSON file"""
        output = {
            "summary": self.get_summary(),
            "results": self.results
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nResults saved to: {filename}")


def scenario_1_low_elevation(test_results: TestResults):
    """
    Scenario 1: UE at low elevation (10°) - poor link quality

    Tests:
    - Low elevation detection
    - High path loss calculation
    - Low link margin warning
    - Handover imminent prediction
    """
    print("\n=== Scenario 1: Low Elevation (10°) - Poor Link Quality ===")

    # Initialize bridge with LEO satellite
    bridge = NTN_E2_Bridge(orbit_type='LEO', carrier_frequency_ghz=2.1)

    # Register UE at equator
    ue_id = "UE-001"
    bridge.register_ue(ue_id, lat=0.0, lon=0.0, altitude_m=0.0)

    # Simulate measurements at low elevation
    # For 10° elevation with 600 km altitude LEO
    measurements = {
        "rsrp": -110.0,  # Very low RSRP
        "rsrq": -18.0,   # Poor quality
        "sinr": 3.0,     # Low SINR
        "bler": 0.15,    # High BLER
        "tx_power_dbm": 23.0,
        "throughput_dl_mbps": 5.0,  # Low throughput
        "throughput_ul_mbps": 1.0,
        "rain_attenuation_db": 0.0,
        "atmospheric_loss_db": 1.5
    }

    # Position satellite to create ~10° elevation
    # At equator, satellite needs to be far from UE longitude
    satellite_lon = 60.0  # Far from UE

    header, message = bridge.process_ue_report(
        ue_id=ue_id,
        measurements=measurements,
        satellite_lat=0.0,
        satellite_lon=satellite_lon
    )

    # Decode message
    message_data = json.loads(message.decode('utf-8'))

    # Test 1: Verify low elevation
    elevation = message_data["satellite_metrics"]["elevation_angle"]
    test_results.add_result(
        scenario="Scenario 1",
        test_name="Low elevation detected (< 15°)",
        passed=elevation < 15.0,
        details={"elevation_angle": elevation, "threshold": 15.0},
        metrics={"elevation_angle": elevation}
    )

    # Test 2: Verify high path loss
    path_loss = message_data["ntn_impairments"]["path_loss_db"]
    test_results.add_result(
        scenario="Scenario 1",
        test_name="High path loss at low elevation (> 170 dB)",
        passed=path_loss > 170.0,
        details={"path_loss_db": path_loss, "threshold": 170.0},
        metrics={"path_loss_db": path_loss}
    )

    # Test 3: Verify low link margin
    link_margin = message_data["link_budget"]["link_margin_db"]
    test_results.add_result(
        scenario="Scenario 1",
        test_name="Low link margin warning (< 5 dB)",
        passed=link_margin < 5.0,
        details={"link_margin_db": link_margin, "threshold": 5.0},
        metrics={"link_margin_db": link_margin}
    )

    # Test 4: Verify handover imminent
    time_to_handover = message_data["handover_prediction"]["time_to_handover_sec"]
    test_results.add_result(
        scenario="Scenario 1",
        test_name="Handover predicted for low elevation",
        passed=time_to_handover < 300.0,  # Within 5 minutes
        details={"time_to_handover_sec": time_to_handover},
        metrics={"time_to_handover_sec": time_to_handover}
    )

    # Test 5: Verify message format
    is_valid = bridge.e2sm_ntn.validate_indication_message(message)
    test_results.add_result(
        scenario="Scenario 1",
        test_name="E2 Indication message format valid",
        passed=is_valid,
        details={"message_valid": is_valid}
    )


def scenario_2_optimal_elevation(test_results: TestResults):
    """
    Scenario 2: UE at optimal elevation (60°) - good link quality

    Tests:
    - Optimal elevation detection
    - Low path loss
    - Good link margin
    - High throughput
    """
    print("\n=== Scenario 2: Optimal Elevation (60°) - Good Link Quality ===")

    bridge = NTN_E2_Bridge(orbit_type='LEO', carrier_frequency_ghz=2.1)

    ue_id = "UE-002"
    bridge.register_ue(ue_id, lat=0.0, lon=0.0, altitude_m=0.0)

    # Simulate measurements at optimal elevation
    measurements = {
        "rsrp": -75.0,   # Good RSRP
        "rsrq": -8.0,    # Good quality
        "sinr": 20.0,    # High SINR
        "bler": 0.001,   # Very low BLER
        "tx_power_dbm": 23.0,
        "throughput_dl_mbps": 100.0,  # High throughput
        "throughput_ul_mbps": 50.0,
        "rain_attenuation_db": 0.0,
        "atmospheric_loss_db": 0.3
    }

    # Position satellite directly above UE for high elevation
    satellite_lon = 0.0  # Same as UE
    satellite_lat = 0.0

    header, message = bridge.process_ue_report(
        ue_id=ue_id,
        measurements=measurements,
        satellite_lat=satellite_lat,
        satellite_lon=satellite_lon
    )

    message_data = json.loads(message.decode('utf-8'))

    # Test 1: Verify optimal elevation
    elevation = message_data["satellite_metrics"]["elevation_angle"]
    test_results.add_result(
        scenario="Scenario 2",
        test_name="Optimal elevation detected (> 45°)",
        passed=elevation > 45.0,
        details={"elevation_angle": elevation, "threshold": 45.0},
        metrics={"elevation_angle": elevation}
    )

    # Test 2: Verify low path loss
    path_loss = message_data["ntn_impairments"]["path_loss_db"]
    test_results.add_result(
        scenario="Scenario 2",
        test_name="Low path loss at high elevation (< 165 dB)",
        passed=path_loss < 165.0,
        details={"path_loss_db": path_loss, "threshold": 165.0},
        metrics={"path_loss_db": path_loss}
    )

    # Test 3: Verify good link margin
    link_margin = message_data["link_budget"]["link_margin_db"]
    test_results.add_result(
        scenario="Scenario 2",
        test_name="Good link margin (> 20 dB)",
        passed=link_margin > 20.0,
        details={"link_margin_db": link_margin, "threshold": 20.0},
        metrics={"link_margin_db": link_margin}
    )

    # Test 4: Verify high CQI
    cqi = message_data["channel_quality"]["cqi"]
    test_results.add_result(
        scenario="Scenario 2",
        test_name="High CQI indicating good channel (> 10)",
        passed=cqi > 10,
        details={"cqi": cqi, "threshold": 10},
        metrics={"cqi": cqi}
    )

    # Test 5: No immediate handover needed
    time_to_handover = message_data["handover_prediction"]["time_to_handover_sec"]
    test_results.add_result(
        scenario="Scenario 2",
        test_name="No immediate handover needed (> 300 sec)",
        passed=time_to_handover > 300.0,
        details={"time_to_handover_sec": time_to_handover},
        metrics={"time_to_handover_sec": time_to_handover}
    )


def scenario_3_handover_prediction(test_results: TestResults):
    """
    Scenario 3: Handover prediction - elevation approaching minimum

    Tests:
    - Handover time prediction
    - Next satellite identification
    - Handover probability calculation
    - Event trigger generation
    """
    print("\n=== Scenario 3: Handover Prediction - Approaching Minimum Elevation ===")

    bridge = NTN_E2_Bridge(orbit_type='LEO', carrier_frequency_ghz=2.1)

    ue_id = "UE-003"
    bridge.register_ue(ue_id, lat=0.0, lon=0.0, altitude_m=0.0)

    # Simulate measurements at 15° elevation (approaching 10° threshold)
    measurements = {
        "rsrp": -105.0,
        "rsrq": -15.0,
        "sinr": 7.0,
        "bler": 0.05,
        "tx_power_dbm": 23.0,
        "throughput_dl_mbps": 15.0,
        "throughput_ul_mbps": 5.0,
        "rain_attenuation_db": 0.0,
        "atmospheric_loss_db": 1.0
    }

    # Position satellite to create ~15° elevation
    satellite_lon = 45.0

    header, message = bridge.process_ue_report(
        ue_id=ue_id,
        measurements=measurements,
        satellite_lat=0.0,
        satellite_lon=satellite_lon
    )

    message_data = json.loads(message.decode('utf-8'))

    # Test 1: Verify handover prediction exists
    time_to_handover = message_data["handover_prediction"]["time_to_handover_sec"]
    test_results.add_result(
        scenario="Scenario 3",
        test_name="Handover time predicted",
        passed=0 < time_to_handover < 200.0,
        details={"time_to_handover_sec": time_to_handover},
        metrics={"time_to_handover_sec": time_to_handover}
    )

    # Test 2: Verify next satellite identified
    next_sat_id = message_data["handover_prediction"]["next_satellite_id"]
    test_results.add_result(
        scenario="Scenario 3",
        test_name="Next satellite identified",
        passed=next_sat_id is not None and next_sat_id != "",
        details={"next_satellite_id": next_sat_id}
    )

    # Test 3: Verify high handover probability
    handover_prob = message_data["handover_prediction"]["handover_probability"]
    test_results.add_result(
        scenario="Scenario 3",
        test_name="High handover probability (> 0.8)",
        passed=handover_prob > 0.8,
        details={"handover_probability": handover_prob},
        metrics={"handover_probability": handover_prob}
    )

    # Test 4: Create handover event trigger
    event_trigger = bridge.e2sm_ntn.create_event_trigger(
        NTNEventTrigger.HANDOVER_IMMINENT,
        time_to_handover_threshold_sec=30.0
    )
    test_results.add_result(
        scenario="Scenario 3",
        test_name="Handover event trigger created",
        passed=len(event_trigger) > 0,
        details={"event_trigger_size_bytes": len(event_trigger)}
    )

    # Test 5: Verify handover prediction method
    handover_pred = bridge.predict_next_handover(ue_id)
    test_results.add_result(
        scenario="Scenario 3",
        test_name="Bridge handover prediction works",
        passed=handover_pred is not None,
        details={"prediction": handover_pred}
    )


def scenario_4_power_control(test_results: TestResults):
    """
    Scenario 4: Power control recommendation

    Tests:
    - Link margin calculation
    - Power adjustment recommendation
    - Control message creation
    - Power control execution
    """
    print("\n=== Scenario 4: Power Control Recommendation ===")

    bridge = NTN_E2_Bridge(orbit_type='LEO', carrier_frequency_ghz=2.1)
    e2sm = bridge.e2sm_ntn

    ue_id = "UE-004"
    bridge.register_ue(ue_id, lat=0.0, lon=0.0, altitude_m=0.0)

    # Scenario 4a: Excessive link margin - reduce power
    print("\n  Sub-scenario 4a: Excessive link margin")

    measurements_high_margin = {
        "rsrp": -60.0,  # Very high RSRP
        "rsrq": -5.0,
        "sinr": 25.0,
        "bler": 0.0001,
        "tx_power_dbm": 23.0,
        "throughput_dl_mbps": 150.0,
        "throughput_ul_mbps": 75.0,
        "rain_attenuation_db": 0.0,
        "atmospheric_loss_db": 0.2
    }

    header, message = bridge.process_ue_report(
        ue_id=ue_id,
        measurements=measurements_high_margin,
        satellite_lat=0.0,
        satellite_lon=0.0
    )

    message_data = json.loads(message.decode('utf-8'))
    link_budget = LinkBudget(**message_data["link_budget"])

    # Test 1: Detect excessive margin
    test_results.add_result(
        scenario="Scenario 4a",
        test_name="Excessive link margin detected (> 30 dB)",
        passed=link_budget.link_margin_db > 30.0,
        details={"link_margin_db": link_budget.link_margin_db},
        metrics={"link_margin_db": link_budget.link_margin_db}
    )

    # Test 2: Recommend power reduction
    power_recommendation = e2sm.recommend_power_control(
        link_budget=link_budget,
        current_power_dbm=23.0
    )

    test_results.add_result(
        scenario="Scenario 4a",
        test_name="Power reduction recommended",
        passed=power_recommendation["power_adjustment_db"] < 0,
        details=power_recommendation,
        metrics={"power_adjustment_db": power_recommendation["power_adjustment_db"]}
    )

    # Test 3: Create control message for power adjustment
    control_msg = e2sm.create_control_message(
        action_type=NTNControlAction.POWER_CONTROL,
        ue_id=ue_id,
        parameters=power_recommendation
    )

    test_results.add_result(
        scenario="Scenario 4a",
        test_name="Power control message created",
        passed=len(control_msg) > 0,
        details={"control_message_size_bytes": len(control_msg)}
    )

    # Test 4: Execute power control action
    action_result = bridge.execute_control_action(
        action_type="POWER_CONTROL",
        ue_id=ue_id,
        parameters=power_recommendation
    )

    test_results.add_result(
        scenario="Scenario 4a",
        test_name="Power control action executed",
        passed=action_result["success"],
        details=action_result
    )

    # Scenario 4b: Low link margin - increase power
    print("\n  Sub-scenario 4b: Low link margin")

    measurements_low_margin = {
        "rsrp": -108.0,  # Low RSRP
        "rsrq": -17.0,
        "sinr": 4.0,
        "bler": 0.1,
        "tx_power_dbm": 20.0,  # Not at max power
        "throughput_dl_mbps": 8.0,
        "throughput_ul_mbps": 2.0,
        "rain_attenuation_db": 0.0,
        "atmospheric_loss_db": 1.2
    }

    header, message = bridge.process_ue_report(
        ue_id=ue_id,
        measurements=measurements_low_margin,
        satellite_lat=0.0,
        satellite_lon=50.0
    )

    message_data = json.loads(message.decode('utf-8'))
    link_budget_low = LinkBudget(**message_data["link_budget"])

    # Test 5: Recommend power increase
    power_recommendation_increase = e2sm.recommend_power_control(
        link_budget=link_budget_low,
        current_power_dbm=20.0
    )

    test_results.add_result(
        scenario="Scenario 4b",
        test_name="Power increase recommended for low margin",
        passed=power_recommendation_increase["power_adjustment_db"] > 0,
        details=power_recommendation_increase,
        metrics={"power_adjustment_db": power_recommendation_increase["power_adjustment_db"]}
    )


def scenario_5_multi_satellite(test_results: TestResults):
    """
    Scenario 5: Multi-satellite scenario

    Tests:
    - Multiple UEs tracking
    - Different orbit types (LEO, MEO, GEO)
    - Satellite visibility
    - Statistics collection
    """
    print("\n=== Scenario 5: Multi-Satellite Scenario ===")

    # Test LEO satellite
    print("\n  Testing LEO satellite")
    bridge_leo = NTN_E2_Bridge(orbit_type='LEO', carrier_frequency_ghz=2.1)

    ue_leo = "UE-LEO-001"
    bridge_leo.register_ue(ue_leo, lat=45.0, lon=-93.0, altitude_m=300.0)

    measurements_leo = {
        "rsrp": -85.0,
        "rsrq": -12.0,
        "sinr": 15.0,
        "bler": 0.01,
        "tx_power_dbm": 23.0,
        "throughput_dl_mbps": 75.0,
        "throughput_ul_mbps": 25.0
    }

    header_leo, message_leo = bridge_leo.process_ue_report(
        ue_id=ue_leo,
        measurements=measurements_leo,
        satellite_lat=0.0,
        satellite_lon=-93.0
    )

    message_leo_data = json.loads(message_leo.decode('utf-8'))

    # Test 1: LEO characteristics
    prop_delay_leo = message_leo_data["ntn_impairments"]["propagation_delay_ms"]
    test_results.add_result(
        scenario="Scenario 5 - LEO",
        test_name="LEO propagation delay (< 10 ms)",
        passed=prop_delay_leo < 10.0,
        details={"propagation_delay_ms": prop_delay_leo},
        metrics={"propagation_delay_ms": prop_delay_leo}
    )

    doppler_leo = abs(message_leo_data["ntn_impairments"]["doppler_shift_hz"])
    test_results.add_result(
        scenario="Scenario 5 - LEO",
        test_name="LEO Doppler shift significant (> 1000 Hz)",
        passed=doppler_leo > 1000.0,
        details={"doppler_shift_hz": doppler_leo},
        metrics={"doppler_shift_hz": doppler_leo}
    )

    # Test MEO satellite
    print("\n  Testing MEO satellite")
    bridge_meo = NTN_E2_Bridge(orbit_type='MEO', carrier_frequency_ghz=2.1)

    ue_meo = "UE-MEO-001"
    bridge_meo.register_ue(ue_meo, lat=45.0, lon=-93.0, altitude_m=300.0)

    measurements_meo = {
        "rsrp": -95.0,
        "rsrq": -14.0,
        "sinr": 12.0,
        "bler": 0.02,
        "tx_power_dbm": 23.0,
        "throughput_dl_mbps": 50.0,
        "throughput_ul_mbps": 15.0
    }

    header_meo, message_meo = bridge_meo.process_ue_report(
        ue_id=ue_meo,
        measurements=measurements_meo,
        satellite_lat=0.0,
        satellite_lon=-93.0
    )

    message_meo_data = json.loads(message_meo.decode('utf-8'))

    # Test 2: MEO characteristics
    prop_delay_meo = message_meo_data["ntn_impairments"]["propagation_delay_ms"]
    test_results.add_result(
        scenario="Scenario 5 - MEO",
        test_name="MEO propagation delay (10-100 ms)",
        passed=10.0 < prop_delay_meo < 100.0,
        details={"propagation_delay_ms": prop_delay_meo},
        metrics={"propagation_delay_ms": prop_delay_meo}
    )

    # Test GEO satellite
    print("\n  Testing GEO satellite")
    bridge_geo = NTN_E2_Bridge(orbit_type='GEO', carrier_frequency_ghz=2.1)

    ue_geo = "UE-GEO-001"
    bridge_geo.register_ue(ue_geo, lat=45.0, lon=-93.0, altitude_m=300.0)

    measurements_geo = {
        "rsrp": -105.0,
        "rsrq": -16.0,
        "sinr": 8.0,
        "bler": 0.05,
        "tx_power_dbm": 23.0,
        "throughput_dl_mbps": 25.0,
        "throughput_ul_mbps": 5.0
    }

    header_geo, message_geo = bridge_geo.process_ue_report(
        ue_id=ue_geo,
        measurements=measurements_geo,
        satellite_lat=0.0,
        satellite_lon=-93.0
    )

    message_geo_data = json.loads(message_geo.decode('utf-8'))

    # Test 3: GEO characteristics
    prop_delay_geo = message_geo_data["ntn_impairments"]["propagation_delay_ms"]
    test_results.add_result(
        scenario="Scenario 5 - GEO",
        test_name="GEO propagation delay (> 100 ms)",
        passed=prop_delay_geo > 100.0,
        details={"propagation_delay_ms": prop_delay_geo},
        metrics={"propagation_delay_ms": prop_delay_geo}
    )

    doppler_geo = abs(message_geo_data["ntn_impairments"]["doppler_shift_hz"])
    test_results.add_result(
        scenario="Scenario 5 - GEO",
        test_name="GEO Doppler shift minimal (< 100 Hz)",
        passed=doppler_geo < 100.0,
        details={"doppler_shift_hz": doppler_geo},
        metrics={"doppler_shift_hz": doppler_geo}
    )

    # Test 4: Statistics collection
    stats_leo = bridge_leo.get_statistics()
    test_results.add_result(
        scenario="Scenario 5",
        test_name="Statistics collection works",
        passed=stats_leo["registered_ues"] == 1,
        details=stats_leo
    )


def main():
    """Run all test scenarios"""
    print("=" * 80)
    print("E2SM-NTN Service Model Test Suite")
    print("=" * 80)

    test_results = TestResults()

    # Run all scenarios
    try:
        scenario_1_low_elevation(test_results)
        scenario_2_optimal_elevation(test_results)
        scenario_3_handover_prediction(test_results)
        scenario_4_power_control(test_results)
        scenario_5_multi_satellite(test_results)
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Print summary
    summary = test_results.get_summary()
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests:  {summary['total_tests']}")
    print(f"Passed:       {summary['passed']}")
    print(f"Failed:       {summary['failed']}")
    print(f"Pass Rate:    {summary['pass_rate']}")
    print(f"Duration:     {summary['duration_seconds']} seconds")
    print("=" * 80)

    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), 'test_results')
    os.makedirs(results_dir, exist_ok=True)

    results_file = os.path.join(results_dir, 'e2sm_ntn_test_results.json')
    test_results.save_to_file(results_file)

    # Return exit code
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    exit(main())
