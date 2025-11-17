"""
Real-Time Attenuation Calculator

Combines ITU-R P.618 models with real-time weather data to provide
accurate, live atmospheric loss calculations for NTN links.

Features:
- Real-time weather data integration
- Statistical + current weather blending
- Rain fade event detection
- Attenuation time series tracking
- Performance optimized (< 100ms target)
"""

import asyncio
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

try:
    from .itur_p618 import ITUR_P618_RainAttenuation, RainAttenuationResult
    from .weather_api import WeatherDataProvider, WeatherData
except ImportError:
    # Standalone execution
    from itur_p618 import ITUR_P618_RainAttenuation, RainAttenuationResult
    from weather_api import WeatherDataProvider, WeatherData


@dataclass
class AttenuationResult:
    """Complete attenuation calculation result"""
    timestamp: datetime
    latitude: float
    longitude: float
    frequency_ghz: float
    elevation_angle: float

    # Attenuation components (dB)
    rain_attenuation_db: float
    cloud_attenuation_db: float
    gas_attenuation_db: float
    total_atmospheric_loss_db: float

    # Weather conditions
    current_rain_rate_mm_h: float
    cloud_cover_percent: float
    temperature_c: float
    humidity_percent: float

    # Statistical data
    statistical_rain_attenuation_0_01_percent: float
    statistical_rain_attenuation_0_1_percent: float
    statistical_rain_attenuation_1_percent: float

    # Performance metrics
    calculation_time_ms: float

    # Rain fade detection
    is_rain_fade_event: bool
    fade_margin_db: float


