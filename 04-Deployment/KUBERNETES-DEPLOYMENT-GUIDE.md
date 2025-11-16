# Kubernetes Deployment Guide
## SDR-O-RAN Platform

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Production Ready

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Deployment](#detailed-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## Prerequisites

### Required Tools

- **Kubernetes cluster** (v1.27+)
  - Minimum 3 nodes
  - 16 GB RAM per node
  - 4 CPU cores per node
- **kubectl** (v1.27+)
- **Helm** (v3.12+) - optional but recommended
- **Docker** (v24.0+) - for building images

### Cluster Requirements

```bash
# Verify cluster version
kubectl version --short

# Check cluster nodes
kubectl get nodes

# Verify resource availability
kubectl top nodes
```

### Network Requirements

- **Ports to expose**:
  - `36421/SCTP` - E2 Interface
  - `50051/TCP` - gRPC server
  - `3000/TCP` - Grafana dashboard
  - `9090/TCP` - Prometheus (internal)
  - `6379/TCP` - Redis (internal)

---

## Quick Start

### Option 1: Using Deploy Script

```bash
# Navigate to deployment directory
cd 04-Deployment/kubernetes

# Deploy all components
./deploy-all.sh

# Monitor deployment
kubectl get pods -n sdr-oran -w
```

### Option 2: Using Helm

```bash
# Add Helm dependencies
cd 04-Deployment/helm/sdr-oran
helm dependency update

# Install the chart
helm install sdr-oran . \
  --namespace sdr-oran \
  --create-namespace

# Check status
helm status sdr-oran -n sdr-oran
```

---

## Detailed Deployment

### Step 1: Build Docker Images

```bash
cd 04-Deployment/docker

# Build all images
./build-images.sh

# (Optional) Push to registry
./build-images.sh --push --registry your-registry.io
```

### Step 2: Create Namespace

```bash
kubectl apply -f 04-Deployment/kubernetes/namespace.yaml
```

### Step 3: Deploy Redis (SDL Backend)

```bash
kubectl apply -f 04-Deployment/kubernetes/redis-cluster.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis -n sdr-oran --timeout=180s

# Verify Redis
kubectl exec -it redis-cluster-0 -n sdr-oran -- redis-cli ping
```

### Step 4: Deploy Monitoring Stack

```bash
kubectl apply -f 04-Deployment/kubernetes/monitoring-stack.yaml

# Wait for Prometheus
kubectl wait --for=condition=ready pod -l app=prometheus -n sdr-oran --timeout=180s

# Wait for Grafana
kubectl wait --for=condition=ready pod -l app=grafana -n sdr-oran --timeout=180s
```

### Step 5: Deploy E2 Interface

```bash
kubectl apply -f 04-Deployment/kubernetes/e2-interface-deployment.yaml

# Verify E2 Interface
kubectl get pods -l app=e2-interface -n sdr-oran
kubectl logs -f deployment/e2-interface -n sdr-oran
```

### Step 6: Deploy xApps

```bash
# Deploy QoS Optimizer xApp
kubectl apply -f 04-Deployment/kubernetes/xapp-qos-deployment.yaml

# Deploy Handover Manager xApp
kubectl apply -f 04-Deployment/kubernetes/xapp-handover-deployment.yaml

# Verify xApps
kubectl get pods -l component=xapp -n sdr-oran
```

### Step 7: Deploy gRPC Server

```bash
kubectl apply -f 04-Deployment/kubernetes/grpc-server-deployment.yaml

# Get LoadBalancer IP
kubectl get svc sdr-grpc-server-service -n sdr-oran
```

---

## Configuration

### E2 Interface Configuration

Edit `e2-interface-config` ConfigMap:

```bash
kubectl edit configmap e2-interface-config -n sdr-oran
```

Key parameters:
- `global_ric_id`: RIC identifier
- `health_check_interval_sec`: Node health check interval
- `subscription_timeout_sec`: Subscription timeout

### xApp Configuration

**QoS Optimizer**:
```bash
kubectl set env deployment/xapp-qos-optimizer \
  THROUGHPUT_THRESHOLD_MBPS=15.0 \
  -n sdr-oran
```

**Handover Manager**:
```bash
kubectl set env deployment/xapp-handover-manager \
  RSRP_THRESHOLD_DBM=-115 \
  -n sdr-oran
```

### Resource Limits

Adjust resources in deployment manifests:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

---

## Monitoring

### Access Grafana Dashboard

```bash
# Get Grafana LoadBalancer IP
GRAFANA_IP=$(kubectl get svc grafana-service -n sdr-oran \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Grafana URL: http://${GRAFANA_IP}:3000"
echo "Username: admin"
echo "Password: admin12345"
```

### Access Prometheus

```bash
# Port-forward Prometheus
kubectl port-forward -n sdr-oran svc/prometheus-service 9090:9090

# Open http://localhost:9090
```

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `e2_nodes_connected` | Number of connected E2 nodes | < 1 (critical) |
| `e2_setup_requests_total` | Total E2 setup requests | Rate < 0.1/s (warning) |
| `xapp_health_status` | xApp health status | 0 (critical) |
| `redis_connected_clients` | Redis connections | > 100 (warning) |
| `grpc_requests_total` | gRPC request rate | Rate > 1000/s (info) |

### View Logs

```bash
# E2 Interface logs
kubectl logs -f deployment/e2-interface -n sdr-oran

# xApp logs
kubectl logs -f deployment/xapp-qos-optimizer -n sdr-oran
kubectl logs -f deployment/xapp-handover-manager -n sdr-oran

# gRPC server logs
kubectl logs -f deployment/sdr-grpc-server -n sdr-oran

# All logs from namespace
kubectl logs -f -n sdr-oran --all-containers=true
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n sdr-oran

# Check events
kubectl get events -n sdr-oran --sort-by='.lastTimestamp'

# Check resource quotas
kubectl describe resourcequotas -n sdr-oran
```

### E2 Interface Issues

```bash
# Check E2 Interface logs
kubectl logs deployment/e2-interface -n sdr-oran | grep ERROR

# Verify SCTP connectivity
kubectl exec -it <e2-pod> -n sdr-oran -- netstat -an | grep 36421

# Test E2 health endpoint
kubectl exec -it <e2-pod> -n sdr-oran -- curl localhost:8080/health
```

### xApp Not Connecting to E2

```bash
# Check xApp logs for connection errors
kubectl logs deployment/xapp-qos-optimizer -n sdr-oran | grep "E2 Interface"

# Verify E2 service endpoint
kubectl get endpoints e2-interface-service -n sdr-oran

# Test connectivity from xApp pod
kubectl exec -it <xapp-pod> -n sdr-oran -- nc -zv e2-interface-service 36421
```

### Redis Connection Issues

```bash
# Check Redis status
kubectl exec -it redis-cluster-0 -n sdr-oran -- redis-cli info

# Test connectivity from xApp
kubectl exec -it <xapp-pod> -n sdr-oran -- nc -zv redis-service 6379

# Check Redis logs
kubectl logs statefulset/redis-cluster -n sdr-oran
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n sdr-oran

# Check node resource usage
kubectl top nodes

# Horizontal Pod Autoscaling
kubectl autoscale deployment e2-interface --cpu-percent=70 --min=3 --max=10 -n sdr-oran
```

---

## Maintenance

### Scaling Components

```bash
# Scale E2 Interface
kubectl scale deployment e2-interface --replicas=5 -n sdr-oran

# Scale xApps
kubectl scale deployment xapp-qos-optimizer --replicas=4 -n sdr-oran

# Verify scaling
kubectl get deployments -n sdr-oran
```

### Rolling Updates

```bash
# Update E2 Interface image
kubectl set image deployment/e2-interface \
  e2-interface=sdr-oran/e2-interface:1.1.0 \
  -n sdr-oran

# Check rollout status
kubectl rollout status deployment/e2-interface -n sdr-oran

# Rollback if needed
kubectl rollout undo deployment/e2-interface -n sdr-oran
```

### Backup and Restore

#### Backup Redis Data

```bash
# Create Redis backup
kubectl exec redis-cluster-0 -n sdr-oran -- redis-cli BGSAVE

# Copy backup file
kubectl cp sdr-oran/redis-cluster-0:/data/dump.rdb ./redis-backup.rdb
```

#### Backup Configuration

```bash
# Export all configurations
kubectl get configmaps,secrets -n sdr-oran -o yaml > sdr-oran-config-backup.yaml

# Export deployments
kubectl get deployments,statefulsets,services -n sdr-oran -o yaml > sdr-oran-workloads-backup.yaml
```

### Cleanup

```bash
# Delete entire namespace (WARNING: destroys all data)
kubectl delete namespace sdr-oran

# Delete specific components
kubectl delete deployment e2-interface -n sdr-oran
kubectl delete deployment xapp-qos-optimizer -n sdr-oran

# Delete PVCs (data will be lost)
kubectl delete pvc -l app=redis -n sdr-oran
```

---

## Architecture in Kubernetes

```
┌─────────────────────────────────────────────────────────────────┐
│                      sdr-oran Namespace                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            E2 Interface (3 replicas)                     │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐                          │  │
│  │  │ Pod  │  │ Pod  │  │ Pod  │                          │  │
│  │  └──────┘  └──────┘  └──────┘                          │  │
│  │         E2 Interface Service (ClusterIP)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         ↓                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             xApp Framework (2 replicas each)             │  │
│  │  ┌──────────────┐         ┌─────────────────┐           │  │
│  │  │ QoS xApp     │         │ Handover xApp   │           │  │
│  │  │ ┌──────┐     │         │ ┌──────┐        │           │  │
│  │  │ │ Pod1 │     │         │ │ Pod1 │        │           │  │
│  │  │ └──────┘     │         │ └──────┘        │           │  │
│  │  │ ┌──────┐     │         │ ┌──────┐        │           │  │
│  │  │ │ Pod2 │     │         │ │ Pod2 │        │           │  │
│  │  │ └──────┘     │         │ └──────┘        │           │  │
│  │  └──────────────┘         └─────────────────┘           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         ↓                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Redis Cluster (StatefulSet - 3 replicas)            │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐                     │  │
│  │  │redis-0 │  │redis-1 │  │redis-2 │                     │  │
│  │  └────────┘  └────────┘  └────────┘                     │  │
│  │  (10Gi PVC)   (10Gi PVC)  (10Gi PVC)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Monitoring Stack                                   │  │
│  │  ┌─────────────┐         ┌─────────────┐                │  │
│  │  │ Prometheus  │────────▶│  Grafana    │                │  │
│  │  │  (50Gi PVC) │         │  (10Gi PVC) │                │  │
│  │  └─────────────┘         └─────────────┘                │  │
│  │                          LoadBalancer                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      gRPC Server (3 replicas)                            │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐                          │  │
│  │  │ Pod  │  │ Pod  │  │ Pod  │                          │  │
│  │  └──────┘  └──────┘  └──────┘                          │  │
│  │       LoadBalancer Service (External Access)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Production Checklist

Before deploying to production, ensure:

- [ ] All Docker images are tested and scanned for vulnerabilities
- [ ] TLS/mTLS certificates are properly configured
- [ ] Resource limits are set appropriately
- [ ] Persistent storage is configured with backups
- [ ] Monitoring and alerting are configured
- [ ] Log aggregation is set up (e.g., ELK stack)
- [ ] Network policies are defined
- [ ] RBAC is properly configured
- [ ] High availability is configured (3+ replicas)
- [ ] Disaster recovery plan is documented
- [ ] Performance testing is complete
- [ ] Security audit is performed

---

## Support and Contact

For issues and questions:
- **Documentation**: https://sdr-oran.example.com/docs
- **Issue Tracker**: https://github.com/sdr-oran/platform/issues
- **Email**: support@sdr-oran.example.com

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-17
**Maintained By**: SDR-O-RAN Team
