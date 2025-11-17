#!/usr/bin/env python3
"""
NTN Stress Testing Suite
=========================

Progressively increases load to find system limits and identify bottlenecks.

Tests scalability with:
- Gradual load increase (10 -> 50 -> 100 -> 200 -> 500 -> 1000 UEs)
- Performance degradation detection
- Bottleneck identification
- Resource limit discovery
- Maximum capacity determination

Author: Large-Scale Performance Testing Specialist
Date: 2025-11-17
"""

import asyncio
import numpy as np
import time
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing.large_scale_test import LargeScaleNTNTest, TestResults


@dataclass
class StressTestPoint:
    """Single stress test data point"""
    num_ues: int
    duration_seconds: float
    latency_p99_ms: float
    throughput_msg_s: float
    cpu_percent: float
    memory_mb: float
    handover_success_rate: float
    all_targets_met: bool
    degradation_detected: bool
    bottleneck: Optional[str] = None


class NTNStressTest:
    """
    Stress testing framework for NTN platform

    Progressively increases load to determine:
    - Maximum UE capacity
    - Performance degradation thresholds
    - System bottlenecks
    - Resource limits
    """

    def __init__(self):
        """Initialize stress test"""
        self.test_points: List[StressTestPoint] = []
        self.max_capacity_found = False
        self.max_ues = 0

        # Performance thresholds
        self.latency_threshold_ms = 50.0  # P99 latency threshold
        self.cpu_threshold_percent = 95.0
        self.memory_threshold_mb = 32 * 1024  # 32 GB
        self.degradation_threshold = 0.5  # 50% performance drop

        print("[StressTest] Initialized")
        print(f"  Latency threshold: {self.latency_threshold_ms} ms (P99)")
        print(f"  CPU threshold: {self.cpu_threshold_percent}%")
        print(f"  Memory threshold: {self.memory_threshold_mb} MB")

    async def run_gradual_load_test(
        self,
        start_ues: int = 10,
        max_ues: int = 1000,
        step_multiplier: float = 2.0,
        duration_per_test_min: int = 10
    ):
        """
        Run gradual load increase test

        Args:
            start_ues: Starting number of UEs
            max_ues: Maximum UEs to test
            step_multiplier: Multiplier for each step
            duration_per_test_min: Duration of each test point
        """
        print(f"\n{'='*80}")
        print("Gradual Load Stress Test")
        print(f"{'='*80}")
        print(f"Starting UEs: {start_ues}")
        print(f"Maximum UEs: {max_ues}")
        print(f"Step multiplier: {step_multiplier}x")
        print(f"Duration per test: {duration_per_test_min} minutes")
        print(f"{'='*80}\n")

        # Generate test points
        num_ues_list = []
        current_ues = start_ues
        while current_ues <= max_ues:
            num_ues_list.append(int(current_ues))
            current_ues *= step_multiplier

        # Run tests at each load level
        for i, num_ues in enumerate(num_ues_list):
            print(f"\n{'='*80}")
            print(f"Test Point {i+1}/{len(num_ues_list)}: {num_ues} UEs")
            print(f"{'='*80}")

            # Run test
            test_point = await self.run_test_point(
                num_ues=num_ues,
                duration_min=duration_per_test_min
            )

            self.test_points.append(test_point)

            # Print immediate results
            self._print_test_point(test_point)

            # Check for degradation
            if test_point.degradation_detected:
                print(f"\n⚠ Performance degradation detected at {num_ues} UEs!")
                print(f"  Bottleneck: {test_point.bottleneck}")

                if test_point.latency_p99_ms > self.latency_threshold_ms:
                    print(f"  Latency exceeded threshold: {test_point.latency_p99_ms:.2f} ms > {self.latency_threshold_ms} ms")
                    self.max_capacity_found = True
                    self.max_ues = num_ues
                    print(f"\nMaximum capacity determined: {self.max_ues} UEs")
                    break

            # Check resource limits
            if test_point.cpu_percent > self.cpu_threshold_percent:
                print(f"\n⚠ CPU limit reached at {num_ues} UEs!")
                self.max_capacity_found = True
                self.max_ues = num_ues
                break

            if test_point.memory_mb > self.memory_threshold_mb:
                print(f"\n⚠ Memory limit reached at {num_ues} UEs!")
                self.max_capacity_found = True
                self.max_ues = num_ues
                break

            print(f"✓ {num_ues} UEs: All checks passed")

        # Final summary
        self._print_stress_test_summary()

    async def run_test_point(
        self,
        num_ues: int,
        duration_min: int = 10
    ) -> StressTestPoint:
        """
        Run single stress test point

        Args:
            num_ues: Number of UEs to test
            duration_min: Test duration in minutes

        Returns:
            StressTestPoint with results
        """
        print(f"\n[Test] Running with {num_ues} UEs for {duration_min} minutes...")

        # Create test
        test = LargeScaleNTNTest(
            num_ues=num_ues,
            scenario_name=f"Stress Test - {num_ues} UEs"
        )

        # Setup
        await test.setup_scenario(ue_distribution="global")

        # Run
        start_time = time.time()
        await test.run_scenario(duration_minutes=duration_min, time_step_sec=1.0)
        duration_seconds = time.time() - start_time

        # Analyze
        results = test.analyze_results()

        # Cleanup
        await test.cleanup()

        # Check for degradation
        degradation_detected, bottleneck = self._detect_degradation(results)

        # Create test point
        test_point = StressTestPoint(
            num_ues=num_ues,
            duration_seconds=duration_seconds,
            latency_p99_ms=results.latency_p99,
            throughput_msg_s=results.messages_per_second,
            cpu_percent=results.avg_cpu_percent,
            memory_mb=results.avg_memory_mb,
            handover_success_rate=results.handover_success_rate,
            all_targets_met=(
                results.target_latency_met and
                results.target_throughput_met and
                results.target_cpu_met and
                results.target_memory_met
            ),
            degradation_detected=degradation_detected,
            bottleneck=bottleneck
        )

        return test_point

    def _detect_degradation(
        self,
        results: TestResults
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect performance degradation and identify bottleneck

        Args:
            results: Test results to analyze

        Returns:
            Tuple of (degradation_detected, bottleneck_name)
        """
        degradation = False
        bottleneck = None

        # Check latency degradation
        if results.latency_p99 > self.latency_threshold_ms:
            degradation = True
            bottleneck = "LATENCY"

        # Check CPU
        elif results.avg_cpu_percent > self.cpu_threshold_percent:
            degradation = True
            bottleneck = "CPU"

        # Check memory
        elif results.avg_memory_mb > self.memory_threshold_mb:
            degradation = True
            bottleneck = "MEMORY"

        # Check if latency increased significantly from baseline
        elif len(self.test_points) > 0:
            baseline_latency = self.test_points[0].latency_p99_ms
            current_latency = results.latency_p99

            latency_increase_ratio = (current_latency - baseline_latency) / baseline_latency

            if latency_increase_ratio > self.degradation_threshold:
                degradation = True
                bottleneck = "LATENCY_DEGRADATION"

        return degradation, bottleneck

    def _print_test_point(self, point: StressTestPoint):
        """Print single test point results"""
        print(f"\nResults:")
        print(f"  Latency (P99):     {point.latency_p99_ms:.2f} ms")
        print(f"  Throughput:        {point.throughput_msg_s:.1f} msg/s")
        print(f"  CPU:               {point.cpu_percent:.1f}%")
        print(f"  Memory:            {point.memory_mb:.1f} MB")
        print(f"  Handover Success:  {point.handover_success_rate:.1f}%")
        print(f"  Targets Met:       {'✓ Yes' if point.all_targets_met else '✗ No'}")

    def _print_stress_test_summary(self):
        """Print comprehensive stress test summary"""
        print(f"\n{'='*80}")
        print("Stress Test Summary")
        print(f"{'='*80}")

        if not self.test_points:
            print("No test points completed!")
            return

        print(f"\nTest Points Completed: {len(self.test_points)}")

        # Find maximum performing configuration
        max_ues_all_targets = 0
        for point in self.test_points:
            if point.all_targets_met:
                max_ues_all_targets = max(max_ues_all_targets, point.num_ues)

        print(f"Maximum UEs (all targets met): {max_ues_all_targets}")

        if self.max_capacity_found:
            print(f"Maximum capacity found: {self.max_ues} UEs")
        else:
            print(f"Maximum capacity not reached (tested up to {self.test_points[-1].num_ues} UEs)")

        # Performance table
        print(f"\n{'UEs':<8} {'Latency P99':<14} {'Throughput':<14} {'CPU':<10} {'Memory':<12} {'Status':<10}")
        print(f"{'-'*8} {'-'*14} {'-'*14} {'-'*10} {'-'*12} {'-'*10}")

        for point in self.test_points:
            status = "✓ PASS" if point.all_targets_met else "✗ FAIL"
            print(f"{point.num_ues:<8} "
                  f"{point.latency_p99_ms:<14.2f} "
                  f"{point.throughput_msg_s:<14.1f} "
                  f"{point.cpu_percent:<10.1f} "
                  f"{point.memory_mb:<12.1f} "
                  f"{status:<10}")

        # Scalability analysis
        print(f"\nScalability Analysis:")

        if len(self.test_points) >= 2:
            # Linear scalability check
            first_point = self.test_points[0]
            last_point = self.test_points[-1]

            ue_ratio = last_point.num_ues / first_point.num_ues
            throughput_ratio = last_point.throughput_msg_s / first_point.throughput_msg_s
            latency_ratio = last_point.latency_p99_ms / first_point.latency_p99_ms

            scalability_efficiency = throughput_ratio / ue_ratio

            print(f"  UE increase:         {ue_ratio:.1f}x ({first_point.num_ues} -> {last_point.num_ues})")
            print(f"  Throughput increase: {throughput_ratio:.1f}x")
            print(f"  Latency increase:    {latency_ratio:.1f}x")
            print(f"  Scalability efficiency: {scalability_efficiency*100:.1f}%")

            if scalability_efficiency > 0.9:
                print(f"  Assessment: ✓ Excellent scalability (>90%)")
            elif scalability_efficiency > 0.7:
                print(f"  Assessment: ✓ Good scalability (>70%)")
            elif scalability_efficiency > 0.5:
                print(f"  Assessment: ⚠ Moderate scalability (>50%)")
            else:
                print(f"  Assessment: ✗ Poor scalability (<50%)")

        # Bottleneck analysis
        bottlenecks = [p.bottleneck for p in self.test_points if p.bottleneck]
        if bottlenecks:
            print(f"\nBottlenecks Identified:")
            from collections import Counter
            bottleneck_counts = Counter(bottlenecks)
            for bottleneck, count in bottleneck_counts.most_common():
                print(f"  - {bottleneck}: {count} occurrences")

        # Recommendations
        print(f"\nRecommendations:")
        if max_ues_all_targets >= 100:
            print(f"  ✓ System meets 100 UE requirement")
        else:
            print(f"  ✗ System does not meet 100 UE requirement")
            print(f"    Maximum: {max_ues_all_targets} UEs")

        if max_ues_all_targets >= 200:
            print(f"  ✓ System exceeds target goals (200+ UEs)")

        if max_ues_all_targets >= 500:
            print(f"  ✓ System meets stretch goals (500+ UEs)")

        print(f"{'='*80}\n")

    def export_results(self, filepath: str):
        """Export stress test results to JSON"""
        data = {
            'stress_test_summary': {
                'total_test_points': len(self.test_points),
                'max_capacity_found': self.max_capacity_found,
                'max_ues': self.max_ues,
                'thresholds': {
                    'latency_ms': self.latency_threshold_ms,
                    'cpu_percent': self.cpu_threshold_percent,
                    'memory_mb': self.memory_threshold_mb,
                }
            },
            'test_points': [asdict(p) for p in self.test_points],
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"[StressTest] Results exported to {filepath}")


async def main():
    """Run stress test"""
    print("NTN Stress Testing Suite")
    print("="*80)

    stress_test = NTNStressTest()

    # Run gradual load test
    # Start with 10 UEs, go up to 1000, doubling each time, 5 min per test
    await stress_test.run_gradual_load_test(
        start_ues=10,
        max_ues=500,  # Reduced for demo
        step_multiplier=2.0,
        duration_per_test_min=5  # 5 minutes per test point (reduced for demo)
    )

    # Export results
    stress_test.export_results('/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/testing/stress_test_results.json')


if __name__ == "__main__":
    asyncio.run(main())
