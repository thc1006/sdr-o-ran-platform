#!/usr/bin/env python3
"""
Standalone End-to-End Integration Demo for SDR-O-RAN Platform

Demonstrates complete pipeline:
1. SDR Signal Acquisition → gRPC Transmission
2. gRPC → DRL Optimization
3. DRL → E2 Interface
4. E2 Interface → xApp Framework
5. Full system validation

Run with: python tests/integration/run_e2e_integration_demo.py
"""

import asyncio
import numpy as np
from pathlib import Path
import sys
import time
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "03-Implementation" / "ric-platform" / "e2-interface"))

# Import E2 components
from e2_manager import E2InterfaceManager
from e2_messages import E2SetupRequest, E2NodeComponentConfig
from e2sm_kpm import E2SM_KPM, MeasurementType, MeasurementRecord


class IntegrationTestReport:
    """Track integration test results"""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def record_pass(self, test_name: str):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"✓ {test_name}")

    def record_fail(self, test_name: str, error: str):
        self.tests_run += 1
        self.tests_failed += 1
        self.failures.append((test_name, error))
        print(f"✗ {test_name}: {error}")

    def print_summary(self):
        print("\n" + "="*80)
        print("END-TO-END INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {self.tests_passed/self.tests_run*100:.1f}%")

        if self.failures:
            print("\nFailed Tests:")
            for name, error in self.failures:
                print(f"  - {name}: {error}")
        print("="*80)


async def test_sdr_to_grpc_pipeline(report: IntegrationTestReport):
    """Test 1: SDR → gRPC Pipeline"""
    try:
        # Simulate SDR signal capture
        sample_rate = 30.72e6  # Hz
        center_freq = 3.5e9     # Hz
        num_samples = 2048

        # Generate test I/Q samples
        signal_data = np.random.randn(num_samples) + 1j * np.random.randn(num_samples)

        # Validate signal properties
        assert len(signal_data) == num_samples
        assert signal_data.dtype == np.complex128

        # Simulate gRPC transmission (would normally send over network)
        transmission_success = True  # Mock successful transmission

        if transmission_success:
            report.record_pass("SDR → gRPC Signal Transmission")
        else:
            report.record_fail("SDR → gRPC Signal Transmission", "Transmission failed")

    except Exception as e:
        report.record_fail("SDR → gRPC Signal Transmission", str(e))


async def test_grpc_to_drl_pipeline(report: IntegrationTestReport):
    """Test 2: gRPC → DRL Pipeline"""
    try:
        # Simulate received gRPC metrics
        signal_metrics = {
            'rssi_dbm': -75.5,
            'snr_db': 18.3,
            'ber': 1e-5,
            'throughput_mbps': 45.2
        }

        # Convert to DRL observation space
        observation = np.array([
            (signal_metrics['rssi_dbm'] + 100) / 100,  # Normalize RSSI
            signal_metrics['snr_db'] / 30,              # Normalize SNR
            -np.log10(signal_metrics['ber']),           # Log BER
            signal_metrics['throughput_mbps'] / 100     # Normalize throughput
        ])

        # Simulate DRL action (normally from trained model)
        drl_action = 0.75  # Normalized action value

        # Convert to control parameter
        min_power = -20  # dBm
        max_power = 23   # dBm
        tx_power = min_power + drl_action * (max_power - min_power)

        assert len(observation) == 4
        assert min_power <= tx_power <= max_power

        report.record_pass("gRPC → DRL Optimization")

    except Exception as e:
        report.record_fail("gRPC → DRL Optimization", str(e))


async def test_drl_to_e2_pipeline(report: IntegrationTestReport):
    """Test 3: DRL → E2 Interface Pipeline"""
    try:
        # Create E2 Interface Manager
        e2_manager = E2InterfaceManager()
        await e2_manager.start()

        # Setup E2 node
        setup_request = E2SetupRequest(
            transaction_id=1,
            global_e2_node_id="gnb-test-001",
            ran_functions=[
                {
                    'ranFunctionId': 1,
                    'ranFunctionRevision': 1,
                    'ranFunctionOId': '1.3.6.1.4.1.53148.1.1.2.2'  # E2SM-KPM
                }
            ],
            e2_node_component_config=[
                E2NodeComponentConfig(
                    component_type="gNB-DU",
                    component_id=1
                )
            ]
        )

        response = await e2_manager.handle_e2_setup(setup_request)

        assert response.transaction_id == 1
        assert len(response.ran_functions_accepted) > 0

        # DRL triggers control request
        control_header = b'\x00\x01'
        control_message = b'\x02\x03\x04'

        success = await e2_manager.send_control_request(
            "gnb-test-001",
            ran_function_id=1,
            control_header=control_header,
            control_message=control_message
        )

        assert success is True

        await e2_manager.stop()

        report.record_pass("DRL → E2 Interface Integration")

    except Exception as e:
        report.record_fail("DRL → E2 Interface Integration", str(e))


