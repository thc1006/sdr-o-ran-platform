# SDR-O-RAN Platform Operations Guide

Day-to-day operations, maintenance, and troubleshooting procedures.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Monitoring and Alerting](#monitoring-and-alerting)
3. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
4. [Scaling Operations](#scaling-operations)
5. [Security Operations](#security-operations)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Incident Response](#incident-response)
8. [Performance Optimization](#performance-optimization)

---

## Daily Operations

### Morning Checklist

```bash
# 1. Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running

# 2. Verify SDR stations
kubectl get pods -n sdr-platform
kubectl logs -n sdr-platform deployment/sdr-api-gateway --tail=50

# 3. Check gRPC streaming
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    python -c "from sdr_grpc_server import IQStreamServicer; \
    s = IQStreamServicer(); \
    print(f'Active streams: {len(s.active_streams)}')"

# 4. Review Grafana dashboards
# Navigate to: http://grafana.example.com/d/sdr-platform-overview

# 5. Check Prometheus alerts
curl -s http://prometheus.example.com/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
```

### Satellite Pass Management

#### Pre-Pass Checklist (30 minutes before AOS)

```bash
# 1. Verify TLE is up-to-date
TLE_AGE=$(python -c "
from datetime import datetime
import subprocess
tle_date = subprocess.check_output(['grep', 'EPOCH', '/etc/sdr/tle/active.tle']).decode()
age = (datetime.now() - datetime.strptime(tle_date[-14:], '%y%j.%f')).days
print(age)
")

if [ $TLE_AGE -gt 3 ]; then
    echo "WARNING: TLE older than 3 days. Update recommended."
    # Update TLE from CelesTrak
    curl https://celestrak.org/NORAD/elements/gp.php?GROUP=active\&FORMAT=tle \
        > /etc/sdr/tle/active.tle
fi

# 2. Pre-heat USRP hardware
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    uhd_usrp_probe --args="type=x310"

# 3. Verify antenna controller
echo "P" | nc localhost 4533  # Query position

# 4. Start spectrum monitoring
kubectl port-forward -n sdr-platform svc/sdr-grpc-server 50051:50051 &
python -c "
from oran_grpc_client import ORANIQClient
client = ORANIQClient('localhost:50051', 'ground-station-1')
spectrum = client.get_spectrum(center_freq_hz=12e9, span_hz=100e6)
print(f'Peak at {spectrum.peak_frequency_hz/1e9:.4f} GHz, {spectrum.peak_power_dbm:.2f} dBm')
"
```

#### During Pass

```bash
# Monitor real-time metrics
watch -n 5 'kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    python -c "
from sdr_grpc_server import IQStreamServicer
s = IQStreamServicer()
for station_id, stats in s.statistics.items():
    print(f\"{station_id}: {stats.average_throughput_mbps:.2f} Mbps, \
          {stats.average_latency_ms:.2f} ms, \
          Loss: {stats.packet_loss_rate*100:.3f}%\")
"'
```

#### Post-Pass Checklist

```bash
# 1. Verify data capture
DATA_DIR="/mnt/sdr-data/$(date +%Y%m%d)"
ls -lh $DATA_DIR

# 2. Check for errors in logs
kubectl logs -n sdr-platform deployment/sdr-grpc-server --since=1h | grep ERROR

# 3. Archive I/Q samples
tar -czf $DATA_DIR/iq-samples-$(date +%H%M).tar.gz $DATA_DIR/*.bin
rsync -avz $DATA_DIR/ backup-server:/backups/sdr-data/

# 4. Update pass log
cat <<EOF >> /var/log/sdr/pass-log.csv
$(date -Iseconds),PASS_SUCCESS,LEO-123,12.5,18.2,95.3,0.001
EOF
```

---

## Monitoring and Alerting

### Key Performance Indicators (KPIs)

| Metric | Target | Alert Threshold | Critical Threshold |
|--------|--------|-----------------|-------------------|
| **E2E Latency** | <75ms | >80ms | >100ms |
| **SNR** | >15 dB | <12 dB | <10 dB |
| **Packet Loss** | <0.01% | >0.1% | >1.0% |
| **Availability** | >99.9% | <99.5% | <99.0% |
| **Throughput** | >90 Mbps | <80 Mbps | <70 Mbps |

### Alert Response Procedures

#### Critical Alert: E2E Latency >100ms

```bash
# 1. Identify latency source
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    python -c "
import time
start = time.time()
# Test GNU Radio processing latency
print(f'GNU Radio: {(time.time() - start) * 1000:.2f} ms')

start = time.time()
# Test gRPC latency
print(f'gRPC: {(time.time() - start) * 1000:.2f} ms')

start = time.time()
# Test O-RAN processing latency
print(f'O-RAN: {(time.time() - start) * 1000:.2f} ms')
"

# 2. Check network latency
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    ping -c 10 oran-iq-client.oran-platform.svc.cluster.local | \
    grep "avg"

# 3. Reduce gRPC batch size if needed
# Edit config: batch_size=4096

# 4. Check CPU usage
kubectl top pods -n sdr-platform
```

#### Warning Alert: Low SNR (<12 dB)

```bash
# 1. Check antenna pointing
echo "P" | nc localhost 4533

# 2. Verify LNA power supply
# Physical check required

# 3. Check for interference
kubectl port-forward -n sdr-platform svc/sdr-grpc-server 50051:50051
python -c "
from oran_grpc_client import ORANIQClient
client = ORANIQClient('localhost:50051', 'ground-station-1')
spectrum = client.get_spectrum(center_freq_hz=12e9, span_hz=500e6, fft_size=4096)
# Analyze spectrum for interference
"

# 4. Adjust AGC if necessary
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    python -c "
from dvbs2_multiband_receiver import DVBS2Receiver
receiver = DVBS2Receiver(band='Ku-band', simulate=False)
# Adjust AGC target
"
```

---

## Backup and Disaster Recovery

### Backup Strategy

| Data Type | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| **Configuration** | Daily | 30 days | Git + Velero |
| **I/Q Samples** | Per pass | 90 days | rsync to NAS |
| **Logs** | Continuous | 7 days | ELK Stack |
| **Metrics** | Continuous | 30 days | Prometheus |
| **TLE Data** | Daily | Forever | Git |

### Automated Backup Script

```bash
#!/bin/bash
# /usr/local/bin/sdr-backup.sh

BACKUP_DIR="/mnt/backups/sdr-platform"
DATE=$(date +%Y%m%d-%H%M)

# 1. Backup Kubernetes resources
echo "Backing up Kubernetes resources..."
velero backup create sdr-platform-$DATE \
    --include-namespaces sdr-platform \
    --wait

# 2. Backup I/Q data
echo "Backing up I/Q samples..."
rsync -avz --progress /mnt/sdr-data/ \
    backup-server:/backups/sdr-data/ \
    --log-file=/var/log/sdr/backup.log

# 3. Backup configuration files
echo "Backing up configurations..."
tar -czf $BACKUP_DIR/config-$DATE.tar.gz \
    /etc/sdr/ \
    /etc/oai/ \
    ~/.kube/

# 4. Export metrics
echo "Exporting metrics..."
curl -s "http://prometheus.example.com/api/v1/query_range?\
query=sdr_signal_snr_db&\
start=$(date -d '1 day ago' +%s)&\
end=$(date +%s)&\
step=60" \
    > $BACKUP_DIR/metrics-$DATE.json

# 5. Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Disaster Recovery Procedures

#### Scenario 1: Complete Site Failure

```bash
# 1. Deploy to alternate site
cd 03-Implementation/orchestration/nephio/packagevariants

# Update PackageVariant for DR site
kubectl apply -f disaster-recovery-site.yaml

# 2. Wait for deployment
kubectl wait --for=condition=ready \
    packagevariant/sdr-platform-dr-site \
    -n nephio-system \
    --timeout=10m

# 3. Restore data from backup
velero restore create --from-backup sdr-platform-latest

# 4. Update DNS to point to DR site
# Manual DNS update required

# 5. Verify operation
kubectl get pods -n sdr-platform --context dr-site
```

#### Scenario 2: USRP Hardware Failure

```bash
# 1. Identify failed USRP
uhd_find_devices

# 2. Swap to backup USRP
# Physical swap required

# 3. Update Kubernetes node label
kubectl label nodes worker-node-2 hardware.sdr/usrp=true --overwrite

# 4. Restart gRPC server
kubectl rollout restart deployment/sdr-grpc-server -n sdr-platform

# 5. Verify new USRP
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    uhd_usrp_probe
```

---

## Scaling Operations

### Horizontal Scaling

```bash
# Scale API Gateway replicas
kubectl scale deployment sdr-api-gateway \
    --replicas=5 \
    -n sdr-platform

# Verify HPA (Horizontal Pod Autoscaler)
kubectl get hpa -n sdr-platform
kubectl describe hpa sdr-api-gateway-hpa
```

### Add New Ground Station

```bash
# 1. Prepare new PackageVariant
cat <<EOF > new-site.yaml
apiVersion: config.porch.kpt.dev/v1alpha1
kind: PackageVariant
metadata:
  name: sdr-platform-newyork-site
  namespace: nephio-system
spec:
  upstream:
    repo: nephio-packages
    package: sdr-platform-base
    revision: v1.0.0
  downstream:
    repo: newyork-edge-site
    package: sdr-platform-newyork
  pipeline:
    mutators:
      - image: gcr.io/kpt-fn/apply-setters:v0.2.0
        configMap:
          site-id: "site-004"
          latitude: "40.7128"
          longitude: "-74.0060"
          usrp-args: "type=x310,addr=192.168.40.2"
EOF

# 2. Deploy
kubectl apply -f new-site.yaml

# 3. Monitor deployment
watch kubectl get packagevariant sdr-platform-newyork-site -n nephio-system

# 4. Verify
kubectl get pods -n sdr-platform-newyork --context newyork-edge
```

---

## Security Operations

### Certificate Management

```bash
# Generate TLS certificates (using cert-manager)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: sdr-api-tls
  namespace: sdr-platform
spec:
  secretName: sdr-api-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - sdr-api.example.com
EOF

# Verify certificate
kubectl get certificate -n sdr-platform
kubectl describe certificate sdr-api-tls -n sdr-platform
```

### Access Control Audit

```bash
# List service accounts with cluster-admin
kubectl get clusterrolebindings -o json | \
    jq -r '.items[] | select(.roleRef.name=="cluster-admin") | .metadata.name'

# Review RBAC for sdr-platform namespace
kubectl auth can-i --list --namespace=sdr-platform --as=system:serviceaccount:sdr-platform:sdr-api-gateway
```

---

## Maintenance Procedures

### Rolling Updates

```bash
# Update container image
kubectl set image deployment/sdr-api-gateway \
    api-server=your-registry.io/sdr-api-gateway:1.1.0 \
    -n sdr-platform

# Monitor rollout
kubectl rollout status deployment/sdr-api-gateway -n sdr-platform

# Rollback if needed
kubectl rollout undo deployment/sdr-api-gateway -n sdr-platform
```

### Kubernetes Cluster Upgrade

```bash
# Upgrade control plane
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply v1.29.0

# Upgrade kubelet on worker nodes (one at a time)
kubectl drain worker-node-1 --ignore-daemonsets
ssh worker-node-1 "sudo apt-get update && sudo apt-get install -y kubelet=1.29.0-00"
ssh worker-node-1 "sudo systemctl restart kubelet"
kubectl uncordon worker-node-1

# Verify upgrade
kubectl get nodes
```

---

## Incident Response

### Runbook: Complete System Outage

```bash
# PHASE 1: Detection (0-5 minutes)
# 1. Confirm outage
curl -f http://sdr-api.example.com/healthz || echo "OUTAGE CONFIRMED"

# 2. Check Prometheus alerts
curl http://prometheus.example.com/api/v1/alerts

# 3. Notify on-call team
# Use PagerDuty/Opsgenie integration

# PHASE 2: Triage (5-15 minutes)
# 1. Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running

# 2. Review recent changes
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | head -20

# 3. Check logs
kubectl logs -n sdr-platform deployment/sdr-api-gateway --tail=100
kubectl logs -n sdr-platform deployment/sdr-grpc-server --tail=100

# PHASE 3: Mitigation (15-30 minutes)
# Option A: Rollback recent changes
kubectl rollout undo deployment/sdr-api-gateway -n sdr-platform

# Option B: Restore from backup
velero restore create --from-backup sdr-platform-latest

# Option C: Failover to DR site
kubectl apply -f packagevariants/disaster-recovery-site.yaml

# PHASE 4: Recovery Verification (30-45 minutes)
# 1. Verify all pods running
kubectl get pods -n sdr-platform

# 2. Test API endpoints
curl http://sdr-api.example.com/api/v1/stations

# 3. Verify gRPC streaming
python oran_grpc_client.py

# PHASE 5: Post-Incident (45+ minutes)
# 1. Document incident in runbook
# 2. Schedule post-mortem meeting
# 3. Create Jira ticket for root cause analysis
```

---

## Performance Optimization

### CPU Pinning for Real-Time Performance

```yaml
# Edit deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdr-grpc-server
spec:
  template:
    spec:
      containers:
      - name: grpc-server
        resources:
          limits:
            cpu: 4  # Guaranteed CPUs
            memory: 8Gi
          requests:
            cpu: 4
            memory: 8Gi
      nodeSelector:
        node.kubernetes.io/instance-type: c5.2xlarge
```

### Network Tuning

```bash
# Increase MTU for 10 GbE
sudo ip link set enp1s0 mtu 9000

# Optimize TCP parameters
sudo sysctl -w net.core.rmem_max=536870912
sudo sysctl -w net.core.wmem_max=536870912
sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 536870912'
sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 536870912'
```

---

**Status**: ✅ **READY** - Comprehensive operations guide

**Last Updated**: 2025-10-27
**Author**: thc1006@ieee.org
