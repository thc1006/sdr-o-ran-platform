# OpenNTN Integration for SDR-O-RAN Platform

## Overview

This package provides high-level Python wrappers for **OpenNTN**'s 3GPP TR38.811 channel models, specifically designed for integration with the SDR-O-RAN platform. It simplifies Non-Terrestrial Network (NTN) channel modeling for LEO, MEO, and GEO satellite communications.

## Features

- **LEO Channel Model**: Low Earth Orbit (550-1200 km altitude)
- **MEO Channel Model**: Medium Earth Orbit (8,000-20,000 km altitude)
- **GEO Channel Model**: Geostationary Earth Orbit (35,786 km altitude)
- **3GPP TR38.811 Compliance**: Full support for urban, suburban, and dense_urban scenarios
- **Comprehensive Link Budget**: Path loss, Doppler shift, slant range calculations
- **S-band and Ka-band**: Support for 1.9-4.0 GHz and 19-40 GHz
- **GPU Acceleration**: TensorFlow-based with GPU support (when available)

## Installation

### Prerequisites

```bash
# Activate virtual environment
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate

# Required packages (already installed in Day 1 setup)
# - TensorFlow 2.17.1
# - Sionna 1.2.1
# - OpenNTN 0.1.0
```

### Verify Installation

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/openNTN_integration
python -c "from leo_channel import LEOChannelModel; print('✓ Installation verified')"
```

## Quick Start

### LEO Satellite Example

```python
from leo_channel import LEOChannelModel

# Create LEO channel model (Starlink-like)
leo = LEOChannelModel(
    carrier_frequency=2.0e9,  # 2 GHz S-band
    altitude_km=550,           # Starlink altitude
    scenario='urban',          # Urban scenario
    direction='downlink'
)

# Calculate link budget at 30° elevation
budget = leo.calculate_link_budget(elevation_angle=30.0)

print(f"Path Loss: {budget['free_space_path_loss_db']:.2f} dB")
print(f"Doppler Shift: {budget['doppler_shift_khz']:.2f} kHz")
print(f"Slant Range: {budget['slant_range_km']:.2f} km")
```

**Output:**
```
✓ LEO Channel Model initialized:
  - Scenario: urban
  - Altitude: 550 km
  - Frequency: 2.00 GHz
  - Direction: downlink
  - Orbital velocity: 7.59 km/s
  - Orbital period: 95.50 min

Path Loss: 158.41 dB
Doppler Shift: 25.31 kHz
Slant Range: 992.78 km
```

### MEO Satellite Example

```python
from meo_channel import MEOChannelModel

# Create MEO channel model (O3b-like)
meo = MEOChannelModel(
    carrier_frequency=2.0e9,
    altitude_km=8062,
    scenario='suburban'
)

budget = meo.calculate_link_budget(elevation_angle=45.0)
print(f"MEO Path Loss: {budget['free_space_path_loss_db']:.2f} dB")
print(f"MEO Doppler: {budget['doppler_shift_khz']:.2f} kHz")
```

### GEO Satellite Example

```python
from geo_channel import GEOChannelModel

# Create GEO channel model
geo = GEOChannelModel(
    carrier_frequency=2.0e9,
    altitude_km=35786,
    scenario='urban',
    longitude_deg=0.0  # Prime meridian
)

budget = geo.calculate_link_budget(elevation_angle=30.0)
print(f"GEO Path Loss: {budget['free_space_path_loss_db']:.2f} dB")
print(f"GEO Doppler: {budget['doppler_shift_hz']:.2f} Hz")
print(f"Round Trip Delay: {budget['round_trip_delay_ms']:.2f} ms")

