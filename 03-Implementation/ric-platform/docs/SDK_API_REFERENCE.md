# xApp SDK API Reference

## Overview

Complete API reference for the O-RAN xApp Software Development Kit.

## Table of Contents

1. [XAppConfig](#xappconfig)
2. [XAppBase](#xappbase)
3. [SDLClient](#sdlclient)
4. [XAppManager](#xappmanager)

---

## XAppConfig

Configuration dataclass for xApp instances.

### Class Definition

```python
@dataclass
class XAppConfig:
    """xApp Configuration"""
    name: str
    version: str
    description: str
    e2_subscriptions: List[Dict]
    sdl_namespace: str
    metrics_enabled: bool = True
```

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Unique identifier for the xApp |
| `version` | `str` | Yes | Semantic version (e.g., "1.0.0") |
| `description` | `str` | Yes | Human-readable description |
| `e2_subscriptions` | `List[Dict]` | Yes | E2 subscription configurations |
| `sdl_namespace` | `str` | Yes | SDL namespace for data isolation |
| `metrics_enabled` | `bool` | No | Enable metrics collection (default: True) |

### Example

```python
config = XAppConfig(
    name="qos-optimizer",
    version="1.0.0",
    description="Optimizes QoS based on UE metrics",
    e2_subscriptions=[
        {
            "ran_function_id": 1,
            "event_trigger": {"period_ms": 1000}
        }
    ],
    sdl_namespace="qos-optimizer",
    metrics_enabled=True
)
```

---

## XAppBase

Abstract base class for all xApp implementations.

### Class Definition

```python
class XAppBase(ABC):
    """Base class for all xApps"""
```

### Constructor

```python
def __init__(self, config: XAppConfig)
```

**Parameters:**
- `config`: XAppConfig instance with xApp configuration

**Attributes Created:**
- `self.config`: The XAppConfig instance
- `self.logger`: Logger instance for this xApp
- `self.running`: Boolean indicating if xApp is running
- `self.metrics`: Dictionary of xApp metrics

### Abstract Methods

These methods must be implemented by subclasses:

#### `async def init(self)`

Initialize the xApp. Called once during startup.

**Returns:** None

**Usage:**
```python
async def init(self):
    """Initialize xApp resources"""
    self.logger.info("Initializing xApp")
    # Load state from SDL
    self.state = self.sdl.get("state") or {}
    # Initialize any other resources
```

#### `async def handle_indication(self, indication)`

Handle E2 indications received from RAN.

**Parameters:**
- `indication`: E2 indication message object

**Returns:** None

**Usage:**
```python
async def handle_indication(self, indication):
    """Process E2 indication"""
    measurements = self._parse_indication(indication)
    for m in measurements:
        await self._process_measurement(m)
```

### Concrete Methods

#### `async def start(self)`

Start the xApp. Calls `init()` and sets `running=True`.

**Returns:** None

**Usage:**
```python
xapp = MyXApp()
await xapp.start()
```

#### `async def stop(self)`

Stop the xApp gracefully. Sets `running=False`.

**Returns:** None

**Usage:**
```python
await xapp.stop()
```

#### `def update_metric(self, name: str, value: float)`

Update an xApp metric.

**Parameters:**
- `name`: Metric name (string)
- `value`: Metric value (float)

**Returns:** None

**Usage:**
```python
self.update_metric("ues_monitored", 10)
self.update_metric("avg_throughput_mbps", 45.2)
```

**Metric Format:**
```python
{
    "value": 45.2,
    "timestamp": datetime(2025, 1, 17, 12, 30, 45)
}
```

### Complete Example

```python
class MyXApp(XAppBase):
    def __init__(self):
        config = XAppConfig(
            name="my-xapp",
            version="1.0.0",
            description="My custom xApp",
            e2_subscriptions=[{"ran_function_id": 1}],
            sdl_namespace="my-xapp"
        )
        super().__init__(config)
        self.sdl = SDLClient(namespace=config.sdl_namespace)

    async def init(self):
        self.logger.info("Initializing")
        self.state = {}

    async def handle_indication(self, indication):
        self.logger.info(f"Received: {indication}")
        self.update_metric("indications", 1)
```

---

## SDLClient

Client for interacting with the Shared Data Layer (Redis).

### Class Definition

```python
class SDLClient:
    """Shared Data Layer Client"""
```

### Constructor

```python
def __init__(self, host: str = "localhost", port: int = 6379, namespace: str = "xapp")
```

**Parameters:**
- `host`: Redis server hostname (default: "localhost")
- `port`: Redis server port (default: 6379)
- `namespace`: Namespace for key isolation (default: "xapp")

### Methods

#### `def set(self, key: str, value: Dict) -> bool`

Store data in SDL.

**Parameters:**
- `key`: Key name (string)
- `value`: Data to store (dictionary)

**Returns:** `True` if successful, `False` otherwise

**Usage:**
```python
sdl = SDLClient(namespace="my-xapp")
success = sdl.set("ue:UE123", {
    "throughput": 45.2,
    "timestamp": "2025-01-17T12:30:45"
})
```

#### `def get(self, key: str) -> Optional[Dict]`

Retrieve data from SDL.

**Parameters:**
- `key`: Key name (string)

**Returns:** Dictionary if key exists, `None` otherwise

**Usage:**
```python
data = sdl.get("ue:UE123")
if data:
    print(f"Throughput: {data['throughput']}")
else:
    print("Key not found")
```

#### `def delete(self, key: str) -> bool`

Delete data from SDL.

**Parameters:**
- `key`: Key name (string)

**Returns:** `True` if successful, `False` otherwise

**Usage:**
```python
sdl.delete("ue:UE123")
```

#### `def list_keys(self, pattern: str = "*") -> List[str]`

List keys matching a pattern.

**Parameters:**
- `pattern`: Glob pattern (default: "*")

**Returns:** List of matching keys (without namespace prefix)

**Usage:**
```python
# List all UE keys
ue_keys = sdl.list_keys("ue:*")

# List all keys
all_keys = sdl.list_keys("*")
```

### Key Namespacing

All keys are automatically prefixed with the namespace:

```python
sdl = SDLClient(namespace="my-xapp")

# Store with key "config"
sdl.set("config", {"version": "1.0"})

# Actual Redis key: "my-xapp:config"
```

### Error Handling

All SDL operations include error handling:

```python
try:
    result = sdl.set("key", value)
    if result:
        logger.info("Data stored")
    else:
        logger.error("Storage failed")
except Exception as e:
    logger.error(f"SDL error: {e}")
```

---

## XAppManager

Manages xApp lifecycle, deployment, and monitoring.

### Class Definition

```python
class XAppManager:
    """Manages xApp lifecycle"""
```

### Constructor

```python
def __init__(self)
```

**Attributes:**
- `self.xapps`: Dictionary of deployed xApps (name -> XAppBase)
- `self.running`: Boolean indicating if manager is running

### Methods

#### `async def deploy_xapp(self, xapp: XAppBase) -> bool`

Deploy and start an xApp.

**Parameters:**
- `xapp`: XAppBase instance to deploy

**Returns:** `True` if successful, `False` if already deployed

**Usage:**
```python
manager = XAppManager()
xapp = MyXApp()
success = await manager.deploy_xapp(xapp)
```

#### `async def undeploy_xapp(self, xapp_name: str) -> bool`

Stop and remove an xApp.

**Parameters:**
- `xapp_name`: Name of xApp to undeploy

**Returns:** `True` if successful, `False` if not found

**Usage:**
```python
success = await manager.undeploy_xapp("qos-optimizer")
```

#### `def list_xapps(self) -> List[Dict]`

List all deployed xApps.

**Returns:** List of xApp status dictionaries

**Usage:**
```python
xapps = manager.list_xapps()
for xapp in xapps:
    print(f"{xapp['name']}: {xapp['version']} - Running: {xapp['running']}")
```

**Return Format:**
```python
[
    {
        "name": "qos-optimizer",
        "version": "1.0.0",
        "running": True,
        "metrics": {
            "ues_monitored": {"value": 10, "timestamp": ...}
        }
    }
]
```

#### `def get_xapp_status(self, xapp_name: str) -> Dict`

Get detailed status of a specific xApp.

**Parameters:**
- `xapp_name`: Name of xApp

**Returns:** Dictionary with xApp status or error

**Usage:**
```python
status = manager.get_xapp_status("qos-optimizer")
if "error" not in status:
    print(f"Version: {status['version']}")
    print(f"Running: {status['running']}")
    print(f"Metrics: {status['metrics']}")
```

**Success Format:**
```python
{
    "name": "qos-optimizer",
    "version": "1.0.0",
    "description": "Optimizes QoS based on UE metrics",
    "running": True,
    "metrics": {...}
}
```

**Error Format:**
```python
{
    "error": "xApp not found"
}
```

### Complete Example

```python
import asyncio
from xapp_sdk import XAppManager
from xapps import QoSOptimizerXApp, HandoverManagerXApp

async def main():
    manager = XAppManager()

    # Deploy xApps
    qos_xapp = QoSOptimizerXApp()
    ho_xapp = HandoverManagerXApp()

    await manager.deploy_xapp(qos_xapp)
    await manager.deploy_xapp(ho_xapp)

    # List deployed xApps
    for xapp in manager.list_xapps():
        print(f"Deployed: {xapp['name']}")

    # Get status
    status = manager.get_xapp_status("qos-optimizer")
    print(f"QoS xApp metrics: {status['metrics']}")

    # Run for some time
    await asyncio.sleep(60)

    # Undeploy
    await manager.undeploy_xapp("qos-optimizer")
    await manager.undeploy_xapp("handover-manager")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Type Definitions

### E2 Subscription Configuration

```python
{
    "ran_function_id": int,      # E2SM identifier (1=KPM, 2=RC, etc.)
    "event_trigger": {
        "period_ms": int         # Reporting period in milliseconds
    }
}
```

### Indication Message Format

```python
{
    "ric_indication_message": str,  # JSON-encoded measurement data
    "ric_indication_header": str,   # Indication metadata
    "ric_indication_sn": int        # Sequence number
}
```

### Measurement Format

```python
{
    "ueId": str,           # UE identifier
    "cellId": str,         # Cell identifier
    "value": float,        # Measurement value
    "timestamp": str,      # ISO format timestamp
    "type": str            # Measurement type
}
```

---

## Constants and Enumerations

### RAN Function IDs

```python
RAN_FUNCTION_KPM = 1   # E2SM-KPM: Key Performance Measurements
RAN_FUNCTION_RC = 2    # E2SM-RC: RAN Control
RAN_FUNCTION_NI = 3    # E2SM-NI: Network Interface
```

### Common Metric Names

```python
METRIC_INDICATIONS_RECEIVED = "indications_received"
METRIC_CONTROLS_SENT = "controls_sent"
METRIC_ERRORS = "errors"
METRIC_PROCESSING_TIME_MS = "processing_time_ms"
```

---

## Error Handling

### Common Exceptions

The SDK uses standard Python exceptions:

- `ValueError`: Invalid configuration or parameters
- `ConnectionError`: SDL or E2 connection issues
- `TimeoutError`: Operation timeout
- `RuntimeError`: General runtime errors

### Best Practices

```python
try:
    await xapp.start()
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    await xapp.stop()
```

---

## Version History

- **1.0.0** (2025-01-17): Initial release
  - XAppBase framework
  - SDLClient implementation
  - XAppManager lifecycle management
  - E2 indication handling

---

## See Also

- [xApp Development Guide](XAPP_DEVELOPMENT_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Example xApps](EXAMPLE_XAPPS.md)
