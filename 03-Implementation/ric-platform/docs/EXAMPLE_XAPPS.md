# Example xApps Walkthrough

## Overview

This document provides detailed walkthroughs of the example xApps included in the SDK:

1. **QoS Optimizer xApp** - Monitors UE throughput and adjusts QoS parameters
2. **Handover Manager xApp** - Makes intelligent handover decisions

## QoS Optimizer xApp

### Purpose

The QoS Optimizer xApp monitors User Equipment (UE) throughput metrics and dynamically adjusts Quality of Service (QoS) parameters to ensure optimal performance.

### Architecture

```
┌─────────────────────────────────────┐
│      QoS Optimizer xApp             │
├─────────────────────────────────────┤
│  E2 Indications (KPM)               │
│       ↓                             │
│  Parse Throughput Metrics           │
│       ↓                             │
│  Check Against Thresholds           │
│       ↓                             │
│  Decision: Increase/Decrease QoS    │
│       ↓                             │
│  Send E2 Control Request            │
│       ↓                             │
│  Store in SDL & Update Metrics      │
└─────────────────────────────────────┘
```

### Configuration

```python
config = XAppConfig(
    name="qos-optimizer",
    version="1.0.0",
    description="Optimizes QoS based on UE throughput metrics",
    e2_subscriptions=[
        {
            "ran_function_id": 1,  # E2SM-KPM
            "event_trigger": {"period_ms": 1000}
        }
    ],
    sdl_namespace="qos-optimizer"
)
```

**Key Parameters:**
- Subscribes to E2SM-KPM (RAN Function ID 1)
- Reports every 1 second (1000ms)
- Uses isolated SDL namespace "qos-optimizer"

### Initialization

```python
async def init(self):
    """Initialize xApp"""
    self.logger.info("QoS Optimizer xApp initializing...")
    # Load previous state from SDL
    stored_metrics = self.sdl.get("ue_metrics")
    if stored_metrics:
        self.ue_metrics = stored_metrics
        self.logger.info(f"Loaded {len(self.ue_metrics)} UE metrics from SDL")
```

**What happens:**
1. Logs initialization message
2. Attempts to load previous UE metrics from SDL
3. Restores state for seamless restart

### Processing Flow

#### Step 1: Receive E2 Indication

```python
async def handle_indication(self, indication):
    """Handle E2 indication with UE metrics"""
    # Parse KPM indication
    measurements = self._parse_kpm_indication(indication)
```

#### Step 2: Update UE Metrics

```python
for measurement in measurements:
    ue_id = measurement.get("ueId")
    if not ue_id:
        continue

    # Update UE metrics
    self.ue_metrics[ue_id] = {
        "throughput_dl_mbps": measurement.get("value", 0.0),
        "timestamp": measurement.get("timestamp"),
        "cell_id": measurement.get("cellId")
    }

    # Check if QoS adjustment needed
    await self._check_qos_adjustment(ue_id)
```

#### Step 3: Check QoS Adjustment

```python
async def _check_qos_adjustment(self, ue_id: str):
    """Check if QoS adjustment is needed for UE"""
    metrics = self.ue_metrics.get(ue_id)
    if not metrics:
        return

    throughput = metrics["throughput_dl_mbps"]

    if throughput < self.THROUGHPUT_THRESHOLD_MBPS:
        # Low throughput - increase priority
        await self._send_qos_control(ue_id, increase_priority=True)
    elif throughput > self.THROUGHPUT_THRESHOLD_MBPS * 2:
        # Very high throughput - can reduce priority
        await self._send_qos_control(ue_id, increase_priority=False)
```

**Decision Logic:**
- If throughput < 10 Mbps: Increase QoS priority
- If throughput > 20 Mbps: Decrease QoS priority (free resources)
- Otherwise: No action needed

#### Step 4: Send Control Request

