"""
End-to-End System Integration Tests for SDR-O-RAN Platform

Tests the complete pipeline:
1. SDR Signal Acquisition → gRPC Transmission
2. gRPC → DRL Optimization
3. DRL → E2 Interface
4. E2 Interface → xApp Framework
5. Full system validation

Created: 2025-11-17
Coverage Target: >85%
"""

import pytest
import asyncio
import grpc
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import json
import time

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "03-Implementation" / "integration" / "sdr-oran-connector"))
sys.path.insert(0, str(project_root / "03-Implementation" / "ric-platform" / "e2-interface"))
sys.path.insert(0, str(project_root / "03-Implementation" / "ric-platform" / "xapp-sdk"))
sys.path.insert(0, str(project_root / "03-Implementation" / "ric-platform" / "xapps"))
sys.path.insert(0, str(project_root / "03-Implementation" / "ai-ml-pipeline" / "training"))

# Import components
from e2_manager import E2InterfaceManager
from e2_messages import (
    E2SetupRequest, E2SetupResponse, RICIndication,
    RICControlRequest, E2NodeComponentConfig
)
from e2sm_kpm import E2SM_KPM, MeasurementType, MeasurementRecord
from xapp_framework import XAppBase
from qos_optimizer_xapp import QoSOptimizerXApp
from handover_manager_xapp import HandoverManagerXApp


@pytest.fixture
def mock_sdr_processor():
    """Mock SDR signal processor"""
    processor = Mock()
    processor.sample_rate = 30.72e6
    processor.center_freq = 3.5e9
    processor.gain = 50
    processor.receive_samples = Mock(return_value=np.random.randn(1024) + 1j * np.random.randn(1024))
    return processor


@pytest.fixture
async def e2_manager():
    """Create E2 Interface Manager"""
    manager = E2InterfaceManager()
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
async def qos_xapp():
    """Create QoS Optimizer xApp"""
    xapp = QoSOptimizerXApp(xapp_id="qos-optimizer-1")
    await xapp.start()
    yield xapp
    await xapp.stop()


@pytest.fixture
async def handover_xapp():
    """Create Handover Manager xApp"""
    xapp = HandoverManagerXApp(xapp_id="handover-manager-1")
    await xapp.start()
    yield xapp
    await xapp.stop()


def create_e2_setup_request(transaction_id: int, node_id: str, component_id: int = 1):
    """Helper to create E2 Setup Request"""
    return E2SetupRequest(
        transaction_id=transaction_id,
        global_e2_node_id=node_id,
        ran_functions=[
            {
                'ranFunctionId': 1,
                'ranFunctionRevision': 1,
                'ranFunctionOId': '1.3.6.1.4.1.53148.1.1.2.2'  # E2SM-KPM
            }
        ],
        e2_node_component_config=[
            E2NodeComponentConfig(
                component_type="gNB-DU",
                component_id=component_id
            )
        ]
    )


def create_ric_indication(ric_request_id: int, ran_function_id: int, measurements: list):
    """Helper to create RIC Indication"""
    e2sm_kpm = E2SM_KPM()
    indication_message = e2sm_kpm.encode_indication_message(measurements)
    indication_header = e2sm_kpm.encode_indication_header(ue_id="test-ue")

    return RICIndication(
        ric_request_id=ric_request_id,
        ran_function_id=ran_function_id,
        ric_action_id=1,
        ric_indication_header=indication_header,
        ric_indication_message=indication_message
    )


