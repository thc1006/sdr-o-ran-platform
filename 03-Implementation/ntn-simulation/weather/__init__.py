"""
Weather Data Integration Module

This module provides real-time weather data integration with ITU-R P.618
rain attenuation models for accurate NTN link budget calculations.

Components:
- ITU-R P.618-13 rain attenuation model
- Weather API integration (OpenWeatherMap)
- Real-time attenuation calculator
- Cloud and atmospheric loss models
"""

from .itur_p618 import ITUR_P618_RainAttenuation
from .weather_api import WeatherDataProvider
from .realtime_attenuation import RealtimeAttenuationCalculator

__all__ = [
    'ITUR_P618_RainAttenuation',
    'WeatherDataProvider',
    'RealtimeAttenuationCalculator'
]

__version__ = '1.0.0'
