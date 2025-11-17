#!/usr/bin/env python3
"""
Performance Metrics Collector
==============================

Collects comprehensive performance metrics during large-scale testing:
- Latency breakdown (SGP4, weather, E2, xApp, control)
- Throughput metrics (messages/sec, UEs/sec)
- Resource utilization (CPU, memory, network, disk)
- Quality metrics (handover success, power accuracy, link availability)

Author: Large-Scale Performance Testing Specialist
Date: 2025-11-17
"""

import time
import psutil
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import deque
import json


@dataclass
class LatencyBreakdown:
    """Detailed latency breakdown for E2E processing"""
    timestamp: datetime
    ue_id: str

    # Component latencies (ms)
    sgp4_propagation_ms: float = 0.0
    weather_calculation_ms: float = 0.0
    link_budget_ms: float = 0.0
    e2_encoding_ms: float = 0.0
    e2_network_transmission_ms: float = 0.0
    e2_decoding_ms: float = 0.0
    xapp_handover_decision_ms: float = 0.0
    xapp_power_decision_ms: float = 0.0
    e2_control_encoding_ms: float = 0.0
    e2_control_transmission_ms: float = 0.0

    # Total E2E
    total_e2e_latency_ms: float = 0.0


@dataclass
class ThroughputMetrics:
    """Throughput performance metrics"""
    timestamp: datetime
    window_duration_sec: float = 1.0

    # Message throughput
    total_messages: int = 0
    messages_per_second: float = 0.0
    indications_per_second: float = 0.0
    controls_per_second: float = 0.0

    # UE processing
    ues_processed: int = 0
    ues_per_second: float = 0.0

    # Satellite operations
    satellite_propagations_per_second: float = 0.0
    constellation_updates_per_second: float = 0.0


@dataclass
class ResourceMetrics:
    """System resource utilization metrics"""
    timestamp: datetime

    # CPU
    cpu_percent_overall: float = 0.0
    cpu_percent_process: float = 0.0
    cpu_count: int = 0

    # Memory
    memory_used_mb: float = 0.0
    memory_percent: float = 0.0
    memory_available_mb: float = 0.0

    # Network (bytes/sec)
    network_bytes_sent_per_sec: float = 0.0
    network_bytes_recv_per_sec: float = 0.0

    # Disk I/O (bytes/sec)
    disk_read_bytes_per_sec: float = 0.0
    disk_write_bytes_per_sec: float = 0.0

    # Thread count
    thread_count: int = 0


@dataclass
class QualityMetrics:
    """Service quality metrics"""
    timestamp: datetime

    # Handover metrics
    handover_attempts: int = 0
    handover_successes: int = 0
    handover_failures: int = 0
    handover_success_rate: float = 0.0
    avg_handover_latency_ms: float = 0.0

    # Power control metrics
    power_adjustments: int = 0
    power_increases: int = 0
    power_decreases: int = 0
    avg_power_adjustment_db: float = 0.0
    power_control_accuracy_db: float = 0.0  # How close to target margin

    # Link quality
    avg_link_margin_db: float = 0.0
    min_link_margin_db: float = 0.0
    link_availability_percent: float = 0.0
    avg_snr_db: float = 0.0

    # Message metrics
    message_loss_count: int = 0
    message_loss_rate: float = 0.0


