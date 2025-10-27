# OpenAirInterface 5G NR gNB Package for SDR-O-RAN Platform

## Overview

This Nephio package deploys a complete **5G NR base station (gNB)** using **OpenAirInterface (OAI)** 2025.w25 release, implementing the **O-RAN architecture** with:

- **O-DU (Distributed Unit)**: PHY + MAC + RLC layers
- **O-CU-CP (Centralized Unit - Control Plane)**: PDCP + RRC + SDAP + NGAP
- **O-CU-UP (Centralized Unit - User Plane)**: PDCP + SDAP + GTP-U

### Key Features

✅ **3GPP Release 18** compliance (5G NR Standalone)
✅ **O-RAN Alliance** specifications (O-RAN.WG4.CUS)
✅ **FAPI P5/P7** interfaces for PHY-MAC split
✅ **F1 interface** (F1-C + F1-U) between DU and CU
✅ **E1 interface** between CU-CP and CU-UP
✅ **VITA 49.2 integration** via SDR gRPC server
✅ **Kubernetes-native** deployment with Nephio
✅ **Multi-site** capable with PackageVariants

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  5G NR gNB (OpenAirInterface)                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐  F1-C/F1-U  ┌──────────────┐  E1  ┌──────────┐ │
│  │   O-DU        │◄────────────►│  O-CU-CP     │◄─────►│ O-CU-UP  │ │
│  │               │              │              │      │          │ │
│  │  PHY          │              │  RRC         │      │ PDCP-UP  │ │
│  │  MAC          │              │  PDCP-CP     │      │ SDAP     │ │
│  │  RLC          │              │  SDAP-CP     │      │ GTP-U    │ │
│  │               │              │  NGAP (N2)   │      │ N3       │ │
│  └───────┬───────┘              └──────┬───────┘      └────┬─────┘ │
│          │                             │                   │       │
│          │ FAPI P5/P7                  │ N2                │ N3    │
│          ▼                             ▼                   ▼       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐            ┌──────────┐      ┌───────────┐   │
│  │ SDR gRPC Server │            │   AMF    │      │    UPF    │   │
│  │ (VITA 49 Bridge)│            │ (5G Core)│      │ (5G Core) │   │
│  └─────────────────┘            └──────────┘      └───────────┘   │
│          │                                                         │
│          │ VITA 49.2 (UDP)                                         │
│          ▼                                                         │
│  ┌──────────────┐                                                  │
│  │ USRP X310    │                                                  │
│  │ (Hardware)   │                                                  │
│  └──────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. Hardware Requirements

| Component | Specification | Purpose |
|-----------|--------------|---------|
| **USRP X310** | Dual-channel SDR | RF front-end |
| **GPS Disciplined Oscillator** | 10 MHz reference | Precise timing |
| **10 GbE Network** | Low-latency connectivity | F1/E1/N2/N3 interfaces |
| **Server** | 8+ CPU cores, 32 GB RAM | gNB processing |

### 2. Software Requirements

| Software | Version | Installation |
|----------|---------|--------------|
| **Kubernetes** | 1.28+ | `kubeadm init` |
| **Nephio** | R2 | Nephio deployment guide |
| **USRP Host Driver (UHD)** | 4.6+ | `apt install uhd-host` |
| **GNU Radio** | 3.10+ | With `gr-dvbs2rx` OOT module |
| **5G Core** | OAI CN5G / Open5GS | AMF, SMF, UPF |

### 3. Network Requirements

```bash
# Kubernetes cluster networking
kubectl get nodes -o wide

# Service mesh (Istio recommended)
kubectl get pods -n istio-system

# Storage class for persistent volumes
kubectl get storageclass
```

---

## Quick Start

### Step 1: Clone and Prepare Package

```bash
# Clone this repository
cd 03-Implementation/orchestration/nephio/packages/oai-gnb

# Verify package structure
tree .
# .
# ├── Kptfile
# ├── README.md
# ├── base/
# ├── config/
# │   ├── gnb.conf
# │   └── README.md
# └── manifests/
#     ├── oai-du-deployment.yaml
#     ├── oai-cu-deployment.yaml
#     └── oai-configmaps.yaml
```

### Step 2: Generate gRPC Stubs (First Time Only)

```bash
cd ../../integration/sdr-oran-connector

# Generate Protocol Buffer stubs
python generate_grpc_stubs.py

# Verify
python test_grpc_connection.py
```

### Step 3: Deploy SDR Platform

```bash
# Deploy SDR API Gateway and gRPC Server
kubectl apply -f ../../orchestration/kubernetes/sdr-api-gateway-deployment.yaml
kubectl apply -f ../../integration/sdr-oran-connector/sdr-grpc-server-deployment.yaml

# Verify
kubectl get pods -n sdr-platform
```

### Step 4: Deploy 5G Core Network

