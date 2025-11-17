# NTN-O-RAN Kubernetes Deployment Guide

This directory contains production-ready Kubernetes manifests and Helm charts for deploying the NTN-O-RAN platform.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Deployment Methods](#deployment-methods)
5. [Configuration](#configuration)
6. [Monitoring & Logging](#monitoring--logging)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

The NTN-O-RAN platform consists of the following components:

### Core Services
- **E2 Termination**: O-RAN E2 interface endpoint (2 replicas, HA)
- **Handover xApp**: Satellite handover prediction and control (2 replicas)
- **Power xApp**: Power optimization and control (2 replicas)
- **Weather Service**: Weather data integration (1 replica)
- **Orbit Service**: Satellite orbit propagation (1 replica)
- **Redis**: State management and caching (1 replica)

### Monitoring Stack
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards (4 dashboards included)

### Logging Stack (ELK)
- **Elasticsearch**: Log storage and search
- **Logstash**: Log processing and transformation
- **Kibana**: Log visualization
- **Filebeat**: Log collection from all pods

## Prerequisites

### Required
- Kubernetes cluster 1.24+ (minikube, kind, GKE, EKS, AKS)
- kubectl CLI tool installed
- Minimum cluster resources:
  - 8 CPUs
  - 16GB RAM
  - 100GB storage

### Optional
- Helm 3.8+ (recommended for easy deployment)
- Ingress controller (nginx recommended)
- cert-manager (for TLS certificates)
- Persistent volume provisioner

## Quick Start

### Method 1: Using kubectl (Manual)

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply ConfigMaps
kubectl apply -f k8s/configmap.yaml

# 3. Create secrets (edit secrets.yaml first!)
cp k8s/secrets.yaml.template k8s/secrets.yaml
# Edit secrets.yaml and add your actual secrets
kubectl apply -f k8s/secrets.yaml

# 4. Deploy core services
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/

# 5. Deploy monitoring
kubectl apply -f k8s/monitoring/prometheus/
kubectl apply -f k8s/monitoring/grafana/

# 6. Deploy logging (optional)
kubectl apply -f k8s/logging/elasticsearch/
kubectl apply -f k8s/logging/logstash/
kubectl apply -f k8s/logging/kibana/
kubectl apply -f k8s/logging/filebeat/

# 7. Apply ingress, HPA, and PDB
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml

# 8. Verify deployment
kubectl get pods -n ntn-oran
kubectl get services -n ntn-oran
```

### Method 2: Using Helm (Recommended)

```bash
# 1. Install the chart
helm install ntn-oran ./k8s/helm/ntn-oran -n ntn-oran --create-namespace

# 2. Verify deployment
helm status ntn-oran -n ntn-oran
kubectl get pods -n ntn-oran

# 3. Access services
# See "Accessing Services" section below
```

## Deployment Methods

### Local Development (minikube)

```bash
# Start minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --disk-size=50g

# Enable addons
minikube addons enable ingress
minikube addons enable metrics-server

# Deploy
helm install ntn-oran ./k8s/helm/ntn-oran -n ntn-oran --create-namespace

# Access services
minikube service grafana-service -n ntn-oran
minikube service prometheus-service -n ntn-oran
```

### Production Deployment (Cloud)

```bash
# Set up kubectl context for your cluster
kubectl config use-context production-cluster

# Create namespace
kubectl create namespace ntn-oran

# Apply secrets (ensure secrets are properly configured)
kubectl apply -f k8s/secrets.yaml

# Deploy using Helm with production values
helm install ntn-oran ./k8s/helm/ntn-oran \
  -n ntn-oran \
  -f production-values.yaml \
  --wait --timeout 15m

# Verify
kubectl get all -n ntn-oran
```

## Configuration

### Environment Variables

All configuration is managed through ConfigMaps. Edit `k8s/configmap.yaml` to customize:

```yaml
# Key configuration parameters
LOG_LEVEL: "INFO"                    # DEBUG, INFO, WARNING, ERROR
TARGET_LATENCY_MS: "5.5"             # Target E2E latency
TARGET_THROUGHPUT_MPS: "600"          # Target message throughput
MAX_SATELLITES: "8805"                # Starlink constellation size
```

### Resource Allocation

Edit resource requests/limits in deployment manifests or Helm values:

```yaml
# In k8s/helm/ntn-oran/values.yaml
e2Termination:
  resources:
    requests:
      cpu: 1000m      # 1 CPU
      memory: 2Gi     # 2GB RAM
    limits:
      cpu: 2000m      # 2 CPUs max
      memory: 4Gi     # 4GB RAM max
```

### Autoscaling

HPA (Horizontal Pod Autoscaler) is configured for:
- E2 Termination: 2-5 replicas (CPU: 70%, Memory: 80%)
- Handover xApp: 1-5 replicas (CPU: 70%)
- Power xApp: 1-5 replicas (CPU: 70%)
- Orbit Service: 1-3 replicas (CPU: 75%)

## Monitoring & Logging

### Accessing Grafana

```bash
# Port-forward method
kubectl port-forward -n ntn-oran svc/grafana-service 3000:3000

# Access at: http://localhost:3000
# Default credentials: admin / changeme (set in secrets)
```

### Pre-configured Dashboards

1. **NTN-O-RAN Overview** - System health, latency, throughput
2. **E2 Interface Metrics** - E2 message rates, ASN.1 encoding, errors
3. **Satellite Tracking** - Elevation angles, Doppler shift, handovers
4. **xApp Performance** - Prediction accuracy, decision latency, power optimization

### Accessing Prometheus

```bash
kubectl port-forward -n ntn-oran svc/prometheus-service 9090:9090
# Access at: http://localhost:9090
```

### Accessing Kibana (Logs)

```bash
kubectl port-forward -n ntn-oran svc/kibana 5601:5601
# Access at: http://localhost:5601
```

### Log Queries

Example Kibana queries:
- All E2 errors: `kubernetes.namespace:"ntn-oran" AND app:"e2-termination" AND log_level:"ERROR"`
- Handover events: `kubernetes.namespace:"ntn-oran" AND message:"handover"`
- High latency: `kubernetes.namespace:"ntn-oran" AND latency_ms > 10`

## Maintenance

### Updating Deployments

```bash
# Update a specific deployment
kubectl set image deployment/e2-termination \
  e2-termination=ntn/e2-termination:v2.0 \
  -n ntn-oran

# Rollout status
kubectl rollout status deployment/e2-termination -n ntn-oran

# Rollback if needed
kubectl rollout undo deployment/e2-termination -n ntn-oran
```

### Scaling Services

```bash
# Manual scaling
kubectl scale deployment/handover-xapp --replicas=3 -n ntn-oran

# HPA handles automatic scaling based on CPU/memory
kubectl get hpa -n ntn-oran
```

### Backup and Restore

```bash
# Backup persistent data
kubectl get pvc -n ntn-oran
# Use your cloud provider's volume snapshot feature

# Backup configuration
kubectl get configmap -n ntn-oran -o yaml > backup-configmap.yaml
kubectl get secret -n ntn-oran -o yaml > backup-secrets.yaml
```

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n ntn-oran
kubectl logs <pod-name> -n ntn-oran
```

**Service not accessible:**
```bash
kubectl get svc -n ntn-oran
kubectl get endpoints -n ntn-oran
```

**High latency:**
```bash
# Check Prometheus metrics
# View "NTN-O-RAN Overview" dashboard in Grafana
# Increase replicas if CPU is high
```

**Out of memory:**
```bash
# Check resource usage
kubectl top pods -n ntn-oran

# Increase memory limits in deployment
kubectl edit deployment/e2-termination -n ntn-oran
```

## Next Steps

- [Monitoring Guide](./MONITORING_GUIDE.md) - Detailed monitoring setup
- [Scaling Guide](./SCALING_GUIDE.md) - Production scaling strategies
- [Security Guide](./SECURITY_GUIDE.md) - Security best practices
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md) - Pre-deployment checklist

## Support

For issues and questions:
- Open a GitHub issue
- Check the troubleshooting guide
- Review Grafana dashboards for performance insights
