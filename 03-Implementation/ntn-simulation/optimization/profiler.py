#!/usr/bin/env python3
"""
NTN Performance Profiler
========================

Comprehensive performance profiling for all NTN-O-RAN platform components:
- SGP4 orbit propagation
- ITU-R P.618 weather calculations
- ASN.1 PER encoding/decoding
- E2 message pipeline
- Database operations

Identifies bottlenecks and generates performance flamegraphs.

Author: Performance Optimization & Profiling Specialist
Date: 2025-11-17
"""

import cProfile
import pstats
import io
import time
import sys
import os
import json
import statistics
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
import tracemalloc

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orbit_propagation.sgp4_propagator import SGP4Propagator
from orbit_propagation.tle_manager import TLEManager
from weather.itur_p618 import ITUR_P618_RainAttenuation
from e2_ntn_extension.asn1_codec import E2SM_NTN_ASN1_Codec


@dataclass
class ProfileResult:
    """Single profiling result"""
    component: str
    operation: str
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p50_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    std_dev_ms: float
    iterations: int
    total_time_ms: float
    throughput_ops_sec: float
    memory_delta_mb: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class NTNPerformanceProfiler:
    """
    Comprehensive performance profiler for NTN-O-RAN platform

    Profiles all major components and identifies bottlenecks:
    - SGP4 propagation and coordinate transforms
    - Weather calculation (ITU-R P.618)
    - ASN.1 encoding/decoding
    - E2 message pipeline
    - End-to-end latency breakdown
    """

    def __init__(self):
        """Initialize profiler"""
        self.results: List[ProfileResult] = []
        self.profile_data: Dict[str, Any] = {}

        print("="*70)
        print("NTN Performance Profiler Initialized")
        print("="*70)

    def _measure_operation(
        self,
        operation_func,
        iterations: int = 1000,
        measure_memory: bool = False
    ) -> Tuple[List[float], Optional[float]]:
        """
        Measure operation performance

        Args:
            operation_func: Function to measure
            iterations: Number of iterations
            measure_memory: Whether to measure memory usage

        Returns:
            Tuple of (execution times in ms, memory delta in MB)
        """
        times = []
        memory_delta = None

        # Warmup
        for _ in range(10):
            operation_func()

        # Start memory tracking if requested
        if measure_memory:
            tracemalloc.start()
            snapshot_before = tracemalloc.take_snapshot()

        # Measure iterations
        for _ in range(iterations):
            start = time.perf_counter()
            operation_func()
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(elapsed)

        # Measure memory if requested
        if measure_memory:
            snapshot_after = tracemalloc.take_snapshot()
            top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
            memory_delta = sum(stat.size_diff for stat in top_stats) / 1024 / 1024  # MB
            tracemalloc.stop()

        return times, memory_delta

    def _create_profile_result(
        self,
        component: str,
        operation: str,
        times: List[float],
        memory_delta: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProfileResult:
        """Create ProfileResult from timing data"""
        total_time = sum(times)
        iterations = len(times)

        return ProfileResult(
            component=component,
            operation=operation,
            avg_time_ms=statistics.mean(times),
            min_time_ms=min(times),
            max_time_ms=max(times),
            p50_time_ms=np.percentile(times, 50),
            p95_time_ms=np.percentile(times, 95),
            p99_time_ms=np.percentile(times, 99),
            std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0.0,
            iterations=iterations,
            total_time_ms=total_time,
            throughput_ops_sec=iterations / (total_time / 1000) if total_time > 0 else 0,
            memory_delta_mb=memory_delta,
            metadata=metadata or {}
        )

    def profile_sgp4_propagation(self, iterations: int = 10000) -> List[ProfileResult]:
        """
        Profile SGP4 orbit propagation components

        Profiles:
        - SGP4 propagation (ECI position/velocity)
        - ECI to ECEF coordinate transform
        - Geodetic to ECEF conversion
        - Look angle calculation
        - Doppler shift calculation
        - Complete ground track calculation

        Args:
            iterations: Number of profiling iterations

        Returns:
            List of ProfileResult objects
        """
        print(f"\nProfiling SGP4 Propagation ({iterations} iterations)...")

        results = []

        # Initialize SGP4
        manager = TLEManager()
        tles = manager.fetch_starlink_tles(limit=1)
        if not tles:
            print("Error: No TLE data available")
            return results

        propagator = SGP4Propagator(tles[0])
        timestamp = datetime.utcnow()

        # Test coordinates (Taipei)
        lat, lon, alt = 25.0330, 121.5654, 0.0

        # Profile 1: SGP4 Propagation Only
        def sgp4_propagate():
            propagator.propagate(timestamp)

        times, memory = self._measure_operation(sgp4_propagate, iterations, measure_memory=True)
        results.append(self._create_profile_result(
            "SGP4",
            "propagate (ECI position/velocity)",
            times,
            memory,
            {"description": "Core SGP4 algorithm"}
        ))

        # Profile 2: ECI to ECEF Transform
        pos_eci, vel_eci = propagator.propagate(timestamp)

        def eci_to_ecef():
            propagator.eci_to_ecef(pos_eci, timestamp)

        times, _ = self._measure_operation(eci_to_ecef, iterations)
        results.append(self._create_profile_result(
            "SGP4",
            "eci_to_ecef (coordinate transform)",
            times,
            metadata={"description": "ECI to ECEF rotation matrix"}
        ))

        # Profile 3: Geodetic to ECEF
        def geodetic_to_ecef():
            propagator.geodetic_to_ecef(lat, lon, alt)

        times, _ = self._measure_operation(geodetic_to_ecef, iterations)
        results.append(self._create_profile_result(
            "SGP4",
            "geodetic_to_ecef (observer position)",
            times,
            metadata={"description": "WGS84 geodetic conversion"}
        ))

        # Profile 4: Look Angles Calculation
        sat_pos_ecef = propagator.eci_to_ecef(pos_eci, timestamp)
        observer_pos_ecef = propagator.geodetic_to_ecef(lat, lon, alt)

        def calculate_look_angles():
            propagator.calculate_look_angles(sat_pos_ecef, observer_pos_ecef, lat, lon)

        times, _ = self._measure_operation(calculate_look_angles, iterations)
        results.append(self._create_profile_result(
            "SGP4",
            "calculate_look_angles (elevation/azimuth)",
            times,
            metadata={"description": "ECEF to topocentric SEZ conversion"}
        ))

        # Profile 5: Doppler Shift Calculation
        def calculate_doppler():
            propagator.calculate_doppler(sat_pos_ecef, vel_eci, observer_pos_ecef, timestamp)

        times, _ = self._measure_operation(calculate_doppler, iterations)
        results.append(self._create_profile_result(
            "SGP4",
            "calculate_doppler (frequency shift)",
            times,
            metadata={"description": "Radial velocity calculation"}
        ))

        # Profile 6: Complete Ground Track (E2E)
        def get_ground_track():
            propagator.get_ground_track(lat, lon, alt, timestamp)

        times, memory = self._measure_operation(get_ground_track, iterations, measure_memory=True)
        results.append(self._create_profile_result(
            "SGP4",
            "get_ground_track (complete E2E)",
            times,
            memory,
            {"description": "Full satellite geometry calculation"}
        ))

        # Print summary
        print(f"  Completed SGP4 profiling: {len(results)} operations")
        for result in results:
            print(f"    {result.operation:40s}: {result.avg_time_ms:.4f} ms (avg)")

        return results

    def profile_weather_calculation(self, iterations: int = 10000) -> List[ProfileResult]:
        """
        Profile ITU-R P.618 weather calculations

        Profiles:
        - Rain attenuation calculation
        - Rain rate lookup
        - Specific attenuation coefficients
        - Effective path length
        - Cloud attenuation
        - Atmospheric gases attenuation
        - Total atmospheric loss

        Args:
            iterations: Number of profiling iterations

        Returns:
            List of ProfileResult objects
        """
        print(f"\nProfiling Weather Calculation ({iterations} iterations)...")

        results = []

        # Initialize ITU-R P.618
        itur = ITUR_P618_RainAttenuation()

        # Test parameters
        lat, lon = 40.7128, -74.0060  # New York
        frequency_ghz = 20.0  # Ka-band
        elevation_angle = 30.0
        polarization = 'circular'

        # Profile 1: Rain Rate Lookup
        def get_rain_rate():
            itur.get_rain_rate(lat, lon, 0.01)

        times, _ = self._measure_operation(get_rain_rate, iterations)
        results.append(self._create_profile_result(
            "Weather",
            "get_rain_rate (ITU-R P.837)",
            times,
            metadata={"description": "Rain rate statistics lookup"}
        ))

        # Profile 2: Specific Attenuation Coefficients
        rain_rate = itur.get_rain_rate(lat, lon, 0.01)

        def calculate_specific_attenuation():
            itur.calculate_specific_attenuation(frequency_ghz, rain_rate, elevation_angle, polarization)

        times, _ = self._measure_operation(calculate_specific_attenuation, iterations)
        results.append(self._create_profile_result(
            "Weather",
            "calculate_specific_attenuation (ITU-R P.838)",
            times,
            metadata={"description": "k and alpha coefficients"}
        ))

        # Profile 3: Complete Rain Attenuation
        def calculate_rain_attenuation():
            itur.calculate_rain_attenuation(lat, lon, frequency_ghz, elevation_angle, polarization)

        times, memory = self._measure_operation(calculate_rain_attenuation, iterations, measure_memory=True)
        results.append(self._create_profile_result(
            "Weather",
            "calculate_rain_attenuation (complete)",
            times,
            memory,
            {"description": "Full ITU-R P.618 model"}
        ))

        # Profile 4: Cloud Attenuation
        def calculate_cloud_attenuation():
            itur.calculate_cloud_attenuation(frequency_ghz, elevation_angle)

        times, _ = self._measure_operation(calculate_cloud_attenuation, iterations)
        results.append(self._create_profile_result(
            "Weather",
            "calculate_cloud_attenuation (ITU-R P.840)",
            times,
            metadata={"description": "Cloud liquid water model"}
        ))

        # Profile 5: Atmospheric Gases
        def calculate_gas_attenuation():
            itur.calculate_atmospheric_gases_attenuation(frequency_ghz, elevation_angle)

        times, _ = self._measure_operation(calculate_gas_attenuation, iterations)
        results.append(self._create_profile_result(
            "Weather",
            "calculate_atmospheric_gases (ITU-R P.676)",
            times,
            metadata={"description": "Oxygen and water vapor"}
        ))

        # Profile 6: Total Atmospheric Loss
        def get_total_atmospheric_loss():
            itur.get_total_atmospheric_loss(lat, lon, frequency_ghz, elevation_angle, polarization)

        times, memory = self._measure_operation(get_total_atmospheric_loss, iterations, measure_memory=True)
        results.append(self._create_profile_result(
            "Weather",
            "get_total_atmospheric_loss (E2E)",
            times,
            memory,
            {"description": "Rain + cloud + gases"}
        ))

        # Print summary
        print(f"  Completed Weather profiling: {len(results)} operations")
        for result in results:
            print(f"    {result.operation:45s}: {result.avg_time_ms:.4f} ms (avg)")

        return results

    def profile_asn1_encoding(self, iterations: int = 10000) -> List[ProfileResult]:
        """
        Profile ASN.1 PER encoding/decoding

        Profiles:
        - Schema compilation
        - Indication message encoding
        - Indication message decoding
        - Control message encoding
        - Control message decoding
        - Message validation

        Args:
            iterations: Number of profiling iterations

        Returns:
            List of ProfileResult objects
        """
        print(f"\nProfiling ASN.1 Encoding ({iterations} iterations)...")

        results = []

        # Initialize codec
        codec = E2SM_NTN_ASN1_Codec()

        # Create test message
        test_message = {
            'timestamp_ns': int(time.time() * 1e9),
            'ue_id': 'UE-PROFILE-001',
            'satellite_metrics': {
                'satellite_id': 'SAT-LEO-001',
                'orbit_type': 'LEO',
                'beam_id': 1,
                'elevation_angle': 45.0,
                'azimuth_angle': 180.0,
                'slant_range_km': 850.0,
                'satellite_velocity': 7.5,
                'angular_velocity': -0.5
            },
            'channel_quality': {
                'rsrp': -85.0,
                'rsrq': -12.0,
                'sinr': 15.0,
                'bler': 0.01,
                'cqi': 10
            },
            'ntn_impairments': {
                'doppler_shift_hz': 25000.0,
                'doppler_rate_hz_s': 50.0,
                'propagation_delay_ms': 2.8,
                'path_loss_db': 165.0,
                'rain_attenuation_db': 0.5,
                'atmospheric_loss_db': 1.0
            },
            'link_budget': {
                'tx_power_dbm': 23.0,
                'rx_power_dbm': -85.0,
                'link_margin_db': 12.0,
                'snr_db': 15.0,
                'required_snr_db': 8.0
            },
            'handover_prediction': {
                'time_to_handover_sec': 120.0,
                'handover_trigger_threshold': 10.0,
                'next_satellite_id': 'SAT-LEO-002',
                'next_satellite_elevation': 10.0,
                'handover_probability': 0.75
            },
            'performance': {
                'throughput_dl_mbps': 80.0,
                'throughput_ul_mbps': 15.0,
                'latency_rtt_ms': 12.5,
                'packet_loss_rate': 0.005
            }
        }

        # Profile 1: Indication Message Encoding
        def encode_indication():
            codec.encode_indication_message(test_message)

        times, memory = self._measure_operation(encode_indication, iterations, measure_memory=True)
        encoded_msg, _ = codec.encode_indication_message(test_message)
        results.append(self._create_profile_result(
            "ASN.1",
            "encode_indication_message (PER)",
            times,
            memory,
            {"description": "Full message to ASN.1 PER", "avg_size_bytes": len(encoded_msg)}
        ))

        # Profile 2: Indication Message Decoding
        def decode_indication():
            codec.decode_indication_message(encoded_msg)

        times, _ = self._measure_operation(decode_indication, iterations)
        results.append(self._create_profile_result(
            "ASN.1",
            "decode_indication_message (PER)",
            times,
            metadata={"description": "ASN.1 PER to Python dict"}
        ))

        # Profile 3: Control Message Encoding
        control_msg = {
            'actionType': 'POWER_CONTROL',
            'ue_id': 'UE-001',
            'parameters': {
                'target_tx_power_dbm': 20.0,
                'power_adjustment_db': -3.0,
                'reason': 'CHANNEL_QUALITY'
            }
        }

        def encode_control():
            codec.encode_control_message(control_msg)

        times, _ = self._measure_operation(encode_control, iterations)
        encoded_control, _ = codec.encode_control_message(control_msg)
        results.append(self._create_profile_result(
            "ASN.1",
            "encode_control_message (PER)",
            times,
            metadata={"description": "Control action encoding", "avg_size_bytes": len(encoded_control)}
        ))

        # Profile 4: Control Message Decoding
        def decode_control():
            codec.decode_control_message(encoded_control)

        times, _ = self._measure_operation(decode_control, iterations)
        results.append(self._create_profile_result(
            "ASN.1",
            "decode_control_message (PER)",
            times,
            metadata={"description": "Control action decoding"}
        ))

        # Profile 5: Message Validation
        def validate_message():
            codec.validate_message('indication_format1', test_message)

        times, _ = self._measure_operation(validate_message, iterations)
        results.append(self._create_profile_result(
            "ASN.1",
            "validate_message (schema check)",
            times,
            metadata={"description": "Message validation against schema"}
        ))

        # Print summary
        print(f"  Completed ASN.1 profiling: {len(results)} operations")
        for result in results:
            print(f"    {result.operation:45s}: {result.avg_time_ms:.4f} ms (avg)")

        return results

    def profile_e2_pipeline(self, num_ues: int = 100) -> List[ProfileResult]:
        """
        Profile complete E2 pipeline for multiple UEs

        Simulates end-to-end processing:
        - SGP4 propagation for UE
        - Weather calculation for UE
        - ASN.1 encoding
        - Total E2E latency

        Args:
            num_ues: Number of UEs to simulate

        Returns:
            List of ProfileResult objects
        """
        print(f"\nProfiling E2 Pipeline ({num_ues} UEs)...")

        results = []

        # Initialize components
        manager = TLEManager()
        tles = manager.fetch_starlink_tles(limit=1)
        if not tles:
            print("Error: No TLE data available")
            return results

        propagator = SGP4Propagator(tles[0])
        itur = ITUR_P618_RainAttenuation()
        codec = E2SM_NTN_ASN1_Codec()

        timestamp = datetime.utcnow()

        # Simulate UEs at different locations
        ue_locations = [
            (25.0330 + i * 0.01, 121.5654 + i * 0.01, 0.0)
            for i in range(num_ues)
        ]

        # Profile: Complete E2E Pipeline per UE
        pipeline_times = []
        sgp4_times = []
        weather_times = []
        encoding_times = []

        for lat, lon, alt in ue_locations:
            # Time SGP4
            start = time.perf_counter()
            geometry = propagator.get_ground_track(lat, lon, alt, timestamp)
            sgp4_time = (time.perf_counter() - start) * 1000
            sgp4_times.append(sgp4_time)

            # Time Weather
            start = time.perf_counter()
            weather_loss = itur.calculate_rain_attenuation(
                lat, lon, 20.0, geometry['elevation_deg'], 'circular'
            )
            weather_time = (time.perf_counter() - start) * 1000
            weather_times.append(weather_time)

            # Create message
            ntn_message = {
                'timestamp_ns': int(time.time() * 1e9),
                'ue_id': f'UE-{lat:.4f}-{lon:.4f}',
                'satellite_metrics': {
                    'satellite_id': geometry['satellite_id'],
                    'orbit_type': 'LEO',
                    'beam_id': 1,
                    'elevation_angle': geometry['elevation_deg'],
                    'azimuth_angle': geometry['azimuth_deg'],
                    'slant_range_km': geometry['slant_range_km'],
                    'satellite_velocity': geometry['satellite_velocity_kmps'],
                    'angular_velocity': 0.5
                },
                'channel_quality': {
                    'rsrp': -85.0,
                    'rsrq': -12.0,
                    'sinr': 15.0,
                    'bler': 0.01,
                    'cqi': 10
                },
                'ntn_impairments': {
                    'doppler_shift_hz': geometry['doppler_shift_hz'],
                    'doppler_rate_hz_s': 50.0,
                    'propagation_delay_ms': geometry['slant_range_km'] / 299.792,
                    'path_loss_db': 165.0,
                    'rain_attenuation_db': weather_loss.exceeded_0_01_percent,
                    'atmospheric_loss_db': 1.0
                },
                'link_budget': {
                    'tx_power_dbm': 23.0,
                    'rx_power_dbm': -85.0,
                    'link_margin_db': 12.0,
                    'snr_db': 15.0,
                    'required_snr_db': 8.0
                },
                'handover_prediction': {
                    'time_to_handover_sec': 120.0,
                    'handover_trigger_threshold': 10.0,
                    'next_satellite_id': 'SAT-LEO-002',
                    'next_satellite_elevation': 10.0,
                    'handover_probability': 0.75
                },
                'performance': {
                    'throughput_dl_mbps': 80.0,
                    'throughput_ul_mbps': 15.0,
                    'latency_rtt_ms': 12.5,
                    'packet_loss_rate': 0.005
                }
            }

            # Time ASN.1 Encoding
            start = time.perf_counter()
            encoded_msg, _ = codec.encode_indication_message(ntn_message)
            encoding_time = (time.perf_counter() - start) * 1000
            encoding_times.append(encoding_time)

            # Total pipeline time
            pipeline_times.append(sgp4_time + weather_time + encoding_time)

        # Create results
        results.append(self._create_profile_result(
            "E2 Pipeline",
            "sgp4_component (per UE)",
            sgp4_times,
            metadata={"description": "SGP4 propagation time"}
        ))

        results.append(self._create_profile_result(
            "E2 Pipeline",
            "weather_component (per UE)",
            weather_times,
            metadata={"description": "Weather calculation time"}
        ))

        results.append(self._create_profile_result(
            "E2 Pipeline",
            "asn1_encoding_component (per UE)",
            encoding_times,
            metadata={"description": "ASN.1 encoding time"}
        ))

        results.append(self._create_profile_result(
            "E2 Pipeline",
            "complete_e2e_latency (per UE)",
            pipeline_times,
            metadata={
                "description": "Total E2E processing time",
                "num_ues": num_ues,
                "breakdown": {
                    "sgp4_pct": (sum(sgp4_times) / sum(pipeline_times) * 100),
                    "weather_pct": (sum(weather_times) / sum(pipeline_times) * 100),
                    "encoding_pct": (sum(encoding_times) / sum(pipeline_times) * 100)
                }
            }
        ))

        # Print summary
        print(f"  Completed E2 Pipeline profiling: {num_ues} UEs")
        for result in results:
            print(f"    {result.operation:45s}: {result.avg_time_ms:.4f} ms (avg)")

        return results

    def run_all_profiles(self) -> Dict[str, Any]:
        """
        Run all profiling benchmarks

        Returns:
            Dictionary containing all profiling results
        """
        print("\n" + "="*70)
        print("STARTING COMPREHENSIVE PERFORMANCE PROFILING")
        print("="*70)

        # Profile all components
        self.results.extend(self.profile_sgp4_propagation(iterations=10000))
        self.results.extend(self.profile_weather_calculation(iterations=10000))
        self.results.extend(self.profile_asn1_encoding(iterations=10000))
        self.results.extend(self.profile_e2_pipeline(num_ues=100))

        # Generate report
        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive profiling report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_operations_profiled": len(self.results),
                "components": list(set(r.component for r in self.results))
            },
            "results": [
                {
                    "component": r.component,
                    "operation": r.operation,
                    "avg_time_ms": r.avg_time_ms,
                    "p50_time_ms": r.p50_time_ms,
                    "p95_time_ms": r.p95_time_ms,
                    "p99_time_ms": r.p99_time_ms,
                    "std_dev_ms": r.std_dev_ms,
                    "min_time_ms": r.min_time_ms,
                    "max_time_ms": r.max_time_ms,
                    "throughput_ops_sec": r.throughput_ops_sec,
                    "iterations": r.iterations,
                    "memory_delta_mb": r.memory_delta_mb,
                    "metadata": r.metadata
                }
                for r in self.results
            ],
            "bottlenecks": self._identify_bottlenecks()
        }

        # Print summary
        self._print_summary(report)

        return report

    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        # Sort by average time (descending)
        sorted_results = sorted(self.results, key=lambda r: r.avg_time_ms, reverse=True)

        bottlenecks = []
        for result in sorted_results[:10]:  # Top 10 slowest operations
            bottlenecks.append({
                "component": result.component,
                "operation": result.operation,
                "avg_time_ms": result.avg_time_ms,
                "throughput_ops_sec": result.throughput_ops_sec,
                "severity": "high" if result.avg_time_ms > 0.1 else "medium" if result.avg_time_ms > 0.05 else "low"
            })

        return bottlenecks

    def _print_summary(self, report: Dict[str, Any]):
        """Print profiling summary"""
        print("\n" + "="*70)
        print("PROFILING RESULTS SUMMARY")
        print("="*70)

        # Group by component
        by_component = {}
        for result in self.results:
            if result.component not in by_component:
                by_component[result.component] = []
            by_component[result.component].append(result)

        # Print results by component
        for component, results in by_component.items():
            print(f"\n{component} Component:")
            print("-" * 70)
            print(f"{'Operation':<45} {'Avg (ms)':<12} {'P95 (ms)':<12} {'Ops/sec':<12}")
            print("-" * 70)

            for result in results:
                print(f"{result.operation[:44]:<45} {result.avg_time_ms:<12.4f} "
                      f"{result.p95_time_ms:<12.4f} {result.throughput_ops_sec:<12.0f}")

        # Print bottlenecks
        print("\n" + "="*70)
        print("TOP 10 BOTTLENECKS (Slowest Operations)")
        print("="*70)
        print(f"{'Rank':<6} {'Component':<15} {'Operation':<35} {'Avg Time (ms)':<15}")
        print("-" * 70)

        for i, bottleneck in enumerate(report['bottlenecks'], 1):
            print(f"{i:<6} {bottleneck['component']:<15} {bottleneck['operation'][:34]:<35} "
                  f"{bottleneck['avg_time_ms']:<15.4f}")

        print("="*70)

    def save_report(self, filename: str = "profiling_report.json"):
        """Save profiling report to file"""
        report = self.generate_report()

        output_path = os.path.join(
            os.path.dirname(__file__),
            filename
        )

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nProfiling report saved to: {output_path}")
        return output_path


def main():
    """Main profiling entry point"""
    profiler = NTNPerformanceProfiler()

    # Run all profiles
    report = profiler.run_all_profiles()

    # Save report
    profiler.save_report("profiling_report.json")

    print("\n" + "="*70)
    print("PROFILING COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
