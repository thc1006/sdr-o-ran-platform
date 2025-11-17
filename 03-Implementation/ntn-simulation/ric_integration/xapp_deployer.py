"""
xApp Deployment Manager for O-RAN SC Near-RT RIC
Handles packaging, deployment, and lifecycle management of NTN xApps

Features:
- xApp descriptor generation
- Docker image building and packaging
- Deployment via RIC AppMgr REST API
- Health monitoring and status checking
- Kubernetes integration
"""

import json
import os
import subprocess
import requests
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import tarfile
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class XAppConfig:
    """xApp Configuration"""
    name: str
    version: str
    namespace: str = "ricxapp"
    image_name: str = ""
    image_tag: str = "latest"
    replicas: int = 1
    ric_platform_namespace: str = "ricplt"
    messaging_service: str = "ricplt-e2mgr-rmr"
    rtmgr_service: str = "ricplt-rtmgr"
    a1mediator_service: str = "ricplt-a1mediator"
    config_map: Optional[Dict[str, Any]] = None
    resource_limits: Optional[Dict[str, str]] = None


@dataclass
class XAppDescriptor:
    """xApp Descriptor (config-file.json)"""
    xapp_name: str
    version: str
    containers: List[Dict[str, Any]]
    messaging: Dict[str, Any]
    rmr: Dict[str, Any]
    config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class XAppDeployer:
    """
    xApp Deployment Manager

    Handles deployment of NTN xApps to O-RAN SC Near-RT RIC platform.
    Supports both local development deployment and production Kubernetes deployment.
    """

    def __init__(
        self,
        appmgr_url: str = "http://localhost:8080",
        docker_registry: str = "localhost:5000",
        use_kubernetes: bool = True
    ):
        """
        Initialize xApp Deployer

        Args:
            appmgr_url: RIC AppMgr REST API URL
            docker_registry: Docker registry for xApp images
            use_kubernetes: Whether to use Kubernetes for deployment
        """
        self.appmgr_url = appmgr_url
        self.docker_registry = docker_registry
        self.use_kubernetes = use_kubernetes

        logger.info(f"XAppDeployer initialized: appmgr={appmgr_url}, registry={docker_registry}")

    def create_xapp_descriptor(
        self,
        config: XAppConfig,
        xapp_code_path: str
    ) -> XAppDescriptor:
        """
        Create xApp descriptor (config-file.json)

        Args:
            config: xApp configuration
            xapp_code_path: Path to xApp Python code

        Returns:
            XAppDescriptor instance
        """
        # Default resource limits if not specified
        resource_limits = config.resource_limits or {
            "cpu": "100m",
            "memory": "128Mi"
        }

        # Container definition
        containers = [
            {
                "name": config.name,
                "image": {
                    "registry": self.docker_registry,
                    "name": config.image_name or config.name,
                    "tag": config.image_tag
                },
                "command": ["python3", "-u", "/app/main.py"],
                "resources": {
                    "limits": resource_limits,
                    "requests": resource_limits
                }
            }
        ]

        # RMR (RIC Message Router) configuration
        rmr_config = {
            "protPort": "tcp:4560",
            "maxSize": 65536,
            "numWorkers": 1,
            "txMessages": [
                "RIC_SUB_REQ",
                "RIC_SUB_DEL_REQ"
            ],
            "rxMessages": [
                "RIC_SUB_RESP",
                "RIC_SUB_DEL_RESP",
                "RIC_INDICATION"
            ],
            "policies": []
        }

        # Messaging configuration
        messaging_config = {
            "ports": [
                {
                    "name": "rmr-data",
                    "container": "tcp:4560",
                    "port": 4560,
                    "protocol": "tcp"
                },
                {
                    "name": "rmr-route",
                    "container": "tcp:4561",
                    "port": 4561,
                    "protocol": "tcp"
                }
            ]
        }

        # xApp-specific configuration
        xapp_config = config.config_map or {
            "name": config.name,
            "version": config.version,
            "description": f"NTN {config.name} xApp",
            "config": {}
        }

        descriptor = XAppDescriptor(
            xapp_name=config.name,
            version=config.version,
            containers=containers,
            messaging=messaging_config,
            rmr=rmr_config,
            config=xapp_config
        )

        logger.info(f"Created xApp descriptor for {config.name} v{config.version}")
        return descriptor

    def create_dockerfile(
        self,
        xapp_name: str,
        xapp_code_path: str,
        output_dir: str
    ) -> str:
        """
        Create Dockerfile for xApp

        Args:
            xapp_name: xApp name
            xapp_code_path: Path to xApp Python code
            output_dir: Output directory for Dockerfile

        Returns:
            Path to created Dockerfile
        """
        dockerfile_content = f"""# NTN xApp Dockerfile
FROM python:3.9-slim

# Install dependencies
RUN pip install --no-cache-dir \\
    asyncio \\
    aiohttp \\
    numpy \\
    requests

# Install RMR library (RIC Message Router)
# In production, would install from O-RAN SC repository
# RUN apt-get update && apt-get install -y rmr-dev

# Create app directory
WORKDIR /app

# Copy xApp code
COPY {os.path.basename(xapp_code_path)} /app/main.py
COPY ../e2_ntn_extension /app/e2_ntn_extension

# Set Python path
ENV PYTHONPATH=/app

# Run xApp
CMD ["python3", "-u", "/app/main.py"]
"""

        dockerfile_path = os.path.join(output_dir, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        logger.info(f"Created Dockerfile at {dockerfile_path}")
        return dockerfile_path

    def build_docker_image(
        self,
        config: XAppConfig,
        xapp_code_path: str,
        build_context: str
    ) -> bool:
        """
        Build Docker image for xApp

        Args:
            config: xApp configuration
            xapp_code_path: Path to xApp code
            build_context: Docker build context directory

        Returns:
            True if build successful
        """
        try:
            image_name = f"{self.docker_registry}/{config.image_name or config.name}"
            image_tag = f"{image_name}:{config.image_tag}"

            logger.info(f"Building Docker image: {image_tag}")

            # Create Dockerfile
            self.create_dockerfile(config.name, xapp_code_path, build_context)

            # Build image
            build_cmd = [
                "docker", "build",
                "-t", image_tag,
                "-f", os.path.join(build_context, "Dockerfile"),
                build_context
            ]

            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                cwd=build_context
            )

            if result.returncode != 0:
                logger.error(f"Docker build failed: {result.stderr}")
                return False

            logger.info(f"Docker image built successfully: {image_tag}")

            # Push to registry if not localhost
            if self.docker_registry != "localhost":
                push_cmd = ["docker", "push", image_tag]
                push_result = subprocess.run(push_cmd, capture_output=True, text=True)

                if push_result.returncode != 0:
                    logger.error(f"Docker push failed: {push_result.stderr}")
                    return False

                logger.info(f"Docker image pushed to registry: {image_tag}")

            return True

        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            return False

    def create_kubernetes_manifest(
        self,
        config: XAppConfig,
        descriptor: XAppDescriptor,
        output_path: str
    ) -> str:
        """
        Create Kubernetes deployment manifest

        Args:
            config: xApp configuration
            descriptor: xApp descriptor
            output_path: Output path for manifest

        Returns:
            Path to created manifest
        """
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.name,
                "namespace": config.namespace,
                "labels": {
                    "app": config.name,
                    "version": config.version
                }
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": config.name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": config.name,
                            "version": config.version
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": config.name,
                                "image": f"{self.docker_registry}/{config.image_name or config.name}:{config.image_tag}",
                                "imagePullPolicy": "IfNotPresent",
                                "ports": [
                                    {
                                        "name": "rmr-data",
                                        "containerPort": 4560,
                                        "protocol": "TCP"
                                    },
                                    {
                                        "name": "rmr-route",
                                        "containerPort": 4561,
                                        "protocol": "TCP"
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "RMR_SEED_RT",
                                        "value": f"service-{config.ric_platform_namespace}-{config.rtmgr_service}.{config.ric_platform_namespace}:4561"
                                    },
                                    {
                                        "name": "RMR_RTG_SVC",
                                        "value": f"{config.rtmgr_service}.{config.ric_platform_namespace}:4561"
                                    }
                                ],
                                "resources": {
                                    "limits": config.resource_limits or {
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    },
                                    "requests": config.resource_limits or {
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }

        with open(output_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)

        logger.info(f"Created Kubernetes manifest at {output_path}")
        return output_path

    def deploy_xapp_appmgr(
        self,
        config: XAppConfig,
        descriptor: XAppDescriptor
    ) -> bool:
        """
        Deploy xApp via RIC AppMgr REST API

        Args:
            config: xApp configuration
            descriptor: xApp descriptor

        Returns:
            True if deployment successful
        """
        try:
            # Prepare deployment payload
            payload = {
                "config-file.json": json.dumps(descriptor.to_dict())
            }

            # POST to AppMgr
            url = f"{self.appmgr_url}/ric/v1/xapps"
            headers = {"Content-Type": "application/json"}

            logger.info(f"Deploying xApp {config.name} via AppMgr: {url}")

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code in [200, 201]:
                logger.info(f"xApp {config.name} deployed successfully")
                return True
            else:
                logger.error(f"AppMgr deployment failed: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to AppMgr: {e}")
            return False
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    def deploy_xapp_kubernetes(
        self,
        config: XAppConfig,
        manifest_path: str
    ) -> bool:
        """
        Deploy xApp via kubectl

        Args:
            config: xApp configuration
            manifest_path: Path to Kubernetes manifest

        Returns:
            True if deployment successful
        """
        try:
            logger.info(f"Deploying xApp {config.name} via kubectl")

            # Apply manifest
            kubectl_cmd = ["kubectl", "apply", "-f", manifest_path]
            result = subprocess.run(kubectl_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"kubectl apply failed: {result.stderr}")
                return False

            logger.info(f"xApp {config.name} deployed to Kubernetes")

            # Wait for deployment to be ready
            return self.wait_for_deployment(config.name, config.namespace, timeout=60)

        except Exception as e:
            logger.error(f"Kubernetes deployment failed: {e}")
            return False

    def wait_for_deployment(
        self,
        name: str,
        namespace: str,
        timeout: int = 60
    ) -> bool:
        """
        Wait for Kubernetes deployment to be ready

        Args:
            name: Deployment name
            namespace: Kubernetes namespace
            timeout: Timeout in seconds

        Returns:
            True if deployment ready
        """
        logger.info(f"Waiting for deployment {name} to be ready...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                cmd = [
                    "kubectl", "get", "deployment", name,
                    "-n", namespace,
                    "-o", "jsonpath={.status.readyReplicas}"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0 and result.stdout.strip():
                    ready_replicas = int(result.stdout.strip())
                    if ready_replicas > 0:
                        logger.info(f"Deployment {name} is ready ({ready_replicas} replicas)")
                        return True

                time.sleep(2)

            except Exception as e:
                logger.warning(f"Error checking deployment status: {e}")
                time.sleep(2)

        logger.error(f"Deployment {name} not ready after {timeout}s")
        return False

    def undeploy_xapp(
        self,
        xapp_name: str,
        namespace: str = "ricxapp"
    ) -> bool:
        """
        Undeploy xApp

        Args:
            xapp_name: xApp name
            namespace: Kubernetes namespace

        Returns:
            True if undeployment successful
        """
        try:
            if self.use_kubernetes:
                logger.info(f"Undeploying xApp {xapp_name} from Kubernetes")

                cmd = ["kubectl", "delete", "deployment", xapp_name, "-n", namespace]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    logger.error(f"kubectl delete failed: {result.stderr}")
                    return False

                logger.info(f"xApp {xapp_name} undeployed")
                return True

            else:
                # Undeploy via AppMgr
                url = f"{self.appmgr_url}/ric/v1/xapps/{xapp_name}"
                response = requests.delete(url, timeout=30)

                if response.status_code in [200, 204]:
                    logger.info(f"xApp {xapp_name} undeployed via AppMgr")
                    return True
                else:
                    logger.error(f"AppMgr undeploy failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Undeploy failed: {e}")
            return False

    def get_xapp_status(
        self,
        xapp_name: str,
        namespace: str = "ricxapp"
    ) -> Dict[str, Any]:
        """
        Get xApp deployment status

        Args:
            xapp_name: xApp name
            namespace: Kubernetes namespace

        Returns:
            Status dictionary
        """
        try:
            if self.use_kubernetes:
                cmd = [
                    "kubectl", "get", "deployment", xapp_name,
                    "-n", namespace,
                    "-o", "json"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    deployment = json.loads(result.stdout)
                    status = deployment.get("status", {})

                    return {
                        "name": xapp_name,
                        "namespace": namespace,
                        "replicas": status.get("replicas", 0),
                        "ready_replicas": status.get("readyReplicas", 0),
                        "available_replicas": status.get("availableReplicas", 0),
                        "conditions": status.get("conditions", []),
                        "deployed": True
                    }
                else:
                    return {
                        "name": xapp_name,
                        "deployed": False,
                        "error": "Not found"
                    }

            else:
                # Query AppMgr
                url = f"{self.appmgr_url}/ric/v1/xapps/{xapp_name}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "name": xapp_name,
                        "deployed": False,
                        "error": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"Failed to get xApp status: {e}")
            return {
                "name": xapp_name,
                "deployed": False,
                "error": str(e)
            }

    def list_deployed_xapps(self, namespace: str = "ricxapp") -> List[str]:
        """
        List all deployed xApps

        Args:
            namespace: Kubernetes namespace

        Returns:
            List of xApp names
        """
        try:
            if self.use_kubernetes:
                cmd = [
                    "kubectl", "get", "deployments",
                    "-n", namespace,
                    "-o", "jsonpath={.items[*].metadata.name}"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    return result.stdout.strip().split()
                else:
                    return []

            else:
                url = f"{self.appmgr_url}/ric/v1/xapps"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    xapps = response.json()
                    return [xapp["name"] for xapp in xapps]
                else:
                    return []

        except Exception as e:
            logger.error(f"Failed to list xApps: {e}")
            return []
