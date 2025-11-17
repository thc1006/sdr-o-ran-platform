# NTN-O-RAN Kubernetes Troubleshooting Guide

Common issues and their solutions for the NTN-O-RAN Kubernetes deployment.

## Table of Contents

1. [Pod Issues](#pod-issues)
2. [Service Connectivity](#service-connectivity)
3. [Performance Issues](#performance-issues)
4. [Storage Issues](#storage-issues)
5. [Monitoring & Logging](#monitoring--logging)
6. [Network Issues](#network-issues)
7. [Resource Constraints](#resource-constraints)

## Pod Issues

### Pods Not Starting

**Symptoms:**
- Pods stuck in `Pending`, `ImagePullBackOff`, or `CrashLoopBackOff`

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n ntn-oran

# Describe pod for events
kubectl describe pod <pod-name> -n ntn-oran

# Check pod logs
kubectl logs <pod-name> -n ntn-oran

# Check previous container logs (if crashed)
kubectl logs <pod-name> -n ntn-oran --previous
```

**Common Causes & Solutions:**

1. **ImagePullBackOff**
   - Cause: Docker image not found or credentials missing
   - Solution:
     ```bash
     # Verify image exists
     docker pull ntn/e2-termination:latest

     # Check image pull secrets
     kubectl get secrets -n ntn-oran

     # Create image pull secret if needed
     kubectl create secret docker-registry regcred \
       --docker-server=docker.io \
       --docker-username=<username> \
       --docker-password=<password> \
       -n ntn-oran
     ```

2. **CrashLoopBackOff**
   - Cause: Application error, missing config, or failed health checks
   - Solution:
     ```bash
     # Check logs
     kubectl logs <pod-name> -n ntn-oran

     # Check ConfigMap
     kubectl get configmap ntn-config -n ntn-oran -o yaml

     # Verify secrets exist
     kubectl get secret ntn-secrets -n ntn-oran

     # Temporarily disable probes for debugging
     kubectl edit deployment/<deployment-name> -n ntn-oran
     # Comment out livenessProbe and readinessProbe
     ```

3. **Pending (Insufficient Resources)**
   - Cause: Not enough CPU/memory on nodes
   - Solution:
     ```bash
     # Check node resources
     kubectl describe nodes
     kubectl top nodes

     # Reduce resource requests
     kubectl edit deployment/<deployment-name> -n ntn-oran

     # Or add more nodes to cluster
     ```

### Pod Restarts

**Symptoms:**
- Frequent pod restarts shown in `kubectl get pods`

**Diagnosis:**
```bash
# Check restart count
kubectl get pods -n ntn-oran

# Check events
kubectl get events -n ntn-oran --sort-by='.lastTimestamp'

# Check pod logs before crash
kubectl logs <pod-name> -n ntn-oran --previous
```

**Solutions:**

1. **OOMKilled (Out of Memory)**
   ```bash
   # Check memory usage
   kubectl top pods -n ntn-oran

   # Increase memory limits
   kubectl edit deployment/<deployment-name> -n ntn-oran
   # Increase resources.limits.memory
   ```

2. **Failed Health Checks**
   ```bash
   # Check probe configuration
   kubectl describe pod <pod-name> -n ntn-oran

   # Adjust probe timings
   kubectl edit deployment/<deployment-name> -n ntn-oran
   # Increase initialDelaySeconds, periodSeconds, or timeoutSeconds
   ```

## Service Connectivity

### Cannot Access Service

**Symptoms:**
- Service not reachable from other pods or externally
- Connection timeouts

**Diagnosis:**
```bash
# Check service
kubectl get svc -n ntn-oran

# Check endpoints
kubectl get endpoints -n ntn-oran

# Describe service
kubectl describe svc <service-name> -n ntn-oran

# Test from another pod
kubectl run test-pod --image=curlimages/curl -it --rm -n ntn-oran -- sh
# Inside pod:
curl http://<service-name>:8080/health
```

**Solutions:**

1. **No Endpoints**
   - Cause: Selector doesn't match pod labels
   ```bash
   # Check service selector
   kubectl get svc <service-name> -n ntn-oran -o yaml | grep selector -A 5

   # Check pod labels
   kubectl get pods -n ntn-oran --show-labels

   # Fix selector in service
   kubectl edit svc <service-name> -n ntn-oran
   ```

2. **LoadBalancer Pending**
   - Cause: No cloud load balancer provisioner
   ```bash
   # Check service type
   kubectl get svc -n ntn-oran

   # Change to NodePort for local testing
   kubectl patch svc <service-name> -n ntn-oran -p '{"spec":{"type":"NodePort"}}'

   # Or use port-forward
   kubectl port-forward svc/<service-name> 8080:8080 -n ntn-oran
   ```

### DNS Issues

**Symptoms:**
- Services cannot resolve each other by name

**Diagnosis:**
```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Test DNS from pod
kubectl run test-dns --image=busybox -it --rm -n ntn-oran -- nslookup e2-termination-service
```

**Solutions:**
```bash
# Restart CoreDNS
kubectl rollout restart deployment/coredns -n kube-system

# Check DNS configuration
kubectl get configmap coredns -n kube-system -o yaml
```

## Performance Issues

### High Latency

**Symptoms:**
- E2E latency > 10ms (target: 5.5ms)

**Diagnosis:**
```bash
# Check Grafana dashboard
kubectl port-forward -n ntn-oran svc/grafana-service 3000:3000
# View "NTN-O-RAN Overview" dashboard

# Check Prometheus metrics
kubectl port-forward -n ntn-oran svc/prometheus-service 9090:9090
# Query: avg(e2_message_latency_ms)
```

**Solutions:**

1. **CPU Throttling**
   ```bash
   # Check CPU usage
   kubectl top pods -n ntn-oran

   # Increase CPU limits
   kubectl edit deployment/e2-termination -n ntn-oran
   # Increase resources.limits.cpu

   # Scale replicas
   kubectl scale deployment/e2-termination --replicas=3 -n ntn-oran
   ```

2. **Network Latency**
   ```bash
   # Check pod distribution across nodes
   kubectl get pods -n ntn-oran -o wide

   # Use pod affinity to co-locate related services
   kubectl edit deployment/handover-xapp -n ntn-oran
   # Add affinity rules
   ```

3. **Slow Database Queries**
   ```bash
   # Check Redis performance
   kubectl exec -it deployment/redis -n ntn-oran -- redis-cli
   > INFO stats
   > SLOWLOG GET 10

   # Increase Redis memory
   kubectl edit deployment/redis -n ntn-oran
   ```

### Low Throughput

**Symptoms:**
- Message throughput < 400 msg/s (target: 600 msg/s)

**Diagnosis:**
```bash
# Check Prometheus
# Query: sum(rate(e2_messages_total[1m]))
```

**Solutions:**
```bash
# Scale E2 Termination
kubectl scale deployment/e2-termination --replicas=5 -n ntn-oran

# Check HPA status
kubectl get hpa -n ntn-oran

# Verify HPA is working
kubectl describe hpa e2-termination-hpa -n ntn-oran
```

## Storage Issues

### PVC Pending

**Symptoms:**
- PersistentVolumeClaim stuck in `Pending`

**Diagnosis:**
```bash
# Check PVC status
kubectl get pvc -n ntn-oran

# Describe PVC
kubectl describe pvc <pvc-name> -n ntn-oran
```

**Solutions:**

1. **No Storage Class**
   ```bash
   # Check storage classes
   kubectl get storageclass

   # Create default storage class for minikube
   kubectl patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
   ```

2. **Insufficient Storage**
   ```bash
   # Check available storage
   kubectl get pv

   # Reduce PVC size
   kubectl edit pvc <pvc-name> -n ntn-oran
   ```

### Disk Full

**Symptoms:**
- Elasticsearch or Prometheus pods failing

**Solutions:**
```bash
# Check disk usage
kubectl exec -it <pod-name> -n ntn-oran -- df -h

# Clean old data
kubectl exec -it elasticsearch-0 -n ntn-oran -- sh
# Delete old indices

# Increase PVC size (if supported)
kubectl edit pvc prometheus-pvc -n ntn-oran
```

## Monitoring & Logging

### Metrics Not Showing in Grafana

**Diagnosis:**
```bash
# Check Prometheus targets
kubectl port-forward -n ntn-oran svc/prometheus-service 9090:9090
# Navigate to: http://localhost:9090/targets

# Check pod annotations
kubectl get pod <pod-name> -n ntn-oran -o yaml | grep prometheus
```

**Solutions:**
```bash
# Verify annotations on pods
kubectl edit deployment/e2-termination -n ntn-oran
# Ensure these annotations exist:
#   prometheus.io/scrape: "true"
#   prometheus.io/port: "8082"
#   prometheus.io/path: "/metrics"

# Restart Prometheus
kubectl rollout restart deployment/prometheus -n ntn-oran
```

### Logs Not in Kibana

**Diagnosis:**
```bash
# Check Filebeat DaemonSet
kubectl get daemonset/filebeat -n ntn-oran

# Check Logstash
kubectl logs deployment/logstash -n ntn-oran

# Check Elasticsearch
kubectl logs statefulset/elasticsearch -n ntn-oran
```

**Solutions:**
```bash
# Restart Filebeat
kubectl rollout restart daemonset/filebeat -n ntn-oran

# Check Elasticsearch health
kubectl port-forward -n ntn-oran svc/elasticsearch 9200:9200
curl http://localhost:9200/_cluster/health

# Create index pattern in Kibana
# Navigate to Kibana -> Stack Management -> Index Patterns
# Create pattern: ntn-oran-logs-*
```

## Network Issues

### Ingress Not Working

**Diagnosis:**
```bash
# Check Ingress
kubectl get ingress -n ntn-oran

# Describe Ingress
kubectl describe ingress ntn-oran-ingress -n ntn-oran

# Check Ingress controller
kubectl get pods -n ingress-nginx
```

**Solutions:**
```bash
# Install nginx ingress controller (minikube)
minikube addons enable ingress

# Check Ingress class
kubectl get ingressclass

# Update /etc/hosts
echo "$(minikube ip) ntn-oran.local" | sudo tee -a /etc/hosts
```

### Pod-to-Pod Communication Failing

**Diagnosis:**
```bash
# Test connectivity
kubectl run test-curl --image=curlimages/curl -it --rm -n ntn-oran -- sh
curl http://e2-termination-service:8082/health
```

**Solutions:**
```bash
# Check network policies
kubectl get networkpolicies -n ntn-oran

# Check CNI plugin
kubectl get pods -n kube-system | grep -i cni

# Restart pods
kubectl rollout restart deployment/<deployment-name> -n ntn-oran
```

## Resource Constraints

### HPA Not Scaling

**Diagnosis:**
```bash
# Check HPA status
kubectl get hpa -n ntn-oran

# Describe HPA
kubectl describe hpa e2-termination-hpa -n ntn-oran

# Check metrics-server
kubectl get deployment metrics-server -n kube-system
```

**Solutions:**
```bash
# Install metrics-server (minikube)
minikube addons enable metrics-server

# Verify metrics available
kubectl top pods -n ntn-oran

# Check HPA conditions
kubectl get hpa -n ntn-oran -o yaml
```

### Node Out of Resources

**Diagnosis:**
```bash
# Check node status
kubectl describe nodes | grep -A 5 "Allocated resources"

# Check node pressure
kubectl get nodes -o wide
```

**Solutions:**
```bash
# Add more nodes (cloud)
# Or reduce resource requests

# Evict non-critical pods
kubectl delete pod <pod-name> -n other-namespace

# Adjust resource requests
kubectl edit deployment/<deployment-name> -n ntn-oran
```

## Quick Debug Commands

```bash
# Get everything in namespace
kubectl get all -n ntn-oran

# Check events
kubectl get events -n ntn-oran --sort-by='.lastTimestamp' | tail -20

# Check pod logs (all containers)
kubectl logs <pod-name> -n ntn-oran --all-containers=true

# Execute command in pod
kubectl exec -it <pod-name> -n ntn-oran -- /bin/bash

# Port-forward for debugging
kubectl port-forward <pod-name> 8080:8080 -n ntn-oran

# Check resource usage
kubectl top pods -n ntn-oran
kubectl top nodes

# Get pod YAML
kubectl get pod <pod-name> -n ntn-oran -o yaml

# Delete and recreate pod
kubectl delete pod <pod-name> -n ntn-oran
```

## Escalation

If issues persist:
1. Collect diagnostic bundle:
   ```bash
   kubectl get all -n ntn-oran -o yaml > diagnostics.yaml
   kubectl describe pods -n ntn-oran > pod-descriptions.txt
   kubectl logs deployment/e2-termination -n ntn-oran > e2-logs.txt
   ```

2. Check Grafana dashboards for patterns
3. Review Prometheus alerts
4. Analyze logs in Kibana
5. Open GitHub issue with diagnostics
