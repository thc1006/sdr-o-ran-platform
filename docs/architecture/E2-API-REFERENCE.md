# E2 Interface API Reference

## Overview
This document provides detailed API reference for the O-RAN E2 Interface implementation.

## Table of Contents
- [E2 Messages](#e2-messages)
- [E2SM-KPM Service Model](#e2sm-kpm-service-model)
- [E2 Interface Manager](#e2-interface-manager)
- [Usage Examples](#usage-examples)

## E2 Messages

### E2SetupRequest

**Description**: Initial setup message from E2 Node to Near-RT RIC.

**Attributes**:
- `transaction_id` (int): Unique transaction identifier
- `global_e2_node_id` (str): Global E2 Node identifier (e.g., "gnb-001")
- `ran_functions` (List[Dict]): List of supported RAN functions
- `e2_node_component_config` (List[E2NodeComponentConfig]): Node component configuration

**Methods**:
- `to_dict() -> Dict`: Convert to dictionary representation

**Example**:
```python
from e2_messages import E2SetupRequest, E2NodeComponentConfig
from e2sm_kpm import E2SM_KPM

request = E2SetupRequest(
    transaction_id=1,
    global_e2_node_id="gnb-001",
    ran_functions=[E2SM_KPM.RAN_FUNCTION_DEFINITION],
    e2_node_component_config=[
        E2NodeComponentConfig("DU", 1),
        E2NodeComponentConfig("CU-CP", 2)
    ]
)
```

### E2SetupResponse

**Description**: Response from Near-RT RIC to E2 Setup Request.

**Attributes**:
- `transaction_id` (int): Matching transaction identifier
- `global_ric_id` (str): Global RIC identifier
- `ran_functions_accepted` (List[int]): List of accepted RAN function IDs

**Methods**:
- `to_dict() -> Dict`: Convert to dictionary representation

### RICSubscriptionRequest

**Description**: Subscription request from Near-RT RIC to E2 Node.

**Attributes**:
- `ric_request_id` (int): Subscription identifier
- `ran_function_id` (int): RAN function to subscribe to
- `ric_event_trigger_definition` (bytes): Event trigger configuration (E2SM-specific)
- `ric_action_list` (List[Dict]): List of RIC actions to execute

**Methods**:
- `to_dict() -> Dict`: Convert to dictionary representation

**Example**:
```python
from e2_messages import RICSubscriptionRequest
from e2sm_kpm import E2SM_KPM

request = RICSubscriptionRequest(
    ric_request_id=1,
    ran_function_id=E2SM_KPM.RAN_FUNCTION_ID,
    ric_event_trigger_definition=E2SM_KPM.create_event_trigger(1000),
    ric_action_list=[
        {"ricActionId": 1, "ricActionType": "REPORT"}
    ]
)
```

### RICIndication

**Description**: Indication message from E2 Node to Near-RT RIC containing measurements or events.

**Attributes**:
- `ric_request_id` (int): Subscription identifier
- `ran_function_id` (int): RAN function ID
- `ric_action_id` (int): Action identifier
- `ric_indication_header` (bytes): Indication header (E2SM-specific)
- `ric_indication_message` (bytes): Indication message (E2SM-specific)
- `ric_call_process_id` (Optional[bytes]): Call process identifier

**Methods**:
- `to_dict() -> Dict`: Convert to dictionary representation

### RICControlRequest

**Description**: Control request from Near-RT RIC to E2 Node.

**Attributes**:
- `ric_request_id` (int): Request identifier
- `ran_function_id` (int): RAN function ID
- `ric_call_process_id` (Optional[bytes]): Call process identifier
- `ric_control_header` (bytes): Control header (E2SM-specific)
- `ric_control_message` (bytes): Control message (E2SM-specific)
- `ric_control_ack_request` (bool): Whether acknowledgement is required

**Methods**:
- `to_dict() -> Dict`: Convert to dictionary representation

## E2SM-KPM Service Model

### E2SM_KPM Class

**Description**: E2 Service Model for Key Performance Metrics.

**Constants**:
- `RAN_FUNCTION_ID = 1`: RAN Function identifier for KPM
- `RAN_FUNCTION_DEFINITION`: Full RAN function definition

**Static Methods**:

#### create_event_trigger(period_ms: int) -> bytes

Creates event trigger definition for periodic reporting.

**Parameters**:
- `period_ms` (int): Reporting period in milliseconds

**Returns**:
- bytes: Encoded event trigger definition

**Example**:
```python
trigger = E2SM_KPM.create_event_trigger(1000)  # 1 second period
```

#### create_indication(measurements: List[MeasurementRecord]) -> tuple

Creates indication header and message from measurement records.

**Parameters**:
- `measurements` (List[MeasurementRecord]): List of measurement records

**Returns**:
- tuple: (header_bytes, message_bytes)

**Example**:
```python
from e2sm_kpm import E2SM_KPM, MeasurementRecord, MeasurementType

measurements = [
    MeasurementRecord(
        measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
        value=150.5,
        timestamp=int(time.time() * 1e9),
        ue_id="ue-001",
        cell_id="cell-001"
    )
]

header, message = E2SM_KPM.create_indication(measurements)
```

### MeasurementType Enum

**Description**: Supported measurement types.

**Values**:
- `DRB_UE_THROUGHPUT_DL = "DRB.UEThpDl"`: UE throughput downlink
- `DRB_UE_THROUGHPUT_UL = "DRB.UEThpUl"`: UE throughput uplink
- `RRC_CONN_ESTAB_SUCC = "RRC.ConnEstabSucc"`: RRC connection success count
- `RRC_CONN_ESTAB_ATT = "RRC.ConnEstabAtt"`: RRC connection attempt count
- `HANDOVER_SUCC_RATE = "HANDOVER.SuccRate"`: Handover success rate

### MeasurementRecord Class

**Description**: Single measurement record.

**Attributes**:
- `measurement_type` (MeasurementType): Type of measurement
- `value` (float): Measurement value
- `timestamp` (int): Unix timestamp in nanoseconds
- `ue_id` (Optional[str]): UE identifier
- `cell_id` (Optional[str]): Cell identifier

**Example**:
```python
import time
from e2sm_kpm import MeasurementRecord, MeasurementType

record = MeasurementRecord(
    measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
    value=100.5,
    timestamp=int(time.time() * 1e9),
    ue_id="ue-001",
    cell_id="cell-001"
)
```

## E2 Interface Manager

### E2InterfaceManager Class

**Description**: Main manager for E2 interface connections and subscriptions.

**Attributes**:
- `connected_nodes` (Dict[str, E2Node]): Connected E2 nodes
- `subscriptions` (Dict[int, E2Subscription]): Active subscriptions
- `next_subscription_id` (int): Next subscription ID
- `running` (bool): Manager running state

### Methods

#### async start()

Start the E2 Interface Manager and background tasks.

**Example**:
```python
manager = E2InterfaceManager()
await manager.start()
```

#### async stop()

Stop the E2 Interface Manager.

**Example**:
```python
await manager.stop()
```

#### async handle_e2_setup(request: E2SetupRequest) -> E2SetupResponse

Handle E2 Setup Request from E2 Node.

**Parameters**:
- `request` (E2SetupRequest): E2 setup request

**Returns**:
- E2SetupResponse: Setup response

**Example**:
```python
request = E2SetupRequest(...)
response = await manager.handle_e2_setup(request)
```

#### async create_subscription(node_id: str, ran_function_id: int, callback: Callable) -> int

Create a RIC subscription.

**Parameters**:
- `node_id` (str): E2 Node identifier
- `ran_function_id` (int): RAN function ID to subscribe to
- `callback` (Callable): Callback function for indications

**Returns**:
- int: Subscription ID

**Example**:
```python
async def indication_callback(indication: RICIndication):
    print(f"Received indication: {indication}")

subscription_id = await manager.create_subscription(
    node_id="gnb-001",
    ran_function_id=E2SM_KPM.RAN_FUNCTION_ID,
    callback=indication_callback
)
```

#### async handle_ric_indication(indication: RICIndication)

Handle RIC Indication from E2 Node.

**Parameters**:
- `indication` (RICIndication): RIC indication message

**Example**:
```python
await manager.handle_ric_indication(indication)
```

#### async send_control_request(node_id: str, ran_function_id: int, control_header: bytes, control_message: bytes) -> bool

Send RIC Control Request to E2 Node.

**Parameters**:
- `node_id` (str): E2 Node identifier
- `ran_function_id` (int): RAN function ID
- `control_header` (bytes): Control header
- `control_message` (bytes): Control message

**Returns**:
- bool: Success status

**Example**:
```python
success = await manager.send_control_request(
    node_id="gnb-001",
    ran_function_id=2,
    control_header=b"...",
    control_message=b"..."
)
```

## Usage Examples

### Complete E2 Setup Flow

```python
import asyncio
from e2_manager import E2InterfaceManager
from e2_messages import E2SetupRequest, E2NodeComponentConfig
from e2sm_kpm import E2SM_KPM

async def main():
    # Initialize E2 Manager
    manager = E2InterfaceManager()
    await manager.start()

    # Simulate E2 Node sending setup request
    request = E2SetupRequest(
        transaction_id=1,
        global_e2_node_id="gnb-001",
        ran_functions=[E2SM_KPM.RAN_FUNCTION_DEFINITION],
        e2_node_component_config=[
            E2NodeComponentConfig("DU", 1)
        ]
    )

    # Handle setup
    response = await manager.handle_e2_setup(request)
    print(f"E2 Setup Response: {response.to_dict()}")

    await manager.stop()

asyncio.run(main())
```

### Creating Subscription and Handling Indications

```python
import asyncio
from e2_manager import E2InterfaceManager
from e2_messages import RICIndication
from e2sm_kpm import E2SM_KPM

async def indication_callback(indication: RICIndication):
    """Callback for handling indications"""
    print(f"Received indication from subscription {indication.ric_request_id}")
    print(f"RAN Function: {indication.ran_function_id}")
    print(f"Header: {indication.ric_indication_header.hex()}")
    print(f"Message: {indication.ric_indication_message.hex()}")

async def main():
    manager = E2InterfaceManager()
    await manager.start()

    # Create subscription
    subscription_id = await manager.create_subscription(
        node_id="gnb-001",
        ran_function_id=E2SM_KPM.RAN_FUNCTION_ID,
        callback=indication_callback
    )

    print(f"Created subscription: {subscription_id}")

    # Keep running to receive indications
    await asyncio.sleep(60)

    await manager.stop()

asyncio.run(main())
```

### Sending Control Request

```python
import asyncio
from e2_manager import E2InterfaceManager

async def main():
    manager = E2InterfaceManager()
    await manager.start()

    # Create control header and message
    control_header = b"\x01\x02\x03"  # Example header
    control_message = b"\x04\x05\x06"  # Example message

    # Send control request
    success = await manager.send_control_request(
        node_id="gnb-001",
        ran_function_id=2,  # E2SM-RC
        control_header=control_header,
        control_message=control_message
    )

    print(f"Control request {'succeeded' if success else 'failed'}")

    await manager.stop()

asyncio.run(main())
```

### Creating and Encoding KPM Measurements

```python
import time
from e2sm_kpm import E2SM_KPM, MeasurementRecord, MeasurementType

# Create measurement records
measurements = [
    MeasurementRecord(
        measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
        value=150.5,
        timestamp=int(time.time() * 1e9),
        ue_id="ue-001",
        cell_id="cell-001"
    ),
    MeasurementRecord(
        measurement_type=MeasurementType.DRB_UE_THROUGHPUT_UL,
        value=80.3,
        timestamp=int(time.time() * 1e9),
        ue_id="ue-001",
        cell_id="cell-001"
    ),
    MeasurementRecord(
        measurement_type=MeasurementType.RRC_CONN_ESTAB_SUCC,
        value=100,
        timestamp=int(time.time() * 1e9),
        cell_id="cell-001"
    )
]

# Create indication
header, message = E2SM_KPM.create_indication(measurements)

print(f"Header length: {len(header)} bytes")
print(f"Message length: {len(message)} bytes")
print(f"Header (hex): {header.hex()}")
print(f"Message: {message.decode('utf-8')}")
```

## Error Handling

### Connection Errors

```python
async def handle_setup_with_error_handling():
    manager = E2InterfaceManager()

    try:
        await manager.start()

        request = E2SetupRequest(...)
        response = await manager.handle_e2_setup(request)

    except Exception as e:
        print(f"Setup failed: {e}")
    finally:
        await manager.stop()
```

### Subscription Errors

```python
async def create_subscription_safely():
    manager = E2InterfaceManager()
    await manager.start()

    # Check if node is connected
    if "gnb-001" not in manager.connected_nodes:
        print("Node not connected")
        return

    try:
        subscription_id = await manager.create_subscription(
            node_id="gnb-001",
            ran_function_id=E2SM_KPM.RAN_FUNCTION_ID,
            callback=indication_callback
        )
        print(f"Subscription created: {subscription_id}")
    except Exception as e:
        print(f"Subscription failed: {e}")
```

## Best Practices

1. **Always use async/await**: All E2 Manager methods are asynchronous
2. **Clean shutdown**: Always call `stop()` to clean up resources
3. **Error handling**: Wrap E2 operations in try-except blocks
4. **Logging**: Enable logging to debug E2 interface issues
5. **Callback functions**: Keep indication callbacks lightweight and non-blocking
6. **Thread safety**: E2 Manager uses asyncio, not thread-safe

## Configuration Example

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Use E2 Manager
manager = E2InterfaceManager()
```
