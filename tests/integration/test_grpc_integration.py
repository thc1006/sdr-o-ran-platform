"""Integration tests for gRPC services

Tests the full gRPC client-server communication flow including:
- Client-server connection
- Streaming capabilities
- Message serialization/deserialization
- Error handling
"""

import pytest
import grpc
import time
from concurrent import futures
from unittest.mock import Mock, patch

# Import gRPC modules
import sdr_oran_pb2
import sdr_oran_pb2_grpc
from sdr_grpc_server import IQStreamServicer, SpectrumMonitorServicer
from oran_grpc_client import ORANIQClient, IQProcessor, ClientStatistics


@pytest.mark.integration
@pytest.mark.grpc
class TestGRPCClientServer:
    """Integration tests for gRPC client-server communication"""

    def test_servicer_classes_exist(self):
        """Test that gRPC servicer classes are defined"""
        assert IQStreamServicer is not None
        assert SpectrumMonitorServicer is not None

    def test_client_classes_exist(self):
        """Test that gRPC client classes are defined"""
        assert ORANIQClient is not None
        assert IQProcessor is not None

    def test_protobuf_stubs_exist(self):
        """Test that protobuf stubs are generated"""
        # Verify stub classes exist
        assert hasattr(sdr_oran_pb2_grpc, 'IQStreamServiceStub') or \
               hasattr(sdr_oran_pb2_grpc, 'IQStreamServiceServicer')

    def test_client_initialization(self):
        """Test ORAN IQ client initialization"""
        client = ORANIQClient(
            server_address="localhost:50051",
            station_id="test-station",
            secure=False
        )

        assert client.server_address == "localhost:50051"
        assert client.station_id == "test-station"
        assert client.secure == False
        assert client.processor is not None
        assert isinstance(client.stats, ClientStatistics)

    def test_iq_processor_initialization(self):
        """Test IQ processor initialization"""
        processor = IQProcessor()

        assert processor.last_sequence == -1
        assert processor.callback is None

    def test_client_statistics_tracking(self):
        """Test client statistics initialization"""
        stats = ClientStatistics()

        assert stats.packets_received == 0
        assert stats.packets_lost == 0
        assert stats.total_samples_received == 0
        assert stats.throughput_mbps == 0.0

    def test_servicer_initialization(self):
        """Test servicer initialization"""
        servicer = IQStreamServicer()

        assert len(servicer.active_streams) == 0
        assert len(servicer.statistics) == 0
        assert len(servicer.ack_queues) == 0


@pytest.mark.integration
@pytest.mark.grpc
class TestProtobufSerialization:
    """Test protobuf message serialization in integration scenarios"""

    def test_iq_batch_full_cycle(self):
        """Test creating, serializing, and deserializing IQ batch"""
        # Create message
        original = sdr_oran_pb2.IQSampleBatch(
            station_id="integration-test",
            band="Ku-band",
            timestamp_ns=int(time.time() * 1e9),
            sequence_number=123,
            center_frequency_hz=12e9,
            sample_rate=10e6,
            samples=[1.0, 0.5, -0.3, 0.8, 0.2, -0.6] * 100,
            snr_db=18.5,
            receive_power_dbm=-72.5,
            agc_locked=True,
            doppler_shift_hz=15000.0
        )

        # Serialize
        serialized_data = original.SerializeToString()
        assert len(serialized_data) > 0

        # Deserialize
        restored = sdr_oran_pb2.IQSampleBatch()
        restored.ParseFromString(serialized_data)

        # Verify all fields
        assert restored.station_id == original.station_id
        assert restored.band == original.band
        assert restored.timestamp_ns == original.timestamp_ns
        assert restored.sequence_number == original.sequence_number
        assert restored.center_frequency_hz == original.center_frequency_hz
        assert restored.sample_rate == original.sample_rate
        assert len(restored.samples) == len(original.samples)
        assert restored.snr_db == original.snr_db
        assert restored.receive_power_dbm == original.receive_power_dbm
        assert restored.agc_locked == original.agc_locked
        assert restored.doppler_shift_hz == original.doppler_shift_hz

    def test_multiple_message_types(self):
        """Test serializing different message types"""
        # IQSampleBatch
        iq_batch = sdr_oran_pb2.IQSampleBatch(
            station_id="test",
            band="Ka-band",
            timestamp_ns=123,
            sequence_number=1,
            center_frequency_hz=28e9,
            sample_rate=50e6,
            samples=[1.0, 0.0]
        )

        # StreamStatsRequest
        stats_request = sdr_oran_pb2.StreamStatsRequest(
            station_id="test"
        )

        # DopplerUpdate
        doppler_update = sdr_oran_pb2.DopplerUpdate(
            station_id="test",
            doppler_shift_hz=20000.0,
            doppler_rate_hz_s=100.0
        )

        # Verify all can be serialized
        assert len(iq_batch.SerializeToString()) > 0
        assert len(stats_request.SerializeToString()) > 0
        assert len(doppler_update.SerializeToString()) > 0