```bash
# Option A: OpenAirInterface CN5G
kubectl apply -f https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed/-/raw/master/charts/oai-5g-core/all-in-one.yaml

# Option B: Open5GS
kubectl apply -f https://github.com/open5gs/open5gs/raw/main/misc/k8s/open5gs-all-in-one.yaml

# Verify AMF and UPF are running
kubectl get pods -n core5g
```

### Step 5: Deploy gNB via Nephio

```bash
# Create namespace
kubectl create namespace oran-platform

# Deploy using Nephio
kpt pkg get https://github.com/your-repo/sdr-oran-packages.git/oai-gnb .
kpt fn render oai-gnb
kubectl apply -f oai-gnb

# Or use PackageVariant for multi-site deployment
kubectl apply -f ../packagevariants/oai-gnb-tokyo-site.yaml
```

### Step 6: Verify Deployment

```bash
# Check pod status
kubectl get pods -n oran-platform

# Expected output:
# NAME                         READY   STATUS    RESTARTS   AGE
# oai-du-xxxxx                 1/1     Running   0          2m
# oai-cu-cp-xxxxx              1/1     Running   0          2m
# oai-cu-up-xxxxx              1/1     Running   0          2m

# Check logs
kubectl logs -n oran-platform deployment/oai-du --tail=50

# Expected: "gNB initialized successfully", "F1 interface connected"

# Verify USRP connectivity
kubectl exec -n oran-platform deployment/oai-du -- uhd_find_devices

# Expected: USRP X310 detected at 192.168.10.2

# Check F1 interface
kubectl exec -n oran-platform deployment/oai-du -- \
    bash -c "source /opt/oai-gnb/scripts/verify-f1-interface.sh"
```

---

## Configuration

### Site-Specific Parameters (via Kptfile)

These parameters are automatically substituted during Nephio package specialization:

```yaml
# In packagevariants/oai-gnb-site-001.yaml
configMap:
  site-id: "site-001"
  cell-id: "1"
  tracking-area-code: "1"
  plmn-mcc: "001"
  plmn-mnc: "01"
  sst: "1"
  sd: "0x000001"
  usrp-args: "type=x310,addr=192.168.10.2,master_clock_rate=184.32e6"
  f1-cu-address: "oai-cu-cp.oran-platform.svc.cluster.local"
```

### Advanced Configuration

#### 1. Change Frequency Band

Edit `config/gnb.conf`:

```conf
nr_band = 78;  # 3.5 GHz (n78)
# Options: 1 (2.1 GHz), 3 (1.8 GHz), 7 (2.6 GHz), 28 (700 MHz), 78 (3.5 GHz)

dl_carrierBandwidth = 106;  # PRBs for 20 MHz @ 30 kHz SCS
# Options: 51 (10 MHz), 106 (20 MHz), 216 (40 MHz), 273 (50 MHz)
```

#### 2. Enable GPS Timing

```conf
RUs = (
  {
    clock_src = "gpsdo";  # Use GPS disciplined oscillator
    time_src = "gpsdo";
  }
);
```

#### 3. Adjust Resource Allocation

```yaml
# In manifests/oai-du-deployment.yaml
resources:
  requests:
    cpu: 8000m      # Increase for higher throughput
    memory: 16Gi
    hugepages-1Gi: 4Gi
```

---

## Integration Points

### 1. FAPI P5/P7 Interface (DU ↔ SDR gRPC Server)

```conf
# In config/gnb.conf
fapi_p5_addr = "sdr-grpc-server.sdr-platform.svc.cluster.local";
fapi_p5_port = 50052;  # Control plane
fapi_p7_addr = "sdr-grpc-server.sdr-platform.svc.cluster.local";
fapi_p7_port = 50053;  # Data plane (IQ samples)
```

**FAPI Messages**:
- **P5**: Configuration requests, cell start/stop, slot indications
- **P7**: DL_TTI.request, UL_TTI.request, PRACH indications, PUSCH/PDSCH data

### 2. F1 Interface (DU ↔ CU)

```conf
# F1-C: Control Plane (SCTP)
F1_INTERFACE = {
  local_ip_address  = "0.0.0.0";
  remote_ip_address = "oai-cu-cp.oran-platform.svc.cluster.local";
  local_port        = 2153;
  remote_port       = 2153;
};

# F1-U: User Plane (GTP-U)
F1U_INTERFACE = {
  remote_ip_address = "oai-cu-up.oran-platform.svc.cluster.local";
  local_port        = 2152;
  remote_port       = 2152;
};
```

### 3. E1 Interface (CU-CP ↔ CU-UP)

```conf
# In CU-CP config
E1_INTERFACE = {
  remote_ip_address = "oai-cu-up.oran-platform.svc.cluster.local";
  local_port        = 38462;
};
```

### 4. N2 Interface (CU-CP ↔ AMF)

```conf
N2_INTERFACE = {
  remote_ip_address = "oai-amf.core5g.svc.cluster.local";
  local_port        = 38412;
};
```

---

## Monitoring

### Prometheus Metrics