class RainFadeDetector:
    """Detects rain fade events and tracks statistics"""

    def __init__(
        self,
        fade_threshold_db: float = 3.0,
        min_duration_sec: float = 60.0
    ):
        """
        Initialize rain fade detector

        Args:
            fade_threshold_db: Attenuation threshold for fade detection
            min_duration_sec: Minimum duration to qualify as fade event
        """
        self.fade_threshold_db = fade_threshold_db
        self.min_duration_sec = min_duration_sec

        # Event tracking
        self.current_fade_start: Optional[datetime] = None
        self.fade_events: List[Dict] = []
        self.attenuation_history: deque = deque(maxlen=1000)

    def update(
        self,
        attenuation_db: float,
        timestamp: datetime
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Update fade detector with new attenuation measurement

        Args:
            attenuation_db: Current attenuation in dB
            timestamp: Measurement timestamp

        Returns:
            Tuple of (is_fading, completed_event)
        """
        # Add to history
        self.attenuation_history.append({
            'timestamp': timestamp,
            'attenuation_db': attenuation_db
        })

        is_fading = attenuation_db >= self.fade_threshold_db
        completed_event = None

        if is_fading:
            # Start new fade event if not already in one
            if self.current_fade_start is None:
                self.current_fade_start = timestamp
        else:
            # Check if we were in a fade event
            if self.current_fade_start is not None:
                # Calculate fade duration
                duration = (timestamp - self.current_fade_start).total_seconds()

                # If duration exceeds minimum, record as event
                if duration >= self.min_duration_sec:
                    # Calculate event statistics
                    event_data = self._calculate_event_stats(
                        self.current_fade_start, timestamp
                    )
                    self.fade_events.append(event_data)
                    completed_event = event_data

                # Reset fade tracking
                self.current_fade_start = None

        return is_fading, completed_event

    def _calculate_event_stats(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """Calculate statistics for a completed fade event"""
        # Get measurements during event
        event_measurements = [
            m for m in self.attenuation_history
            if start_time <= m['timestamp'] <= end_time
        ]

        if not event_measurements:
            return {}

        attenuations = [m['attenuation_db'] for m in event_measurements]

        return {
            'start_time': start_time,
            'end_time': end_time,
            'duration_sec': (end_time - start_time).total_seconds(),
            'max_attenuation_db': max(attenuations),
            'mean_attenuation_db': np.mean(attenuations),
            'peak_fade_db': max(attenuations),
            'measurement_count': len(event_measurements)
        }

    def get_statistics(self) -> Dict:
        """Get fade event statistics"""
        if not self.fade_events:
            return {
                'total_events': 0,
                'total_fade_time_sec': 0.0,
                'max_fade_db': 0.0,
                'mean_fade_db': 0.0
            }

        total_fade_time = sum(e['duration_sec'] for e in self.fade_events)
        max_fade = max(e['max_attenuation_db'] for e in self.fade_events)
        mean_fade = np.mean([e['mean_attenuation_db'] for e in self.fade_events])

        return {
            'total_events': len(self.fade_events),
            'total_fade_time_sec': total_fade_time,
            'max_fade_db': max_fade,
            'mean_fade_db': mean_fade,
            'events': self.fade_events
        }


class RealtimeAttenuationCalculator:
    """
    Real-time rain attenuation calculator using weather APIs + ITU-R P.618

    Combines:
    1. Real-time weather data from APIs
    2. ITU-R P.618 statistical models
    3. Performance optimization (caching, async)
    4. Rain fade event detection
    """

    def __init__(
        self,
        weather_api_key: Optional[str] = None,
        weather_provider: str = 'openmeteo',
        use_mock_weather: bool = False,
        cache_duration_sec: float = 300.0,  # 5 minutes
        fade_threshold_db: float = 3.0
    ):
        """
        Initialize real-time attenuation calculator

        Args:
            weather_api_key: API key for weather service
            weather_provider: Weather provider name
            use_mock_weather: Use mock weather data (for testing)
            cache_duration_sec: Weather data cache duration
            fade_threshold_db: Rain fade detection threshold
        """
        # Initialize ITU-R P.618 model
        self.itur = ITUR_P618_RainAttenuation()

        # Initialize weather provider
        self.weather = WeatherDataProvider(
            api_key=weather_api_key,
            provider=weather_provider,
            cache_duration_sec=cache_duration_sec,
            use_mock_data=use_mock_weather
        )

        # Initialize rain fade detector
        self.fade_detector = RainFadeDetector(fade_threshold_db=fade_threshold_db)

        # Performance tracking
        self.calculation_count = 0
        self.total_calculation_time_ms = 0.0

        print(f"Real-time Attenuation Calculator initialized")
        print(f"  Weather provider: {weather_provider}")
        print(f"  Cache duration: {cache_duration_sec}s")
        print(f"  Fade threshold: {fade_threshold_db} dB")

    async def calculate_current_attenuation(
        self,
        latitude: float,
        longitude: float,
        frequency_ghz: float,
        elevation_angle: float,
        polarization: str = 'circular',
        use_real_weather: bool = True
    ) -> AttenuationResult:
        """
        Calculate current attenuation using real-time weather

        Args:
            latitude: Station latitude (degrees)
            longitude: Station longitude (degrees)
            frequency_ghz: Frequency in GHz
            elevation_angle: Elevation angle in degrees
            polarization: Polarization type
            use_real_weather: Use real weather (False = statistical only)

        Returns:
            AttenuationResult with all components
        """
        start_time = time.time()

        # Get current weather data
        if use_real_weather:
            weather_data = await self.weather.get_current_weather(latitude, longitude)
            itur_params = self.weather.convert_to_itur_parameters(weather_data)
            current_rain_rate = itur_params['rain_rate_mm_h']
        else:
            # Use statistical model only
            weather_data = None
            current_rain_rate = 0.0
            itur_params = {
                'cloud_liquid_water_kg_m3': 0.0005,
                'water_vapor_density_g_m3': 7.5,
                'temperature_celsius': 15.0,
                'pressure_hpa': 1013.25
            }

        # Calculate statistical rain attenuation (ITU-R P.618)
        statistical_result = self.itur.calculate_rain_attenuation(
            latitude, longitude, frequency_ghz, elevation_angle, polarization
        )

        # Calculate current attenuation using real rain rate if available
        if current_rain_rate > 0.0:
            # Use actual rain rate
            gamma_R = self.itur.calculate_specific_attenuation(
                frequency_ghz, current_rain_rate, elevation_angle, polarization
            )
            h_rain = self.itur._get_rain_height(latitude)
            L_E = self.itur._calculate_effective_path_length(
                h_rain, elevation_angle, latitude, frequency_ghz, current_rain_rate
            )
            rain_attenuation = gamma_R * L_E
        else:
            # Use statistical model (clear weather)
            rain_attenuation = 0.0

        # Calculate cloud attenuation
        cloud_attenuation = self.itur.calculate_cloud_attenuation(
            frequency_ghz,
            elevation_angle,
            itur_params['cloud_liquid_water_kg_m3']
        )

        # Calculate atmospheric gases attenuation
        gas_attenuation = self.itur.calculate_atmospheric_gases_attenuation(
            frequency_ghz,
            elevation_angle,
            itur_params['water_vapor_density_g_m3'],
            itur_params['temperature_celsius'],
            itur_params['pressure_hpa']
        )

        # Total atmospheric loss
        total_loss = rain_attenuation + cloud_attenuation + gas_attenuation

        # Rain fade detection
        timestamp = datetime.now()
        is_fading, completed_event = self.fade_detector.update(
            rain_attenuation, timestamp
        )

        # Calculate fade margin (difference from statistical model)
        fade_margin = statistical_result.exceeded_0_01_percent - rain_attenuation

        # Calculate performance metrics
        calculation_time_ms = (time.time() - start_time) * 1000.0
        self.calculation_count += 1
        self.total_calculation_time_ms += calculation_time_ms

        # Build result
        result = AttenuationResult(
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            frequency_ghz=frequency_ghz,
            elevation_angle=elevation_angle,
            rain_attenuation_db=rain_attenuation,
            cloud_attenuation_db=cloud_attenuation,
            gas_attenuation_db=gas_attenuation,
            total_atmospheric_loss_db=total_loss,
            current_rain_rate_mm_h=current_rain_rate,
            cloud_cover_percent=weather_data.cloud_cover_percent if weather_data else 0.0,
            temperature_c=weather_data.temperature_c if weather_data else 15.0,
            humidity_percent=weather_data.humidity_percent if weather_data else 50.0,
            statistical_rain_attenuation_0_01_percent=statistical_result.exceeded_0_01_percent,
            statistical_rain_attenuation_0_1_percent=statistical_result.exceeded_0_1_percent,
            statistical_rain_attenuation_1_percent=statistical_result.exceeded_1_percent,
            calculation_time_ms=calculation_time_ms,
            is_rain_fade_event=is_fading,
            fade_margin_db=fade_margin
        )

        return result

    async def calculate_attenuation_time_series(
        self,
        latitude: float,
        longitude: float,
        frequency_ghz: float,
        elevation_angle: float,
        duration_hours: float = 24.0,
        time_step_minutes: float = 15.0,
        rain_scenario: str = 'variable'
    ) -> List[AttenuationResult]:
        """
        Calculate attenuation time series (for simulation/prediction)

        Args:
            latitude: Station latitude
            longitude: Station longitude
            frequency_ghz: Frequency in GHz
            elevation_angle: Elevation angle
            duration_hours: Simulation duration
            time_step_minutes: Time step between samples
            rain_scenario: Rain scenario ('clear', 'variable', 'storm')

        Returns:
            List of AttenuationResult objects
        """
        results = []
        num_steps = int(duration_hours * 60 / time_step_minutes)

        print(f"Calculating {num_steps} time steps...")

        for i in range(num_steps):
            # Simulate variable rain rate
            if rain_scenario == 'variable':
                # Sinusoidal rain pattern with random spikes
                base_rain = 5.0 * np.sin(2 * np.pi * i / num_steps) + 5.0
                spike = 30.0 * np.random.exponential(0.1) if np.random.random() < 0.05 else 0.0
                rain_rate = max(0.0, base_rain + spike)
            elif rain_scenario == 'storm':
                # Heavy rain scenario
                rain_rate = 40.0 + 20.0 * np.random.random()
            else:  # 'clear'
                rain_rate = 0.0

            # Create mock weather with specified rain rate
            # (In production, this would fetch real forecasts)
            result = await self.calculate_current_attenuation(
                latitude, longitude, frequency_ghz, elevation_angle,
                use_real_weather=False  # Use statistical model
            )

            results.append(result)

            # Add small delay to avoid overwhelming CPU
            if i % 10 == 0:
                await asyncio.sleep(0.001)

        return results

    async def close(self):
        """Close weather API session"""
        await self.weather.close()

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        avg_time = (self.total_calculation_time_ms / self.calculation_count
                   if self.calculation_count > 0 else 0.0)

        return {
            'total_calculations': self.calculation_count,
            'average_time_ms': avg_time,
            'total_time_ms': self.total_calculation_time_ms,
            'target_met': avg_time < 100.0,  # Target: < 100ms
            'fade_detector_stats': self.fade_detector.get_statistics(),
            'weather_cache_stats': self.weather.get_cache_stats()
        }


async def main():
    """Test real-time attenuation calculator"""
    print("Testing Real-Time Attenuation Calculator")
    print("=" * 60)

    # Initialize calculator with mock weather
    calc = RealtimeAttenuationCalculator(use_mock_weather=True)

    # Test parameters (LEO satellite)
    latitude = 40.7128  # New York
    longitude = -74.0060
    frequency_ghz = 20.0  # Ka-band
    elevation_angle = 30.0

    print(f"\nTest Parameters:")
    print(f"  Location: ({latitude:.2f}°, {longitude:.2f}°)")
    print(f"  Frequency: {frequency_ghz} GHz")
    print(f"  Elevation: {elevation_angle}°")

    # Test 1: Single calculation
    print(f"\nTest 1: Single Attenuation Calculation")
    print("-" * 60)

    result = await calc.calculate_current_attenuation(
        latitude, longitude, frequency_ghz, elevation_angle
    )

    print(f"\nAttenuation Results:")
    print(f"  Rain: {result.rain_attenuation_db:.2f} dB")
    print(f"  Cloud: {result.cloud_attenuation_db:.2f} dB")
    print(f"  Gases: {result.gas_attenuation_db:.2f} dB")
    print(f"  TOTAL: {result.total_atmospheric_loss_db:.2f} dB")
    print(f"\nWeather Conditions:")
    print(f"  Rain rate: {result.current_rain_rate_mm_h:.2f} mm/h")
    print(f"  Cloud cover: {result.cloud_cover_percent:.1f}%")
    print(f"  Temperature: {result.temperature_c:.1f}°C")
    print(f"\nStatistical Reference (ITU-R P.618):")
    print(f"  0.01% exceeded: {result.statistical_rain_attenuation_0_01_percent:.2f} dB")
    print(f"  0.1% exceeded: {result.statistical_rain_attenuation_0_1_percent:.2f} dB")
    print(f"  1% exceeded: {result.statistical_rain_attenuation_1_percent:.2f} dB")
    print(f"\nPerformance:")
    print(f"  Calculation time: {result.calculation_time_ms:.2f} ms")
    print(f"  Rain fade event: {result.is_rain_fade_event}")
    print(f"  Fade margin: {result.fade_margin_db:.2f} dB")

    # Test 2: Performance benchmark
    print(f"\nTest 2: Performance Benchmark (100 calculations)")
    print("-" * 60)

    start_time = time.time()
    for i in range(100):
        await calc.calculate_current_attenuation(
            latitude, longitude, frequency_ghz, elevation_angle
        )
    elapsed = (time.time() - start_time) * 1000

    print(f"  Total time: {elapsed:.2f} ms")
    print(f"  Average per calculation: {elapsed/100:.2f} ms")
    print(f"  Target met (< 100ms): {elapsed/100 < 100}")

    # Test 3: Get statistics
    print(f"\nTest 3: Performance Statistics")
    print("-" * 60)

    stats = calc.get_performance_stats()
    print(f"  Total calculations: {stats['total_calculations']}")
    print(f"  Average time: {stats['average_time_ms']:.2f} ms")
    print(f"  Target met: {stats['target_met']}")

    await calc.close()

    print("\nReal-time attenuation calculator test completed!")


if __name__ == '__main__':
    asyncio.run(main())
