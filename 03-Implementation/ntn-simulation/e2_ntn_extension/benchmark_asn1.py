"""
Performance Benchmarking: ASN.1 PER vs JSON Encoding

Compares:
- Encoding time
- Decoding time
- Message size
- Memory usage
- Throughput (messages/second)

Generates performance comparison charts and reports.
"""

import json
import time
import sys
import statistics
import random
from typing import Dict, Any, List, Tuple
import matplotlib.pyplot as plt
import numpy as np

from asn1_codec import E2SM_NTN_ASN1_Codec


class EncodingBenchmark:
    """Performance benchmark for encoding comparison"""

    def __init__(self, num_samples: int = 1000):
        """
        Initialize benchmark

        Args:
            num_samples: Number of test messages to generate
        """
        self.num_samples = num_samples
        self.codec = E2SM_NTN_ASN1_Codec()
        self.test_messages = []
        self.results = {
            'asn1': {
                'encode_times': [],
                'decode_times': [],
                'message_sizes': []
            },
            'json': {
                'encode_times': [],
                'decode_times': [],
                'message_sizes': []
            }
        }

    def generate_test_messages(self):
        """Generate diverse test messages with varying parameters"""
        print(f"Generating {self.num_samples} test messages...")

        for i in range(self.num_samples):
            # Vary parameters to test different scenarios
            elevation = random.uniform(10.0, 90.0)
            azimuth = random.uniform(0.0, 360.0)
            rsrp = random.uniform(-120.0, -70.0)
            sinr = random.uniform(-10.0, 30.0)
            doppler = random.uniform(-50000.0, 50000.0)

            msg = {
                'timestamp_ns': int(time.time() * 1e9) + i,
                'ue_id': f'UE-{i:05d}',
                'satellite_metrics': {
                    'satellite_id': f'SAT-LEO-{(i % 10) + 1:03d}',
                    'orbit_type': random.choice(['LEO', 'MEO', 'GEO']),
                    'beam_id': random.randint(1, 256),
                    'elevation_angle': elevation,
                    'azimuth_angle': azimuth,
                    'slant_range_km': random.uniform(600.0, 1200.0),
                    'satellite_velocity': random.uniform(6.0, 8.0),
                    'angular_velocity': random.uniform(-1.0, 1.0)
                },
                'channel_quality': {
                    'rsrp': rsrp,
                    'rsrq': random.uniform(-20.0, -5.0),
                    'sinr': sinr,
                    'bler': random.uniform(0.0001, 0.1),
                    'cqi': random.randint(0, 15)
                },
                'ntn_impairments': {
                    'doppler_shift_hz': doppler,
                    'doppler_rate_hz_s': random.uniform(-100.0, 100.0),
                    'propagation_delay_ms': random.uniform(2.0, 4.0),
                    'path_loss_db': random.uniform(150.0, 180.0),
                    'rain_attenuation_db': random.uniform(0.0, 5.0),
                    'atmospheric_loss_db': random.uniform(0.5, 2.0)
                },
                'link_budget': {
                    'tx_power_dbm': random.uniform(15.0, 23.0),
                    'rx_power_dbm': rsrp,
                    'link_margin_db': random.uniform(5.0, 20.0),
                    'snr_db': sinr,
                    'required_snr_db': random.uniform(5.0, 15.0)
                },
                'handover_prediction': {
                    'time_to_handover_sec': random.uniform(10.0, 300.0),
                    'handover_trigger_threshold': 10.0,
                    'next_satellite_id': f'SAT-LEO-{((i + 1) % 10) + 1:03d}',
                    'next_satellite_elevation': random.uniform(5.0, 15.0),
                    'handover_probability': random.uniform(0.0, 1.0)
                },
                'performance': {
                    'throughput_dl_mbps': random.uniform(20.0, 100.0),
                    'throughput_ul_mbps': random.uniform(5.0, 20.0),
                    'latency_rtt_ms': random.uniform(8.0, 20.0),
                    'packet_loss_rate': random.uniform(0.0001, 0.05)
                }
            }

            self.test_messages.append(msg)

        print(f"✓ Generated {len(self.test_messages)} test messages")

    def benchmark_asn1_encoding(self):
        """Benchmark ASN.1 PER encoding"""
        print("\nBenchmarking ASN.1 PER encoding...")

        for msg in self.test_messages:
            # Encode
            start = time.perf_counter()
            encoded, _ = self.codec.encode_indication_message(msg)
            encode_time = (time.perf_counter() - start) * 1000  # ms

            # Decode
            start = time.perf_counter()
            decoded, _ = self.codec.decode_indication_message(encoded)
            decode_time = (time.perf_counter() - start) * 1000  # ms

            # Store results
            self.results['asn1']['encode_times'].append(encode_time)
            self.results['asn1']['decode_times'].append(decode_time)
            self.results['asn1']['message_sizes'].append(len(encoded))

        print(f"✓ Completed {len(self.test_messages)} ASN.1 encode/decode operations")

    def benchmark_json_encoding(self):
        """Benchmark JSON encoding"""
        print("\nBenchmarking JSON encoding...")

        for msg in self.test_messages:
            # Encode
            start = time.perf_counter()
            encoded = json.dumps(msg).encode('utf-8')
            encode_time = (time.perf_counter() - start) * 1000  # ms

            # Decode
            start = time.perf_counter()
            decoded = json.loads(encoded.decode('utf-8'))
            decode_time = (time.perf_counter() - start) * 1000  # ms

            # Store results
            self.results['json']['encode_times'].append(encode_time)
            self.results['json']['decode_times'].append(decode_time)
            self.results['json']['message_sizes'].append(len(encoded))

        print(f"✓ Completed {len(self.test_messages)} JSON encode/decode operations")

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistical summary of benchmark results"""
        stats = {}

        for encoding_type in ['asn1', 'json']:
            stats[encoding_type] = {
                'encode': {
                    'mean': statistics.mean(self.results[encoding_type]['encode_times']),
                    'median': statistics.median(self.results[encoding_type]['encode_times']),
                    'stdev': statistics.stdev(self.results[encoding_type]['encode_times']),
                    'min': min(self.results[encoding_type]['encode_times']),
                    'max': max(self.results[encoding_type]['encode_times']),
                    'p95': np.percentile(self.results[encoding_type]['encode_times'], 95),
                    'p99': np.percentile(self.results[encoding_type]['encode_times'], 99)
                },
                'decode': {
                    'mean': statistics.mean(self.results[encoding_type]['decode_times']),
                    'median': statistics.median(self.results[encoding_type]['decode_times']),
                    'stdev': statistics.stdev(self.results[encoding_type]['decode_times']),
                    'min': min(self.results[encoding_type]['decode_times']),
                    'max': max(self.results[encoding_type]['decode_times']),
                    'p95': np.percentile(self.results[encoding_type]['decode_times'], 95),
                    'p99': np.percentile(self.results[encoding_type]['decode_times'], 99)
                },
                'size': {
                    'mean': statistics.mean(self.results[encoding_type]['message_sizes']),
                    'median': statistics.median(self.results[encoding_type]['message_sizes']),
                    'min': min(self.results[encoding_type]['message_sizes']),
                    'max': max(self.results[encoding_type]['message_sizes'])
                }
            }

        # Calculate throughput (messages/second)
        asn1_total_time = sum(self.results['asn1']['encode_times']) + sum(self.results['asn1']['decode_times'])
        json_total_time = sum(self.results['json']['encode_times']) + sum(self.results['json']['decode_times'])

        stats['throughput'] = {
            'asn1': (self.num_samples / (asn1_total_time / 1000.0)),  # messages/sec
            'json': (self.num_samples / (json_total_time / 1000.0))
        }

        return stats

    def print_results(self, stats: Dict[str, Any]):
        """Print benchmark results"""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS: ASN.1 PER vs JSON")
        print("=" * 80)

        # Encoding time comparison
        print("\n--- ENCODING TIME (ms) ---")
        print(f"{'Metric':<15} {'ASN.1 PER':<15} {'JSON':<15} {'Improvement':<15}")
        print("-" * 60)

        asn1_enc = stats['asn1']['encode']
        json_enc = stats['json']['encode']

        print(f"{'Mean':<15} {asn1_enc['mean']:<15.4f} {json_enc['mean']:<15.4f} "
              f"{((json_enc['mean'] - asn1_enc['mean']) / json_enc['mean'] * 100):>+14.1f}%")
        print(f"{'Median':<15} {asn1_enc['median']:<15.4f} {json_enc['median']:<15.4f} "
              f"{((json_enc['median'] - asn1_enc['median']) / json_enc['median'] * 100):>+14.1f}%")
        print(f"{'P95':<15} {asn1_enc['p95']:<15.4f} {json_enc['p95']:<15.4f} "
              f"{((json_enc['p95'] - asn1_enc['p95']) / json_enc['p95'] * 100):>+14.1f}%")
        print(f"{'P99':<15} {asn1_enc['p99']:<15.4f} {json_enc['p99']:<15.4f} "
              f"{((json_enc['p99'] - asn1_enc['p99']) / json_enc['p99'] * 100):>+14.1f}%")

        # Decoding time comparison
        print("\n--- DECODING TIME (ms) ---")
        print(f"{'Metric':<15} {'ASN.1 PER':<15} {'JSON':<15} {'Improvement':<15}")
        print("-" * 60)

        asn1_dec = stats['asn1']['decode']
        json_dec = stats['json']['decode']

        print(f"{'Mean':<15} {asn1_dec['mean']:<15.4f} {json_dec['mean']:<15.4f} "
              f"{((json_dec['mean'] - asn1_dec['mean']) / json_dec['mean'] * 100):>+14.1f}%")
        print(f"{'Median':<15} {asn1_dec['median']:<15.4f} {json_dec['median']:<15.4f} "
              f"{((json_dec['median'] - asn1_dec['median']) / json_dec['median'] * 100):>+14.1f}%")
        print(f"{'P95':<15} {asn1_dec['p95']:<15.4f} {json_dec['p95']:<15.4f} "
              f"{((json_dec['p95'] - asn1_dec['p95']) / json_dec['p95'] * 100):>+14.1f}%")

        # Message size comparison
        print("\n--- MESSAGE SIZE (bytes) ---")
        print(f"{'Metric':<15} {'ASN.1 PER':<15} {'JSON':<15} {'Reduction':<15}")
        print("-" * 60)

        asn1_size = stats['asn1']['size']
        json_size = stats['json']['size']

        print(f"{'Mean':<15} {asn1_size['mean']:<15.1f} {json_size['mean']:<15.1f} "
              f"{((json_size['mean'] - asn1_size['mean']) / json_size['mean'] * 100):>14.1f}%")
        print(f"{'Median':<15} {asn1_size['median']:<15.1f} {json_size['median']:<15.1f} "
              f"{((json_size['median'] - asn1_size['median']) / json_size['median'] * 100):>14.1f}%")

        # Throughput comparison
        print("\n--- THROUGHPUT (messages/second) ---")
        print(f"{'ASN.1 PER':<15} {stats['throughput']['asn1']:<15.1f}")
        print(f"{'JSON':<15} {stats['throughput']['json']:<15.1f}")
        print(f"{'Improvement':<15} "
              f"{((stats['throughput']['asn1'] - stats['throughput']['json']) / stats['throughput']['json'] * 100):>+14.1f}%")

        print("\n" + "=" * 80)

    def generate_plots(self, stats: Dict[str, Any]):
        """Generate comparison plots"""
        print("\nGenerating comparison plots...")

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('ASN.1 PER vs JSON Performance Comparison', fontsize=16, fontweight='bold')

        # Plot 1: Encoding Time Distribution
        ax1 = axes[0, 0]
        ax1.hist(self.results['asn1']['encode_times'], bins=50, alpha=0.7, label='ASN.1 PER', color='blue')
        ax1.hist(self.results['json']['encode_times'], bins=50, alpha=0.7, label='JSON', color='red')
        ax1.set_xlabel('Encoding Time (ms)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Encoding Time Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Decoding Time Distribution
        ax2 = axes[0, 1]
        ax2.hist(self.results['asn1']['decode_times'], bins=50, alpha=0.7, label='ASN.1 PER', color='blue')
        ax2.hist(self.results['json']['decode_times'], bins=50, alpha=0.7, label='JSON', color='red')
        ax2.set_xlabel('Decoding Time (ms)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Decoding Time Distribution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot 3: Message Size Distribution
        ax3 = axes[1, 0]
        ax3.hist(self.results['asn1']['message_sizes'], bins=30, alpha=0.7, label='ASN.1 PER', color='blue')
        ax3.hist(self.results['json']['message_sizes'], bins=30, alpha=0.7, label='JSON', color='red')
        ax3.set_xlabel('Message Size (bytes)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Message Size Distribution')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Plot 4: Performance Summary
        ax4 = axes[1, 1]
        metrics = ['Encode\nTime', 'Decode\nTime', 'Message\nSize']
        asn1_values = [
            stats['asn1']['encode']['mean'],
            stats['asn1']['decode']['mean'],
            stats['asn1']['size']['mean']
        ]
        json_values = [
            stats['json']['encode']['mean'],
            stats['json']['decode']['mean'],
            stats['json']['size']['mean']
        ]

        # Normalize values for comparison
        asn1_norm = [100, 100, 100]  # ASN.1 as baseline
        json_norm = [
            (json_values[0] / asn1_values[0]) * 100,
            (json_values[1] / asn1_values[1]) * 100,
            (json_values[2] / asn1_values[2]) * 100
        ]

        x = np.arange(len(metrics))
        width = 0.35

        ax4.bar(x - width/2, asn1_norm, width, label='ASN.1 PER', color='blue')
        ax4.bar(x + width/2, json_norm, width, label='JSON', color='red')
        ax4.set_ylabel('Normalized Value (ASN.1 = 100%)')
        ax4.set_title('Performance Summary (Lower is Better)')
        ax4.set_xticks(x)
        ax4.set_xticklabels(metrics)
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.axhline(y=100, color='black', linestyle='--', linewidth=0.8)

        plt.tight_layout()
        plt.savefig('asn1_vs_json_benchmark.png', dpi=150)
        print("✓ Saved plot to: asn1_vs_json_benchmark.png")

    def run(self):
        """Run complete benchmark suite"""
        print("\n" + "=" * 80)
        print("ASN.1 PER vs JSON ENCODING BENCHMARK")
        print("=" * 80)
        print(f"Test samples: {self.num_samples}")

        # Generate test data
        self.generate_test_messages()

        # Run benchmarks
        self.benchmark_asn1_encoding()
        self.benchmark_json_encoding()

        # Calculate statistics
        stats = self.calculate_statistics()

        # Print results
        self.print_results(stats)

        # Generate plots
        self.generate_plots(stats)

        # Save detailed results to file
        self.save_results_to_file(stats)

        print("\n✓ Benchmark complete!")

    def save_results_to_file(self, stats: Dict[str, Any]):
        """Save detailed results to JSON file"""
        output_file = 'benchmark_results.json'

        results_data = {
            'test_configuration': {
                'num_samples': self.num_samples,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'statistics': stats,
            'raw_data': {
                'asn1': {
                    'encode_times_ms': self.results['asn1']['encode_times'],
                    'decode_times_ms': self.results['asn1']['decode_times'],
                    'message_sizes_bytes': self.results['asn1']['message_sizes']
                },
                'json': {
                    'encode_times_ms': self.results['json']['encode_times'],
                    'decode_times_ms': self.results['json']['decode_times'],
                    'message_sizes_bytes': self.results['json']['message_sizes']
                }
            }
        }

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"✓ Saved detailed results to: {output_file}")


if __name__ == '__main__':
    # Run benchmark with 1000 samples (can be adjusted)
    num_samples = 1000 if len(sys.argv) < 2 else int(sys.argv[1])

    benchmark = EncodingBenchmark(num_samples=num_samples)
    benchmark.run()