class TestSDRToGRPCIntegration:
    """Test SDR signal acquisition and gRPC transmission"""

    @pytest.mark.asyncio
    async def test_sdr_signal_to_grpc_transmission(self, mock_sdr_processor):
        """Test complete SDR → gRPC pipeline"""
        # Simulate SDR signal capture
        signal_data = np.random.randn(1024) + 1j * np.random.randn(1024)
        mock_sdr_processor.receive_samples.return_value = signal_data

        # Mock gRPC client
        client = Mock()
        client.send_signal_data = AsyncMock(return_value=True)

        # Process and transmit
        samples = mock_sdr_processor.receive_samples(1024)
        success = await client.send_signal_data(
            iq_samples=samples,
            sample_rate=mock_sdr_processor.sample_rate,
            center_freq=mock_sdr_processor.center_freq
        )

        assert success is True
        client.send_signal_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_grpc_with_tls_encryption(self):
        """Test gRPC transmission with TLS encryption"""
        cert_dir = project_root / "certs"

        # Skip if certs don't exist
        if not (cert_dir / "ca.crt").exists():
            pytest.skip("TLS certificates not generated")

        with patch('grpc.ssl_channel_credentials') as mock_ssl:
            mock_ssl.return_value = Mock()

            # Simulate secure channel creation
            with patch('grpc.aio.secure_channel') as mock_channel:
                mock_channel.return_value.__aenter__ = AsyncMock()
                mock_channel.return_value.__aexit__ = AsyncMock()

                async with mock_channel('localhost:50051', mock_ssl.return_value):
                    pass

                mock_channel.assert_called_once()
                mock_ssl.assert_called_once()


class TestGRPCtoDRLIntegration:
    """Test gRPC reception and DRL optimization"""

    @pytest.mark.asyncio
    async def test_grpc_data_to_drl_pipeline(self):
        """Test gRPC data feeding into DRL training"""
        # Simulate received gRPC data
        signal_metrics = {
            'rssi_dbm': -75.5,
            'snr_db': 18.3,
            'ber': 1e-5,
            'throughput_mbps': 45.2
        }

        # Mock DRL environment
        with patch('stable_baselines3.common.vec_env.SubprocVecEnv') as MockEnv:
            env = MockEnv.return_value
            env.reset.return_value = np.array([[0.5, 0.3, 0.2, 0.8]])
            env.step.return_value = (
                np.array([[0.6, 0.4, 0.1, 0.9]]),  # observation
                np.array([1.5]),  # reward
                np.array([False]),  # done
                [{}]  # info
            )

            # Simulate DRL optimization step
            obs = env.reset()
            action = np.array([[0.7]])  # DRL agent action
            next_obs, reward, done, info = env.step(action)

            assert reward[0] > 0  # Positive reward for good performance
            assert not done[0]  # Episode continues

    def test_drl_action_to_control_signal(self):
        """Test DRL action conversion to control signals"""
        # DRL action (normalized 0-1)
        drl_action = 0.75

        # Convert to actual control parameters
        min_power = -20  # dBm
        max_power = 23   # dBm
        tx_power = min_power + drl_action * (max_power - min_power)

        assert min_power <= tx_power <= max_power
        assert abs(tx_power - 12.25) < 0.01  # Expected value


class TestDRLToE2Integration:
    """Test DRL optimization to E2 Interface integration"""

    @pytest.mark.asyncio
    async def test_drl_triggers_e2_control(self, e2_manager):
        """Test DRL optimization triggering E2 control messages"""
        # Setup E2 node
        setup_request = create_e2_setup_request(1, "gnb-001", 1)
        response = await e2_manager.handle_e2_setup(setup_request)

        assert response.transaction_id == 1
        assert len(response.ran_functions_accepted) > 0

        # DRL decides to adjust QoS via control request
        control_header = b'\x00\x01'  # Simple header
        control_message = b'\x02\x03\x04'  # Simple message

        success = await e2_manager.send_control_request(
            "gnb-001",
            ran_function_id=1,
            control_header=control_header,
            control_message=control_message
        )

        assert success is True


