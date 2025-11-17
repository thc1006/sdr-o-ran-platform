#!/usr/bin/env python3
"""
Master Baseline Comparison Runner
==================================

Complete end-to-end execution of baseline comparison demonstrating
predictive NTN superiority over reactive traditional methods.

Generates all artifacts for IEEE paper publication.

Author: Baseline Comparison & Research Validation Specialist
Date: 2025-11-17
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baseline.comparative_simulation import ComparativeSimulator, ScenarioConfig
from baseline.statistical_analysis import StatisticalAnalyzer


async def main():
    """Run complete baseline comparison"""
    print("="*80)
    print("BASELINE COMPARISON: Predictive NTN vs Reactive Traditional")
    print("="*80)
    print(f"Started: {datetime.now().isoformat()}")
    print("="*80)

    # Step 1: Create simulator
    print("\n[Step 1] Initializing Comparative Simulator...")
    simulator = ComparativeSimulator()

    # Step 2: Define scenarios (quick test scenarios for demo)
    print("\n[Step 2] Defining Test Scenarios...")
    simulator.scenarios = [
        ScenarioConfig(
            name="Quick_LEO_Pass_Clear_Weather",
            description="Quick LEO pass test with clear weather",
            num_ues=20,
            duration_minutes=5,
            ue_distribution='global',
            weather_scenario='clear',
            satellite_count=50
        ),
        ScenarioConfig(
            name="Quick_LEO_Pass_Rain_Storm",
            description="Quick LEO pass test during rain",
            num_ues=20,
            duration_minutes=5,
            ue_distribution='global',
            weather_scenario='storm',
            satellite_count=50
        ),
    ]
    print(f"  Defined {len(simulator.scenarios)} quick test scenarios")

    # Step 3: Run comparative simulations
    print("\n[Step 3] Running Comparative Simulations...")
    print("  This will take several minutes...")
    await simulator.run_all_scenarios()

    # Step 4: Save simulation results
    print("\n[Step 4] Saving Simulation Results...")
    simulator.save_results('baseline_comparison_results.json')

    # Step 5: Statistical analysis
    print("\n[Step 5] Performing Statistical Analysis...")
    analyzer = StatisticalAnalyzer(alpha=0.05)

    for result in simulator.results:
        summary = analyzer.analyze_comparison_results(result)
        analyzer.summaries.append(summary)
        analyzer.print_statistical_summary(summary)

    # Step 6: Save statistical analysis
    print("\n[Step 6] Saving Statistical Analysis...")
    analyzer.save_analysis('baseline_statistical_analysis.json')

    # Step 7: Generate LaTeX table
    print("\n[Step 7] Generating LaTeX Table for Paper...")
    latex_table = analyzer.generate_latex_table(analyzer.summaries)
    latex_file = os.path.join(os.path.dirname(__file__), 'paper_table.tex')
    with open(latex_file, 'w') as f:
        f.write(latex_table)
    print(f"  LaTeX table saved to: {latex_file}")

    # Step 8: Print final summary
    print("\n" + "="*80)
    print("BASELINE COMPARISON COMPLETE")
    print("="*80)

    print(f"\nKey Findings:")
    for summary in analyzer.summaries:
        print(f"\nScenario: {summary.scenario_name}")

        if summary.handover_success_test:
            hs = summary.handover_success_test
            print(f"  Handover Success:  {hs.reactive_mean:.1f}% → {hs.predictive_mean:.1f}% "
                  f"(+{hs.improvement_percent:.1f}%, p={hs.p_value:.4f})")

        if summary.interruption_time_test:
            it = summary.interruption_time_test
            print(f"  Interruption Time: {it.reactive_mean:.1f}ms → {it.predictive_mean:.1f}ms "
                  f"({it.improvement_percent:.1f}% reduction, p={it.p_value:.4f})")

        if summary.throughput_test:
            tp = summary.throughput_test
            print(f"  Throughput:        {tp.reactive_mean:.1f}Mbps → {tp.predictive_mean:.1f}Mbps "
                  f"(+{tp.improvement_percent:.1f}%, p={tp.p_value:.4f})")

        if summary.packet_loss_test:
            pl = summary.packet_loss_test
            print(f"  Packet Loss:       {pl.reactive_mean:.2f}% → {pl.predictive_mean:.2f}% "
                  f"({pl.improvement_percent:.1f}% reduction, p={pl.p_value:.4f})")

        print(f"  Statistical Significance: {summary.highly_significant_count}/{summary.total_tests} "
              f"metrics highly significant (p<0.01)")

    print("\n" + "="*80)
    print("Generated Artifacts:")
    print("="*80)
    print(f"  1. Simulation Results:     baseline_comparison_results.json")
    print(f"  2. Statistical Analysis:   baseline_statistical_analysis.json")
    print(f"  3. LaTeX Table:            paper_table.tex")
    print(f"\nNext Steps:")
    print(f"  - Run visualization module to generate plots")
    print(f"  - Include results in IEEE paper Section V")
    print(f"  - Highlight statistically significant improvements (p<0.01)")
    print("="*80)

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == '__main__':
    asyncio.run(main())
