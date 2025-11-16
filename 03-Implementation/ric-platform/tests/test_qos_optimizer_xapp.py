"""
Unit tests for QoS Optimizer xApp
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from xapps.qos_optimizer_xapp import QoSOptimizerXApp


@pytest.fixture
def qos_xapp():
    """Create QoS Optimizer xApp"""
    with patch('xapps.qos_optimizer_xapp.SDLClient'):
        xapp = QoSOptimizerXApp()
        xapp.sdl = Mock()
        return xapp


@pytest.mark.asyncio
async def test_qos_xapp_initialization(qos_xapp):
    """Test QoS xApp initialization"""
    qos_xapp.sdl.get.return_value = None

    await qos_xapp.init()

    assert len(qos_xapp.ue_metrics) == 0


@pytest.mark.asyncio
async def test_qos_xapp_load_previous_state(qos_xapp):
    """Test loading previous state from SDL"""
    previous_metrics = {
        "UE1": {"throughput_dl_mbps": 15.0}
    }
    qos_xapp.sdl.get.return_value = previous_metrics

    await qos_xapp.init()

    assert qos_xapp.ue_metrics == previous_metrics


@pytest.mark.asyncio
async def test_handle_indication_updates_metrics(qos_xapp):
    """Test handling indication updates UE metrics"""
    await qos_xapp.init()

    indication = Mock()
    indication.ric_indication_message = '{"measurements": [{"ueId": "UE1", "value": 12.0, "cellId": "Cell1"}]}'

    await qos_xapp.handle_indication(indication)

    assert "UE1" in qos_xapp.ue_metrics
    assert qos_xapp.ue_metrics["UE1"]["throughput_dl_mbps"] == 12.0
    qos_xapp.sdl.set.assert_called()


@pytest.mark.asyncio
async def test_qos_control_triggered_on_low_throughput(qos_xapp):
    """Test QoS control triggered on low throughput"""
    await qos_xapp.init()

    # Set low throughput
    qos_xapp.ue_metrics["UE1"] = {
        "throughput_dl_mbps": 5.0,
        "cell_id": "Cell1"
    }

    await qos_xapp._check_qos_adjustment("UE1")

    # Should trigger QoS control
    qos_xapp.sdl.set.assert_called()
    assert qos_xapp.metrics.get("qos_controls_sent", {}).get("value", 0) > 0


@pytest.mark.asyncio
async def test_qos_control_decrease_on_high_throughput(qos_xapp):
    """Test QoS control decrease on very high throughput"""
    await qos_xapp.init()

    # Set very high throughput
    qos_xapp.ue_metrics["UE1"] = {
        "throughput_dl_mbps": 25.0,
        "cell_id": "Cell1"
    }

    await qos_xapp._check_qos_adjustment("UE1")

    # Should trigger QoS decrease
    qos_xapp.sdl.set.assert_called()


@pytest.mark.asyncio
async def test_no_qos_control_on_normal_throughput(qos_xapp):
    """Test no QoS control on normal throughput"""
    await qos_xapp.init()

    # Set normal throughput
    qos_xapp.ue_metrics["UE1"] = {
        "throughput_dl_mbps": 15.0,
        "cell_id": "Cell1"
    }

    qos_xapp.sdl.set.reset_mock()
    await qos_xapp._check_qos_adjustment("UE1")

    # Should not trigger extra QoS control
    # (SDL set is only called for storing UE metrics, not control action)
    assert "qos_controls_sent" not in qos_xapp.metrics


def test_parse_kpm_indication_valid(qos_xapp):
    """Test parsing valid KPM indication"""
    indication = Mock()
    indication.ric_indication_message = '{"measurements": [{"ueId": "UE1", "value": 10.0}]}'

    result = qos_xapp._parse_kpm_indication(indication)

    assert len(result) == 1
    assert result[0]["ueId"] == "UE1"


def test_parse_kpm_indication_invalid(qos_xapp):
    """Test parsing invalid KPM indication"""
    indication = Mock()
    indication.ric_indication_message = 'invalid json'

    result = qos_xapp._parse_kpm_indication(indication)

    assert result == []
