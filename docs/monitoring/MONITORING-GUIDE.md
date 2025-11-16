# SDR-O-RAN Platform - Monitoring and Observability Guide

**Version:** 1.0.0
**Date:** 2025-11-17
**Author:** Agent 4 - Monitoring Infrastructure & Deployment Specialist

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Prometheus Metrics Catalog](#prometheus-metrics-catalog)
5. [Grafana Dashboards](#grafana-dashboards)
6. [Alert Configuration](#alert-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Performance Tuning](#performance-tuning)

---

## Overview

This guide provides comprehensive documentation for monitoring the SDR-O-RAN Platform using Prometheus and Grafana. The monitoring stack provides:

- **Real-time Metrics Collection**: Prometheus scrapes metrics from all platform components
- **Visualization**: Grafana dashboards for comprehensive system insights
- **Alerting**: Prometheus alerting rules for critical system events
- **Service Discovery**: Automatic detection of monitoring endpoints

### Components

| Component | Purpose | Port | URL |
|-----------|---------|------|-----|
| Prometheus | Metrics collection and storage | 9090 | http://localhost:9090 |
| Grafana | Metrics visualization | 3002 | http://localhost:3002 |
| gRPC Server | gRPC metrics endpoint | 8000 | http://localhost:8000/metrics |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Grafana Dashboard                      │
│              http://localhost:3002                       │
│         (Username: admin, Password: admin)               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ PromQL Queries
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   Prometheus Server                      │
│              http://localhost:9090                       │
│         - Metrics Storage (TSDB)                         │
│         - Alert Evaluation                               │
│         - Service Discovery                              │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼───────┐ ┌────▼────┐ ┌──────▼───────┐
│  SDR Gateway  │ │   DRL   │ │     LEO      │
│  :8000/metrics│ │  Trainer│ │  Simulator   │
└───────────────┘ └─────────┘ └──────────────┘
```

---

## Quick Start

### 1. Start Monitoring Services

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform

# Start Prometheus and Grafana
docker compose up -d prometheus grafana

# Verify services are running
docker compose ps | grep -E "(prometheus|grafana)"
```

### 2. Access Dashboards

**Prometheus UI:**
- URL: http://localhost:9090
- No authentication required
- Use the Explore tab to query metrics

**Grafana UI:**
- URL: http://localhost:3002
- Username: `admin`
- Password: `admin` (change on first login)
- Pre-configured dashboards under "SDR-O-RAN Platform"

### 3. Test Metrics Endpoints

```bash
# Test Prometheus health
curl http://localhost:9090/-/healthy

# Test Grafana health
curl http://localhost:3002/api/health

# Test gRPC server metrics (when running)
curl http://localhost:8000/metrics
```

---

## Prometheus Metrics Catalog

### gRPC Server Metrics

#### Request Metrics

**`grpc_requests_total`** (Counter)
- **Description**: Total number of gRPC requests
- **Labels**: `method`, `status`
- **Example PromQL**:
  ```promql
  rate(grpc_requests_total{status="success"}[5m])
  ```

**`grpc_request_duration_seconds`** (Histogram)
- **Description**: gRPC request duration in seconds
- **Labels**: `method`
- **Buckets**: 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0
- **Example PromQL** (P95 latency):
  ```promql
  histogram_quantile(0.95, sum(rate(grpc_request_duration_seconds_bucket[5m])) by (method, le))
  ```

#### IQ Stream Metrics

**`active_iq_streams`** (Gauge)
- **Description**: Number of active IQ streams
- **Example PromQL**:
  ```promql
  active_iq_streams
  ```

**`iq_samples_total`** (Counter)
- **Description**: Total IQ samples processed
- **Labels**: `station_id`
- **Example PromQL** (sample rate):
  ```promql
  rate(iq_samples_total[5m])
  ```

**`iq_throughput_mbps`** (Gauge)
- **Description**: IQ data throughput in Mbps
- **Labels**: `station_id`
- **Example PromQL**:
  ```promql
  iq_throughput_mbps{station_id="test-station-1"}
  ```

#### Performance Metrics

**`packet_loss_rate`** (Gauge)
- **Description**: Packet loss rate (0.0 to 1.0)
- **Labels**: `station_id`
- **Alert Threshold**: > 0.01 (1%)
- **Example PromQL**:
  ```promql
  packet_loss_rate > 0.01
  ```

**`average_latency_ms`** (Gauge)
- **Description**: Average processing latency in milliseconds
- **Labels**: `station_id`
- **LEO Target**: < 100ms
- **GEO Target**: < 350ms
- **Example PromQL**:
  ```promql
  average_latency_ms{station_id="test-station-1"}
  ```

---

## Grafana Dashboards

### SDR-O-RAN Platform - gRPC Metrics Dashboard

**Location**: Pre-provisioned in Grafana
**UID**: `sdr-oran-grpc`

#### Panels

1. **gRPC Request Rate**
   - **Type**: Time Series
   - **Query**: `rate(grpc_requests_total[5m])`
   - **Breakdown**: By method and status

2. **gRPC Request Duration (P95/P99)**
   - **Type**: Time Series
   - **Query**:
     - P95: `histogram_quantile(0.95, sum(rate(grpc_request_duration_seconds_bucket[5m])) by (method, le))`
     - P99: `histogram_quantile(0.99, sum(rate(grpc_request_duration_seconds_bucket[5m])) by (method, le))`
   - **Thresholds**: Yellow at 0.1s, Red at 0.15s

3. **Active IQ Streams**
   - **Type**: Gauge
   - **Query**: `active_iq_streams`
   - **Thresholds**: Red < 1, Yellow = 1, Green >= 2

4. **IQ Samples Processed Rate**
   - **Type**: Time Series
   - **Query**: `rate(iq_samples_total[5m]) * 8`
   - **Unit**: Bytes per second

5. **IQ Throughput**
   - **Type**: Time Series
   - **Query**: `iq_throughput_mbps`
   - **Thresholds**: Yellow at 50 Mbps, Red at 80 Mbps

6. **Packet Loss Rate**
   - **Type**: Time Series
   - **Query**: `packet_loss_rate`
   - **Thresholds**: Yellow at 0.1%, Red at 1%

7. **Average Latency**
   - **Type**: Time Series
   - **Query**: `average_latency_ms`
   - **Thresholds**: Yellow at 100ms, Red at 150ms

### Customizing Dashboards

1. Log into Grafana (http://localhost:3002)
2. Navigate to Dashboards → SDR-O-RAN Platform
3. Click the gear icon (⚙) to edit
4. Add new panels using the "Add panel" button
5. Save changes with "Save dashboard"

---

## Alert Configuration

### Recommended Alert Rules

Create `/home/gnb/thc1006/sdr-o-ran-platform/04-Deployment/prometheus/alert-rules.yml`:

```yaml
groups:
  - name: sdr_oran_alerts
    interval: 30s
    rules:
      # High packet loss
      - alert: HighPacketLoss
        expr: packet_loss_rate > 0.01
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High packet loss detected"
          description: "Station {{ $labels.station_id }} has {{ $value | humanizePercentage }} packet loss"

      # High latency (LEO)
      - alert: HighLatencyLEO
        expr: average_latency_ms > 100
        for: 5m
        labels:
          severity: warning
          orbit: LEO
        annotations:
          summary: "LEO latency exceeds target"
          description: "Station {{ $labels.station_id }} latency is {{ $value }}ms (target: <100ms)"

      # No active streams
      - alert: NoActiveStreams
        expr: active_iq_streams == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "No active IQ streams"
          description: "Zero IQ streams are currently active"

      # Low throughput
      - alert: LowThroughput
        expr: iq_throughput_mbps < 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low IQ throughput"
          description: "Station {{ $labels.station_id }} throughput is {{ $value }}Mbps (target: 80-95 Mbps)"

      # High error rate
      - alert: HighErrorRate
        expr: rate(grpc_requests_total{status="error"}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High gRPC error rate"
          description: "Method {{ $labels.method }} error rate: {{ $value | humanize }} req/s"
```

### Enabling Alerts

1. Add alert rules to Prometheus configuration:

```yaml
# prometheus.yml
rule_files:
  - "alert-rules.yml"
```

2. Restart Prometheus:

```bash
docker compose restart prometheus
```

3. View alerts at: http://localhost:9090/alerts

---

## Troubleshooting

### Common Issues

#### 1. Prometheus Cannot Scrape Targets

**Symptom**: Targets show as "DOWN" in Prometheus UI

**Solutions**:
- Verify the service is running: `docker compose ps`
- Check network connectivity: `docker network inspect sdr-o-ran-platform_oran-network`
- Verify metrics endpoint: `curl http://<service>:<port>/metrics`
- Check Prometheus logs: `docker logs prometheus`

#### 2. Grafana Dashboard Shows No Data

**Symptom**: Panels display "No data"

**Solutions**:
- Verify Prometheus datasource: Grafana → Configuration → Data Sources
- Test the datasource connection
- Check time range (top-right corner)
- Verify PromQL query syntax in panel edit mode
- Ensure metrics are being scraped: http://localhost:9090/targets

#### 3. Permission Denied Errors

**Symptom**: Containers fail to start with permission errors

**Solutions**:
```bash
# Fix configuration file permissions
chmod 644 /home/gnb/thc1006/sdr-o-ran-platform/04-Deployment/prometheus/prometheus.yml
chmod 644 /home/gnb/thc1006/sdr-o-ran-platform/04-Deployment/grafana/datasources/prometheus.yml
chmod 644 /home/gnb/thc1006/sdr-o-ran-platform/04-Deployment/grafana/dashboards/*.yml
chmod 644 /home/gnb/thc1006/sdr-o-ran-platform/04-Deployment/grafana/dashboards/*.json

# Restart services
docker compose restart prometheus grafana
```

#### 4. Port Already in Use

**Symptom**: Container fails to start with "port is already allocated"

**Solutions**:
```bash
# Check what's using the port
sudo lsof -i :<port>

# Option 1: Stop the conflicting service
# Option 2: Change port in docker-compose.yml
```

### Debugging Commands

```bash
# View Prometheus configuration
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# View Grafana logs
docker logs grafana --tail 50

# Test metrics endpoint manually
curl http://localhost:8000/metrics

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

---

## Performance Tuning

### Prometheus Optimization

#### 1. Scrape Interval Tuning

For high-frequency IQ streaming, use shorter intervals:

```yaml
scrape_configs:
  - job_name: 'sdr-gateway'
    scrape_interval: 5s  # More frequent scraping
    scrape_timeout: 3s
```

#### 2. Retention Policy

Adjust data retention based on storage capacity:

```yaml
# docker-compose.yml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.retention.time=30d'  # Keep 30 days of data
  - '--storage.tsdb.retention.size=50GB'  # Max 50GB storage
```

#### 3. Query Performance

- Use recording rules for frequently accessed queries
- Limit time ranges for heavy queries
- Use rate() instead of irate() for stable metrics

### Grafana Optimization

#### 1. Dashboard Performance

- Limit the number of panels per dashboard (< 20 recommended)
- Use appropriate refresh intervals (10s-30s)
- Avoid overly complex PromQL queries

#### 2. Data Source Settings

```yaml
# datasources/prometheus.yml
jsonData:
  httpMethod: POST          # Faster for complex queries
  timeInterval: 15s         # Match Prometheus scrape interval
  queryTimeout: 60s         # Timeout for long queries
```

### Metrics Export Optimization

#### 1. gRPC Server Tuning

In `sdr_grpc_server.py`:

```python
# Adjust histogram buckets for your use case
grpc_request_duration = Histogram(
    'grpc_request_duration_seconds',
    'gRPC request duration',
    ['method'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5, 1.0)
)

# Start metrics server on separate port
start_metrics_server(port=8000)
```

#### 2. Metric Cardinality

- Limit the number of unique label values
- Avoid high-cardinality labels (user IDs, timestamps)
- Use label aggregation when possible

---

## Monitoring Best Practices

### 1. SLO/SLI Definition

| Service Level Indicator (SLI) | Target (LEO) | Target (GEO) |
|-------------------------------|--------------|--------------|
| E2E Latency (P95) | < 100ms | < 350ms |
| Throughput | 80-95 Mbps | 80-95 Mbps |
| Packet Loss | < 0.1% | < 0.1% |
| Availability | > 99.9% | > 99.9% |

### 2. Alert Fatigue Prevention

- Set appropriate thresholds and durations
- Use severity levels (critical, warning, info)
- Implement alert grouping and routing
- Review and tune alerts regularly

### 3. Dashboard Organization

- Create role-specific dashboards (operator, developer, SRE)
- Use consistent naming conventions
- Document panel purposes and queries
- Version control dashboard JSON files

### 4. Capacity Planning

Monitor these metrics for capacity planning:
- CPU and memory usage (via node-exporter)
- Disk I/O and storage growth
- Network bandwidth utilization
- Container resource limits

---

## Additional Resources

### Prometheus Documentation
- Official docs: https://prometheus.io/docs/
- PromQL guide: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Best practices: https://prometheus.io/docs/practices/naming/

### Grafana Documentation
- Official docs: https://grafana.com/docs/
- Dashboard creation: https://grafana.com/docs/grafana/latest/dashboards/
- Provisioning: https://grafana.com/docs/grafana/latest/administration/provisioning/

### Platform-Specific
- SDR-O-RAN Architecture: `/home/gnb/thc1006/sdr-o-ran-platform/01-Architecture-Analysis/`
- Deployment Guide: `/home/gnb/thc1006/sdr-o-ran-platform/06-Deployment-Operations/`
- Testing Guide: `/home/gnb/thc1006/sdr-o-ran-platform/TESTING_GUIDE.md`

---

## Support and Contributions

For issues, questions, or contributions related to monitoring:

1. Check the troubleshooting section above
2. Review existing documentation in `/docs/monitoring/`
3. Submit issues via the project issue tracker
4. Contact: thc1006@ieee.org

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-17
**Maintained By**: Platform Monitoring Team
