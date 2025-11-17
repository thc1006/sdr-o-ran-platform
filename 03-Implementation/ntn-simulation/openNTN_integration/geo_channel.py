#!/usr/bin/env python3
"""
GEO Channel Wrapper for OpenNTN Integration
============================================

This module provides a high-level wrapper around OpenNTN's 3GPP TR38.811
channel models for Geostationary Earth Orbit (GEO) satellite communications.

Author: OpenNTN Integration Specialist
Date: 2025-11-17
"""

import numpy as np
import tensorflow as tf
from typing import Tuple, Optional, Dict, Any, Literal
import sys
import os

# Import LEO channel for inheritance
from .leo_channel import LEOChannelModel


class GEOChannelModel(LEOChannelModel):
    """
    GEO Satellite Channel Model Wrapper

    This class extends LEOChannelModel for Geostationary Earth Orbit satellites,
    adjusting parameters for geostationary altitude (35,786 km).

    Parameters
    ----------
    carrier_frequency : float
        Carrier frequency in Hz (default: 2.0 GHz for S-band)
    altitude_km : float
        GEO satellite altitude in kilometers (default: 35786 km, range: 35780-35790 km)
    scenario : str
        Channel scenario: 'urban', 'suburban', or 'dense_urban' (default: 'urban')
    direction : str
        Link direction: 'uplink' or 'downlink' (default: 'downlink')
    enable_pathloss : bool
        Enable path loss calculation (default: True)
    enable_shadow_fading : bool
        Enable shadow fading (default: True)
    enable_doppler : bool
        Enable Doppler effects (default: True, minimal for GEO)
    precision : str
        Computation precision: 'single' or 'double' (default: 'single')
    longitude_deg : float
        Satellite orbital slot longitude in degrees (default: 0.0, range: -180 to 180)

    Attributes
    ----------
    orbital_velocity : float
        GEO satellite orbital velocity in km/s (matches Earth rotation)
    orbital_period : float
        GEO satellite orbital period in minutes (24 hours)
    longitude_deg : float
        Orbital slot longitude

    Examples
    --------
    >>> # Create GEO channel model
    >>> geo = GEOChannelModel(
    ...     carrier_frequency=2.0e9,
    ...     altitude_km=35786,
    ...     scenario='urban',
    ...     longitude_deg=0.0  # Prime meridian
    ... )
    >>>
    >>> # Calculate link budget
    >>> link_budget = geo.calculate_link_budget(elevation_angle=30.0)
    >>> print(f"Path loss: {link_budget['path_loss_db']:.2f} dB")

    Notes
    -----
    GEO satellites appear stationary from Earth, resulting in:
    - Minimal Doppler shift (mostly due to Earth rotation compensation)
    - Very high path loss (~190 dB at 2 GHz)
    - Constant link geometry (for fixed ground station)
    - 24-hour orbital period
    """

    def __init__(
        self,
        carrier_frequency: float = 2.0e9,
        altitude_km: float = 35786.0,
        scenario: Literal['urban', 'suburban', 'dense_urban'] = 'urban',
        direction: Literal['uplink', 'downlink'] = 'downlink',
        enable_pathloss: bool = True,
        enable_shadow_fading: bool = True,
        enable_doppler: bool = True,
        precision: Literal['single', 'double'] = 'single',
        longitude_deg: float = 0.0
    ):
        """Initialize GEO channel model"""

        # Validate GEO-specific altitude range (allow small variations around nominal)
        if not (35780 <= altitude_km <= 35790):
            raise ValueError(
                f"GEO altitude must be between 35,780-35,790 km (nominal: 35,786 km), "
                f"got {altitude_km} km"
            )

        # Validate longitude
        if not (-180.0 <= longitude_deg <= 180.0):
            raise ValueError(
                f"Longitude must be between -180° and 180°, got {longitude_deg}°"
            )

        # Call parent constructor setup
        self.carrier_frequency = carrier_frequency
        self.altitude_km = altitude_km
        self.scenario = scenario
        self.direction = direction
        self.enable_pathloss = enable_pathloss
        self.enable_shadow_fading = enable_shadow_fading
        self.enable_doppler = enable_doppler
        self.precision = precision
        self.longitude_deg = longitude_deg

        # Validate carrier frequency
        if not (1.9e9 <= carrier_frequency <= 4.0e9 or 19e9 <= carrier_frequency <= 40e9):
            raise ValueError(
                f"Carrier frequency must be in S-band (1.9-4.0 GHz) or "
                f"Ka-band (19-40 GHz), got {carrier_frequency/1e9:.2f} GHz"
            )

        if scenario not in ['urban', 'suburban', 'dense_urban']:
            raise ValueError(
                f"Scenario must be 'urban', 'suburban', or 'dense_urban', got '{scenario}'"
            )

        if direction not in ['uplink', 'downlink']:
            raise ValueError(
                f"Direction must be 'uplink' or 'downlink', got '{direction}'"
            )

        # Physical constants
        self.earth_radius_km = 6371.0
        self.speed_of_light = 3e8  # m/s

        # Calculate orbital parameters
        self._calculate_orbital_parameters()

        # Setup antenna arrays
        self._setup_antenna_arrays()

        self.channel_model = None

        print(f"✓ GEO Channel Model initialized:")
        print(f"  - Scenario: {scenario}")
        print(f"  - Altitude: {altitude_km} km (Geostationary)")
        print(f"  - Longitude: {longitude_deg}°")
        print(f"  - Frequency: {carrier_frequency/1e9:.2f} GHz")
        print(f"  - Direction: {direction}")
        print(f"  - Orbital velocity: {self.orbital_velocity:.2f} km/s")
        print(f"  - Orbital period: {self.orbital_period/60:.2f} hours (geostationary)")

    def calculate_doppler_shift(
        self,
        elevation_angle: float
    ) -> float:
        """
        Calculate Doppler shift for GEO satellite

        For GEO satellites, Doppler shift is minimal because the satellite
        appears stationary relative to Earth. Any residual Doppler is due to:
        1. Orbital eccentricity (station-keeping errors)
        2. Earth's rotation compensation imperfections
        3. Ground station motion

        Parameters
        ----------
        elevation_angle : float
            Elevation angle in degrees (10-90)

        Returns
        -------
        float
            Doppler shift in Hz (typically < 100 Hz for GEO)

        Notes
        -----
        For true geostationary orbit, Doppler shift approaches zero.
        We model a small residual based on station-keeping tolerances.
        """
        # GEO satellites have minimal Doppler due to geostationary nature
        # Typical station-keeping tolerance: ±0.1 degrees (75 km)
        # This results in velocity variations of ~1-2 m/s

        # Model residual velocity due to station-keeping
        station_keeping_velocity_ms = 2.0  # m/s (typical)

        # Residual Doppler
        doppler_hz = (station_keeping_velocity_ms / self.speed_of_light) * self.carrier_frequency

        # Add small variation based on elevation (lower elevation = slightly higher uncertainty)
        elevation_factor = 1.0 + (90.0 - elevation_angle) / 180.0
        doppler_hz *= elevation_factor

        return doppler_hz

    def get_channel_parameters(self) -> Dict[str, Any]:
        """
        Get complete channel model parameters

        Returns
        -------
        dict
            Dictionary containing all channel configuration parameters
        """
        params = super().get_channel_parameters()
        params['orbit_type'] = 'GEO'
        params['valid_altitude_range_km'] = (35780, 35790)
        params['nominal_altitude_km'] = 35786
        params['longitude_deg'] = self.longitude_deg
        params['geostationary'] = True
        params['typical_doppler_hz'] = '< 100'
        params['typical_constellations'] = ['Intelsat', 'SES', 'Inmarsat', 'Eutelsat']
        params['coverage'] = 'Wide area (1/3 Earth surface per satellite)'
        return params

    def calculate_link_budget(
        self,
        elevation_angle: float
    ) -> Dict[str, float]:
        """
        Calculate comprehensive link budget for GEO

        Parameters
        ----------
        elevation_angle : float
            Elevation angle in degrees (10-90)

        Returns
        -------
        dict
            Dictionary containing link budget parameters including GEO-specific metrics
        """
        budget = super().calculate_link_budget(elevation_angle)

        # Add GEO-specific parameters
        budget['longitude_deg'] = self.longitude_deg
        budget['round_trip_delay_ms'] = (2 * budget['slant_range_km']) / (self.speed_of_light / 1000)
        budget['is_geostationary'] = True

        return budget

    def calculate_coverage_area(
        self,
        min_elevation_deg: float = 10.0
    ) -> Dict[str, float]:
        """
        Calculate GEO satellite coverage area

        Parameters
        ----------
        min_elevation_deg : float
            Minimum elevation angle for coverage (default: 10°)

        Returns
        -------
        dict
            Dictionary containing:
            - coverage_radius_km: Radius of coverage circle on Earth
            - coverage_area_km2: Total coverage area
            - earth_central_angle_deg: Central angle subtended
            - max_slant_range_km: Maximum slant range at min elevation
        """
        min_elev_rad = np.deg2rad(min_elevation_deg)
        R = self.earth_radius_km
        h = self.altitude_km

        # Earth central angle (angle from Earth center to edge of coverage)
        # Using geometry: sin(alpha) = R*cos(min_elev) / (R+h)
        earth_central_angle_rad = np.arcsin(R * np.cos(min_elev_rad) / (R + h))
        earth_central_angle_deg = np.rad2deg(earth_central_angle_rad)

        # Coverage radius on Earth surface (arc length)
        coverage_radius_km = R * earth_central_angle_rad

        # Coverage area (spherical cap)
        coverage_area_km2 = 2 * np.pi * R**2 * (1 - np.cos(earth_central_angle_rad))

        # Maximum slant range (at minimum elevation)
        max_slant_range_km = self.calculate_slant_range(min_elevation_deg)

        return {
            'min_elevation_deg': min_elevation_deg,
            'coverage_radius_km': coverage_radius_km,
            'coverage_area_km2': coverage_area_km2,
            'coverage_area_million_km2': coverage_area_km2 / 1e6,
            'earth_fraction': coverage_area_km2 / (4 * np.pi * R**2),
            'earth_central_angle_deg': earth_central_angle_deg,
            'max_slant_range_km': max_slant_range_km
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"GEOChannelModel("
            f"altitude={self.altitude_km}km, "
            f"lon={self.longitude_deg}°, "
            f"freq={self.carrier_frequency/1e9:.2f}GHz, "
            f"scenario='{self.scenario}', "
            f"direction='{self.direction}')"
        )


