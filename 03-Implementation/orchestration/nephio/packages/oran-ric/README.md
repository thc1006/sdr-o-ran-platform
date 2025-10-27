# O-RAN Near-RT RIC Deployment Package

## Overview

This package deploys the **O-RAN Software Community (OSC) Near-Real-Time RAN Intelligent Controller (Near-RT RIC)** - the AI/ML engine for intelligent network optimization in the SDR-O-RAN platform.

### What is the Near-RT RIC?

The Near-RT RIC is the "brain" of O-RAN architecture, enabling:
- **Real-time RAN optimization** (10ms - 1s control loop)
- **AI/ML-driven decision making** via xApps
- **Policy-based network management** via A1 interface
- **E2 interface** for gNB communication and control

### Components Deployed

| Component | Purpose | Interface |
|-----------|---------|-----------|
| **E2 Termination (E2T)** | E2AP protocol handling | E2 (SCTP) to gNB |
| **Subscription Manager** | E2 subscription lifecycle | Internal RMR |
| **Routing Manager** | Message routing to xApps | Internal RMR |
| **A1 Mediator** | Policy management | A1 (HTTP) to Non-RT RIC |
| **xApp Manager** | xApp lifecycle management | Internal |
| **SDL (Redis)** | Shared Data Layer for xApps | Internal |

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│  Near-RT RIC Platform (ricplt namespace)                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐  E2AP   ┌─────────┐  RMR   ┌──────────────┐       │
│  │   E2T    │◄────────►│ SubMgr  │◄──────►│   RTMgr      │       │
│  │  (SCTP)  │         │         │        │  (Routing)   │       │
│  └────┬─────┘         └────┬────┘        └──────┬───────┘       │
│       │                    │                     │               │
│       │ RMR (38000)        │ RMR                 │ RMR           │
│       ▼                    ▼                     ▼               │
│  ┌────────────────────────────────────────────────────┐          │
│  │           xApps (ricxapp namespace)                │          │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────┐       │          │
│  │  │ KPI Mon  │  │ Traffic  │  │  QoE/QoS  │       │          │
│  │  │  xApp    │  │ Steering │  │ Predictor │       │          │
│  │  └────┬─────┘  └────┬─────┘  └─────┬─────┘       │          │
│  └───────┼─────────────┼──────────────┼─────────────┘          │
│          │             │              │                         │
│          └─────────────┴──────────────┘                         │
│                        │                                        │
│                        ▼                                        │
│              ┌────────────────┐                                 │
│              │ SDL (Redis)    │                                 │
│              │ Shared Data    │                                 │
│              └────────────────┘                                 │
│                                                                 │
│  ┌──────────┐  A1 (HTTP)                                       │
│  │    A1    │◄────────────── Non-RT RIC (Policy Management)    │
│  │ Mediator │                                                   │
│  └──────────┘                                                   │
└───────────────────────────────────────────────────────────────────┘
         │
         │ E2AP (SCTP, port 36422)
         ▼
   ┌──────────┐
   │ O-DU     │ (OpenAirInterface gNB)
   │ (gNB)    │
   └──────────┘
```

---

## Prerequisites

### 1. Kubernetes Cluster
```bash
kubectl version --client
# Client Version: v1.28+
```

### 2. Nephio Platform
```bash
kubectl get packagevariants -n nephio-system
```

### 3. O-RAN gNB Deployed
```bash
kubectl get pods -n oran-platform
# oai-du-xxxxx     1/1   Running
# oai-cu-cp-xxxxx  1/1   Running
# oai-cu-up-xxxxx  1/1   Running
```

### 4. Network Connectivity
- **E2 Interface**: SCTP port 36422 accessible from gNB to RIC
- **A1 Interface**: HTTP(S) port 10000 for Non-RT RIC

---

## Quick Start

### Step 1: Deploy RIC Platform

```bash
cd 03-Implementation/orchestration/nephio/packages/oran-ric

# Apply namespace and RBAC
kubectl apply -f manifests/ric-platform-deployment.yaml

# Wait for platform components
kubectl wait --for=condition=ready pod -l app=e2term -n ricplt --timeout=300s
kubectl wait --for=condition=ready pod -l app=submgr -n ricplt --timeout=300s
kubectl wait --for=condition=ready pod -l app=rtmgr -n ricplt --timeout=300s
kubectl wait --for=condition=ready pod -l app=a1mediator -n ricplt --timeout=300s
```

### Step 2: Verify Platform Components

```bash
# Check all ricplt pods
kubectl get pods -n ricplt

