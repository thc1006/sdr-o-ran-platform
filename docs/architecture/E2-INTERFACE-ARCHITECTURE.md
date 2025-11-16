# O-RAN E2 Interface Architecture

## Overview
The E2 interface connects the Near-RT RIC to E2 Nodes (gNB, eNB, including DU and CU components). This implementation is based on O-RAN E2 specifications v4.0.0/v4.1.0 (October 2024) and ETSI TS 104 039 (E2AP) and ETSI TS 104 040 (E2SM-KPM).

## Components

### E2 Termination (Near-RT RIC)
The Near-RT RIC side of the E2 interface consists of:

- **E2AP Protocol Handler**: Processes E2 Application Protocol messages (setup, subscription, indication, control)
- **SCTP Connection Manager**: Manages reliable SCTP transport connections to E2 nodes
- **E2SM Service Models**: Implements E2 Service Models (E2SM-KPM, E2SM-RC)
- **Subscription Manager**: Tracks active subscriptions and routes indications to xApps
- **ASN.1 Encoder/Decoder**: Encodes and decodes E2AP messages using ASN.1 PER

### E2 Node (gNB/DU/CU)
The E2 node side consists of:

- **E2 Agent**: Main agent managing E2 interface interactions
- **E2AP Encoder/Decoder**: ASN.1 encoding/decoding for E2AP messages
- **KPM Service Model**: Collects and reports Key Performance Metrics
- **RC Service Model**: Executes RAN control actions from RIC
- **Measurement Collection**: Gathers RAN metrics (throughput, PRB usage, connection stats)

## Message Flow

### 1. E2 Setup Procedure
```
E2 Node                                 Near-RT RIC
   |                                         |
   |-------- E2 Setup Request -------------->|
   |  (Global E2 Node ID, RAN Functions)     |
   |                                         |
   |<------- E2 Setup Response --------------|
   |  (Global RIC ID, Accepted Functions)    |
```

**E2 Setup Request** contains:
- Global E2 Node ID (unique identifier)
- List of supported RAN Functions (E2SM-KPM, E2SM-RC, etc.)
- E2 Node Component Configuration (DU, CU, etc.)

**E2 Setup Response** contains:
- Global RIC ID
- List of accepted RAN Functions
- RIC configuration parameters

### 2. RIC Subscription Procedure
```
Near-RT RIC                             E2 Node
   |                                         |
   |------ RIC Subscription Request -------->|
   |  (RAN Function ID, Event Trigger,       |
   |   Action List)                          |
   |                                         |
   |<----- RIC Subscription Response --------|
   |  (Subscription ID, Accepted Actions)    |
```

**RIC Subscription Request** specifies:
- RAN Function ID (which service model)
- Event Trigger Definition (when to report)
- RIC Action List (what to report)

### 3. RIC Indication (Periodic/On-Change)
```
E2 Node                                 Near-RT RIC
   |                                         |
   |--------- RIC Indication --------------->|
   |  (Subscription ID, Indication Header,   |
   |   Indication Message)                   |
   |                                         |
   |  [Periodic or event-triggered reports]  |
```

**RIC Indication** delivers:
- Indication Header (timing, granularity)
- Indication Message (actual measurements/data)
- Service Model-specific encoding

### 4. RIC Control Procedure
```
Near-RT RIC                             E2 Node
   |                                         |
   |-------- RIC Control Request ----------->|
   |  (RAN Function ID, Control Header,      |
   |   Control Message)                      |
   |                                         |
   |<----- RIC Control Acknowledge ----------|
   |  (Control Outcome)                      |
```

**RIC Control Request** contains:
- Control Header (target identification)
- Control Message (control action parameters)
- Acknowledgement request flag

## Service Models Implemented

### E2SM-KPM v3.0 (Key Performance Metrics)

**Purpose**: Report RAN performance metrics to Near-RT RIC for monitoring and optimization.

