#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC Server: SDR Ground Station → O-RAN Data Plane
Implements FR-INT-001: High-performance IQ sample streaming

Features:
- Real-time IQ sample streaming (bidirectional)
- Spectrum monitoring service
- Antenna control interface
- Performance monitoring and statistics

Author: thc1006@ieee.org
Version: 1.0.0
Date: 2025-10-27

🟡 SIMULATED: Generate protobuf stubs before production use:
   python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/sdr_oran.proto
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

# ✅ Import generated protobuf stubs (2025-11-17: stubs verified to exist)
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

grpc_requests_total = Counter(
    'grpc_requests_total',
    'Total gRPC requests',
    ['method', 'status']
)

grpc_request_duration = Histogram(
    'grpc_request_duration_seconds',
    'gRPC request duration in seconds',
    ['method'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

active_streams_gauge = Gauge(
    'active_iq_streams',
    'Number of active IQ streams'
)

iq_samples_total = Counter(
    'iq_samples_total',
    'Total IQ samples processed',
    ['station_id']
)

iq_throughput_mbps = Gauge(
    'iq_throughput_mbps',
    'IQ data throughput in Mbps',
    ['station_id']
)

packet_loss_rate_gauge = Gauge(
    'packet_loss_rate',
    'Packet loss rate',
    ['station_id']
)

average_latency_ms_gauge = Gauge(
    'average_latency_ms',
    'Average processing latency in milliseconds',
    ['station_id']
)


def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics HTTP server"""
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


class IQSampleGenerator:
    """
    Generate simulated IQ samples for testing
    🟡 SIMULATED: Replace with actual GNU Radio connection in production
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
        # Signal: QPSK modulated carrier
        symbols = np.random.choice([1+1j, 1-1j, -1+1j, -1-1j], self.batch_size)
        signal = symbols / np.sqrt(2)  # Normalize

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
            'receive_power_dbm': -70 + 10 * np.log10(signal_power),  # Simulated
            'doppler_shift_hz': 5000 * np.sin(2 * np.pi * time.time() / 600)  # Simulated LEO
        }

        self.sequence += 1

        return samples.real, samples.imag, metadata


class IQStreamServicer:  # (sdr_oran_pb2_grpc.IQStreamServiceServicer):
    """
    gRPC service implementation for IQ streaming

    🟡 SIMULATED: Uncomment inheritance after protoc generation
    """

    def __init__(self):
        self.active_streams = {}  # station_id -> IQSampleGenerator
        self.statistics = {}      # station_id -> StreamStatistics
        self.ack_queues = {}      # station_id -> queue.Queue
        self.lock = threading.Lock()

        logger.info("IQStreamServicer initialized")

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

            # Create IQ generator
            generator = IQSampleGenerator(
                sample_rate=request.sample_rate,
                batch_size=request.batch_size_samples,
                carrier_freq=request.center_frequency_hz
            )
            generator.running = True

            self.active_streams[station_id] = generator
            self.statistics[station_id] = StreamStatistics(station_id=station_id)
            self.ack_queues[station_id] = queue.Queue(maxsize=100)

            # Update Prometheus active streams gauge
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

            # Update Prometheus active streams gauge
            active_streams_gauge.set(len(self.active_streams))

        logger.info(f"Stream stopped: {station_id}, "
                   f"Sent {stats.packets_sent} packets, "
                   f"Throughput {stats.average_throughput_mbps:.2f} Mbps")

        return {
            'success': True,
            'message': 'Stream stopped successfully'
        }

    def StreamIQ(self, request_iterator, context):
        """
        Bidirectional streaming RPC
        Client → Server: IQ sample batches
        Server → Client: Acknowledgments

        🟡 SIMULATED: For testing, this generates samples server-side
        In production, samples come from GNU Radio via request_iterator
        """
        # Extract station_id from first request
        # For simulation, we'll use a test station
        station_id = "test-station-1"

        logger.info(f"StreamIQ called for {station_id}")

        # Ensure stream is started
        if station_id not in self.active_streams:
            logger.warning(f"Stream not started for {station_id}, starting now")
            # Auto-start with defaults
            # self.StartStream(default_config, context)

        generator = self.active_streams.get(station_id)
        stats = self.statistics.get(station_id)
        ack_queue = self.ack_queues.get(station_id)

        if not generator:
            logger.error(f"No generator for {station_id}")
            return

        # Start sending IQ samples
        try:
            while generator.running and not context.is_active():
                # Generate IQ batch
                i_samples, q_samples, metadata = generator.generate_batch()

                # Interleave I/Q samples
                samples = np.empty(len(i_samples) * 2, dtype=np.float32)
                samples[0::2] = i_samples
                samples[1::2] = q_samples

                # Create IQ batch message
                # 🟡 Uncomment after protoc generation
                # batch = sdr_oran_pb2.IQSampleBatch(
                #     station_id=station_id,
                #     band="Ku-band",
                #     timestamp_ns=metadata['timestamp_ns'],
                #     sequence_number=metadata['sequence_number'],
                #     center_frequency_hz=generator.carrier_freq,
                #     sample_rate=generator.sample_rate,
                #     samples=samples.tolist(),
                #     snr_db=metadata['snr_db'],
                #     receive_power_dbm=metadata['receive_power_dbm'],
                #     doppler_shift_hz=metadata['doppler_shift_hz'],
                #     agc_locked=True
                # )

                # Update statistics
                stats.total_samples_sent += len(samples) // 2
                stats.total_bytes_sent += samples.nbytes
                stats.packets_sent += 1

                # Simulate network latency (1-5ms)
                time.sleep(np.random.uniform(0.001, 0.005))

                # Yield batch
                # 🟡 Uncomment after protoc generation
                # yield batch

                # Check for acknowledgments (non-blocking)
                try:
                    ack = ack_queue.get_nowait()
                    stats.packets_acked += 1
                    stats.latencies_ms.append(ack.processing_latency_ms)
                except queue.Empty:
                    pass

                # Throttle to match sample rate
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

        # Update Prometheus metrics
        iq_throughput_mbps.labels(station_id=station_id).set(stats.average_throughput_mbps)
        packet_loss_rate_gauge.labels(station_id=station_id).set(stats.packet_loss_rate)
        average_latency_ms_gauge.labels(station_id=station_id).set(stats.average_latency_ms)

        logger.debug(f"Stats request for {station_id}: "
                    f"Throughput={stats.average_throughput_mbps:.2f} Mbps")

        # 🟡 Uncomment after protoc generation
        # return sdr_oran_pb2.StreamStatsResponse(
        #     station_id=station_id,
        #     total_samples_sent=stats.total_samples_sent,
        #     total_bytes_sent=stats.total_bytes_sent,
        #     average_throughput_mbps=stats.average_throughput_mbps,
        #     average_latency_ms=stats.average_latency_ms,
        #     packets_sent=stats.packets_sent,
        #     packets_acked=stats.packets_acked,
        #     packets_lost=stats.packets_lost,
        #     packet_loss_rate=stats.packet_loss_rate,
        #     uptime_seconds=stats.uptime_seconds
        # )

        return {}  # Placeholder

    def UpdateDoppler(self, request, context):
        """Update Doppler compensation"""
        station_id = request.station_id
        doppler_hz = request.doppler_shift_hz

        logger.info(f"Doppler update for {station_id}: {doppler_hz/1e3:.2f} kHz")

        # 🟡 TODO: Forward to GNU Radio flowgraph
        # receiver.update_doppler(doppler_hz)

        return {
            'success': True,
            'message': f'Doppler updated to {doppler_hz:.2f} Hz'
        }


class SpectrumMonitorServicer:  # (sdr_oran_pb2_grpc.SpectrumMonitorServiceServicer):
    """gRPC service for spectrum monitoring"""

    def GetSpectrum(self, request, context):
        """Get single spectrum snapshot"""
        station_id = request.station_id
        fft_size = request.fft_size

        logger.debug(f"Spectrum request: {station_id}, FFT={fft_size}")

        # 🟡 SIMULATED: Generate fake spectrum
        frequencies = np.linspace(
            request.center_frequency_hz - request.span_hz/2,
            request.center_frequency_hz + request.span_hz/2,
            fft_size
        )

        # Simulate spectrum with signal + noise
        noise_floor = -100  # dBm
        spectrum = noise_floor + 10 * np.random.randn(fft_size)

        # Add signal peak at center
        peak_idx = fft_size // 2
        spectrum[peak_idx-10:peak_idx+10] += 40  # 40 dB above noise

        return sdr_oran_pb2.SpectrumData(
            station_id=station_id,
            timestamp_ns=int(time.time_ns()),
            center_frequency_hz=request.center_frequency_hz,
            span_hz=request.span_hz,
            fft_size=fft_size,
            magnitude_dbm=spectrum.tolist(),
            frequencies_hz=frequencies.tolist(),
            peak_frequency_hz=frequencies[peak_idx],
            peak_power_dbm=float(spectrum[peak_idx])
        )

    def StreamSpectrum(self, request, context):
        """Stream spectrum updates continuously"""
        logger.info(f"Starting spectrum stream for {request.station_id}")

        try:
            while context.is_active():
                # Generate spectrum data (same as GetSpectrum)
                fft_size = request.fft_size
                frequencies = np.linspace(
                    request.center_frequency_hz - request.span_hz/2,
                    request.center_frequency_hz + request.span_hz/2,
                    fft_size
                )

                noise_floor = -100  # dBm
                spectrum = noise_floor + 10 * np.random.randn(fft_size)

                # Add signal peak at center
                peak_idx = fft_size // 2
                spectrum[peak_idx-10:peak_idx+10] += 40  # 40 dB above noise

                spectrum_data = sdr_oran_pb2.SpectrumData(
                    station_id=request.station_id,
                    timestamp_ns=int(time.time_ns()),
                    center_frequency_hz=request.center_frequency_hz,
                    span_hz=request.span_hz,
                    fft_size=fft_size,
                    magnitude_dbm=spectrum.tolist(),
                    frequencies_hz=frequencies.tolist(),
                    peak_frequency_hz=frequencies[peak_idx],
                    peak_power_dbm=float(spectrum[peak_idx])
                )

                yield spectrum_data

                # Update rate: ~10 Hz
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in StreamSpectrum: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))


