"""Tests for E2 Interface"""

import pytest
import asyncio
from datetime import datetime

import sys
sys.path.insert(0, '/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ric-platform/e2-interface')

from e2_messages import E2SetupRequest, E2NodeComponentConfig
from e2_manager import E2InterfaceManager
from e2sm_kpm import E2SM_KPM, MeasurementType, MeasurementRecord


class TestE2Messages:
    """Test E2 message structures"""

    def test_e2_setup_request(self):
        """Test E2 Setup Request creation"""
        request = E2SetupRequest(
            transaction_id=1,
            global_e2_node_id="gnb-001",
            ran_functions=[E2SM_KPM.RAN_FUNCTION_DEFINITION],
            e2_node_component_config=[
                E2NodeComponentConfig("DU", 1)
            ]
        )

        assert request.transaction_id == 1
        assert request.global_e2_node_id == "gnb-001"
        assert len(request.ran_functions) == 1


class TestE2SM_KPM:
    """Test E2SM-KPM service model"""

    def test_measurement_record(self):
        """Test measurement record creation"""
        record = MeasurementRecord(
            measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
            value=100.5,
            timestamp=1234567890,
            ue_id="ue-001"
        )

        assert record.value == 100.5
        assert record.ue_id == "ue-001"

    def test_kpm_indication_encoding(self):
        """Test KPM indication encoding"""
        measurements = [
            MeasurementRecord(
                measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
                value=100.5,
                timestamp=1234567890
            )
        ]

        header, message = E2SM_KPM.create_indication(measurements)

        assert len(header) > 0
        assert len(message) > 0


@pytest.mark.asyncio
class TestE2Manager:
    """Test E2 Interface Manager"""

    async def test_manager_start_stop(self):
        """Test manager lifecycle"""
        manager = E2InterfaceManager()

        await manager.start()
        assert manager.running

        await manager.stop()
        assert not manager.running

    async def test_e2_setup_handling(self):
        """Test E2 setup request handling"""
        manager = E2InterfaceManager()
        await manager.start()

        request = E2SetupRequest(
            transaction_id=1,
            global_e2_node_id="gnb-001",
            ran_functions=[E2SM_KPM.RAN_FUNCTION_DEFINITION],
            e2_node_component_config=[]
        )

        response = await manager.handle_e2_setup(request)

        assert response.transaction_id == 1
        assert "gnb-001" in manager.connected_nodes

        await manager.stop()