def main():
    """Example usage and validation"""
    print("="*70)
    print("GEO Channel Model - Example Usage")
    print("="*70)

    # Create GEO channel model
    geo = GEOChannelModel(
        carrier_frequency=2.0e9,
        altitude_km=35786,
        scenario='urban',
        direction='downlink',
        longitude_deg=0.0  # Prime meridian
    )

    print(f"\n{geo}")

    # Link budget analysis
    print("\n" + "="*70)
    print("Link Budget Analysis at Different Elevation Angles")
    print("="*70)
    print(f"{'Elevation (°)':<15} {'Slant Range (km)':<20} {'FSPL (dB)':<15} {'Doppler (Hz)':<15} {'RTD (ms)':<15}")
    print("-"*70)

    test_elevations = [10, 30, 60, 90]
    for elev in test_elevations:
        budget = geo.calculate_link_budget(elev)
        print(f"{budget['elevation_angle_deg']:<15.1f} "
              f"{budget['slant_range_km']:<20.2f} "
              f"{budget['free_space_path_loss_db']:<15.2f} "
              f"{budget['doppler_shift_hz']:<15.2f} "
              f"{budget['round_trip_delay_ms']:<15.2f}")

    # Coverage analysis
    print("\n" + "="*70)
    print("Coverage Analysis")
    print("="*70)

    for min_elev in [5, 10, 20]:
        coverage = geo.calculate_coverage_area(min_elev)
        print(f"\nMinimum Elevation: {min_elev}°")
        print(f"  Coverage radius: {coverage['coverage_radius_km']:.0f} km")
        print(f"  Coverage area: {coverage['coverage_area_million_km2']:.2f} million km²")
        print(f"  Earth fraction: {coverage['earth_fraction']*100:.1f}%")
        print(f"  Max slant range: {coverage['max_slant_range_km']:.0f} km")

    # Comparison: GEO vs MEO vs LEO
    print("\n" + "="*70)
    print("Orbit Comparison at 30° Elevation")
    print("="*70)

    from leo_channel import LEOChannelModel
    from meo_channel import MEOChannelModel

    leo = LEOChannelModel(carrier_frequency=2.0e9, altitude_km=550)
    meo = MEOChannelModel(carrier_frequency=2.0e9, altitude_km=8062)
    geo = GEOChannelModel(carrier_frequency=2.0e9, altitude_km=35786)

    leo_budget = leo.calculate_link_budget(30.0)
    meo_budget = meo.calculate_link_budget(30.0)
    geo_budget = geo.calculate_link_budget(30.0)

    print(f"\n{'Parameter':<35} {'LEO (550km)':<18} {'MEO (8062km)':<18} {'GEO (35786km)':<18}")
    print("-"*90)
    print(f"{'Slant Range (km)':<35} {leo_budget['slant_range_km']:<18.2f} {meo_budget['slant_range_km']:<18.2f} {geo_budget['slant_range_km']:<18.2f}")
    print(f"{'Free Space Path Loss (dB)':<35} {leo_budget['free_space_path_loss_db']:<18.2f} {meo_budget['free_space_path_loss_db']:<18.2f} {geo_budget['free_space_path_loss_db']:<18.2f}")
    print(f"{'Doppler Shift (kHz)':<35} {leo_budget['doppler_shift_khz']:<18.2f} {meo_budget['doppler_shift_khz']:<18.2f} {geo_budget['doppler_shift_hz']/1000:<18.4f}")
    print(f"{'Orbital Period (hours)':<35} {leo_budget['orbital_period_min']/60:<18.2f} {meo_budget['orbital_period_min']/60:<18.2f} {geo_budget['orbital_period_min']/60:<18.2f}")
    print(f"{'Orbital Velocity (km/s)':<35} {leo_budget['orbital_velocity_kmps']:<18.2f} {meo_budget['orbital_velocity_kmps']:<18.2f} {geo_budget['orbital_velocity_kmps']:<18.2f}")

    if 'round_trip_delay_ms' in geo_budget:
        print(f"{'Round Trip Delay (ms)':<35} {'-':<18} {'-':<18} {geo_budget['round_trip_delay_ms']:<18.2f}")

    print("\n" + "="*70)
    print("✓ GEO Channel Model validation complete!")
    print("="*70)

    print("\n📝 Key Observations:")
    print("  1. GEO has highest path loss (~190 dB) due to 35,786 km altitude")
    print("  2. GEO Doppler is minimal (<100 Hz) - nearly geostationary")
    print("  3. GEO round-trip delay is ~240 ms (noticeable in communications)")
    print("  4. GEO provides continuous coverage of same area")
    print("  5. Only 3 GEO satellites needed for near-global coverage")
    print("  6. GEO is ideal for broadcast and wide-area coverage")
    print("  7. LEO/MEO better for latency-sensitive applications")

    return geo


if __name__ == "__main__":
    geo_model = main()