**Supported Measurements**:
- `DRB.UEThpDl`: DRB UE Throughput Downlink (Mbps)
- `DRB.UEThpUl`: DRB UE Throughput Uplink (Mbps)
- `RRC.ConnEstabSucc`: RRC Connection Establishment Success count
- `RRC.ConnEstabAtt`: RRC Connection Establishment Attempts count
- `HANDOVER.SuccRate`: Handover Success Rate (percentage)
- `PRB.Usage`: Physical Resource Block Usage (percentage)

**Report Styles**:
- Style 1: UE Throughput Report (per-UE DL/UL throughput)
- Style 2: Cell Performance Report (cell-level KPIs)
- Style 3: Aggregate Statistics (network-wide metrics)

**Event Triggers**:
- Periodic (configurable interval: 100ms - 60s)
- On-change (threshold-based reporting)

### E2SM-RC v1.0 (RAN Control)

**Purpose**: Enable Near-RT RIC to control RAN behavior for optimization.

**Control Actions**:
- QoS Flow Management (add/modify/delete QoS flows)
- Radio Resource Allocation (PRB allocation adjustment)
- Handover Control (trigger/cancel handovers)
- UE Context Management (connection release, reconfiguration)

**Control Modes**:
- Direct Control: Immediate execution
- Delegated Control: Policy-based execution

## Interfaces

### E2AP (E2 Application Protocol)
- **Encoding**: ASN.1 PER (Packed Encoding Rules)
- **Version**: v4.0.0 (October 2024)
- **Message Types**:
  - Initiating Messages: E2 Setup Request, RIC Subscription Request, RIC Control Request
  - Successful Outcomes: E2 Setup Response, RIC Subscription Response, RIC Control Acknowledge
  - Unsuccessful Outcomes: E2 Setup Failure, RIC Subscription Failure, RIC Control Failure
  - Indication Messages: RIC Indication

### SCTP (Stream Control Transmission Protocol)
- **Transport Protocol**: SCTP over IP
- **Port**: 36421 (default for E2 interface)
- **Streams**: Multiple streams for different message priorities
- **Features**:
  - Multi-homing support
  - Message-oriented delivery
  - Congestion control
  - Path failover

### Internal Messaging (Protobuf)
- **Purpose**: Communication between E2 Manager and xApps
- **Benefits**:
  - Language-agnostic serialization
  - Efficient binary encoding
  - Schema evolution support
- **Message Types**:
  - E2NodeConnected
  - E2NodeDisconnected
  - RICIndication
  - ControlRequestStatus

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Near-RT RIC Platform                    │
│                                                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│  │  xApp 1  │   │  xApp 2  │   │  xApp N  │                │
│  │ (QoS Opt)│   │(Handover)│   │ (Custom) │                │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                │
│       │              │              │                        │
│       └──────────────┴──────────────┘                        │
│                      │                                       │
│               ┌──────▼───────┐                               │
│               │  E2 Manager  │                               │
│               │              │                               │
│               │ - Subscription│                              │
│               │   Manager    │                               │
│               │ - Connection │                               │
│               │   Manager    │                               │
│               └──────┬───────┘                               │
│                      │                                       │
│               ┌──────▼────────┐                              │
│               │ E2AP Handler  │                              │
│               │               │                              │
│               │ - E2SM-KPM    │                              │
│               │ - E2SM-RC     │                              │
│               │ - ASN.1 Codec │                              │
│               └──────┬────────┘                              │
│                      │                                       │
│               ┌──────▼────────┐                              │
│               │ SCTP Transport│                              │
│               └──────┬────────┘                              │
└──────────────────────┼─────────────────────────────────────┘
                       │ E2 Interface
                       │ (SCTP, Port 36421)
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                      E2 Node (gNB)                          │
│                                                              │
│               ┌──────────────┐                              │
│               │ SCTP Transport│                             │
│               └──────┬────────┘                             │
│                      │                                      │
│               ┌──────▼────────┐                             │
│               │  E2 Agent     │                             │
│               │               │                             │
│               │ - E2AP Handler│                             │
│               │ - E2SM-KPM    │                             │
│               │ - E2SM-RC     │                             │
│               │ - ASN.1 Codec │                             │
│               └──────┬────────┘                             │
│                      │                                      │
│       ┌──────────────┼──────────────┐                      │
│       │              │               │                      │
│  ┌────▼─────┐  ┌────▼─────┐  ┌─────▼────┐                │
│  │   DU     │  │   CU-CP  │  │  CU-UP   │                │
│  │          │  │          │  │          │                 │
│  │ - PHY    │  │ - RRC    │  │ - PDCP   │                │
│  │ - MAC    │  │ - NGAP   │  │ - SDAP   │                │
│  │ - RLC    │  │          │  │          │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Message Sequence Examples

