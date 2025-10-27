# SDR Platform Monitoring Dashboards

Grafana dashboards for comprehensive observability of SDR ground station and O-RAN integration.

## Dashboards

### 1. SDR Platform Overview (`sdr-platform-overview.json`)

**Purpose**: High-level operational metrics for SDR ground stations

**Panels**:
- **System Health**: Active stations, availability (NFR-REL-001: 99.9%)
- **Signal Quality**: SNR, receive power per station/band
- **Data Plane**: gRPC throughput, E2E latency (NFR-PERF-001: <100ms)
- **Satellite Tracking**: Doppler shift, antenna pointing accuracy

**Key Metrics**:
```promql
# Active ground stations
count(up{job="sdr-api-gateway"} == 1)

# Average SNR
avg(sdr_signal_snr_db)

# IQ Stream Throughput (Mbps)
sum(rate(sdr_iq_samples_bytes_total[5m])) * 8 / 1e6

# E2E Latency (ms)
avg(sdr_e2e_latency_ms)

# Packet Loss Rate
sum(rate(sdr_grpc_packets_lost_total[5m])) / sum(rate(sdr_grpc_packets_sent_total[5m]))

# 30-day Availability
avg_over_time(up{job="sdr-api-gateway"}[30d])
```

**Alerts**:
- ⚠️ Yellow: SNR <15 dB, Latency >80ms, Loss >0.1%
- 🔴 Red: SNR <10 dB, Latency >100ms, Loss >1%

---

## Installation

### Prerequisites

1. **Prometheus** installed and scraping SDR metrics
2. **Grafana** 8.0+ installed
3. SDR pods annotated with Prometheus scrape configuration:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/metrics"
```

### Import Dashboards

#### Option 1: Grafana UI

1. Navigate to Grafana → Dashboards → Import
2. Upload JSON file: `sdr-platform-overview.json`
3. Select Prometheus datasource
4. Click Import

#### Option 2: Grafana API

```bash
# Set Grafana credentials
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_API_KEY="your-api-key"

# Import dashboard
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @sdr-platform-overview.json \
  $GRAFANA_URL/api/dashboards/db
```

#### Option 3: Kubernetes ConfigMap (GitOps)

```bash
# Create ConfigMap from dashboard JSON
kubectl create configmap grafana-dashboard-sdr-overview \
  --from-file=sdr-platform-overview.json \
  --namespace=monitoring

# Label for Grafana discovery
kubectl label configmap grafana-dashboard-sdr-overview \
  grafana_dashboard=1 \
  --namespace=monitoring
```

**Grafana sidecar will automatically load the dashboard.**

---

## Prometheus Metrics Reference

### Required Metrics (to be exported by SDR components)

```python
# In sdr_api_server.py or sdr_grpc_server.py
from prometheus_client import Counter, Gauge, Histogram

# Signal Quality
sdr_signal_snr_db = Gauge(
    'sdr_signal_snr_db',
    'Signal-to-Noise Ratio in dB',
    ['station_id', 'band', 'satellite']
)

sdr_receive_power_dbm = Gauge(
    'sdr_receive_power_dbm',
    'Received signal power in dBm',
    ['station_id', 'band']
)

# Data Plane Performance
sdr_iq_samples_bytes_total = Counter(
    'sdr_iq_samples_bytes_total',
    'Total bytes of IQ samples streamed',
    ['station_id', 'band']
)

sdr_grpc_packets_sent_total = Counter(
    'sdr_grpc_packets_sent_total',
    'Total gRPC packets sent',
    ['station_id']
)

sdr_grpc_packets_lost_total = Counter(
    'sdr_grpc_packets_lost_total',
    'Total gRPC packets lost',
    ['station_id']
)

sdr_e2e_latency_ms = Histogram(
    'sdr_e2e_latency_ms',
    'End-to-end latency in milliseconds',
    ['station_id'],
    buckets=[10, 25, 50, 75, 100, 150, 200, 300]
)

# Satellite Tracking
sdr_doppler_shift_hz = Gauge(
    'sdr_doppler_shift_hz',
    'Doppler frequency shift in Hz',
    ['station_id', 'satellite']
)

sdr_antenna_pointing_error_deg = Gauge(
    'sdr_antenna_pointing_error_deg',
    'Antenna pointing error in degrees',
    ['station_id']
)

# System Health
up = Gauge(
    'up',
    'System health status (1=up, 0=down)',
    ['job', 'instance']
)
```

### Example Instrumentation

```python
# Update metrics in your code
sdr_signal_snr_db.labels(
    station_id="tokyo-site-001",
    band="Ku-band",
    satellite="LEO-123"
).set(18.5)

sdr_receive_power_dbm.labels(
    station_id="tokyo-site-001",
    band="Ku-band"
).set(-68.2)

sdr_iq_samples_bytes_total.labels(
    station_id="tokyo-site-001",
    band="Ku-band"
).inc(8192 * 4)  # 8192 complex samples @ 4 bytes each

# Measure latency
with sdr_e2e_latency_ms.labels(station_id="tokyo-site-001").time():
    process_iq_batch(batch)
