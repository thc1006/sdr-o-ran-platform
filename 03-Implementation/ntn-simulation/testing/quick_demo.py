#!/usr/bin/env python3
"""
Quick Demo of Large-Scale Testing Framework
============================================

Runs a simplified version of the testing framework to demonstrate
capabilities without requiring extensive computation time.

Author: Large-Scale Performance Testing Specialist
Date: 2025-11-17
"""

import asyncio
import numpy as np
import time
import json
import os
from datetime import datetime
from dataclasses import asdict
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing.visualize_results import TestResultsVisualizer


async def simulate_test_scenario(num_ues: int, scenario_name: str) -> dict:
    """
    Simulate a test scenario with realistic performance metrics

    Args:
        num_ues: Number of UEs
        scenario_name: Scenario name

    Returns:
        Dictionary with simulated results
    """
    print(f"\n[Simulating] {scenario_name} with {num_ues} UEs...")

    # Simulate test duration
    await asyncio.sleep(2.0)

    # Generate realistic performance metrics based on UE count
    # Performance degrades slightly with increased load

    # Base performance (10 UEs)
    base_latency = 8.5
    base_throughput = 95.0
    base_cpu = 15.0
    base_memory = 512.0

    # Scaling factors (realistic degradation)
    ue_factor = num_ues / 10.0

    # Latency increases sub-linearly with load
    latency_p99 = base_latency * (1 + np.log10(ue_factor) * 0.5) + np.random.uniform(-1, 1)

    # Throughput scales less than linearly
    throughput_msg_s = base_throughput * ue_factor * 0.85 + np.random.uniform(-10, 10)

    # CPU usage increases
    cpu_percent = min(95, base_cpu * ue_factor * 0.6 + np.random.uniform(-2, 2))

    # Memory usage (roughly linear)
    memory_mb = base_memory * ue_factor + np.random.uniform(-50, 50)

    # Handover success rate (decreases slightly with load)
    handover_success_rate = max(95, 99.5 - (num_ues / 200) + np.random.uniform(-0.5, 0.5))

    # Check if targets met
    target_latency_met = latency_p99 < 15.0
    target_throughput_met = throughput_msg_s > 100.0
    target_cpu_met = cpu_percent < 50.0
    target_memory_met = memory_mb < 4096.0

    results = {
        'scenario_name': scenario_name,
        'num_ues': num_ues,
        'duration_seconds': 120.0,  # 2 minutes
        'latency_mean': latency_p99 * 0.7,
        'latency_p50': latency_p99 * 0.75,
        'latency_p95': latency_p99 * 0.95,
        'latency_p99': latency_p99,
        'latency_max': latency_p99 * 1.2,
        'total_messages': int(throughput_msg_s * 120),
        'messages_per_second': throughput_msg_s,
        'ues_processed_per_second': throughput_msg_s / num_ues if num_ues > 0 else 0,
        'avg_cpu_percent': cpu_percent,
        'max_cpu_percent': cpu_percent * 1.15,
        'avg_memory_mb': memory_mb,
        'max_memory_mb': memory_mb * 1.1,
        'total_handovers': int(num_ues * 0.3),  # ~30% of UEs perform handover
        'successful_handovers': int(num_ues * 0.3 * handover_success_rate / 100),
        'handover_success_rate': handover_success_rate,
        'total_power_adjustments': int(num_ues * 2.5),  # Multiple adjustments per UE
        'power_increases': int(num_ues * 1.0),
        'power_decreases': int(num_ues * 1.5),
        'avg_link_margin_db': 10.0 + np.random.uniform(-2, 2),
        'min_link_margin_db': 5.0 + np.random.uniform(-1, 1),
        'link_availability_percent': max(95, 99.9 - (num_ues / 500)),
        'target_latency_met': target_latency_met,
        'target_throughput_met': target_throughput_met,
        'target_cpu_met': target_cpu_met,
        'target_memory_met': target_memory_met
    }

    # Print results
    status = "PASS" if all([
        target_latency_met, target_throughput_met, target_cpu_met, target_memory_met
    ]) else "FAIL"

    print(f"  Latency P99: {latency_p99:.2f} ms")
    print(f"  Throughput:  {throughput_msg_s:.1f} msg/s")
    print(f"  CPU:         {cpu_percent:.1f}%")
    print(f"  Memory:      {memory_mb:.1f} MB")
    print(f"  Status:      {status}")

    return results


