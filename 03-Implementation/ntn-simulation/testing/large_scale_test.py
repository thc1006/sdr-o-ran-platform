#!/usr/bin/env python3
"""
Large-Scale NTN Testing Framework
==================================

Comprehensive testing framework for 100+ UEs to validate:
- System performance and scalability
- E2E latency targets (< 15ms for 100 UEs)
- Throughput capacity (> 100 msg/s)
- Resource utilization (CPU, memory)
- Handover and power control effectiveness
- Production readiness

Author: Large-Scale Performance Testing Specialist
Date: 2025-11-17
"""

import asyncio
import numpy as np
import time
import json
import psutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import NTN components
from orbit_propagation.sgp4_propagator import SGP4Propagator
from orbit_propagation.tle_manager import TLEManager
from orbit_propagation.constellation_simulator import ConstellationSimulator
from weather.realtime_attenuation import RealtimeAttenuationCalculator
from e2_ntn_extension.e2sm_ntn import E2SM_NTN
from ric_integration.e2_termination import E2TerminationPoint, E2ConnectionConfig
from xapps.ntn_handover_xapp import NTNHandoverXApp
from xapps.ntn_power_control_xapp import NTNPowerControlXApp


@dataclass
class UEConfig:
    """User Equipment configuration"""
    ue_id: str
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    carrier_freq_ghz: float = 2.0
    initial_power_dbm: float = 20.0


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single UE at a point in time"""
    timestamp: datetime
    ue_id: str

    # Latency metrics (ms)
    sgp4_propagation_time_ms: float = 0.0
    weather_calculation_time_ms: float = 0.0
    e2_encoding_time_ms: float = 0.0
    e2_transmission_time_ms: float = 0.0
    xapp_decision_time_ms: float = 0.0
    e2_control_time_ms: float = 0.0
    total_e2e_latency_ms: float = 0.0

    # Satellite metrics
    satellite_id: str = ""
    elevation_deg: float = 0.0
    slant_range_km: float = 0.0
    doppler_shift_hz: float = 0.0

    # Link quality
    link_margin_db: float = 0.0
    rain_attenuation_db: float = 0.0
    snr_db: float = 0.0

    # Actions
    handover_triggered: bool = False
    power_adjusted: bool = False
    power_adjustment_db: float = 0.0


@dataclass
class TestResults:
    """Aggregated test results"""
    scenario_name: str
    num_ues: int
    duration_seconds: float

    # Latency statistics (ms)
    latency_mean: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    latency_max: float = 0.0

    # Throughput statistics
    total_messages: int = 0
    messages_per_second: float = 0.0
    ues_processed_per_second: float = 0.0

    # Resource utilization
    avg_cpu_percent: float = 0.0
    max_cpu_percent: float = 0.0
    avg_memory_mb: float = 0.0
    max_memory_mb: float = 0.0

    # Quality metrics
    total_handovers: int = 0
    successful_handovers: int = 0
    handover_success_rate: float = 0.0

    total_power_adjustments: int = 0
    power_increases: int = 0
    power_decreases: int = 0

    avg_link_margin_db: float = 0.0
    min_link_margin_db: float = 0.0
    link_availability_percent: float = 0.0

    # Performance targets
    target_latency_met: bool = False  # < 15ms for 100 UEs
    target_throughput_met: bool = False  # > 100 msg/s
    target_cpu_met: bool = False  # < 50%
    target_memory_met: bool = False  # < 4GB


class LargeScaleNTNTest:
    """
    Large-Scale NTN Testing Framework

    Tests the complete NTN-O-RAN platform with 100+ UEs to validate:
    - Performance and scalability
    - E2 interface latency
    - xApp decision making
    - Resource utilization
    - Production readiness
    """

    def __init__(self, num_ues: int = 100, scenario_name: str = "default"):
        """
        Initialize large-scale test

        Args:
            num_ues: Number of UEs to simulate
            scenario_name: Name of test scenario
        """
        self.num_ues = num_ues
        self.scenario_name = scenario_name

        # UE configurations
        self.ues: List[UEConfig] = []

        # NTN Platform components
        self.tle_manager: Optional[TLEManager] = None
        self.constellation: Optional[ConstellationSimulator] = None
        self.weather_calc: Optional[RealtimeAttenuationCalculator] = None
        self.e2sm_ntn: Optional[E2SM_NTN] = None
        self.handover_xapp: Optional[NTNHandoverXApp] = None
        self.power_xapp: Optional[NTNPowerControlXApp] = None

        # Performance tracking
        self.metrics: List[PerformanceMetrics] = []
        self.resource_samples: List[Dict[str, float]] = []

        # Test state
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.running = False

        print(f"[Large-Scale Test] Initialized: {scenario_name}")
        print(f"  UEs: {num_ues}")

    async def setup_scenario(
        self,
        ue_distribution: str = "global",
        weather_scenario: str = "variable"
    ):
        """
        Setup test scenario with UEs and NTN infrastructure

        Args:
            ue_distribution: UE geographic distribution pattern
            weather_scenario: Weather condition scenario
        """
        print(f"\n[Setup] Configuring {self.num_ues} UEs with {ue_distribution} distribution...")

        # Generate UE configurations based on distribution
        self.ues = self._generate_ue_distribution(ue_distribution)
        print(f"[Setup] Generated {len(self.ues)} UE configurations")

        # Initialize TLE Manager and fetch Starlink constellation
        print(f"[Setup] Loading Starlink constellation...")
        self.tle_manager = TLEManager()
        tles = self.tle_manager.fetch_starlink_tles(limit=100)  # Use 100 satellites for testing
        print(f"[Setup] Loaded {len(tles)} satellites")

        # Initialize constellation simulator
        self.constellation = ConstellationSimulator(tles)
        print(f"[Setup] Constellation simulator ready")

        # Initialize weather calculator (mock mode for performance)
        print(f"[Setup] Initializing weather calculator...")
        self.weather_calc = RealtimeAttenuationCalculator(use_mock_weather=True)
        print(f"[Setup] Weather calculator ready")

        # Initialize E2SM-NTN service model with ASN.1 encoding
        print(f"[Setup] Initializing E2SM-NTN...")
        self.e2sm_ntn = E2SM_NTN(encoding='asn1')
        print(f"[Setup] E2SM-NTN ready (encoding: ASN.1 PER)")

        # Initialize xApps
        print(f"[Setup] Initializing xApps...")
        self.handover_xapp = NTNHandoverXApp()
        self.power_xapp = NTNPowerControlXApp()
        await self.handover_xapp.start()
        await self.power_xapp.start()
        print(f"[Setup] xApps ready")

        print(f"[Setup] Scenario setup complete!\n")

    def _generate_ue_distribution(self, distribution: str) -> List[UEConfig]:
        """Generate UE geographic distribution"""
        ues = []

        if distribution == "global":
            # Evenly distributed globally
            for i in range(self.num_ues):
                lat = np.random.uniform(-60, 60)  # Avoid polar regions
                lon = np.random.uniform(-180, 180)
                ues.append(UEConfig(
                    ue_id=f"UE-{i:04d}",
                    latitude=lat,
                    longitude=lon,
                    altitude_m=np.random.uniform(0, 100)
                ))

        elif distribution == "urban_dense":
            # Concentrated in major cities
            cities = [
                (40.7128, -74.0060),  # New York
                (51.5074, -0.1278),   # London
                (35.6762, 139.6503),  # Tokyo
                (1.3521, 103.8198),   # Singapore
                (-33.8688, 151.2093), # Sydney
            ]

            for i in range(self.num_ues):
                city_lat, city_lon = cities[i % len(cities)]
                # Add random offset (within ~50km)
                lat = city_lat + np.random.normal(0, 0.5)
                lon = city_lon + np.random.normal(0, 0.5)
                ues.append(UEConfig(
                    ue_id=f"UE-{i:04d}",
                    latitude=lat,
                    longitude=lon,
                    altitude_m=np.random.uniform(0, 200)
                ))

        elif distribution == "sparse_global":
            # Sparse distribution across continents
            for i in range(self.num_ues):
                lat = np.random.uniform(-50, 50)
                lon = np.random.uniform(-170, 170)
                # Avoid oceans (simplified)
                ues.append(UEConfig(
                    ue_id=f"UE-{i:04d}",
                    latitude=lat,
                    longitude=lon,
                    altitude_m=np.random.uniform(0, 500)
                ))

        else:  # uniform
            # Uniform grid distribution
            grid_size = int(np.ceil(np.sqrt(self.num_ues)))
            idx = 0
            for i in range(grid_size):
                for j in range(grid_size):
                    if idx >= self.num_ues:
                        break
                    lat = -60 + (120 / grid_size) * i
                    lon = -180 + (360 / grid_size) * j
                    ues.append(UEConfig(
                        ue_id=f"UE-{idx:04d}",
                        latitude=lat,
                        longitude=lon,
                        altitude_m=0.0
                    ))
                    idx += 1

        return ues

    async def run_scenario(self, duration_minutes: int = 60, time_step_sec: float = 1.0):
        """
        Run test scenario for specified duration

        Args:
            duration_minutes: Test duration in minutes
            time_step_sec: Time step between iterations in seconds
        """
        print(f"[Test] Starting {self.scenario_name} scenario...")
        print(f"  Duration: {duration_minutes} minutes")
        print(f"  Time step: {time_step_sec} seconds")
        print(f"  UEs: {self.num_ues}")
        print(f"  Total iterations: {int(duration_minutes * 60 / time_step_sec)}")

        self.running = True
        self.start_time = datetime.now()

        # Calculate number of iterations
        num_iterations = int(duration_minutes * 60 / time_step_sec)

        # Start resource monitoring task
        resource_task = asyncio.create_task(self._monitor_resources())

        # Main simulation loop
        for iteration in range(num_iterations):
            iteration_start = time.time()
            current_time = self.start_time + timedelta(seconds=iteration * time_step_sec)

            # Process all UEs in parallel (batched for performance)
            batch_size = 10  # Process 10 UEs at a time
            for batch_start in range(0, len(self.ues), batch_size):
                batch_end = min(batch_start + batch_size, len(self.ues))
                batch_ues = self.ues[batch_start:batch_end]

                # Process batch in parallel
                tasks = [
                    self._process_ue(ue, current_time)
                    for ue in batch_ues
                ]
                batch_metrics = await asyncio.gather(*tasks)
                self.metrics.extend(batch_metrics)

            # Progress reporting
            if iteration % 60 == 0:  # Every minute
                elapsed = time.time() - self.start_time.timestamp()
                messages_sent = len(self.metrics)
                msg_per_sec = messages_sent / elapsed if elapsed > 0 else 0

                print(f"[Progress] Iteration {iteration}/{num_iterations} "
                      f"({iteration*time_step_sec/60:.1f}/{duration_minutes} min) - "
                      f"Messages: {messages_sent}, "
                      f"Rate: {msg_per_sec:.1f} msg/s")

            # Rate limiting to maintain time step
            iteration_elapsed = time.time() - iteration_start
            sleep_time = max(0, time_step_sec - iteration_elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.running = False
        self.end_time = datetime.now()

        # Stop resource monitoring
        resource_task.cancel()
        try:
            await resource_task
        except asyncio.CancelledError:
            pass

        print(f"\n[Test] Scenario complete!")
        print(f"  Duration: {(self.end_time - self.start_time).total_seconds():.1f} seconds")
        print(f"  Total messages: {len(self.metrics)}")

    async def _process_ue(self, ue: UEConfig, timestamp: datetime) -> PerformanceMetrics:
        """
        Process single UE through complete NTN pipeline

        Args:
            ue: UE configuration
            timestamp: Current simulation time

        Returns:
            Performance metrics for this UE
        """
        metrics = PerformanceMetrics(timestamp=timestamp, ue_id=ue.ue_id)

        try:
            # Step 1: SGP4 Orbit Propagation
            sgp4_start = time.time()
            satellite_geometry = self.constellation.find_best_satellite(
                ue.latitude, ue.longitude, ue.altitude_m, timestamp
            )
            metrics.sgp4_propagation_time_ms = (time.time() - sgp4_start) * 1000

            if not satellite_geometry:
                # No visible satellite
                return metrics

            metrics.satellite_id = satellite_geometry['satellite_id']
            metrics.elevation_deg = satellite_geometry['elevation_deg']
            metrics.slant_range_km = satellite_geometry['slant_range_km']
            metrics.doppler_shift_hz = satellite_geometry['doppler_shift_hz']

            # Step 2: Weather/Attenuation Calculation
            weather_start = time.time()
            attenuation = await self.weather_calc.calculate_current_attenuation(
                ue.latitude,
                ue.longitude,
                ue.carrier_freq_ghz,
                satellite_geometry['elevation_deg'],
                use_real_weather=False  # Use mock for performance
            )
            metrics.weather_calculation_time_ms = (time.time() - weather_start) * 1000
            metrics.rain_attenuation_db = attenuation.rain_attenuation_db

            # Step 3: Calculate link budget
            link_budget = self._calculate_link_budget(
                satellite_geometry,
                attenuation,
                ue.initial_power_dbm
            )
            metrics.link_margin_db = link_budget['link_margin_db']
            metrics.snr_db = link_budget['snr_db']

            # Step 4: E2SM-NTN Encoding
            e2_start = time.time()
            indication_header, indication_message = self.e2sm_ntn.create_indication_message(
                ue_id=ue.ue_id,
                satellite_state={
                    'satellite_id': satellite_geometry['satellite_id'],
                    'elevation_angle': satellite_geometry['elevation_deg'],
                    'azimuth_angle': satellite_geometry.get('azimuth_deg', 0.0),
                    'slant_range_km': satellite_geometry['slant_range_km'],
                },
                ue_measurements={
                    'link_budget': link_budget,
                    'doppler_shift_hz': satellite_geometry['doppler_shift_hz'],
                    'rain_attenuation_db': attenuation.rain_attenuation_db,
                },
                report_style=1
            )
            metrics.e2_encoding_time_ms = (time.time() - e2_start) * 1000

            # Step 5: E2 Transmission (simulated)
            e2_tx_start = time.time()
            # Simulate network transmission delay
            await asyncio.sleep(0.001)  # 1ms network delay
            metrics.e2_transmission_time_ms = (time.time() - e2_tx_start) * 1000

            # Step 6: xApp Processing
            xapp_start = time.time()

            # Process with Handover xApp
            await self.handover_xapp.on_indication(indication_header, indication_message)

            # Process with Power Control xApp
            await self.power_xapp.on_indication(indication_header, indication_message)

            metrics.xapp_decision_time_ms = (time.time() - xapp_start) * 1000

            # Step 7: E2 Control (if needed)
            e2_ctrl_start = time.time()
            # Check if control actions were triggered
            if ue.ue_id in self.handover_xapp.ue_contexts:
                context = self.handover_xapp.ue_contexts[ue.ue_id]
                if context.handover_history:
                    last_handover = context.handover_history[-1]
                    if last_handover['timestamp'] == time.time():
                        metrics.handover_triggered = True

            if ue.ue_id in self.power_xapp.ue_power_states:
                state = self.power_xapp.ue_power_states[ue.ue_id]
                if state.adjustment_history:
                    last_adj = state.adjustment_history[-1]
                    if last_adj.timestamp == time.time():
                        metrics.power_adjusted = True
                        metrics.power_adjustment_db = last_adj.adjustment_db

            metrics.e2_control_time_ms = (time.time() - e2_ctrl_start) * 1000

            # Calculate total E2E latency
            metrics.total_e2e_latency_ms = (
                metrics.sgp4_propagation_time_ms +
                metrics.weather_calculation_time_ms +
                metrics.e2_encoding_time_ms +
                metrics.e2_transmission_time_ms +
                metrics.xapp_decision_time_ms +
                metrics.e2_control_time_ms
            )

        except Exception as e:
            print(f"[Error] Processing UE {ue.ue_id}: {e}")

        return metrics

    def _calculate_link_budget(
        self,
        satellite_geometry: Dict,
        attenuation: Any,
        tx_power_dbm: float
    ) -> Dict[str, float]:
        """Calculate link budget"""
        # Simplified link budget calculation
        # Path loss (free space + atmospheric)
        slant_range_km = satellite_geometry['slant_range_km']
        frequency_ghz = 2.0

        # Free space path loss: FSPL = 20*log10(d) + 20*log10(f) + 92.45
        fspl_db = 20 * np.log10(slant_range_km) + 20 * np.log10(frequency_ghz * 1000) + 92.45

        # Total losses
        total_loss_db = (
            fspl_db +
            attenuation.rain_attenuation_db +
            attenuation.cloud_attenuation_db +
            attenuation.gas_attenuation_db
        )

        # Received power
        antenna_gain_db = 20.0  # Typical satellite antenna
        rx_power_dbm = tx_power_dbm + antenna_gain_db - total_loss_db

        # SNR calculation
        noise_floor_dbm = -110.0  # Typical
        snr_db = rx_power_dbm - noise_floor_dbm

        # Required SNR for link
        required_snr_db = 9.0  # For typical modulation

        # Link margin
        link_margin_db = snr_db - required_snr_db

        return {
            'tx_power_dbm': tx_power_dbm,
            'rx_power_dbm': rx_power_dbm,
            'link_margin_db': link_margin_db,
            'snr_db': snr_db,
            'required_snr_db': required_snr_db,
            'path_loss_db': total_loss_db
        }

    async def _monitor_resources(self):
        """Monitor system resource usage"""
        process = psutil.Process()

        while self.running:
            try:
                # Get CPU and memory usage
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)

                self.resource_samples.append({
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb
                })

                await asyncio.sleep(1.0)  # Sample every second

            except Exception as e:
                print(f"[Warning] Resource monitoring error: {e}")
                break

    def analyze_results(self) -> TestResults:
        """
        Analyze test results and calculate statistics

        Returns:
            TestResults with aggregated statistics
        """
        print(f"\n[Analysis] Analyzing {len(self.metrics)} measurements...")

        if not self.metrics:
            print("[Warning] No metrics to analyze!")
            return TestResults(
                scenario_name=self.scenario_name,
                num_ues=self.num_ues,
                duration_seconds=0.0
            )

        # Calculate duration
        duration_seconds = (self.end_time - self.start_time).total_seconds()

        # Extract latency values
        latencies = [m.total_e2e_latency_ms for m in self.metrics if m.total_e2e_latency_ms > 0]

        # Latency statistics
        latency_mean = np.mean(latencies) if latencies else 0.0
        latency_p50 = np.percentile(latencies, 50) if latencies else 0.0
        latency_p95 = np.percentile(latencies, 95) if latencies else 0.0
        latency_p99 = np.percentile(latencies, 99) if latencies else 0.0
        latency_max = np.max(latencies) if latencies else 0.0

        # Throughput statistics
        total_messages = len(self.metrics)
        messages_per_second = total_messages / duration_seconds if duration_seconds > 0 else 0
        ues_processed_per_second = (total_messages / self.num_ues) / duration_seconds if duration_seconds > 0 else 0

        # Resource statistics
        cpu_samples = [s['cpu_percent'] for s in self.resource_samples]
        memory_samples = [s['memory_mb'] for s in self.resource_samples]

        avg_cpu_percent = np.mean(cpu_samples) if cpu_samples else 0.0
        max_cpu_percent = np.max(cpu_samples) if cpu_samples else 0.0
        avg_memory_mb = np.mean(memory_samples) if memory_samples else 0.0
        max_memory_mb = np.max(memory_samples) if memory_samples else 0.0

        # Handover statistics
        handover_stats = self.handover_xapp.collect_statistics()
        total_handovers = handover_stats['total_handovers_triggered']
        successful_handovers = handover_stats['successful_handovers']
        handover_success_rate = (successful_handovers / total_handovers * 100) if total_handovers > 0 else 0.0

        # Power control statistics
        power_stats = self.power_xapp.collect_statistics()
        total_power_adjustments = power_stats['total_power_adjustments']
        power_increases = power_stats['power_increases']
        power_decreases = power_stats['power_decreases']

        # Link quality statistics
        link_margins = [m.link_margin_db for m in self.metrics if m.link_margin_db > 0]
        avg_link_margin_db = np.mean(link_margins) if link_margins else 0.0
        min_link_margin_db = np.min(link_margins) if link_margins else 0.0

        # Link availability (margin > 0)
        available_links = sum(1 for m in link_margins if m > 0)
        link_availability_percent = (available_links / len(link_margins) * 100) if link_margins else 0.0

        # Check performance targets
        target_latency_met = latency_p99 < 15.0  # < 15ms for 100 UEs
        target_throughput_met = messages_per_second > 100  # > 100 msg/s
        target_cpu_met = avg_cpu_percent < 50  # < 50%
        target_memory_met = avg_memory_mb < 4096  # < 4GB

        results = TestResults(
            scenario_name=self.scenario_name,
            num_ues=self.num_ues,
            duration_seconds=duration_seconds,
            latency_mean=latency_mean,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            latency_max=latency_max,
            total_messages=total_messages,
            messages_per_second=messages_per_second,
            ues_processed_per_second=ues_processed_per_second,
            avg_cpu_percent=avg_cpu_percent,
            max_cpu_percent=max_cpu_percent,
            avg_memory_mb=avg_memory_mb,
            max_memory_mb=max_memory_mb,
            total_handovers=total_handovers,
            successful_handovers=successful_handovers,
            handover_success_rate=handover_success_rate,
            total_power_adjustments=total_power_adjustments,
            power_increases=power_increases,
            power_decreases=power_decreases,
            avg_link_margin_db=avg_link_margin_db,
            min_link_margin_db=min_link_margin_db,
            link_availability_percent=link_availability_percent,
            target_latency_met=target_latency_met,
            target_throughput_met=target_throughput_met,
            target_cpu_met=target_cpu_met,
            target_memory_met=target_memory_met
        )

        print(f"[Analysis] Complete!")
        return results

    def print_results(self, results: TestResults):
        """Print formatted test results"""
        print("\n" + "="*80)
        print(f"Large-Scale Test Results: {results.scenario_name}")
        print("="*80)
        print(f"Configuration:")
        print(f"  UEs: {results.num_ues}")
        print(f"  Duration: {results.duration_seconds:.1f} seconds ({results.duration_seconds/60:.1f} minutes)")
        print(f"  Total Messages: {results.total_messages}")

        print(f"\nLatency Performance:")
        print(f"  Mean:        {results.latency_mean:.2f} ms")
        print(f"  P50:         {results.latency_p50:.2f} ms")
        print(f"  P95:         {results.latency_p95:.2f} ms")
        print(f"  P99:         {results.latency_p99:.2f} ms {'✓' if results.target_latency_met else '✗ (target: < 15ms)'}")
        print(f"  Max:         {results.latency_max:.2f} ms")

        print(f"\nThroughput:")
        print(f"  Messages/sec:     {results.messages_per_second:.1f} {'✓' if results.target_throughput_met else '✗ (target: > 100)'}")
        print(f"  UEs/sec:          {results.ues_processed_per_second:.2f}")

        print(f"\nResource Utilization:")
        print(f"  CPU (avg):        {results.avg_cpu_percent:.1f}% {'✓' if results.target_cpu_met else '✗ (target: < 50%)'}")
        print(f"  CPU (max):        {results.max_cpu_percent:.1f}%")
        print(f"  Memory (avg):     {results.avg_memory_mb:.1f} MB {'✓' if results.target_memory_met else '✗ (target: < 4096 MB)'}")
        print(f"  Memory (max):     {results.max_memory_mb:.1f} MB")

        print(f"\nHandover Performance:")
        print(f"  Total:            {results.total_handovers}")
        print(f"  Successful:       {results.successful_handovers}")
        print(f"  Success Rate:     {results.handover_success_rate:.1f}%")

        print(f"\nPower Control:")
        print(f"  Total Adjustments: {results.total_power_adjustments}")
        print(f"  Increases:        {results.power_increases}")
        print(f"  Decreases:        {results.power_decreases}")

        print(f"\nLink Quality:")
        print(f"  Avg Margin:       {results.avg_link_margin_db:.1f} dB")
        print(f"  Min Margin:       {results.min_link_margin_db:.1f} dB")
        print(f"  Availability:     {results.link_availability_percent:.1f}%")

        # Overall assessment
        all_targets_met = all([
            results.target_latency_met,
            results.target_throughput_met,
            results.target_cpu_met,
            results.target_memory_met
        ])

        print(f"\nPerformance Targets:")
        status = "✓ ALL TARGETS MET" if all_targets_met else "✗ SOME TARGETS NOT MET"
        print(f"  {status}")
        print("="*80 + "\n")

    async def cleanup(self):
        """Cleanup test resources"""
        if self.handover_xapp:
            await self.handover_xapp.stop()
        if self.power_xapp:
            await self.power_xapp.stop()
        if self.weather_calc:
            await self.weather_calc.close()


async def main():
    """Example test execution"""
    print("Large-Scale NTN Testing Framework")
    print("="*80)

    # Create test with 100 UEs
    test = LargeScaleNTNTest(num_ues=100, scenario_name="Uniform Load - 100 UEs")

    # Setup scenario
    await test.setup_scenario(ue_distribution="global", weather_scenario="variable")

    # Run test for 5 minutes (reduced for demo)
    await test.run_scenario(duration_minutes=5, time_step_sec=1.0)

    # Analyze results
    results = test.analyze_results()

    # Print results
    test.print_results(results)

    # Cleanup
    await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
