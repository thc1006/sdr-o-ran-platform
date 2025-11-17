#!/usr/bin/env python3
"""
RIC Integration Performance Benchmarking Suite

Benchmarks:
1. E2 Setup time
2. Indication message encoding latency (JSON vs ASN.1)
3. Indication transmission latency
4. Control request latency
5. End-to-end control loop time
6. Message throughput (indications/sec)
7. Memory usage
8. CPU utilization

Compares:
- Simulated E2 interface vs Production E2 Termination
- JSON encoding vs ASN.1 PER encoding
- Different reporting periods
"""

import asyncio
import logging
import time
import sys
import os
import json
import psutil
import statistics
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

base_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'e2_ntn_extension'))

from e2sm_ntn import E2SM_NTN
from ric_integration.e2_termination import E2TerminationPoint, E2ConnectionConfig
from ric_integration.test_ric_integration import SimulatedRIC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    name: str
    metric: str
    value: float
    unit: str
    samples: int
    std_dev: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RICPerformanceBenchmark:
    """RIC Integration Performance Benchmark Suite"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()

    async def benchmark_e2_setup(self) -> BenchmarkResult:
        """Benchmark E2 Setup time"""
        logger.info("Benchmarking E2 Setup...")

        setup_times = []
        num_trials = 10

        for i in range(num_trials):
            # Start simulated RIC
            ric = SimulatedRIC(port=36421 + i)
            await ric.start()
            await asyncio.sleep(0.1)

            # Create E2 Termination
            config = E2ConnectionConfig(
                ric_ip="127.0.0.1",
                ric_port=36421 + i
            )
            e2_term = E2TerminationPoint(config=config)

            # Measure setup time
            start_time = time.time()
            await e2_term.connect_to_ric()
            setup_time = (time.time() - start_time) * 1000

            setup_times.append(setup_time)

            # Cleanup
            await e2_term.stop()
            await ric.stop()
            await asyncio.sleep(0.1)

        return BenchmarkResult(
            name="E2 Setup Time",
            metric="setup_time",
            value=statistics.mean(setup_times),
            unit="ms",
            samples=num_trials,
            std_dev=statistics.stdev(setup_times) if len(setup_times) > 1 else 0,
            min_value=min(setup_times),
            max_value=max(setup_times)
        )

    async def benchmark_indication_encoding(self) -> List[BenchmarkResult]:
        """Benchmark indication message encoding (JSON vs ASN.1)"""
        logger.info("Benchmarking indication encoding...")

        # Create test data
        ntn_metrics = {
            "ue_id": "UE-BENCH-001",
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

        results = []
        num_trials = 1000

        # Benchmark JSON encoding
        e2sm_json = E2SM_NTN(encoding='json')
        json_times = []
        json_sizes = []

        for _ in range(num_trials):
            start = time.time()
            header, message = e2sm_json.create_indication_message(
                ue_id=ntn_metrics["ue_id"],
                satellite_state=ntn_metrics["satellite_state"],
                ue_measurements=ntn_metrics["measurements"]
            )
            encode_time = (time.time() - start) * 1000
            json_times.append(encode_time)
            json_sizes.append(len(header) + len(message))

        results.append(BenchmarkResult(
            name="Indication Encoding (JSON)",
            metric="encoding_latency",
            value=statistics.mean(json_times),
            unit="ms",
            samples=num_trials,
            std_dev=statistics.stdev(json_times),
            min_value=min(json_times),
            max_value=max(json_times),
            metadata={"avg_size_bytes": statistics.mean(json_sizes)}
        ))

        # Benchmark ASN.1 encoding
        e2sm_asn1 = E2SM_NTN(encoding='asn1')
        asn1_times = []
        asn1_sizes = []

        for _ in range(num_trials):
            start = time.time()
            header, message = e2sm_asn1.create_indication_message(
                ue_id=ntn_metrics["ue_id"],
                satellite_state=ntn_metrics["satellite_state"],
                ue_measurements=ntn_metrics["measurements"]
            )
            encode_time = (time.time() - start) * 1000
            asn1_times.append(encode_time)
            asn1_sizes.append(len(header) + len(message))

        results.append(BenchmarkResult(
            name="Indication Encoding (ASN.1)",
            metric="encoding_latency",
            value=statistics.mean(asn1_times),
            unit="ms",
            samples=num_trials,
            std_dev=statistics.stdev(asn1_times),
            min_value=min(asn1_times),
            max_value=max(asn1_times),
            metadata={"avg_size_bytes": statistics.mean(asn1_sizes)}
        ))

        # Calculate size reduction
        size_reduction = (1 - statistics.mean(asn1_sizes) / statistics.mean(json_sizes)) * 100

        results.append(BenchmarkResult(
            name="ASN.1 Size Reduction",
            metric="size_reduction",
            value=size_reduction,
            unit="%",
            samples=num_trials,
            metadata={
                "json_avg_bytes": statistics.mean(json_sizes),
                "asn1_avg_bytes": statistics.mean(asn1_sizes)
            }
        ))

        return results

    async def benchmark_indication_transmission(self) -> BenchmarkResult:
        """Benchmark indication transmission latency"""
        logger.info("Benchmarking indication transmission...")

        # Setup E2 connection
        ric = SimulatedRIC(port=36422)
        await ric.start()
        await asyncio.sleep(0.1)

        config = E2ConnectionConfig(
            ric_ip="127.0.0.1",
            ric_port=36422
        )
        e2_term = E2TerminationPoint(config=config)

        def data_provider():
            return {
                "ue_id": "UE-001",
                "satellite_state": {
                    "satellite_id": "SAT-001",
                    "orbit_type": "LEO",
                    "beam_id": 1,
                    "elevation_angle": 45.0,
                    "azimuth_angle": 180.0,
                    "slant_range_km": 850.0,
                    "satellite_velocity": 7.5,
                    "angular_velocity": -0.5
                },
                "measurements": {
                    "rsrp": -85.0,
                    "rsrq": -12.0,
                    "sinr": 15.0,
                    "bler": 0.01
                }
            }

        e2_term.set_indication_data_provider(data_provider)

        await e2_term.connect_to_ric()
        await asyncio.sleep(0.5)

        # Create subscription
        from ric_integration.e2ap_messages import RICSubscriptionRequest

        event_trigger = E2SM_NTN.create_event_trigger(trigger_type=1, period_ms=100)
        sub_req = RICSubscriptionRequest(
            ric_request_id=1001,
            ran_function_id=E2SM_NTN.RAN_FUNCTION_ID,
            ric_event_trigger_definition=event_trigger,
            ric_actions=[{"id": 1, "type": "report"}]
        )
        await e2_term.handle_subscription_request(sub_req)

        # Send multiple indications
        num_indications = 100
        transmission_times = []

        sub_id = list(e2_term.subscriptions.keys())[0]

        for _ in range(num_indications):
            start = time.time()
            await e2_term.send_indication(sub_id, data_provider())
            transmission_time = (time.time() - start) * 1000
            transmission_times.append(transmission_time)
            await asyncio.sleep(0.01)

        # Cleanup
        await e2_term.stop()
        await ric.stop()

        return BenchmarkResult(
            name="Indication Transmission",
            metric="transmission_latency",
            value=statistics.mean(transmission_times),
            unit="ms",
            samples=num_indications,
            std_dev=statistics.stdev(transmission_times),
            min_value=min(transmission_times),
            max_value=max(transmission_times)
        )

    async def benchmark_throughput(self) -> BenchmarkResult:
        """Benchmark message throughput (indications/sec)"""
        logger.info("Benchmarking message throughput...")

        # Setup E2 connection
        ric = SimulatedRIC(port=36423)
        await ric.start()
        await asyncio.sleep(0.1)

        config = E2ConnectionConfig(
            ric_ip="127.0.0.1",
            ric_port=36423
        )
        e2_term = E2TerminationPoint(config=config)

        def data_provider():
            return {
                "ue_id": "UE-001",
                "satellite_state": {
                    "satellite_id": "SAT-001",
                    "orbit_type": "LEO",
                    "beam_id": 1,
                    "elevation_angle": 45.0,
                    "azimuth_angle": 180.0,
                    "slant_range_km": 850.0,
                    "satellite_velocity": 7.5,
                    "angular_velocity": -0.5
                },
                "measurements": {"rsrp": -85.0, "rsrq": -12.0, "sinr": 15.0, "bler": 0.01}
            }

        e2_term.set_indication_data_provider(data_provider)
        await e2_term.connect_to_ric()
        await asyncio.sleep(0.5)

        # Create subscription
        from ric_integration.e2ap_messages import RICSubscriptionRequest

        event_trigger = E2SM_NTN.create_event_trigger(trigger_type=1, period_ms=10)
        sub_req = RICSubscriptionRequest(
            ric_request_id=1001,
            ran_function_id=E2SM_NTN.RAN_FUNCTION_ID,
            ric_event_trigger_definition=event_trigger,
            ric_actions=[{"id": 1, "type": "report"}]
        )
        await e2_term.handle_subscription_request(sub_req)

        # Send indications as fast as possible
        test_duration = 5.0  # 5 seconds
        start_time = time.time()
        num_sent = 0

        sub_id = list(e2_term.subscriptions.keys())[0]

        while time.time() - start_time < test_duration:
            await e2_term.send_indication(sub_id, data_provider())
            num_sent += 1

        elapsed = time.time() - start_time
        throughput = num_sent / elapsed

        # Cleanup
        await e2_term.stop()
        await ric.stop()

        return BenchmarkResult(
            name="Message Throughput",
            metric="throughput",
            value=throughput,
            unit="msg/sec",
            samples=num_sent,
            metadata={
                "total_messages": num_sent,
                "duration_sec": elapsed
            }
        )

    async def benchmark_e2e_latency(self) -> BenchmarkResult:
        """Benchmark end-to-end control loop latency"""
        logger.info("Benchmarking E2E control loop...")

        # Setup E2 connection
        ric = SimulatedRIC(port=36424)
        await ric.start()
        await asyncio.sleep(0.1)

        config = E2ConnectionConfig(
            ric_ip="127.0.0.1",
            ric_port=36424
        )
        e2_term = E2TerminationPoint(config=config)

        control_received_times = []

        def control_callback(control_msg):
            control_received_times.append(time.time())

        e2_term.set_control_callback(control_callback)

        await e2_term.connect_to_ric()
        await asyncio.sleep(0.5)

        # Send control requests and measure latency
        num_trials = 50
        e2e_latencies = []

        for _ in range(num_trials):
            control_sent_time = time.time()
            await ric.send_control_request("UE-001", "TRIGGER_HANDOVER")
            await asyncio.sleep(0.05)  # Wait for processing

            if control_received_times:
                latency = (control_received_times[-1] - control_sent_time) * 1000
                e2e_latencies.append(latency)

        # Cleanup
        await e2_term.stop()
        await ric.stop()

        return BenchmarkResult(
            name="E2E Control Loop",
            metric="e2e_latency",
            value=statistics.mean(e2e_latencies) if e2e_latencies else 0,
            unit="ms",
            samples=len(e2e_latencies),
            std_dev=statistics.stdev(e2e_latencies) if len(e2e_latencies) > 1 else 0,
            min_value=min(e2e_latencies) if e2e_latencies else 0,
            max_value=max(e2e_latencies) if e2e_latencies else 0
        )

    async def benchmark_resource_usage(self) -> List[BenchmarkResult]:
        """Benchmark CPU and memory usage"""
        logger.info("Benchmarking resource usage...")

        # Setup E2 connection
        ric = SimulatedRIC(port=36425)
        await ric.start()
        await asyncio.sleep(0.1)

        config = E2ConnectionConfig(
            ric_ip="127.0.0.1",
            ric_port=36425
        )
        e2_term = E2TerminationPoint(config=config)

        def data_provider():
            return {
                "ue_id": "UE-001",
                "satellite_state": {
                    "satellite_id": "SAT-001",
                    "orbit_type": "LEO",
                    "beam_id": 1,
                    "elevation_angle": 45.0,
                    "azimuth_angle": 180.0,
                    "slant_range_km": 850.0,
                    "satellite_velocity": 7.5,
                    "angular_velocity": -0.5
                },
                "measurements": {"rsrp": -85.0, "rsrq": -12.0, "sinr": 15.0, "bler": 0.01}
            }

        e2_term.set_indication_data_provider(data_provider)
        await e2_term.connect_to_ric()
        await asyncio.sleep(0.5)

        # Measure baseline
        baseline_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        baseline_cpu = self.process.cpu_percent(interval=0.1)

        # Create subscription and send indications
        from ric_integration.e2ap_messages import RICSubscriptionRequest

        event_trigger = E2SM_NTN.create_event_trigger(trigger_type=1, period_ms=100)
        sub_req = RICSubscriptionRequest(
            ric_request_id=1001,
            ran_function_id=E2SM_NTN.RAN_FUNCTION_ID,
            ric_event_trigger_definition=event_trigger,
            ric_actions=[{"id": 1, "type": "report"}]
        )
        await e2_term.handle_subscription_request(sub_req)

        # Send indications for 10 seconds
        sub_id = list(e2_term.subscriptions.keys())[0]
        start_time = time.time()

        cpu_samples = []
        mem_samples = []

        while time.time() - start_time < 10.0:
            await e2_term.send_indication(sub_id, data_provider())

            # Sample resources every 1 second
            if int((time.time() - start_time) * 10) % 10 == 0:
                cpu_samples.append(self.process.cpu_percent(interval=None))
                mem_samples.append(self.process.memory_info().rss / 1024 / 1024)

            await asyncio.sleep(0.1)

        # Cleanup
        await e2_term.stop()
        await ric.stop()

        results = [
            BenchmarkResult(
                name="Memory Usage",
                metric="memory",
                value=statistics.mean(mem_samples) if mem_samples else baseline_mem,
                unit="MB",
                samples=len(mem_samples),
                metadata={"baseline_mb": baseline_mem}
            ),
            BenchmarkResult(
                name="CPU Usage",
                metric="cpu",
                value=statistics.mean(cpu_samples) if cpu_samples else baseline_cpu,
                unit="%",
                samples=len(cpu_samples),
                metadata={"baseline_percent": baseline_cpu}
            )
        ]

        return results

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks"""
        logger.info("="*60)
        logger.info("STARTING RIC PERFORMANCE BENCHMARKS")
        logger.info("="*60)

        # Run benchmarks
        self.results.append(await self.benchmark_e2_setup())
        self.results.extend(await self.benchmark_indication_encoding())
        self.results.append(await self.benchmark_indication_transmission())
        self.results.append(await self.benchmark_throughput())
        self.results.append(await self.benchmark_e2e_latency())
        self.results.extend(await self.benchmark_resource_usage())

        # Generate report
        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate benchmark report"""
        report = {
            "timestamp": time.time(),
            "benchmarks": [
                {
                    "name": r.name,
                    "metric": r.metric,
                    "value": r.value,
                    "unit": r.unit,
                    "samples": r.samples,
                    "std_dev": r.std_dev,
                    "min": r.min_value,
                    "max": r.max_value,
                    "metadata": r.metadata
                }
                for r in self.results
            ]
        }

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK RESULTS")
        logger.info("="*60)

        for result in self.results:
            logger.info(f"{result.name:30s}: {result.value:8.2f} {result.unit}")
            if result.std_dev:
                logger.info(f"  {'Std Dev':28s}: {result.std_dev:8.2f} {result.unit}")
            if result.min_value is not None:
                logger.info(f"  {'Min/Max':28s}: {result.min_value:8.2f} / {result.max_value:8.2f} {result.unit}")

        logger.info("="*60)

        return report


async def main():
    """Main benchmark entry point"""
    benchmark = RICPerformanceBenchmark()
    report = await benchmark.run_all_benchmarks()

    # Save report
    report_file = "/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/ric_integration/benchmark_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nBenchmark report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
