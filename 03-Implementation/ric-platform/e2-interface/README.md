# O-RAN E2 Interface Implementation

This module implements the O-RAN E2 interface for Near-RT RIC integration, based on O-RAN specifications v4.0.0/v4.1.0 (October 2024).

## Overview

The E2 interface connects the Near-RT RIC to E2 Nodes (gNB, eNB, including DU and CU components) for RAN monitoring and control.

### Key Features

- **E2AP Protocol Support**: Full E2 Application Protocol implementation
- **Service Models**: E2SM-KPM (Key Performance Metrics) and E2SM-RC (RAN Control) stubs
- **Connection Management**: SCTP-based transport with health monitoring
- **Subscription Management**: Handle multiple concurrent subscriptions
- **Asynchronous Design**: Built on Python asyncio for scalability

## Architecture

```
┌─────────────────────────────────────────┐
│         Near-RT RIC Platform            │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      E2 Interface Manager        │  │
│  │                                  │  │
│  │  - Connection Management         │  │
│  │  - Subscription Management       │  │
│  │  - Message Routing               │  │
│  └──────────────────────────────────┘  │
│              ↓                          │
│  ┌──────────────────────────────────┐  │
│  │      E2AP Message Handler        │  │
│  │                                  │  │
│  │  - E2 Setup                      │  │
│  │  - RIC Subscription              │  │
│  │  - RIC Indication                │  │
│  │  - RIC Control                   │  │
│  └──────────────────────────────────┘  │
│              ↓                          │
│  ┌──────────────────────────────────┐  │
│  │    E2SM Service Models           │  │
│  │                                  │  │
│  │  - E2SM-KPM (Metrics)            │  │
│  │  - E2SM-RC (Control)             │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
              ↓ SCTP (Port 36421)
┌─────────────────────────────────────────┐
│         E2 Node (gNB)                   │
└─────────────────────────────────────────┘
```

## Components

### Core Modules

1. **e2_messages.py**: E2AP message structures
   - E2SetupRequest/Response
   - RICSubscriptionRequest/Response
   - RICIndication
   - RICControlRequest/Acknowledge

2. **e2sm_kpm.py**: E2SM-KPM service model
   - Measurement types and records
   - KPM indication encoding
   - Event trigger creation

3. **e2_manager.py**: E2 Interface Manager
   - Connection lifecycle management
   - Subscription tracking
   - Message routing to callbacks

## Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup

```bash
# Navigate to project root
cd /home/gnb/thc1006/sdr-o-ran-platform

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic E2 Manager Setup

```python
import asyncio
from e2_manager import E2InterfaceManager

async def main():
    # Create and start E2 manager
    manager = E2InterfaceManager()
    await manager.start()

    # Manager is now ready to accept E2 connections
    print("E2 Interface Manager running...")

    # Keep running
    await asyncio.sleep(3600)

    # Clean shutdown
    await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Handling E2 Setup

```python
from e2_messages import E2SetupRequest, E2NodeComponentConfig
from e2sm_kpm import E2SM_KPM

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
print(f"Setup successful: {response.global_ric_id}")
```

### Creating Subscriptions

```python
from e2_messages import RICIndication

# Define callback for indications
async def indication_callback(indication: RICIndication):
    print(f"Received indication: {indication.ric_request_id}")
    # Process indication data

# Create subscription
subscription_id = await manager.create_subscription(
    node_id="gnb-001",
    ran_function_id=E2SM_KPM.RAN_FUNCTION_ID,
    callback=indication_callback
)

print(f"Subscription created: {subscription_id}")
```

### Working with KPM Measurements

```python
import time
from e2sm_kpm import E2SM_KPM, MeasurementRecord, MeasurementType

# Create measurement records
measurements = [
    MeasurementRecord(
        measurement_type=MeasurementType.DRB_UE_THROUGHPUT_DL,
        value=150.5,  # Mbps
        timestamp=int(time.time() * 1e9),
        ue_id="ue-001",
        cell_id="cell-001"
    ),
    MeasurementRecord(
        measurement_type=MeasurementType.DRB_UE_THROUGHPUT_UL,
        value=80.3,  # Mbps
        timestamp=int(time.time() * 1e9),
        ue_id="ue-001",
        cell_id="cell-001"
    )
]

# Create indication
header, message = E2SM_KPM.create_indication(measurements)
```

