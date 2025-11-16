"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add implementation directories to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03-Implementation" / "integration" / "sdr-oran-connector"))
sys.path.insert(0, str(PROJECT_ROOT / "03-Implementation" / "ai-ml-pipeline" / "training"))
sys.path.insert(0, str(PROJECT_ROOT / "03-Implementation" / "sdr-platform" / "api-gateway"))
sys.path.insert(0, str(PROJECT_ROOT / "03-Implementation"))


@pytest.fixture(scope="session")
def project_root():
    """Provide project root directory"""
    return PROJECT_ROOT


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock(return_value=True)
    redis_mock.delete = Mock(return_value=1)
    redis_mock.exists = Mock(return_value=False)
    return redis_mock


@pytest.fixture
def mock_grpc_context():
    """Mock gRPC context for testing"""
    context = Mock()
    context.is_active = Mock(return_value=True)
    context.set_code = Mock()
    context.set_details = Mock()
    return context


@pytest.fixture
def sample_ric_state():
    """Provide a sample RIC state for testing"""
    return {
        "ue_throughput_dl_mbps": 75.5,
        "ue_throughput_ul_mbps": 35.2,
        "ue_buffer_status_dl_kb": 250.0,
        "ue_buffer_status_ul_kb": 100.0,
        "prb_utilization_dl_percent": 65.0,
        "prb_utilization_ul_percent": 45.0,
        "active_ues": 5,
        "cqi_dl": 12.0,
        "rsrp_dbm": -85.0,
        "rsrq_db": -8.5,
        "sinr_db": 18.5,
        "e2e_latency_ms": 65.0,
        "rlc_latency_ms": 8.0,
        "mac_latency_ms": 4.5,
        "bler_dl": 0.005,
        "bler_ul": 0.008,
        "timestamp_ns": 1700000000000000000
    }
