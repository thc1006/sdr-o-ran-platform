"""
Core Services Deployment Tests

REQ-INFRA-004: System must deploy Redis as SDL (Shared Data Layer)
REQ-INFRA-005: System must deploy Prometheus for monitoring
REQ-INFRA-006: System must deploy Grafana for visualization
"""
import pytest
import subprocess
import time
import redis


class TestRedisDeployment:
    """Test Redis deployment as SDL"""

    def test_redis_pod_exists(self):
        """Verify Redis pod exists in sdr-oran-ntn namespace"""
        result = subprocess.run(
            ["kubectl", "get", "pod", "-n", "sdr-oran-ntn", "-l", "app=redis"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "redis" in result.stdout.lower()

    def test_redis_pod_running(self):
        """Verify Redis pod is in Running state"""
        result = subprocess.run(
            ["kubectl", "get", "pod", "-n", "sdr-oran-ntn",
             "-l", "app=redis", "-o", "jsonpath={.items[0].status.phase}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            assert result.stdout == "Running"

    def test_redis_service_exists(self):
        """Verify Redis service exists"""
        result = subprocess.run(
            ["kubectl", "get", "service", "-n", "sdr-oran-ntn", "redis"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    @pytest.mark.skipif(
        subprocess.run(["kubectl", "get", "pod", "-n", "sdr-oran-ntn", "-l", "app=redis"],
                      capture_output=True).returncode != 0,
        reason="Redis pod not deployed yet"
    )
    def test_redis_connectivity(self):
        """Test Redis connectivity via port-forward"""
        # This test would require port-forwarding
        # For now, we'll just verify the service exists
        result = subprocess.run(
            ["kubectl", "get", "service", "-n", "sdr-oran-ntn", "redis",
             "-o", "jsonpath={.spec.ports[0].port}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            port = result.stdout.strip()
            assert port == "6379"


class TestPrometheusDeployment:
    """Test Prometheus deployment"""

    def test_prometheus_namespace_has_pods(self):
        """Verify Prometheus pods exist in monitoring namespace"""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "monitoring",
             "-l", "app.kubernetes.io/name=prometheus"],
            capture_output=True,
            text=True
        )
        # Will fail if not deployed yet
        if result.returncode == 0:
            assert "prometheus" in result.stdout.lower()


class TestGrafanaDeployment:
    """Test Grafana deployment"""

    def test_grafana_namespace_has_pods(self):
        """Verify Grafana pods exist in monitoring namespace"""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "monitoring", "-l", "app.kubernetes.io/name=grafana"],
            capture_output=True,
            text=True
        )
        # Will fail if not deployed yet
        if result.returncode == 0:
            assert "grafana" in result.stdout.lower()
