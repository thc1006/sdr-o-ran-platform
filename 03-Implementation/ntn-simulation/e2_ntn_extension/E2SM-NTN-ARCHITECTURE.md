# E2SM-NTN Architecture Documentation
## System Architecture and Data Flow

**Version:** 1.0.0
**Date:** 2025-11-17
**Project:** SDR-O-RAN Platform with NTN Extension

---

## 1. System Overview

The E2SM-NTN (E2 Service Model for Non-Terrestrial Networks) extends the O-RAN architecture to support satellite-based 5G networks. The system integrates OpenNTN channel models with the existing E2 interface to enable intelligent RAN control for NTN scenarios.

### Key Components:
1. **OpenNTN Channel Models** - 3GPP TR38.811 compliant LEO/MEO/GEO channel simulation
2. **E2SM-NTN Service Model** - NTN-specific KPM definitions and E2 message formats
3. **NTN-E2 Bridge** - Integration layer between OpenNTN and E2 Interface
4. **E2 Interface** - O-RAN E2AP protocol implementation
5. **Near-RT RIC** - RAN Intelligent Controller
6. **xApps** - Intelligent applications (handover optimization, power control)

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SATELLITE CONSTELLATION                         │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐                      │
│  │   LEO    │        │   MEO    │        │   GEO    │                      │
│  │ 600 km   │        │ 10000 km │        │ 35786 km │                      │
│  │ 7.5 km/s │        │  4 km/s  │        │ 0 km/s   │                      │
│  └────┬─────┘        └────┬─────┘        └────┬─────┘                      │
│       │                   │                   │                             │
│       └───────────────────┴───────────────────┘                             │
│                           │                                                 │
│                    Satellite Link                                           │
│                    - Doppler: ±15 kHz (LEO)                                │
│                    - Delay: 2-280 ms                                        │
│                    - Path Loss: 160-200 dB                                  │
└───────────────────────────┼─────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GROUND SEGMENT                                      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                          gNB / E2 Node                              │    │
│  │                                                                      │    │
│  │  ┌──────────────────┐         ┌──────────────────────────────┐    │    │
│  │  │  OpenNTN Models  │         │     NTN-E2 Bridge            │    │    │
│  │  │                  │         │                               │    │    │
│  │  │  • LEO Channel   │────────▶│  • Satellite Geometry        │    │    │
│  │  │  • MEO Channel   │         │  • Doppler Calculation       │    │    │
│  │  │  • GEO Channel   │         │  • Link Budget Analysis      │    │    │
│  │  │  • TR38.811      │         │  • Handover Prediction       │    │    │
│  │  └──────────────────┘         └──────────┬───────────────────┘    │    │
│  │                                           │                         │    │
│  │                                           ▼                         │    │
│  │                              ┌────────────────────────┐            │    │
│  │                              │   E2SM-NTN Service     │            │    │
│  │                              │       Model            │            │    │
│  │                              │                        │            │    │
│  │                              │  • NTN KPMs           │            │    │
│  │                              │  • RIC Indication     │            │    │
│  │                              │  • RIC Control        │            │    │
│  │                              │  • Event Triggers     │            │    │
│  │                              └──────────┬─────────────┘            │    │
│  └─────────────────────────────────────────┼──────────────────────────┘    │
│                                             │                               │
│                                      E2 Interface                           │
│                                      (E2AP Protocol)                        │
│                                             │                               │
└─────────────────────────────────────────────┼───────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEAR-RT RIC                                        │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      E2 Interface Manager                           │    │
│  │                                                                      │    │
│  │  • E2 Setup          • RIC Subscriptions     • Health Monitoring   │    │
│  └──────────────┬───────────────────────────────────────┬──────────────┘    │
│                 │                                       │                   │
│                 ▼                                       ▼                   │
│  ┌──────────────────────────┐           ┌──────────────────────────┐      │
│  │   NTN Handover xApp      │           │   NTN Power Control xApp │      │
│  │                          │           │                          │      │
│  │  • Predict handovers     │           │  • Monitor link margin   │      │
│  │  • Select next satellite │           │  • Optimize Tx power     │      │
│  │  • Trigger HO commands   │           │  • Rain fade mitigation  │      │
│  └──────────────────────────┘           └──────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. E2SM-NTN Data Flow

### 3.1 Subscription Flow (Initialization)

```
xApp                    Near-RT RIC              E2 Node (gNB)         NTN-E2 Bridge
  │                          │                         │                      │
  │  1. Subscribe to         │                         │                      │
  │     NTN metrics          │                         │                      │
  ├─────────────────────────▶│                         │                      │
  │                          │  2. RIC Subscription    │                      │
  │                          │     Request (E2AP)      │                      │
  │                          ├────────────────────────▶│                      │
  │                          │                         │  3. Configure        │
  │                          │                         │     reporting        │
  │                          │                         ├─────────────────────▶│
  │                          │                         │                      │
  │                          │  4. RIC Subscription    │                      │
  │                          │     Response            │                      │
  │                          │◀────────────────────────┤                      │
  │  5. Subscription OK      │                         │                      │
  │◀─────────────────────────┤                         │                      │
  │                          │                         │                      │
```

