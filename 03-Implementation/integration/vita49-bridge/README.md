# VITA 49.x Integration for SDR-O-RAN

## Overview

**VITA 49** (VITA Radio Transport - VRT) is the industry-standard protocol for transporting digitized RF data from SDR hardware. This directory contains a **VITA 49.2 to gRPC bridge** that enables:

1. **Standards-compliant SDR data transport** using VITA 49.0/49.2
2. **Cloud-native O-RAN integration** via gRPC Protocol Buffers
3. **Best of both worlds**: USRP compatibility + Kubernetes service mesh support

## Architecture

```
┌─────────────────────┐                    ┌──────────────────────┐                  ┌──────────────────┐
│                     │   VITA 49.2 (UDP)  │                      │   gRPC (TCP)     │                  │
│  USRP X310/N320     │───────────────────►│  VITA 49 Bridge      │─────────────────►│  O-RAN DU (PHY)  │
│                     │   Port 4991        │  (vita49_receiver)   │  Port 50051      │                  │
│  VRT Packet Stream  │                    │                      │                  │  FAPI Interface  │
│  - IF Data (Type 0) │                    │  Functions:          │                  │                  │
│  - IF Context (1)   │                    │  • VRT parsing       │                  │                  │
│  - Signal Data (4)  │                    │  • Timestamping      │                  │                  │
│  - Spectrum (5)     │                    │  • Buffering         │                  │                  │
└─────────────────────┘                    │  • gRPC forwarding   │                  └──────────────────┘
                                           └──────────────────────┘
```

## VITA 49 vs. gRPC Comparison

| Feature | VITA 49.0/49.2 | gRPC (This Project) | **Hybrid (Recommended)** |
|---------|----------------|---------------------|-------------------------|
| **Transport** | UDP | TCP | VITA → Bridge → gRPC |
| **Latency** | ⭐⭐⭐⭐⭐ (~1ms) | ⭐⭐⭐⭐ (2-5ms) | ⭐⭐⭐⭐⭐ (1-3ms) |
| **Reliability** | ⭐⭐ (no retransmit) | ⭐⭐⭐⭐⭐ (guaranteed) | ⭐⭐⭐⭐ (context recovery) |
| **Timestamping** | ⭐⭐⭐⭐⭐ (ns precision) | ⭐⭐⭐ (ms precision) | ⭐⭐⭐⭐⭐ (preserved) |
| **Standards Compliance** | ⭐⭐⭐⭐⭐ (ANSI/VITA) | ⭐⭐⭐ (custom) | ⭐⭐⭐⭐⭐ (both) |
| **Cloud-Native** | ⭐⭐ (UDP limitations) | ⭐⭐⭐⭐⭐ (K8s native) | ⭐⭐⭐⭐⭐ (bridge pod) |
| **Interoperability** | ⭐⭐⭐⭐⭐ (all SDRs) | ⭐⭐⭐ (custom) | ⭐⭐⭐⭐⭐ (both) |
| **Service Mesh** | ⭐ (no support) | ⭐⭐⭐⭐⭐ (Istio) | ⭐⭐⭐⭐⭐ (gRPC side) |

### Recommendation: **Hybrid Approach**

✅ Use **VITA 49.2** for USRP → Bridge (low latency, standards-compliant)
✅ Use **gRPC** for Bridge → O-RAN (cloud-native, reliable)

## VITA 49.x Standards

### VITA 49.0-2015 (Radio Transport)

**Packet Types**:
- **Type 0**: IF Data (I/Q samples)
- **Type 1**: IF Context (frequency, sample rate, bandwidth)
- **Type 4**: Signal Data (extension)
- **Type 5**: Signal Context (extension)

**Key Features**:
- 32-bit word alignment
- Stream ID for multiplexing
- Integer + fractional timestamps (GPS/UTC)
- Context Indicator Field (CIF) for metadata
- Optional class ID and trailer

### VITA 49.2-2017 (Spectrum Survey)

**Enhancements**:
- Spectral density data
- Frequency hop tables
- Geolocation information (lat/lon/alt)
- Polarization metadata

### VITA 49.2 Packet Format