## Configuration

See `e2_config_example.yaml` for detailed configuration options.

Key configuration parameters:

- **SCTP Settings**: Port, connections, heartbeat
- **E2AP Settings**: Timeouts, retries
- **Service Models**: Enabled models, parameters
- **Health Checks**: Intervals, timeouts
- **Logging**: Levels, output destinations

## Testing

### Running Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all E2 interface tests
pytest tests/unit/test_e2_interface.py -v

# Run with coverage
pytest tests/unit/test_e2_interface.py --cov=03-Implementation/ric-platform/e2-interface
```

### Test Coverage

Current test coverage: **81.18%**

Covered areas:
- E2 message creation and serialization
- E2SM-KPM measurement encoding
- E2 Manager lifecycle
- E2 Setup handling
- Subscription management

## Development

### Adding New Service Models

To add a new E2 Service Model:

1. Create service model module (e.g., `e2sm_rc.py`)
2. Define RAN function definition
3. Implement encoding/decoding methods
4. Register in E2 Manager
5. Add tests

Example structure:

```python
# e2sm_rc.py
class E2SM_RC:
    RAN_FUNCTION_ID = 2
    RAN_FUNCTION_DEFINITION = { ... }

    @staticmethod
    def create_control_message(...):
        ...
```

### Extending E2 Manager

The E2 Manager can be extended to:

- Add custom message handlers
- Implement additional E2AP procedures
- Add metrics collection
- Integrate with xApps

## API Reference

See [E2-API-REFERENCE.md](/home/gnb/thc1006/sdr-o-ran-platform/docs/architecture/E2-API-REFERENCE.md) for complete API documentation.

## Architecture Documentation

See [E2-INTERFACE-ARCHITECTURE.md](/home/gnb/thc1006/sdr-o-ran-platform/docs/architecture/E2-INTERFACE-ARCHITECTURE.md) for detailed architecture.

## Specifications

This implementation is based on:

- **O-RAN WG3.E2AP-v04.00**: E2 Application Protocol
- **O-RAN WG3.E2SM-KPM-v03.00**: E2 Service Model for KPM
- **O-RAN WG3.E2SM-RC-v01.00**: E2 Service Model for RC
- **ETSI TS 104 039**: E2 Application Protocol (E2AP)
- **ETSI TS 104 040**: E2 Service Model (E2SM)

## Known Limitations

Current implementation limitations:

1. **ASN.1 Encoding**: Uses simplified encoding (JSON/struct) instead of ASN.1 PER
2. **SCTP Transport**: SCTP layer not fully implemented (placeholder)
3. **E2SM-RC**: RAN Control service model is a stub
4. **Security**: TLS/DTLS not implemented
5. **Multi-Instance**: Single RIC instance only

## Roadmap

Planned enhancements:

- [ ] Full ASN.1 PER encoding/decoding
- [ ] Complete SCTP transport implementation
- [ ] E2SM-RC full implementation
- [ ] Additional service models (E2SM-NI, E2SM-RSM)
- [ ] TLS/DTLS security
- [ ] Multi-RIC federation
- [ ] Performance optimizations

## Contributing

To contribute to the E2 interface implementation:

1. Follow Python PEP 8 style guidelines
2. Add unit tests for new features
3. Update documentation
4. Ensure test coverage > 80%

## License

This implementation is part of the SDR O-RAN Platform project.

## Support

For issues and questions:
- Check documentation in `/docs/architecture`
- Review test cases in `/tests/unit`
- Refer to O-RAN specifications

## Acknowledgments

Based on O-RAN Alliance specifications and ETSI standards for 5G RAN.
