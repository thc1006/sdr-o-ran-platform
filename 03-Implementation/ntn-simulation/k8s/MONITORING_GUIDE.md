# NTN-O-RAN Monitoring Guide

Complete guide to monitoring the NTN-O-RAN platform using Prometheus and Grafana.

## Table of Contents

1. [Overview](#overview)
2. [Metrics Architecture](#metrics-architecture)
3. [Grafana Dashboards](#grafana-dashboards)
4. [Prometheus Queries](#prometheus-queries)
5. [Alerts](#alerts)
6. [Performance Baselines](#performance-baselines)

## Overview

The monitoring stack provides comprehensive observability:
- **Prometheus**: Time-series metrics collection (15s scrape interval)
- **Grafana**: Visual dashboards and alerts
- **Metrics**: Application, infrastructure, and business metrics

## Metrics Architecture

### Metrics Collected

#### E2 Interface Metrics
- `e2_messages_total` - Total E2 messages (counter)
- `e2_message_latency_ms` - E2E message latency (histogram)
- `e2_errors_total` - E2 errors by type (counter)
- `e2_indication_messages_total` - RIC indication messages (counter)
- `e2_control_actions_total` - Control actions by type (counter)
- `e2_asn1_encoding_duration_ms` - ASN.1 encoding time (histogram)
- `e2_message_size_bytes` - Message size distribution (histogram)
- `e2_connected_nodes` - Number of connected E2 nodes (gauge)
- `e2_subscription_success_total` - Successful subscriptions (counter)
- `e2_subscription_failure_total` - Failed subscriptions (counter)

#### Satellite Metrics
- `satellite_total_tracked` - Total satellites tracked (gauge)
- `satellite_visible_count` - Currently visible satellites (gauge)
- `satellite_active_connections` - Active satellite connections (gauge)
- `satellite_elevation_degrees` - Elevation angle per satellite (gauge)
- `satellite_doppler_shift_hz` - Doppler shift per satellite (gauge)
- `satellite_rsrp_dbm` - Reference Signal Received Power (gauge)
- `satellite_sinr_db` - Signal-to-Interference-plus-Noise Ratio (gauge)
- `satellite_handover_total` - Total handover events (counter)
- `satellite_handover_success_total` - Successful handovers (counter)
- `satellite_handover_failure_total` - Failed handovers (counter)

#### xApp Metrics
- `handover_prediction_accuracy_percent` - ML prediction accuracy (gauge)
- `handover_decision_latency_ms` - Handover decision time (histogram)
- `handover_success_total` - Successful handovers (counter)
- `handover_failure_total` - Failed handovers (counter)
- `power_consumption_watts` - Current power consumption (gauge)
- `power_target_watts` - Target power level (gauge)
- `power_xapp_rsrp_dbm` - Maintained RSRP level (gauge)
- `power_xapp_rsrp_target_dbm` - Target RSRP level (gauge)
- `power_adjustments_total` - Power adjustment actions (counter)
- `xapp_processing_time_ms` - xApp processing latency (histogram)
- `xapp_requests_total` - xApp requests by type (counter)
- `xapp_errors_total` - xApp errors by type (counter)

#### Infrastructure Metrics
- `container_cpu_usage_seconds_total` - CPU usage per container
- `container_memory_usage_bytes` - Memory usage per container
- `kube_pod_container_status_restarts_total` - Pod restart count
- `kube_deployment_status_replicas` - Deployment replica status

## Grafana Dashboards

### 1. NTN-O-RAN System Overview

**Purpose**: High-level system health and performance

**Key Panels**:
- Pod health (running/total)
- Average E2E latency (target: <5.5ms)
- Message throughput (target: >600 msg/s)
- Error rate
- CPU/Memory usage by service
- Pod restarts

**Alerts**:
- Latency > 10ms for 5 minutes
- Error rate > 5% for 5 minutes
- Pod restarts > 3 in 1 hour

**Access**:
```bash
kubectl port-forward -n ntn-oran svc/grafana-service 3000:3000
# Navigate to: Dashboards -> NTN-O-RAN -> System Overview
```

### 2. E2 Interface Metrics

**Purpose**: Deep dive into E2 interface performance

**Key Panels**:
- E2 message rate by type (Indication, Control, Subscription)
- Control actions (Handover, Power Adjust, Beam Switch)
- ASN.1 encoding time (p50, p95, p99)
- Message size distribution
- E2 connection status
- Error types breakdown
- Subscription success rate

**Use Cases**:
- Troubleshooting E2 connection issues
- Analyzing message patterns
- Identifying encoding bottlenecks

### 3. Satellite Tracking Dashboard

**Purpose**: Monitor satellite constellation and handover performance

**Key Panels**:
- Total satellites tracked (target: 8,805)
- Visible satellites
- Active connections
- Elevation angles over time
- Doppler shift
- RSRP (signal strength)
- SINR (signal quality)
- Handover event rate
- Handover success rate

**Alerts**:
- RSRP < -100 dBm (weak signal)
- Handover failure rate > 10%
- No visible satellites

**Use Cases**:
- Satellite visibility analysis
- Handover prediction validation
- Link quality monitoring

### 4. xApp Performance Dashboard

**Purpose**: Monitor xApp ML/optimization performance

**Key Panels**:
- Handover prediction accuracy (target: >90%)
- Handover decision latency
- Power consumption vs target
- RSRP maintenance
- xApp request rate
- xApp error rate
- Processing time distribution

**Alerts**:
- Prediction accuracy < 85%
- Processing time > 20ms

**Use Cases**:
- ML model performance tracking
- Power optimization validation
- xApp health monitoring

## Prometheus Queries

### Common Queries

**Average E2E Latency:**
```promql
avg(e2_message_latency_ms)
```

**Message Throughput (msg/s):**
```promql
sum(rate(e2_messages_total[1m]))
```

**Error Rate (%):**
```promql
sum(rate(e2_errors_total[5m])) / sum(rate(e2_messages_total[5m])) * 100
```

**Handover Success Rate:**
```promql
rate(satellite_handover_success_total[5m]) /
(rate(satellite_handover_success_total[5m]) + rate(satellite_handover_failure_total[5m])) * 100
```

**CPU Usage by Pod:**
```promql
rate(container_cpu_usage_seconds_total{namespace="ntn-oran"}[5m])
```

**Memory Usage by Pod:**
```promql
container_memory_usage_bytes{namespace="ntn-oran"} / 1024 / 1024
```

**Pod Restart Count:**
```promql
kube_pod_container_status_restarts_total{namespace="ntn-oran"}
```

### Advanced Queries

**95th Percentile Latency:**
```promql
histogram_quantile(0.95, rate(e2_message_latency_ms_bucket[5m]))
```

**Top 5 Error Types:**
```promql
topk(5, sum by (error_type) (rate(e2_errors_total[5m])))
```

**Satellites Above 30° Elevation:**
```promql
count(satellite_elevation_degrees > 30)
```

**Average Handover Prediction Accuracy (24h):**
```promql
avg_over_time(handover_prediction_accuracy_percent[24h])
```

## Alerts

### Critical Alerts

```yaml
# High Latency
alert: HighE2Latency
expr: avg(e2_message_latency_ms) > 10
for: 5m
severity: critical
description: E2E latency exceeds 10ms (target: 5.5ms)

# High Error Rate
alert: HighErrorRate
expr: sum(rate(e2_errors_total[5m])) / sum(rate(e2_messages_total[5m])) > 0.05
for: 5m
severity: critical
description: Error rate exceeds 5%

# Service Down
alert: ServiceDown
expr: up{job="e2-termination"} == 0
for: 1m
severity: critical
description: E2 Termination service is down

# Low RSRP
alert: WeakSignal
expr: avg(satellite_rsrp_dbm) < -100
for: 10m
severity: warning
description: Average RSRP below -100 dBm
```

### Warning Alerts

```yaml
# Low Prediction Accuracy
alert: LowPredictionAccuracy
expr: handover_prediction_accuracy_percent < 85
for: 15m
severity: warning
description: Handover prediction accuracy below 85%

# High Pod Restarts
alert: HighPodRestarts
expr: increase(kube_pod_container_status_restarts_total[1h]) > 3
for: 5m
severity: warning
description: Pod restarted more than 3 times in 1 hour
```

## Performance Baselines

### Expected Performance

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| E2E Latency | <5.5ms | <10ms | >15ms |
| Message Throughput | >600 msg/s | >400 msg/s | <200 msg/s |
| Error Rate | <1% | <5% | >10% |
| Handover Success Rate | >95% | >90% | <85% |
| Prediction Accuracy | >90% | >85% | <80% |
| CPU Usage (per pod) | <50% | <70% | >90% |
| Memory Usage | <50% | <80% | >95% |

### Capacity Planning

**Current Capacity:**
- E2 Termination: 2 replicas (can scale to 5)
- Handover xApp: 2 replicas (can scale to 5)
- Power xApp: 2 replicas (can scale to 5)

**Scaling Triggers:**
- CPU > 70% for 5 minutes
- Memory > 80% for 5 minutes

**Expected Load:**
- 8,805 satellites tracked
- ~600 messages/second
- ~10-20 handovers/minute

## Best Practices

1. **Regular Monitoring**
   - Check dashboards daily
   - Review alerts weekly
   - Analyze trends monthly

2. **Baseline Updates**
   - Update baselines after major changes
   - Document performance improvements
   - Track degradation patterns

3. **Alert Tuning**
   - Adjust thresholds based on actual performance
   - Reduce false positives
   - Ensure critical alerts are actionable

4. **Dashboard Customization**
   - Create team-specific dashboards
   - Add business-relevant metrics
   - Share insights across teams

## Accessing Metrics

### Via Grafana UI
```bash
kubectl port-forward -n ntn-oran svc/grafana-service 3000:3000
# Open: http://localhost:3000
```

### Via Prometheus UI
```bash
kubectl port-forward -n ntn-oran svc/prometheus-service 9090:9090
# Open: http://localhost:9090
```

### Via kubectl (Pod metrics)
```bash
kubectl top pods -n ntn-oran
kubectl top nodes
```

## Troubleshooting

**Metrics not showing:**
- Check Prometheus targets: http://localhost:9090/targets
- Verify pod annotations: `prometheus.io/scrape: "true"`
- Check service endpoints

**Dashboard empty:**
- Verify Prometheus datasource in Grafana
- Check time range selection
- Ensure pods are running

**High latency:**
- Check CPU/memory usage
- Review error logs
- Analyze network latency
