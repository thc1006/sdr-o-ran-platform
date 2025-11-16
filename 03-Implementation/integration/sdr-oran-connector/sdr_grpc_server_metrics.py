#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC Server with Prometheus Metrics: SDR Ground Station → O-RAN Data Plane
Implements FR-INT-001 with comprehensive monitoring

Features:
- Real-time IQ sample streaming (bidirectional)
- Prometheus metrics integration
- Performance monitoring and statistics
- Grafana-ready metrics export

Author: thc1006@ieee.org
Version: 1.1.0 (with Prometheus)
Date: 2025-11-17
"""

import grpc
from concurrent import futures
import time
import logging
import numpy as np
from typing import Iterator, Optional
from dataclasses import dataclass, field
from collections import deque
import threading
import queue

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Import generated protobuf stubs
import sdr_oran_pb2
import sdr_oran_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Prometheus Metrics Definition
# =============================================================================

# gRPC request counters
grpc_requests_total = Counter(
    'grpc_requests_total',
    'Total gRPC requests',
    ['method', 'status']
)

# gRPC request duration
grpc_request_duration = Histogram(
    'grpc_request_duration_seconds',
    'gRPC request duration in seconds',
    ['method'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Active IQ streams
active_streams_gauge = Gauge(
    'active_iq_streams',
    'Number of active IQ streams'
)

# IQ samples processed
iq_samples_total = Counter(
    'iq_samples_total',
    'Total IQ samples processed',
    ['station_id']
)

# IQ throughput
iq_throughput_mbps = Gauge(
    'iq_throughput_mbps',
    'IQ data throughput in Mbps',
    ['station_id']
)

# Packet loss rate
packet_loss_rate_gauge = Gauge(
    'packet_loss_rate',
    'Packet loss rate',
    ['station_id']
)

# Average latency
average_latency_ms_gauge = Gauge(
    'average_latency_ms',
    'Average processing latency in milliseconds',
    ['station_id']
)

# SNR metric
snr_db_gauge = Gauge(
    'snr_db',
    'Signal-to-Noise Ratio in dB',
    ['station_id']
)

# Doppler shift metric
doppler_shift_hz_gauge = Gauge(
    'doppler_shift_hz',
    'Doppler shift in Hz',
    ['station_id']
)


def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics HTTP server

    Args:
        port: Port to expose metrics endpoint (default: 8000)
    """
    start_http_server(port)
    logger.info(f"Prometheus metrics available at http://localhost:{port}/metrics")


def instrument_method(method_name: str):
    """Decorator to instrument gRPC methods with Prometheus metrics"""
    def decorator(func):
        def wrapper(self, request, context):
            start_time = time.time()
            status = 'success'
            try:
                result = func(self, request, context)
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"Error in {method_name}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                grpc_request_duration.labels(method=method_name).observe(duration)
                grpc_requests_total.labels(method=method_name, status=status).inc()
        return wrapper
    return decorator


@dataclass
class StreamStatistics:
    """Track streaming performance metrics"""
    station_id: str
    total_samples_sent: int = 0
    total_bytes_sent: int = 0
    packets_sent: int = 0
    packets_acked: int = 0
    packets_lost: int = 0
    start_time: float = field(default_factory=time.time)
    latencies_ms: deque = field(default_factory=lambda: deque(maxlen=1000))

    @property
    def uptime_seconds(self) -> int:
        return int(time.time() - self.start_time)

    @property
    def average_throughput_mbps(self) -> float:
        if self.uptime_seconds == 0:
            return 0.0
        return (self.total_bytes_sent * 8) / (self.uptime_seconds * 1e6)

    @property
    def average_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return sum(self.latencies_ms) / len(self.latencies_ms)

    @property
    def packet_loss_rate(self) -> float:
        if self.packets_sent == 0:
            return 0.0
        return self.packets_lost / self.packets_sent

    def update_prometheus_metrics(self):
        """Update Prometheus gauges with current statistics"""
        iq_throughput_mbps.labels(station_id=self.station_id).set(self.average_throughput_mbps)
        packet_loss_rate_gauge.labels(station_id=self.station_id).set(self.packet_loss_rate)
        average_latency_ms_gauge.labels(station_id=self.station_id).set(self.average_latency_ms)