# Expected output:
# NAME                         READY   STATUS    RESTARTS   AGE
# e2term-xxxxxx                1/1     Running   0          2m
# e2term-xxxxxx                1/1     Running   0          2m
# submgr-xxxxxx                1/1     Running   0          2m
# rtmgr-xxxxxx                 1/1     Running   0          2m
# a1mediator-xxxxxx            1/1     Running   0          2m
# appmgr-xxxxxx                1/1     Running   0          2m
# redis-standalone-0           1/1     Running   0          2m

# Check E2T logs
kubectl logs -n ricplt deployment/e2term --tail=20

# Expected: "E2 Termination started", "Listening on SCTP port 36422"
```

### Step 3: Configure gNB E2 Interface

Update OAI gNB configuration to connect to RIC:

```bash
# Get E2T service external IP
E2T_IP=$(kubectl get svc service-ricplt-e2term-sctp -n ricplt \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "E2T endpoint: $E2T_IP:36422"

# Update gNB config
kubectl edit configmap oai-du-config -n oran-platform

# Add E2 configuration:
# e2_agent = {
#   near_rt_ric_ip = "$E2T_IP";
#   near_rt_ric_port = 36422;
#   ran_function_id = 0;  # KPM
#   plmn_id = "00101";
# };

# Restart gNB to apply
kubectl rollout restart deployment/oai-du -n oran-platform
```

### Step 4: Verify E2 Connection

```bash
# Check E2T logs for gNB connection
kubectl logs -n ricplt deployment/e2term | grep "E2 Setup Request"

# Expected: "Received E2 Setup Request from gNB-001"

# Query SDL for connected gNBs
kubectl exec -n ricplt redis-standalone-0 -- \
    redis-cli KEYS "e2:gnb:*"

# Expected: "e2:gnb:00101:1" (PLMN:gNB-ID)
```

---

## Deploying xApps

### Example: KPI Monitoring xApp

```bash
# Create xApp descriptor
cat <<EOF > kpimon-xapp-descriptor.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kpimon-xapp-descriptor
  namespace: ricxapp
data:
  config.json: |
    {
      "name": "kpimon",
      "version": "1.0.0",
      "containers": [
        {
          "name": "kpimon",
          "image": "nexus3.o-ran-sc.org:10002/o-ran-sc/ric-app-kpimon:1.2.0",
          "imagePullPolicy": "IfNotPresent"
        }
      ],
      "messaging": {
        "ports": [
          {
            "name": "rmr-data",
            "container": "kpimon",
            "port": 38000,
            "rxMessages": ["RIC_INDICATION"],
            "txMessages": ["RIC_SUB_REQ", "RIC_SUB_DEL_REQ"],
            "policies": [20000],
            "description": "RMR messaging port"
          }
        ]
      },
      "rmr": {
        "protPort": "tcp:38000",
        "maxSize": 2072,
        "numWorkers": 1,
        "rxMessages": ["RIC_INDICATION"],
        "txMessages": ["RIC_SUB_REQ", "RIC_SUB_DEL_REQ"]
      }
    }
EOF

kubectl apply -f kpimon-xapp-descriptor.yaml

# Onboard xApp via AppMgr
kubectl exec -n ricplt deployment/appmgr -- \
    curl -X POST \
    -H "Content-Type: application/json" \
    -d @/config/kpimon-xapp-descriptor.json \
    http://service-ricplt-appmgr-http:8080/ric/v1/xapps

# Verify xApp deployment
kubectl get pods -n ricxapp
```

---

## AI/ML xApp Development

### xApp SDK Structure

```python
# Example: Traffic Steering xApp with Deep Reinforcement Learning

import ricxappframe as ricxapp
from ricxappframe.rmr import rmr
from ricxappframe.xapp_sdl import SDLWrapper
import numpy as np
import torch

class TrafficSteeringxApp:
    def __init__(self):
        # RMR messaging
        self.rmr_context = rmr.rmr_init(38000, rmr.RMR_MAX_RCV_BYTES, 0)

        # SDL for data sharing
        self.sdl = SDLWrapper(use_fake_sdl=False)

        # DRL agent (from our AI/ML pipeline)
        self.agent = self.load_drl_agent()

        # E2 subscription
        self.setup_e2_subscription()

    def load_drl_agent(self):
        """Load trained DRL model from SDL"""
        model_bytes = self.sdl.get("drl_models", "traffic_steering_v1")
        model = torch.load(io.BytesIO(model_bytes))
        return model

    def setup_e2_subscription(self):
        """Subscribe to KPM indications from gNB"""
        sub_req = {
            "SubscriptionId": "traffic-steering-001",
            "ClientEndpoint": {"Host": "service-ricxapp-ts-xapp-rmr.ricxapp"},
            "Meid": "gnb-001",
            "RANFunctionID": 0,  # KPM
            "E2SM-KPM-EventTriggerDefinition": {
                "reportingPeriod": 1000  # 1 second
            },
            "E2SM-KPM-ActionDefinition": [
                {
                    "actionID": 1,
                    "actionType": "report",
                    "actionDefinition": {
                        "measName": "DRB.UEThpDl"  # DL throughput
                    }
                }
            ]
        }

        # Send RIC_SUB_REQ via RMR
        self.send_rmr_message(12010, sub_req)

    def handle_ric_indication(self, msg):
        """Process KPM indication from gNB"""
        kpm_data = self.parse_kpm_indication(msg)

        # Extract state for DRL agent
        state = np.array([
            kpm_data["ue_throughput"],
            kpm_data["prb_utilization"],
            kpm_data["cqi"],
            kpm_data["buffer_status"]
        ])

        # Get action from DRL agent
        action = self.agent.act(state)

        # Send RIC_CONTROL_REQ to gNB
        self.send_ran_control(action)

    def send_ran_control(self, action):
        """Send RAN control message to gNB"""
        control_req = {
            "RICControlHeader": {
                "ueID": "ue-001",
                "cellID": 1
            },
            "RICControlMessage": {
                "targetCellID": action["target_cell"],
                "priority": action["priority"]
            }
        }

        self.send_rmr_message(12030, control_req)

    def run(self):
        """Main xApp loop"""
        while True:
            msg = self.receive_rmr_message()

            if msg.mtype == 12020:  # RIC_INDICATION
                self.handle_ric_indication(msg)

if __name__ == "__main__":
    xapp = TrafficSteeringxApp()
    xapp.run()
```

---

## Integration with SDR-O-RAN Platform

### Data Flow

```
USRP X310
    ↓ (VITA 49.2)
SDR gRPC Server
    ↓ (gRPC IQ samples)
OAI gNB (O-DU)
    ↓ (E2AP, SCTP)
Near-RT RIC (E2T)
    ↓ (RMR messages)
xApps (KPI Mon, Traffic Steering, QoS Predictor)
    ↓ (RIC_CONTROL_REQ)
OAI gNB (apply control decisions)
    ↓ (optimized RAN behavior)
Improved User Experience
```

### E2 Service Models Implemented

| E2SM | Purpose | Metrics | Control |
|------|---------|---------|---------|
| **KPM v2.0** | KPI Measurement | DL/UL throughput, BLER, CQI, PRB usage | N/A (report only) |
| **RC v1.0** | RAN Control | N/A | Cell handover, QoS enforcement |
| **NI v1.0** | SDR Integration (custom) | SNR, Doppler shift, RSSI | AGC, frequency correction |

---

## Monitoring

### Prometheus Metrics

```bash
# E2T metrics
curl http://service-ricplt-e2term-sctp.ricplt:8080/metrics

# Key metrics:
# - e2t_connected_gnbs_total
# - e2t_subscriptions_active
# - e2t_indications_received_total
# - e2t_control_requests_sent_total

# xApp metrics
curl http://service-ricxapp-kpimon-rmr.ricxapp:8080/metrics

# - xapp_kpi_prb_utilization_percent
# - xapp_kpi_dl_throughput_mbps
# - xapp_kpi_bler_dl
```

### Grafana Dashboard

```bash
# Import RIC monitoring dashboard
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Dashboard panels:
# - Connected gNBs (gauge)
# - Active E2 subscriptions (gauge)
# - E2 message rate (graph)
# - xApp decision latency (histogram)
# - RAN KPIs (multi-panel)
```

---

## Troubleshooting

### Issue 1: E2 Connection Not Established

```bash
# Check E2T logs
kubectl logs -n ricplt deployment/e2term | grep ERROR

# Common errors:
# - "SCTP connection refused" → Check gNB E2 config
# - "E2 Setup Request timeout" → Check network connectivity

# Test SCTP connectivity
kubectl exec -n oran-platform deployment/oai-du -- \
    nc -z -v service-ricplt-e2term-sctp.ricplt 36422
```

### Issue 2: xApp Not Receiving Indications

```bash
# Check subscription status
kubectl exec -n ricplt deployment/submgr -- \
    curl http://localhost:8080/ric/v1/subscriptions

# Check RMR routing
kubectl logs -n ricplt deployment/rtmgr | grep "Route update"

# Verify xApp RMR port
kubectl exec -n ricxapp deployment/kpimon -- \
    netstat -tulpn | grep 38000
```

---

## References

- **O-RAN SC Wiki**: https://wiki.o-ran-sc.org/
- **E2AP Specification**: O-RAN.WG3.E2AP-v03.00
- **E2SM-KPM**: O-RAN.WG3.E2SM-KPM-v03.00
- **xApp Framework**: https://github.com/o-ran-sc/ric-plt-xapp-frame-py

---

**Status**: 🟡 **READY FOR TESTING** - Requires OAI gNB with E2 agent enabled

**Last Updated**: 2025-10-27
**Author**: thc1006@ieee.org