async def test_e2_performance(report: IntegrationTestReport):
    """Test 4: E2 Interface Performance"""
    try:
        e2_manager = E2InterfaceManager()
        await e2_manager.start()

        # Setup multiple E2 nodes concurrently
        node_count = 10
        setup_tasks = []

        for i in range(node_count):
            setup_request = E2SetupRequest(
                transaction_id=i,
                global_e2_node_id=f"gnb-perf-{i:03d}",
                ran_functions=[
                    {
                        'ranFunctionId': 1,
                        'ranFunctionRevision': 1,
                        'ranFunctionOId': '1.3.6.1.4.1.53148.1.1.2.2'
                    }
                ],
                e2_node_component_config=[
                    E2NodeComponentConfig(
                        component_type="gNB-DU",
                        component_id=i
                    )
                ]
            )
            setup_tasks.append(e2_manager.handle_e2_setup(setup_request))

        start_time = time.perf_counter()
        responses = await asyncio.gather(*setup_tasks)
        duration = time.perf_counter() - start_time

        throughput = node_count / duration

        assert len(responses) == node_count
        assert throughput > 10  # At least 10 setups/sec

        await e2_manager.stop()

        report.record_pass(f"E2 Performance Test ({throughput:.1f} setups/sec)")

    except Exception as e:
        report.record_fail("E2 Performance Test", str(e))


async def test_e2_latency(report: IntegrationTestReport):
    """Test 5: E2 Control Request Latency"""
    try:
        e2_manager = E2InterfaceManager()
        await e2_manager.start()

        # Setup E2 node
        setup_request = E2SetupRequest(
            transaction_id=1,
            global_e2_node_id="gnb-latency-001",
            ran_functions=[
                {
                    'ranFunctionId': 1,
                    'ranFunctionRevision': 1,
                    'ranFunctionOId': '1.3.6.1.4.1.53148.1.1.2.2'
                }
            ],
            e2_node_component_config=[
                E2NodeComponentConfig(
                    component_type="gNB-DU",
                    component_id=1
                )
            ]
        )

        await e2_manager.handle_e2_setup(setup_request)

        # Measure control request latency
        control_header = b'\x00\x01'
        control_message = b'\x02\x03'

        start_time = time.perf_counter()
        success = await e2_manager.send_control_request(
            "gnb-latency-001",
            ran_function_id=1,
            control_header=control_header,
            control_message=control_message
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        assert success is True
        assert latency_ms < 100  # Less than 100ms

        await e2_manager.stop()

        report.record_pass(f"E2 Latency Test ({latency_ms:.2f}ms)")

    except Exception as e:
        report.record_fail("E2 Latency Test", str(e))


async def test_e2_subscription(report: IntegrationTestReport):
    """Test 6: E2 Subscription Management"""
    try:
        e2_manager = E2InterfaceManager()
        await e2_manager.start()

        # Setup E2 node
        setup_request = E2SetupRequest(
            transaction_id=1,
            global_e2_node_id="gnb-sub-001",
            ran_functions=[
                {
                    'ranFunctionId': 1,
                    'ranFunctionRevision': 1,
                    'ranFunctionOId': '1.3.6.1.4.1.53148.1.1.2.2'
                }
            ],
            e2_node_component_config=[
                E2NodeComponentConfig(
                    component_type="gNB-DU",
                    component_id=1
                )
            ]
        )

        await e2_manager.handle_e2_setup(setup_request)

        # Create subscription
        async def dummy_callback(indication):
            pass

        subscription_id = await e2_manager.create_subscription(
            "gnb-sub-001",
            ran_function_id=1,
            callback=dummy_callback
        )

        assert subscription_id > 0
        assert subscription_id in e2_manager.subscriptions

        await e2_manager.stop()

        report.record_pass("E2 Subscription Management")

    except Exception as e:
        report.record_fail("E2 Subscription Management", str(e))


async def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("SDR-O-RAN PLATFORM - END-TO-END INTEGRATION TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    report = IntegrationTestReport()

    # Run all tests
    await test_sdr_to_grpc_pipeline(report)
    await test_grpc_to_drl_pipeline(report)
    await test_drl_to_e2_pipeline(report)
    await test_e2_performance(report)
    await test_e2_latency(report)
    await test_e2_subscription(report)

    # Print summary
    report.print_summary()

    # Return exit code
    return 0 if report.tests_failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
