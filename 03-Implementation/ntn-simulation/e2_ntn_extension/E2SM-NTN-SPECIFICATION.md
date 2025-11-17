# E2SM-NTN Service Model Specification
## E2 Service Model for Non-Terrestrial Networks

**Version:** 1.0.0
**Date:** 2025-11-17
**Status:** Draft Specification
**Based on:** O-RAN.WG3.E2SM-v03.00, 3GPP TR 38.811

---

## 1. Executive Summary

The E2SM-NTN (E2 Service Model for Non-Terrestrial Networks) extends the O-RAN E2 interface to support LEO/MEO/GEO satellite-based 5G networks. This service model enables near-RT RIC to collect NTN-specific metrics and execute control actions optimized for satellite communications.

### Key Objectives:
- Report NTN-specific KPMs (Doppler shift, propagation delay, satellite position)
- Enable predictive handover decisions based on satellite orbital mechanics
- Support adaptive power control for varying link budgets
- Provide link margin monitoring and rain fade mitigation

---

## 2. Service Model Overview

### 2.1 RAN Function Definition

```yaml
RAN Function ID: 10
RAN Function Short Name: "ORAN-E2SM-NTN"
RAN Function E2SM OID: "1.3.6.1.4.1.53148.1.1.2.10"
RAN Function Description: "E2 Service Model for Non-Terrestrial Networks"
Revision: 1
```

### 2.2 Supported Orbit Types
- **LEO (Low Earth Orbit):** 600-1200 km altitude
- **MEO (Medium Earth Orbit):** 7000-25000 km altitude
- **GEO (Geostationary Orbit):** 35786 km altitude

---

## 3. NTN-Specific KPMs (Key Performance Metrics)

### 3.1 Satellite Identification Metrics

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `satellite_id` | String | - | Unique satellite identifier |
| `orbit_type` | Enum | LEO/MEO/GEO | Orbital classification |
| `beam_id` | Integer | - | Active beam identifier |
| `satellite_epoch` | Integer | seconds | Time since satellite epoch |

### 3.2 Orbital Dynamics Metrics

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `elevation_angle` | Float | degrees | Current elevation angle (0-90°) |
| `azimuth_angle` | Float | degrees | Current azimuth angle (0-360°) |
| `slant_range_km` | Float | km | Distance UE to satellite |
| `satellite_velocity` | Float | km/s | Satellite velocity vector magnitude |
| `angular_velocity` | Float | deg/s | Angular velocity as seen from UE |

### 3.3 Channel Quality Metrics

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `rsrp` | Float | dBm | Reference Signal Received Power |
| `rsrq` | Float | dB | Reference Signal Received Quality |
| `sinr` | Float | dB | Signal-to-Interference-plus-Noise Ratio |
| `bler` | Float | % | Block Error Rate |
| `cqi` | Integer | 0-15 | Channel Quality Indicator |

### 3.4 NTN-Specific Impairment Metrics

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `doppler_shift_hz` | Float | Hz | Frequency offset due to Doppler |
| `doppler_rate_hz_s` | Float | Hz/s | Rate of Doppler change |
| `propagation_delay_ms` | Float | ms | One-way propagation delay |
| `path_loss_db` | Float | dB | Total path loss (free space + atmospheric) |
| `rain_attenuation_db` | Float | dB | Additional loss due to rain fade |
| `atmospheric_loss_db` | Float | dB | Tropospheric/ionospheric loss |

### 3.5 Link Budget Metrics

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `tx_power_dbm` | Float | dBm | Transmit power (UE or satellite) |
| `rx_power_dbm` | Float | dBm | Received power |
| `link_margin_db` | Float | dB | Link margin above threshold |
| `snr_db` | Float | dB | Signal-to-Noise Ratio |
| `required_snr_db` | Float | dB | Required SNR for target BLER |

### 3.6 Handover Prediction Metrics

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `time_to_handover_sec` | Float | seconds | Predicted time until handover needed |
| `handover_trigger_threshold` | Float | degrees | Elevation threshold for handover |
| `next_satellite_id` | String | - | Next candidate satellite ID |
| `next_satellite_elevation` | Float | degrees | Next satellite elevation |
| `handover_probability` | Float | 0-1 | Probability of successful handover |

### 3.7 Performance Metrics

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `throughput_dl_mbps` | Float | Mbps | Downlink throughput |
| `throughput_ul_mbps` | Float | Mbps | Uplink throughput |
| `latency_rtt_ms` | Float | ms | Round-trip time |
| `packet_loss_rate` | Float | % | Packet loss percentage |

---

## 4. E2 Message Formats

### 4.1 RIC Event Trigger Styles

#### Event Trigger Style 1: Periodic NTN Report
```yaml
Event Trigger Style Type: 1
Event Trigger Style Name: "Periodic NTN Metrics"
Event Trigger Format Type: 1
Parameters:
  - report_period_ms: 1000  # 100ms - 10000ms
```

#### Event Trigger Style 2: Elevation Threshold
```yaml
Event Trigger Style Type: 2
Event Trigger Style Name: "Elevation Threshold Trigger"
Event Trigger Format Type: 2
Parameters:
  - min_elevation_deg: 10.0
  - threshold_type: "BELOW" | "ABOVE"
```

