#!/usr/bin/env python3
"""
Test Results Visualization
===========================

Creates publication-quality plots for large-scale test results:
- Latency vs Number of UEs (with P50/P95/P99)
- Throughput vs Number of UEs
- CPU Usage vs Number of UEs
- Memory Usage vs Number of UEs
- Handover Success Rate
- Power Control Accuracy
- Scalability Analysis
- E2E Latency Breakdown

Author: Large-Scale Performance Testing Specialist
Date: 2025-11-17
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os

# Configure matplotlib for publication-quality plots
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 300


class TestResultsVisualizer:
    """
    Visualize large-scale test results

    Creates comprehensive plots for analyzing:
    - Performance scalability
    - Resource utilization
    - System bottlenecks
    - Quality metrics
    """

    def __init__(self, output_dir: str = "./test_results"):
        """
        Initialize visualizer

        Args:
            output_dir: Directory for output plots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        print(f"[Visualizer] Output directory: {output_dir}")

    def create_scalability_plots(
        self,
        test_points: List[Dict[str, Any]],
        title: str = "NTN Platform Scalability Analysis"
    ):
        """
        Create comprehensive scalability analysis plots

        Args:
            test_points: List of stress test data points
            title: Main title for the plot
        """
        if not test_points:
            print("[Warning] No test points to visualize")
            return

        # Extract data
        num_ues = [p['num_ues'] for p in test_points]
        latency_p99 = [p['latency_p99_ms'] for p in test_points]
        throughput = [p['throughput_msg_s'] for p in test_points]
        cpu_percent = [p['cpu_percent'] for p in test_points]
        memory_mb = [p['memory_mb'] for p in test_points]
        handover_success = [p['handover_success_rate'] for p in test_points]

        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(title, fontsize=16, fontweight='bold')

        # 1. Latency vs Number of UEs
        ax = axes[0, 0]
        ax.plot(num_ues, latency_p99, 'o-', color='#2E86AB', linewidth=2, markersize=8)
        ax.axhline(y=15, color='r', linestyle='--', label='Target (15ms)', linewidth=2)
        ax.axhline(y=50, color='orange', linestyle='--', label='Threshold (50ms)', linewidth=2)
        ax.set_xlabel('Number of UEs')
        ax.set_ylabel('Latency P99 (ms)')
        ax.set_title('E2E Latency vs Load')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xscale('log')

        # 2. Throughput vs Number of UEs
        ax = axes[0, 1]
        ax.plot(num_ues, throughput, 'o-', color='#A23B72', linewidth=2, markersize=8)
        ax.axhline(y=100, color='r', linestyle='--', label='Target (100 msg/s)', linewidth=2)
        ax.set_xlabel('Number of UEs')
        ax.set_ylabel('Throughput (msg/s)')
        ax.set_title('System Throughput vs Load')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xscale('log')

        # 3. CPU Usage vs Number of UEs
        ax = axes[0, 2]
        ax.plot(num_ues, cpu_percent, 'o-', color='#F18F01', linewidth=2, markersize=8)
        ax.axhline(y=50, color='g', linestyle='--', label='Target (50%)', linewidth=2)
        ax.axhline(y=95, color='r', linestyle='--', label='Limit (95%)', linewidth=2)
        ax.set_xlabel('Number of UEs')
        ax.set_ylabel('CPU Usage (%)')
        ax.set_title('CPU Utilization vs Load')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xscale('log')

        # 4. Memory Usage vs Number of UEs
        ax = axes[1, 0]
        memory_gb = [m / 1024 for m in memory_mb]
        ax.plot(num_ues, memory_gb, 'o-', color='#6A994E', linewidth=2, markersize=8)
        ax.axhline(y=4, color='g', linestyle='--', label='Target (4 GB)', linewidth=2)
        ax.axhline(y=32, color='r', linestyle='--', label='Limit (32 GB)', linewidth=2)
        ax.set_xlabel('Number of UEs')
        ax.set_ylabel('Memory Usage (GB)')
        ax.set_title('Memory Utilization vs Load')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xscale('log')

        # 5. Handover Success Rate
        ax = axes[1, 1]
        ax.plot(num_ues, handover_success, 'o-', color='#BC4B51', linewidth=2, markersize=8)
        ax.axhline(y=99, color='g', linestyle='--', label='Target (99%)', linewidth=2)
        ax.set_xlabel('Number of UEs')
        ax.set_ylabel('Success Rate (%)')
        ax.set_title('Handover Success Rate vs Load')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_ylim([90, 101])
        ax.set_xscale('log')

        # 6. Scalability Efficiency
        ax = axes[1, 2]
        if len(num_ues) > 1:
            # Calculate scalability efficiency
            baseline_throughput = throughput[0]
            baseline_ues = num_ues[0]

            scalability_efficiency = []
            for i, (ues, tput) in enumerate(zip(num_ues, throughput)):
                ue_ratio = ues / baseline_ues
                throughput_ratio = tput / baseline_throughput
                efficiency = (throughput_ratio / ue_ratio) * 100 if ue_ratio > 0 else 0
                scalability_efficiency.append(efficiency)

            ax.plot(num_ues, scalability_efficiency, 'o-', color='#5F0F40', linewidth=2, markersize=8)
            ax.axhline(y=90, color='g', linestyle='--', label='Excellent (90%)', linewidth=2)
            ax.axhline(y=70, color='orange', linestyle='--', label='Good (70%)', linewidth=2)
            ax.set_xlabel('Number of UEs')
            ax.set_ylabel('Scalability Efficiency (%)')
            ax.set_title('Scalability Efficiency vs Load')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.set_xscale('log')

        plt.tight_layout()

        # Save figure
        output_path = os.path.join(self.output_dir, 'scalability_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[Visualizer] Saved scalability plots: {output_path}")

        plt.close()

    def create_latency_breakdown_plot(
        self,
        latency_stats: Dict[str, float],
        title: str = "E2E Latency Component Breakdown"
    ):
        """
        Create latency component breakdown pie chart

        Args:
            latency_stats: Dictionary with component latency averages
            title: Plot title
        """
        # Extract components
        components = {
            'SGP4 Propagation': latency_stats.get('avg_sgp4_ms', 0),
            'Weather Calculation': latency_stats.get('avg_weather_ms', 0),
            'E2 Encoding': latency_stats.get('avg_e2_encoding_ms', 0),
            'xApp Decision': latency_stats.get('avg_xapp_ms', 0),
            'E2 Network': latency_stats.get('avg_e2_network_ms', 0.5),  # Assumed
        }

        # Remove zero components
        components = {k: v for k, v in components.items() if v > 0}

        if not components:
            print("[Warning] No latency components to visualize")
            return

        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))

        colors = ['#2E86AB', '#A23B72', '#F18F01', '#6A994E', '#BC4B51']
        explode = [0.05] * len(components)  # Slightly separate slices

        wedges, texts, autotexts = ax.pie(
            components.values(),
            labels=components.keys(),
            autopct='%1.1f%%',
            colors=colors[:len(components)],
            explode=explode,
            shadow=True,
            startangle=90
        )

        # Enhance text
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Add legend with absolute values
        legend_labels = [f'{k}: {v:.2f} ms' for k, v in components.items()]
        ax.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1))

        plt.tight_layout()

        # Save
        output_path = os.path.join(self.output_dir, 'latency_breakdown.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[Visualizer] Saved latency breakdown: {output_path}")

        plt.close()

    def create_performance_comparison_bar(
        self,
        test_results: List[Dict[str, Any]],
        title: str = "Performance Comparison Across Scenarios"
    ):
        """
        Create bar chart comparing performance across different test scenarios

        Args:
            test_results: List of test result dictionaries
            title: Plot title
        """
        if not test_results:
            print("[Warning] No test results to visualize")
            return

        # Extract data
        scenario_names = [r.get('scenario_name', f"Scenario {i+1}") for i, r in enumerate(test_results)]
        latencies = [r.get('latency_p99', 0) for r in test_results]
        throughputs = [r.get('messages_per_second', 0) for r in test_results]
        cpu_usage = [r.get('avg_cpu_percent', 0) for r in test_results]
        memory_usage = [r.get('avg_memory_mb', 0) / 1024 for r in test_results]  # Convert to GB

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(title, fontsize=16, fontweight='bold')

        x = np.arange(len(scenario_names))
        width = 0.6

        # 1. Latency comparison
        ax = axes[0, 0]
        bars = ax.bar(x, latencies, width, color='#2E86AB', edgecolor='black', linewidth=1.2)
        ax.axhline(y=15, color='r', linestyle='--', label='Target', linewidth=2)
        ax.set_ylabel('Latency P99 (ms)')
        ax.set_title('E2E Latency (P99)')
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=9)

        # 2. Throughput comparison
        ax = axes[0, 1]
        bars = ax.bar(x, throughputs, width, color='#A23B72', edgecolor='black', linewidth=1.2)
        ax.axhline(y=100, color='r', linestyle='--', label='Target', linewidth=2)
        ax.set_ylabel('Throughput (msg/s)')
        ax.set_title('System Throughput')
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=9)

        # 3. CPU usage comparison
        ax = axes[1, 0]
        bars = ax.bar(x, cpu_usage, width, color='#F18F01', edgecolor='black', linewidth=1.2)
        ax.axhline(y=50, color='r', linestyle='--', label='Target', linewidth=2)
        ax.set_ylabel('CPU Usage (%)')
        ax.set_title('CPU Utilization')
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=9)

        # 4. Memory usage comparison
        ax = axes[1, 1]
        bars = ax.bar(x, memory_usage, width, color='#6A994E', edgecolor='black', linewidth=1.2)
        ax.axhline(y=4, color='r', linestyle='--', label='Target', linewidth=2)
        ax.set_ylabel('Memory Usage (GB)')
        ax.set_title('Memory Utilization')
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=9)

        plt.tight_layout()

        # Save
        output_path = os.path.join(self.output_dir, 'performance_comparison.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[Visualizer] Saved performance comparison: {output_path}")

        plt.close()

    def create_time_series_plot(
        self,
        metrics_time_series: List[Dict[str, Any]],
        metric_name: str,
        title: Optional[str] = None,
        ylabel: Optional[str] = None
    ):
        """
        Create time series plot for a specific metric

        Args:
            metrics_time_series: List of timestamped metrics
            metric_name: Name of metric to plot
            title: Plot title
            ylabel: Y-axis label
        """
        if not metrics_time_series:
            print(f"[Warning] No time series data for {metric_name}")
            return

        # Extract data
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in metrics_time_series]
        values = [m.get(metric_name, 0) for m in metrics_time_series]

        # Create plot
        fig, ax = plt.subplots(figsize=(14, 6))

        ax.plot(timestamps, values, '-', color='#2E86AB', linewidth=1.5, alpha=0.8)
        ax.fill_between(timestamps, values, alpha=0.2, color='#2E86AB')

        ax.set_xlabel('Time')
        ax.set_ylabel(ylabel or metric_name)
        ax.set_title(title or f'{metric_name} Over Time')
        ax.grid(True, alpha=0.3)

        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        # Save
        safe_metric_name = metric_name.replace(' ', '_').lower()
        output_path = os.path.join(self.output_dir, f'timeseries_{safe_metric_name}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[Visualizer] Saved time series: {output_path}")

        plt.close()

    def generate_summary_report(
        self,
        stress_test_results: Dict[str, Any],
        output_filename: str = "test_summary_report.txt"
    ):
        """
        Generate text summary report

        Args:
            stress_test_results: Stress test results dictionary
            output_filename: Output file name
        """
        output_path = os.path.join(self.output_dir, output_filename)

        with open(output_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("NTN PLATFORM LARGE-SCALE TESTING - SUMMARY REPORT\n")
            f.write("="*80 + "\n\n")

            f.write(f"Report Generated: {datetime.now().isoformat()}\n")
            f.write(f"Test Duration: {stress_test_results.get('duration_seconds', 0)/60:.1f} minutes\n\n")

            f.write("="*80 + "\n")
            f.write("EXECUTIVE SUMMARY\n")
            f.write("="*80 + "\n\n")

            # Test points summary
            test_points = stress_test_results.get('test_points', [])
            if test_points:
                f.write(f"Test Points Completed: {len(test_points)}\n")
                f.write(f"UE Range Tested: {test_points[0]['num_ues']} - {test_points[-1]['num_ues']} UEs\n\n")

                # Find maximum capacity
                max_ues_passed = max([p['num_ues'] for p in test_points if p.get('all_targets_met', False)], default=0)
                f.write(f"Maximum Capacity (All Targets Met): {max_ues_passed} UEs\n\n")

            f.write("="*80 + "\n")
            f.write("PERFORMANCE TARGETS\n")
            f.write("="*80 + "\n\n")

            f.write("Target                    | Requirement | Status\n")
            f.write("-" * 60 + "\n")
            f.write(f"100 UEs Support           | Required    | {'PASS' if max_ues_passed >= 100 else 'FAIL'}\n")
            f.write(f"200 UEs Support           | Target      | {'PASS' if max_ues_passed >= 200 else 'N/A'}\n")
            f.write(f"500 UEs Support           | Stretch     | {'PASS' if max_ues_passed >= 500 else 'N/A'}\n\n")

            f.write("="*80 + "\n")
            f.write("DETAILED RESULTS\n")
            f.write("="*80 + "\n\n")

            if test_points:
                f.write(f"{'UEs':<10} {'Latency':<12} {'Throughput':<14} {'CPU %':<10} {'Memory GB':<12} {'Status':<10}\n")
                f.write("-" * 80 + "\n")

                for point in test_points:
                    status = "PASS" if point.get('all_targets_met', False) else "FAIL"
                    f.write(f"{point['num_ues']:<10} "
                           f"{point['latency_p99_ms']:<12.2f} "
                           f"{point['throughput_msg_s']:<14.1f} "
                           f"{point['cpu_percent']:<10.1f} "
                           f"{point['memory_mb']/1024:<12.2f} "
                           f"{status:<10}\n")

            f.write("\n" + "="*80 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*80 + "\n")

        print(f"[Visualizer] Saved summary report: {output_path}")


def main():
    """Test visualizer with sample data"""
    print("Test Results Visualizer")
    print("="*80)

    visualizer = TestResultsVisualizer(output_dir="./test_results")

    # Sample stress test data
    sample_data = [
        {'num_ues': 10, 'latency_p99_ms': 8.5, 'throughput_msg_s': 95, 'cpu_percent': 15, 'memory_mb': 512, 'handover_success_rate': 99.5, 'all_targets_met': True},
        {'num_ues': 20, 'latency_p99_ms': 10.2, 'throughput_msg_s': 185, 'cpu_percent': 25, 'memory_mb': 896, 'handover_success_rate': 99.2, 'all_targets_met': True},
        {'num_ues': 50, 'latency_p99_ms': 12.8, 'throughput_msg_s': 450, 'cpu_percent': 38, 'memory_mb': 1850, 'handover_success_rate': 99.0, 'all_targets_met': True},
        {'num_ues': 100, 'latency_p99_ms': 14.5, 'throughput_msg_s': 880, 'cpu_percent': 48, 'memory_mb': 3500, 'handover_success_rate': 98.8, 'all_targets_met': True},
        {'num_ues': 200, 'latency_p99_ms': 19.2, 'throughput_msg_s': 1650, 'cpu_percent': 68, 'memory_mb': 6800, 'handover_success_rate': 98.5, 'all_targets_met': False},
        {'num_ues': 500, 'latency_p99_ms': 28.5, 'throughput_msg_s': 3800, 'cpu_percent': 85, 'memory_mb': 15000, 'handover_success_rate': 97.8, 'all_targets_met': False},
    ]

    # Create scalability plots
    visualizer.create_scalability_plots(sample_data)

    # Sample latency breakdown
    latency_breakdown = {
        'avg_sgp4_ms': 1.2,
        'avg_weather_ms': 2.5,
        'avg_e2_encoding_ms': 0.8,
        'avg_xapp_ms': 1.5,
        'avg_e2_network_ms': 0.5,
    }

    visualizer.create_latency_breakdown_plot(latency_breakdown)

    # Sample test results for comparison
    test_results = [
        {'scenario_name': '100 UEs Uniform', 'latency_p99': 14.5, 'messages_per_second': 880, 'avg_cpu_percent': 48, 'avg_memory_mb': 3500},
        {'scenario_name': '200 UEs Dense', 'latency_p99': 19.2, 'messages_per_second': 1650, 'avg_cpu_percent': 68, 'avg_memory_mb': 6800},
        {'scenario_name': '500 UEs Global', 'latency_p99': 28.5, 'messages_per_second': 3800, 'avg_cpu_percent': 85, 'avg_memory_mb': 15000},
    ]

    visualizer.create_performance_comparison_bar(test_results)

    # Generate summary report
    stress_results = {
        'duration_seconds': 3600,
        'test_points': sample_data
    }

    visualizer.generate_summary_report(stress_results)

    print("\nVisualization complete! Check ./test_results directory")


if __name__ == "__main__":
    main()
