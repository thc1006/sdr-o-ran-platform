# xApp Development Guide

## Overview

This guide provides comprehensive instructions for developing xApps (RAN Intelligent Controller Applications) using the O-RAN xApp SDK.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Creating Your First xApp](#creating-your-first-xapp)
5. [xApp Lifecycle](#xapp-lifecycle)
6. [Working with E2 Interface](#working-with-e2-interface)
7. [Shared Data Layer (SDL)](#shared-data-layer-sdl)
8. [Best Practices](#best-practices)

## Introduction

xApps are microservices that run on the Near-RT RIC platform and control RAN functions through the E2 interface. They implement intelligent algorithms for:

- QoS optimization
- Load balancing
- Handover management
- Resource allocation
- Interference management
- And more...

## Architecture

### xApp Components

```
┌─────────────────────────────────────┐
│           xApp Instance             │
├─────────────────────────────────────┤
│  ┌──────────────────────────────┐  │
│  │   Your xApp Logic            │  │
│  │  (inherits XAppBase)         │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   xApp Framework SDK         │  │
│  │  - Lifecycle Management      │  │
│  │  - E2 Interface Handler      │  │
│  │  - Metrics Collection        │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   SDL Client                 │  │
│  │  - Data Sharing              │  │
│  │  - State Persistence         │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
         ↓              ↓
    E2 Interface    Redis (SDL)
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Redis server (for SDL)
- Access to Near-RT RIC platform

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install redis asyncio-mqtt pytest pytest-asyncio
```

### Project Structure

```
ric-platform/
├── xapp-sdk/
│   ├── __init__.py
│   ├── xapp_framework.py    # Base class for xApps
│   ├── sdl_client.py         # Shared Data Layer client
│   └── xapp_manager.py       # xApp lifecycle manager
├── xapps/
│   ├── qos_optimizer_xapp.py
│   ├── handover_manager_xapp.py
│   └── your_xapp.py
├── tests/
│   └── test_*.py
└── docs/
    └── *.md
```

## Creating Your First xApp

### Step 1: Define Configuration

```python
from xapp_sdk import XAppConfig

config = XAppConfig(
    name="my-first-xapp",
    version="1.0.0",
    description="My first xApp for learning",
    e2_subscriptions=[
        {
            "ran_function_id": 1,  # E2SM-KPM
            "event_trigger": {"period_ms": 1000}
        }
    ],
    sdl_namespace="my-xapp"
)
```

### Step 2: Implement xApp Class

```python
from xapp_sdk import XAppBase, XAppConfig, SDLClient
import logging

logger = logging.getLogger(__name__)


class MyFirstXApp(XAppBase):
    """My first xApp implementation"""

    def __init__(self):
        config = XAppConfig(
            name="my-first-xapp",
            version="1.0.0",
            description="My first xApp",
            e2_subscriptions=[{"ran_function_id": 1}],
            sdl_namespace="my-xapp"
        )
        super().__init__(config)
        self.sdl = SDLClient(namespace=config.sdl_namespace)

    async def init(self):
        """Initialize xApp resources"""
        self.logger.info("Initializing My First xApp")
        # Load any previous state
        self.state = self.sdl.get("state") or {}

    async def handle_indication(self, indication):
        """Process E2 indications"""
        self.logger.info(f"Received indication: {indication}")

        # Parse and process the indication
        # Update metrics
        self.update_metric("indications_received", 1)

        # Store state in SDL
        self.sdl.set("state", self.state)
```

### Step 3: Add Main Entry Point

```python
import asyncio

async def main():
    logging.basicConfig(level=logging.INFO)

    xapp = MyFirstXApp()
    await xapp.start()

    try:
        while xapp.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await xapp.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

## xApp Lifecycle

### Lifecycle States

1. **Created** - xApp instance created but not initialized
2. **Initialized** - `init()` called, resources allocated
3. **Running** - xApp is actively processing indications
4. **Stopped** - xApp has been gracefully shut down

### Lifecycle Methods

```python
async def init(self):
    """
    Called once during xApp startup.
    Use for:
    - Loading configuration
    - Connecting to external services
    - Initializing state from SDL
    """
    pass

async def start(self):
    """
    Starts the xApp.
    Automatically calls init() and sets running=True
    """
    pass

async def stop(self):
    """
    Gracefully stops the xApp.
    Use for:
    - Cleanup resources
    - Save state to SDL
    - Close connections
    """
    pass

async def handle_indication(self, indication):
    """
    Called for each E2 indication received.
    Main processing logic goes here.
    """
    pass
```

## Working with E2 Interface

### E2 Service Models

The xApp SDK supports multiple E2 Service Models (E2SM):

- **E2SM-KPM**: Key Performance Measurements
- **E2SM-RC**: RAN Control
- **E2SM-NI**: Network Interface

### Subscribing to E2 Indications

```python
config = XAppConfig(
    name="my-xapp",
    version="1.0.0",
    description="Example xApp",
    e2_subscriptions=[
        {
            "ran_function_id": 1,      # E2SM-KPM
            "event_trigger": {
                "period_ms": 1000       # Report every 1 second
            }
        }
    ],
    sdl_namespace="my-xapp"
)
```

### Processing Indications

```python
async def handle_indication(self, indication):
    """Process E2 indication"""
    # Parse the indication message
    measurements = self._parse_indication(indication)

    for measurement in measurements:
        ue_id = measurement.get("ueId")
        metric_value = measurement.get("value")

        # Process the measurement
        self.logger.info(f"UE {ue_id}: {metric_value}")

        # Make control decisions
        if metric_value < THRESHOLD:
            await self._send_control_request(ue_id)

def _parse_indication(self, indication):
    """Parse indication based on service model"""
    import json
    try:
        message = json.loads(indication.ric_indication_message)
        return message.get("measurements", [])
    except:
        return []
```

### Sending E2 Control Requests

```python
async def _send_control_request(self, ue_id: str):
    """Send E2 Control Request to RAN"""
    self.logger.info(f"Sending control for UE {ue_id}")

    # TODO: Implement E2 Control Request encoding
    # This will be integrated with E2 interface from Agent 1

    # For now, log the action
    control_action = {
        "ue_id": ue_id,
        "action": "adjust_qos",
        "timestamp": datetime.now().isoformat()
    }

    # Store in SDL for tracking
    self.sdl.set(f"control:{ue_id}", control_action)
```

## Shared Data Layer (SDL)

The SDL provides data sharing between xApps using Redis.

### Using SDL Client

```python
from xapp_sdk import SDLClient

# Create SDL client
sdl = SDLClient(
    host="localhost",
    port=6379,
    namespace="my-xapp"
)

# Store data
sdl.set("key1", {"value": 42, "timestamp": "2025-01-01"})

# Retrieve data
data = sdl.get("key1")

# Delete data
sdl.delete("key1")

# List keys
keys = sdl.list_keys("*")
```

### SDL Best Practices

1. **Use Namespaces**: Each xApp should use its own namespace
2. **Keep Data Small**: SDL is for coordination, not bulk storage
3. **Handle Failures**: SDL operations can fail, always check returns
4. **Clean Up**: Delete obsolete data to prevent memory leaks

```python
# Good: Namespaced keys
sdl.set("ue:UE123:metrics", data)

# Good: Check return values
if sdl.set("key", data):
    logger.info("Data stored successfully")
else:
    logger.error("Failed to store data")

# Good: Clean up old data
for key in sdl.list_keys("ue:*"):
    data = sdl.get(key)
    if is_old(data):
        sdl.delete(key)
```

## Metrics and Monitoring

### Updating Metrics

```python
def update_metric(self, name: str, value: float):
    """Update xApp metric"""
    self.metrics[name] = {
        "value": value,
        "timestamp": datetime.now()
    }

# Usage
self.update_metric("ues_monitored", 10)
self.update_metric("avg_throughput_mbps", 45.2)
self.update_metric("handovers_triggered", 3)
```

### Standard Metrics

Common metrics to track:

- `indications_received`: Count of E2 indications processed
- `control_requests_sent`: Count of E2 control requests sent
- `errors`: Count of errors encountered
- `processing_time_ms`: Average processing time
- Domain-specific metrics (throughput, latency, etc.)

## Best Practices

### 1. Error Handling

```python
async def handle_indication(self, indication):
    try:
        measurements = self._parse_indication(indication)
        # Process measurements
    except Exception as e:
        self.logger.error(f"Error processing indication: {e}")
        self.update_metric("errors",
                          self.metrics.get("errors", {}).get("value", 0) + 1)
```

### 2. Logging

```python
# Use structured logging
self.logger.info(f"Processing UE {ue_id}", extra={
    "ue_id": ue_id,
    "cell_id": cell_id,
    "metric": metric_value
})

# Log levels
self.logger.debug("Detailed debug information")
self.logger.info("Normal operation information")
self.logger.warning("Warning about unusual condition")
self.logger.error("Error that needs attention")
```

### 3. Async Programming

```python
# Good: Use async/await properly
async def handle_indication(self, indication):
    await self._process_async(indication)
    await self._send_control()

# Good: Concurrent operations
await asyncio.gather(
    self._task1(),
    self._task2(),
    self._task3()
)
```

### 4. Testing

```python
import pytest

@pytest.mark.asyncio
async def test_xapp_initialization():
    xapp = MyFirstXApp()
    await xapp.init()
    assert xapp.running is False

@pytest.mark.asyncio
async def test_handle_indication():
    xapp = MyFirstXApp()
    await xapp.start()

    indication = create_test_indication()
    await xapp.handle_indication(indication)

    assert "indications_received" in xapp.metrics
```

### 5. Configuration Management

```python
import os
from dataclasses import dataclass

@dataclass
class MyXAppConfig:
    threshold: float = float(os.getenv("THRESHOLD", "10.0"))
    period_ms: int = int(os.getenv("PERIOD_MS", "1000"))
    redis_host: str = os.getenv("REDIS_HOST", "localhost")

# Use in xApp
config = MyXAppConfig()
if value < config.threshold:
    # Take action
```

## Next Steps

1. Review the example xApps:
   - [QoS Optimizer xApp](../xapps/qos_optimizer_xapp.py)
   - [Handover Manager xApp](../xapps/handover_manager_xapp.py)

2. Read the API reference: [SDK_API_REFERENCE.md](SDK_API_REFERENCE.md)

3. Learn about deployment: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

4. Explore advanced topics:
   - Multi-xApp coordination
   - ML model integration
   - Performance optimization

## Support

For questions or issues:
- Check the documentation in `/docs`
- Review example xApps in `/xapps`
- Run tests to verify your implementation

Happy xApp development!