def create_server_credentials(cert_dir: str = "./certs", require_client_auth: bool = True):
    """Create gRPC server credentials with TLS/mTLS encryption.

    Args:
        cert_dir: Directory containing SSL certificates
        require_client_auth: Whether to require client certificate (mTLS)

    Returns:
        grpc.ServerCredentials object
    """
    import os

    # Read certificate files
    with open(f'{cert_dir}/server.key', 'rb') as f:
        server_key = f.read()
    with open(f'{cert_dir}/server.crt', 'rb') as f:
        server_cert = f.read()
    with open(f'{cert_dir}/ca.crt', 'rb') as f:
        ca_cert = f.read()

    # Create server credentials with optional mTLS
    server_credentials = grpc.ssl_server_credentials(
        [(server_key, server_cert)],
        root_certificates=ca_cert,
        require_client_auth=require_client_auth  # Enable mTLS
    )

    return server_credentials


def serve(port: int = 50051, metrics_port: int = 8000, max_workers: int = 10, use_tls: bool = True, use_mtls: bool = False, cert_dir: str = "./certs"):
    """Start gRPC server with optional TLS/mTLS encryption and Prometheus metrics.

    Args:
        port: Port to bind the server
        metrics_port: Port for Prometheus metrics endpoint
        max_workers: Maximum number of worker threads
        use_tls: Whether to enable TLS encryption
        use_mtls: Whether to enable mTLS (mutual authentication)
        cert_dir: Directory containing SSL certificates
    """

    logger.info("="*60)
    logger.info("SDR-to-O-RAN gRPC Server with Prometheus Metrics")
    logger.info(f"gRPC Port: {port}")
    logger.info(f"Metrics Port: {metrics_port}")
    logger.info(f"Max Workers: {max_workers}")
    if use_mtls:
        logger.info(f"Security: mTLS (Mutual Authentication)")
    elif use_tls:
        logger.info(f"Security: TLS (Server Authentication)")
    else:
        logger.info(f"Security: INSECURE (No Encryption)")
    logger.info("="*60)

    # Start Prometheus metrics server
    start_metrics_server(metrics_port)

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100 MB
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.so_reuseport', 1),
            ('grpc.use_local_subchannel_pool', 1)
        ]
    )

    # Add servicers
    sdr_oran_pb2_grpc.add_IQStreamServiceServicer_to_server(
        IQStreamServicer(), server
    )
    sdr_oran_pb2_grpc.add_SpectrumMonitorServiceServicer_to_server(
        SpectrumMonitorServicer(), server
    )

    # Bind with mTLS, TLS, or insecure
    if use_mtls:
        server_credentials = create_server_credentials(cert_dir, require_client_auth=True)
        server.add_secure_port(f'[::]:{port}', server_credentials)
        logger.info(f"Secure gRPC server listening on port {port} (mTLS enabled - mutual authentication)")
    elif use_tls:
        server_credentials = create_server_credentials(cert_dir, require_client_auth=False)
        server.add_secure_port(f'[::]:{port}', server_credentials)
        logger.info(f"Secure gRPC server listening on port {port} (TLS enabled)")
    else:
        server.add_insecure_port(f'[::]:{port}')
        logger.warning(f"Insecure gRPC server listening on port {port} (TLS disabled)")

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
    parser = argparse.ArgumentParser(description='SDR-to-O-RAN gRPC Server')
    parser.add_argument('--port', type=int, default=50051, help='Server port (default: 50051)')
    parser.add_argument('--workers', type=int, default=10, help='Max worker threads (default: 10)')
    parser.add_argument('--tls', action='store_true', default=True, help='Enable TLS encryption')
    parser.add_argument('--mtls', action='store_true', help='Enable mTLS (mutual authentication)')
    parser.add_argument('--cert-dir', type=str, default='./certs', help='Certificate directory (default: ./certs)')
    args = parser.parse_args()

    serve(port=args.port, max_workers=args.workers, use_tls=args.tls, use_mtls=args.mtls, cert_dir=args.cert_dir)