### 3.2 Periodic Reporting Flow

```
Satellite          UE          NTN-E2 Bridge       E2SM-NTN          RIC          xApp
    │               │                │                  │              │            │
    │  RF Signal    │                │                  │              │            │
    ├──────────────▶│                │                  │              │            │
    │               │  UE Report     │                  │              │            │
    │               │  (RSRP, SINR)  │                  │              │            │
    │               ├───────────────▶│                  │              │            │
    │               │                │  Calculate       │              │            │
    │               │                │  Geometry,       │              │            │
    │               │                │  Doppler,        │              │            │
    │               │                │  Link Budget     │              │            │
    │               │                │  ────────────    │              │            │
    │               │                │             │    │              │            │
    │               │                │◀────────────┘    │              │            │
    │               │                │  Create NTN      │              │            │
    │               │                │  metrics         │              │            │
    │               │                ├─────────────────▶│              │            │
    │               │                │                  │  Encode      │            │
    │               │                │                  │  E2 Msg      │            │
    │               │                │                  │  ──────────  │            │
    │               │                │                  │          │   │            │
    │               │                │                  │◀─────────┘   │            │
    │               │                │  RIC Indication  │              │            │
    │               │                │  (Header + Msg)  │              │            │
    │               │                │──────────────────┼─────────────▶│            │
    │               │                │                  │              │  Process   │
    │               │                │                  │              │  NTN KPMs  │
    │               │                │                  │              ├───────────▶│
    │               │                │                  │              │            │
```

### 3.3 Control Action Flow (Handover Example)

```
xApp          RIC          E2SM-NTN       NTN-E2 Bridge        gNB        Satellite
  │             │              │                 │              │              │
  │  Detect     │              │                 │              │              │
  │  low elev   │              │                 │              │              │
  │  ─────────  │              │                 │              │              │
  │         │   │              │                 │              │              │
  │◀────────┘   │              │                 │              │              │
  │  Decision:  │              │                 │              │              │
  │  Trigger HO │              │                 │              │              │
  │             │              │                 │              │              │
  │  RIC Control│              │                 │              │              │
  │  Request    │              │                 │              │              │
  ├────────────▶│              │                 │              │              │
  │             │  Decode &    │                 │              │              │
  │             │  Validate    │                 │              │              │
  │             ├─────────────▶│                 │              │              │
  │             │              │  Parse control  │              │              │
  │             │              │  action         │              │              │
  │             │              ├────────────────▶│              │              │
  │             │              │                 │  Execute     │              │
  │             │              │                 │  Handover    │              │
  │             │              │                 ├─────────────▶│              │
  │             │              │                 │              │  Switch to   │
  │             │              │                 │              │  new sat     │
  │             │              │                 │              ├─────────────▶│
  │             │              │                 │              │              │
  │             │              │                 │  HO Complete │              │
  │             │              │                 │◀─────────────┤              │
  │             │              │  Control ACK    │              │              │
  │             │              │◀────────────────┤              │              │
  │             │  RIC Control │                 │              │              │
  │             │  ACK         │                 │              │              │
  │◀────────────┤              │                 │              │              │
  │             │              │                 │              │              │
```

---

## 4. Component Details

### 4.1 OpenNTN Channel Models

**Location:** `/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/openNTN_integration/`

**Components:**
- `leo_channel.py` - LEO satellite channel model (600-1200 km)
- `meo_channel.py` - MEO satellite channel model (7000-25000 km)
- `geo_channel.py` - GEO satellite channel model (35786 km)

**Features:**
- 3GPP TR38.811 compliant channel modeling
- TensorFlow + Sionna integration
- Doppler, delay, and path loss modeling

### 4.2 E2SM-NTN Service Model

**Location:** `/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/e2_ntn_extension/e2sm_ntn.py`

**Key Classes:**
- `E2SM_NTN` - Main service model class
- `NTNIndicationMessage` - NTN metrics payload
- `NTNControlMessage` - Control action payload

**Functions:**
- `create_indication_message()` - Generate RIC Indication
- `parse_control_message()` - Parse RIC Control
- `calculate_ntn_kpms()` - Calculate all NTN KPMs
- `predict_handover_time()` - Predict handover timing
- `recommend_power_control()` - Power control recommendations

### 4.3 NTN-E2 Bridge

**Location:** `/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/e2_ntn_extension/ntn_e2_bridge.py`

**Key Class:**
- `NTN_E2_Bridge` - Bridge between OpenNTN and E2 Interface

