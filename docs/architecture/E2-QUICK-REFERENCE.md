# E2 Interface Quick Reference Guide

## Overview

Quick reference for O-RAN E2 Interface implementation in the SDR O-RAN Platform.

## Key Concepts

### E2 Interface
- **Purpose**: Connect Near-RT RIC to E2 Nodes (gNB, eNB)
- **Transport**: SCTP on port 36421
- **Protocol**: E2AP (E2 Application Protocol)
- **Encoding**: ASN.1 PER (simplified in current implementation)

### Service Models
- **E2SM-KPM**: Key Performance Metrics (monitoring)
- **E2SM-RC**: RAN Control (configuration and optimization)

## Message Types

### 1. E2 Setup
**Purpose**: Initial connection establishment

```
E2 Node → Near-RT RIC: E2 Setup Request
Near-RT RIC → E2 Node: E2 Setup Response
```

**Key Fields**:
- Global E2 Node ID
- RAN Functions (supported service models)
- Component Configuration

### 2. RIC Subscription
**Purpose**: Subscribe to measurements/events

```
Near-RT RIC → E2 Node: RIC Subscription Request
E2 Node → Near-RT RIC: RIC Subscription Response
```

**Key Fields**:
- RAN Function ID
- Event Trigger (periodic/on-change)
- Action List (what to report)

### 3. RIC Indication
**Purpose**: Report measurements/events

```
E2 Node → Near-RT RIC: RIC Indication (periodic)
```

**Key Fields**:
- Subscription ID
- Indication Header (timing, granularity)
- Indication Message (actual data)

### 4. RIC Control
**Purpose**: Control RAN behavior

```
Near-RT RIC → E2 Node: RIC Control Request
E2 Node → Near-RT RIC: RIC Control Acknowledge
```

**Key Fields**:
- RAN Function ID
- Control Header (target)
- Control Message (action parameters)

## E2SM-KPM Measurements

### Common Metrics

| Measurement Type | Description | Unit |
|-----------------|-------------|------|
| DRB.UEThpDl | UE Throughput Downlink | Mbps |
| DRB.UEThpUl | UE Throughput Uplink | Mbps |
| RRC.ConnEstabSucc | RRC Connection Success | count |
| RRC.ConnEstabAtt | RRC Connection Attempts | count |
| HANDOVER.SuccRate | Handover Success Rate | % |

### Report Styles

1. **UE Throughput Report**: Per-UE DL/UL throughput
2. **Cell Performance Report**: Cell-level KPIs
3. **Aggregate Statistics**: Network-wide metrics

## Quick Start Code

### Initialize E2 Manager

```python
import asyncio
from e2_manager import E2InterfaceManager

async def main():
    manager = E2InterfaceManager()
    await manager.start()
    # ... use manager ...
    await manager.stop()

asyncio.run(main())
```

### Handle E2 Setup

```python
from e2_messages import E2SetupRequest, E2NodeComponentConfig
from e2sm_kpm import E2SM_KPM

request = E2SetupRequest(
    transaction_id=1,
    global_e2_node_id="gnb-001",
    ran_functions=[E2SM_KPM.RAN_FUNCTION_DEFINITION],
    e2_node_component_config=[E2NodeComponentConfig("DU", 1)]
)

response = await manager.handle_e2_setup(request)
```

### Create Subscription

```python
async def indication_callback(indication):
    print(f"Indication: {indication}")

subscription_id = await manager.create_subscription(
    node_id="gnb-001",
    ran_function_id=E2SM_KPM.RAN_FUNCTION_ID,
    callback=indication_callback
)
```

### Create KPM Measurements

```python
import time
from e2sm_kpm import MeasurementRecord, MeasurementType, E2SM_KPM

measurements = [
    MeasurementRecord(
        measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
        value=150.5,
        timestamp=int(time.time() * 1e9),
        ue_id="ue-001"
    )
]

header, message = E2SM_KPM.create_indication(measurements)
```

## File Locations

### Implementation Files
```
03-Implementation/ric-platform/e2-interface/
├── __init__.py              # Module exports
├── e2_messages.py           # E2AP messages
├── e2sm_kpm.py              # KPM service model
├── e2_manager.py            # E2 Manager
├── e2_config_example.yaml   # Configuration example
└── README.md                # Module documentation
```

### Documentation Files
```
docs/architecture/
├── E2-INTERFACE-ARCHITECTURE.md  # Architecture design
├── E2-API-REFERENCE.md           # API documentation
└── E2-QUICK-REFERENCE.md         # This file
```

