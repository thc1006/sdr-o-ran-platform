# NTN-O-RAN Helm Chart

This Helm chart deploys the complete NTN-O-RAN platform on Kubernetes.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PV provisioner support in the underlying infrastructure
- Ingress controller (nginx recommended)

## Installation

### Quick Start

```bash
# Add the repository (if published)
helm repo add ntn-oran https://charts.ntn-oran.local
helm repo update

# Install the chart
helm install ntn-oran ntn-oran/ntn-oran -n ntn-oran --create-namespace
```

### Local Installation

```bash
# Create namespace
kubectl create namespace ntn-oran

# Install from local directory
helm install ntn-oran ./k8s/helm/ntn-oran -n ntn-oran

# Or with custom values
helm install ntn-oran ./k8s/helm/ntn-oran -n ntn-oran -f custom-values.yaml
```

## Configuration

The following table lists the configurable parameters of the NTN-O-RAN chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Kubernetes namespace | `ntn-oran` |
| `global.environment` | Environment (production/staging/dev) | `production` |
| `e2Termination.enabled` | Enable E2 Termination service | `true` |
| `e2Termination.replicas` | Number of E2 Termination replicas | `2` |
| `e2Termination.autoscaling.enabled` | Enable autoscaling for E2 Termination | `true` |
| `monitoring.prometheus.enabled` | Enable Prometheus | `true` |
| `monitoring.grafana.enabled` | Enable Grafana | `true` |
| `logging.elasticsearch.enabled` | Enable Elasticsearch | `true` |

## Upgrading

```bash
# Upgrade the release
helm upgrade ntn-oran ./k8s/helm/ntn-oran -n ntn-oran

# Upgrade with new values
helm upgrade ntn-oran ./k8s/helm/ntn-oran -n ntn-oran -f new-values.yaml
```

## Uninstallation

```bash
# Uninstall the release
helm uninstall ntn-oran -n ntn-oran

# Delete the namespace
kubectl delete namespace ntn-oran
```

## Custom Values Example

```yaml
# custom-values.yaml
global:
  environment: staging

e2Termination:
  replicas: 3
  resources:
    limits:
      cpu: 3000m
      memory: 6Gi

monitoring:
  grafana:
    adminPassword: "secure-password"
```

## Monitoring

After installation, you can access:

- **Grafana**: http://grafana.ntn-oran.local (default: admin/changeme)
- **Prometheus**: http://prometheus.ntn-oran.local
- **Kibana**: http://kibana.ntn-oran.local

## Troubleshooting

```bash
# Check pod status
kubectl get pods -n ntn-oran

# Check logs
kubectl logs -n ntn-oran deployment/e2-termination

# Check helm release status
helm status ntn-oran -n ntn-oran

# Get all resources
kubectl get all -n ntn-oran
```

## Support

For issues and questions, please open an issue on GitHub.
