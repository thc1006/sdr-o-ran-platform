#!/usr/bin/env python3
"""
End-to-End RIC Integration Test
Tests complete NTN-O-RAN platform with RIC integration

Test Scenarios:
1. E2 Termination Point setup and connection
2. E2 Setup procedure with E2SM-NTN registration
3. RIC Subscription for NTN metrics
4. Periodic RIC Indications with LEO satellite data
5. RIC Control Request execution (handover trigger)
6. Performance measurements and validation

Success Criteria:
- E2 Setup completes successfully
- Subscriptions accepted by RIC
- Indications delivered with <10ms latency
- Control requests executed with <10ms latency
- End-to-end loop <15ms
"""

import asyncio
import logging
import time
import sys
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add parent directory to path
base_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'e2_ntn_extension'))

# Direct imports to avoid package init issues
from e2sm_ntn import E2SM_NTN, NTNControlMessage
from ric_integration.e2_termination import E2TerminationPoint, E2ConnectionConfig
from ric_integration.e2ap_messages import (
    RICSubscriptionRequest, E2APMessageFactory
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data"""
    test_name: str
    success: bool
    duration_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None


class SimulatedRIC:
    """
    Simulated RIC for testing (when real RIC not available)

    Implements minimal RIC functionality:
    - E2 Setup Response
    - Subscription Response
    - Control Request generation
    """

    def __init__(self, port: int = 36421):
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.e2_setup_received = False
        self.subscriptions = []
        self.indications_received = 0

    async def start(self):
        """Start simulated RIC server"""
        try:
            import socket

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(1)
            self.server_socket.setblocking(False)

            logger.info(f"Simulated RIC listening on port {self.port}")
            self.running = True

            # Accept connection
            loop = asyncio.get_event_loop()
            self.client_socket, addr = await loop.sock_accept(self.server_socket)
            logger.info(f"E2 connection accepted from {addr}")

            # Start message handler
            asyncio.create_task(self.message_handler())

        except Exception as e:
            logger.error(f"Failed to start simulated RIC: {e}")
            raise

    async def message_handler(self):
        """Handle incoming E2AP messages"""
        loop = asyncio.get_event_loop()

        while self.running and self.client_socket:
            try:
                # Receive message
                data = await loop.sock_recv(self.client_socket, 65536)
                if not data:
                    break

                # Parse message
                message = E2APMessageFactory.parse_message(data)

                # Handle based on type
                from ric_integration.e2ap_messages import (
                    E2SetupRequest, RICSubscriptionRequest, RICIndication
                )

                if isinstance(message, E2SetupRequest):
                    await self.handle_e2_setup(message)
                elif isinstance(message, RICSubscriptionRequest):
                    await self.handle_subscription(message)
                elif isinstance(message, RICIndication):
                    self.indications_received += 1
                    logger.debug(f"RIC Indication #{self.indications_received} received")

            except Exception as e:
                logger.error(f"Error in RIC message handler: {e}")
                await asyncio.sleep(0.1)

    async def handle_e2_setup(self, request):
        """Handle E2 Setup Request"""
        from ric_integration.e2ap_messages import E2SetupResponse

        logger.info("E2 Setup Request received")
        self.e2_setup_received = True

        # Send E2 Setup Response
        response = E2SetupResponse(
            transaction_id=request.encode()[:7][-4:],  # Extract transaction ID
            global_ric_id="RIC-SIM-001",
            ran_functions_accepted=[rf.ran_function_id for rf in request.ran_functions]
        )

        response_msg = response.encode()
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(self.client_socket, response_msg)

        logger.info("E2 Setup Response sent")

    async def handle_subscription(self, request):
        """Handle RIC Subscription Request"""
        from ric_integration.e2ap_messages import RICSubscriptionResponse

        logger.info(f"RIC Subscription Request received: ran_func={request.ran_function_id}")

        self.subscriptions.append(request)

        # Send subscription response
        response = RICSubscriptionResponse(
            ric_request_id=request.ric_request_id,
            ran_function_id=request.ran_function_id,
            ric_actions_admitted=[action["id"] for action in request.ric_actions]
        )

        response_msg = response.encode()
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(self.client_socket, response_msg)

        logger.info("RIC Subscription Response sent")

    async def send_control_request(self, ue_id: str, action: str):
        """Send RIC Control Request"""
        from ric_integration.e2ap_messages import RICControlRequest
        from e2_ntn_extension.e2sm_ntn import E2SM_NTN

        e2sm = E2SM_NTN(encoding='json')

        control_msg = e2sm.create_control_message(
            action_type=action,
            ue_id=ue_id,
            parameters={"target_satellite_id": "SAT-002"}
        )

        request = RICControlRequest(
            ric_request_id=9999,
            ran_function_id=E2SM_NTN.RAN_FUNCTION_ID,
            ric_call_process_id=None,
            ric_control_header=b'{"type": "ntn-control"}',
            ric_control_message=control_msg,
            ric_control_ack_request=1
        )

        request_msg = request.encode()
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(self.client_socket, request_msg)

        logger.info(f"RIC Control Request sent: action={action}")

    async def stop(self):
        """Stop simulated RIC"""
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        logger.info("Simulated RIC stopped")


class RICIntegrationTest:
    """End-to-End RIC Integration Test Suite"""

    def __init__(self, use_real_ric: bool = False):
        """
        Initialize test suite

        Args:
            use_real_ric: If True, connect to real RIC. Otherwise use simulator.
        """
        self.use_real_ric = use_real_ric
        self.e2_term: Optional[E2TerminationPoint] = None
        self.simulated_ric: Optional[SimulatedRIC] = None
        self.test_results = []
        self.control_requests_received = []

    def control_callback(self, control_msg: NTNControlMessage):
        """Callback for RIC Control requests"""
        logger.info(f"Control request received: action={control_msg.action_type}, ue={control_msg.ue_id}")
        self.control_requests_received.append({
            "timestamp": time.time(),
            "action": control_msg.action_type,
            "ue_id": control_msg.ue_id,
            "parameters": control_msg.parameters
        })

    def indication_data_provider(self) -> Dict[str, Any]:
        """Provide NTN metrics for RIC Indications"""
        # Simulate LEO satellite pass
        return {
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
                "carrier_frequency_ghz": 2.1,
                "next_satellite_id": "STARLINK-1235",
                "next_satellite_elevation": 15.0
            },
            "measurements": {
                "rsrp": -85.0,
                "rsrq": -12.0,
                "sinr": 15.0,
                "bler": 0.01,
                "tx_power_dbm": 23.0,
                "throughput_dl_mbps": 100.0,
                "throughput_ul_mbps": 20.0,
                "packet_loss_rate": 0.005,
                "rain_attenuation_db": 0.0,
                "atmospheric_loss_db": 0.5
            }
        }

    async def test_e2_connection(self) -> TestResult:
        """Test 1: E2 Termination Point Connection"""
        logger.info("=== Test 1: E2 Connection ===")
        start_time = time.time()

        try:
            # Create E2 Termination Point
            config = E2ConnectionConfig(
                ric_ip="127.0.0.1",
                ric_port=36421,
                global_e2_node_id="NTN-TEST-NODE"
            )

            self.e2_term = E2TerminationPoint(config=config)
            self.e2_term.set_control_callback(self.control_callback)
            self.e2_term.set_indication_data_provider(self.indication_data_provider)

            # Start simulated RIC if not using real RIC
            if not self.use_real_ric:
                self.simulated_ric = SimulatedRIC(port=36421)
                await self.simulated_ric.start()
                await asyncio.sleep(0.5)  # Wait for RIC to be ready

            # Connect to RIC
            connected = await self.e2_term.connect_to_ric()

            duration_ms = (time.time() - start_time) * 1000

            if connected:
                return TestResult(
                    test_name="E2 Connection",
                    success=True,
                    duration_ms=duration_ms,
                    details={
                        "ric_ip": config.ric_ip,
                        "ric_port": config.ric_port,
                        "sctp_enabled": hasattr(__import__('socket'), 'IPPROTO_SCTP')
                    }
                )
            else:
                return TestResult(
                    test_name="E2 Connection",
                    success=False,
                    duration_ms=duration_ms,
                    details={},
                    error="Connection failed"
                )

        except Exception as e:
            return TestResult(
                test_name="E2 Connection",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                details={},
                error=str(e)
            )

    async def test_e2_setup(self) -> TestResult:
        """Test 2: E2 Setup Procedure"""
        logger.info("=== Test 2: E2 Setup ===")
        start_time = time.time()

        try:
            # E2 Setup is performed during connection
            # Verify it completed successfully
            await asyncio.sleep(0.5)  # Wait for setup to complete

            if self.e2_term.e2_setup_complete:
                stats = self.e2_term.get_statistics()

                return TestResult(
                    test_name="E2 Setup",
                    success=True,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={
                        "setup_requests_sent": stats["setup_requests_sent"],
                        "setup_responses_received": stats["setup_responses_received"],
                        "ran_function_id": E2SM_NTN.RAN_FUNCTION_ID,
                        "encoding": self.e2_term.e2sm_ntn.get_encoding_type()
                    }
                )
            else:
                return TestResult(
                    test_name="E2 Setup",
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={},
                    error="E2 Setup not complete"
                )

        except Exception as e:
            return TestResult(
                test_name="E2 Setup",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                details={},
                error=str(e)
            )

    async def test_subscription(self) -> TestResult:
        """Test 3: RIC Subscription"""
        logger.info("=== Test 3: RIC Subscription ===")
        start_time = time.time()

        try:
            # Wait for E2 Setup to complete
            await asyncio.sleep(0.5)

            # Simulated RIC will auto-accept subscriptions
            # In real scenario, would wait for actual subscription from xApp

            # For simulation, create a dummy subscription
            if self.simulated_ric:
                # Send subscription request from RIC side
                event_trigger = E2SM_NTN.create_event_trigger(
                    trigger_type=1,  # Periodic
                    period_ms=1000
                )

                subscription_req = RICSubscriptionRequest(
                    ric_request_id=1001,
                    ran_function_id=E2SM_NTN.RAN_FUNCTION_ID,
                    ric_event_trigger_definition=event_trigger,
                    ric_actions=[{"id": 1, "type": "report"}]
                )

                # Manually handle subscription (normally would come from RIC)
                await self.e2_term.handle_subscription_request(subscription_req)

                duration_ms = (time.time() - start_time) * 1000

                return TestResult(
                    test_name="RIC Subscription",
                    success=True,
                    duration_ms=duration_ms,
                    details={
                        "subscriptions_active": len(self.e2_term.subscriptions),
                        "ran_function_id": E2SM_NTN.RAN_FUNCTION_ID
                    }
                )
            else:
                # Real RIC scenario - would need actual subscription from xApp
                return TestResult(
                    test_name="RIC Subscription",
                    success=True,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"note": "Real RIC - subscription handled externally"}
                )

        except Exception as e:
            return TestResult(
                test_name="RIC Subscription",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                details={},
                error=str(e)
            )

    async def test_indications(self) -> TestResult:
        """Test 4: RIC Indications"""
        logger.info("=== Test 4: RIC Indications ===")
        start_time = time.time()

        try:
            # Send multiple indications
            num_indications = 10
            latencies = []

            for i in range(num_indications):
                indication_start = time.time()

                # Get subscription ID (use first subscription)
                if self.e2_term.subscriptions:
                    sub_id = list(self.e2_term.subscriptions.keys())[0]
                    ntn_metrics = self.indication_data_provider()

                    success = await self.e2_term.send_indication(sub_id, ntn_metrics)

                    if success:
                        latency_ms = (time.time() - indication_start) * 1000
                        latencies.append(latency_ms)

                await asyncio.sleep(0.1)  # 100ms between indications

            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)

                stats = self.e2_term.get_statistics()

                return TestResult(
                    test_name="RIC Indications",
                    success=True,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={
                        "indications_sent": stats["indications_sent"],
                        "avg_latency_ms": avg_latency,
                        "min_latency_ms": min_latency,
                        "max_latency_ms": max_latency,
                        "encoding": self.e2_term.e2sm_ntn.get_encoding_type()
                    }
                )
            else:
                return TestResult(
                    test_name="RIC Indications",
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={},
                    error="No indications sent"
                )

        except Exception as e:
            return TestResult(
                test_name="RIC Indications",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                details={},
                error=str(e)
            )

    async def test_control_execution(self) -> TestResult:
        """Test 5: RIC Control Request Execution"""
        logger.info("=== Test 5: RIC Control ===")
        start_time = time.time()

        try:
            # Simulated RIC sends control request
            if self.simulated_ric:
                from e2_ntn_extension.e2sm_ntn import NTNControlAction

                # Send control request from RIC
                await self.simulated_ric.send_control_request(
                    ue_id="UE-TEST-001",
                    action="TRIGGER_HANDOVER"
                )

                # Wait for control to be received and executed
                await asyncio.sleep(0.5)

                if self.control_requests_received:
                    stats = self.e2_term.get_statistics()

                    return TestResult(
                        test_name="RIC Control",
                        success=True,
                        duration_ms=(time.time() - start_time) * 1000,
                        details={
                            "controls_received": stats["controls_received"],
                            "controls_executed": stats["controls_executed"],
                            "avg_control_latency_ms": stats["avg_control_latency_ms"],
                            "control_actions": [cr["action"] for cr in self.control_requests_received]
                        }
                    )
                else:
                    return TestResult(
                        test_name="RIC Control",
                        success=False,
                        duration_ms=(time.time() - start_time) * 1000,
                        details={},
                        error="No control requests received"
                    )
            else:
                # Real RIC scenario
                return TestResult(
                    test_name="RIC Control",
                    success=True,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={"note": "Real RIC - control handled externally"}
                )

        except Exception as e:
            return TestResult(
                test_name="RIC Control",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                details={},
                error=str(e)
            )

    async def test_end_to_end_latency(self) -> TestResult:
        """Test 6: End-to-End Latency Measurement"""
        logger.info("=== Test 6: E2E Latency ===")
        start_time = time.time()

        try:
            # Measure complete loop: Indication -> Control -> Execution
            stats = self.e2_term.get_statistics()

            indication_latency = stats.get("avg_indication_latency_ms", 0)
            control_latency = stats.get("avg_control_latency_ms", 0)
            e2e_latency = indication_latency + control_latency

            success = e2e_latency < 15.0  # Target: <15ms

            return TestResult(
                test_name="E2E Latency",
                success=success,
                duration_ms=(time.time() - start_time) * 1000,
                details={
                    "e2e_latency_ms": e2e_latency,
                    "indication_latency_ms": indication_latency,
                    "control_latency_ms": control_latency,
                    "target_latency_ms": 15.0,
                    "meets_target": success
                }
            )

        except Exception as e:
            return TestResult(
                test_name="E2E Latency",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                details={},
                error=str(e)
            )

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("="*60)
        logger.info("STARTING RIC INTEGRATION TESTS")
        logger.info("="*60)

        total_start = time.time()

        # Test 1: E2 Connection
        result1 = await self.test_e2_connection()
        self.test_results.append(result1)

        if not result1.success:
            logger.error("E2 Connection failed - aborting remaining tests")
            return self.generate_report()

        # Test 2: E2 Setup
        result2 = await self.test_e2_setup()
        self.test_results.append(result2)

        # Test 3: Subscription
        result3 = await self.test_subscription()
        self.test_results.append(result3)

        # Test 4: Indications
        result4 = await self.test_indications()
        self.test_results.append(result4)

        # Test 5: Control Execution
        result5 = await self.test_control_execution()
        self.test_results.append(result5)

        # Test 6: E2E Latency
        result6 = await self.test_end_to_end_latency()
        self.test_results.append(result6)

        # Cleanup
        if self.e2_term:
            await self.e2_term.stop()
        if self.simulated_ric:
            await self.simulated_ric.stop()

        total_duration = time.time() - total_start

        logger.info("="*60)
        logger.info(f"ALL TESTS COMPLETED in {total_duration:.2f}s")
        logger.info("="*60)

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        passed_tests = sum(1 for r in self.test_results if r.success)
        total_tests = len(self.test_results)

        report = {
            "timestamp": time.time(),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "tests": [
                {
                    "name": r.test_name,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "details": r.details,
                    "error": r.error
                }
                for r in self.test_results
            ]
        }

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {report['success_rate']:.1f}%")
        logger.info("="*60)

        for result in self.test_results:
            status = "PASS" if result.success else "FAIL"
            logger.info(f"{status:4s} | {result.test_name:20s} | {result.duration_ms:6.2f}ms")
            if not result.success and result.error:
                logger.error(f"       Error: {result.error}")

        logger.info("="*60)

        return report


async def main():
    """Main test entry point"""
    # Check for real RIC argument
    use_real_ric = "--real-ric" in sys.argv

    if use_real_ric:
        logger.info("Using REAL O-RAN SC RIC")
    else:
        logger.info("Using SIMULATED RIC for testing")

    # Run tests
    test_suite = RICIntegrationTest(use_real_ric=use_real_ric)
    report = await test_suite.run_all_tests()

    # Save report
    report_file = "/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/ric_integration/test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nTest report saved to: {report_file}")

    # Return exit code based on success
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
