# xApp Deployment Guide

## Overview

This guide covers deploying xApps in various environments, from development to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Considerations](#production-considerations)
6. [Monitoring and Debugging](#monitoring-and-debugging)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.8 or higher
- **Redis**: 6.0 or higher
- **Memory**: 2GB minimum per xApp
- **CPU**: 2 cores minimum

### Software Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Redis
sudo apt-get update
sudo apt-get install redis-server

# Verify Redis is running
redis-cli ping  # Should return PONG
```

---

## Development Deployment

### Local Setup

#### 1. Set Up Environment

```bash
# Navigate to RIC platform directory
cd /path/to/sdr-o-ran-platform/03-Implementation/ric-platform

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Redis

```bash
# Start Redis server
redis-server --daemonize yes

# Verify connection
redis-cli ping
```

#### 3. Run a Single xApp

```bash
# Run QoS Optimizer xApp
python xapps/qos_optimizer_xapp.py
```

Output:
```
INFO:xapp.qos-optimizer:Starting xApp: qos-optimizer v1.0.0
INFO:xapp.qos-optimizer:QoS Optimizer xApp initializing...
```

#### 4. Run Multiple xApps with Manager

Create `run_xapps.py`:

```python
import asyncio
import logging
from xapp_sdk import XAppManager
from xapps import QoSOptimizerXApp, HandoverManagerXApp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    manager = XAppManager()

    # Deploy xApps
    qos_xapp = QoSOptimizerXApp()
    ho_xapp = HandoverManagerXApp()

    await manager.deploy_xapp(qos_xapp)
    await manager.deploy_xapp(ho_xapp)

    logging.info("All xApps deployed")

    # List deployed xApps
    for xapp in manager.list_xapps():
        logging.info(f"Running: {xapp['name']} v{xapp['version']}")

    try:
        # Run indefinitely
        while True:
            await asyncio.sleep(60)

            # Periodic status check
            for xapp in manager.list_xapps():
                status = manager.get_xapp_status(xapp['name'])
                logging.info(f"{xapp['name']} metrics: {status['metrics']}")
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        await manager.undeploy_xapp("qos-optimizer")
        await manager.undeploy_xapp("handover-manager")

if __name__ == "__main__":
    asyncio.run(main())
```

Run:
```bash
python run_xapps.py
```

---

## Docker Deployment

### Dockerfile for xApp

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy xApp SDK and applications
COPY xapp-sdk/ ./xapp-sdk/
COPY xapps/ ./xapps/

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "xapps/qos_optimizer_xapp.py"]
```

### Build and Run

```bash
# Build image
docker build -t xapp-qos-optimizer:1.0.0 .

# Run with Redis connection
docker run -d \
  --name qos-optimizer \
  --network host \
  -e REDIS_HOST=localhost \
  -e REDIS_PORT=6379 \
  xapp-qos-optimizer:1.0.0
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:6.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  qos-optimizer:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    command: python xapps/qos_optimizer_xapp.py
    restart: unless-stopped

  handover-manager:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    command: python xapps/handover_manager_xapp.py
    restart: unless-stopped

volumes:
  redis-data:
```

Run:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f qos-optimizer

# Stop all services
docker-compose down
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Helm (optional, recommended)

### ConfigMap for Configuration

`k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: xapp-config
  namespace: ric-platform
data:
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  LOG_LEVEL: "INFO"
```

### Redis Deployment

`k8s/redis-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: ric-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6.2-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: ric-platform
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### xApp Deployment

`k8s/qos-optimizer-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qos-optimizer
  namespace: ric-platform
  labels:
    app: qos-optimizer
    version: "1.0.0"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qos-optimizer
  template:
    metadata:
      labels:
        app: qos-optimizer
        version: "1.0.0"
    spec:
      containers:
      - name: qos-optimizer
        image: xapp-qos-optimizer:1.0.0
        imagePullPolicy: IfNotPresent
        envFrom:
        - configMapRef:
            name: xapp-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace ric-platform

# Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/qos-optimizer-deployment.yaml
kubectl apply -f k8s/handover-manager-deployment.yaml

# Verify deployments
kubectl get pods -n ric-platform

# View logs
kubectl logs -f deployment/qos-optimizer -n ric-platform
```

### Helm Chart (Advanced)

Create `helm/xapp/Chart.yaml`:

```yaml
apiVersion: v2
name: xapp
description: O-RAN xApp Helm Chart
version: 1.0.0
appVersion: "1.0.0"
```

Create `helm/xapp/values.yaml`:

```yaml
redis:
  enabled: true
  host: redis-service
  port: 6379

xapps:
  qos-optimizer:
    enabled: true
    replicas: 1
    image:
      repository: xapp-qos-optimizer
      tag: "1.0.0"
    resources:
      requests:
        memory: 256Mi
        cpu: 250m
      limits:
        memory: 512Mi
        cpu: 500m

  handover-manager:
    enabled: true
    replicas: 1
    image:
      repository: xapp-handover-manager
      tag: "1.0.0"
    resources:
      requests:
        memory: 256Mi
        cpu: 250m
      limits:
        memory: 512Mi
        cpu: 500m
```

Deploy with Helm:
```bash
helm install my-xapps ./helm/xapp -n ric-platform
```

---

## Production Considerations

### 1. High Availability

#### Redis Sentinel for HA

```yaml
# Use Redis Sentinel for automatic failover
redis-sentinel:
  enabled: true
  replicas: 3
  quorum: 2
```

#### Multiple xApp Replicas

```yaml
# Scale xApps for redundancy
spec:
  replicas: 2  # Run 2 instances
```

### 2. Security

#### Network Policies

`k8s/network-policy.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: xapp-network-policy
  namespace: ric-platform
spec:
  podSelector:
    matchLabels:
      app: qos-optimizer
  policyTypes:
  - Ingress
  - Egress
  ingress: []  # No ingress allowed
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

#### Secrets Management

```bash
# Create secret for Redis password
kubectl create secret generic redis-secret \
  --from-literal=password=your-secure-password \
  -n ric-platform
```

### 3. Resource Management

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"

# Autoscaling
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: qos-optimizer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: qos-optimizer
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

### 4. Logging and Monitoring

#### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_obj)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

#### Prometheus Metrics

Add to xApp:

```python
from prometheus_client import Counter, Gauge, start_http_server

# Define metrics
indications_counter = Counter('xapp_indications_total', 'Total indications received')
ues_gauge = Gauge('xapp_ues_active', 'Number of active UEs')

# Start metrics server
start_http_server(8000)

# Update metrics
indications_counter.inc()
ues_gauge.set(len(self.ue_metrics))
```

---

## Monitoring and Debugging

### Health Checks

Add to xApp:

```python
from aiohttp import web

async def health_check(request):
    return web.Response(text="OK", status=200)

async def readiness_check(request):
    if self.running and self.sdl_connected:
        return web.Response(text="Ready", status=200)
    return web.Response(text="Not Ready", status=503)

app = web.Application()
app.router.add_get('/health', health_check)
app.router.add_get('/ready', readiness_check)
web.run_app(app, port=8080)
```

### Debugging

```bash
# View logs
kubectl logs -f deployment/qos-optimizer -n ric-platform

# Execute into container
kubectl exec -it deployment/qos-optimizer -n ric-platform -- /bin/bash

# Check Redis data
kubectl exec -it deployment/redis -n ric-platform -- redis-cli
> KEYS qos-optimizer:*
> GET qos-optimizer:ue_metrics
```

### Performance Monitoring

```bash
# Monitor resource usage
kubectl top pods -n ric-platform

# Monitor metrics
curl http://qos-optimizer-service:8000/metrics
```

---

## Troubleshooting

### Common Issues

#### 1. xApp Can't Connect to Redis

```bash
# Check Redis is running
kubectl get pods -n ric-platform | grep redis

# Check network connectivity
kubectl exec -it deployment/qos-optimizer -n ric-platform -- \
  redis-cli -h redis-service ping
```

#### 2. xApp Not Receiving Indications

- Verify E2 interface connection
- Check subscription configuration
- Review E2 termination logs

#### 3. High Memory Usage

```bash
# Check Redis memory
redis-cli INFO memory

# Clean up old keys
redis-cli --scan --pattern "qos-optimizer:old-*" | xargs redis-cli DEL
```

#### 4. Performance Issues

- Increase resource limits
- Scale horizontally
- Optimize processing logic
- Use caching

---

## Summary

This deployment guide covered:
- Local development setup
- Docker containerization
- Kubernetes orchestration
- Production best practices
- Monitoring and debugging

For more information:
- [xApp Development Guide](XAPP_DEVELOPMENT_GUIDE.md)
- [SDK API Reference](SDK_API_REFERENCE.md)
- [Example xApps](EXAMPLE_XAPPS.md)