#### Event Trigger Style 3: Handover Imminent
```yaml
Event Trigger Style Type: 3
Event Trigger Style Name: "Handover Prediction Trigger"
Event Trigger Format Type: 3
Parameters:
  - time_to_handover_threshold_sec: 30.0
  - elevation_change_rate_threshold: -0.5  # deg/s
```

#### Event Trigger Style 4: Link Quality Degradation
```yaml
Event Trigger Style Type: 4
Event Trigger Style Name: "Link Quality Alert"
Event Trigger Format Type: 4
Parameters:
  - min_sinr_db: 5.0
  - max_bler_percent: 10.0
  - min_link_margin_db: 3.0
```

### 4.2 RIC Report Styles

#### Report Style 1: Full NTN Metrics Report
```json
{
  "reportStyleType": 1,
  "reportStyleName": "Full NTN Metrics",
  "indicationHeaderFormatType": 1,
  "indicationMessageFormatType": 1,
  "measInfoList": [
    "satellite_id", "orbit_type", "elevation_angle", "azimuth_angle",
    "slant_range_km", "doppler_shift_hz", "propagation_delay_ms",
    "rsrp", "rsrq", "sinr", "bler", "path_loss_db", "link_margin_db",
    "time_to_handover_sec"
  ]
}
```

#### Report Style 2: Minimal NTN Report (Critical Metrics Only)
```json
{
  "reportStyleType": 2,
  "reportStyleName": "Minimal NTN Report",
  "indicationHeaderFormatType": 1,
  "indicationMessageFormatType": 2,
  "measInfoList": [
    "satellite_id", "elevation_angle", "rsrp", "sinr",
    "doppler_shift_hz", "time_to_handover_sec"
  ]
}
```

#### Report Style 3: Handover Preparation Report
```json
{
  "reportStyleType": 3,
  "reportStyleName": "Handover Preparation",
  "indicationHeaderFormatType": 1,
  "indicationMessageFormatType": 3,
  "measInfoList": [
    "satellite_id", "elevation_angle", "time_to_handover_sec",
    "next_satellite_id", "next_satellite_elevation",
    "handover_probability", "link_margin_db"
  ]
}
```

### 4.3 RIC Indication Message Format

#### Indication Header (Format 1)
```c
// ASN.1-like structure (simplified for documentation)
E2SM-NTN-IndicationHeader ::= SEQUENCE {
    timestamp                   INTEGER,        // Unix time in nanoseconds
    satellite-id                UTF8String,
    orbit-type                  ENUMERATED {leo, meo, geo},
    granularity-period-ms       INTEGER,
    measurement-type            ENUMERATED {periodic, event-triggered}
}
```

#### Indication Message (Format 1 - Full Metrics)
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
    "angular_velocity": 0.42
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

### 4.4 RIC Control Message Formats

#### Control Action 1: Power Control Adjustment
```json
{
  "actionType": "POWER_CONTROL",
  "ue_id": "UE-001",
  "parameters": {
    "target_tx_power_dbm": 20.0,
    "power_adjustment_db": -3.0,
    "reason": "LINK_MARGIN_EXCESSIVE"
  }
}
```

#### Control Action 2: Trigger Handover
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

#### Control Action 3: Doppler Pre-Compensation
```json
{
  "actionType": "DOPPLER_COMPENSATION",
  "ue_id": "UE-001",
  "parameters": {
    "frequency_offset_hz": 12500.0,
    "update_rate_ms": 100,
    "compensation_method": "PRE_COMPENSATE"
  }
}
```

#### Control Action 4: Link Adaptation
```json
{
  "actionType": "LINK_ADAPTATION",
  "ue_id": "UE-001",
  "parameters": {
    "target_mcs": 16,
    "target_bler": 0.01,
    "adaptation_reason": "RAIN_FADE_DETECTED"
  }
}
```

#### Control Action 5: Beam Switching
```json
{
  "actionType": "BEAM_SWITCH",
  "ue_id": "UE-001",
  "parameters": {
    "target_beam_id": 8,
    "switch_reason": "BETTER_COVERAGE"
  }
}
```

---

## 5. Service Model Functions

### 5.1 Event Trigger Definitions

```python
class NTNEventTrigger:
    PERIODIC = 1                    # Periodic reporting (100ms - 10s)
    ELEVATION_THRESHOLD = 2         # Elevation crosses threshold
    HANDOVER_IMMINENT = 3           # Predicted handover in < threshold
    LINK_QUALITY_ALERT = 4          # SINR/BLER/margin degraded
    DOPPLER_THRESHOLD = 5           # Doppler shift exceeds limit
    RAIN_FADE_DETECTED = 6          # Rain attenuation detected
```

### 5.2 Action Definitions

```python
class NTNControlAction:
    POWER_CONTROL = 1               # Adjust transmit power
    TRIGGER_HANDOVER = 2            # Initiate satellite handover
    DOPPLER_COMPENSATION = 3        # Configure Doppler pre-compensation
    LINK_ADAPTATION = 4             # Change MCS/coding
    BEAM_SWITCH = 5                 # Switch to different beam
    ACTIVATE_FADE_MITIGATION = 6    # Enable rain fade mitigation
```