# Calculate coverage area
coverage = geo.calculate_coverage_area(min_elevation_deg=10.0)
print(f"Coverage Area: {coverage['coverage_area_million_km2']:.2f} million km²")
```

## API Reference

### LEOChannelModel

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `carrier_frequency` | float | 2.0e9 | Carrier frequency in Hz |
| `altitude_km` | float | 550.0 | Altitude in km (550-1200) |
| `scenario` | str | 'urban' | Channel scenario |
| `direction` | str | 'downlink' | Link direction |
| `enable_pathloss` | bool | True | Enable path loss |
| `enable_shadow_fading` | bool | True | Enable shadow fading |
| `enable_doppler` | bool | True | Enable Doppler effects |

#### Key Methods

**`calculate_link_budget(elevation_angle)`**
- Calculates comprehensive link budget
- Returns dict with path loss, Doppler, slant range, etc.

**`calculate_slant_range(elevation_angle)`**
- Calculates satellite-to-ground distance
- Returns float in kilometers

**`calculate_doppler_shift(elevation_angle)`**
- Calculates Doppler shift
- Returns float in Hz

**`get_channel_parameters()`**
- Returns complete channel configuration
- Returns dict with all parameters

**`apply_channel(signal, elevation_angle, ...)`**
- Applies channel effects to signal
- Returns tuple (output_signal, channel_info)

### MEOChannelModel

Inherits from `LEOChannelModel` with MEO-specific parameters:
- Altitude range: 8,000-20,000 km
- Lower Doppler shift (~4-5x less than LEO)
- Longer orbital periods (4-12 hours)

### GEOChannelModel

Inherits from `LEOChannelModel` with GEO-specific features:
- Altitude: ~35,786 km (geostationary)
- Minimal Doppler (<100 Hz)
- 24-hour orbital period
- Additional method: `calculate_coverage_area(min_elevation_deg)`

## Testing

### Run Comprehensive Tests

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/openNTN_integration
python test_leo_channel.py
```

**Test Coverage:**
1. ✓ LEO Elevation Angle Sweep (10-90°)
2. ✓ Altitude Comparison (550-1200 km)
3. ✓ Scenario Comparison (urban, suburban, dense_urban)
4. ✓ Orbit Comparison (LEO vs MEO vs GEO)
5. ✓ 3GPP TR38.811 Compliance

**Test Results:**
```
======================================================================
Test Summary
======================================================================
  ✓ PASS: LEO Elevation Sweep
  ✓ PASS: Altitude Comparison
  ✓ PASS: Scenario Comparison
  ✓ PASS: Orbit Comparison
  ✓ PASS: 3GPP TR38.811 Compliance

Overall: 5/5 tests passed

🎉 All tests passed successfully!
```

### Test Outputs

Results saved to `test_results/`:
- `ntn_channel_test_results.png`: Visualization plots
- `test_results.json`: Detailed test data

## Technical Details

### Path Loss Calculation

Free-Space Path Loss (FSPL) is calculated using:

```
FSPL(dB) = 20*log10(4*π*d/λ)
```

where:
- `d` = slant range (m)
- `λ` = wavelength (m)

### Slant Range Geometry

Using spherical Earth geometry:

```
d = sqrt((R+h)² - (R*cos(θ))²) - R*sin(θ)
```

where:
- `R` = Earth radius (6,371 km)
- `h` = satellite altitude (km)
- `θ` = elevation angle (radians)

### Doppler Shift Calculation

```
f_doppler = (v_radial / c) * f_carrier
```

where:
- `v_radial` = radial velocity component (m/s)
- `c` = speed of light (m/s)
- `f_carrier` = carrier frequency (Hz)

For satellites:
- `v_radial = v_sat * cos(90° - elevation)`

### Orbital Parameters

Calculated using Kepler's laws:

**Orbital Velocity:**
```
v = sqrt(GM / r)
```

**Orbital Period:**
```
T = 2*π*r / v
```

where:
- `GM` = 398,600.4418 km³/s² (Earth standard gravitational parameter)
- `r` = orbital radius = R_earth + altitude

## Performance

### Typical Link Budget Values

