#!/usr/bin/env python3
"""
Parallel UE Processing System
==============================

Implements parallel processing for multiple UEs using:
- Multi-processing for CPU-bound tasks (SGP4, Weather calculations)
- Async I/O for network operations
- Worker pool management
- Load balancing across workers

Expected improvement: 3-4x throughput for 100+ UEs

Author: Performance Optimization & Profiling Specialist
Date: 2025-11-17
"""

import asyncio
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import time
import os
import sys
from datetime import datetime
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from optimization.optimized_components import (
    OptimizedSGP4Propagator,
    OptimizedASN1Codec,
    OptimizedWeatherCalculator
)
from orbit_propagation.tle_manager import TLEManager


@dataclass
class UEProcessingTask:
    """UE processing task definition"""
    ue_id: str
    latitude: float
    longitude: float
    altitude: float
    timestamp: datetime
    satellite_id: Optional[str] = None


@dataclass
class UEProcessingResult:
    """UE processing result"""
    ue_id: str
    processing_time_ms: float
    geometry: Dict[str, Any]
    weather_loss: Dict[str, float]
    encoded_message: bytes
    success: bool
    error: Optional[str] = None


class ParallelUEProcessor:
    """
    Parallel UE processing system using multi-processing

    Architecture:
    - Main process: Manages task queue and result aggregation
    - Worker processes: Process UE batches independently
    - Shared TLE data: Loaded once, shared across workers

    Performance:
    - Linear scaling up to num_cores workers
    - Expected 3-4x speedup for 100+ UEs on 4-core system
    """

    def __init__(self, num_workers: int = None, batch_size: int = 25):
        """
        Initialize parallel UE processor

        Args:
            num_workers: Number of worker processes (default: CPU count)
            batch_size: UEs per worker batch
        """
        self.num_workers = num_workers or mp.cpu_count()
        self.batch_size = batch_size

        # Process pool
        self.executor: Optional[ProcessPoolExecutor] = None

        # Statistics
        self._total_ues_processed = 0
        self._total_processing_time_ms = 0.0
        self._worker_stats: Dict[int, Dict[str, Any]] = {}

        print(f"ParallelUEProcessor initialized")
        print(f"  - Workers: {self.num_workers}")
        print(f"  - Batch size: {batch_size} UEs/worker")

    def start(self):
        """Start worker pool"""
        if self.executor is None:
            self.executor = ProcessPoolExecutor(max_workers=self.num_workers)
            print(f"Worker pool started: {self.num_workers} workers")

    def stop(self):
        """Stop worker pool"""
        if self.executor is not None:
            self.executor.shutdown(wait=True)
            self.executor = None
            print("Worker pool stopped")

    def _split_into_batches(
        self,
        tasks: List[UEProcessingTask]
    ) -> List[List[UEProcessingTask]]:
        """Split tasks into batches for parallel processing"""
        batches = []
        for i in range(0, len(tasks), self.batch_size):
            batches.append(tasks[i:i + self.batch_size])
        return batches

    async def process_ues_parallel(
        self,
        tasks: List[UEProcessingTask]
    ) -> List[UEProcessingResult]:
        """
        Process UEs in parallel using worker pool

        Args:
            tasks: List of UE processing tasks

        Returns:
            List of processing results
        """
        if self.executor is None:
            self.start()

        print(f"\nProcessing {len(tasks)} UEs in parallel...")
        start_time = time.time()

        # Split into batches
        batches = self._split_into_batches(tasks)
        print(f"  - Created {len(batches)} batches")
        print(f"  - Avg batch size: {len(tasks) / len(batches):.1f} UEs")

        # Submit batches to worker pool
        loop = asyncio.get_event_loop()
        futures = []

        for batch_idx, batch in enumerate(batches):
            future = loop.run_in_executor(
                self.executor,
                process_ue_batch,
                batch,
                batch_idx
            )
            futures.append(future)

        # Wait for all batches to complete
        batch_results = await asyncio.gather(*futures)

        # Flatten results
        all_results = []
        for batch_result in batch_results:
            all_results.extend(batch_result)

        # Update statistics
        elapsed_ms = (time.time() - start_time) * 1000
        self._total_ues_processed += len(tasks)
        self._total_processing_time_ms += elapsed_ms

        print(f"  - Completed in {elapsed_ms:.2f} ms")
        print(f"  - Throughput: {len(tasks) / (elapsed_ms / 1000):.1f} UEs/sec")

        return all_results

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        avg_time_per_ue = (
            self._total_processing_time_ms / self._total_ues_processed
            if self._total_ues_processed > 0 else 0
        )

        throughput = (
            self._total_ues_processed / (self._total_processing_time_ms / 1000)
            if self._total_processing_time_ms > 0 else 0
        )

        return {
            'num_workers': self.num_workers,
            'batch_size': self.batch_size,
            'total_ues_processed': self._total_ues_processed,
            'total_processing_time_ms': self._total_processing_time_ms,
            'avg_time_per_ue_ms': avg_time_per_ue,
            'throughput_ues_sec': throughput
        }