### 5.3 Report Format Definitions

All E2SM-NTN messages use JSON encoding for simplicity and compatibility with xApps. Production implementations should use ASN.1 PER (Packed Encoding Rules) for efficiency.

---

## 6. Integration with E2 Interface

### 6.1 RAN Function Setup

During E2 Setup, the gNB announces E2SM-NTN capability:

```json
{
  "ranFunctionId": 10,
  "ranFunctionDefinition": {
    "ranFunctionName": {
      "ranFunctionShortName": "ORAN-E2SM-NTN",
      "ranFunctionE2SMOid": "1.3.6.1.4.1.53148.1.1.2.10"
    },
    "ricEventTriggerStyle": [
      {"ricEventTriggerStyleType": 1, "ricEventTriggerStyleName": "Periodic NTN Metrics"},
      {"ricEventTriggerStyleType": 2, "ricEventTriggerStyleName": "Elevation Threshold"},
      {"ricEventTriggerStyleType": 3, "ricEventTriggerStyleName": "Handover Imminent"},
      {"ricEventTriggerStyleType": 4, "ricEventTriggerStyleName": "Link Quality Alert"}
    ],
    "ricReportStyle": [
      {"ricReportStyleType": 1, "ricReportStyleName": "Full NTN Metrics"},
      {"ricReportStyleType": 2, "ricReportStyleName": "Minimal NTN Report"},
      {"ricReportStyleType": 3, "ricReportStyleName": "Handover Preparation"}
    ]
  }
}
```

### 6.2 Subscription Flow

1. xApp subscribes to NTN metrics via RIC Subscription Request
2. gNB acknowledges subscription
3. gNB sends periodic RIC Indications with NTN metrics
4. xApp processes metrics and may send RIC Control messages

### 6.3 Control Flow

1. xApp analyzes NTN metrics (e.g., detects low elevation)
2. xApp sends RIC Control Request (e.g., trigger handover)
3. gNB executes control action
4. gNB sends RIC Control Acknowledge

---

## 7. Calculation Methods

### 7.1 Doppler Shift Calculation

```
doppler_shift_hz = (satellite_velocity / c) * carrier_frequency * cos(elevation)
```

Where:
- `c` = speed of light (3e8 m/s)
- `carrier_frequency` = 2.1 GHz (example)
- `elevation` = elevation angle in radians

### 7.2 Propagation Delay Calculation

```
propagation_delay_ms = slant_range_km / (c / 1000)
```

### 7.3 Time to Handover Prediction

```
time_to_handover_sec = (current_elevation - min_elevation) / abs(elevation_rate)
```

Where:
- `min_elevation` = handover trigger threshold (e.g., 10°)
- `elevation_rate` = rate of elevation change (deg/s, negative when descending)

### 7.4 Link Margin Calculation

```
link_margin_db = rx_power_dbm - sensitivity_dbm
```

Where:
- `sensitivity_dbm` = receiver sensitivity (e.g., -110 dBm)

---

## 8. Compliance and Standards

### 8.1 O-RAN Alliance Standards
- **O-RAN.WG3.E2AP-v03.00:** E2 Application Protocol
- **O-RAN.WG3.E2SM-v03.00:** E2 Service Model framework
- **O-RAN.WG3.E2SM-KPM-v03.00:** KPM service model (reference)

### 8.2 3GPP Standards
- **3GPP TS 38.300:** NR overall description
- **3GPP TS 38.821:** Solutions for NR to support non-terrestrial networks
- **3GPP TR 38.811:** Study on NTN

### 8.3 ITU-R Standards
- **ITU-R P.618:** Propagation data for satellite systems
- **ITU-R M.1829:** Doppler and delay characteristics

---

## 9. Implementation Notes

### 9.1 Threading and Performance
- NTN metrics should be collected at 100ms - 1s intervals
- Orbital calculations are computationally light (< 1ms per UE)
- Doppler prediction requires satellite ephemeris data

### 9.2 Data Persistence
- Store last 1 hour of NTN metrics in time-series database
- Maintain satellite TLE (Two-Line Element) database
- Cache handover predictions for fast lookup

### 9.3 Error Handling
- Handle satellite outages gracefully (no satellite in view)
- Validate elevation angles (0-90°)
- Detect and report anomalous Doppler values

### 9.4 Testing Requirements
- Unit tests for all KPM calculations
- Integration tests with OpenNTN channel models
- End-to-end tests with E2 interface
- Scenario tests (low elevation, handover, rain fade)

---

## 10. Future Extensions

### 10.1 Multi-Satellite Diversity
- Report metrics for multiple visible satellites
- Support satellite diversity selection

### 10.2 Inter-Satellite Links (ISL)
- ISL-specific metrics (ISL delay, ISL capacity)
- Multi-hop routing metrics

### 10.3 Satellite Constellation Optimization
- Constellation-wide load balancing
- Predictive resource allocation

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-17 | E2SM-NTN Architect | Initial specification |

---

**End of Specification**
