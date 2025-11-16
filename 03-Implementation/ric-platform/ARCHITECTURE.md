# xApp Platform Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        O-RAN Near-RT RIC Platform                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  QoS Optimizer│          │   Handover    │          │  Your xApp    │
│     xApp      │          │  Manager xApp │          │               │
├───────────────┤          ├───────────────┤          ├───────────────┤
│ • Throughput  │          │ • RSRP Mon.   │          │ • Custom      │
│   Monitoring  │          │ • Cell Load   │          │   Logic       │
│ • QoS Adjust  │          │ • Smart HO    │          │ • Your Algo   │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────────────┐
        │              xApp Lifecycle Manager                    │
        │  • deploy_xapp()    • undeploy_xapp()                 │
        │  • list_xapps()     • get_xapp_status()               │
        └────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   XAppBase    │          │  SDLClient    │          │    Metrics    │
├───────────────┤          ├───────────────┤          ├───────────────┤
│ • init()      │          │ • set()       │          │ • update()    │
│ • start()     │          │ • get()       │          │ • collect()   │
│ • stop()      │          │ • delete()    │          │ • export()    │
│ • handle_ind()│          │ • list_keys() │          │               │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │
        │                           ▼
        │                   ┌───────────────┐
        │                   │  Redis (SDL)  │
        │                   │  • Key-Value  │
        │                   │  • Persistence│
        │                   └───────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│          E2 Interface (Agent 1)         │
│  • E2 Setup    • Subscriptions          │
│  • Indications • Control Requests       │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│              RAN (gNodeB)               │
└─────────────────────────────────────────┘
```

## Component Architecture

### xApp SDK Layers

```
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                      │
│        (QoS Optimizer, Handover Manager, etc.)         │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   xApp Framework                        │
│  ┌───────────────────────────────────────────────────┐ │
│  │              XAppBase (Abstract)                  │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │  Lifecycle:  init, start, stop              │ │ │
│  │  │  Processing: handle_indication              │ │ │
│  │  │  Metrics:    update_metric                  │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ SDL Client   │ │   E2 Client  │ │   Metrics    │
│              │ │              │ │   Client     │
│ • Redis      │ │ • Subscribe  │ │ • Collect    │
│ • Namespace  │ │ • Control    │ │ • Export     │
│ • Serialize  │ │ • Indicate   │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Data Flow

### Indication Processing Flow

```
RAN (gNodeB)
    │
    │ E2 Indication
    ▼
E2 Manager (Agent 1)
    │
    │ Parse & Route
    ▼
xApp Manager
    │
    │ Forward to xApp
    ▼
xApp.handle_indication()
    │
    ├─► Parse Indication
    │
    ├─► Update State
    │   └─► SDL.set(state)
    │
    ├─► Decision Logic
    │   ├─► Check Thresholds
    │   └─► Apply Algorithm
    │
    ├─► Send Control (if needed)
    │   └─► E2 Control Request
    │
    └─► Update Metrics
        └─► update_metric()
```

### SDL Data Flow

```
xApp A                          xApp B
    │                              │
    │ SDL.set("ue:123", data)      │
    ▼                              │
┌─────────────────────────────────┐│
│         Redis (SDL)             ││
│  ┌────────────────────────────┐││
│  │ Namespace: xapp-a          │││
│  │   key: ue:123 → data       │││
│  └────────────────────────────┘││
│  ┌────────────────────────────┐││
│  │ Namespace: xapp-b          │││
│  │   key: decision → data     │││
│  └────────────────────────────┘││
└─────────────────────────────────┘│
                                   │
                                   │ SDL.get("decision")
                                   ▼
                            Read shared data
```

## xApp Lifecycle

```
Created
   │
   │ XAppManager.deploy_xapp()
   ▼
Initializing
   │
   │ xapp.init()
   ▼
Initialized
   │
   │ xapp.start()
   ▼
Running ◄─────┐
   │          │
   │ handle_indication()
   │          │
   │ Process  │
   └──────────┘
   │
   │ xapp.stop() or error
   ▼
Stopped
   │
   │ XAppManager.undeploy_xapp()
   ▼
Removed
```

## QoS Optimizer xApp Architecture