### Complete E2 Setup and Subscription Flow

```
E2 Node (gNB)          Near-RT RIC              xApp
    |                       |                      |
    |--- E2 Setup Req ----->|                      |
    |   (Node ID: gnb-001)  |                      |
    |   (RAN Func: KPM,RC)  |                      |
    |                       |                      |
    |<-- E2 Setup Rsp ------|                      |
    |   (RIC ID: ric-001)   |                      |
    |   (Accepted: KPM,RC)  |                      |
    |                       |                      |
    |                       |<-- Subscribe Req ----|
    |                       |   (KPM, 1s periodic) |
    |                       |                      |
    |<- RIC Sub Req --------|                      |
    |   (Func: KPM)         |                      |
    |   (Period: 1000ms)    |                      |
    |                       |                      |
    |-- RIC Sub Rsp ------->|                      |
    |   (Sub ID: 1)         |                      |
    |                       |--- Sub Confirm ----->|
    |                       |                      |
    |                       |                      |
    |--- RIC Indication --->|                      |
    |   (Sub ID: 1)         |                      |
    |   (UE Thp: 100Mbps)   |                      |
    |                       |--- Indication ------>|
    |                       |   (Metrics data)     |
    |                       |                      |
    |   [Every 1 second]    |                      |
    |--- RIC Indication --->|--- Indication ------>|
    |                       |                      |
```

### RIC Control Flow Example

```
xApp                 Near-RT RIC          E2 Node (gNB)
 |                       |                      |
 |-- Control Req ------->|                      |
 |  (Adjust QoS for UE1) |                      |
 |                       |                      |
 |                       |--- RIC Ctrl Req ---->|
 |                       |   (QoS params)       |
 |                       |                      |
 |                       |                  [Execute]
 |                       |                  [QoS change]
 |                       |                      |
 |                       |<-- RIC Ctrl Ack -----|
 |                       |   (Success)          |
 |                       |                      |
 |<- Control Rsp --------|                      |
 |  (Status: OK)         |                      |
 |                       |                      |
```

## Implementation Details

### E2 Manager Responsibilities
1. **Connection Management**:
   - Accept incoming SCTP connections from E2 nodes
   - Maintain connection state and heartbeat monitoring
   - Handle connection failures and reconnection

2. **Subscription Management**:
   - Process subscription requests from xApps
   - Map subscriptions to E2 nodes
   - Route indications to correct xApps
   - Handle subscription lifecycle

3. **Message Routing**:
   - Route control requests from xApps to E2 nodes
   - Deliver indications from E2 nodes to xApps
   - Handle message acknowledgements

4. **Service Model Support**:
   - Load and manage E2SM implementations
   - Validate service model messages
   - Provide service model APIs to xApps

### E2 Node Agent Responsibilities
1. **Connection Establishment**:
   - Initiate SCTP connection to Near-RT RIC
   - Send E2 Setup Request with capabilities
   - Handle setup response and configuration