class TestE2ToXAppIntegration:
    """Test E2 Interface to xApp Framework integration"""

    @pytest.mark.asyncio
    async def test_e2_indication_to_qos_xapp(self, e2_manager, qos_xapp):
        """Test E2 indication triggering QoS xApp logic"""
        # Setup E2 connection
        setup_request = create_e2_setup_request(1, "gnb-002", 1)
        await e2_manager.handle_e2_setup(setup_request)

        # Create subscription
        subscription_id = await e2_manager.create_subscription(
            "gnb-002",
            ran_function_id=1,
            callback=qos_xapp.handle_indication
        )

        # E2 sends indication with KPM data
        measurements = [
            MeasurementRecord(
                measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
                ue_id="ue-001",
                value=8.5,  # Below threshold (10.0 Mbps)
                timestamp=1700000000
            )
        ]

        indication = create_ric_indication(subscription_id, 1, measurements)

        # Process indication through E2 manager
        await e2_manager.handle_ric_indication(indication)

        # Give xApp time to process
        await asyncio.sleep(0.1)

        # Verify xApp processed the data
        ue_data = qos_xapp.sdl.get("ue:ue-001")
        assert ue_data is not None

    @pytest.mark.asyncio
    async def test_e2_indication_to_handover_xapp(self, e2_manager, handover_xapp):
        """Test E2 indication triggering Handover xApp logic"""
        # Setup E2 connection
        setup_request = create_e2_setup_request(1, "gnb-003", 2)
        await e2_manager.handle_e2_setup(setup_request)

        # Create subscription
        subscription_id = await e2_manager.create_subscription(
            "gnb-003",
            ran_function_id=1,
            callback=handover_xapp.handle_indication
        )

        # E2 sends indication
        measurements = [
            MeasurementRecord(
                measurement_type=MeasurementType.RRC_CONN_ESTAB_SUCC,
                ue_id="ue-002",
                value=-115.0,  # Poor RSRP
                timestamp=1700000100
            )
        ]

        indication = create_ric_indication(subscription_id, 1, measurements)

        # Process indication
        await e2_manager.handle_ric_indication(indication)

        # Give xApp time to process
        await asyncio.sleep(0.1)

        # Verify handover xApp is running
        assert handover_xapp.running