**Functions:**
- `register_ue()` - Register UE for tracking
- `process_ue_report()` - Process measurements and generate E2 Indication
- `execute_control_action()` - Execute E2 control actions
- `calculate_satellite_geometry()` - Compute elevation, azimuth, slant range
- `predict_next_handover()` - Predict handover events

### 4.4 E2 Interface (Existing)

**Location:** `/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ric-platform/e2-interface/`

**Components:**
- `e2_manager.py` - E2 connection and subscription manager
- `e2_messages.py` - E2AP message definitions
- `e2sm_kpm.py` - Existing KPM service model

**Integration Point:** E2SM-NTN extends the existing E2 interface by adding RAN Function ID 10.

### 4.5 xApp Framework (Existing)

**Location:** `/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ric-platform/xapp-sdk/`

**Base Class:**
- `XAppBase` - Base class for xApp development

**NTN xApps (Future):**
- Handover Optimization xApp
- Power Control xApp
- Link Adaptation xApp

---

## 5. Message Flow Examples

### 5.1 RIC Indication Message (Full NTN Metrics)

```json
{
  "timestamp_ns": 1700000000000000000,
  "ue_id": "UE-001",
  "satellite_metrics": {
    "satellite_id": "SAT-LEO-042",
    "orbit_type": "LEO",
    "beam_id": 7,
    "elevation_angle": 45.3,
    "azimuth_angle": 127.5,
    "slant_range_km": 847.2,
    "satellite_velocity": 7.5,
    "angular_velocity": -0.42
  },
  "channel_quality": {
    "rsrp": -85.3,
    "rsrq": -12.1,
    "sinr": 18.5,
    "bler": 0.01,
    "cqi": 12
  },
  "ntn_impairments": {
    "doppler_shift_hz": 12500.0,
    "doppler_rate_hz_s": -45.2,
    "propagation_delay_ms": 5.6,
    "path_loss_db": 175.4,
    "rain_attenuation_db": 2.3,
    "atmospheric_loss_db": 0.8
  },
  "link_budget": {
    "tx_power_dbm": 23.0,
    "rx_power_dbm": -85.3,
    "link_margin_db": 8.7,
    "snr_db": 18.5,
    "required_snr_db": 9.8
  },
  "handover_prediction": {
    "time_to_handover_sec": 127.3,
    "handover_trigger_threshold": 10.0,
    "next_satellite_id": "SAT-LEO-043",
    "next_satellite_elevation": 8.2,
    "handover_probability": 0.95
  },
  "performance": {
    "throughput_dl_mbps": 45.3,
    "throughput_ul_mbps": 12.7,
    "latency_rtt_ms": 11.2,
    "packet_loss_rate": 0.02
  }
}
```

### 5.2 RIC Control Message (Trigger Handover)

```json
{
  "actionType": "TRIGGER_HANDOVER",
  "ue_id": "UE-001",
  "parameters": {
    "target_satellite_id": "SAT-LEO-043",
    "handover_type": "PREDICTIVE",
    "preparation_time_ms": 5000
  }
}
```

---

## 6. NTN-Specific Algorithms

### 6.1 Satellite Geometry Calculation

```python
def calculate_satellite_geometry(ue_lat, ue_lon, sat_lat, sat_lon, altitude_km):
    # 1. Calculate central angle using Haversine formula
    central_angle = haversine(ue_lat, ue_lon, sat_lat, sat_lon)

    # 2. Calculate slant range using law of cosines
    slant_range = sqrt(
        R_earth^2 + (R_earth + altitude)^2 -
        2 * R_earth * (R_earth + altitude) * cos(central_angle)
    )

    # 3. Calculate elevation angle
    elevation = arcsin((R_earth + altitude) * sin(central_angle) / slant_range)

    # 4. Calculate azimuth angle
    azimuth = arctan2(
        sin(lon_diff) * cos(sat_lat),
        cos(ue_lat) * sin(sat_lat) - sin(ue_lat) * cos(sat_lat) * cos(lon_diff)
    )

    return elevation, azimuth, slant_range
```

### 6.2 Doppler Shift Calculation

```python
def calculate_doppler_shift(sat_velocity, elevation, carrier_freq):
    # Doppler shift = (v/c) * f * cos(elevation)
    doppler = (sat_velocity / SPEED_OF_LIGHT) * carrier_freq * cos(elevation)
    return doppler
```

### 6.3 Handover Time Prediction

```python
def predict_handover_time(current_elevation, angular_velocity, min_elevation):
    # Time = (current_elevation - min_elevation) / |angular_velocity|
    if angular_velocity >= 0:
        return INFINITY  # Satellite rising
    else:
        time_to_handover = (current_elevation - min_elevation) / abs(angular_velocity)
        return time_to_handover
```

---

## 7. Integration Points

### 7.1 With Existing E2 Interface

