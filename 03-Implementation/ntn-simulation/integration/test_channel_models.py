#!/usr/bin/env python3
"""
Integration Tests for OpenNTN Channel Models
=============================================

Test-Driven Development: These tests define the EXPECTED API.
Write tests FIRST, then fix implementations to pass.

Expected API:
- LEOChannelModel(carrier_frequency, altitude_km, scenario)
- calculate_link_budget(elevation_angle, rain_rate=0.0) -> Dict
- MEOChannelModel/GEOChannelModel inherit same interface

Author: Software Integration Specialist
Date: 2025-11-17
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np


class TestLEOChannelModel:
    """Test LEO channel model API"""

    def test_initialization(self):
        """Test LEO channel model initialization"""
        from openNTN_integration import LEOChannelModel

        # Should accept these parameters
        leo = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550,
            scenario='urban'
        )

        assert leo is not None
        assert leo.carrier_frequency == 2.0e9
        assert leo.altitude_km == 550
        assert leo.scenario == 'urban'

    def test_calculate_link_budget_without_rain(self):
        """Test link budget calculation without rain parameter"""
        from openNTN_integration import LEOChannelModel

        leo = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550,
            scenario='urban'
        )

        # Should work without rain_rate parameter (default to 0.0)
        budget = leo.calculate_link_budget(elevation_angle=30.0)

        assert isinstance(budget, dict)
        assert 'path_loss_db' in budget or 'free_space_path_loss_db' in budget
        assert 'doppler_shift_hz' in budget
        assert 'elevation_angle_deg' in budget
        assert 'slant_range_km' in budget

    def test_calculate_link_budget_with_rain(self):
        """Test link budget calculation WITH rain parameter (EXPECTED API)"""
        from openNTN_integration import LEOChannelModel

        leo = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550,
            scenario='urban'
        )

        # EXPECTED: Should accept rain_rate parameter
        budget = leo.calculate_link_budget(
            elevation_angle=30.0,
            rain_rate=0.0  # <-- This should be supported
        )

        assert isinstance(budget, dict)
        assert 'path_loss_db' in budget or 'free_space_path_loss_db' in budget
        assert 'doppler_shift_hz' in budget

    def test_link_budget_ranges_leo(self):
        """Test LEO channel link budget output ranges"""
        from openNTN_integration import LEOChannelModel

        leo = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550,
            scenario='urban'
        )

        budget = leo.calculate_link_budget(elevation_angle=30.0, rain_rate=0.0)

        # Extract path loss (try both possible keys)
        path_loss = budget.get('path_loss_db') or budget.get('free_space_path_loss_db')

        # LEO at 550km, 2GHz should have path loss around 160-170 dB
        assert 160 <= path_loss <= 170, f"LEO path loss {path_loss} dB out of range"

        # Doppler shift should be reasonable
        doppler = budget['doppler_shift_hz']
        assert abs(doppler) <= 50000, f"LEO Doppler {doppler} Hz unreasonable"


class TestMEOChannelModel:
    """Test MEO channel model API"""

    def test_initialization(self):
        """Test MEO channel model initialization"""
        from openNTN_integration import MEOChannelModel

        meo = MEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=8000,
            scenario='suburban'
        )

        assert meo is not None
        assert meo.altitude_km == 8000

    def test_calculate_link_budget(self):
        """Test MEO link budget with rain parameter"""
        from openNTN_integration import MEOChannelModel

        meo = MEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=8000,
            scenario='suburban'
        )

        budget = meo.calculate_link_budget(elevation_angle=45.0, rain_rate=0.0)

        # Extract path loss
        path_loss = budget.get('path_loss_db') or budget.get('free_space_path_loss_db')

        # MEO at 8000km should have higher path loss than LEO
        assert 175 <= path_loss <= 185, f"MEO path loss {path_loss} dB out of range"


class TestGEOChannelModel:
    """Test GEO channel model API"""

    def test_initialization(self):
        """Test GEO channel model initialization"""
        from openNTN_integration import GEOChannelModel

        geo = GEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=35786,
            scenario='rural'
        )

        assert geo is not None
        assert geo.altitude_km == 35786

    def test_calculate_link_budget(self):
        """Test GEO link budget with rain parameter"""
        from openNTN_integration import GEOChannelModel

        geo = GEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=35786,
            scenario='rural'
        )

        budget = geo.calculate_link_budget(elevation_angle=60.0, rain_rate=0.0)

        # Extract path loss
        path_loss = budget.get('path_loss_db') or budget.get('free_space_path_loss_db')

        # GEO at 35786km should have highest path loss
        assert 190 <= path_loss <= 200, f"GEO path loss {path_loss} dB out of range"


class TestChannelModelConsistency:
    """Test API consistency across all orbit types"""

    def test_all_models_have_same_interface(self):
        """Verify LEO, MEO, GEO have consistent interfaces"""
        from openNTN_integration import LEOChannelModel, MEOChannelModel, GEOChannelModel

        models = [
            LEOChannelModel(2.0e9, 550, 'urban'),
            MEOChannelModel(2.0e9, 8000, 'suburban'),
            GEOChannelModel(2.0e9, 35786, 'rural')
        ]

        for model in models:
            # All should have calculate_link_budget method
            assert hasattr(model, 'calculate_link_budget')

            # All should accept elevation_angle and rain_rate
            budget = model.calculate_link_budget(
                elevation_angle=30.0,
                rain_rate=0.0
            )

            # All should return dictionary with these keys
            assert isinstance(budget, dict)
            path_loss_key = 'path_loss_db' if 'path_loss_db' in budget else 'free_space_path_loss_db'
            assert path_loss_key in budget
            assert 'doppler_shift_hz' in budget


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
