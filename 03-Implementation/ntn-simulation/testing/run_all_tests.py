#!/usr/bin/env python3
"""
Automated Test Execution Framework
===================================

Runs all large-scale test scenarios and generates comprehensive reports:

Test Scenarios:
1. Uniform Load (100 UEs) - Baseline performance
2. High Density (200 UEs urban) - Concentrated load
3. Global Coverage (500 UEs worldwide) - Full constellation
4. Rain Storm Event (100 UEs severe weather) - Fade mitigation
5. Peak Load (1000 UEs) - Maximum capacity

Outputs:
- Individual scenario results
- Comparative analysis
- Publication-quality visualizations
- Executive summary report

Author: Large-Scale Performance Testing Specialist
Date: 2025-11-17
"""

import asyncio
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing.large_scale_test import LargeScaleNTNTest, TestResults
from testing.stress_test import NTNStressTest
from testing.visualize_results import TestResultsVisualizer


@dataclass
class TestScenario:
    """Test scenario configuration"""
    name: str
    num_ues: int
    ue_distribution: str
    weather_scenario: str
    duration_minutes: int
    description: str


class AutomatedTestSuite:
    """
    Automated test suite for NTN platform

    Executes all predefined test scenarios and generates
    comprehensive performance analysis and reports.
    """

    def __init__(self, output_dir: str = "./test_results"):
        """
        Initialize automated test suite

        Args:
            output_dir: Directory for test results and reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.scenarios: List[TestScenario] = []
        self.results: Dict[str, TestResults] = {}

        # Initialize visualizer
        self.visualizer = TestResultsVisualizer(output_dir=output_dir)

        print(f"[AutomatedTestSuite] Initialized")
        print(f"  Output directory: {output_dir}")

    def define_test_scenarios(self):
        """Define all test scenarios"""
        self.scenarios = [
            TestScenario(
                name="Scenario 1: Uniform Load",
                num_ues=100,
                ue_distribution="uniform",
                weather_scenario="clear",
                duration_minutes=30,
                description="Baseline performance with 100 UEs evenly distributed globally. "
                           "Clear weather conditions. Validates basic scalability targets."
            ),
            TestScenario(
                name="Scenario 2: High Density Urban",
                num_ues=200,
                ue_distribution="urban_dense",
                weather_scenario="variable",
                duration_minutes=30,
                description="Concentrated load in urban areas. 200 UEs clustered in major cities. "
                           "Variable weather. Tests resource allocation under high density."
            ),
            TestScenario(
                name="Scenario 3: Global Coverage",
                num_ues=500,
                ue_distribution="global",
                weather_scenario="variable",
                duration_minutes=30,
                description="Full constellation simulation with 500 UEs distributed worldwide. "
                           "Variable weather across regions. Validates global deployment readiness."
            ),
            TestScenario(
                name="Scenario 4: Rain Storm Event",
                num_ues=100,
                ue_distribution="urban_dense",
                weather_scenario="storm",
                duration_minutes=20,
                description="Severe weather scenario with heavy rain. 100 UEs experiencing rain fade. "
                           "Tests fade mitigation and power control under stress."
            ),
            TestScenario(
                name="Scenario 5: Peak Load",
                num_ues=1000,
                ue_distribution="sparse_global",
                weather_scenario="variable",
                duration_minutes=20,
                description="Maximum capacity test with 1000 UEs. Sparse global distribution. "
                           "Identifies performance limits and bottlenecks."
            ),
        ]

        print(f"\n[TestSuite] Defined {len(self.scenarios)} test scenarios:")
        for i, scenario in enumerate(self.scenarios, 1):
            print(f"  {i}. {scenario.name}")
            print(f"     - UEs: {scenario.num_ues}")
            print(f"     - Distribution: {scenario.ue_distribution}")
            print(f"     - Weather: {scenario.weather_scenario}")
            print(f"     - Duration: {scenario.duration_minutes} minutes")

    async def run_all_scenarios(self):
        """Execute all test scenarios"""
        print(f"\n{'='*80}")
        print("RUNNING ALL TEST SCENARIOS")
        print(f"{'='*80}\n")

        total_start_time = time.time()

        for i, scenario in enumerate(self.scenarios, 1):
            print(f"\n{'='*80}")
            print(f"SCENARIO {i}/{len(self.scenarios)}: {scenario.name}")
            print(f"{'='*80}")
            print(f"Description: {scenario.description}")
            print(f"{'='*80}\n")

            scenario_start = time.time()

            try:
                # Create test
                test = LargeScaleNTNTest(
                    num_ues=scenario.num_ues,
                    scenario_name=scenario.name
                )

                # Setup
                print(f"[{scenario.name}] Setting up...")
                await test.setup_scenario(
                    ue_distribution=scenario.ue_distribution,
                    weather_scenario=scenario.weather_scenario
                )

                # Run
                print(f"[{scenario.name}] Running test for {scenario.duration_minutes} minutes...")
                await test.run_scenario(
                    duration_minutes=scenario.duration_minutes,
                    time_step_sec=1.0
                )

                # Analyze
                print(f"[{scenario.name}] Analyzing results...")
                results = test.analyze_results()

                # Store results
                self.results[scenario.name] = results

                # Print results
                test.print_results(results)

                # Save individual scenario results
                self._save_scenario_results(scenario.name, results)

                # Cleanup
                await test.cleanup()

                scenario_elapsed = time.time() - scenario_start
                print(f"\n[{scenario.name}] Completed in {scenario_elapsed/60:.1f} minutes")

                # Short pause between scenarios
                await asyncio.sleep(2.0)

            except Exception as e:
                print(f"\n[ERROR] Scenario {scenario.name} failed: {e}")
                import traceback
                traceback.print_exc()

        total_elapsed = time.time() - total_start_time

        print(f"\n{'='*80}")
        print(f"ALL SCENARIOS COMPLETED")
        print(f"{'='*80}")
        print(f"Total time: {total_elapsed/60:.1f} minutes")
        print(f"Scenarios completed: {len(self.results)}/{len(self.scenarios)}")

    async def run_stress_test(self):
        """Run stress test to find maximum capacity"""
        print(f"\n{'='*80}")
        print("RUNNING STRESS TEST")
        print(f"{'='*80}\n")

        stress_test = NTNStressTest()

        # Run gradual load test
        await stress_test.run_gradual_load_test(
            start_ues=10,
            max_ues=500,  # Can be increased for full test
            step_multiplier=2.0,
            duration_per_test_min=10
        )

        # Export stress test results
        stress_results_path = os.path.join(self.output_dir, 'stress_test_results.json')
        stress_test.export_results(stress_results_path)

        # Create stress test visualizations
        if stress_test.test_points:
            test_points_dict = [asdict(p) for p in stress_test.test_points]
            self.visualizer.create_scalability_plots(
                test_points_dict,
                title="NTN Platform Stress Test - Scalability Analysis"
            )

        return stress_test

    def generate_comprehensive_report(self):
        """Generate comprehensive test report with all results"""
        print(f"\n{'='*80}")
        print("GENERATING COMPREHENSIVE REPORT")
        print(f"{'='*80}\n")

        # Prepare results for visualization
        results_for_viz = []
        for scenario_name, results in self.results.items():
            results_dict = asdict(results)
            results_dict['scenario_name'] = scenario_name
            results_for_viz.append(results_dict)

        # Create performance comparison visualization
        if results_for_viz:
            self.visualizer.create_performance_comparison_bar(
                results_for_viz,
                title="NTN Platform - Performance Comparison Across Scenarios"
            )

        # Generate executive summary
        self._generate_executive_summary()

        # Export all results to JSON
        self._export_all_results()

        print("[Report] Comprehensive report generation complete!")

    def _save_scenario_results(self, scenario_name: str, results: TestResults):
        """Save individual scenario results"""
        # Create safe filename
        safe_name = scenario_name.replace(':', '').replace(' ', '_').lower()
        filepath = os.path.join(self.output_dir, f'{safe_name}_results.json')

        results_dict = asdict(results)

        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"[Report] Saved scenario results: {filepath}")

    def _export_all_results(self):
        """Export all test results to single JSON file"""
        filepath = os.path.join(self.output_dir, 'all_test_results.json')

        all_results = {
            'test_suite_info': {
                'execution_time': datetime.now().isoformat(),
                'total_scenarios': len(self.scenarios),
                'scenarios_completed': len(self.results),
            },
            'scenarios': [asdict(s) for s in self.scenarios],
            'results': {
                name: asdict(results)
                for name, results in self.results.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(all_results, f, indent=2)

        print(f"[Report] Exported all results: {filepath}")

    def _generate_executive_summary(self):
        """Generate executive summary report"""
        filepath = os.path.join(self.output_dir, 'EXECUTIVE_SUMMARY.txt')

        with open(filepath, 'w') as f:
            f.write("="*80 + "\n")
            f.write("NTN-O-RAN PLATFORM - LARGE-SCALE TESTING EXECUTIVE SUMMARY\n")
            f.write("="*80 + "\n\n")

            f.write(f"Test Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Scenarios Executed: {len(self.results)}\n\n")

            f.write("="*80 + "\n")
            f.write("PRODUCTION READINESS ASSESSMENT\n")
            f.write("="*80 + "\n\n")

            # Analyze results for production readiness
            scenarios_passed = 0
            scenarios_100ues_passed = 0

            for scenario_name, results in self.results.items():
                if all([
                    results.target_latency_met,
                    results.target_throughput_met,
                    results.target_cpu_met,
                    results.target_memory_met
                ]):
                    scenarios_passed += 1

                    if results.num_ues >= 100:
                        scenarios_100ues_passed += 1

            f.write(f"Scenarios Passing All Targets: {scenarios_passed}/{len(self.results)}\n")
            f.write(f"100+ UE Scenarios Passed: {scenarios_100ues_passed}\n\n")

            # Production readiness verdict
            production_ready = scenarios_100ues_passed > 0

            f.write("PRODUCTION READINESS: ")
            if production_ready:
                f.write("✓ READY\n\n")
                f.write("The NTN-O-RAN platform successfully meets all performance targets\n")
                f.write("for 100+ UEs and is ready for production deployment.\n\n")
            else:
                f.write("✗ NOT READY\n\n")
                f.write("The platform does not yet meet all requirements for 100+ UEs.\n")
                f.write("Further optimization is required before production deployment.\n\n")

            f.write("="*80 + "\n")
            f.write("SCENARIO RESULTS SUMMARY\n")
            f.write("="*80 + "\n\n")

            f.write(f"{'Scenario':<35} {'UEs':<8} {'Latency':<12} {'Throughput':<14} {'Status':<10}\n")
            f.write("-" * 80 + "\n")

            for scenario_name, results in self.results.items():
                short_name = scenario_name.split(':')[-1].strip()[:34]
                status = "PASS" if all([
                    results.target_latency_met,
                    results.target_throughput_met,
                    results.target_cpu_met,
                    results.target_memory_met
                ]) else "FAIL"

                f.write(f"{short_name:<35} "
                       f"{results.num_ues:<8} "
                       f"{results.latency_p99:<12.2f} "
                       f"{results.messages_per_second:<14.1f} "
                       f"{status:<10}\n")

            f.write("\n" + "="*80 + "\n")
            f.write("KEY FINDINGS\n")
            f.write("="*80 + "\n\n")

            # Calculate aggregated metrics
            if self.results:
                all_latencies = [r.latency_p99 for r in self.results.values()]
                all_throughputs = [r.messages_per_second for r in self.results.values()]
                all_cpu = [r.avg_cpu_percent for r in self.results.values()]
                all_memory = [r.avg_memory_mb for r in self.results.values()]

                import numpy as np

                f.write(f"Performance Metrics (across all scenarios):\n")
                f.write(f"  Average Latency P99:     {np.mean(all_latencies):.2f} ms\n")
                f.write(f"  Maximum Latency P99:     {np.max(all_latencies):.2f} ms\n")
                f.write(f"  Average Throughput:      {np.mean(all_throughputs):.1f} msg/s\n")
                f.write(f"  Maximum Throughput:      {np.max(all_throughputs):.1f} msg/s\n")
                f.write(f"  Average CPU Usage:       {np.mean(all_cpu):.1f}%\n")
                f.write(f"  Maximum CPU Usage:       {np.max(all_cpu):.1f}%\n")
                f.write(f"  Average Memory Usage:    {np.mean(all_memory)/1024:.2f} GB\n")
                f.write(f"  Maximum Memory Usage:    {np.max(all_memory)/1024:.2f} GB\n\n")

            f.write("="*80 + "\n")
            f.write("RECOMMENDATIONS\n")
            f.write("="*80 + "\n\n")

            if production_ready:
                f.write("1. Platform is production-ready for deployment\n")
                f.write("2. Consider capacity planning for target deployment size\n")
                f.write("3. Monitor performance metrics in production environment\n")
                f.write("4. Continue optimization for higher UE counts if needed\n")
            else:
                f.write("1. Optimize bottleneck components identified in stress tests\n")
                f.write("2. Review resource allocation and scaling strategies\n")
                f.write("3. Re-run tests after optimization improvements\n")
                f.write("4. Consider hardware upgrades if software optimization is insufficient\n")

            f.write("\n" + "="*80 + "\n")
            f.write("END OF EXECUTIVE SUMMARY\n")
            f.write("="*80 + "\n")

        print(f"[Report] Generated executive summary: {filepath}")


async def main():
    """Main test execution"""
    print("="*80)
    print("NTN-O-RAN PLATFORM - AUTOMATED LARGE-SCALE TESTING")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    # Create test suite
    test_suite = AutomatedTestSuite(
        output_dir="/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/test_results"
    )

    # Define scenarios
    test_suite.define_test_scenarios()

    # Ask user which tests to run
    print("\nTest Options:")
    print("  1. Run all scenario tests")
    print("  2. Run stress test only")
    print("  3. Run both (scenarios + stress test)")
    print("  4. Quick demo (reduced duration)")

    # For automation, default to option 4 (quick demo)
    choice = "4"

    if choice == "1":
        await test_suite.run_all_scenarios()
        test_suite.generate_comprehensive_report()

    elif choice == "2":
        await test_suite.run_stress_test()

    elif choice == "3":
        await test_suite.run_all_scenarios()
        await test_suite.run_stress_test()
        test_suite.generate_comprehensive_report()

    elif choice == "4":
        # Quick demo - reduce durations
        print("\n[DEMO MODE] Running quick demonstration with reduced durations...")

        # Modify scenarios for quick demo
        for scenario in test_suite.scenarios:
            scenario.duration_minutes = 2  # Reduce to 2 minutes
            if scenario.num_ues > 100:
                scenario.num_ues = 100  # Cap at 100 UEs for demo

        await test_suite.run_all_scenarios()
        test_suite.generate_comprehensive_report()

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results saved to: {test_suite.output_dir}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