```
┌─────────────────────────────────────────────────────────┐
│              QoS Optimizer xApp                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  E2 Indication (KPM)                                    │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Parse Throughput Metrics    │                       │
│  │  • UE ID                      │                       │
│  │  • Throughput (Mbps)         │                       │
│  │  • Cell ID                    │                       │
│  └──────────────────────────────┘                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Update UE Metrics            │                       │
│  │  ue_metrics[ue_id] = {        │                       │
│  │    throughput, cell, ts       │                       │
│  │  }                            │                       │
│  └──────────────────────────────┘                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Check QoS Adjustment         │                       │
│  │  IF throughput < 10 Mbps      │                       │
│  │    → Increase Priority        │                       │
│  │  ELSE IF throughput > 20 Mbps │                       │
│  │    → Decrease Priority        │                       │
│  └──────────────────────────────┘                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Send E2 Control Request      │                       │
│  │  • Target: UE                 │                       │
│  │  • Action: Adjust QoS         │                       │
│  └──────────────────────────────┘                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Store in SDL & Metrics       │                       │
│  │  • SDL: control_action        │                       │
│  │  • Metric: qos_controls_sent  │                       │
│  └──────────────────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## Handover Manager xApp Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Handover Manager xApp                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  E2 Indication (KPM)                                    │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Parse Measurements           │                       │
│  │  • RSRP (signal)              │                       │
│  │  • Cell Load                  │                       │
│  │  • Neighbor Cells             │                       │
│  └──────────────────────────────┘                       │
│         │                                                │
│    ┌────┴────┐                                          │
│    │         │                                           │
│    ▼         ▼                                           │
│ RSRP?    Cell Load?                                     │
│    │         │                                           │
│    ▼         ▼                                           │
│ ┌─────┐  ┌─────┐                                        │
│ │ UE  │  │Cell │                                        │
│ │Meas │  │Load │                                        │
│ └─────┘  └─────┘                                        │
│    │         │                                           │
│    └────┬────┘                                           │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Evaluate Handover            │                       │
│  │  1. Poor Signal?              │                       │
│  │     → Find Best Neighbor      │                       │
│  │  2. Cell Overloaded?          │                       │
│  │     → Find Least Loaded       │                       │
│  └──────────────────────────────┘                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Trigger Handover             │                       │
│  │  • Source Cell                │                       │
│  │  • Target Cell                │                       │
│  │  • Reason                     │                       │
│  └──────────────────────────────┘                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────┐                       │
│  │  Store Decision & Metrics     │                       │
│  │  • SDL: handover decision     │                       │
│  │  • Metric: handovers_triggered│                       │
│  └──────────────────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Kubernetes Deployment

```
┌─────────────────────────────────────────────────────────┐
│              Kubernetes Namespace: ric-platform         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Deployment: qos-optimizer                     │    │
│  │  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │ Pod (replica)│  │ Pod (replica)│           │    │
│  │  │ QoS xApp     │  │ QoS xApp     │           │    │
│  │  └──────────────┘  └──────────────┘           │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Deployment: handover-manager                  │    │
│  │  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │ Pod (replica)│  │ Pod (replica)│           │    │
│  │  │ HO xApp      │  │ HO xApp      │           │    │
│  │  └──────────────┘  └──────────────┘           │    │
│  └────────────────────────────────────────────────┘    │
│                         │                               │
│                         │ Connect to                    │
│                         ▼                               │
│  ┌────────────────────────────────────────────────┐    │
│  │  StatefulSet: redis                            │    │
│  │  ┌──────────────┐                              │    │
│  │  │ Pod (master) │                              │    │
│  │  │ Redis Server │                              │    │
│  │  └──────────────┘                              │    │
│  │                                                 │    │
│  │  Service: redis-service                        │    │
│  │  ClusterIP: 10.0.0.50:6379                     │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  ConfigMap: xapp-config                        │    │
│  │  • REDIS_HOST=redis-service                    │    │
│  │  • REDIS_PORT=6379                             │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Integration Points

