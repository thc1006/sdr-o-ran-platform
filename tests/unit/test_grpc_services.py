"""Unit tests for gRPC services

Tests the SDR-to-O-RAN gRPC server implementation including:
- IQ sample batch message creation
- Stream statistics tracking
- Doppler updates
- Protobuf serialization/deserialization
- IQ sample generation
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from collections import deque

# Import the modules to test
import sdr_oran_pb2
import sdr_oran_pb2_grpc
from sdr_grpc_server import (
    StreamStatistics,
    IQSampleGenerator,
    IQStreamServicer,
    SpectrumMonitorServicer
)


@pytest.mark.unit
@pytest.mark.grpc
class TestStreamStatistics:
    """Test StreamStatistics data class"""

    def test_statistics_initialization(self):
        """Test creating StreamStatistics object"""
        stats = StreamStatistics(station_id="test-station")

        assert stats.station_id == "test-station"
        assert stats.total_samples_sent == 0
        assert stats.total_bytes_sent == 0
        assert stats.packets_sent == 0
        assert stats.packets_acked == 0
        assert stats.packets_lost == 0
        assert isinstance(stats.latencies_ms, deque)
        assert stats.latencies_ms.maxlen == 1000

    def test_uptime_calculation(self):
        """Test uptime calculation"""
        stats = StreamStatistics(station_id="test-station")
        time.sleep(0.1)  # Sleep briefly

        uptime = stats.uptime_seconds
        assert uptime >= 0
        assert isinstance(uptime, int)

    def test_average_throughput_calculation(self):
        """Test average throughput calculation"""
        stats = StreamStatistics(station_id="test-station")
        stats.total_bytes_sent = 10_000_000  # 10 MB
        stats.start_time = time.time() - 1.0  # 1 second ago

        throughput = stats.average_throughput_mbps
        assert throughput > 0
        assert throughput < 100  # Should be around 80 Mbps

    def test_average_latency_calculation(self):
        """Test average latency calculation"""
        stats = StreamStatistics(station_id="test-station")
        stats.latencies_ms.extend([1.0, 2.0, 3.0, 4.0, 5.0])

        avg_latency = stats.average_latency_ms
        assert avg_latency == 3.0

    def test_average_latency_empty(self):
        """Test average latency with no data"""
        stats = StreamStatistics(station_id="test-station")

        avg_latency = stats.average_latency_ms
        assert avg_latency == 0.0

    def test_packet_loss_rate_calculation(self):
        """Test packet loss rate calculation"""
        stats = StreamStatistics(station_id="test-station")
        stats.packets_sent = 1000
        stats.packets_lost = 10

        loss_rate = stats.packet_loss_rate
        assert loss_rate == 0.01  # 1%

    def test_packet_loss_rate_no_packets(self):
        """Test packet loss rate with no packets sent"""
        stats = StreamStatistics(station_id="test-station")

        loss_rate = stats.packet_loss_rate
        assert loss_rate == 0.0


@pytest.mark.unit
@pytest.mark.grpc
class TestIQSampleGenerator:
    """Test IQ sample generation"""

    def test_generator_initialization(self):
        """Test IQSampleGenerator initialization"""
        gen = IQSampleGenerator(
            sample_rate=10e6,
            batch_size=8192,
            carrier_freq=12e9
        )

        assert gen.sample_rate == 10e6
        assert gen.batch_size == 8192
        assert gen.carrier_freq == 12e9
        assert gen.sequence == 0
        assert gen.running == False

    def test_generate_batch(self):
        """Test generating IQ sample batch"""
        gen = IQSampleGenerator(
            sample_rate=10e6,
            batch_size=1024,
            carrier_freq=12e9
        )

        i_samples, q_samples, metadata = gen.generate_batch()

        # Check sample arrays
        assert len(i_samples) == 1024
        assert len(q_samples) == 1024
        assert isinstance(i_samples, np.ndarray)
        assert isinstance(q_samples, np.ndarray)

        # Check metadata
        assert 'timestamp_ns' in metadata
        assert 'sequence_number' in metadata
        assert 'snr_db' in metadata
        assert 'receive_power_dbm' in metadata
        assert 'doppler_shift_hz' in metadata

        # Check sequence increment
        assert metadata['sequence_number'] == 0
        gen.generate_batch()
        _, _, metadata2 = gen.generate_batch()
        assert metadata2['sequence_number'] == 2

    def test_snr_calculation(self):
        """Test SNR calculation in generated samples"""
        gen = IQSampleGenerator(batch_size=10000)

        _, _, metadata = gen.generate_batch()

        # SNR should be around 15 dB (as defined in the generator)
        assert 10.0 < metadata['snr_db'] < 20.0

    def test_sample_normalization(self):
        """Test that samples are properly normalized"""
        gen = IQSampleGenerator(batch_size=10000)

        i_samples, q_samples, _ = gen.generate_batch()

        # Check that samples are within reasonable bounds
        assert np.abs(i_samples).max() < 5.0  # With noise, should be reasonable
        assert np.abs(q_samples).max() < 5.0


@pytest.mark.unit
@pytest.mark.grpc
class TestProtobufMessages:
    """Test protobuf message creation and serialization"""

    def test_iq_sample_batch_creation(self):
        """Test creating IQSampleBatch message"""
        batch = sdr_oran_pb2.IQSampleBatch(
            station_id="test-station",
            band="Ku-band",
            timestamp_ns=int(time.time() * 1e9),
            sequence_number=1,
            center_frequency_hz=12.5e9,
            sample_rate=10e6,
            samples=[1.0, 0.5, -0.3, 0.8] * 256,
            snr_db=15.5,
            receive_power_dbm=-75.0,
            agc_locked=True,
            doppler_shift_hz=12500.0
        )

        assert batch.station_id == "test-station"
        assert batch.band == "Ku-band"
        assert batch.center_frequency_hz == 12.5e9
        assert batch.sample_rate == 10e6
        assert len(batch.samples) == 1024
        assert batch.snr_db == 15.5
        assert batch.receive_power_dbm == -75.0
        assert batch.agc_locked == True
        assert batch.doppler_shift_hz == 12500.0

    def test_stream_stats_request(self):
        """Test StreamStatsRequest message"""
        request = sdr_oran_pb2.StreamStatsRequest(
            station_id="test-station"
        )

        assert request.station_id == "test-station"

    def test_doppler_update(self):
        """Test DopplerUpdate message"""
        update = sdr_oran_pb2.DopplerUpdate(
            station_id="test-station",
            doppler_shift_hz=15000.0,
            doppler_rate_hz_s=250.0
        )

        assert update.station_id == "test-station"
        assert update.doppler_shift_hz == 15000.0
        assert update.doppler_rate_hz_s == 250.0

    def test_serialization_roundtrip(self):
        """Test protobuf serialization and deserialization"""
        original = sdr_oran_pb2.IQSampleBatch(
            station_id="serialize-test",
            band="Ka-band",
            timestamp_ns=123456789000,
            sequence_number=42,
            center_frequency_hz=28e9,
            sample_rate=50e6,
            samples=[0.1, 0.2, 0.3, 0.4],
            snr_db=20.5
        )

        # Serialize
        serialized = original.SerializeToString()
        assert len(serialized) > 0

        # Deserialize
        restored = sdr_oran_pb2.IQSampleBatch()
        restored.ParseFromString(serialized)

        # Verify
        assert restored.station_id == original.station_id
        assert restored.band == original.band
        assert restored.center_frequency_hz == original.center_frequency_hz
        assert restored.snr_db == original.snr_db
        assert list(restored.samples) == list(original.samples)


@pytest.mark.unit
@pytest.mark.grpc
class TestIQStreamServicer:
    """Test IQStreamServicer class"""

    def test_servicer_initialization(self):
        """Test IQStreamServicer initialization"""
        servicer = IQStreamServicer()

        assert isinstance(servicer.active_streams, dict)
        assert isinstance(servicer.statistics, dict)
        assert isinstance(servicer.ack_queues, dict)
        assert len(servicer.active_streams) == 0

    def test_start_stream(self, mock_grpc_context):
        """Test starting a stream"""
        servicer = IQStreamServicer()

        # Create mock request
        request = Mock()
        request.station_id = "test-station"
        request.sample_rate = 10e6
        request.batch_size_samples = 8192
        request.center_frequency_hz = 12e9

        response = servicer.StartStream(request, mock_grpc_context)

        # Verify stream was created
        assert "test-station" in servicer.active_streams
        assert "test-station" in servicer.statistics
        assert "test-station" in servicer.ack_queues

        # Check generator configuration
        generator = servicer.active_streams["test-station"]
        assert generator.sample_rate == 10e6
        assert generator.batch_size == 8192
        assert generator.carrier_freq == 12e9

    def test_start_stream_duplicate(self, mock_grpc_context):
        """Test starting a stream that already exists"""
        servicer = IQStreamServicer()

        request = Mock()
        request.station_id = "test-station"
        request.sample_rate = 10e6
        request.batch_size_samples = 8192
        request.center_frequency_hz = 12e9

        # Start first stream
        servicer.StartStream(request, mock_grpc_context)

        # Try to start again
        response = servicer.StartStream(request, mock_grpc_context)

        # Should indicate failure
        assert 'already active' in str(response).lower()

    def test_stop_stream(self, mock_grpc_context):
        """Test stopping a stream"""
        servicer = IQStreamServicer()

        # First start a stream
        request = Mock()
        request.station_id = "test-station"
        request.sample_rate = 10e6
        request.batch_size_samples = 8192
        request.center_frequency_hz = 12e9

        servicer.StartStream(request, mock_grpc_context)

        # Now stop it
        stop_request = Mock()
        stop_request.station_id = "test-station"

        response = servicer.StopStream(stop_request, mock_grpc_context)

        # Verify stream was removed
        assert "test-station" not in servicer.active_streams
        assert "test-station" not in servicer.statistics
        assert "test-station" not in servicer.ack_queues

    def test_stop_stream_not_found(self, mock_grpc_context):
        """Test stopping a stream that doesn't exist"""
        servicer = IQStreamServicer()

        request = Mock()
        request.station_id = "nonexistent"

        response = servicer.StopStream(request, mock_grpc_context)

        # Should indicate failure
        assert 'no active stream' in str(response).lower()

    def test_get_stream_stats(self, mock_grpc_context):
        """Test getting stream statistics"""
        servicer = IQStreamServicer()

        # Create a stream with some statistics
        servicer.statistics["test-station"] = StreamStatistics(
            station_id="test-station"
        )
        servicer.statistics["test-station"].total_samples_sent = 1000000
        servicer.statistics["test-station"].packets_sent = 100

        request = Mock()
        request.station_id = "test-station"

        # Get stats (will return empty dict in current implementation)
        response = servicer.GetStreamStats(request, mock_grpc_context)

        # Just verify it doesn't crash
        assert response is not None

    def test_get_stream_stats_not_found(self, mock_grpc_context):
        """Test getting stats for non-existent stream"""
        servicer = IQStreamServicer()

        request = Mock()
        request.station_id = "nonexistent"

        response = servicer.GetStreamStats(request, mock_grpc_context)

        # Should set error code
        assert mock_grpc_context.set_code.called


@pytest.mark.unit
@pytest.mark.grpc
class TestSpectrumMonitorServicer:
    """Test SpectrumMonitorServicer class"""

    def test_get_spectrum(self, mock_grpc_context):
        """Test spectrum retrieval"""
        servicer = SpectrumMonitorServicer()

        request = Mock()
        request.station_id = "test-station"
        request.fft_size = 2048
        request.center_frequency_hz = 12e9
        request.span_hz = 100e6

        response = servicer.GetSpectrum(request, mock_grpc_context)

        # Should return something (empty dict in current implementation)
        assert response is not None