**Integration Method:**
1. E2SM-NTN registers as RAN Function ID 10 during E2 Setup
2. xApps subscribe to NTN metrics using standard RIC Subscription
3. E2 Manager routes NTN indications to subscribed xApps
4. xApps send control requests using standard RIC Control messages

**Code Integration:**
```python
# In e2_manager.py
from e2sm_ntn import E2SM_NTN

# Register NTN service model
ntn_service_model = E2SM_NTN()
self.service_models[10] = ntn_service_model
```

### 7.2 With xApp Framework

**Integration Method:**
1. xApps inherit from `XAppBase`
2. Override `handle_indication()` to process NTN metrics
3. Use E2SM-NTN to decode indication messages
4. Use E2SM-NTN to create control messages

**Example xApp:**
```python
class NTNHandoverXApp(XAppBase):
    def __init__(self):
        self.e2sm_ntn = E2SM_NTN()

    async def handle_indication(self, indication):
        # Decode NTN metrics
        ntn_data = json.loads(indication.ric_indication_message)

        # Check if handover needed
        if ntn_data["handover_prediction"]["time_to_handover_sec"] < 30:
            # Send handover control
            control_msg = self.e2sm_ntn.create_control_message(
                action_type=NTNControlAction.TRIGGER_HANDOVER,
                ue_id=ntn_data["ue_id"],
                parameters={"target_satellite_id": "SAT-LEO-043"}
            )
            await self.send_control_request(control_msg)
```

---

## 8. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                   Namespace: oran-ric                   │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │    │
│  │  │ E2 Interface │  │ NTN-E2 Bridge│  │   E2SM-NTN   │ │    │
│  │  │   Service    │  │   Service    │  │   ConfigMap  │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐                    │    │
│  │  │ Handover xApp│  │Power Ctrl xApp│                   │    │
│  │  └──────────────┘  └──────────────┘                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                Namespace: oran-gnb                      │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐                    │    │
│  │  │  gNB Service │  │ OpenNTN Model│                    │    │
│  │  └──────────────┘  └──────────────┘                    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Performance Considerations

### 9.1 Latency Budget

| Component | Latency | Notes |
|-----------|---------|-------|
| UE Measurement | 10-100 ms | Depends on reporting period |
| NTN-E2 Bridge Processing | < 1 ms | Geometry calculations |
| E2SM-NTN Encoding | < 1 ms | JSON serialization |
| E2 Transport | 1-5 ms | SCTP over IP |
| RIC Processing | 1-10 ms | xApp decision making |
| Control Action | 10-50 ms | Command execution |
| **Total** | **23-167 ms** | End-to-end control loop |

### 9.2 Scalability

| Metric | Value | Notes |
|--------|-------|-------|
| UEs per Satellite | 100-1000 | Depends on beam capacity |
| Reporting Period | 100 ms - 10 s | Configurable |
| Message Size | 500-2000 bytes | JSON format |
| Throughput | ~10k msg/s | Per RIC instance |

### 9.3 Resource Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| NTN-E2 Bridge | 0.5 core | 512 MB | 1 GB |
| E2SM-NTN Service | 0.2 core | 256 MB | 100 MB |
| Handover xApp | 0.3 core | 256 MB | 500 MB |

---

## 10. Testing and Validation

### Test Scenarios Implemented:
1. **Low Elevation** - Verify poor link quality detection
2. **Optimal Elevation** - Verify good link quality
3. **Handover Prediction** - Verify handover timing accuracy
4. **Power Control** - Verify power recommendations
5. **Multi-Satellite** - Verify LEO/MEO/GEO support

**Test Results:** See `test_results/e2sm_ntn_test_results.json`

---

## 11. Future Enhancements

### Phase 2 (Day 6-7):
- [ ] Implement NTN Handover Optimization xApp
- [ ] Implement NTN Power Control xApp
- [ ] Real-time satellite ephemeris integration

### Phase 3:
- [ ] Multi-satellite diversity support
- [ ] Inter-satellite link (ISL) metrics
- [ ] Satellite constellation optimization

### Phase 4:
- [ ] ASN.1 PER encoding (replace JSON)
- [ ] SCTP transport integration
- [ ] Production hardening

---

## 12. References

### O-RAN Alliance:
- O-RAN.WG3.E2AP-v03.00 - E2 Application Protocol
- O-RAN.WG3.E2SM-v03.00 - E2 Service Model Framework
- O-RAN.WG3.E2SM-KPM-v03.00 - KPM Service Model

### 3GPP:
- 3GPP TS 38.300 - NR Overall Description
- 3GPP TS 38.821 - NTN Solutions
- 3GPP TR 38.811 - NTN Study

### Implementation:
- OpenNTN Documentation
- TensorFlow 2.17.1
- Sionna 1.2.1

---

**End of Architecture Documentation**
