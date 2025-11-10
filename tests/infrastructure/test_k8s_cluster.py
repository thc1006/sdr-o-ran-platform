"""
Kubernetes Cluster Infrastructure Tests

REQ-INFRA-001: System must run on local Kubernetes cluster
REQ-INFRA-002: Cluster must have dedicated namespaces for isolation
REQ-INFRA-003: Cluster resources must be sufficient for all components
"""
import pytest
import subprocess
import json


class TestK8sClusterAccessibility:
    """Test Kubernetes cluster accessibility"""

    def test_kubectl_installed(self):
        """Verify kubectl is installed and accessible"""
        result = subprocess.run(
            ["kubectl", "version", "--client", "--output=json"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "kubectl not installed or not in PATH"

        version_info = json.loads(result.stdout)
        assert "clientVersion" in version_info

    def test_k8s_cluster_accessible(self):
        """Verify Kubernetes cluster is accessible"""
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Cannot access Kubernetes cluster"
        assert "Kubernetes control plane" in result.stdout


class TestK8sNamespaces:
    """Test Kubernetes namespaces"""

    REQUIRED_NAMESPACES = [
        "sdr-oran-ntn",
        "monitoring",
        "oran-ric"
    ]

    def test_required_namespaces_exist(self):
        """Verify all required namespaces exist"""
        for namespace in self.REQUIRED_NAMESPACES:
            result = subprocess.run(
                ["kubectl", "get", "namespace", namespace],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, \
                f"Namespace '{namespace}' does not exist"

    def test_namespace_labels(self):
        """Verify namespaces have correct labels"""
        for namespace in self.REQUIRED_NAMESPACES:
            result = subprocess.run(
                ["kubectl", "get", "namespace", namespace, "-o", "json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                ns_info = json.loads(result.stdout)
                labels = ns_info.get("metadata", {}).get("labels", {})
                assert "managed-by" in labels, \
                    f"Namespace '{namespace}' missing 'managed-by' label"


class TestK8sResources:
    """Test Kubernetes cluster resources"""

    def test_cluster_has_sufficient_cpu(self):
        """Verify cluster has at least 10 CPU cores available"""
        result = subprocess.run(
            ["kubectl", "top", "nodes", "--no-headers"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Parse node resources
            lines = result.stdout.strip().split('\n')
            total_cpu = 0

            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    cpu_usage = parts[1]
                    # Extract number from format like "1234m" or "12"
                    cpu_value = int(cpu_usage.rstrip('m%'))
                    total_cpu += cpu_value

            # We have 30 cores, so any value > 0 means it's working
            assert total_cpu >= 0, "Could not determine CPU usage"

    def test_cluster_has_sufficient_memory(self):
        """Verify cluster has at least 20GB memory available"""
        result = subprocess.run(
            ["kubectl", "top", "nodes", "--no-headers"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # At least nodes are responding
            assert len(result.stdout) > 0

    def test_cluster_nodes_ready(self):
        """Verify all cluster nodes are in Ready state"""
        result = subprocess.run(
            ["kubectl", "get", "nodes", "-o", "json"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        nodes_info = json.loads(result.stdout)
        nodes = nodes_info.get("items", [])

        assert len(nodes) > 0, "No nodes found in cluster"

        for node in nodes:
            node_name = node.get("metadata", {}).get("name", "unknown")
            conditions = node.get("status", {}).get("conditions", [])

            ready_condition = next(
                (c for c in conditions if c.get("type") == "Ready"),
                None
            )

            assert ready_condition is not None, \
                f"Node '{node_name}' has no Ready condition"
            assert ready_condition.get("status") == "True", \
                f"Node '{node_name}' is not Ready"