```python
async def _send_qos_control(self, ue_id: str, increase_priority: bool):
    """Send E2 Control Request to adjust QoS"""
    action = "increase" if increase_priority else "decrease"
    self.logger.info(f"Sending QoS control to {action} priority for UE {ue_id}")

    # Store control action in SDL for monitoring
    control_action = {
        "ue_id": ue_id,
        "action": action,
        "timestamp": datetime.now().isoformat()
    }
    self.sdl.set(f"control_action:{ue_id}", control_action)

    # Update metric
    metric_name = "qos_controls_sent"
    current = self.metrics.get(metric_name, {}).get("value", 0)
    self.update_metric(metric_name, current + 1)
```

### Key Features

1. **State Persistence**: UE metrics stored in SDL
2. **Adaptive Thresholds**: Configurable throughput thresholds
3. **Metrics Tracking**: Counts UEs monitored and controls sent
4. **Graceful Degradation**: Handles missing data gracefully

### Usage Example

```python
import asyncio
from qos_optimizer_xapp import QoSOptimizerXApp

async def main():
    xapp = QoSOptimizerXApp()
    await xapp.start()

    try:
        while xapp.running:
            # Check metrics
            ues = xapp.metrics.get("ues_monitored", {}).get("value", 0)
            controls = xapp.metrics.get("qos_controls_sent", {}).get("value", 0)
            print(f"UEs: {ues}, Controls: {controls}")

            await asyncio.sleep(5)
    except KeyboardInterrupt:
        await xapp.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Customization Points

1. **Threshold Tuning**:
```python
THROUGHPUT_THRESHOLD_MBPS = 15.0  # Change threshold
```

2. **Additional Metrics**:
```python
# Add latency monitoring
if metrics.get("latency_ms", 0) > MAX_LATENCY:
    await self._send_qos_control(ue_id, increase_priority=True)
```

3. **Hysteresis**:
```python
# Avoid oscillation
if throughput < threshold - HYSTERESIS:
    increase_qos()
elif throughput > threshold + HYSTERESIS:
    decrease_qos()
```

---

## Handover Manager xApp

### Purpose

The Handover Manager xApp makes intelligent handover decisions based on:
- Signal quality (RSRP - Reference Signal Received Power)
- Cell load distribution
- Neighbor cell availability

### Architecture

```
┌─────────────────────────────────────┐
│    Handover Manager xApp            │
├─────────────────────────────────────┤
│  E2 Indications                     │
│    ↓                                │
│  Parse RSRP & Cell Load             │
│    ↓                                │
│  Evaluate Handover Need             │
│    ↓                                │
│  ┌──────────────┬─────────────┐    │
│  │ Poor Signal? │ Cell Loaded?│    │
│  └──────────────┴─────────────┘    │
│         ↓              ↓            │
│  Find Best      Find Least          │
│  Neighbor       Loaded Cell         │
│         ↓              ↓            │
│  Trigger Handover Decision          │
│         ↓                           │
│  Store in SDL & Update Metrics      │
└─────────────────────────────────────┘
```

### Configuration

```python
config = XAppConfig(
    name="handover-manager",
    version="1.0.0",
    description="Intelligent handover decision making",
    e2_subscriptions=[
        {
            "ran_function_id": 1,  # E2SM-KPM for metrics
            "event_trigger": {"period_ms": 500}
        }
    ],
    sdl_namespace="handover-manager"
)
```

**Key Parameters:**
- Fast reporting period (500ms) for quick handover decisions
- Tracks both UE measurements and cell load

### Data Structures

```python
# UE measurements
self.ue_measurements = {
    "UE1": {
        "serving_cell": "Cell1",
        "rsrp_dbm": -105,
        "neighbor_cells": [
            {"cell_id": "Cell2", "rsrp": -100},
            {"cell_id": "Cell3", "rsrp": -108}
        ]
    }
}

# Cell load tracking
self.cell_load = {
    "Cell1": 85.0,  # 85% loaded
    "Cell2": 50.0,  # 50% loaded
    "Cell3": 70.0   # 70% loaded
}
```

### Processing Flow

#### Step 1: Handle Different Measurement Types

```python
async def handle_indication(self, indication):
    """Handle E2 indication"""
    measurements = self._parse_indication(indication)

    for m in measurements:
        ue_id = m.get("ueId")
        cell_id = m.get("cellId")

        if "rsrp" in m:
            # Signal strength measurement
            self.ue_measurements[ue_id] = {
                "serving_cell": cell_id,
                "rsrp_dbm": m["rsrp"],
                "neighbor_cells": m.get("neighborCells", [])
            }
            await self._evaluate_handover(ue_id)

        elif "cellLoad" in m:
            # Cell load measurement
            self.cell_load[cell_id] = m["cellLoad"]
