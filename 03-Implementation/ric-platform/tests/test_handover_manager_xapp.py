"""
Unit tests for Handover Manager xApp
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from xapps.handover_manager_xapp import HandoverManagerXApp


@pytest.fixture
def handover_xapp():
    """Create Handover Manager xApp"""
    with patch('xapps.handover_manager_xapp.SDLClient'):
        xapp = HandoverManagerXApp()
        xapp.sdl = Mock()
        return xapp


@pytest.mark.asyncio
async def test_handover_xapp_initialization(handover_xapp):
    """Test Handover Manager xApp initialization"""
    await handover_xapp.init()

    assert len(handover_xapp.ue_measurements) == 0
    assert len(handover_xapp.cell_load) == 0


@pytest.mark.asyncio
async def test_handle_rsrp_measurement(handover_xapp):
    """Test handling RSRP measurement"""
    await handover_xapp.init()

    indication = Mock()
    indication.ric_indication_message = '{"measurements": [{"ueId": "UE1", "cellId": "Cell1", "rsrp": -105}]}'

    await handover_xapp.handle_indication(indication)

    assert "UE1" in handover_xapp.ue_measurements
    assert handover_xapp.ue_measurements["UE1"]["rsrp_dbm"] == -105


@pytest.mark.asyncio
async def test_handle_cell_load_measurement(handover_xapp):
    """Test handling cell load measurement"""
    await handover_xapp.init()

    indication = Mock()
    indication.ric_indication_message = '{"measurements": [{"cellId": "Cell1", "cellLoad": 75.0}]}'

    await handover_xapp.handle_indication(indication)

    assert handover_xapp.cell_load["Cell1"] == 75.0


def test_find_best_neighbor_with_better_signal(handover_xapp):
    """Test finding best neighbor with better signal"""
    ue_data = {
        "rsrp_dbm": -110,
        "neighbor_cells": [
            {"cell_id": "Cell2", "rsrp": -100},
            {"cell_id": "Cell3", "rsrp": -105}
        ]
    }

    result = handover_xapp._find_best_neighbor(ue_data)

    assert result is not None
    assert result["cell_id"] == "Cell2"


def test_find_best_neighbor_no_improvement(handover_xapp):
    """Test finding best neighbor when no improvement"""
    ue_data = {
        "rsrp_dbm": -100,
        "neighbor_cells": [
            {"cell_id": "Cell2", "rsrp": -102},
            {"cell_id": "Cell3", "rsrp": -105}
        ]
    }

    result = handover_xapp._find_best_neighbor(ue_data)

    # Should not handover as improvement is not significant
    assert result is None


def test_find_best_neighbor_no_neighbors(handover_xapp):
    """Test finding best neighbor with no neighbors"""
    ue_data = {
        "rsrp_dbm": -110,
        "neighbor_cells": []
    }

    result = handover_xapp._find_best_neighbor(ue_data)

    assert result is None


def test_find_least_loaded_neighbor(handover_xapp):
    """Test finding least loaded neighbor"""
    handover_xapp.cell_load["Cell2"] = 50.0
    handover_xapp.cell_load["Cell3"] = 70.0

    ue_data = {
        "rsrp_dbm": -100,
        "neighbor_cells": [
            {"cell_id": "Cell2", "rsrp": -95},
            {"cell_id": "Cell3", "rsrp": -98}
        ]
    }

    result = handover_xapp._find_least_loaded_neighbor(ue_data)

    assert result is not None
    assert result["cell_id"] == "Cell2"


def test_find_least_loaded_neighbor_poor_signal(handover_xapp):
    """Test finding least loaded neighbor with poor signal quality"""
    handover_xapp.cell_load["Cell2"] = 30.0

    ue_data = {
        "rsrp_dbm": -100,
        "neighbor_cells": [
            {"cell_id": "Cell2", "rsrp": -120}  # Too weak signal
        ]
    }

    result = handover_xapp._find_least_loaded_neighbor(ue_data)

    assert result is None


@pytest.mark.asyncio
async def test_trigger_handover(handover_xapp):
    """Test triggering handover"""
    await handover_xapp._trigger_handover(
        ue_id="UE1",
        source_cell="Cell1",
        target_cell="Cell2",
        reason="poor_signal"
    )

    handover_xapp.sdl.set.assert_called()
    assert handover_xapp.metrics.get("handovers_triggered", {}).get("value", 0) > 0


@pytest.mark.asyncio
async def test_evaluate_handover_poor_signal(handover_xapp):
    """Test handover evaluation for poor signal"""
    await handover_xapp.init()

    handover_xapp.ue_measurements["UE1"] = {
        "serving_cell": "Cell1",
        "rsrp_dbm": -115,  # Below threshold
        "neighbor_cells": [
            {"cell_id": "Cell2", "rsrp": -100}
        ]
    }

    await handover_xapp._evaluate_handover("UE1")

    # Should trigger handover
    handover_xapp.sdl.set.assert_called()


@pytest.mark.asyncio
async def test_evaluate_handover_overloaded_cell(handover_xapp):
    """Test handover evaluation for overloaded cell"""
    await handover_xapp.init()

    handover_xapp.ue_measurements["UE1"] = {
        "serving_cell": "Cell1",
        "rsrp_dbm": -95,
        "neighbor_cells": [
            {"cell_id": "Cell2", "rsrp": -90}
        ]
    }
    handover_xapp.cell_load["Cell1"] = 85.0  # Overloaded
    handover_xapp.cell_load["Cell2"] = 50.0

    await handover_xapp._evaluate_handover("UE1")

    # Should trigger load balancing handover
    handover_xapp.sdl.set.assert_called()