```
┌─────────────────────────────────────────────────────────┐
│                    SDR O-RAN Platform                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Agent 1: E2 Interface                                  │
│  ┌────────────────────────────────┐                     │
│  │ • E2 Setup                     │                     │
│  │ • Subscription Management      │ ◄────┐             │
│  │ • Indication Routing           │      │             │
│  │ • Control Request Handling     │      │             │
│  └────────────────────────────────┘      │             │
│                │                          │             │
│                ▼                          │             │
│  Agent 2: xApp Framework ◄────────────────┤             │
│  ┌────────────────────────────────┐      │             │
│  │ • xApp SDK                     │      │             │
│  │ • SDL Client                   │      │             │
│  │ • Lifecycle Manager            │      │             │
│  │ • Example xApps                │      │             │
│  └────────────────────────────────┘      │             │
│                │                          │             │
│                ▼                          │             │
│  Agent 3: AI/ML Pipeline                 │             │
│  ┌────────────────────────────────┐      │             │
│  │ • Model Training               │      │             │
│  │ • Inference Engine             │ ◄────┤             │
│  │ • Data Collection              │      │             │
│  └────────────────────────────────┘      │             │
│                │                          │             │
│                ▼                          │             │
│  Agent 4: Orchestration                  │             │
│  ┌────────────────────────────────┐      │             │
│  │ • Kubernetes Deployment        │      │             │
│  │ • Resource Management          │ ◄────┘             │
│  │ • Health Monitoring            │                     │
│  └────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│              Python 3.8+ (Async/Await)                  │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   xApp SDK   │ │     SDL      │ │   Testing    │
│              │ │              │ │              │
│ • asyncio    │ │ • Redis 6+   │ │ • pytest     │
│ • logging    │ │ • redis-py   │ │ • pytest-    │
│ • dataclasses│ │ • JSON       │ │   asyncio    │
│ • ABC        │ │              │ │ • pytest-mock│
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
        ┌────────────────────────────────┐
        │      Container Platform        │
        │  • Docker                      │
        │  • Kubernetes                  │
        │  • Helm                        │
        └────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Security Layers                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Network Security                                        │
│  ┌────────────────────────────────┐                     │
│  │ • Kubernetes Network Policies  │                     │
│  │ • Pod-to-Pod isolation         │                     │
│  │ • Service mesh (future)        │                     │
│  └────────────────────────────────┘                     │
│                                                          │
│  Data Security                                          │
│  ┌────────────────────────────────┐                     │
│  │ • SDL Namespacing              │                     │
│  │ • Redis Authentication         │                     │
│  │ • TLS for E2 (future)          │                     │
│  └────────────────────────────────┘                     │
│                                                          │
│  Application Security                                   │
│  ┌────────────────────────────────┐                     │
│  │ • Input validation             │                     │
│  │ • Error handling               │                     │
│  │ • Resource limits              │                     │
│  └────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Monitoring & Observability                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  xApp Metrics                                           │
│  ┌────────────────────────────────┐                     │
│  │ • Internal metrics collection  │                     │
│  │ • Prometheus export (future)   │                     │
│  │ • Custom dashboards (future)   │                     │
│  └────────────────────────────────┘                     │
│         │                                                │
│         ▼                                                │
│  ┌────────────────────────────────┐                     │
│  │  Prometheus Server (future)    │                     │
│  │  • Scrape metrics              │                     │
│  │  • Time series DB              │                     │
│  └────────────────────────────────┘                     │
│         │                                                │
│         ▼                                                │
│  ┌────────────────────────────────┐                     │
│  │  Grafana (future)              │                     │
│  │  • Visualization               │                     │
│  │  • Alerting                    │                     │
│  └────────────────────────────────┘                     │
│                                                          │
│  Logging                                                │
│  ┌────────────────────────────────┐                     │
│  │ • Structured logging           │                     │
│  │ • Log aggregation (future)     │                     │
│  │ • Log analysis (future)        │                     │
│  └────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

---

## Summary

This architecture provides:

1. **Modularity**: Clear separation of concerns
2. **Scalability**: Horizontal scaling via Kubernetes
3. **Reliability**: State persistence and recovery
4. **Extensibility**: Easy to add new xApps
5. **Observability**: Comprehensive metrics and logging
6. **Security**: Multi-layer security controls
7. **Integration**: Clean interfaces with other agents

The design follows O-RAN Alliance specifications while providing a developer-friendly framework for creating intelligent RAN applications.