class IQSampleGenerator:
    """
    Generate simulated IQ samples for testing
    SIMULATED: Replace with actual GNU Radio connection in production
    """

    def __init__(self,
                 sample_rate: float = 10e6,
                 batch_size: int = 8192,
                 carrier_freq: float = 12e9):
        self.sample_rate = sample_rate
        self.batch_size = batch_size
        self.carrier_freq = carrier_freq
        self.sequence = 0
        self.running = False

        logger.info(f"IQ Generator initialized: SR={sample_rate/1e6:.2f} MSPS, "
                   f"Batch={batch_size}")

    def generate_batch(self) -> tuple:
        """
        Generate one batch of simulated IQ samples
        Returns: (I_samples, Q_samples, metadata)
        """
        # Simulate QPSK signal + noise
        symbols = np.random.choice([1+1j, 1-1j, -1+1j, -1-1j], self.batch_size)
        signal = symbols / np.sqrt(2)

        # Add AWGN (SNR = 15 dB)
        noise_power = 10**(-15/10)
        noise = np.sqrt(noise_power/2) * (
            np.random.randn(self.batch_size) + 1j * np.random.randn(self.batch_size)
        )

        samples = signal + noise

        # Calculate SNR
        signal_power = np.mean(np.abs(signal)**2)
        noise_power_measured = np.mean(np.abs(noise)**2)
        snr_db = 10 * np.log10(signal_power / noise_power_measured)

        # Metadata
        metadata = {
            'timestamp_ns': int(time.time_ns()),
            'sequence_number': self.sequence,
            'snr_db': snr_db,
            'receive_power_dbm': -70 + 10 * np.log10(signal_power),
            'doppler_shift_hz': 5000 * np.sin(2 * np.pi * time.time() / 600)
        }

        self.sequence += 1

        return samples.real, samples.imag, metadata