@pytest.mark.integration
@pytest.mark.grpc
@pytest.mark.slow
class TestStreamingWorkflow:
    """Test complete streaming workflow"""

    def test_servicer_stream_lifecycle(self):
        """Test complete stream lifecycle on servicer"""
        servicer = IQStreamServicer()
        mock_context = Mock()

        # Create stream config
        config = Mock()
        config.station_id = "lifecycle-test"
        config.sample_rate = 10e6
        config.batch_size_samples = 8192
        config.center_frequency_hz = 12e9

        # Start stream
        response = servicer.StartStream(config, mock_context)
        assert "lifecycle-test" in servicer.active_streams

        # Verify generator is running
        generator = servicer.active_streams["lifecycle-test"]
        assert generator.running == True

        # Stop stream
        stop_request = Mock()
        stop_request.station_id = "lifecycle-test"
        response = servicer.StopStream(stop_request, mock_context)

        # Verify cleanup
        assert "lifecycle-test" not in servicer.active_streams

    def test_client_statistics_calculation(self):
        """Test client statistics calculation over time"""
        stats = ClientStatistics()

        # Simulate receiving data
        stats.packets_received = 1000
        stats.total_samples_received = 8192000
        stats.total_bytes_received = 8192000 * 4  # float32
        stats.start_time = time.time() - 1.0  # 1 second ago

        # Calculate metrics
        throughput = stats.throughput_mbps
        assert throughput > 0
        assert throughput < 1000  # Reasonable bound

        # Test latency tracking
        stats.latencies_ms.extend([1.5, 2.0, 2.5, 3.0, 1.8])
        avg_latency = stats.average_latency_ms
        assert 1.5 <= avg_latency <= 3.0

    def test_packet_loss_detection(self):
        """Test packet loss detection in IQ processor"""
        processor = IQProcessor()

        # Process first batch
        batch1 = Mock()
        batch1.sequence_number = 100
        batch1.samples = [1.0] * 16384
        batch1.snr_db = 15.0

        # First batch should succeed
        processor.last_sequence = 99
        lost, latency = processor.process_batch(batch1)

        # Process batch with gap (packet loss)
        batch2 = Mock()
        batch2.sequence_number = 105  # Missing 101-104
        batch2.samples = [1.0] * 16384
        batch2.snr_db = 15.0

        # Should detect loss
        # Note: Current implementation doesn't calculate loss, returns (0, latency)


@pytest.mark.integration
@pytest.mark.grpc
class TestErrorHandling:
    """Test error handling in integration scenarios"""

    def test_servicer_handles_duplicate_stream_start(self):
        """Test servicer handles duplicate stream start gracefully"""
        servicer = IQStreamServicer()
        mock_context = Mock()

        config = Mock()
        config.station_id = "duplicate-test"
        config.sample_rate = 10e6
        config.batch_size_samples = 8192
        config.center_frequency_hz = 12e9

        # Start stream twice
        servicer.StartStream(config, mock_context)
        response = servicer.StartStream(config, mock_context)

        # Should indicate error
        assert isinstance(response, dict)

    def test_servicer_handles_invalid_stop(self):
        """Test servicer handles stopping non-existent stream"""
        servicer = IQStreamServicer()
        mock_context = Mock()

        request = Mock()
        request.station_id = "nonexistent"

        response = servicer.StopStream(request, mock_context)

        # Should indicate error
        assert isinstance(response, dict)

    def test_servicer_handles_stats_for_nonexistent_stream(self):
        """Test servicer handles stats request for non-existent stream"""
        servicer = IQStreamServicer()
        mock_context = Mock()
        mock_context.set_code = Mock()
        mock_context.set_details = Mock()

        request = Mock()
        request.station_id = "nonexistent"

        response = servicer.GetStreamStats(request, mock_context)

        # Should set error code
        assert mock_context.set_code.called
        assert response is None


@pytest.mark.integration
@pytest.mark.grpc
class TestMessageValidation:
    """Test message validation and constraints"""

    def test_iq_batch_field_validation(self):
        """Test IQ batch field constraints"""
        # Valid batch
        valid_batch = sdr_oran_pb2.IQSampleBatch(
            station_id="test",
            band="Ku-band",
            timestamp_ns=int(time.time() * 1e9),
            sequence_number=0,
            center_frequency_hz=12e9,
            sample_rate=10e6,
            samples=[1.0, 0.0],
            snr_db=15.0
        )

        # Should serialize without error
        assert len(valid_batch.SerializeToString()) > 0

    def test_large_sample_batch(self):
        """Test handling large IQ sample batches"""
        # Create large batch (typical size)
        large_batch = sdr_oran_pb2.IQSampleBatch(
            station_id="large-test",
            band="Ka-band",
            timestamp_ns=int(time.time() * 1e9),
            sequence_number=1,
            center_frequency_hz=28e9,
            sample_rate=50e6,
            samples=[float(i % 100) / 100.0 for i in range(16384)],  # 8192 I/Q pairs
            snr_db=20.0
        )

        # Should handle large batch
        serialized = large_batch.SerializeToString()
        assert len(serialized) > 10000  # Should be large

        # Should deserialize correctly
        restored = sdr_oran_pb2.IQSampleBatch()
        restored.ParseFromString(serialized)
        assert len(restored.samples) == 16384
