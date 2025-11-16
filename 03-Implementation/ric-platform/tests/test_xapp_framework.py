"""
Unit tests for xApp Framework
"""

import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from xapp_sdk.xapp_framework import XAppBase, XAppConfig


class TestXApp(XAppBase):
    """Test implementation of XAppBase"""

    async def init(self):
        """Initialize test xApp"""
        self.initialized = True

    async def handle_indication(self, indication):
        """Handle test indication"""
        self.last_indication = indication


@pytest.fixture
def xapp_config():
    """Create test xApp configuration"""
    return XAppConfig(
        name="test-xapp",
        version="1.0.0",
        description="Test xApp",
        e2_subscriptions=[{"ran_function_id": 1}],
        sdl_namespace="test"
    )


@pytest.fixture
def test_xapp(xapp_config):
    """Create test xApp instance"""
    return TestXApp(xapp_config)


@pytest.mark.asyncio
async def test_xapp_initialization(test_xapp):
    """Test xApp initialization"""
    assert not test_xapp.running
    assert len(test_xapp.metrics) == 0

    await test_xapp.start()

    assert test_xapp.running
    assert test_xapp.initialized


@pytest.mark.asyncio
async def test_xapp_stop(test_xapp):
    """Test xApp stop"""
    await test_xapp.start()
    assert test_xapp.running

    await test_xapp.stop()
    assert not test_xapp.running


@pytest.mark.asyncio
async def test_xapp_handle_indication(test_xapp):
    """Test handling indications"""
    await test_xapp.start()

    test_indication = {"type": "test", "data": "test_data"}
    await test_xapp.handle_indication(test_indication)

    assert test_xapp.last_indication == test_indication


def test_xapp_update_metric(test_xapp):
    """Test metric updates"""
    test_xapp.update_metric("test_metric", 42.0)

    assert "test_metric" in test_xapp.metrics
    assert test_xapp.metrics["test_metric"]["value"] == 42.0
    assert "timestamp" in test_xapp.metrics["test_metric"]


def test_xapp_config_creation(xapp_config):
    """Test XAppConfig creation"""
    assert xapp_config.name == "test-xapp"
    assert xapp_config.version == "1.0.0"
    assert xapp_config.metrics_enabled is True
    assert len(xapp_config.e2_subscriptions) == 1


@pytest.mark.asyncio
async def test_multiple_metric_updates(test_xapp):
    """Test multiple metric updates"""
    test_xapp.update_metric("metric1", 10.0)
    test_xapp.update_metric("metric2", 20.0)
    test_xapp.update_metric("metric1", 15.0)  # Update existing

    assert len(test_xapp.metrics) == 2
    assert test_xapp.metrics["metric1"]["value"] == 15.0
    assert test_xapp.metrics["metric2"]["value"] == 20.0
