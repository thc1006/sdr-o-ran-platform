# NTN-O-RAN Platform API Specification
## Version 1.0 - Post-TDD Harmonization

**Date**: 2025-11-17
**Author**: Software Integration Specialist
**Purpose**: Define unified APIs across all Week 2 components

---

## Executive Summary

This document defines the **correct** API specification for all NTN-O-RAN components after Test-Driven Development (TDD) analysis. Integration tests identified 3 critical API mismatches that prevented E2E integration.

### API Mismatches Identified

1. **Weather API** (CRITICAL): Returns `RainAttenuationResult` object instead of `float`
2. **Baseline API** (CRITICAL): Uses `handover_threshold_db` instead of `rsrp_threshold_dbm`
3. **ASN.1 Module** (CRITICAL): Missing `asn1/__init__.py` causes import failure

---

## 1. OpenNTN Channel Models

### 1.1 LEOChannelModel

```python
from openNTN_integration import LEOChannelModel

# Initialization
leo = LEOChannelModel(
    carrier_frequency: float = 2.0e9,    # Hz (S-band: 1.9-4.0 GHz, Ka-band: 19-40 GHz)
    altitude_km: float = 550.0,          # km (LEO: 550-1200 km)
    scenario: str = 'urban',             # 'urban', 'suburban', 'dense_urban'
    direction: str = 'downlink',         # 'uplink' or 'downlink'
    enable_pathloss: bool = True,
    enable_shadow_fading: bool = True,
    enable_doppler: bool = True,
    precision: str = 'single'            # 'single' or 'double'
)

# Link Budget Calculation
budget = leo.calculate_link_budget(
    elevation_angle: float,              # degrees (10-90)
    rain_rate: float = 0.0              # mm/h (OPTIONAL - defaults to 0.0)
) -> Dict[str, float]

# Returns:
{
    'elevation_angle_deg': float,
    'slant_range_km': float,
    'free_space_path_loss_db': float,    # NOTE: Key is 'free_space_path_loss_db'
    'doppler_shift_hz': float,
    'doppler_shift_khz': float,
    'wavelength_m': float,
    'orbital_velocity_kmps': float,
    'orbital_period_min': float
}
```

**API Status**: ✅ CORRECT (rain_rate parameter is already optional)

### 1.2 MEOChannelModel

Inherits from `LEOChannelModel` - same API.

```python
from openNTN_integration import MEOChannelModel

meo = MEOChannelModel(
    carrier_frequency=2.0e9,
    altitude_km=8000,              # MEO: 7000-25000 km
    scenario='suburban'
)

budget = meo.calculate_link_budget(elevation_angle=45.0, rain_rate=0.0)
# Path loss range: 175-185 dB for MEO at 8000 km
```

**API Status**: ✅ CORRECT

### 1.3 GEOChannelModel

Inherits from `LEOChannelModel` - same API.

```python
from openNTN_integration import GEOChannelModel

geo = GEOChannelModel(
    carrier_frequency=2.0e9,
    altitude_km=35786,             # GEO: exactly 35786 km
    scenario='rural'
)

budget = geo.calculate_link_budget(elevation_angle=60.0, rain_rate=0.0)
# Path loss range: 190-200 dB for GEO
```

**API Status**: ✅ CORRECT

---

## 2. E2SM-NTN Service Model

### 2.1 E2SM_NTN Class

```python
from e2_ntn_extension.e2sm_ntn import E2SM_NTN

# Initialization
e2sm = E2SM_NTN(
    channel_model = None,                # Optional OpenNTN channel model
    encoding: str = 'asn1'              # 'asn1' or 'json' (auto-falls back to json)
)

# Constants
E2SM_NTN.RAN_FUNCTION_ID = 10
E2SM_NTN.RAN_FUNCTION_SHORT_NAME = "ORAN-E2SM-NTN"
```

### 2.2 create_indication_message Method

**Current Signature** (CORRECT):
```python
header, message = e2sm.create_indication_message(
    ue_id: str,
    satellite_state: Dict[str, Any],
    ue_measurements: Dict[str, float],
    report_style: int = 1
) -> Tuple[bytes, bytes]
```

**Validation Script Uses** (MISMATCH):
```python
indication = e2sm.create_indication_message(ntn_meas, sat_state)
# Only 2 positional args - missing ue_id!
```

**Required Fix**: Add compatibility wrapper or reorder parameters.

**RECOMMENDED API**:
```python
# Option 1: Reorder parameters (ue_measurements includes ue_id)
header, message = e2sm.create_indication_message(
    ue_measurements: Dict,               # Must include 'ue_id' key
    satellite_state: Dict,
    report_style: int = 1
) -> Tuple[bytes, bytes]

# ue_measurements format:
{
    'ue_id': str,
    'satellite_id': str,
    'rsrp_dbm': float,
    'elevation_angle_deg': float,
    'doppler_shift_hz': float,
    'timestamp': str  # ISO format
}

# satellite_state format:
{
    'satellite_id': str,
    'orbit_type': str,  # 'LEO', 'MEO', 'GEO'
    'altitude_km': float,
    'velocity_kmps': float
}
```