async def run_quick_demo():
    """Run quick demonstration of testing framework"""
    print("="*80)
    print("NTN LARGE-SCALE TESTING FRAMEWORK - QUICK DEMONSTRATION")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    output_dir = "/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/test_results"
    os.makedirs(output_dir, exist_ok=True)

    # Initialize visualizer
    visualizer = TestResultsVisualizer(output_dir=output_dir)

    # Define test scenarios
    scenarios = [
        ("Scenario 1: Uniform Load (100 UEs)", 100),
        ("Scenario 2: High Density (200 UEs)", 200),
        ("Scenario 3: Global Coverage (500 UEs)", 500),
        ("Scenario 4: Rain Storm (100 UEs)", 100),
        ("Scenario 5: Peak Load (1000 UEs)", 1000),
    ]

    # Run scenarios
    all_results = []
    for scenario_name, num_ues in scenarios:
        print(f"\n{'='*80}")
        print(f"Running: {scenario_name}")
        print(f"{'='*80}")

        results = await simulate_test_scenario(num_ues, scenario_name)
        all_results.append(results)

    # Run stress test simulation
    print(f"\n{'='*80}")
    print("Simulating Stress Test (Gradual Load Increase)")
    print(f"{'='*80}")

    stress_test_points = []
    for num_ues in [10, 20, 50, 100, 200, 500]:
        print(f"\nStress Test Point: {num_ues} UEs")
        results = await simulate_test_scenario(num_ues, f"Stress Test - {num_ues} UEs")

        stress_test_point = {
            'num_ues': num_ues,
            'duration_seconds': results['duration_seconds'],
            'latency_p99_ms': results['latency_p99'],
            'throughput_msg_s': results['messages_per_second'],
            'cpu_percent': results['avg_cpu_percent'],
            'memory_mb': results['avg_memory_mb'],
            'handover_success_rate': results['handover_success_rate'],
            'all_targets_met': all([
                results['target_latency_met'],
                results['target_throughput_met'],
                results['target_cpu_met'],
                results['target_memory_met']
            ]),
            'degradation_detected': False,
            'bottleneck': None
        }

        stress_test_points.append(stress_test_point)

    # Generate visualizations
    print(f"\n{'='*80}")
    print("Generating Visualizations")
    print(f"{'='*80}\n")

    # 1. Scalability plots
    print("[Viz] Creating scalability analysis plots...")
    visualizer.create_scalability_plots(
        stress_test_points,
        title="NTN Platform Scalability Analysis - Demo Results"
    )

    # 2. Latency breakdown
    print("[Viz] Creating latency breakdown plot...")
    latency_breakdown = {
        'avg_sgp4_ms': 1.2,
        'avg_weather_ms': 2.5,
        'avg_e2_encoding_ms': 0.8,
        'avg_xapp_ms': 1.5,
        'avg_e2_network_ms': 0.5,
    }
    visualizer.create_latency_breakdown_plot(latency_breakdown)

    # 3. Performance comparison
    print("[Viz] Creating performance comparison chart...")
    visualizer.create_performance_comparison_bar(
        all_results,
        title="NTN Platform Performance Across Test Scenarios - Demo"
    )

    # Generate reports
    print(f"\n{'='*80}")
    print("Generating Reports")
    print(f"{'='*80}\n")

    # Executive summary
    print("[Report] Generating executive summary...")
    exec_summary_path = os.path.join(output_dir, "DEMO_EXECUTIVE_SUMMARY.txt")

    with open(exec_summary_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("NTN-O-RAN PLATFORM - LARGE-SCALE TESTING DEMONSTRATION REPORT\n")
        f.write("="*80 + "\n\n")

        f.write(f"Demo Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Scenarios: {len(all_results)}\n")
        f.write(f"Stress Test Points: {len(stress_test_points)}\n\n")

        f.write("="*80 + "\n")
        f.write("DEMONSTRATION RESULTS SUMMARY\n")
        f.write("="*80 + "\n\n")

        f.write(f"{'Scenario':<40} {'UEs':<8} {'Latency P99':<14} {'Throughput':<14} {'Status':<10}\n")
        f.write("-" * 80 + "\n")

        scenarios_passed = 0
        for result in all_results:
            short_name = result['scenario_name'][:39]
            status = "PASS" if all([
                result['target_latency_met'],
                result['target_throughput_met'],
                result['target_cpu_met'],
                result['target_memory_met']
            ]) else "FAIL"

            if status == "PASS":
                scenarios_passed += 1

            f.write(f"{short_name:<40} "
                   f"{result['num_ues']:<8} "
                   f"{result['latency_p99']:<14.2f} "
                   f"{result['messages_per_second']:<14.1f} "
                   f"{status:<10}\n")

        f.write("\n" + "="*80 + "\n")
        f.write("KEY FINDINGS (SIMULATED DATA)\n")
        f.write("="*80 + "\n\n")

        f.write(f"Scenarios Passing All Targets: {scenarios_passed}/{len(all_results)}\n\n")

        # Find max UEs passing
        max_ues_passed = 0
        for result in all_results:
            if all([result['target_latency_met'], result['target_throughput_met'],
                   result['target_cpu_met'], result['target_memory_met']]):
                max_ues_passed = max(max_ues_passed, result['num_ues'])

        f.write(f"Maximum UEs (All Targets Met): {max_ues_passed}\n\n")

        f.write("PRODUCTION READINESS ASSESSMENT:\n")
        if max_ues_passed >= 100:
            f.write("  ✓ Platform meets 100 UE requirement\n")
            f.write("  ✓ Ready for production deployment\n\n")
        else:
            f.write("  ✗ Platform does not meet 100 UE requirement\n")
            f.write("  ✗ Further optimization needed\n\n")

        if max_ues_passed >= 200:
            f.write("  ✓ Platform exceeds target goals (200+ UEs)\n\n")

        if max_ues_passed >= 500:
            f.write("  ✓ Platform meets stretch goals (500+ UEs)\n\n")

        f.write("="*80 + "\n")
        f.write("STRESS TEST ANALYSIS\n")
        f.write("="*80 + "\n\n")

        f.write(f"{'UEs':<8} {'Latency':<12} {'Throughput':<14} {'CPU %':<10} {'Memory MB':<12} {'Status':<10}\n")
        f.write("-" * 80 + "\n")

        for point in stress_test_points:
            status = "PASS" if point['all_targets_met'] else "FAIL"
            f.write(f"{point['num_ues']:<8} "
                   f"{point['latency_p99_ms']:<12.2f} "
                   f"{point['throughput_msg_s']:<14.1f} "
                   f"{point['cpu_percent']:<10.1f} "
                   f"{point['memory_mb']:<12.1f} "
                   f"{status:<10}\n")

        # Scalability analysis
        if len(stress_test_points) >= 2:
            first = stress_test_points[0]
            last = stress_test_points[-1]

            ue_ratio = last['num_ues'] / first['num_ues']
            throughput_ratio = last['throughput_msg_s'] / first['throughput_msg_s']
            scalability_efficiency = (throughput_ratio / ue_ratio) * 100

            f.write(f"\nScalability Analysis:\n")
            f.write(f"  UE Increase: {ue_ratio:.1f}x ({first['num_ues']} -> {last['num_ues']})\n")
            f.write(f"  Throughput Increase: {throughput_ratio:.1f}x\n")
            f.write(f"  Scalability Efficiency: {scalability_efficiency:.1f}%\n")

            if scalability_efficiency > 90:
                f.write(f"  Assessment: ✓ Excellent scalability\n")
            elif scalability_efficiency > 70:
                f.write(f"  Assessment: ✓ Good scalability\n")
            else:
                f.write(f"  Assessment: ⚠ Moderate scalability\n")

        f.write("\n" + "="*80 + "\n")
        f.write("NOTE: This is a DEMONSTRATION using simulated data.\n")
        f.write("For actual performance validation, run full test suite.\n")
        f.write("="*80 + "\n")

    print(f"[Report] Executive summary saved: {exec_summary_path}")

    # Save all results to JSON
    json_path = os.path.join(output_dir, "demo_results.json")
    demo_data = {
        'execution_time': datetime.now().isoformat(),
        'scenario_results': all_results,
        'stress_test_results': stress_test_points,
        'note': 'This is demonstration data with simulated performance metrics'
    }

    with open(json_path, 'w') as f:
        json.dump(demo_data, f, indent=2)

    print(f"[Report] All results saved: {json_path}")

    print(f"\n{'='*80}")
    print("DEMONSTRATION COMPLETE")
    print(f"{'='*80}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nResults Directory: {output_dir}")
    print("\nGenerated Files:")
    print("  - scalability_analysis.png         (6 scalability plots)")
    print("  - latency_breakdown.png            (Component breakdown)")
    print("  - performance_comparison.png       (Scenario comparison)")
    print("  - DEMO_EXECUTIVE_SUMMARY.txt       (Executive summary)")
    print("  - demo_results.json                (All results)")
    print(f"{'='*80}\n")

    # Print file list
    print("Files in output directory:")
    for file in sorted(os.listdir(output_dir)):
        filepath = os.path.join(output_dir, file)
        size = os.path.getsize(filepath)
        print(f"  - {file:<40} ({size:>8} bytes)")


if __name__ == "__main__":
    asyncio.run(run_quick_demo())
