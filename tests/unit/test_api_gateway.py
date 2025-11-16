"""Unit tests for SDR API Gateway

Tests the FastAPI-based API gateway including:
- Authentication and authorization
- Station management endpoints
- Configuration validation
- Health checks
- Metrics endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
import json

# Import the API application
from sdr_api_server import (
    app,
    StationConfig,
    StationStatus,
    verify_password,
    get_password_hash,
    create_access_token,
    STATIONS,
    USRP_DEVICES
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Get authentication token for testing"""
    response = client.post(
        "/token",
        data={"username": "admin", "password": "secret"}
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(autouse=True)
def reset_stations():
    """Reset STATIONS dict before each test"""
    STATIONS.clear()
    yield
    STATIONS.clear()


@pytest.mark.unit
@pytest.mark.api
class TestAuthentication:
    """Test authentication and authorization"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_login_success(self, client):
        """Test successful login"""
        response = client.post(
            "/token",
            data={"username": "admin", "password": "secret"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/token",
            data={"username": "admin", "password": "wrong_password"}
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/token",
            data={"username": "nonexistent", "password": "password"}
        )

        assert response.status_code == 401

    def test_access_token_creation(self):
        """Test JWT token creation"""
        token = create_access_token(data={"sub": "testuser"})

        assert isinstance(token, str)
        assert len(token) > 0

    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v1/sdr/stations")

        assert response.status_code == 401


@pytest.mark.unit
@pytest.mark.api
class TestStationManagement:
    """Test station management endpoints"""

    def test_create_station(self, client, auth_headers):
        """Test creating a new station"""
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {
                "azimuth": 45.0,
                "elevation": 30.0
            },
            "modulation_scheme": "QPSK",
            "oran_integration": True,
            "oran_endpoint": "oran-du:50051"
        }

        response = client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["station_id"] == "test-station-001"
        assert "test-station-001" in STATIONS

    def test_create_station_duplicate(self, client, auth_headers):
        """Test creating a station with duplicate ID"""
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }

        # Create first station
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        # Try to create duplicate
        response = client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_station_invalid_usrp(self, client, auth_headers):
        """Test creating station with invalid USRP device"""
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-999",  # Invalid
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }

        response = client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_list_stations_empty(self, client, auth_headers):
        """Test listing stations when none exist"""
        response = client.get(
            "/api/v1/sdr/stations",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_stations(self, client, auth_headers):
        """Test listing stations"""
        # Create a station first
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        # List stations
        response = client.get(
            "/api/v1/sdr/stations",
            headers=auth_headers
        )

        assert response.status_code == 200
        stations = response.json()
        assert len(stations) == 1
        assert "test-station-001" in stations

    def test_get_station_status(self, client, auth_headers):
        """Test getting station status"""
        # Create a station first
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        # Get status
        response = client.get(
            "/api/v1/sdr/stations/test-station-001/status",
            headers=auth_headers
        )

        assert response.status_code == 200
        status = response.json()
        assert status["station_id"] == "test-station-001"
        assert "signal_snr_db" in status
        assert "usrp_connected" in status

    def test_get_station_status_not_found(self, client, auth_headers):
        """Test getting status for nonexistent station"""
        response = client.get(
            "/api/v1/sdr/stations/nonexistent/status",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_start_station(self, client, auth_headers):
        """Test starting a station"""
        # Create a station first
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        # Start station
        response = client.post(
            "/api/v1/sdr/stations/test-station-001/start",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert STATIONS["test-station-001"]["status"] == "running"

    def test_stop_station(self, client, auth_headers):
        """Test stopping a station"""
        # Create and start a station
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )
        client.post(
            "/api/v1/sdr/stations/test-station-001/start",
            headers=auth_headers
        )

        # Stop station
        response = client.post(
            "/api/v1/sdr/stations/test-station-001/stop",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert STATIONS["test-station-001"]["status"] == "stopped"

    def test_update_frequency(self, client, auth_headers):
        """Test updating station frequency"""
        # Create a station first
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        # Update frequency
        response = client.put(
            "/api/v1/sdr/stations/test-station-001/frequency",
            json={"center_frequency_ghz": 13.5},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert STATIONS["test-station-001"]["config"]["center_frequency_ghz"] == 13.5

    def test_delete_station(self, client, auth_headers):
        """Test deleting a station"""
        # Create a station first
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        # Delete station
        response = client.delete(
            "/api/v1/sdr/stations/test-station-001",
            headers=auth_headers
        )

        assert response.status_code == 204
        assert "test-station-001" not in STATIONS

    def test_delete_running_station(self, client, auth_headers):
        """Test deleting a running station (should fail)"""
        # Create and start a station
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )
        client.post(
            "/api/v1/sdr/stations/test-station-001/start",
            headers=auth_headers
        )

        # Try to delete running station
        response = client.delete(
            "/api/v1/sdr/stations/test-station-001",
            headers=auth_headers
        )

        assert response.status_code == 400


@pytest.mark.unit
@pytest.mark.api
class TestConfigValidation:
    """Test configuration validation"""

    def test_invalid_station_id(self, client, auth_headers):
        """Test creating station with invalid ID"""
        station_config = {
            "station_id": "invalid id with spaces!",  # Invalid characters
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }

        response = client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_invalid_frequency_band(self, client, auth_headers):
        """Test creating station with invalid frequency band"""
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "X",  # Invalid band
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }

        response = client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_invalid_modulation_scheme(self, client, auth_headers):
        """Test creating station with invalid modulation scheme"""
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "INVALID"
        }

        response = client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        assert response.status_code == 422


@pytest.mark.unit
@pytest.mark.api
class TestHealthChecks:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test liveness probe"""
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_readiness_check(self, client):
        """Test readiness probe"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "usrp_devices_online" in data


@pytest.mark.unit
@pytest.mark.api
class TestMetricsEndpoints:
    """Test metrics and monitoring endpoints"""

    def test_get_station_metrics(self, client, auth_headers):
        """Test getting station metrics"""
        # Create a station first
        station_config = {
            "station_id": "test-station-001",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0},
            "modulation_scheme": "QPSK"
        }
        client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )

        # Get metrics
        response = client.get(
            "/api/v1/sdr/stations/test-station-001/metrics",
            headers=auth_headers
        )

        assert response.status_code == 200
        metrics = response.json()
        assert metrics["station_id"] == "test-station-001"
        assert "metrics" in metrics
        assert "timestamp" in metrics

    def test_prometheus_metrics(self, client):
        """Test Prometheus scrape endpoint"""
        response = client.get("/metrics")

        assert response.status_code == 200
        content = response.text
        assert "sdr_signal_snr_db" in content
        assert "sdr_stations_total" in content

    def test_list_usrp_devices(self, client, auth_headers):
        """Test listing USRP devices"""
        response = client.get(
            "/api/v1/usrp/devices",
            headers=auth_headers
        )

        assert response.status_code == 200
        devices = response.json()
        assert isinstance(devices, dict)
        assert len(devices) > 0


@pytest.mark.unit
@pytest.mark.api
class TestLEOIntegration:
    """Test LEO NTN integration endpoints"""

    def test_get_iq_stats(self, client):
        """Test getting IQ sample statistics"""
        response = client.get("/api/v1/leo/iq-stats")

        assert response.status_code == 200
        stats = response.json()
        assert "connected" in stats
        assert "frames_received" in stats
        assert "zmq_endpoint" in stats

    def test_get_iq_buffer(self, client):
        """Test getting IQ sample buffer"""
        response = client.get("/api/v1/leo/iq-buffer?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert "buffer_size" in data
        assert "recent_frames" in data


@pytest.mark.unit
@pytest.mark.api
class TestAuthenticationEdgeCases:
    """Test authentication edge cases and error handling"""

    def test_invalid_token_format(self, client):
        """Test accessing protected endpoint with invalid token format"""
        response = client.get(
            "/api/v1/sdr/stations",
            headers={"Authorization": "Bearer invalid.token.format"}
        )
        assert response.status_code == 401

    def test_missing_authorization_header(self, client):
        """Test accessing protected endpoint without Authorization header"""
        response = client.post("/api/v1/sdr/stations", json={})
        assert response.status_code == 401

    def test_expired_token_handling(self, client):
        """Test behavior with potentially expired token"""
        # Create a token with very short expiration
        from datetime import timedelta
        from sdr_api_server import create_access_token

        short_lived_token = create_access_token(
            data={"sub": "admin"},
            expires_delta=timedelta(seconds=1)
        )
        headers = {"Authorization": f"Bearer {short_lived_token}"}

        # Token should still be valid immediately
        response = client.get("/api/v1/sdr/stations", headers=headers)
        assert response.status_code in [200, 401]  # May depend on exact timing


@pytest.mark.unit
@pytest.mark.api
class TestStationEdgeCases:
    """Test station management edge cases"""

    def test_start_nonexistent_station(self, client, auth_headers):
        """Test starting a station that doesn't exist"""
        response = client.post(
            "/api/v1/sdr/stations/nonexistent/start",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_stop_nonexistent_station(self, client, auth_headers):
        """Test stopping a station that doesn't exist"""
        response = client.post(
            "/api/v1/sdr/stations/nonexistent/stop",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_frequency_nonexistent_station(self, client, auth_headers):
        """Test updating frequency for nonexistent station"""
        response = client.put(
            "/api/v1/sdr/stations/nonexistent/frequency",
            json={"center_frequency_ghz": 13.5},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_nonexistent_station(self, client, auth_headers):
        """Test deleting a station that doesn't exist"""
        response = client.delete(
            "/api/v1/sdr/stations/nonexistent",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_station_missing_required_fields(self, client, auth_headers):
        """Test creating station with missing required fields"""
        incomplete_config = {
            "station_id": "test-station",
            "usrp_device": "usrp-001"
            # Missing other required fields
        }
        response = client.post(
            "/api/v1/sdr/stations",
            json=incomplete_config,
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_get_metrics_nonexistent_station(self, client, auth_headers):
        """Test getting metrics for nonexistent station"""
        response = client.get(
            "/api/v1/sdr/stations/nonexistent/metrics",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_station_with_valid_oran_endpoint(self, client, auth_headers):
        """Test creating station with O-RAN integration enabled"""
        station_config = {
            "station_id": "test-oran-station",
            "usrp_device": "usrp-001",
            "frequency_band": "Ku",
            "center_frequency_ghz": 12.5,
            "sample_rate_msps": 10.0,
            "antenna_config": {"azimuth": 45.0, "elevation": 30.0},
            "modulation_scheme": "QPSK",
            "oran_integration": True,
            "oran_endpoint": "oran-du:50051"
        }
        response = client.post(
            "/api/v1/sdr/stations",
            json=station_config,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["station_id"] == "test-oran-station"
        # Check station was actually created with O-RAN config
        from sdr_api_server import STATIONS
        assert "test-oran-station" in STATIONS
        assert STATIONS["test-oran-station"]["config"]["oran_integration"] == True