```bash
# Scrape metrics from gNB components
curl http://oai-du.oran-platform.svc.cluster.local:9090/metrics

# Key metrics:
# - gnb_connected_ues_total
# - gnb_dl_throughput_mbps
# - gnb_ul_throughput_mbps
# - gnb_prb_utilization_percent
# - gnb_bler_dl
# - gnb_bler_ul
```

### Grafana Dashboard

```bash
# Import dashboard from 05-Documentation/monitoring-dashboards/sdr-platform-overview.json
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Navigate to: http://localhost:3000
# Import dashboard ID: 15000+ (OAI gNB)
```

---

## Troubleshooting

### Issue 1: DU Cannot Find USRP

```bash
# Check node label
kubectl get nodes --show-labels | grep usrp

# If missing, add label:
kubectl label nodes worker-node-1 hardware.sdr/usrp=true

# Verify USRP connectivity from node
ssh worker-node-1
uhd_find_devices
uhd_usrp_probe --args="type=x310,addr=192.168.10.2"
```

### Issue 2: F1 Interface Not Connected

```bash
# Check CU-CP service
kubectl get svc oai-cu-cp -n oran-platform

# Verify DNS resolution from DU pod
kubectl exec -n oran-platform deployment/oai-du -- \
    nslookup oai-cu-cp.oran-platform.svc.cluster.local

# Check SCTP connectivity
kubectl exec -n oran-platform deployment/oai-du -- \
    nc -z -v oai-cu-cp.oran-platform.svc.cluster.local 2153
```

### Issue 3: No UEs Connecting

```bash
# Check gNB logs for PRACH preambles
kubectl logs -n oran-platform deployment/oai-du | grep PRACH

# Verify SSB transmission
kubectl exec -n oran-platform deployment/oai-du -- \
    python -c "
from oran_grpc_client import ORANIQClient
client = ORANIQClient('localhost:50051', 'oai-du')
spectrum = client.get_spectrum(center_freq_hz=3.5e9, span_hz=20e6)
print(f'SSB power: {spectrum.peak_power_dbm:.2f} dBm')
"

# Check 5G Core AMF logs
kubectl logs -n core5g deployment/oai-amf | grep "NG Setup"
```

---

## Performance Tuning

### 1. CPU Pinning

```yaml
# In deployment manifest
env:
  - name: CPU_AFFINITY
    value: "0,1,2,3,4,5,6,7"  # Pin to CPUs 0-7
  - name: THREAD_PRIORITY
    value: "80"  # Real-time priority
```

### 2. Hugepages

```bash
# On worker node
echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Verify
cat /proc/meminfo | grep HugePages
```

### 3. Network Optimization

```bash
# Increase MTU for 10 GbE
sudo ip link set enp1s0 mtu 9000

# Optimize SCTP parameters
sudo sysctl -w net.sctp.sndbuf_policy=1
sudo sysctl -w net.sctp.rcvbuf_policy=1
```

---

## Multi-Site Deployment with Nephio

### Create PackageVariant for New Site

```yaml
# packagevariants/oai-gnb-london-site.yaml
apiVersion: config.porch.kpt.dev/v1alpha1
kind: PackageVariant
metadata:
  name: oai-gnb-london-site
  namespace: nephio-system
spec:
  upstream:
    repo: nephio-packages
    package: oai-gnb
    revision: v1.0.0
  downstream:
    repo: london-edge-site
    package: oai-gnb-london
  pipeline:
    mutators:
      - image: gcr.io/kpt-fn/apply-setters:v0.2.0
        configMap:
          site-id: "site-002"
          cell-id: "2"
          plmn-mcc: "234"  # UK
          plmn-mnc: "15"
          usrp-args: "type=x310,addr=192.168.20.2"
```

```bash
# Deploy
kubectl apply -f packagevariants/oai-gnb-london-site.yaml

# Monitor
watch kubectl get packagevariant oai-gnb-london-site -n nephio-system
```

---

## References

### Standards
- **3GPP TS 38.300**: NR Overall Description
- **3GPP TS 38.401**: NG-RAN Architecture
- **3GPP TS 38.470-473**: F1 Interface
- **3GPP TS 38.460-463**: E1 Interface
- **O-RAN.WG4.CUS**: Control, User and Synchronization Plane Specification
- **ORAN-WG8.xAPI**: Open Fronthaul Interfaces (FAPI P5/P7)

### OpenAirInterface
- **Documentation**: https://gitlab.eurecom.fr/oai/openairinterface5g/-/wikis/home
- **Releases**: https://gitlab.eurecom.fr/oai/openairinterface5g/-/releases
- **Docker Images**: https://hub.docker.com/u/oaisoftwarealliance

### USRP/UHD
- **UHD Manual**: https://files.ettus.com/manual/
- **VITA 49.x**: Integration guide in `../vita49-bridge/README.md`

---

**Status**: 🟡 **READY FOR TESTING** - Requires USRP X310 hardware and 5G Core deployment

**Last Updated**: 2025-10-27
**Author**: thc1006@ieee.org
**License**: Apache 2.0
