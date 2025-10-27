# SDR-O-RAN Platform Deployment Guide

Complete guide for deploying the SDR ground station and O-RAN integration platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Hardware Setup](#hardware-setup)
3. [Software Installation](#software-installation)
4. [Kubernetes Cluster Preparation](#kubernetes-cluster-preparation)
5. [Deploy SDR Components](#deploy-sdr-components)
6. [Deploy O-RAN Components](#deploy-oran-components)
7. [Nephio Multi-Site Deployment](#nephio-multi-site-deployment)
8. [Verification and Testing](#verification-and-testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Infrastructure Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Kubernetes Cluster** | 1.26+ | 1.28+ | With CNI plugin (Calico/Cilium) |
| **Worker Nodes** | 3 nodes | 5+ nodes | For high availability |
| **Node CPU** | 8 cores | 16+ cores | Per worker node |
| **Node Memory** | 16 GB | 32+ GB | Per worker node |
| **Node Storage** | 100 GB SSD | 500 GB NVMe | For I/Q sample recording |
| **Network** | 1 Gbps | 10 Gbps | For gRPC streaming |

### Hardware Requirements

#### SDR Hardware (per ground station)

| Option | Frequency Range | Bandwidth | Price | Notes |
|--------|----------------|-----------|-------|-------|
| **USRP B210** | 70 MHz - 6 GHz | 56 MHz | $1,730 | Entry-level, USB 3.0 |
| **USRP X310** | DC - 6 GHz | 120 MHz | $9,000 | Professional, 10 GbE |
| **USRP N320** | DC - 6 GHz | 100 MHz | $7,000 | Network SDR, 2x2 MIMO |

**Recommended for production**: USRP X310 with UBX-160 daughterboard

#### Antenna System

- **C-band (4-8 GHz)**: 1.2-3.0m parabolic dish
- **Ku-band (10.7-12.75 GHz)**: 0.6-1.2m parabolic dish
- **Ka-band (17.7-20.2 GHz)**: 0.45-0.9m parabolic dish
- **Antenna controller**: Az/El rotator with 0.1° precision
- **LNA**: Low-noise amplifier (0.5-1.0 dB NF)

### Software Prerequisites

```bash
# Verify Kubernetes
kubectl version --client

# Expected: v1.28.0 or higher

# Verify Helm
helm version

# Expected: v3.12.0 or higher

# Verify Docker
docker --version

# Expected: Docker version 24.0.0 or higher
```

---

## Hardware Setup

### 1. USRP Installation

#### Physical Installation

```bash
# Install UHD drivers (Ubuntu 22.04)
sudo add-apt-repository ppa:ettusresearch/uhd
sudo apt-get update
sudo apt-get install -y uhd-host uhd-images

# Verify USRP connection
uhd_find_devices

# Expected output:
# --------------------------------------------------
# -- UHD Device 0
# --------------------------------------------------
# Device Address:
#     serial: 12345678
#     product: B210
#     type: b200
```

#### Network Configuration (for X310/N320)

```bash
# Set static IP for 10 GbE interface
sudo ip addr add 192.168.10.1/24 dev enp1s0
sudo ip link set enp1s0 up
sudo ip link set enp1s0 mtu 9000  # Enable jumbo frames

# Verify connectivity
ping -c 3 192.168.10.2  # USRP IP
```

#### Performance Tuning

```bash
# Increase network buffer sizes
sudo sysctl -w net.core.rmem_max=268435456
sudo sysctl -w net.core.wmem_max=268435456

# Set CPU governor to performance mode
sudo cpupower frequency-set -g performance

# Disable CPU frequency scaling
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 2. Antenna System Setup

#### Antenna Controller Configuration

```bash
# Install rotctld (Hamlib)
sudo apt-get install -y hamlib-utils

# Start rotator daemon
rotctld -m 1 -r /dev/ttyUSB0 -s 9600

# Test antenna control
echo "P 180 45" | nc localhost 4533  # Point to Az=180°, El=45°
```

#### Calibration

1. **Polarization alignment**: Use beacon signal
2. **Pointing accuracy**: Verify with known satellite
3. **Tracking test**: Follow LEO satellite pass

---

## Software Installation

### 1. GNU Radio

```bash
# Install GNU Radio 3.10+
sudo apt-get install -y gnuradio

# Verify installation
gnuradio-config-info --version

# Expected: 3.10.9.2 or higher

# Install OOT modules
git clone https://github.com/drmpeg/gr-dvbs2rx.git
cd gr-dvbs2rx
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

### 2. Container Images

Build and push container images:

```bash
# Navigate to project root
cd /path/to/sdr-oran-platform

# Build SDR API Gateway
cd 03-Implementation/sdr-platform/api-gateway
docker build -t your-registry.io/sdr-api-gateway:1.0.0 .
docker push your-registry.io/sdr-api-gateway:1.0.0

# Build gRPC Server
cd ../integration/sdr-oran-connector
docker build -t your-registry.io/sdr-grpc-server:1.0.0 .
docker push your-registry.io/sdr-grpc-server:1.0.0
```

### 3. Generate gRPC Stubs

```bash
cd 03-Implementation/integration/sdr-oran-connector

# Install protoc compiler
sudo apt-get install -y protobuf-compiler

# Generate Python stubs
python -m grpc_tools.protoc \
    -I./proto \
    --python_out=. \
    --grpc_python_out=. \
    proto/sdr_oran.proto
```

---

## Kubernetes Cluster Preparation

### 1. Install Kubernetes

#### Using kubeadm (for bare metal)

```bash
# Install kubeadm, kubelet, kubectl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet=1.28.0-00 kubeadm=1.28.0-00 kubectl=1.28.0-00
sudo apt-mark hold kubelet kubeadm kubectl

# Initialize cluster (on master node)
sudo kubeadm init \
    --pod-network-cidr=10.244.0.0/16 \
    --apiserver-advertise-address=<MASTER_IP>

# Copy kubeconfig
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install CNI (Calico)
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

# Join worker nodes (run on each worker)
sudo kubeadm join <MASTER_IP>:6443 \
    --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH>
```

#### Using K3s (lightweight alternative)

```bash
# Master node
curl -sfL https://get.k3s.io | sh -

# Get token
sudo cat /var/lib/rancher/k3s/server/node-token

# Worker nodes
curl -sfL https://get.k3s.io | K3S_URL=https://<MASTER_IP>:6443 K3S_TOKEN=<TOKEN> sh -
```

### 2. Install Istio Service Mesh

```bash
# Download Istio
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
cd istio-1.20.0
export PATH=$PWD/bin:$PATH

# Install Istio
istioctl install --set profile=default -y

# Enable sidecar injection for SDR namespace
kubectl label namespace sdr-platform istio-injection=enabled
```

### 3. Install Monitoring Stack

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --set grafana.enabled=true \
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Wait for deployment
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s

# Get Grafana password
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode; echo
```

---

## Deploy SDR Components

### 1. Create Secrets

```bash
# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)

# Create Kubernetes secret
kubectl create secret generic sdr-api-secrets \
    --from-literal=jwt-secret-key=$JWT_SECRET \
    --from-literal=admin-password=$(openssl rand -base64 16) \
    --namespace sdr-platform
```

### 2. Deploy SDR API Gateway

```bash
cd 03-Implementation/orchestration/kubernetes

# Update image registry in deployment YAML
sed -i 's|your-registry.io|asia-northeast1-docker.pkg.dev/your-project|g' \
    sdr-api-gateway-deployment.yaml

# Deploy
kubectl apply -f sdr-api-gateway-deployment.yaml

# Verify deployment
kubectl get pods -n sdr-platform
kubectl logs -n sdr-platform deployment/sdr-api-gateway

# Expected output:
# INFO:     Started server process [1]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 3. Deploy gRPC Server

**⚠️ Important**: gRPC server requires USRP hardware access

```bash
# Label node with USRP hardware
kubectl label nodes <WORKER_NODE_NAME> hardware.sdr/usrp=true

# Deploy gRPC server
kubectl apply -f sdr-grpc-server-deployment.yaml

# Verify USRP access
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- uhd_find_devices
```

### 4. Expose Services

```bash
# Create Istio Gateway
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: sdr-gateway
  namespace: sdr-platform
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "sdr-api.example.com"
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: sdr-api
  namespace: sdr-platform
spec:
  hosts:
  - "sdr-api.example.com"
  gateways:
  - sdr-gateway
  http:
  - route:
    - destination:
        host: sdr-api-gateway
        port:
          number: 80
EOF

# Get Istio ingress IP
kubectl get svc -n istio-system istio-ingressgateway
```

---

## Deploy O-RAN Components

### 1. Deploy OAI O-RAN DU

```bash
# Clone OAI repository
git clone https://gitlab.eurecom.fr/oai/openairinterface5g.git
cd openairinterface5g

# Build OAI DU
./build_oai -I -w USRP --gNB
cd cmake_targets/ran_build/build
sudo make install

# Configure DU
cp ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpx310.conf \
   /etc/oai/gnb.conf

# Edit configuration (update IP addresses)
sudo nano /etc/oai/gnb.conf
```

### 2. Deploy Near-RT RIC (FlexRIC)

```bash
# Install FlexRIC
git clone https://gitlab.eurecom.fr/mosaic5g/flexric.git
cd flexric
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install

# Start RIC
./flexric
```

### 3. Configure E2 Interface

```bash
# In gnb.conf, add E2 configuration:
cat <<EOF | sudo tee -a /etc/oai/gnb.conf
E2_AGENT = {
  near_ric_ip_addr = "192.168.1.100";
  sm_dir = "/usr/local/lib/flexric/";
};
EOF
```

---

## Nephio Multi-Site Deployment

### 1. Install Nephio

```bash
# Install Nephio R1
curl -fsSL https://github.com/nephio-project/nephio/releases/download/v1.0.0/install.sh | bash

# Verify installation
kubectl get pods -n nephio-system
```

### 2. Register Edge Clusters

```bash
# Tokyo edge site
nephio cluster add tokyo-edge \
    --kubeconfig ~/.kube/tokyo-kubeconfig \
    --type edge

# London edge site
nephio cluster add london-edge \
    --kubeconfig ~/.kube/london-kubeconfig \
    --type edge

# Singapore edge site
nephio cluster add singapore-edge \
    --kubeconfig ~/.kube/singapore-kubeconfig \
    --type edge

# Verify clusters
kubectl get clusters -n nephio-system
```

### 3. Deploy PackageVariants

```bash
cd 03-Implementation/orchestration/nephio

# Apply PackageVariants for all sites
kubectl apply -f packagevariants/sdr-edge-deployment.yaml

# Monitor deployment
watch kubectl get packagevariants -n nephio-system

# Expected:
# NAME                         READY   REASON
# sdr-platform-tokyo-site      True    Ready
# sdr-platform-london-site     True    Ready
# sdr-platform-singapore-site  True    Ready
```

### 4. Verify Multi-Site Deployment

```bash
# Check Tokyo site
kubectl get pods -n sdr-platform-tokyo --context tokyo-edge

# Check London site
kubectl get pods -n sdr-platform-london --context london-edge

# Check Singapore site
kubectl get pods -n sdr-platform-singapore --context singapore-edge
```

---

## Verification and Testing

### 1. Health Checks

```bash
# SDR API Gateway
curl http://sdr-api.example.com/healthz

# Expected: {"status":"healthy"}

# gRPC Server
grpcurl -plaintext sdr-grpc-server.sdr-platform.svc.cluster.local:50051 \
    sdr.oran.IQStreamService/GetStreamStats

# USRP Hardware
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    uhd_usrp_probe --args="type=x310"
```

### 2. End-to-End Test

```bash
# Start IQ stream
python 03-Implementation/integration/sdr-oran-connector/oran_grpc_client.py

# Monitor metrics
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open http://localhost:9090

# Check E2E latency
curl -s http://localhost:9090/api/v1/query?query=avg\(sdr_e2e_latency_ms\) | jq '.data.result[0].value[1]'

# Expected: <100 (ms)
```

### 3. Performance Benchmarks

```bash
# IQ streaming throughput test
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    python -c "
from sdr_grpc_server import IQSampleGenerator
gen = IQSampleGenerator(sample_rate=10e6, batch_size=8192)
import time
start = time.time()
for _ in range(1000):
    gen.generate_batch()
throughput = (1000 * 8192 * 8) / (time.time() - start) / 1e6
print(f'Throughput: {throughput:.2f} Mbps')
"

# Expected: >80 Mbps
```

---

## Troubleshooting

### Common Issues

#### 1. USRP Not Detected

**Symptom**: `uhd_find_devices` returns no devices

**Solutions**:

```bash
# Check USB connection (for B210)
lsusb | grep "Ettus Research"

# Reload UHD driver
sudo modprobe -r uhd
sudo modprobe uhd

# Check permissions
sudo usermod -a -G usrp $USER
sudo udevadm control --reload-rules && sudo udevadm trigger

# For X310/N320, check network
ping 192.168.10.2
ethtool enp1s0 | grep "Link detected"
```

#### 2. High gRPC Latency

**Symptom**: `sdr_e2e_latency_ms > 100ms`

**Solutions**:

```bash
# Check network RTT
kubectl exec -n sdr-platform deployment/sdr-grpc-server -- \
    ping -c 10 oran-iq-client.oran-platform.svc.cluster.local

# Reduce batch size
# Edit gRPC client configuration: batch_size=4096 (instead of 8192)

# Enable CPU pinning
kubectl patch deployment sdr-grpc-server -n sdr-platform --type='json' -p='[
  {"op": "add", "path": "/spec/template/spec/containers/0/resources/requests/cpu", "value": "4"},
  {"op": "add", "path": "/spec/template/spec/containers/0/resources/limits/cpu", "value": "4"}
]'
```

#### 3. PackageVariant Not Rendering

**Symptom**: `kubectl get packagevariants` shows "NotReady"

**Solutions**:

```bash
# Check Porch logs
kubectl logs -n porch-system deployment/porch-server --tail=100

# Verify upstream package exists
kpt alpha rpkg get sdr-platform-base --revision v1.0.0

# Re-approve package
kpt alpha rpkg propose sdr-platform-base-v1.0.0
kpt alpha rpkg approve sdr-platform-base-v1.0.0

# Force re-render
kubectl delete packagevariant sdr-platform-tokyo-site -n nephio-system
kubectl apply -f packagevariants/sdr-edge-deployment.yaml
```

---

## Next Steps

1. **Configure TLS/mTLS**: See [Security Guide](security-guide.md)
2. **Set up Backup/DR**: See [Operations Guide](operations-guide.md)
3. **Tune Performance**: See [Performance Tuning Guide](performance-tuning.md)
4. **Monitor Dashboard**: Import Grafana dashboards from `05-Documentation/monitoring-dashboards/`

---

**Status**: ✅ **READY** - Production deployment guide

**Last Updated**: 2025-10-27
**Author**: thc1006@ieee.org