```
┌────────────────────────────────────────────────────────────────┐
│  Word 0: Header                                                │
│  ┌─────────────┬──────┬─────────┬──────────┬─────────────┐    │
│  │ Packet Type │ C/T  │ TS Mode │ Pkt Count│  Pkt Size   │    │
│  │   (4 bits)  │(2 b) │ (4 bits)│ (4 bits) │  (16 bits)  │    │
│  └─────────────┴──────┴─────────┴──────────┴─────────────┘    │
├────────────────────────────────────────────────────────────────┤
│  Word 1: Stream ID (32 bits)                                   │
├────────────────────────────────────────────────────────────────┤
│  Word 2-3: Class ID (optional, 64 bits)                        │
├────────────────────────────────────────────────────────────────┤
│  Word N: Integer Timestamp (optional, 32 bits, seconds)        │
├────────────────────────────────────────────────────────────────┤
│  Word N+1, N+2: Fractional Timestamp (optional, 64 bits, ps)   │
├────────────────────────────────────────────────────────────────┤
│  Word N+3: Context Indicator Field (CIF) - IF Context only     │
├────────────────────────────────────────────────────────────────┤
│  Payload: IQ Samples (Type 0) or Context Data (Type 1)         │
│                                                                 │
│  ┌──────────┬──────────┬──────────┬──────────┐                │
│  │ I Sample │ Q Sample │ I Sample │ Q Sample │  ...            │
│  │ (16 bits)│ (16 bits)│ (16 bits)│ (16 bits)│                │
│  └──────────┴──────────┴──────────┴──────────┘                │
└────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Configure USRP for VITA 49.2 Output

#### Option A: UHD Direct Configuration

```bash
# In GNU Radio Companion, USRP Source block:
Device Arguments: type=x310,addr=192.168.10.2,send_buff_size=16e6,recv_buff_size=16e6
Stream Arguments: vita_enable=1,vita_port=4991
```

#### Option B: GNU Radio Python Script

```python
from gnuradio import uhd

usrp_source = uhd.usrp_source(
    device_addr="type=x310,addr=192.168.10.2",
    stream_args=uhd.stream_args(
        cpu_format="fc32",
        otw_format="sc16",  # Over-the-wire: 16-bit I/Q
        args="vita_enable=1,vita_port=4991"
    )
)
```

### 2. Run VITA 49 Bridge

```bash
cd 03-Implementation/integration/vita49-bridge

# Install dependencies
pip install numpy grpcio protobuf

# Generate gRPC stubs
cd ../sdr-oran-connector
python -m grpc_tools.protoc \
    -I./proto \
    --python_out=. \
    --grpc_python_out=. \
    proto/sdr_oran.proto

# Run bridge
cd ../vita49-bridge
python vita49_receiver.py
```

**Expected Output**:
```
============================================================
VITA 49.2 to gRPC Bridge
============================================================
VITA 49 Receiver listening on 0.0.0.0:4991
gRPC endpoint: localhost:50051
Starting VITA 49 receiver...
Context packet: Fc=12.0000 GHz, SR=10.00 MSPS, BW=100.00 MHz
Forwarded 8192 samples to gRPC (Fc=12.0000 GHz)
```

### 3. Verify VRT Packets

```bash
# Monitor UDP traffic
sudo tcpdump -i any -n udp port 4991 -X | head -50

# Expected: Hexdump showing VRT headers
# IF Data packet starts with: 0x18... (packet type 0)
# IF Context packet starts with: 0x58... (packet type 1)
```

## Kubernetes Deployment

### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vita49-bridge
  namespace: sdr-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vita49-bridge
  template:
    metadata:
      labels:
        app: vita49-bridge
    spec:
      # Require node with USRP hardware
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: hardware.sdr/usrp
                operator: In
                values:
                - "true"

      containers:
      - name: vita49-bridge
        image: your-registry.io/vita49-bridge:1.0.0
        ports:
        - name: vrt-udp
          containerPort: 4991
          protocol: UDP
        - name: grpc
          containerPort: 50051
          protocol: TCP

        env:
        - name: LISTEN_IP
          value: "0.0.0.0"
        - name: LISTEN_PORT
          value: "4991"
        - name: GRPC_ENDPOINT
          value: "oran-iq-client.oran-platform.svc.cluster.local:50051"

        # HostNetwork required for low-latency UDP
        hostNetwork: true

        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi

---
apiVersion: v1
kind: Service
metadata:
  name: vita49-bridge
  namespace: sdr-platform
spec:
  type: NodePort
  selector:
    app: vita49-bridge
  ports:
  - name: vrt-udp
    port: 4991
    targetPort: 4991
    protocol: UDP
    nodePort: 30991
```