class PerformanceCollector:
    """
    Comprehensive performance metrics collector

    Tracks all performance aspects of the NTN platform during testing:
    - E2E latency breakdown
    - Throughput capacity
    - Resource utilization
    - Service quality metrics
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize performance collector

        Args:
            window_size: Number of samples to keep for moving averages
        """
        self.window_size = window_size

        # Metrics storage
        self.latency_samples: deque = deque(maxlen=window_size)
        self.throughput_samples: deque = deque(maxlen=window_size)
        self.resource_samples: deque = deque(maxlen=window_size)
        self.quality_samples: deque = deque(maxlen=window_size)

        # Counters
        self.total_messages = 0
        self.total_indications = 0
        self.total_controls = 0
        self.total_ues_processed = 0

        # Resource monitoring state
        self.process = psutil.Process()
        self.last_net_io = None
        self.last_disk_io = None
        self.last_sample_time = None

        # Running state
        self.collection_start_time = datetime.now()

        print("[PerformanceCollector] Initialized")

    def collect_latency_metrics(
        self,
        ue_id: str,
        component_times: Dict[str, float]
    ):
        """
        Collect E2E latency breakdown

        Args:
            ue_id: UE identifier
            component_times: Dictionary of component processing times
        """
        breakdown = LatencyBreakdown(
            timestamp=datetime.now(),
            ue_id=ue_id,
            sgp4_propagation_ms=component_times.get('sgp4', 0.0),
            weather_calculation_ms=component_times.get('weather', 0.0),
            link_budget_ms=component_times.get('link_budget', 0.0),
            e2_encoding_ms=component_times.get('e2_encoding', 0.0),
            e2_network_transmission_ms=component_times.get('e2_network', 0.0),
            e2_decoding_ms=component_times.get('e2_decoding', 0.0),
            xapp_handover_decision_ms=component_times.get('xapp_handover', 0.0),
            xapp_power_decision_ms=component_times.get('xapp_power', 0.0),
            e2_control_encoding_ms=component_times.get('e2_control_encoding', 0.0),
            e2_control_transmission_ms=component_times.get('e2_control_transmission', 0.0)
        )

        # Calculate total
        breakdown.total_e2e_latency_ms = sum([
            breakdown.sgp4_propagation_ms,
            breakdown.weather_calculation_ms,
            breakdown.link_budget_ms,
            breakdown.e2_encoding_ms,
            breakdown.e2_network_transmission_ms,
            breakdown.e2_decoding_ms,
            breakdown.xapp_handover_decision_ms,
            breakdown.xapp_power_decision_ms,
            breakdown.e2_control_encoding_ms,
            breakdown.e2_control_transmission_ms
        ])

        self.latency_samples.append(breakdown)
        self.total_messages += 1

    def collect_throughput_metrics(self) -> ThroughputMetrics:
        """
        Collect throughput metrics for current window

        Returns:
            ThroughputMetrics for current period
        """
        current_time = datetime.now()
        duration = (current_time - self.collection_start_time).total_seconds()

        if duration == 0:
            duration = 1.0

        metrics = ThroughputMetrics(
            timestamp=current_time,
            window_duration_sec=duration,
            total_messages=self.total_messages,
            messages_per_second=self.total_messages / duration,
            indications_per_second=self.total_indications / duration,
            controls_per_second=self.total_controls / duration,
            ues_processed=self.total_ues_processed,
            ues_per_second=self.total_ues_processed / duration
        )

        self.throughput_samples.append(metrics)
        return metrics

    def collect_resource_metrics(self) -> ResourceMetrics:
        """
        Collect current system resource utilization

        Returns:
            ResourceMetrics for current state
        """
        current_time = time.time()

        # CPU metrics
        cpu_percent_overall = psutil.cpu_percent(interval=0.1)
        cpu_percent_process = self.process.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # Memory metrics
        memory_info = self.process.memory_info()
        memory_used_mb = memory_info.rss / (1024 * 1024)
        memory_percent = self.process.memory_percent()

        vm_memory = psutil.virtual_memory()
        memory_available_mb = vm_memory.available / (1024 * 1024)

        # Network I/O
        net_io = psutil.net_io_counters()
        if self.last_net_io and self.last_sample_time:
            time_delta = current_time - self.last_sample_time
            network_bytes_sent_per_sec = (
                (net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
            )
            network_bytes_recv_per_sec = (
                (net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
            )
        else:
            network_bytes_sent_per_sec = 0.0
            network_bytes_recv_per_sec = 0.0

        self.last_net_io = net_io

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if disk_io and self.last_disk_io and self.last_sample_time:
            time_delta = current_time - self.last_sample_time
            disk_read_bytes_per_sec = (
                (disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
            )
            disk_write_bytes_per_sec = (
                (disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta
            )
        else:
            disk_read_bytes_per_sec = 0.0
            disk_write_bytes_per_sec = 0.0

        self.last_disk_io = disk_io

        # Thread count
        thread_count = self.process.num_threads()

        self.last_sample_time = current_time

        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent_overall=cpu_percent_overall,
            cpu_percent_process=cpu_percent_process,
            cpu_count=cpu_count,
            memory_used_mb=memory_used_mb,
            memory_percent=memory_percent,
            memory_available_mb=memory_available_mb,
            network_bytes_sent_per_sec=network_bytes_sent_per_sec,
            network_bytes_recv_per_sec=network_bytes_recv_per_sec,
            disk_read_bytes_per_sec=disk_read_bytes_per_sec,
            disk_write_bytes_per_sec=disk_write_bytes_per_sec,
            thread_count=thread_count
        )

        self.resource_samples.append(metrics)
        return metrics

    def collect_quality_metrics(
        self,
        handover_stats: Dict[str, Any],
        power_stats: Dict[str, Any],
        link_stats: Dict[str, Any]
    ) -> QualityMetrics:
        """
        Collect service quality metrics

        Args:
            handover_stats: Handover xApp statistics
            power_stats: Power control xApp statistics
            link_stats: Link quality statistics

        Returns:
            QualityMetrics
        """
        # Handover metrics
        handover_attempts = handover_stats.get('total_handovers_triggered', 0)
        handover_successes = handover_stats.get('successful_handovers', 0)
        handover_failures = handover_stats.get('failed_handovers', 0)
        handover_success_rate = (
            (handover_successes / handover_attempts * 100)
            if handover_attempts > 0 else 0.0
        )
        avg_handover_latency_ms = handover_stats.get('average_execution_time_ms', 0.0)

        # Power control metrics
        power_adjustments = power_stats.get('total_power_adjustments', 0)
        power_increases = power_stats.get('power_increases', 0)
        power_decreases = power_stats.get('power_decreases', 0)

        # Calculate average adjustment magnitude
        if power_adjustments > 0:
            avg_power_adjustment_db = (power_increases + power_decreases) / power_adjustments
        else:
            avg_power_adjustment_db = 0.0

        power_control_accuracy_db = abs(
            power_stats.get('average_link_margin_db', 10.0) - 10.0  # Target margin
        )

        # Link quality metrics
        avg_link_margin_db = link_stats.get('avg_link_margin_db', 0.0)
        min_link_margin_db = link_stats.get('min_link_margin_db', 0.0)
        link_availability_percent = link_stats.get('link_availability_percent', 0.0)
        avg_snr_db = link_stats.get('avg_snr_db', 0.0)

        # Message loss
        message_loss_count = link_stats.get('message_loss_count', 0)
        total_messages = link_stats.get('total_messages', 1)
        message_loss_rate = (message_loss_count / total_messages) if total_messages > 0 else 0.0

        metrics = QualityMetrics(
            timestamp=datetime.now(),
            handover_attempts=handover_attempts,
            handover_successes=handover_successes,
            handover_failures=handover_failures,
            handover_success_rate=handover_success_rate,
            avg_handover_latency_ms=avg_handover_latency_ms,
            power_adjustments=power_adjustments,
            power_increases=power_increases,
            power_decreases=power_decreases,
            avg_power_adjustment_db=avg_power_adjustment_db,
            power_control_accuracy_db=power_control_accuracy_db,
            avg_link_margin_db=avg_link_margin_db,
            min_link_margin_db=min_link_margin_db,
            link_availability_percent=link_availability_percent,
            avg_snr_db=avg_snr_db,
            message_loss_count=message_loss_count,
            message_loss_rate=message_loss_rate
        )

        self.quality_samples.append(metrics)
        return metrics

    def get_latency_statistics(self) -> Dict[str, float]:
        """Get latency statistics summary"""
        if not self.latency_samples:
            return {}

        latencies = [s.total_e2e_latency_ms for s in self.latency_samples]

        # Component averages
        sgp4_times = [s.sgp4_propagation_ms for s in self.latency_samples]
        weather_times = [s.weather_calculation_ms for s in self.latency_samples]
        e2_encoding_times = [s.e2_encoding_ms for s in self.latency_samples]
        xapp_times = [
            s.xapp_handover_decision_ms + s.xapp_power_decision_ms
            for s in self.latency_samples
        ]

        return {
            'mean_ms': float(np.mean(latencies)),
            'median_ms': float(np.median(latencies)),
            'p95_ms': float(np.percentile(latencies, 95)),
            'p99_ms': float(np.percentile(latencies, 99)),
            'max_ms': float(np.max(latencies)),
            'min_ms': float(np.min(latencies)),
            'std_dev_ms': float(np.std(latencies)),
            'avg_sgp4_ms': float(np.mean(sgp4_times)),
            'avg_weather_ms': float(np.mean(weather_times)),
            'avg_e2_encoding_ms': float(np.mean(e2_encoding_times)),
            'avg_xapp_ms': float(np.mean(xapp_times)),
        }

    def get_resource_statistics(self) -> Dict[str, float]:
        """Get resource utilization statistics"""
        if not self.resource_samples:
            return {}

        cpu_samples = [s.cpu_percent_process for s in self.resource_samples]
        memory_samples = [s.memory_used_mb for s in self.resource_samples]

        return {
            'avg_cpu_percent': float(np.mean(cpu_samples)),
            'max_cpu_percent': float(np.max(cpu_samples)),
            'avg_memory_mb': float(np.mean(memory_samples)),
            'max_memory_mb': float(np.max(memory_samples)),
            'avg_threads': float(np.mean([s.thread_count for s in self.resource_samples])),
        }

    def export_to_json(self, filepath: str):
        """Export all metrics to JSON file"""
        data = {
            'collection_start': self.collection_start_time.isoformat(),
            'collection_end': datetime.now().isoformat(),
            'summary': {
                'total_messages': self.total_messages,
                'total_indications': self.total_indications,
                'total_controls': self.total_controls,
                'total_ues_processed': self.total_ues_processed,
            },
            'latency_statistics': self.get_latency_statistics(),
            'resource_statistics': self.get_resource_statistics(),
            'latency_samples': [asdict(s) for s in self.latency_samples],
            'resource_samples': [asdict(s) for s in self.resource_samples],
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"[PerformanceCollector] Metrics exported to {filepath}")

    def print_summary(self):
        """Print performance summary"""
        latency_stats = self.get_latency_statistics()
        resource_stats = self.get_resource_statistics()

        print("\n" + "="*70)
        print("Performance Metrics Summary")
        print("="*70)

        print(f"\nLatency (E2E):")
        print(f"  Mean:     {latency_stats.get('mean_ms', 0):.2f} ms")
        print(f"  Median:   {latency_stats.get('median_ms', 0):.2f} ms")
        print(f"  P95:      {latency_stats.get('p95_ms', 0):.2f} ms")
        print(f"  P99:      {latency_stats.get('p99_ms', 0):.2f} ms")
        print(f"  Max:      {latency_stats.get('max_ms', 0):.2f} ms")

        print(f"\nComponent Breakdown:")
        print(f"  SGP4:         {latency_stats.get('avg_sgp4_ms', 0):.2f} ms")
        print(f"  Weather:      {latency_stats.get('avg_weather_ms', 0):.2f} ms")
        print(f"  E2 Encoding:  {latency_stats.get('avg_e2_encoding_ms', 0):.2f} ms")
        print(f"  xApp:         {latency_stats.get('avg_xapp_ms', 0):.2f} ms")

        print(f"\nResource Utilization:")
        print(f"  CPU (avg):    {resource_stats.get('avg_cpu_percent', 0):.1f}%")
        print(f"  CPU (max):    {resource_stats.get('max_cpu_percent', 0):.1f}%")
        print(f"  Memory (avg): {resource_stats.get('avg_memory_mb', 0):.1f} MB")
        print(f"  Memory (max): {resource_stats.get('max_memory_mb', 0):.1f} MB")

        print(f"\nThroughput:")
        print(f"  Total messages: {self.total_messages}")
        print(f"  Total UEs:      {self.total_ues_processed}")

        print("="*70 + "\n")


if __name__ == "__main__":
    # Test the performance collector
    collector = PerformanceCollector()

    # Simulate some measurements
    for i in range(100):
        collector.collect_latency_metrics(
            ue_id=f"UE-{i:03d}",
            component_times={
                'sgp4': np.random.uniform(0.5, 2.0),
                'weather': np.random.uniform(1.0, 3.0),
                'e2_encoding': np.random.uniform(0.1, 0.5),
                'xapp_handover': np.random.uniform(0.2, 0.8),
                'xapp_power': np.random.uniform(0.2, 0.8),
            }
        )

    collector.print_summary()