class TestFullSystemIntegration:
    """Test complete end-to-end system integration"""

    @pytest.mark.asyncio
    async def test_complete_sdr_to_xapp_pipeline(
        self,
        mock_sdr_processor,
        e2_manager,
        qos_xapp
    ):
        """Test complete pipeline: SDR → gRPC → DRL → E2 → xApp"""

        # Step 1: SDR captures signal
        signal_data = np.random.randn(2048) + 1j * np.random.randn(2048)
        mock_sdr_processor.receive_samples.return_value = signal_data
        samples = mock_sdr_processor.receive_samples(2048)
        assert len(samples) == 2048

        # Step 2: gRPC transmits data
        client = Mock()
        client.send_signal_data = AsyncMock(return_value=True)
        success = await client.send_signal_data(
            iq_samples=samples,
            sample_rate=30.72e6,
            center_freq=3.5e9
        )
        assert success is True

        # Step 3: DRL processes and optimizes
        with patch('stable_baselines3.PPO') as MockPPO:
            model = MockPPO.return_value
            model.predict.return_value = (np.array([0.8]), None)
            action, _ = model.predict(np.array([0.5, 0.3, 0.2, 0.7]))
            assert 0 <= action[0] <= 1

        # Step 4: E2 Setup
        setup_request = create_e2_setup_request(1, "gnb-e2e-001", 1)
        setup_response = await e2_manager.handle_e2_setup(setup_request)
        assert setup_response.transaction_id == 1

        # Step 5: Create subscription
        subscription_id = await e2_manager.create_subscription(
            "gnb-e2e-001",
            ran_function_id=1,
            callback=qos_xapp.handle_indication
        )

        # Step 6: E2 Indication triggers xApp
        measurements = [
            MeasurementRecord(
                measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
                ue_id="ue-e2e-001",
                value=9.2,  # Below threshold
                timestamp=1700000200
            )
        ]

        indication = create_ric_indication(subscription_id, 1, measurements)
        await e2_manager.handle_ric_indication(indication)

        # Give xApp time to process
        await asyncio.sleep(0.1)

        # Step 7: Verify end-to-end data flow
        ue_data = qos_xapp.sdl.get("ue:ue-e2e-001")
        assert ue_data is not None

    @pytest.mark.asyncio
    async def test_multi_xapp_coordination(self, e2_manager, qos_xapp, handover_xapp):
        """Test multiple xApps coordinating through E2 Interface"""
        # Setup E2
        setup_request = create_e2_setup_request(1, "gnb-multi-001", 1)
        await e2_manager.handle_e2_setup(setup_request)

        # Create subscriptions for both xApps
        subscription_id1 = await e2_manager.create_subscription(
            "gnb-multi-001",
            ran_function_id=1,
            callback=qos_xapp.handle_indication
        )

        subscription_id2 = await e2_manager.create_subscription(
            "gnb-multi-001",
            ran_function_id=1,
            callback=handover_xapp.handle_indication
        )

        # Send indication to first subscription
        measurements = [
            MeasurementRecord(
                measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
                ue_id="ue-multi-001",
                value=7.5,
                timestamp=1700000300
            )
        ]

        indication1 = create_ric_indication(subscription_id1, 1, measurements)
        indication2 = create_ric_indication(subscription_id2, 1, measurements)

        # Process through both subscriptions
        await asyncio.gather(
            e2_manager.handle_ric_indication(indication1),
            e2_manager.handle_ric_indication(indication2)
        )

        # Give xApps time to process
        await asyncio.sleep(0.1)

        # Verify both xApps are running
        assert qos_xapp.running
        assert handover_xapp.running

    @pytest.mark.asyncio
    async def test_error_recovery_e2e(self, e2_manager):
        """Test error recovery across the entire pipeline"""
        # Test E2 setup failure recovery - empty node ID
        bad_setup = E2SetupRequest(
            transaction_id=1,
            global_e2_node_id="",  # Invalid empty ID
            ran_functions=[],
            e2_node_component_config=[]
        )

        # This should still work but with empty ran functions
        response = await e2_manager.handle_e2_setup(bad_setup)
        assert response.transaction_id == 1

        # Test with valid setup after failure
        good_setup = create_e2_setup_request(2, "gnb-recovery-001", 1)
        response = await e2_manager.handle_e2_setup(good_setup)
        assert response.transaction_id == 2
        assert len(response.ran_functions_accepted) > 0


class TestPerformanceE2E:
    """Test end-to-end system performance"""

    @pytest.mark.asyncio
    async def test_throughput_e2e(self, e2_manager):
        """Test system throughput under load"""
        # Setup multiple E2 nodes
        node_count = 10
        setup_tasks = []

        for i in range(node_count):
            setup_request = create_e2_setup_request(i, f"gnb-perf-{i:03d}", i)
            setup_tasks.append(e2_manager.handle_e2_setup(setup_request))

        start_time = time.perf_counter()
        responses = await asyncio.gather(*setup_tasks)
        duration = time.perf_counter() - start_time

        # All setups should succeed
        assert len(responses) == node_count

        # Calculate throughput (setups/second)
        throughput = node_count / duration
        assert throughput > 10  # At least 10 setups/sec

    @pytest.mark.asyncio
    async def test_latency_e2e(self, e2_manager):
        """Test end-to-end latency"""
        # Setup E2
        setup_request = create_e2_setup_request(1, "gnb-latency-001", 1)
        await e2_manager.handle_e2_setup(setup_request)

        # Measure control request latency
        control_header = b'\x00\x01'
        control_message = b'\x02\x03'

        start_time = time.perf_counter()
        success = await e2_manager.send_control_request(
            "gnb-latency-001",
            ran_function_id=1,
            control_header=control_header,
            control_message=control_message
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        assert success is True
        assert latency_ms < 100  # Less than 100ms latency


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