class IQStreamServicer:
    """gRPC service implementation for IQ streaming with Prometheus metrics"""

    def __init__(self):
        self.active_streams = {}
        self.statistics = {}
        self.ack_queues = {}
        self.lock = threading.Lock()

        logger.info("IQStreamServicer initialized with Prometheus metrics")

    @instrument_method('StartStream')
    def StartStream(self, request, context):
        """Start IQ sample streaming"""
        station_id = request.station_id
        logger.info(f"Starting stream for station: {station_id}")

        with self.lock:
            if station_id in self.active_streams:
                return {
                    'success': False,
                    'message': f'Stream already active for {station_id}'
                }

            generator = IQSampleGenerator(
                sample_rate=request.sample_rate,
                batch_size=request.batch_size_samples,
                carrier_freq=request.center_frequency_hz
            )
            generator.running = True

            self.active_streams[station_id] = generator
            self.statistics[station_id] = StreamStatistics(station_id=station_id)
            self.ack_queues[station_id] = queue.Queue(maxsize=100)

            # Update active streams gauge
            active_streams_gauge.set(len(self.active_streams))

        logger.info(f"Stream started: {station_id}, SR={request.sample_rate/1e6:.2f} MSPS")

        return {
            'success': True,
            'message': 'Stream started successfully',
            'start_time_ns': int(time.time_ns())
        }

    @instrument_method('StopStream')
    def StopStream(self, request, context):
        """Stop IQ sample streaming"""
        station_id = request.station_id
        logger.info(f"Stopping stream for station: {station_id}")

        with self.lock:
            if station_id not in self.active_streams:
                return {
                    'success': False,
                    'message': f'No active stream for {station_id}'
                }

            generator = self.active_streams.pop(station_id)
            generator.running = False
            stats = self.statistics.pop(station_id)
            self.ack_queues.pop(station_id)

            # Update active streams gauge
            active_streams_gauge.set(len(self.active_streams))

        logger.info(f"Stream stopped: {station_id}, "
                   f"Sent {stats.packets_sent} packets, "
                   f"Throughput {stats.average_throughput_mbps:.2f} Mbps")

        return {
            'success': True,
            'message': 'Stream stopped successfully'
        }

    def StreamIQ(self, request_iterator, context):
        """Bidirectional streaming RPC with Prometheus metrics"""
        station_id = "test-station-1"
        logger.info(f"StreamIQ called for {station_id}")

        generator = self.active_streams.get(station_id)
        stats = self.statistics.get(station_id)
        ack_queue = self.ack_queues.get(station_id)

        if not generator:
            logger.error(f"No generator for {station_id}")
            return

        try:
            while generator.running and not context.is_active():
                i_samples, q_samples, metadata = generator.generate_batch()

                samples = np.empty(len(i_samples) * 2, dtype=np.float32)
                samples[0::2] = i_samples
                samples[1::2] = q_samples

                # Update statistics
                stats.total_samples_sent += len(samples) // 2
                stats.total_bytes_sent += samples.nbytes
                stats.packets_sent += 1

                # Update Prometheus metrics
                iq_samples_total.labels(station_id=station_id).inc(len(samples) // 2)
                snr_db_gauge.labels(station_id=station_id).set(metadata['snr_db'])
                doppler_shift_hz_gauge.labels(station_id=station_id).set(metadata['doppler_shift_hz'])
                stats.update_prometheus_metrics()

                time.sleep(np.random.uniform(0.001, 0.005))

                try:
                    ack = ack_queue.get_nowait()
                    stats.packets_acked += 1
                    stats.latencies_ms.append(ack.processing_latency_ms)
                except queue.Empty:
                    pass

                sleep_time = generator.batch_size / generator.sample_rate
                time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Error in StreamIQ: {e}")
            generator.running = False

    @instrument_method('GetStreamStats')
    def GetStreamStats(self, request, context):
        """Get streaming statistics"""
        station_id = request.station_id

        with self.lock:
            stats = self.statistics.get(station_id)

            if not stats:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f'No statistics for {station_id}')
                return None

        # Update Prometheus metrics before returning
        stats.update_prometheus_metrics()

        logger.debug(f"Stats request for {station_id}: "
                    f"Throughput={stats.average_throughput_mbps:.2f} Mbps")

        return {}

    @instrument_method('UpdateDoppler')
    def UpdateDoppler(self, request, context):
        """Update Doppler compensation"""
        station_id = request.station_id
        doppler_hz = request.doppler_shift_hz

        logger.info(f"Doppler update for {station_id}: {doppler_hz/1e3:.2f} kHz")

        # Update Prometheus metric
        doppler_shift_hz_gauge.labels(station_id=station_id).set(doppler_hz)

        return {
            'success': True,
            'message': f'Doppler updated to {doppler_hz:.2f} Hz'
        }


def serve(port: int = 50051, metrics_port: int = 8000, max_workers: int = 10):
    """Start gRPC server with Prometheus metrics

    Args:
        port: gRPC server port
        metrics_port: Prometheus metrics HTTP port
        max_workers: Maximum worker threads
    """

    logger.info("="*60)
    logger.info("SDR-to-O-RAN gRPC Server with Prometheus Metrics")
    logger.info(f"gRPC Port: {port}")
    logger.info(f"Metrics Port: {metrics_port}")
    logger.info(f"Max Workers: {max_workers}")
    logger.info("="*60)

    # Start Prometheus metrics server
    start_metrics_server(metrics_port)

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.so_reuseport', 1),
            ('grpc.use_local_subchannel_pool', 1)
        ]
    )

    # Add servicers (would be uncommented after protoc generation)
    # sdr_oran_pb2_grpc.add_IQStreamServiceServicer_to_server(
    #     IQStreamServicer(), server
    # )

    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"gRPC server listening on port {port}")

    server.start()
    logger.info("Server started. Press Ctrl+C to stop.")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(grace=5)
        logger.info("Server stopped")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='SDR-to-O-RAN gRPC Server with Prometheus')
    parser.add_argument('--port', type=int, default=50051, help='gRPC port')
    parser.add_argument('--metrics-port', type=int, default=8000, help='Prometheus metrics port')
    parser.add_argument('--workers', type=int, default=10, help='Max worker threads')
    args = parser.parse_args()

    serve(port=args.port, metrics_port=args.metrics_port, max_workers=args.workers)
