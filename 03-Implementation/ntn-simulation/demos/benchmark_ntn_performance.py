#!/usr/bin/env python3
"""
NTN-O-RAN Performance Benchmarking
Measures system performance and latency metrics

Benchmarks:
1. Channel model calculation time (samples/sec)
2. E2 message encoding/decoding time
3. xApp decision latency
4. End-to-end loop time (measurement → decision → action)
5. Memory usage
6. CPU utilization
"""

import sys
import os
import time
import json
import asyncio
import psutil
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'openNTN_integration'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'e2_ntn_extension'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'xapps'))

from leo_channel import LEOChannelModel
from e2sm_ntn import E2SM_NTN, NTNControlAction
from ntn_e2_bridge import NTN_E2_Bridge
from ntn_handover_xapp import NTNHandoverXApp
from ntn_power_control_xapp import NTNPowerControlXApp


@dataclass
class BenchmarkResult:
    """Store benchmark results"""
    name: str
    mean_ms: float
    std_ms: float
    min_ms: float
    max_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    throughput_ops_per_sec: float
    sample_count: int


class NTNPerformanceBenchmark:
    """Performance benchmarking for NTN-O-RAN platform"""

    def __init__(self):
        """Initialize benchmarking"""
        print("="*80)
        print("NTN-O-RAN Performance Benchmarking")
        print("="*80)

        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()

        print("\nInitializing components...")

    def benchmark_channel_model(self, iterations: int = 1000) -> BenchmarkResult:
        """
        Benchmark OpenNTN channel model calculations

        Args:
            iterations: Number of iterations

        Returns:
            Benchmark result
        """
        print(f"\n[1/6] Benchmarking Channel Model ({iterations} iterations)...")

        leo_channel = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550.0,
            scenario='urban'
        )

        latencies = []
        elevation_angles = np.random.uniform(10, 90, iterations)

        for elev in elevation_angles:
            start = time.perf_counter()
            _ = leo_channel.calculate_link_budget(elevation_angle=elev)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        return self._calculate_statistics("Channel Model Calculation", latencies)

    def benchmark_e2_encoding(self, iterations: int = 1000) -> BenchmarkResult:
        """
        Benchmark E2 message encoding

        Args:
            iterations: Number of iterations

        Returns:
            Benchmark result
        """
        print(f"\n[2/6] Benchmarking E2 Message Encoding ({iterations} iterations)...")

        e2sm_ntn = E2SM_NTN()

        # Sample data
        satellite_state = {
            'satellite_id': 'SAT-LEO-001',
            'orbit_type': 'LEO',
            'beam_id': 1,
            'elevation_angle': 45.0,
            'azimuth_angle': 180.0,
            'slant_range_km': 800.0,
            'satellite_velocity': 7.5,
            'angular_velocity': -0.5,
            'carrier_frequency_ghz': 2.1,
            'doppler_rate': -45.0
        }

        measurements = {
            'rsrp': -85.0,
            'rsrq': -12.0,
            'sinr': 15.0,
            'bler': 0.01,
            'tx_power_dbm': 23.0
        }

        latencies = []

        for i in range(iterations):
            start = time.perf_counter()
            header, message = e2sm_ntn.create_indication_message(
                ue_id=f"UE-{i%100:03d}",
                satellite_state=satellite_state,
                ue_measurements=measurements
            )
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        return self._calculate_statistics("E2 Message Encoding", latencies)

    def benchmark_e2_decoding(self, iterations: int = 1000) -> BenchmarkResult:
        """
        Benchmark E2 message decoding

        Args:
            iterations: Number of iterations

        Returns:
            Benchmark result
        """
        print(f"\n[3/6] Benchmarking E2 Message Decoding ({iterations} iterations)...")

        e2sm_ntn = E2SM_NTN()

        # Create sample message
        satellite_state = {
            'satellite_id': 'SAT-LEO-001',
            'orbit_type': 'LEO',
            'beam_id': 1,
            'elevation_angle': 45.0,
            'azimuth_angle': 180.0,
            'slant_range_km': 800.0,
            'satellite_velocity': 7.5,
            'angular_velocity': -0.5,
            'carrier_frequency_ghz': 2.1,
            'doppler_rate': -45.0
        }

        measurements = {
            'rsrp': -85.0,
            'rsrq': -12.0,
            'sinr': 15.0,
            'bler': 0.01,
            'tx_power_dbm': 23.0
        }

        header, message = e2sm_ntn.create_indication_message(
            ue_id="UE-TEST-001",
            satellite_state=satellite_state,
            ue_measurements=measurements
        )

        latencies = []

        for _ in range(iterations):
            start = time.perf_counter()
            ntn_data = json.loads(message.decode('utf-8'))
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        return self._calculate_statistics("E2 Message Decoding", latencies)

    async def benchmark_xapp_handover(self, iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark handover xApp decision latency

        Args:
            iterations: Number of iterations

        Returns:
            Benchmark result
        """
        print(f"\n[4/6] Benchmarking Handover xApp ({iterations} iterations)...")

        xapp = NTNHandoverXApp(config={
            'handover_threshold_sec': 30.0,
            'min_elevation_deg': 10.0
        })
        await xapp.start()

        # Create sample indication
        ntn_data = {
            'timestamp_ns': int(time.time() * 1e9),
            'ue_id': 'UE-BENCH-001',
            'satellite_metrics': {
                'satellite_id': 'SAT-LEO-001',
                'orbit_type': 'LEO',
                'beam_id': 1,
                'elevation_angle': 15.0,
                'azimuth_angle': 180.0,
                'slant_range_km': 800.0,
                'satellite_velocity': 7.5,
                'angular_velocity': -0.5
            },
            'channel_quality': {
                'rsrp': -85.0,
                'rsrq': -12.0,
                'sinr': 15.0,
                'bler': 0.01,
                'cqi': 12
            },
            'ntn_impairments': {
                'doppler_shift_hz': 15000.0,
                'doppler_rate_hz_s': -45.0,
                'propagation_delay_ms': 2.67,
                'path_loss_db': 165.0,
                'rain_attenuation_db': 0.0,
                'atmospheric_loss_db': 0.5
            },
            'link_budget': {
                'tx_power_dbm': 23.0,
                'rx_power_dbm': -85.0,
                'link_margin_db': 25.0,
                'snr_db': 15.0,
                'required_snr_db': 9.0
            },
            'handover_prediction': {
                'time_to_handover_sec': 25.0,
                'handover_trigger_threshold': 10.0,
                'next_satellite_id': 'SAT-LEO-002',
                'next_satellite_elevation': 50.0,
                'handover_probability': 0.95
            },
            'performance': {
                'throughput_dl_mbps': 50.0,
                'throughput_ul_mbps': 10.0,
                'latency_rtt_ms': 10.0,
                'packet_loss_rate': 0.01
            }
        }

        indication_msg = json.dumps(ntn_data).encode('utf-8')
        indication_hdr = json.dumps({'timestamp_ns': ntn_data['timestamp_ns']}).encode('utf-8')

        latencies = []

        for _ in range(iterations):
            start = time.perf_counter()
            await xapp.on_indication(indication_hdr, indication_msg)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        await xapp.stop()

        return self._calculate_statistics("Handover xApp Decision", latencies)

    async def benchmark_xapp_power(self, iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark power control xApp decision latency

        Args:
            iterations: Number of iterations

        Returns:
            Benchmark result
        """
        print(f"\n[5/6] Benchmarking Power Control xApp ({iterations} iterations)...")

        xapp = NTNPowerControlXApp(config={
            'target_margin_db': 10.0,
            'margin_tolerance_db': 3.0
        })
        await xapp.start()

        # Create sample indication
        ntn_data = {
            'timestamp_ns': int(time.time() * 1e9),
            'ue_id': 'UE-BENCH-002',
            'satellite_metrics': {
                'satellite_id': 'SAT-LEO-001',
                'orbit_type': 'LEO',
                'beam_id': 1,
                'elevation_angle': 45.0,
                'azimuth_angle': 180.0,
                'slant_range_km': 800.0,
                'satellite_velocity': 7.5,
                'angular_velocity': -0.5
            },
            'channel_quality': {
                'rsrp': -85.0,
                'rsrq': -12.0,
                'sinr': 15.0,
                'bler': 0.01,
                'cqi': 12
            },
            'ntn_impairments': {
                'doppler_shift_hz': 15000.0,
                'doppler_rate_hz_s': -45.0,
                'propagation_delay_ms': 2.67,
                'path_loss_db': 165.0,
                'rain_attenuation_db': 0.0,
                'atmospheric_loss_db': 0.5
            },
            'link_budget': {
                'tx_power_dbm': 23.0,
                'rx_power_dbm': -85.0,
                'link_margin_db': 18.0,  # Excessive margin
                'snr_db': 15.0,
                'required_snr_db': 9.0
            },
            'handover_prediction': {
                'time_to_handover_sec': 120.0,
                'handover_trigger_threshold': 10.0,
                'next_satellite_id': 'SAT-LEO-002',
                'next_satellite_elevation': 45.0,
                'handover_probability': 0.5
            },
            'performance': {
                'throughput_dl_mbps': 50.0,
                'throughput_ul_mbps': 10.0,
                'latency_rtt_ms': 10.0,
                'packet_loss_rate': 0.01
            }
        }

        indication_msg = json.dumps(ntn_data).encode('utf-8')
        indication_hdr = json.dumps({'timestamp_ns': ntn_data['timestamp_ns']}).encode('utf-8')

        latencies = []

        for _ in range(iterations):
            start = time.perf_counter()
            await xapp.on_indication(indication_hdr, indication_msg)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        await xapp.stop()

        return self._calculate_statistics("Power Control xApp Decision", latencies)

    async def benchmark_end_to_end(self, iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark end-to-end loop (measurement → decision → action)

        Args:
            iterations: Number of iterations

        Returns:
            Benchmark result
        """
        print(f"\n[6/6] Benchmarking End-to-End Loop ({iterations} iterations)...")

        # Initialize components
        bridge = NTN_E2_Bridge(orbit_type='LEO', carrier_frequency_ghz=2.0)
        handover_xapp = NTNHandoverXApp()
        power_xapp = NTNPowerControlXApp()

        await handover_xapp.start()
        await power_xapp.start()

        # Register UE
        bridge.register_ue(ue_id="UE-E2E-001", lat=45.0, lon=-93.0, altitude_m=300.0)

        latencies = []

        for _ in range(iterations):
            # Measurement generation
            measurements = {
                'rsrp': -85.0,
                'rsrq': -12.0,
                'sinr': 15.0,
                'bler': 0.01,
                'tx_power_dbm': 23.0
            }

            start = time.perf_counter()

            # Generate E2 Indication
            header, message = bridge.process_ue_report(
                ue_id="UE-E2E-001",
                measurements=measurements,
                satellite_lat=0.0,
                satellite_lon=-93.0
            )

            # Process in xApps
            await handover_xapp.on_indication(header, message)
            await power_xapp.on_indication(header, message)

            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        await handover_xapp.stop()
        await power_xapp.stop()

        return self._calculate_statistics("End-to-End Loop", latencies)

    def benchmark_memory_usage(self) -> Dict[str, float]:
        """
        Measure memory usage

        Returns:
            Memory usage statistics
        """
        print("\n[Bonus] Measuring Memory Usage...")

        mem_info = self.process.memory_info()

        usage = {
            'rss_mb': mem_info.rss / (1024 * 1024),  # Resident Set Size
            'vms_mb': mem_info.vms / (1024 * 1024),  # Virtual Memory Size
            'percent': self.process.memory_percent()
        }

        print(f"  RSS: {usage['rss_mb']:.1f} MB")
        print(f"  VMS: {usage['vms_mb']:.1f} MB")
        print(f"  Percent: {usage['percent']:.2f}%")

        return usage

    def _calculate_statistics(self, name: str, latencies_ms: List[float]) -> BenchmarkResult:
        """Calculate benchmark statistics"""
        latencies_array = np.array(latencies_ms)

        result = BenchmarkResult(
            name=name,
            mean_ms=float(np.mean(latencies_array)),
            std_ms=float(np.std(latencies_array)),
            min_ms=float(np.min(latencies_array)),
            max_ms=float(np.max(latencies_array)),
            median_ms=float(np.median(latencies_array)),
            p95_ms=float(np.percentile(latencies_array, 95)),
            p99_ms=float(np.percentile(latencies_array, 99)),
            throughput_ops_per_sec=1000.0 / np.mean(latencies_array),
            sample_count=len(latencies_ms)
        )

        self.results.append(result)

        print(f"  Mean: {result.mean_ms:.3f} ms")
        print(f"  Median: {result.median_ms:.3f} ms")
        print(f"  P95: {result.p95_ms:.3f} ms")
        print(f"  P99: {result.p99_ms:.3f} ms")
        print(f"  Throughput: {result.throughput_ops_per_sec:.0f} ops/sec")

        return result

    def print_summary(self, target_latency_ms: float = 10.0):
        """
        Print benchmark summary

        Args:
            target_latency_ms: Target latency threshold
        """
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)

        print(f"\nTarget Latency: < {target_latency_ms} ms\n")

        print(f"{'Benchmark':<30} {'Mean (ms)':<12} {'P95 (ms)':<12} {'P99 (ms)':<12} {'Status':<10}")
        print("-"*80)

        for result in self.results:
            status = "PASS" if result.p99_ms < target_latency_ms else "FAIL"
            status_symbol = "✓" if status == "PASS" else "✗"

            print(f"{result.name:<30} {result.mean_ms:<12.3f} {result.p95_ms:<12.3f} " +
                  f"{result.p99_ms:<12.3f} {status_symbol} {status:<10}")

        print("-"*80)

        # Overall status
        all_pass = all(r.p99_ms < target_latency_ms for r in self.results)
        overall_status = "ALL BENCHMARKS PASSED" if all_pass else "SOME BENCHMARKS FAILED"
        print(f"\nOverall: {overall_status}")

        print("\n" + "="*80 + "\n")

    def save_results(self, output_path: str):
        """Save benchmark results to JSON"""
        results_dict = {
            'timestamp': time.time(),
            'target_latency_ms': 10.0,
            'benchmarks': [
                {
                    'name': r.name,
                    'mean_ms': r.mean_ms,
                    'std_ms': r.std_ms,
                    'min_ms': r.min_ms,
                    'max_ms': r.max_ms,
                    'median_ms': r.median_ms,
                    'p95_ms': r.p95_ms,
                    'p99_ms': r.p99_ms,
                    'throughput_ops_per_sec': r.throughput_ops_per_sec,
                    'sample_count': r.sample_count,
                    'pass': r.p99_ms < 10.0
                }
                for r in self.results
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"Results saved to: {output_path}")

    def generate_plots(self, output_path: str):
        """Generate benchmark visualization"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Plot 1: Latency comparison
        names = [r.name for r in self.results]
        means = [r.mean_ms for r in self.results]
        p95s = [r.p95_ms for r in self.results]
        p99s = [r.p99_ms for r in self.results]

        x = np.arange(len(names))
        width = 0.25

        ax1.bar(x - width, means, width, label='Mean', alpha=0.8)
        ax1.bar(x, p95s, width, label='P95', alpha=0.8)
        ax1.bar(x + width, p99s, width, label='P99', alpha=0.8)

        ax1.axhline(y=10.0, color='r', linestyle='--', linewidth=2, label='Target (10ms)')

        ax1.set_xlabel('Benchmark')
        ax1.set_ylabel('Latency (ms)')
        ax1.set_title('NTN-O-RAN Performance Benchmarks')
        ax1.set_xticks(x)
        ax1.set_xticklabels([n.replace(' ', '\n') for n in names], fontsize=8)
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')

        # Plot 2: Throughput
        throughputs = [r.throughput_ops_per_sec for r in self.results]

        ax2.bar(names, throughputs, alpha=0.8, color='green')
        ax2.set_xlabel('Benchmark')
        ax2.set_ylabel('Throughput (ops/sec)')
        ax2.set_title('Operation Throughput')
        ax2.set_xticklabels([n.replace(' ', '\n') for n in names], fontsize=8, rotation=0)
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plots saved to: {output_path}")
        plt.close()


async def main():
    """Main benchmark function"""
    print("\n" + "="*80)
    print("NTN-O-RAN Platform - Performance Benchmarking")
    print("="*80 + "\n")

    benchmark = NTNPerformanceBenchmark()

    # Run benchmarks
    benchmark.benchmark_channel_model(iterations=1000)
    benchmark.benchmark_e2_encoding(iterations=1000)
    benchmark.benchmark_e2_decoding(iterations=1000)
    await benchmark.benchmark_xapp_handover(iterations=100)
    await benchmark.benchmark_xapp_power(iterations=100)
    await benchmark.benchmark_end_to_end(iterations=100)

    # Memory usage
    memory_usage = benchmark.benchmark_memory_usage()

    # Print summary
    benchmark.print_summary(target_latency_ms=10.0)

    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'demo_results')
    os.makedirs(output_dir, exist_ok=True)

    results_path = os.path.join(output_dir, 'benchmark_results.json')
    plots_path = os.path.join(output_dir, 'benchmark_plots.png')

    benchmark.save_results(results_path)
    benchmark.generate_plots(plots_path)

    print("\nBenchmarking complete!")


if __name__ == '__main__':
    asyncio.run(main())