def process_ue_batch(
    batch: List[UEProcessingTask],
    batch_idx: int
) -> List[UEProcessingResult]:
    """
    Worker function to process a batch of UEs

    This function runs in a separate process.

    Args:
        batch: List of UE processing tasks
        batch_idx: Batch index (for logging)

    Returns:
        List of UE processing results
    """
    results = []

    # Initialize components (per-worker)
    # Note: Each worker has its own instance to avoid shared state
    try:
        manager = TLEManager()
        tles = manager.fetch_starlink_tles(limit=1)

        if not tles:
            # Return error results
            for task in batch:
                results.append(UEProcessingResult(
                    ue_id=task.ue_id,
                    processing_time_ms=0.0,
                    geometry={},
                    weather_loss={},
                    encoded_message=b'',
                    success=False,
                    error="No TLE data available"
                ))
            return results

        propagator = OptimizedSGP4Propagator(tles[0])
        weather_calc = OptimizedWeatherCalculator()
        codec = OptimizedASN1Codec()

    except Exception as e:
        # Return error results
        for task in batch:
            results.append(UEProcessingResult(
                ue_id=task.ue_id,
                processing_time_ms=0.0,
                geometry={},
                weather_loss={},
                encoded_message=b'',
                success=False,
                error=f"Worker initialization failed: {str(e)}"
            ))
        return results

    # Process each UE in batch
    for task in batch:
        ue_start = time.time()

        try:
            # Step 1: SGP4 propagation
            geometry = propagator.get_ground_track(
                task.latitude,
                task.longitude,
                task.altitude,
                task.timestamp
            )

            # Step 2: Weather calculation
            weather_loss = weather_calc.get_total_atmospheric_loss(
                task.latitude,
                task.longitude,
                20.0,  # Ka-band frequency
                geometry['elevation_deg'],
                'circular'
            )

            # Step 3: Create E2SM-NTN message
            ntn_message = {
                'timestamp_ns': int(task.timestamp.timestamp() * 1e9),
                'ue_id': task.ue_id,
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
                    'rain_attenuation_db': weather_loss['rain_attenuation_db'],
                    'atmospheric_loss_db': weather_loss['gas_attenuation_db']
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

            # Step 4: ASN.1 encoding
            encoded_msg, _ = codec.encode_indication_message(ntn_message)

            # Success
            processing_time = (time.time() - ue_start) * 1000

            results.append(UEProcessingResult(
                ue_id=task.ue_id,
                processing_time_ms=processing_time,
                geometry=geometry,
                weather_loss=weather_loss,
                encoded_message=encoded_msg,
                success=True,
                error=None
            ))

        except Exception as e:
            # Error processing this UE
            processing_time = (time.time() - ue_start) * 1000

            results.append(UEProcessingResult(
                ue_id=task.ue_id,
                processing_time_ms=processing_time,
                geometry={},
                weather_loss={},
                encoded_message=b'',
                success=False,
                error=str(e)
            ))

    return results


async def demo_parallel_processing():
    """Demonstrate parallel UE processing"""
    print("\n" + "="*70)
    print("PARALLEL UE PROCESSING DEMONSTRATION")
    print("="*70)

    # Create test UE tasks
    num_ues = 100
    timestamp = datetime.utcnow()

    tasks = [
        UEProcessingTask(
            ue_id=f"UE-{i:05d}",
            latitude=25.0330 + (i % 10) * 0.1,
            longitude=121.5654 + (i % 10) * 0.1,
            altitude=0.0,
            timestamp=timestamp
        )
        for i in range(num_ues)
    ]

    print(f"\nCreated {num_ues} UE processing tasks")

    # Sequential processing (baseline)
    print("\n--- Sequential Processing (Baseline) ---")
    seq_start = time.time()

    manager = TLEManager()
    tles = manager.fetch_starlink_tles(limit=1)
    if tles:
        seq_results = process_ue_batch(tasks, 0)
        seq_time = (time.time() - seq_start) * 1000

        seq_success = sum(1 for r in seq_results if r.success)
        print(f"  Processed: {seq_success}/{num_ues} UEs")
        print(f"  Time: {seq_time:.2f} ms")
        print(f"  Throughput: {num_ues / (seq_time / 1000):.1f} UEs/sec")

        # Parallel processing
        print("\n--- Parallel Processing ---")
        processor = ParallelUEProcessor(num_workers=4, batch_size=25)

        par_start = time.time()
        par_results = await processor.process_ues_parallel(tasks)
        par_time = (time.time() - par_start) * 1000

        par_success = sum(1 for r in par_results if r.success)
        print(f"  Processed: {par_success}/{num_ues} UEs")
        print(f"  Time: {par_time:.2f} ms")
        print(f"  Throughput: {num_ues / (par_time / 1000):.1f} UEs/sec")

        # Comparison
        speedup = seq_time / par_time if par_time > 0 else 0
        print(f"\n--- Performance Comparison ---")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Time reduction: {((seq_time - par_time) / seq_time * 100):.1f}%")

        processor.stop()

        # Statistics
        stats = processor.get_stats()
        print(f"\n--- Processor Statistics ---")
        print(f"  Workers: {stats['num_workers']}")
        print(f"  Batch size: {stats['batch_size']}")
        print(f"  Avg time per UE: {stats['avg_time_per_ue_ms']:.2f} ms")
        print(f"  Throughput: {stats['throughput_ues_sec']:.1f} UEs/sec")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(demo_parallel_processing())
