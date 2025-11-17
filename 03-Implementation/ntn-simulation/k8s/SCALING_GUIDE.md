# NTN-O-RAN Scaling Guide

Guide for scaling the NTN-O-RAN platform to handle increased load.

## Table of Contents

1. [Overview](#overview)
2. [Horizontal Scaling](#horizontal-scaling)
3. [Vertical Scaling](#vertical-scaling)
4. [Auto-Scaling](#auto-scaling)
5. [Performance Optimization](#performance-optimization)
6. [Capacity Planning](#capacity-planning)

## Overview

The NTN-O-RAN platform supports both horizontal (more pods) and vertical (bigger pods) scaling.

### Current Capacity

| Component | Default Replicas | Max Auto-Scale | CPU Request | Memory Request |
|-----------|-----------------|----------------|-------------|----------------|
| E2 Termination | 2 | 5 | 1000m | 2Gi |
| Handover xApp | 2 | 5 | 500m | 1Gi |
| Power xApp | 2 | 5 | 500m | 1Gi |
| Orbit Service | 1 | 3 | 500m | 1Gi |
| Weather Service | 1 | - | 250m | 512Mi |
| Redis | 1 | - | 100m | 256Mi |

### Expected Performance

- **Current**: ~600 messages/second, ~5.5ms latency
- **Scaled (5x E2)**: ~3000 messages/second, ~5ms latency
- **Satellites**: 8,805 Starlink satellites tracked

## Horizontal Scaling

### Manual Scaling

Scale deployments manually:

```bash
# Scale E2 Termination to 5 replicas
kubectl scale deployment/e2-termination --replicas=5 -n ntn-oran

# Scale Handover xApp
kubectl scale deployment/handover-xapp --replicas=4 -n ntn-oran

# Scale Power xApp
kubectl scale deployment/power-xapp --replicas=4 -n ntn-oran

# Verify scaling
kubectl get deployments -n ntn-oran
```

### When to Scale

Scale up when:
- CPU usage > 70% for 5+ minutes
- Memory usage > 80%
- Latency > 10ms consistently
- Throughput < target (600 msg/s)
- Queue lengths increasing

Scale down when:
- CPU usage < 30% for 30+ minutes
- Low traffic periods
- Cost optimization needed

### Scaling Recommendations by Load

| Load Level | E2 Term | Handover xApp | Power xApp | Expected Performance |
|------------|---------|---------------|------------|---------------------|
| Low (<200 msg/s) | 2 | 1 | 1 | <4ms latency |
| Medium (200-600 msg/s) | 2-3 | 2 | 2 | <5.5ms latency |
| High (600-1500 msg/s) | 4 | 3 | 3 | <7ms latency |
| Very High (>1500 msg/s) | 5 | 5 | 5 | <10ms latency |

## Vertical Scaling

### Increase Resources

Edit deployment to increase CPU/memory:

```bash
kubectl edit deployment/e2-termination -n ntn-oran
```

Change resources:

```yaml
resources:
  requests:
    cpu: 2000m      # Was: 1000m
    memory: 4Gi     # Was: 2Gi
  limits:
    cpu: 4000m      # Was: 2000m
    memory: 8Gi     # Was: 4Gi
```

### Resource Sizing Guide

**E2 Termination:**
- Light: 500m CPU, 1Gi RAM (dev/test)
- Medium: 1000m CPU, 2Gi RAM (production default)
- Heavy: 2000m CPU, 4Gi RAM (high load)
- Extreme: 4000m CPU, 8Gi RAM (maximum throughput)

**xApps (Handover, Power):**
- Light: 250m CPU, 512Mi RAM
- Medium: 500m CPU, 1Gi RAM (default)
- Heavy: 1000m CPU, 2Gi RAM

**Redis:**
- Small: 100m CPU, 256Mi RAM (default)
- Medium: 500m CPU, 512Mi RAM
- Large: 1000m CPU, 1Gi RAM

## Auto-Scaling

### Horizontal Pod Autoscaler (HPA)

HPA automatically scales based on metrics.

**View HPA status:**
```bash
kubectl get hpa -n ntn-oran

NAME                  REFERENCE                    TARGETS         MINPODS   MAXPODS   REPLICAS
e2-termination-hpa    Deployment/e2-termination    45%/70%         2         5         2
handover-xapp-hpa     Deployment/handover-xapp     30%/70%         1         5         2
power-xapp-hpa        Deployment/power-xapp        25%/70%         1         5         2
```

**Modify HPA:**
```bash
# Change CPU threshold
kubectl edit hpa e2-termination-hpa -n ntn-oran

# Change min/max replicas
kubectl patch hpa e2-termination-hpa -n ntn-oran --patch '{"spec":{"minReplicas":3,"maxReplicas":10}}'
```

**Custom HPA based on custom metrics:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: e2-termination-hpa-custom
  namespace: ntn-oran
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: e2-termination
  minReplicas: 2
  maxReplicas: 10
  metrics:
  # CPU-based
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Memory-based
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  # Custom metric: message rate
  - type: Pods
    pods:
      metric:
        name: e2_messages_per_second
      target:
        type: AverageValue
        averageValue: "500"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### Vertical Pod Autoscaler (VPA)

VPA automatically adjusts resource requests/limits.

**Install VPA:**
```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh
```

**Create VPA:**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: e2-termination-vpa
  namespace: ntn-oran
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: e2-termination
  updatePolicy:
    updateMode: "Auto"  # Or "Off" to recommend only
  resourcePolicy:
    containerPolicies:
    - containerName: e2-termination
      minAllowed:
        cpu: 500m
        memory: 1Gi
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
```

## Performance Optimization

### Database Optimization (Redis)

```bash
# Increase Redis maxmemory
kubectl exec -it deployment/redis -n ntn-oran -- redis-cli CONFIG SET maxmemory 1gb

# Set eviction policy
kubectl exec -it deployment/redis -n ntn-oran -- redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Check Redis stats
kubectl exec -it deployment/redis -n ntn-oran -- redis-cli INFO stats
```

### Network Optimization

**Use NodeLocal DNSCache:**
```bash
# Reduces DNS lookup latency
kubectl apply -f https://k8s.io/examples/admin/dns/nodelocaldns.yaml
```

**Pod Affinity (co-locate related services):**
```yaml
affinity:
  podAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - e2-termination
        topologyKey: kubernetes.io/hostname
```

### Resource Limits Tuning

**Set appropriate limits to prevent OOM:**
```yaml
resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 2000m      # 2x request (allows bursting)
    memory: 4Gi     # 2x request (prevents OOM kill)
```

### Connection Pooling

Configure connection pools in application:
- Redis: pool_size=50, max_connections=100
- HTTP: keep-alive=True, pool_maxsize=50

## Capacity Planning

### Monitoring Metrics

Track these metrics for capacity planning:

```bash
# CPU usage trend
kubectl top pods -n ntn-oran

# Memory usage trend
kubectl top pods -n ntn-oran

# Message throughput (Prometheus)
# Query: sum(rate(e2_messages_total[5m]))

# Latency percentiles (Prometheus)
# Query: histogram_quantile(0.95, rate(e2_message_latency_ms_bucket[5m]))
```

### Growth Planning

**Current Capacity:**
- 600 msg/s with 2 E2 replicas
- 8,805 satellites tracked

**6-Month Projection:**
- 1,200 msg/s (2x growth)
- Recommendation: Increase to 4 E2 replicas
- Node resources: +50% (12 CPUs, 24GB RAM)

**1-Year Projection:**
- 2,400 msg/s (4x growth)
- Recommendation: 5 E2 replicas, 5 xApp replicas
- Node resources: +100% (16 CPUs, 32GB RAM)
- Consider multi-region deployment

### Cost Optimization

**Right-size resources:**
```bash
# Check actual resource usage
kubectl top pods -n ntn-oran

# Compare to requests
kubectl describe deployment/e2-termination -n ntn-oran | grep -A 5 "Requests"

# Reduce if over-provisioned
```

**Use spot/preemptible instances:**
```yaml
nodeSelector:
  node.kubernetes.io/instance-type: spot
tolerations:
- key: spot
  operator: Equal
  value: "true"
  effect: NoSchedule
```

**Scale down during off-hours:**
```bash
# Create CronJob to scale down
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-nightly
  namespace: ntn-oran
spec:
  schedule: "0 22 * * *"  # 10 PM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: kubectl
            image: bitnami/kubectl:latest
            command:
            - kubectl
            - scale
            - deployment/e2-termination
            - --replicas=1
            - -n
            - ntn-oran
          restartPolicy: OnFailure
```

### Load Testing

**Generate synthetic load:**
```bash
# Using Apache Bench
kubectl run load-test --image=httpd --rm -it -- ab -n 10000 -c 100 http://e2-termination-service:8082/

# Using custom load generator
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: load-test
  namespace: ntn-oran
spec:
  template:
    spec:
      containers:
      - name: load-generator
        image: ntn/load-generator:latest
        env:
        - name: TARGET_URL
          value: "http://e2-termination-service:8082"
        - name: REQUESTS_PER_SECOND
          value: "1000"
        - name: DURATION_SECONDS
          value: "300"
      restartPolicy: Never
EOF
```

**Monitor during load test:**
```bash
# Watch pods auto-scale
kubectl get hpa -n ntn-oran -w

# Monitor metrics in Grafana
kubectl port-forward -n ntn-oran svc/grafana-service 3000:3000
```

## Best Practices

1. **Start small, scale gradually**
   - Begin with minimum replicas
   - Monitor and scale based on actual load

2. **Use HPA for automatic scaling**
   - Set conservative thresholds initially
   - Tune based on actual behavior

3. **Set appropriate resource limits**
   - Requests: realistic baseline
   - Limits: allow for bursting (1.5-2x requests)

4. **Monitor continuously**
   - Set up alerts for high resource usage
   - Review trends weekly

5. **Plan for peak load**
   - Identify peak traffic patterns
   - Pre-scale before known events

6. **Test scaling regularly**
   - Run load tests monthly
   - Verify HPA triggers correctly

7. **Document scaling decisions**
   - Record why you scaled
   - Track cost implications

## Troubleshooting Scaling Issues

**HPA not scaling:**
- Check metrics-server: `kubectl get deployment metrics-server -n kube-system`
- Verify CPU metrics: `kubectl top pods -n ntn-oran`
- Check HPA conditions: `kubectl describe hpa <hpa-name> -n ntn-oran`

**Pods pending after scale-up:**
- Check node resources: `kubectl describe nodes`
- Add more nodes or reduce resource requests

**Performance not improving after scaling:**
- Check for bottlenecks (Redis, network)
- Review application logs for errors
- Analyze Grafana dashboards