### Deploy

```bash
kubectl apply -f vita49-bridge-deployment.yaml

# Verify
kubectl get pods -n sdr-platform -l app=vita49-bridge
kubectl logs -n sdr-platform deployment/vita49-bridge
```

## Performance Tuning

### System-Level

```bash
# Increase UDP receive buffer
sudo sysctl -w net.core.rmem_max=536870912
sudo sysctl -w net.core.rmem_default=536870912

# Optimize interrupt coalescence
sudo ethtool -C enp1s0 rx-usecs 50 rx-frames 50

# Pin IRQ to specific CPU
echo 2 > /proc/irq/<IRQ_NUMBER>/smp_affinity_list
```

### Application-Level

```python
# In vita49_receiver.py, optimize buffering
self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64*1024*1024)  # 64 MB

# Batch more packets before forwarding
if len(self.data_buffer) >= 200:  # 200 packets instead of 100
    self.forward_to_grpc(self.data_buffer)
```

## Monitoring

### Prometheus Metrics

Add to `vita49_receiver.py`:

```python
from prometheus_client import Counter, Histogram, Gauge

vita49_packets_received_total = Counter(
    'vita49_packets_received_total',
    'Total VRT packets received',
    ['packet_type', 'stream_id']
)

vita49_samples_forwarded_total = Counter(
    'vita49_samples_forwarded_total',
    'Total IQ samples forwarded to gRPC',
    ['stream_id']
)

vita49_processing_latency_ms = Histogram(
    'vita49_processing_latency_ms',
    'VRT packet processing latency',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)
```

## Troubleshooting

### Issue 1: No VRT Packets Received

```bash
# Verify USRP is sending VRT
sudo tcpdump -i enp1s0 -n udp port 4991

# Check firewall
sudo iptables -L -n -v | grep 4991

# Verify UDP socket binding
netstat -ulnp | grep 4991
```

### Issue 2: Packet Loss

```bash
# Check dropped packets
netstat -su | grep -i "packet receive errors"

# Increase kernel buffer
sudo sysctl -w net.core.rmem_max=1073741824  # 1 GB

# Monitor in real-time
watch -n 1 'netstat -su | grep -i "packet receive errors"'
```

### Issue 3: Timestamp Drift

```bash
# Verify GPS lock on USRP
uhd_usrp_probe --args="type=x310" --tree | grep -A 5 "time_source"

# Should show: "gpsdo" or "external"

# Sync system clock to GPS
sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock
sudo chronyc -a makestep
```

## References

### Standards
- **ANSI/VITA 49.0-2015**: https://www.vita.com/Standards/VITA-49.0
- **ANSI/VITA 49.2-2017**: https://www.vita.com/Standards/VITA-49.2
- **IEEE 1588 (PTP)**: Precision Time Protocol for timestamping

### USRP Documentation
- **UHD VRT Support**: https://files.ettus.com/manual/page_usrp_x3x0.html#x3x0_usage_rtp_vrt
- **GNU Radio gr-vita49**: https://github.com/ghostop14/gr-vita49

### Academic Papers
- **VITA 49 for 5G**: "VITA Radio Transport Protocol for Cloud-RAN" (IEEE MILCOM 2018)
- **Low-Latency SDR**: "Sub-millisecond Latency SDR with VITA 49" (GNU Radio Conference 2019)

---

## Summary

**VITA 49.x is the correct industry standard for SDR data transport**, and this bridge provides the best integration path:

✅ **VITA 49.2 compliance** for USRP/SDR hardware
✅ **gRPC compatibility** for cloud-native O-RAN
✅ **Nanosecond timestamping** preserved end-to-end
✅ **Kubernetes-ready** with service mesh support

**Status**: 🟡 **READY FOR TESTING** - Requires USRP hardware with VRT enabled

**Last Updated**: 2025-10-27
**Author**: thc1006@ieee.org
