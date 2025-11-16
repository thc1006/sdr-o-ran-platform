"""
Unit tests for SDL Client
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from xapp_sdk.sdl_client import SDLClient


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    with patch('xapp_sdk.sdl_client.redis.Redis') as mock:
        redis_instance = Mock()
        mock.return_value = redis_instance
        yield redis_instance


@pytest.fixture
def sdl_client(mock_redis):
    """Create SDL client with mocked Redis"""
    return SDLClient(host="localhost", port=6379, namespace="test")


def test_sdl_client_initialization(mock_redis):
    """Test SDL client initialization"""
    client = SDLClient(host="test-host", port=1234, namespace="custom")
    assert client.namespace == "custom"


def test_sdl_key_namespacing(sdl_client):
    """Test key namespacing"""
    key = sdl_client._key("mykey")
    assert key == "test:mykey"


def test_sdl_set(sdl_client, mock_redis):
    """Test setting data in SDL"""
    mock_redis.set.return_value = True

    result = sdl_client.set("key1", {"value": 42})

    assert result is True
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args[0]
    assert call_args[0] == "test:key1"


def test_sdl_get(sdl_client, mock_redis):
    """Test getting data from SDL"""
    import json
    test_data = {"value": 42}
    mock_redis.get.return_value = json.dumps(test_data)

    result = sdl_client.get("key1")

    assert result == test_data
    mock_redis.get.assert_called_once_with("test:key1")


def test_sdl_get_nonexistent(sdl_client, mock_redis):
    """Test getting nonexistent key"""
    mock_redis.get.return_value = None

    result = sdl_client.get("nonexistent")

    assert result is None


def test_sdl_delete(sdl_client, mock_redis):
    """Test deleting data from SDL"""
    mock_redis.delete.return_value = 1

    result = sdl_client.delete("key1")

    assert result is True
    mock_redis.delete.assert_called_once_with("test:key1")


def test_sdl_list_keys(sdl_client, mock_redis):
    """Test listing keys"""
    mock_redis.keys.return_value = ["test:key1", "test:key2", "test:key3"]

    result = sdl_client.list_keys("*")

    assert result == ["key1", "key2", "key3"]
    mock_redis.keys.assert_called_once_with("test:*")


def test_sdl_set_error_handling(sdl_client, mock_redis):
    """Test error handling in set operation"""
    mock_redis.set.side_effect = Exception("Connection error")

    result = sdl_client.set("key1", {"value": 42})

    assert result is False


def test_sdl_get_error_handling(sdl_client, mock_redis):
    """Test error handling in get operation"""
    mock_redis.get.side_effect = Exception("Connection error")

    result = sdl_client.get("key1")

    assert result is None