```

---

## Prometheus Alerting Rules

Create `sdr-alerts.yaml`:

```yaml
groups:
  - name: sdr_platform_alerts
    interval: 30s
    rules:
      # Signal Quality Alerts
      - alert: SDRLowSNR
        expr: sdr_signal_snr_db < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low SNR on {{ $labels.station_id }}"
          description: "SNR is {{ $value }} dB (threshold: 10 dB)"

      - alert: SDRWeakSignal
        expr: sdr_receive_power_dbm < -80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Weak signal on {{ $labels.station_id }}"
          description: "Receive power is {{ $value }} dBm"

      # Latency Alerts
      - alert: SDRHighLatency
        expr: avg(sdr_e2e_latency_ms) > 100
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "E2E latency exceeds 100ms (NFR-PERF-001)"
          description: "Latency is {{ $value }} ms on {{ $labels.station_id }}"

      # Packet Loss Alerts
      - alert: SDRHighPacketLoss
        expr: |
          sum(rate(sdr_grpc_packets_lost_total[5m])) /
          sum(rate(sdr_grpc_packets_sent_total[5m])) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High packet loss detected"
          description: "Packet loss rate is {{ $value | humanizePercentage }}"

      # Availability Alerts
      - alert: SDRStationDown
        expr: up{job="sdr-api-gateway"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "SDR station {{ $labels.instance }} is down"
          description: "Ground station has been unreachable for 1 minute"

      - alert: SDRLowAvailability
        expr: avg_over_time(up{job="sdr-api-gateway"}[1h]) < 0.999
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "SDR availability below 99.9% (NFR-REL-001)"
          description: "Availability is {{ $value | humanizePercentage }}"

      # Satellite Tracking Alerts
      - alert: SDRAntennaPointingError
        expr: sdr_antenna_pointing_error_deg > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Antenna pointing error on {{ $labels.station_id }}"
          description: "Pointing error is {{ $value }}° (threshold: 1.0°)"
```

Apply alerts:

```bash
kubectl apply -f sdr-alerts.yaml -n monitoring
```

---

## Integration with Alertmanager

Configure Prometheus to send alerts to Alertmanager:

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yaml

scrape_configs:
  - job_name: 'sdr-api-gateway'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - sdr-platform
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
```

---

## Customize Dashboards

### Add New Panel

1. Edit dashboard in Grafana UI
2. Add Panel → Select visualization type
3. Configure PromQL query:

```promql
# Example: USRP device temperature
sdr_usrp_temperature_celsius
```

4. Set thresholds, alerts, and display options
5. Save dashboard

### Export Updated Dashboard

```bash
# Get dashboard JSON via API
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  $GRAFANA_URL/api/dashboards/uid/sdr-platform-overview \
  | jq '.dashboard' > sdr-platform-overview-updated.json
```

---

## Multi-Cluster Federation

For monitoring multiple edge sites from central Grafana:

### Prometheus Federation

```yaml
# Central Prometheus scrapes edge Prometheus instances
scrape_configs:
  - job_name: 'federate-tokyo'
    scrape_interval: 30s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="sdr-api-gateway"}'
        - '{__name__=~"sdr_.*"}'
    static_configs:
      - targets:
          - 'prometheus.tokyo-edge.svc.cluster.local:9090'
        labels:
          site: 'tokyo'

  - job_name: 'federate-london'
    scrape_interval: 30s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="sdr-api-gateway"}'
        - '{__name__=~"sdr_.*"}'
    static_configs:
      - targets:
          - 'prometheus.london-edge.svc.cluster.local:9090'
        labels:
          site: 'london'
```

### Thanos for Long-term Storage

```bash
# Deploy Thanos sidecar with Prometheus
helm install thanos-sidecar bitnami/thanos \
  --set querier.enabled=true \
  --set storegateway.enabled=true \
  --set compactor.enabled=true \
  --namespace monitoring
```

---

## Troubleshooting

### Metrics Not Showing

1. **Verify Prometheus scraping**:

```bash
# Check targets
curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="sdr-api-gateway")'

# Check if metrics exist
curl http://prometheus:9090/api/v1/query?query=up{job="sdr-api-gateway"}
```

2. **Check pod annotations**:

```bash
kubectl get pods -n sdr-platform -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations}{"\n"}{end}'
```

3. **Verify metrics endpoint**:

```bash
kubectl port-forward -n sdr-platform sdr-api-gateway-xxxxx 8080:8080
curl http://localhost:8080/metrics | grep sdr_
```

### Dashboard Not Loading

1. **Check Grafana logs**:

```bash
kubectl logs -n monitoring deployment/grafana
```

2. **Verify datasource**:

```bash
# Test Prometheus datasource
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  $GRAFANA_URL/api/datasources
```

3. **Re-import dashboard with updated UID**.

---

## References

- **NFR-PERF-001**: E2E latency <100ms
- **NFR-REL-001**: 99.9% availability
- **NFR-INT-003**: Prometheus/Grafana monitoring integration
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)

---

**Status**: ✅ **READY** - Production-ready monitoring dashboards

**Last Updated**: 2025-10-27
**Author**: thc1006@ieee.org