| Orbit | Altitude | Path Loss @ 30° | Doppler @ 30° | Period |
|-------|----------|-----------------|---------------|--------|
| LEO | 550 km | 158.4 dB | 25.3 kHz | 95 min |
| MEO | 8,062 km | 178.6 dB | 17.5 kHz | 288 min |
| GEO | 35,786 km | 190.2 dB | 17.8 Hz | 24 hours |

## 3GPP TR38.811 Compliance

This implementation supports:

### Frequency Bands
- **S-band**: 1.9-4.0 GHz
- **Ka-band**: 19-40 GHz

### Scenarios
- **Urban**: Urban environment model
- **Suburban**: Suburban environment model
- **Dense Urban**: Dense urban environment model

### Elevation Angles
- **Range**: 10-90 degrees
- **Typical minimum**: 10° (horizon)
- **Optimal**: 30-60° (balance between path loss and coverage)

### Link Types
- **Uplink**: Ground to satellite
- **Downlink**: Satellite to ground

## Integration with OpenNTN

This package is built on top of OpenNTN (https://github.com/ant-uni-bremen/OpenNTN), which implements the full 3GPP TR38.811 channel models including:

- Large Scale Parameters (LSP)
- Small Scale Fading
- Shadow Fading
- Multi-path Propagation
- Antenna Patterns (38.901)
- Doppler Effects

Our wrappers provide simplified access to these models for SDR-O-RAN integration.

## Next Steps for E2SM-NTN Integration

### Phase 3: RIC Integration
1. **E2SM-NTN KPM**: Key Performance Metrics
   - Path loss measurements
   - Doppler shift reporting
   - Link quality indicators

2. **xApp Development**:
   - Satellite handover management
   - Link budget optimization
   - Coverage prediction

3. **Channel-aware Scheduling**:
   - Elevation-based resource allocation
   - Doppler compensation
   - Adaptive modulation and coding

### Recommended Architecture

```python
# Pseudo-code for E2SM-NTN integration

class NTNxApp:
    def __init__(self):
        self.leo_model = LEOChannelModel(...)

    def on_measurement_report(self, ue_id, elevation):
        # Get current link budget
        budget = self.leo_model.calculate_link_budget(elevation)

        # Make RIC control decision
        if budget['path_loss_db'] > THRESHOLD:
            self.trigger_handover(ue_id)
        else:
            self.optimize_mcs(ue_id, budget)
```

## File Structure

```
openNTN_integration/
├── __init__.py              # Package initialization
├── README.md                # This file
├── leo_channel.py           # LEO channel model
├── meo_channel.py           # MEO channel model
├── geo_channel.py           # GEO channel model
├── test_leo_channel.py      # Comprehensive tests
└── test_results/            # Test outputs
    ├── ntn_channel_test_results.png
    └── test_results.json
```

## Dependencies

- Python 3.12+
- TensorFlow 2.17.1
- Sionna 1.2.1
- OpenNTN 0.1.0
- NumPy
- Matplotlib

## References

1. 3GPP TR 38.811: "Study on New Radio (NR) to support non-terrestrial networks"
2. OpenNTN Framework: https://github.com/ant-uni-bremen/OpenNTN
3. Sionna Framework: https://nvlabs.github.io/sionna/
4. Paper: "OpenNTN: An Open-Source Framework for Non-Terrestrial Network Channel Simulations"

## License

MIT License - Compatible with OpenNTN and Sionna

## Authors

- **OpenNTN Integration Specialist** - Initial wrappers and testing
- Based on OpenNTN by University of Bremen
- Built on Sionna by NVIDIA

## Support

For issues or questions:
1. Check test results: `test_results/test_results.json`
2. Review OpenNTN documentation
3. Consult 3GPP TR 38.811 specification

## Changelog

### Version 1.0.0 (2025-11-17)
- Initial release
- LEO, MEO, GEO channel wrappers
- Comprehensive test suite
- Full 3GPP TR38.811 compliance
- All tests passing (5/5)