**API Status**: ⚠️ **NEEDS FIX** - Reorder parameters to match validation script

---

## 3. Orbit Propagation (SGP4)

### 3.1 SGP4Propagator Class

**Current Signature**:
```python
class SGP4Propagator:
    def __init__(self, tle_data: TLEData):  # Requires TLEData object
        ...
```

**Validation Script Expects**:
```python
sgp4 = SGP4Propagator()                    # Parameterless init
sgp4.load_tle(tle1, tle2)                  # Load TLE strings
```

**RECOMMENDED API**:
```python
from orbit_propagation.sgp4_propagator import SGP4Propagator

# Option 1: Parameterless initialization (REQUIRED for validation)
sgp4 = SGP4Propagator()

# Load TLE from strings
sgp4.load_tle(
    tle1: str,                             # Line 1 of TLE
    tle2: str                              # Line 2 of TLE
) -> None

# Option 2: Initialize with TLE data (keep for backward compatibility)
from orbit_propagation.tle_manager import TLEData

tle_data = TLEData(...)
sgp4 = SGP4Propagator(tle_data)            # Also supported

# Get Ground Track
geometry = sgp4.get_ground_track(
    user_lat: float,                       # degrees
    user_lon: float,                       # degrees
    user_alt: float,                       # meters
    timestamp: datetime
) -> Dict[str, float]

# Returns:
{
    'elevation_deg': float,
    'azimuth_deg': float,
    'slant_range_km': float,
    'doppler_shift_hz': float,
    'satellite_altitude_km': float,
    'satellite_velocity_kmps': float,
    'is_visible': bool,
    'satellite_lat': float,
    'satellite_lon': float,
    'timestamp': str,
    'satellite_id': str
}
```

**API Status**: ⚠️ **NEEDS FIX** - Add parameterless `__init__` and `load_tle` method

---

## 4. Weather Integration (ITU-R P.618)

### 4.1 ITUR_P618_RainAttenuation Class

**Current Signature** (INCORRECT):
```python
result = weather.calculate_rain_attenuation(...) -> RainAttenuationResult
# Returns object with exceeded_0_01_percent, exceeded_0_1_percent, etc.
```

**Validation Script Expects** (CORRECT):
```python
atten = weather.calculate_rain_attenuation(...) -> float
assert 0 <= atten <= 50  # Direct numeric comparison
```

**RECOMMENDED API** (CRITICAL FIX):
```python
from weather.itur_p618 import ITUR_P618_RainAttenuation

weather = ITUR_P618_RainAttenuation()

# MUST return float, NOT RainAttenuationResult object
atten_db = weather.calculate_rain_attenuation(
    latitude: float,                       # degrees (-90 to 90)
    longitude: float,                      # degrees (-180 to 180)
    frequency_ghz: float,                  # GHz (1-1000)
    elevation_angle: float,                # degrees (0-90)
    polarization: str = 'circular',
    station_altitude_km: float = 0.0
) -> float                                 # ← MUST be float, not RainAttenuationResult!

# Returns: Rain attenuation in dB (0.01% time exceeded)
# Range: 0-50 dB for typical scenarios
```

**API Status**: ❌ **CRITICAL FIX REQUIRED** - Change return type from `RainAttenuationResult` to `float`

**Implementation Strategy**:
```python
def calculate_rain_attenuation(...) -> float:
    # Calculate full result object internally
    full_result = self._calculate_full_rain_attenuation(...)

    # Return only the 0.01% exceeded value as float
    return full_result.exceeded_0_01_percent  # Return float, not object
```

---

## 5. ASN.1 Encoding

### 5.1 Module Structure

**Current Structure** (INCORRECT):
```
e2_ntn_extension/
  asn1/
    E2SM-NTN-v1.asn1              # ASN.1 schema
    # MISSING: __init__.py ❌
  asn1_codec.py                   # In parent directory
```

**Validation Script Expects**:
```python
from e2_ntn_extension.asn1.asn1_codec import E2SM_NTN_ASN1_Codec
# Fails: ModuleNotFoundError - not a package
```

**RECOMMENDED Structure** (CRITICAL FIX):
```
e2_ntn_extension/
  asn1/
    __init__.py                   # ← MUST create this
    asn1_codec.py                 # ← Move codec here OR
    E2SM-NTN-v1.asn1              # ASN.1 schema
```

**Fix Option 1** - Create `asn1/__init__.py`:
```python
# e2_ntn_extension/asn1/__init__.py

# Import from parent directory
from ..asn1_codec import E2SM_NTN_ASN1_Codec, ASN1CodecError

__all__ = ['E2SM_NTN_ASN1_Codec', 'ASN1CodecError']
```

**Fix Option 2** - Move `asn1_codec.py` into `asn1/`:
```bash
mv e2_ntn_extension/asn1_codec.py e2_ntn_extension/asn1/
# Then create __init__.py to export it
```