### Test Files
```
tests/unit/
└── test_e2_interface.py     # Unit tests
```

## Configuration

### Minimal Configuration

```yaml
e2_interface:
  sctp:
    bind_address: "0.0.0.0"
    port: 36421
  ric:
    global_ric_id: "RIC-001"
  service_models:
    - name: "E2SM-KPM"
      ran_function_id: 1
      enabled: true
```

## Testing

### Run Unit Tests

```bash
source venv/bin/activate
pytest tests/unit/test_e2_interface.py -v
```

### Test Coverage

```bash
pytest tests/unit/test_e2_interface.py --cov=03-Implementation/ric-platform/e2-interface
```

## Common Operations

### Check Connected Nodes

```python
print(f"Connected nodes: {manager.connected_nodes.keys()}")
```

### List Active Subscriptions

```python
print(f"Active subscriptions: {len(manager.subscriptions)}")
for sub_id, sub in manager.subscriptions.items():
    print(f"  {sub_id}: {sub.node_id}, RAN Func {sub.ran_function_id}")
```

### Send Control Request

```python
success = await manager.send_control_request(
    node_id="gnb-001",
    ran_function_id=2,
    control_header=b"...",
    control_message=b"..."
)
```

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check E2 Node Status

```python
node = manager.connected_nodes.get("gnb-001")
if node:
    print(f"Node: {node.node_id}")
    print(f"Type: {node.node_type}")
    print(f"RAN Functions: {node.ran_functions}")
    print(f"Last seen: {node.last_seen}")
```

## Error Handling

### Common Errors

1. **Node Not Connected**: Check E2 setup was successful
2. **Invalid Subscription**: Verify RAN function ID is supported
3. **Timeout**: Check SCTP connection and network

### Error Handling Pattern

```python
try:
    response = await manager.handle_e2_setup(request)
except Exception as e:
    logger.error(f"E2 Setup failed: {e}")
    # Handle error
```

## Performance Tips

1. **Use async/await**: All operations are asynchronous
2. **Lightweight callbacks**: Keep indication callbacks fast
3. **Batch processing**: Process multiple indications together
4. **Connection pooling**: Reuse connections where possible

## Integration Points

### With xApps

```python
# xApp registers callback for indications
async def xapp_callback(indication):
    # Process indication in xApp
    pass

await manager.create_subscription(
    node_id="gnb-001",
    ran_function_id=1,
    callback=xapp_callback
)
```

### With A1 Interface

```python
# Receive policy from A1
# Create E2 subscription based on policy
# Send control requests to enforce policy
```

## Standards References

- **O-RAN.WG3.E2AP-v04.00**: E2 Application Protocol
- **O-RAN.WG3.E2SM-KPM-v03.00**: KPM Service Model
- **ETSI TS 104 039**: E2AP Specification
- **ETSI TS 104 040**: E2SM Specification

## Next Steps

1. **Learn**: Read [E2-INTERFACE-ARCHITECTURE.md](E2-INTERFACE-ARCHITECTURE.md)
2. **Code**: See examples in [E2-API-REFERENCE.md](E2-API-REFERENCE.md)
3. **Test**: Run unit tests and explore test code
4. **Extend**: Add custom service models or xApps

## Support Files

- **API Reference**: `/docs/architecture/E2-API-REFERENCE.md`
- **Architecture**: `/docs/architecture/E2-INTERFACE-ARCHITECTURE.md`
- **Module README**: `/03-Implementation/ric-platform/e2-interface/README.md`
- **Config Example**: `/03-Implementation/ric-platform/e2-interface/e2_config_example.yaml`

## Cheat Sheet

### Import Statements

```python
from e2_messages import E2SetupRequest, E2SetupResponse, RICSubscriptionRequest, RICIndication
from e2sm_kpm import E2SM_KPM, MeasurementType, MeasurementRecord
from e2_manager import E2InterfaceManager
```

### Common Constants

```python
E2SM_KPM.RAN_FUNCTION_ID  # 1
E2_SCTP_PORT              # 36421
```

### Typical Flow

```python
# 1. Start manager
manager = E2InterfaceManager()
await manager.start()

# 2. Handle E2 setup (when node connects)
response = await manager.handle_e2_setup(setup_request)

# 3. Create subscription
sub_id = await manager.create_subscription(node_id, ran_func_id, callback)

# 4. Receive indications (automatic via callback)

# 5. Send control (optional)
await manager.send_control_request(node_id, ran_func_id, header, message)

# 6. Stop manager
await manager.stop()
```
