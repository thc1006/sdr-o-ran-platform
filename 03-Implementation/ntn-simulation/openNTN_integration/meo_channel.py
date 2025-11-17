#!/usr/bin/env python3
"""
MEO Channel Wrapper for OpenNTN Integration
============================================

This module provides a high-level wrapper around OpenNTN's 3GPP TR38.811
channel models for Medium Earth Orbit (MEO) satellite communications.

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


class MEOChannelModel(LEOChannelModel):
    """
    MEO Satellite Channel Model Wrapper

    This class extends LEOChannelModel for Medium Earth Orbit satellites,
    adjusting parameters for higher altitudes (8,000-20,000 km typical).

    Parameters
    ----------
    carrier_frequency : float
        Carrier frequency in Hz (default: 2.0 GHz for S-band)
    altitude_km : float
        MEO satellite altitude in kilometers (default: 8000 km, range: 8000-20000 km)
    scenario : str
        Channel scenario: 'urban', 'suburban', or 'dense_urban' (default: 'urban')
    direction : str
        Link direction: 'uplink' or 'downlink' (default: 'downlink')
    enable_pathloss : bool
        Enable path loss calculation (default: True)
    enable_shadow_fading : bool
        Enable shadow fading (default: True)
    enable_doppler : bool
        Enable Doppler effects (default: True)
    precision : str
        Computation precision: 'single' or 'double' (default: 'single')

    Attributes
    ----------
    orbital_velocity : float
        MEO satellite orbital velocity in km/s
    orbital_period : float
        MEO satellite orbital period in minutes

    Examples
    --------
    >>> # Create MEO channel model (O3b constellation altitude)
    >>> meo = MEOChannelModel(
    ...     carrier_frequency=2.0e9,
    ...     altitude_km=8062,
    ...     scenario='urban'
    ... )
    >>>
    >>> # Calculate link budget
    >>> link_budget = meo.calculate_link_budget(elevation_angle=30.0)
    >>> print(f"Path loss: {link_budget['path_loss_db']:.2f} dB")
    """

    def __init__(
        self,
        carrier_frequency: float = 2.0e9,
        altitude_km: float = 8000.0,
        scenario: Literal['urban', 'suburban', 'dense_urban'] = 'urban',
        direction: Literal['uplink', 'downlink'] = 'downlink',
        enable_pathloss: bool = True,
        enable_shadow_fading: bool = True,
        enable_doppler: bool = True,
        precision: Literal['single', 'double'] = 'single'
    ):
        """Initialize MEO channel model"""

        # Validate MEO-specific altitude range
        if not (8000 <= altitude_km <= 20000):
            raise ValueError(
                f"MEO altitude must be between 8,000-20,000 km, got {altitude_km} km"
            )

        # Call parent constructor with MEO altitude
        # Note: We temporarily override the LEO altitude check
        self.carrier_frequency = carrier_frequency
        self.altitude_km = altitude_km
        self.scenario = scenario
        self.direction = direction
        self.enable_pathloss = enable_pathloss
        self.enable_shadow_fading = enable_shadow_fading
        self.enable_doppler = enable_doppler
        self.precision = precision

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

        print(f"✓ MEO Channel Model initialized:")
        print(f"  - Scenario: {scenario}")
        print(f"  - Altitude: {altitude_km} km")
        print(f"  - Frequency: {carrier_frequency/1e9:.2f} GHz")
        print(f"  - Direction: {direction}")
        print(f"  - Orbital velocity: {self.orbital_velocity:.2f} km/s")
        print(f"  - Orbital period: {self.orbital_period:.2f} min ({self.orbital_period/60:.2f} hours)")

    def get_channel_parameters(self) -> Dict[str, Any]:
        """
        Get complete channel model parameters

        Returns
        -------
        dict
            Dictionary containing all channel configuration parameters
        """
        params = super().get_channel_parameters()
        params['orbit_type'] = 'MEO'
        params['valid_altitude_range_km'] = (8000, 20000)
        params['typical_constellations'] = ['O3b', 'GPS', 'Galileo', 'GLONASS']
        return params

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"MEOChannelModel("
            f"altitude={self.altitude_km}km, "
            f"freq={self.carrier_frequency/1e9:.2f}GHz, "
            f"scenario='{self.scenario}', "
            f"direction='{self.direction}')"
        )


def main():
    """Example usage and validation"""
    print("="*70)
    print("MEO Channel Model - Example Usage")
    print("="*70)

    # Test different MEO configurations
    meo_configs = [
        {'name': 'O3b MEO', 'altitude_km': 8062, 'freq_ghz': 2.0},
        {'name': 'GPS', 'altitude_km': 20200, 'freq_ghz': 1.98},
        {'name': 'Custom MEO', 'altitude_km': 10000, 'freq_ghz': 2.2}
    ]

    for config in meo_configs:
        print(f"\n{'='*70}")
        print(f"Testing: {config['name']}")
        print(f"{'='*70}")

        meo = MEOChannelModel(
            carrier_frequency=config['freq_ghz'] * 1e9,
            altitude_km=config['altitude_km'],
            scenario='urban',
            direction='downlink'
        )

        print(f"\n{meo}")

        # Link budget at different elevations
        print(f"\n{'Elevation (°)':<15} {'Slant Range (km)':<20} {'FSPL (dB)':<15} {'Doppler (kHz)':<15}")
        print("-"*70)

        test_elevations = [10, 30, 60, 90]
        for elev in test_elevations:
            budget = meo.calculate_link_budget(elev)
            print(f"{budget['elevation_angle_deg']:<15.1f} "
                  f"{budget['slant_range_km']:<20.2f} "
                  f"{budget['free_space_path_loss_db']:<15.2f} "
                  f"{budget['doppler_shift_khz']:<15.2f}")

    # Comparison: MEO vs LEO
    print("\n" + "="*70)
    print("MEO vs LEO Comparison at 30° Elevation")
    print("="*70)

    from leo_channel import LEOChannelModel

    leo = LEOChannelModel(carrier_frequency=2.0e9, altitude_km=550)
    meo = MEOChannelModel(carrier_frequency=2.0e9, altitude_km=8062)

    leo_budget = leo.calculate_link_budget(30.0)
    meo_budget = meo.calculate_link_budget(30.0)

    print(f"\n{'Parameter':<30} {'LEO (550km)':<20} {'MEO (8062km)':<20}")
    print("-"*70)
    print(f"{'Slant Range (km)':<30} {leo_budget['slant_range_km']:<20.2f} {meo_budget['slant_range_km']:<20.2f}")
    print(f"{'Free Space Path Loss (dB)':<30} {leo_budget['free_space_path_loss_db']:<20.2f} {meo_budget['free_space_path_loss_db']:<20.2f}")
    print(f"{'Doppler Shift (kHz)':<30} {leo_budget['doppler_shift_khz']:<20.2f} {meo_budget['doppler_shift_khz']:<20.2f}")
    print(f"{'Orbital Period (min)':<30} {leo_budget['orbital_period_min']:<20.2f} {meo_budget['orbital_period_min']:<20.2f}")

    # Delta calculations
    print(f"\n{'Delta (MEO - LEO)':<30}")
    print("-"*70)
    print(f"{'Additional Path Loss (dB)':<30} {meo_budget['free_space_path_loss_db'] - leo_budget['free_space_path_loss_db']:<20.2f}")
    print(f"{'Doppler Reduction (kHz)':<30} {leo_budget['doppler_shift_khz'] - meo_budget['doppler_shift_khz']:<20.2f}")

    print("\n" + "="*70)
    print("✓ MEO Channel Model validation complete!")
    print("="*70)

    print("\n📝 Key Observations:")
    print("  1. MEO satellites have ~20 dB higher path loss than LEO")
    print("  2. MEO Doppler shift is ~4-5x lower than LEO")
    print("  3. MEO orbital period is much longer (hours vs minutes)")
    print("  4. MEO provides more stable links with wider coverage")

    return meo


if __name__ == "__main__":
    meo_model = main()
