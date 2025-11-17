# SGP4 Orbit Propagation Module

Production-grade satellite orbit propagation with real TLE data support.

## Quick Start

```python
from orbit_propagation import TLEManager, SGP4Propagator, ConstellationSimulator
from datetime import datetime

# Fetch TLE data
manager = TLEManager()
tles = manager.fetch_starlink_tles(limit=10)

# Propagate single satellite
propagator = SGP4Propagator(tles[0])
geometry = propagator.get_ground_track(25.033, 121.565, 0.0, datetime.utcnow())

print(f"Elevation: {geometry['elevation_deg']:.2f}°")
print(f"Doppler: {geometry['doppler_shift_hz']/1000:.2f} kHz")

# Simulate constellation
constellation = ConstellationSimulator('starlink', max_satellites=100)
visible = constellation.find_visible_satellites(25.033, 121.565, datetime.utcnow())

print(f"Visible satellites: {len(visible)}")
```

## Modules

- **tle_manager.py** - TLE data fetching and caching
- **sgp4_propagator.py** - SGP4 orbit propagation
- **constellation_simulator.py** - Multi-satellite simulation
- **test_sgp4.py** - Comprehensive test suite

## Performance

- **0.028 ms** per satellite propagation
- **35,411** propagations/second
- **8,805** Starlink satellites supported

## Documentation

See [WEEK2-SGP4-FINAL-REPORT.md](../WEEK2-SGP4-FINAL-REPORT.md) for complete documentation.
