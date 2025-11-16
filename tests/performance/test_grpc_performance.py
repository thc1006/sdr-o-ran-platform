"""Performance benchmarks for gRPC services"""

import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
sys.path.insert(0, '/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector')

import sdr_oran_pb2
import sdr_oran_pb2_grpc


class TestGRPCPerformance:
    """gRPC performance benchmarks"""

    def test_message_serialization_performance(self):
        """Benchmark protobuf serialization"""
        iterations = 10000
        times = []

        for _ in range(iterations):
            batch = sdr_oran_pb2.IQSampleBatch(
                station_id="perf-test",
                band="Ku-band",
                timestamp_ns=int(time.time() * 1e9),
                sequence_number=1,
                center_frequency_hz=12.5e9,
                sample_rate=10e6,
                samples=[1.0, 0.5] * 512,  # 1024 samples
                snr_db=15.5
            )

            start = time.perf_counter()
            serialized = batch.SerializeToString()
            end = time.perf_counter()

            times.append((end - start) * 1000)  # Convert to ms

        avg_time = statistics.mean(times)
        p50 = statistics.median(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        min_time = min(times)
        max_time = max(times)

        print(f"\nSerialization Performance:")
        print(f"  Iterations: {iterations}")
        print(f"  Average: {avg_time:.6f} ms")
        print(f"  Median (P50): {p50:.6f} ms")
        print(f"  P95: {p95:.6f} ms")
        print(f"  Min: {min_time:.6f} ms")
        print(f"  Max: {max_time:.6f} ms")

        # Assert performance targets
        assert avg_time < 1.0, f"Serialization too slow: {avg_time:.3f} ms"

    def test_message_deserialization_performance(self):
        """Benchmark protobuf deserialization"""
        # Create and serialize once
        batch = sdr_oran_pb2.IQSampleBatch(
            station_id="perf-test",
            band="Ku-band",
            timestamp_ns=int(time.time() * 1e9),
            sequence_number=1,
            center_frequency_hz=12.5e9,
            sample_rate=10e6,
            samples=[1.0, 0.5] * 512,
            snr_db=15.5
        )
        serialized = batch.SerializeToString()

        iterations = 10000
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            restored = sdr_oran_pb2.IQSampleBatch()
            restored.ParseFromString(serialized)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = statistics.mean(times)
        p50 = statistics.median(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        min_time = min(times)
        max_time = max(times)

        print(f"\nDeserialization Performance:")
        print(f"  Iterations: {iterations}")
        print(f"  Average: {avg_time:.6f} ms")
        print(f"  Median (P50): {p50:.6f} ms")
        print(f"  P95: {p95:.6f} ms")
        print(f"  Min: {min_time:.6f} ms")
        print(f"  Max: {max_time:.6f} ms")

        assert avg_time < 1.0, f"Deserialization too slow: {avg_time:.3f} ms"

    def test_concurrent_operations(self):
        """Test concurrent message processing"""
        num_threads = 10
        operations_per_thread = 100

        def worker(thread_id):
            times = []
            for i in range(operations_per_thread):
                batch = sdr_oran_pb2.IQSampleBatch(
                    station_id=f"thread-{thread_id}",
                    band="Ku-band",
                    timestamp_ns=int(time.time() * 1e9),
                    sequence_number=i,
                    center_frequency_hz=12.5e9,
                    sample_rate=10e6,
                    samples=[1.0, 0.5] * 512,
                    snr_db=15.5
                )

                start = time.perf_counter()
                serialized = batch.SerializeToString()
                restored = sdr_oran_pb2.IQSampleBatch()
                restored.ParseFromString(serialized)
                end = time.perf_counter()

                times.append(end - start)

            return times

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            results = [f.result() for f in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time
        total_ops = num_threads * operations_per_thread
        throughput = total_ops / total_time

        print(f"\nConcurrent Performance:")
        print(f"  Threads: {num_threads}")
        print(f"  Total operations: {total_ops}")
        print(f"  Total time: {total_time:.2f} s")
        print(f"  Throughput: {throughput:.0f} ops/sec")

        # Target: > 1000 ops/sec
        assert throughput > 1000, f"Throughput too low: {throughput:.0f} ops/sec"