# =============================================================================
# Production Deployment Steps:
# =============================================================================
"""
1. Generate protobuf stubs:
   cd 03-Implementation/integration/sdr-oran-connector
   python -m grpc_tools.protoc \
       -I./proto \
       --python_out=. \
       --grpc_python_out=. \
       proto/sdr_oran.proto

2. Install dependencies:
   pip install grpcio grpcio-tools protobuf numpy

3. Integrate with GNU Radio:
   - Connect to dvbs2_multiband_receiver.py
   - Stream real IQ samples instead of simulated data

4. Performance tuning:
   - Adjust batch_size for optimal throughput vs. latency
   - Consider gRPC compression for bandwidth-limited links
   - Use RDMA transport for ultra-low latency (requires hardware support)

5. Security (NFR-SEC-001):
   - Enable TLS: server_credentials = grpc.ssl_server_credentials(...)
   - Implement authentication: metadata interceptor
   - Network policy: Restrict to O-RAN namespace

6. Monitoring (NFR-INT-003):
   - Export Prometheus metrics
   - Log to centralized logging (ELK stack)
   - Alerting on packet loss >0.1%

Reference:
- FR-INT-001: gRPC data plane integration
- NFR-PERF-001: E2E latency <100ms
- NFR-SEC-001: Secure communication
"""