2. **Measurement Collection**:
   - Collect RAN metrics according to subscriptions
   - Encode measurements using E2SM-KPM
   - Send periodic or event-triggered indications

3. **Control Execution**:
   - Receive and decode control requests
   - Execute control actions on RAN components
   - Report control outcomes

4. **Error Handling**:
   - Detect and report failures
   - Implement retry logic
   - Maintain logs for troubleshooting

## Configuration Parameters

### Near-RT RIC E2 Configuration
```yaml
e2_interface:
  # SCTP configuration
  sctp:
    bind_address: "0.0.0.0"
    port: 36421
    max_connections: 100
    heartbeat_interval: 30  # seconds

  # E2AP configuration
  e2ap:
    transaction_timeout: 5  # seconds
    max_retries: 3

  # Service models
  service_models:
    - name: "E2SM-KPM"
      version: "3.0"
      oid: "1.3.6.1.4.1.53148.1.1.2.3"
      enabled: true

    - name: "E2SM-RC"
      version: "1.0"
      oid: "1.3.6.1.4.1.53148.1.1.2.2"
      enabled: true
```

### E2 Node Configuration
```yaml
e2_agent:
  # RIC connection
  ric_address: "192.168.1.100"
  ric_port: 36421

  # Node identification
  global_e2_node_id: "gnb-001"
  plmn_id: "00101"

  # Reporting configuration
  kpm:
    default_period: 1000  # milliseconds
    measurements:
      - "DRB.UEThpDl"
      - "DRB.UEThpUl"
      - "RRC.ConnEstabSucc"
```

## Security Considerations

### Transport Security
- **SCTP over DTLS**: Encrypt E2 interface traffic
- **Certificate-based Authentication**: Mutual authentication between RIC and E2 nodes
- **Certificate Management**: PKI for certificate issuance and revocation

### Message Security
- **Integrity Protection**: HMAC for message authentication
- **Replay Protection**: Sequence numbers and timestamps
- **Access Control**: Role-based access for control operations

### Deployment Security
- **Network Segmentation**: Isolate E2 interface network
- **Firewall Rules**: Restrict E2 traffic to authorized endpoints
- **Monitoring**: Log all E2 interface activities

## Performance Considerations

### Scalability
- Support for 100+ concurrent E2 node connections
- Handle 1000+ active subscriptions
- Process 10,000+ indications per second

### Latency
- E2 Setup: < 100ms
- Subscription: < 50ms
- Indication delivery: < 10ms
- Control execution: < 20ms

### Reliability
- SCTP multi-homing for path redundancy
- Automatic reconnection on failure
- Message buffering during network issues
- Subscription persistence across restarts

## Testing Strategy

### Unit Tests
- E2AP message encoding/decoding
- E2SM-KPM message creation
- Subscription management logic
- Connection state management

### Integration Tests
- E2 setup procedure
- Subscription lifecycle
- Indication delivery
- Control request execution

### System Tests
- Multi-node scenarios
- Load testing (1000+ subscriptions)
- Failover and recovery
- Performance benchmarking

## Future Enhancements

1. **Additional Service Models**:
   - E2SM-NI (Network Interface)
   - E2SM-RSM (Radio Slice Management)
   - E2SM-CCO (Cell Configuration and Optimization)

2. **Advanced Features**:
   - Multi-RIC coordination
   - E2 interface federation
   - Machine learning integration
   - Real-time analytics

3. **Optimization**:
   - Batched indications for efficiency
   - Compression for large messages
   - Adaptive reporting based on network conditions

## References

- O-RAN WG3.E2AP-v04.00: E2 Application Protocol
- O-RAN WG3.E2SM-KPM-v03.00: E2 Service Model for KPM
- O-RAN WG3.E2SM-RC-v01.00: E2 Service Model for RC
- ETSI TS 104 039: E2 Application Protocol (E2AP)
- ETSI TS 104 040: E2 Service Model (E2SM)
- 3GPP TS 38.300: NR Overall description