```

#### Step 2: Evaluate Handover Need

```python
async def _evaluate_handover(self, ue_id: str):
    """Evaluate if handover is needed for UE"""
    ue_data = self.ue_measurements.get(ue_id)
    if not ue_data:
        return

    serving_rsrp = ue_data["rsrp_dbm"]
    serving_cell = ue_data["serving_cell"]

    # Check 1: Poor signal quality?
    if serving_rsrp < self.RSRP_THRESHOLD_DBM:
        best_neighbor = self._find_best_neighbor(ue_data)
        if best_neighbor:
            await self._trigger_handover(
                ue_id,
                source_cell=serving_cell,
                target_cell=best_neighbor["cell_id"],
                reason="poor_signal"
            )

    # Check 2: Cell overloaded?
    if self.cell_load[serving_cell] > self.CELL_LOAD_THRESHOLD_PERCENT:
        best_neighbor = self._find_least_loaded_neighbor(ue_data)
        if best_neighbor:
            await self._trigger_handover(
                ue_id,
                source_cell=serving_cell,
                target_cell=best_neighbor["cell_id"],
                reason="load_balancing"
            )
```

**Two Handover Triggers:**
1. **Signal-based**: RSRP below -110 dBm
2. **Load-based**: Serving cell above 80% capacity

#### Step 3: Find Best Neighbor (Signal Quality)

```python
def _find_best_neighbor(self, ue_data: dict) -> dict:
    """Find neighbor cell with best signal"""
    neighbors = ue_data.get("neighbor_cells", [])
    if not neighbors:
        return None

    # Sort by RSRP (highest first)
    neighbors.sort(key=lambda x: x.get("rsrp", -999), reverse=True)

    best = neighbors[0]
    # Only handover if neighbor is significantly better (5 dB margin)
    if best.get("rsrp", -999) > ue_data["rsrp_dbm"] + 5:
        return best
    return None
```

**Logic:**
- Requires 5 dB improvement to avoid ping-pong effect
- Selects neighbor with strongest signal

#### Step 4: Find Least Loaded Neighbor

```python
def _find_least_loaded_neighbor(self, ue_data: dict) -> dict:
    """Find least loaded neighbor cell"""
    neighbors = ue_data.get("neighbor_cells", [])
    if not neighbors:
        return None

    # Filter neighbors with acceptable signal
    acceptable = [
        n for n in neighbors
        if n.get("rsrp", -999) > self.RSRP_THRESHOLD_DBM + 10
    ]

    if not acceptable:
        return None

    # Find least loaded
    least_loaded = min(
        acceptable,
        key=lambda x: self.cell_load.get(x["cell_id"], 100)
    )

    return least_loaded