**API Status**: ❌ **CRITICAL FIX REQUIRED** - Create `asn1/__init__.py`

---

## 6. Optimized Components

### 6.1 OptimizedSGP4Propagator

**Must inherit base SGP4Propagator API**:
```python
from optimization.optimized_components import OptimizedSGP4Propagator

# MUST support both initialization modes
opt_sgp4 = OptimizedSGP4Propagator()      # Parameterless
opt_sgp4.load_tle(tle1, tle2)

# OR
opt_sgp4 = OptimizedSGP4Propagator(tle_data)

# Same interface as SGP4Propagator
geometry = opt_sgp4.get_ground_track(lat, lon, alt, timestamp)
```

**API Status**: ⚠️ **NEEDS FIX** - Ensure same API as base SGP4Propagator

### 6.2 OptimizedWeatherCalculator

```python
from optimization.optimized_components import OptimizedWeatherCalculator

opt_weather = OptimizedWeatherCalculator()

# Simplified positional parameters
atten = opt_weather.calculate_rain_attenuation(
    latitude: float,
    longitude: float,
    frequency_ghz: float,
    elevation_angle: float
) -> float  # Must return float
```

**API Status**: ✅ CORRECT (assuming same fix as base weather class)

---

## 7. Baseline Systems

### 7.1 ReactiveHandoverManager

**Current Signature** (INCORRECT):
```python
class ReactiveHandoverManager:
    def __init__(self,
        handover_threshold_db: float = -100.0,  # ← Wrong parameter name
        hysteresis_db: float = 3.0
    ):
```

**Validation Script Expects** (CORRECT):
```python
reactive = ReactiveHandoverManager(rsrp_threshold_dbm=-110.0)
```

**RECOMMENDED API** (CRITICAL FIX):
```python
from baseline.reactive_system import ReactiveHandoverManager

reactive = ReactiveHandoverManager(
    rsrp_threshold_dbm: float = -110.0,   # ← Correct parameter name
    hysteresis_db: float = 3.0
)
```

**API Status**: ❌ **CRITICAL FIX REQUIRED** - Rename `handover_threshold_db` to `rsrp_threshold_dbm`

### 7.2 PredictiveHandoverManager

```python
from baseline.predictive_system import PredictiveHandoverManager

predictive = PredictiveHandoverManager(
    prediction_horizon_sec: float = 60.0
)
```

**API Status**: ✅ CORRECT

---

## 8. Summary of Required API Fixes

### Critical Fixes (Blocking week2_validation.py)

| Component | Issue | Fix Required | Priority |
|-----------|-------|--------------|----------|
| **ITUR_P618_RainAttenuation** | Returns `RainAttenuationResult` object | Return `float` from `calculate_rain_attenuation()` | 🔴 CRITICAL |
| **ReactiveHandoverManager** | Parameter `handover_threshold_db` | Rename to `rsrp_threshold_dbm` | 🔴 CRITICAL |
| **ASN.1 Module** | Missing `asn1/__init__.py` | Create `e2_ntn_extension/asn1/__init__.py` | 🔴 CRITICAL |
| **E2SM_NTN** | Parameter order mismatch | Reorder to `(ue_measurements, satellite_state)` | 🟡 HIGH |
| **SGP4Propagator** | Requires TLEData parameter | Add parameterless `__init__` + `load_tle()` | 🟡 HIGH |
| **OptimizedSGP4Propagator** | Same as SGP4Propagator | Inherit fixed API | 🟡 HIGH |

### Non-Critical (Already Correct)

| Component | Status |
|-----------|--------|
| LEOChannelModel | ✅ `rain_rate` parameter already optional |
| MEOChannelModel | ✅ Inherits correct API |
| GEOChannelModel | ✅ Inherits correct API |
| PredictiveHandoverManager | ✅ Correct parameter names |
| OptimizedWeatherCalculator | ✅ Correct (after base fix) |

---

## 9. Validation Criteria

After implementing fixes, all APIs must pass:

1. **Integration Tests**: `integration/run_integration_tests.py` → 100% pass
2. **Validation Script**: `testing/week2_validation.py` → 7/7 tests pass
3. **E2E Integration**: Complete flow works end-to-end
4. **Performance**: No regression in optimized components

---

## 10. API Compatibility Notes

### Backward Compatibility

Where possible, maintain backward compatibility by:
- Supporting both old and new parameter names
- Supporting multiple initialization modes
- Providing deprecation warnings for old APIs

### Breaking Changes

Document all breaking changes in `API_CHANGELOG.md`.

---

**Next Steps**:
1. Implement fixes in priority order (Critical first)
2. Run integration tests after each fix
3. Verify week2_validation.py passes 7/7
4. Document all changes in changelog
5. Create E2E integration test

---

*Document Version*: 1.0
*Last Updated*: 2025-11-17
*Status*: Ready for Implementation
