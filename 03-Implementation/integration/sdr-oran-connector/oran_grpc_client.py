#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC Client: O-RAN DU ← SDR Ground Station
Receives IQ samples from SDR and processes for O-RAN baseband

Features:
- Subscribe to real-time IQ streams
- Monitor spectrum
- Send acknowledgments and control commands
- Performance metrics collection

Author: thc1006@ieee.org
Version: 1.0.0
Date: 2025-10-27

🟡 SIMULATED: Integrate with actual O-RAN DU PHY layer
"""

import grpc
import time
import logging
import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass
from collections import deque
import threading

# 🟡 Import generated protobuf stubs (run protoc first)
# import sdr_oran_pb2
# import sdr_oran_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ClientStatistics:
    """Track client-side performance metrics"""
    packets_received: int = 0
    packets_lost: int = 0
    total_samples_received: int = 0
    total_bytes_received: int = 0
    start_time: float = 0.0
    latencies_ms: deque = None

    def __post_init__(self):
        if self.latencies_ms is None:
            self.latencies_ms = deque(maxlen=1000)
        if self.start_time == 0.0:
            self.start_time = time.time()

    @property
    def average_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return sum(self.latencies_ms) / len(self.latencies_ms)

    @property
    def throughput_mbps(self) -> float:
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        return (self.total_bytes_received * 8) / (elapsed * 1e6)

    @property
    def packet_loss_rate(self) -> float:
        total = self.packets_received + self.packets_lost
        if total == 0:
            return 0.0
        return self.packets_lost / total


class IQProcessor:
    """
    Process received IQ samples for O-RAN baseband
    🟡 SIMULATED: Replace with actual O-RAN DU PHY processing
    """

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.last_sequence = -1
        logger.info("IQProcessor initialized")

    def process_batch(self, batch):
        """
        Process IQ sample batch

        In production, this would:
        1. De-interleave I/Q samples
        2. Apply channel compensation
        3. Forward to O-RAN DU PHY (FAPI interface)
        4. Perform OFDM demodulation
        5. Extract resource blocks
        """
        start_time = time.time()

        # 🟡 Extract samples from protobuf message
        # samples = np.array(batch.samples, dtype=np.float32)
        # i_samples = samples[0::2]
        # q_samples = samples[1::2]
        # complex_samples = i_samples + 1j * q_samples

        # Detect packet loss
        if self.last_sequence >= 0:
            expected_seq = self.last_sequence + 1
            # if batch.sequence_number != expected_seq:
            #     lost = batch.sequence_number - expected_seq
            #     logger.warning(f"Packet loss detected: {lost} packets")
            #     return lost, None

        # self.last_sequence = batch.sequence_number

        # Simulate processing
        processing_time_ms = (time.time() - start_time) * 1000

        # Callback for custom processing
        if self.callback:
            # self.callback(complex_samples, batch)
            pass

        # logger.debug(f"Processed batch {batch.sequence_number}: "
        #             f"{len(complex_samples)} samples, "
        #             f"SNR={batch.snr_db:.2f} dB, "
        #             f"Processing time={processing_time_ms:.2f} ms")

        processing_time_ms = 2.5  # Simulated
        return 0, processing_time_ms


class ORANIQClient:
    """
    O-RAN gRPC client for receiving IQ samples from SDR
    """

    def __init__(self,
                 server_address: str = "localhost:50051",
                 station_id: str = "ground-station-1",
                 secure: bool = False):

        self.server_address = server_address
        self.station_id = station_id
        self.secure = secure

        # Create channel
        if secure:
            # 🟡 TODO: Load TLS credentials
            # credentials = grpc.ssl_channel_credentials()
            # self.channel = grpc.secure_channel(server_address, credentials)
            logger.warning("🟡 Secure mode not implemented, using insecure channel")
            self.channel = grpc.insecure_channel(server_address)
        else:
            self.channel = grpc.insecure_channel(
                server_address,
                options=[
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100 MB
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),
                    ('grpc.keepalive_time_ms', 10000),
                    ('grpc.keepalive_timeout_ms', 5000)
                ]
            )

        # Create stubs
        # 🟡 Uncomment after protoc generation
        # self.iq_stub = sdr_oran_pb2_grpc.IQStreamServiceStub(self.channel)
        # self.spectrum_stub = sdr_oran_pb2_grpc.SpectrumMonitorServiceStub(self.channel)

        self.processor = IQProcessor()
        self.stats = ClientStatistics()
        self.running = False

        logger.info(f"O-RAN IQ Client initialized: {server_address}")

    def start_stream(self,
                     band: str = "Ku-band",
                     center_freq_hz: float = 12e9,
                     sample_rate: float = 10e6,
                     batch_size: int = 8192,
                     enable_compression: bool = False):
        """Start receiving IQ stream"""

        logger.info(f"Starting IQ stream from {self.station_id}")
        logger.info(f"Band: {band}, Fc={center_freq_hz/1e9:.2f} GHz, "
                   f"SR={sample_rate/1e6:.2f} MSPS")

        # 🟡 Uncomment after protoc generation
        # config = sdr_oran_pb2.StreamConfig(
        #     station_id=self.station_id,
        #     band=band,
        #     center_frequency_hz=center_freq_hz,
        #     sample_rate=sample_rate,
        #     batch_size_samples=batch_size,
        #     enable_compression=enable_compression,
        #     compression=sdr_oran_pb2.CompressionType.NONE
        # )

        try:
            # Start stream on server
            # response = self.iq_stub.StartStream(config)
            # logger.info(f"Stream start response: {response.message}")

            # Start receiving thread
            self.running = True
            self.stats = ClientStatistics()

            receive_thread = threading.Thread(
                target=self._receive_loop,
                daemon=True
            )
            receive_thread.start()

            logger.info("IQ stream started successfully")

        except grpc.RpcError as e:
            logger.error(f"Failed to start stream: {e}")
            raise

    def _receive_loop(self):
        """Receive and process IQ batches (runs in separate thread)"""

        logger.info("Starting receive loop...")

        try:
            # 🟡 Uncomment after protoc generation
            # Create bidirectional stream
            # def ack_generator():
            #     while self.running:
            #         # Generate acknowledgments
            #         ack = sdr_oran_pb2.IQAck(
            #             acked_sequence=self.processor.last_sequence,
            #             packets_received=self.stats.packets_received,
            #             packets_lost=self.stats.packets_lost,
            #             processing_latency_ms=self.stats.average_latency_ms
            #         )
            #         yield ack
            #         time.sleep(0.1)  # Send acks every 100ms

            # stream = self.iq_stub.StreamIQ(ack_generator())

            # for batch in stream:
            #     if not self.running:
            #         break

            #     # Process batch
            #     lost, latency_ms = self.processor.process_batch(batch)

            #     # Update statistics
            #     self.stats.packets_received += 1
            #     self.stats.packets_lost += lost
            #     self.stats.total_samples_received += len(batch.samples) // 2
            #     self.stats.total_bytes_received += len(batch.samples) * 4  # float32
            #     self.stats.latencies_ms.append(latency_ms)

            #     # Log every 100 packets
            #     if self.stats.packets_received % 100 == 0:
            #         logger.info(
            #             f"Received {self.stats.packets_received} packets, "
            #             f"Throughput: {self.stats.throughput_mbps:.2f} Mbps, "
            #             f"Latency: {self.stats.average_latency_ms:.2f} ms, "
            #             f"Loss: {self.stats.packet_loss_rate*100:.3f}%"
            #         )

            # 🟡 Simulation: Just sleep
            logger.info("🟡 SIMULATION: Receive loop would run here")
            while self.running:
                time.sleep(1)

        except grpc.RpcError as e:
            logger.error(f"Stream error: {e}")
            self.running = False

    def stop_stream(self):
        """Stop IQ stream"""
        logger.info("Stopping IQ stream...")

        self.running = False

        # 🟡 Uncomment after protoc generation
        # request = sdr_oran_pb2.StreamStopRequest(station_id=self.station_id)
        # response = self.iq_stub.StopStream(request)
        # logger.info(f"Stop response: {response.message}")

        logger.info("IQ stream stopped")

    def get_statistics(self):
        """Get streaming statistics from server"""

        # 🟡 Uncomment after protoc generation
        # request = sdr_oran_pb2.StreamStatsRequest(station_id=self.station_id)
        # stats = self.iq_stub.GetStreamStats(request)

        # logger.info(f"Server stats: Throughput={stats.average_throughput_mbps:.2f} Mbps, "
        #            f"Packets sent={stats.packets_sent}, "
        #            f"Packet loss={stats.packet_loss_rate*100:.3f}%")

        # return stats

        logger.info("🟡 SIMULATION: Statistics would be retrieved here")
        return None

    def update_doppler(self, doppler_hz: float, doppler_rate_hz_s: float = 0.0):
        """Send Doppler update to SDR"""

        logger.info(f"Sending Doppler update: {doppler_hz/1e3:.2f} kHz")

        # 🟡 Uncomment after protoc generation
        # request = sdr_oran_pb2.DopplerUpdate(
        #     station_id=self.station_id,
        #     doppler_shift_hz=doppler_hz,
        #     doppler_rate_hz_s=doppler_rate_hz_s,
        #     timestamp_ns=int(time.time_ns())
        # )
        # response = self.iq_stub.UpdateDoppler(request)
        # logger.info(f"Doppler update response: {response.message}")

    def get_spectrum(self,
                     center_freq_hz: float = 12e9,
                     span_hz: float = 100e6,
                     fft_size: int = 2048):
        """Request spectrum snapshot"""

        logger.info(f"Requesting spectrum: Fc={center_freq_hz/1e9:.2f} GHz, "
                   f"Span={span_hz/1e6:.2f} MHz")

        # 🟡 Uncomment after protoc generation
        # request = sdr_oran_pb2.SpectrumRequest(
        #     station_id=self.station_id,
        #     center_frequency_hz=center_freq_hz,
        #     span_hz=span_hz,
        #     fft_size=fft_size,
        #     averaging=10
        # )

        # spectrum = self.spectrum_stub.GetSpectrum(request)

        # logger.info(f"Spectrum received: Peak at {spectrum.peak_frequency_hz/1e9:.4f} GHz, "
        #            f"Power: {spectrum.peak_power_dbm:.2f} dBm")

        # return spectrum

        logger.info("🟡 SIMULATION: Spectrum would be retrieved here")
        return None

    def close(self):
        """Close gRPC channel"""
        self.running = False
        self.channel.close()
        logger.info("Client closed")


def main():
    """Example usage"""

    logger.info("="*60)
    logger.info("O-RAN IQ Client - SDR Ground Station Connector")
    logger.info("="*60)

    # Configuration
    SERVER_ADDRESS = "localhost:50051"
    STATION_ID = "ground-station-1"
    BAND = "Ku-band"

    # Create client
    client = ORANIQClient(
        server_address=SERVER_ADDRESS,
        station_id=STATION_ID,
        secure=False
    )

    try:
        # Start IQ stream
        client.start_stream(
            band=BAND,
            center_freq_hz=12e9,
            sample_rate=10e6,
            batch_size=8192
        )

        # Run for 60 seconds
        for t in range(60):
            time.sleep(1)

            # Simulate Doppler updates every 10 seconds
            if t % 10 == 0 and t > 0:
                doppler_hz = 40e3 * np.sin(2 * np.pi * t / 600)
                client.update_doppler(doppler_hz)

            # Get statistics every 30 seconds
            if t % 30 == 0 and t > 0:
                client.get_statistics()

        # Get final spectrum
        client.get_spectrum(
            center_freq_hz=12e9,
            span_hz=100e6,
            fft_size=2048
        )

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    finally:
        client.stop_stream()
        client.close()

    logger.info("Client terminated")


if __name__ == '__main__':
    main()


# =============================================================================
# O-RAN Integration Notes:
# =============================================================================
"""
1. FAPI (Functional API) Integration:
   - Convert IQ samples to FAPI messages
   - Interface: O-RAN.WG8.FAPI specification
   - Example: fapi_rx_data_indication()

2. Split Architecture Options:
   - Split 7.2x: IQ samples at antenna
   - Split 8: Frequency domain (after FFT)
   - This implementation uses Split 7.2x

3. Performance Requirements:
   - Processing latency: <5ms per batch
   - Total E2E latency: <100ms (including propagation)
   - Jitter: <1ms

4. Resource Block Mapping:
   - Map IQ samples to 5G NR resource grid
   - Support for NTN-specific timing advance
   - Implement TA adjustments for satellite delay

5. Synchronization:
   - GPS/GNSS time sync at ground station
   - Propagate timestamps to O-RAN DU
   - Compensate for satellite doppler in timing

6. Deployment:
   - Deploy as Kubernetes pod in O-RAN namespace
   - Service mesh (Istio) for secure communication
   - Prometheus metrics exporter

Reference:
- FR-INT-001: gRPC data plane integration
- FR-ORAN-002: FAPI message conversion
- NFR-PERF-001: E2E latency <100ms
"""