```

**Logic:**
- Only consider neighbors with good signal (RSRP > -100 dBm)
- Select neighbor with lowest load

#### Step 5: Trigger Handover

```python
async def _trigger_handover(self, ue_id: str, source_cell: str,
                           target_cell: str, reason: str):
    """Trigger handover via E2 Control"""
    self.logger.info(
        f"Triggering handover for {ue_id}: {source_cell} -> {target_cell} ({reason})"
    )

    # Store handover decision in SDL
    decision = {
        "ue_id": ue_id,
        "source_cell": source_cell,
        "target_cell": target_cell,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    self.sdl.set(f"handover:{ue_id}", decision)

    # Update metric
    metric_name = "handovers_triggered"
    current = self.metrics.get(metric_name, {}).get("value", 0)
    self.update_metric(metric_name, current + 1)
```

### Key Features

1. **Multi-Criteria Decision**: Signal quality + load balancing
2. **Hysteresis Protection**: 5 dB margin prevents ping-pong
3. **Signal Quality Guard**: Won't handover to weak cells
4. **Metrics Tracking**: Counts active UEs and handovers

### Usage Example

```python
import asyncio
from handover_manager_xapp import HandoverManagerXApp

async def main():
    xapp = HandoverManagerXApp()
    await xapp.start()

    try:
        while xapp.running:
            # Monitor handover activity
            active_ues = xapp.metrics.get("active_ues", {}).get("value", 0)
            handovers = xapp.metrics.get("handovers_triggered", {}).get("value", 0)

            print(f"Active UEs: {active_ues}, Handovers: {handovers}")

            # Check recent handover decisions
            for key in xapp.sdl.list_keys("handover:*"):
                decision = xapp.sdl.get(key)
                print(f"Handover: {decision}")

            await asyncio.sleep(5)
    except KeyboardInterrupt:
        await xapp.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Customization Points

1. **Threshold Tuning**:
```python
RSRP_THRESHOLD_DBM = -105  # More aggressive handover
CELL_LOAD_THRESHOLD_PERCENT = 70  # Earlier load balancing
```

2. **Hysteresis Adjustment**:
```python
RSRP_HYSTERESIS_DB = 3  # Smaller margin for faster handover
```

3. **Additional Criteria**:
```python
# Add throughput consideration
if neighbor_throughput > serving_throughput * 1.5:
    trigger_handover()

# Add latency consideration
if neighbor_latency < serving_latency * 0.8:
    trigger_handover()
```

4. **Blacklisting**:
```python
# Avoid problematic cells
self.blacklisted_cells = set()

def _find_best_neighbor(self, ue_data):
    neighbors = [n for n in ue_data["neighbor_cells"]
                 if n["cell_id"] not in self.blacklisted_cells]
    # ... rest of logic
```

---

## Comparing the Two xApps

| Feature | QoS Optimizer | Handover Manager |
|---------|---------------|------------------|
| **Primary Goal** | Optimize resource allocation | Optimize cell selection |
| **Trigger** | Throughput thresholds | Signal quality & load |
| **Update Period** | 1000ms | 500ms (faster) |
| **Decision Criteria** | Single (throughput) | Multiple (RSRP + load) |
| **Control Action** | QoS parameter adjustment | Handover command |
| **Complexity** | Simple threshold-based | Multi-criteria optimization |

---

## Testing the Example xApps

### Unit Testing

```bash
# Run all tests
pytest tests/

# Run specific xApp tests
pytest tests/test_qos_optimizer_xapp.py
pytest tests/test_handover_manager_xapp.py

# With coverage
pytest --cov=xapps tests/
```

### Integration Testing

```python
# Test both xApps together
async def test_integration():
    manager = XAppManager()

    qos_xapp = QoSOptimizerXApp()
    ho_xapp = HandoverManagerXApp()

    await manager.deploy_xapp(qos_xapp)
    await manager.deploy_xapp(ho_xapp)

    # Simulate E2 indications
    indication = create_test_indication()
    await qos_xapp.handle_indication(indication)
    await ho_xapp.handle_indication(indication)

    # Verify coordination via SDL
    # Both xApps should be able to see each other's decisions
```

---

## Best Practices Demonstrated

1. **State Persistence**: Both xApps use SDL for state
2. **Metrics Collection**: Track key performance indicators
3. **Graceful Degradation**: Handle missing data
4. **Logging**: Structured logging for debugging
5. **Error Handling**: Try-except blocks in parsing
6. **Configurability**: Threshold constants easily adjustable

---

## Next Steps

1. **Extend the xApps**:
   - Add ML-based predictions
   - Implement advanced algorithms
   - Add multi-cell coordination

2. **Create Your Own**:
   - Use these as templates
   - Combine multiple strategies
   - Integrate with external systems

3. **Deploy and Monitor**:
   - See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
   - Set up metrics collection
   - Monitor performance in production

---

## References

- [xApp Development Guide](XAPP_DEVELOPMENT_GUIDE.md)
- [SDK API Reference](SDK_API_REFERENCE.md)
- O-RAN E2 Interface Specifications
