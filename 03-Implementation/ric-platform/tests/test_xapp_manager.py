"""
Unit tests for xApp Manager
"""

import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from xapp_sdk.xapp_framework import XAppBase, XAppConfig
from xapp_sdk.xapp_manager import XAppManager


class MockXApp(XAppBase):
    """Mock xApp for testing"""

    def __init__(self, name: str):
        config = XAppConfig(
            name=name,
            version="1.0.0",
            description="Mock xApp",
            e2_subscriptions=[],
            sdl_namespace="test"
        )
        super().__init__(config)

    async def init(self):
        """Initialize mock xApp"""
        pass

    async def handle_indication(self, indication):
        """Handle indication"""
        pass


@pytest.fixture
def manager():
    """Create xApp manager"""
    return XAppManager()


@pytest.fixture
def mock_xapp():
    """Create mock xApp"""
    return MockXApp("test-xapp")


@pytest.mark.asyncio
async def test_deploy_xapp(manager, mock_xapp):
    """Test deploying an xApp"""
    result = await manager.deploy_xapp(mock_xapp)

    assert result is True
    assert "test-xapp" in manager.xapps
    assert mock_xapp.running


@pytest.mark.asyncio
async def test_deploy_duplicate_xapp(manager, mock_xapp):
    """Test deploying duplicate xApp"""
    await manager.deploy_xapp(mock_xapp)
    result = await manager.deploy_xapp(mock_xapp)

    assert result is False


@pytest.mark.asyncio
async def test_undeploy_xapp(manager, mock_xapp):
    """Test undeploying an xApp"""
    await manager.deploy_xapp(mock_xapp)

    result = await manager.undeploy_xapp("test-xapp")

    assert result is True
    assert "test-xapp" not in manager.xapps
    assert not mock_xapp.running


@pytest.mark.asyncio
async def test_undeploy_nonexistent_xapp(manager):
    """Test undeploying nonexistent xApp"""
    result = await manager.undeploy_xapp("nonexistent")

    assert result is False


@pytest.mark.asyncio
async def test_list_xapps(manager):
    """Test listing xApps"""
    xapp1 = MockXApp("xapp1")
    xapp2 = MockXApp("xapp2")

    await manager.deploy_xapp(xapp1)
    await manager.deploy_xapp(xapp2)

    xapps = manager.list_xapps()

    assert len(xapps) == 2
    assert any(x["name"] == "xapp1" for x in xapps)
    assert any(x["name"] == "xapp2" for x in xapps)


@pytest.mark.asyncio
async def test_get_xapp_status(manager, mock_xapp):
    """Test getting xApp status"""
    await manager.deploy_xapp(mock_xapp)

    status = manager.get_xapp_status("test-xapp")

    assert status["name"] == "test-xapp"
    assert status["version"] == "1.0.0"
    assert status["running"] is True
    assert "metrics" in status


@pytest.mark.asyncio
async def test_get_nonexistent_xapp_status(manager):
    """Test getting status of nonexistent xApp"""
    status = manager.get_xapp_status("nonexistent")

    assert "error" in status


@pytest.mark.asyncio
async def test_list_empty_xapps(manager):
    """Test listing when no xApps deployed"""
    xapps = manager.list_xapps()

    assert len(xapps) == 0
    assert isinstance(xapps, list)
