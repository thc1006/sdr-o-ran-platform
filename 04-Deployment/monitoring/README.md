# SDR O-RAN Platform - Monitoring and Observability Guide

Comprehensive monitoring setup for the SDR O-RAN platform with satellite connectivity, providing real-time insights into system performance, security, and AI/ML operations.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Instructions](#deployment-instructions)
- [Dashboard Guide](#dashboard-guide)
- [Alert Configuration](#alert-configuration)
- [Log Aggregation](#log-aggregation)
- [Metrics Reference](#metrics-reference)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Overview

This monitoring solution provides:

- **Real-time Metrics**: Prometheus 2.50+ for metrics collection and storage
- **Visualization**: Grafana 10.0+ with custom dashboards
- **Log Aggregation**: Loki 2.9.0+ for centralized logging
- **Alerting**: Comprehensive alerting rules based on production thresholds
- **Service Discovery**: Automatic monitoring of Kubernetes services via ServiceMonitors

### Key Performance Indicators (KPIs) Monitored

| Metric | LEO Target | GEO Target | Alert Threshold |
|--------|------------|------------|-----------------|
| E2E Latency (P95) | < 100ms | < 350ms | 150ms (LEO), 400ms (GEO) |
| Throughput | 80-95 Mbps | 80-95 Mbps | < 50 Mbps |
| DRL Inference Latency | < 10ms | < 10ms | > 15ms |
| Packet Loss | < 0.1% | < 0.1% | > 1.0% |
| PQC Handshake Success | > 99% | > 99% | < 95% |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Grafana Dashboards                       │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐ │
│  │  SDR Platform│   O-RAN RIC  │    AI/ML     │ Security │ │
│  └──────────────┴──────────────┴──────────────┴──────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐              ┌───────▼────────┐
│  Prometheus    │              │  Grafana Loki  │
│  (Metrics)     │              │  (Logs)        │
└───────┬────────┘              └───────┬────────┘
        │                               │
        │ ServiceMonitors               │ Promtail
        │                               │
┌───────▼───────────────────────────────▼────────┐
│            Kubernetes Services                  │
│  ┌─────────┬─────────┬─────────┬─────────┐    │
│  │ USRP    │ O-RAN   │ AI/ML   │ PQC     │    │
│  │ Pods    │ RIC     │ Training│ Crypto  │    │
│  └─────────┴─────────┴─────────┴─────────┘    │
└─────────────────────────────────────────────────┘
```

---

## Prerequisites

### Software Requirements

- **Kubernetes**: v1.27+
- **Helm**: v3.12+
- **kubectl**: v1.27+
- **Prometheus Operator**: v0.70+

### Resource Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| Prometheus | 2 cores | 4 GB | 50 GB |
| Grafana | 1 core | 2 GB | 10 GB |
| Loki | 2 cores | 4 GB | 100 GB |
| Promtail (per node) | 0.5 core | 512 MB | 1 GB |

### Network Requirements

- Prometheus scrape endpoints accessible on cluster network
- Grafana accessible via ingress (port 3000)
- AlertManager accessible for alert notifications

---

## Quick Start

### 1. Deploy Prometheus Operator Stack

```bash
# Add Prometheus community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create monitoring namespace
kubectl create namespace monitoring

# Install kube-prometheus-stack (includes Prometheus, Grafana, AlertManager)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.retention=90d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
  --set grafana.adminPassword=admin \
  --set grafana.persistence.enabled=true \
  --set grafana.persistence.size=10Gi
```

### 2. Deploy Loki for Log Aggregation

```bash
# Add Grafana Helm repository
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Loki
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=100Gi \
  --set promtail.enabled=true \
  --set loki.config.table_manager.retention_deletes_enabled=true \
  --set loki.config.table_manager.retention_period=2160h
```

### 3. Apply Custom Configurations

```bash
# Navigate to monitoring directory
cd 04-Deployment/monitoring

# Apply Prometheus alerting rules
kubectl apply -f prometheus-rules.yml

# Apply ServiceMonitors for automatic service discovery
kubectl apply -f servicemonitor.yml

# Apply Loki configuration
kubectl apply -f loki-config.yml
```

### 4. Import Grafana Dashboards

```bash
# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Open browser: http://localhost:3000
# Login: admin / admin (change on first login)

# Import dashboards:
# 1. Go to Dashboards → Import
# 2. Upload each JSON file from grafana-dashboards/
#    - sdr-platform-dashboard.json
#    - oran-ric-dashboard.json
#    - aiml-dashboard.json
#    - security-dashboard.json
```

---

## Deployment Instructions

### Step-by-Step Production Deployment

#### 1. Prepare Kubernetes Cluster

```bash
# Verify cluster is running
kubectl cluster-info

# Verify node resources
kubectl top nodes

# Create namespace
kubectl create namespace monitoring
kubectl label namespace monitoring monitoring=enabled
```

#### 2. Configure Storage Classes

Ensure persistent storage is available:

```yaml
# storage-class.yml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: monitoring-storage
provisioner: kubernetes.io/aws-ebs  # Adjust for your cloud provider
parameters:
  type: gp3
  fsType: ext4
reclaimPolicy: Retain
allowVolumeExpansion: true
```

```bash
kubectl apply -f storage-class.yml
```

#### 3. Deploy Prometheus with Custom Configuration

```bash
# Create values file for Prometheus
cat <<EOF > prometheus-values.yaml
prometheus:
  prometheusSpec:
    retention: 90d
    retentionSize: 45GB
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: monitoring-storage
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi
    resources:
      requests:
        cpu: 2000m
        memory: 4Gi
      limits:
        cpu: 4000m
        memory: 8Gi
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false
    ruleSelectorNilUsesHelmValues: false

grafana:
  adminPassword: "ChangeMe123!"
  persistence:
    enabled: true
    storageClassName: monitoring-storage
    size: 10Gi
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi
  datasources:
    datasources.yaml:
      apiVersion: 1
      datasources:
        - name: Prometheus
          type: prometheus
          url: http://prometheus-kube-prometheus-prometheus:9090
          access: proxy
          isDefault: true
        - name: Loki
          type: loki
          url: http://loki:3100
          access: proxy

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: monitoring-storage
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi

kubeStateMetrics:
  enabled: true

nodeExporter:
  enabled: true

prometheusOperator:
  enabled: true
EOF

# Install with custom values
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values prometheus-values.yaml
```

#### 4. Deploy Loki with Production Configuration

```bash
# Create Loki values file
cat <<EOF > loki-values.yaml
loki:
  persistence:
    enabled: true
    storageClassName: monitoring-storage
    size: 100Gi
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
  config:
    auth_enabled: false
    ingester:
      chunk_idle_period: 3m
      chunk_block_size: 262144
      chunk_retain_period: 1m
      max_transfer_retries: 0
      lifecycler:
        ring:
          kvstore:
            store: inmemory
          replication_factor: 1
    limits_config:
      enforce_metric_name: false
      reject_old_samples: true
      reject_old_samples_max_age: 168h
      ingestion_rate_mb: 50
      ingestion_burst_size_mb: 100
      retention_period: 2160h  # 90 days
    schema_config:
      configs:
        - from: 2024-01-01
          store: boltdb-shipper
          object_store: filesystem
          schema: v11
          index:
            prefix: index_
            period: 24h
    server:
      http_listen_port: 3100
      grpc_listen_port: 9096
    storage_config:
      boltdb_shipper:
        active_index_directory: /data/loki/boltdb-shipper-active
        cache_location: /data/loki/boltdb-shipper-cache
        cache_ttl: 24h
        shared_store: filesystem
      filesystem:
        directory: /data/loki/chunks
    compactor:
      working_directory: /data/loki/compactor
      shared_store: filesystem
      compaction_interval: 10m
      retention_enabled: true
      retention_delete_delay: 2h

promtail:
  enabled: true
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  config:
    clients:
      - url: http://loki:3100/loki/api/v1/push
EOF

# Install Loki
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --values loki-values.yaml
```

#### 5. Apply Custom Monitoring Configurations

```bash
# Apply alerting rules
kubectl apply -f prometheus-rules.yml

# Apply ServiceMonitors
kubectl apply -f servicemonitor.yml

# Verify resources
kubectl get servicemonitors -n monitoring
kubectl get prometheusrules -n monitoring
```

#### 6. Configure Ingress for Grafana

```yaml
# grafana-ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: monitoring
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - grafana.sdr-platform.io
      secretName: grafana-tls
  rules:
    - host: grafana.sdr-platform.io
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: prometheus-grafana
                port:
                  number: 80
```

```bash
kubectl apply -f grafana-ingress.yml
```

---

## Dashboard Guide

### SDR Platform Dashboard

**File**: `grafana-dashboards/sdr-platform-dashboard.json`

#### Key Panels

1. **Current Throughput** (Gauge)
   - Real-time throughput in Mbps
   - Green: > 80 Mbps, Red: < 50 Mbps
   - Query: `rate(sdr_throughput_bytes_total[5m]) * 8 / 1000000`

2. **SDR Throughput Over Time** (Time Series)
   - Historical throughput trends
   - Shows mean, max, min statistics

3. **USRP IQ Sample Rate** (Time Series)
   - Expected: 30.72 MHz (dashed red line)
   - Actual sample rate (blue line)
   - Alerts if deviation > 1 MHz

4. **USRP Packet Loss Rate** (Time Series)
   - Warning: > 0.1%, Critical: > 1.0%
   - Query: `rate(usrp_packet_loss_total[5m]) / rate(usrp_packets_total[5m])`

5. **Overflow/Underrun Errors** (Time Series)
   - Overflow: Host can't keep up with USRP
   - Underrun: TX buffer starvation

6. **RF Signal Metrics**
   - Signal Strength (dBm)
   - SNR (dB)
   - Carrier Frequency
   - TX/RX Power Levels

### O-RAN RIC Dashboard

**File**: `grafana-dashboards/oran-ric-dashboard.json`

#### Key Panels

1. **E2 Control Plane Latency** (Time Series)
   - P50, P95, P99 percentiles
   - Warning: > 8ms, Critical: > 10ms

2. **E2 Interface Status** (Stat)
   - Green: UP, Red: DOWN
   - Critical alert if down > 1 minute

3. **RIC Request Queue Length** (Gauge)
   - Warning: > 1000 requests
   - Indicates RIC overload

4. **xApp Decision Latency** (Time Series)
   - Per-xApp breakdown
   - Threshold: < 20ms

5. **Connected UEs** (Time Series)
   - Active user equipment count

6. **PRB Utilization** (Time Series)
   - Physical Resource Block usage (%)

### AI/ML Dashboard

**File**: `grafana-dashboards/aiml-dashboard.json`

#### Key Panels

1. **DRL Training/Validation Loss** (Time Series)
   - Should decrease over time
   - Alert if not decreasing in 1 hour

2. **Model Accuracy** (Gauge)
   - Red: < 70%, Yellow: 70-85%, Green: > 85%

3. **DRL Inference Latency** (Time Series)
   - P50, P95, P99 percentiles
   - Warning: > 10ms, Critical: > 15ms

4. **GPU Utilization** (Gauge)
   - Warning if < 30% (underutilized)
   - Critical if > 85% (overloaded)

5. **Training Throughput** (Time Series)
   - Steps per second
   - Indicates training pipeline health

6. **TensorBoard Integration**
   - Link to external TensorBoard instance
   - Detailed training visualizations

### Security Dashboard

**File**: `grafana-dashboards/security-dashboard.json`

#### Key Panels

1. **PQC Operations Rate** (Time Series)
   - ML-KEM encapsulation/decapsulation
   - ML-DSA sign/verify operations

2. **PQC Operation Latency** (Time Series)
   - P95 latency for each operation
   - Warning: > 3ms, Critical: > 5ms

3. **PQC Handshake Failure Rate** (Time Series)
   - Warning: > 2%, Critical: > 5%

4. **ML-KEM Key Age** (Stat)
   - Red: > 7 days, Yellow: 7-30 days, Green: < 7 days
   - Recommended rotation: weekly

5. **Certificate Expiry** (Table)
   - Lists all certificates with days to expiry
   - Color-coded: Red < 7 days, Yellow < 30 days

6. **Encrypted Traffic Volume** (Time Series)
   - Total encrypted data transfer rate

---

## Alert Configuration

### Alert Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **Info** | Informational notice | None required | Low GPU utilization |
| **Warning** | Potential issue | 15-30 minutes | High latency (80% threshold) |
| **Critical** | Service impacting | Immediate | Service down, critical latency |

### Key Alerts Explained

#### E2E Latency Alerts

```yaml
- alert: HighLEOLatency
  expr: histogram_quantile(0.95, rate(sdr_e2e_latency_seconds_bucket{orbit="leo"}[5m])) > 0.100
  for: 2m
  annotations:
    summary: "High LEO satellite E2E latency detected"
    description: "95th percentile LEO latency is {{ $value }}s (threshold: 100ms)"
```

**Troubleshooting Steps**:
1. Check satellite link quality: `kubectl logs -n sdr-platform <usrp-pod>`
2. Verify network path: `kubectl exec -n sdr-platform <pod> -- traceroute <destination>`
3. Check for packet loss: Review USRP Packet Loss panel
4. Investigate CPU/memory pressure on pods

#### Throughput Alerts

```yaml
- alert: LowThroughput
  expr: rate(sdr_throughput_bytes_total[5m]) * 8 / 1000000 < 50
  for: 5m
```

**Troubleshooting Steps**:
1. Check USRP connection: `kubectl get pods -n sdr-platform | grep usrp`
2. Verify IQ sample rate: Should be ~30.72 MHz
3. Check overflow/underrun errors
4. Review RF signal strength and SNR

#### DRL Inference Alerts

```yaml
- alert: HighDRLInferenceLatency
  expr: histogram_quantile(0.95, rate(drl_inference_latency_seconds_bucket[5m])) > 0.015
  for: 3m
```

**Troubleshooting Steps**:
1. Check GPU utilization: Should be 30-85%
2. Review model complexity: May need optimization
3. Check batch size configuration
4. Verify GPU memory availability

### Configuring Alert Notifications

#### Slack Integration

```yaml
# alertmanager-config.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#sdr-alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

#### Email Integration

```yaml
receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'sdr-ops@company.com'
        from: 'alerts@sdr-platform.io'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@sdr-platform.io'
        auth_password: 'your-app-password'
```

Apply configuration:

```bash
kubectl create secret generic alertmanager-config \
  --from-file=alertmanager.yml=alertmanager-config.yml \
  -n monitoring

kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    $(cat alertmanager-config.yml)
EOF
```

---

## Log Aggregation

### Loki Query Examples

#### 1. View All SDR Platform Logs (Last Hour)

```logql
{job="sdr-platform"} |~ ".*"
```

#### 2. Filter Error Logs from O-RAN RIC

```logql
{job="oran-ric"} |= "level=error"
```

#### 3. Search for Packet Loss Events

```logql
{component="usrp"} |= "packet loss" |= "rate > 0.1%"
```

#### 4. PQC Handshake Failures

```logql
{component="security"} |~ "handshake.*failed" |= "ml-kem"
```

#### 5. High Latency Warnings

```logql
{job=~"sdr-platform|oran-ric"} |~ "latency.*[1-9][0-9]{2}ms"
```

#### 6. Container Restart Events

```logql
{namespace="sdr-platform"} |= "restarting" or "crashloopbackoff"
```

#### 7. AI/ML Training Errors

```logql
{job="aiml", component="training"} |= "error" or "exception"
```

#### 8. Calculate Error Rate (Metric Query)

```logql
sum(rate({job="sdr-platform"} |= "error" [5m])) by (component)
```

#### 9. Trace Specific Transaction

```logql
{namespace="sdr-platform"} |= "trace_id=abc123"
```

#### 10. Extract Latency Values from Logs

```logql
{component="sdr-platform"}
  | regexp "latency=(?P<latency>\\d+)ms"
  | unwrap latency
```

### Setting Up Log-Based Alerts

```yaml
# loki-alert-rules.yml
groups:
  - name: sdr-log-alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({job="sdr-platform"} |= "error" [5m])) > 10
        for: 5m
        annotations:
          summary: "High error rate in SDR platform"
          description: "More than 10 errors per second"

      - alert: USRPConnectionLost
        expr: |
          count_over_time({component="usrp"} |= "connection lost" [5m]) > 0
        annotations:
          summary: "USRP connection lost"
```

Apply rules:

```bash
kubectl apply -f loki-alert-rules.yml
```

### Log Retention Management

Default retention: **90 days** (2160 hours)

To adjust retention:

```yaml
# In loki-config.yml
limits_config:
  retention_period: 2160h  # 90 days

compactor:
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
```

Verify retention settings:

```bash
kubectl exec -n monitoring loki-0 -- \
  wget -O- http://localhost:3100/config | grep retention
```

---

## Metrics Reference

### SDR Platform Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `sdr_throughput_bytes_total` | Counter | - | Total bytes transmitted |
| `sdr_e2e_latency_seconds` | Histogram | `orbit` | End-to-end latency |
| `sdr_iq_samples_total` | Counter | - | IQ samples processed |
| `sdr_signal_strength_dbm` | Gauge | - | RF signal strength |
| `sdr_snr_db` | Gauge | - | Signal-to-noise ratio |
| `usrp_packet_loss_total` | Counter | - | Packet loss count |
| `usrp_overflow_errors_total` | Counter | - | Overflow errors |
| `usrp_underrun_errors_total` | Counter | - | Underrun errors |
| `usrp_temperature_celsius` | Gauge | - | Device temperature |

### O-RAN RIC Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `oran_e2_control_latency_seconds` | Histogram | - | E2 control latency |
| `oran_kpm_metrics_received_total` | Counter | - | KPM metrics received |
| `xapp_decision_latency_seconds` | Histogram | `xapp_name` | xApp decision time |
| `xapp_decisions_total` | Counter | `xapp_name` | Total decisions made |
| `oran_connected_ues_total` | Gauge | - | Connected UEs |
| `oran_prb_utilization_percent` | Gauge | - | PRB utilization |
| `oran_e2_messages_total` | Counter | `message_type` | E2 messages |

### AI/ML Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `drl_training_loss` | Gauge | - | Training loss value |
| `drl_validation_loss` | Gauge | - | Validation loss |
| `drl_model_accuracy` | Gauge | - | Model accuracy (0-1) |
| `drl_inference_latency_seconds` | Histogram | - | Inference latency |
| `drl_inference_requests_total` | Counter | - | Inference requests |
| `drl_inference_errors_total` | Counter | - | Inference errors |
| `drl_training_episodes_total` | Counter | - | Training episodes |
| `nvidia_gpu_duty_cycle` | Gauge | `gpu` | GPU utilization % |
| `nvidia_gpu_memory_used_bytes` | Gauge | `gpu` | GPU memory used |

### Security Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `pqc_operations_total` | Counter | `algorithm`, `operation` | PQC operations |
| `pqc_operation_duration_seconds` | Histogram | `algorithm`, `operation` | Operation latency |
| `pqc_handshake_attempts_total` | Counter | `algorithm` | Handshake attempts |
| `pqc_handshake_failures_total` | Counter | `algorithm` | Handshake failures |
| `pqc_key_rotation_last_timestamp_seconds` | Gauge | `algorithm` | Last rotation time |
| `pqc_certificate_expiry_timestamp_seconds` | Gauge | `algorithm`, `cert_name` | Cert expiry time |
| `tls_active_connections` | Gauge | - | Active TLS connections |
| `tls_encrypted_bytes_total` | Counter | - | Encrypted data volume |

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Prometheus Not Scraping Targets

**Symptoms**: Missing metrics, empty dashboards

**Diagnosis**:
```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open http://localhost:9090/targets

# Check ServiceMonitor
kubectl get servicemonitors -n monitoring
kubectl describe servicemonitor sdr-platform-monitor -n monitoring
```

**Solution**:
```bash
# Verify service labels match ServiceMonitor selector
kubectl get svc -n sdr-platform --show-labels

# Ensure pods expose metrics endpoint
kubectl exec -n sdr-platform <pod-name> -- wget -O- http://localhost:9090/metrics

# Check RBAC permissions
kubectl get clusterrolebinding | grep prometheus
```

#### 2. High Cardinality Metrics

**Symptoms**: Prometheus OOM, slow queries

**Diagnosis**:
```bash
# Check cardinality
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  promtool tsdb analyze /prometheus

# Identify high-cardinality metrics
# In Prometheus UI: http://localhost:9090/tsdb-status
```

**Solution**:
```yaml
# Add metric relabeling in ServiceMonitor
metricRelabelings:
  - sourceLabels: [__name__]
    regex: 'high_cardinality_metric_.*'
    action: drop
```

#### 3. Loki Logs Not Appearing

**Symptoms**: Empty log queries, no log data

**Diagnosis**:
```bash
# Check Promtail status
kubectl get pods -n monitoring -l app.kubernetes.io/name=promtail

# Check Promtail logs
kubectl logs -n monitoring promtail-xxxxx

# Verify Loki is receiving data
kubectl exec -n monitoring loki-0 -- wget -O- http://localhost:3100/metrics | grep loki_ingester_chunks_created_total
```

**Solution**:
```bash
# Restart Promtail
kubectl rollout restart daemonset promtail -n monitoring

# Verify log paths exist
kubectl exec -n monitoring promtail-xxxxx -- ls /var/log/pods/

# Check Promtail config
kubectl get configmap promtail-config -n monitoring -o yaml
```

#### 4. Grafana Dashboard Not Loading Data

**Symptoms**: "No data" message, loading errors

**Diagnosis**:
```bash
# Check Grafana datasource config
kubectl exec -n monitoring prometheus-grafana-xxxxx -- \
  cat /etc/grafana/provisioning/datasources/datasources.yaml

# Test Prometheus connection from Grafana pod
kubectl exec -n monitoring prometheus-grafana-xxxxx -- \
  wget -O- http://prometheus-kube-prometheus-prometheus:9090/-/healthy
```

**Solution**:
1. Go to Grafana → Configuration → Data Sources
2. Test connection to Prometheus and Loki
3. Verify URLs are correct:
   - Prometheus: `http://prometheus-kube-prometheus-prometheus:9090`
   - Loki: `http://loki:3100`

#### 5. Alerts Not Firing

**Symptoms**: No alert notifications, alerts stuck in "Pending"

**Diagnosis**:
```bash
# Check Prometheus rules
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  promtool check rules /etc/prometheus/rules/prometheus-prometheus-rulefiles-0/*.yaml

# View active alerts
# http://localhost:9090/alerts

# Check AlertManager
kubectl logs -n monitoring alertmanager-prometheus-kube-prometheus-alertmanager-0
```

**Solution**:
```bash
# Verify PrometheusRule is loaded
kubectl get prometheusrules -n monitoring

# Check alert expression syntax
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  promtool check rules /path/to/rules.yaml

# Reload Prometheus config
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  kill -HUP 1
```

#### 6. Storage Issues

**Symptoms**: Disk full, write errors

**Diagnosis**:
```bash
# Check PVC usage
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  df -h /prometheus

# Check Loki storage
kubectl exec -n monitoring loki-0 -- df -h /data
```

**Solution**:
```bash
# Expand PVC (if storage class allows)
kubectl patch pvc prometheus-prometheus-kube-prometheus-prometheus-db-prometheus-prometheus-kube-prometheus-prometheus-0 \
  -n monitoring \
  -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Adjust retention period
kubectl edit prometheus -n monitoring
# Set spec.retention to shorter period (e.g., 30d)

# Clean up old data manually (last resort)
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  rm -rf /prometheus/01*  # Remove old blocks
```

---

## Advanced Configuration

### Custom Metric Exporters

#### Creating a Custom Exporter for USRP

```python
# usrp_exporter.py
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import uhd
import time

# Define metrics
throughput_bytes = Counter('sdr_throughput_bytes_total', 'Total throughput in bytes')
packet_loss = Counter('usrp_packet_loss_total', 'Total packet loss')
temperature = Gauge('usrp_temperature_celsius', 'USRP temperature')
latency = Histogram('sdr_e2e_latency_seconds', 'End-to-end latency', buckets=[0.01, 0.05, 0.1, 0.2, 0.5])

def collect_usrp_metrics(usrp):
    """Collect metrics from USRP device"""
    while True:
        # Collect metrics (example)
        stats = usrp.get_stats()
        throughput_bytes.inc(stats['bytes_received'])
        packet_loss.inc(stats['packets_lost'])
        temperature.set(usrp.get_temperature())

        time.sleep(1)

if __name__ == '__main__':
    # Start metrics server
    start_http_server(9090)

    # Connect to USRP
    usrp = uhd.usrp.MultiUSRP("addr=192.168.10.2")

    # Start collection
    collect_usrp_metrics(usrp)
```

Deploy as Kubernetes Deployment with ServiceMonitor.

### High Availability Setup

#### Prometheus HA Configuration

```yaml
# prometheus-ha-values.yaml
prometheus:
  prometheusSpec:
    replicas: 2
    replicaExternalLabelName: prometheus_replica
    prometheusExternalLabelName: cluster
```

#### Loki HA Configuration

```yaml
# loki-ha-values.yaml
loki:
  replicas: 3
  config:
    replication_factor: 3
    ingester:
      lifecycler:
        ring:
          replication_factor: 3
```

### Performance Tuning

#### Prometheus Query Optimization

```yaml
# Increase query concurrency
prometheus:
  prometheusSpec:
    queryLogFile: /var/log/prometheus/queries.log
    queryMaxConcurrency: 20
    queryTimeout: 2m
    lookbackDelta: 5m
```

#### Loki Query Optimization

```yaml
# Optimize log queries
limits_config:
  max_query_parallelism: 32
  max_entries_limit_per_query: 10000
  split_queries_by_interval: 1h
```

### Backup and Recovery

#### Backup Prometheus Data

```bash
# Create snapshot
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Copy snapshot
kubectl cp monitoring/prometheus-prometheus-kube-prometheus-prometheus-0:/prometheus/snapshots/20250127T000000Z-0123456789abcdef0 \
  ./prometheus-backup/
```

#### Restore Prometheus Data

```bash
# Copy data to new Prometheus instance
kubectl cp ./prometheus-backup/ \
  monitoring/prometheus-prometheus-kube-prometheus-prometheus-0:/prometheus/

# Restart Prometheus
kubectl rollout restart statefulset prometheus-prometheus-kube-prometheus-prometheus -n monitoring
```

---

## Best Practices

### 1. Metric Naming Conventions

- **Use consistent prefixes**: `sdr_`, `oran_`, `drl_`, `pqc_`
- **Include units in name**: `_seconds`, `_bytes`, `_total`, `_celsius`
- **Use base units**: seconds (not milliseconds), bytes (not KB)

### 2. Alert Design

- **Use meaningful names**: `HighLEOLatency` not `Alert1`
- **Set appropriate `for` duration**: Avoid flapping
- **Include actionable descriptions**: What to check, how to fix
- **Use severity labels**: `info`, `warning`, `critical`

### 3. Dashboard Organization

- **One dashboard per component**: SDR, O-RAN, AI/ML, Security
- **Include time range variables**: Allow flexible time selection
- **Show percentiles**: P50, P95, P99 for latency metrics
- **Use consistent colors**: Green = good, Yellow = warning, Red = critical

### 4. Log Management

- **Structured logging**: Use JSON format where possible
- **Include trace IDs**: Enable request tracing
- **Set appropriate levels**: DEBUG, INFO, WARN, ERROR
- **Don't log sensitive data**: PII, credentials, keys

### 5. Performance Optimization

- **Use recording rules**: Pre-compute expensive queries
- **Limit cardinality**: Avoid unbounded label values
- **Set retention appropriately**: Balance storage and historical data
- **Use federation**: For multi-cluster scenarios

---

## Security Considerations

### Securing Prometheus

```yaml
# Enable authentication
prometheus:
  prometheusSpec:
    web:
      tlsConfig:
        clientAuthType: RequireAndVerifyClientCert
        clientCAFile: /etc/prometheus/secrets/ca.crt
```

### Securing Grafana

```yaml
# Enable HTTPS
grafana:
  ingress:
    enabled: true
    tls:
      - secretName: grafana-tls
        hosts:
          - grafana.sdr-platform.io

  # Enable RBAC
  rbac:
    create: true
```

### Securing Loki

```yaml
# Enable authentication
loki:
  config:
    auth_enabled: true
    server:
      http_tls_config:
        cert_file: /etc/loki/tls/tls.crt
        key_file: /etc/loki/tls/tls.key
```

---

## Support and Resources

### Documentation Links

- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/grafana/latest/
- **Loki**: https://grafana.com/docs/loki/latest/
- **Prometheus Operator**: https://prometheus-operator.dev/

### Community

- **Prometheus Slack**: https://slack.cncf.io/
- **Grafana Community**: https://community.grafana.com/
- **CNCF**: https://www.cncf.io/

### Contact

For platform-specific issues:
- Email: sdr-ops@company.com
- Slack: #sdr-platform-monitoring

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-27 | Initial release with comprehensive monitoring setup |

---

## License

Copyright © 2025 SDR O-RAN Platform Project. All rights reserved.
