"""
Weather API Integration Module

Provides real-time weather data from multiple sources:
- OpenWeatherMap (primary)
- Open-Meteo (backup, no API key required)
- NOAA (for US locations)

Converts weather data to ITU-R parameters for attenuation calculations.
"""

import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Try to import aiohttp (optional)
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("Note: aiohttp not available. Only mock weather data will work.")


@dataclass
class WeatherData:
    """Real-time weather conditions"""
    timestamp: datetime
    latitude: float
    longitude: float
    temperature_c: float
    humidity_percent: float
    precipitation_rate_mm_h: float  # Current rain/snow rate
    cloud_cover_percent: float
    pressure_hpa: float
    wind_speed_m_s: float
    wind_direction_deg: float
    weather_description: str
    visibility_m: float
    dew_point_c: Optional[float] = None
    snow_rate_mm_h: Optional[float] = 0.0


class WeatherDataProvider:
    """
    Real-time weather data provider with multiple API backends

    Supports:
    - OpenWeatherMap (requires API key, most accurate)
    - Open-Meteo (free, no API key, good fallback)
    - Mock data (for testing without network)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = 'openweathermap',
        cache_duration_sec: float = 300.0,  # 5 minutes default
        use_mock_data: bool = False
    ):
        """
        Initialize weather data provider

        Args:
            api_key: API key for weather service (required for OpenWeatherMap)
            provider: Weather provider ('openweathermap', 'openmeteo', 'noaa')
            cache_duration_sec: How long to cache weather data (seconds)
            use_mock_data: Use simulated weather data (for testing)
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self.cache_duration_sec = cache_duration_sec
        self.use_mock_data = use_mock_data

        # Weather data cache
        self._cache: Dict[str, tuple] = {}  # {location_key: (weather_data, timestamp)}

        # API endpoints
        self.endpoints = {
            'openweathermap': 'https://api.openweathermap.org/data/2.5/weather',
            'openmeteo': 'https://api.open-meteo.com/v1/forecast',
        }

        # Session for HTTP requests
        self._session = None

        # Check if network features are available
        if not AIOHTTP_AVAILABLE and not use_mock_data:
            print("  Warning: aiohttp not available, switching to mock data mode")
            self.use_mock_data = True

        print(f"Weather API Provider initialized: {self.provider}")
        if self.use_mock_data:
            print("  Using MOCK weather data (testing mode)")
        elif self.provider == 'openweathermap' and not api_key:
            print("  WARNING: No API key provided for OpenWeatherMap")
            print("  Falling back to Open-Meteo (free, no API key required)")
            self.provider = 'openmeteo'

    async def _get_session(self):
        """Get or create HTTP session"""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not available")
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close HTTP session"""
        if self._session and hasattr(self._session, 'closed') and not self._session.closed:
            await self._session.close()

    def _get_cache_key(self, latitude: float, longitude: float) -> str:
        """Generate cache key for location"""
        # Round to 2 decimal places for caching (~ 1 km resolution)
        return f"{latitude:.2f},{longitude:.2f}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return False

        _, cache_time = self._cache[cache_key]
        age = time.time() - cache_time

        return age < self.cache_duration_sec

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        use_cache: bool = True
    ) -> WeatherData:
        """
        Get current weather conditions

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            use_cache: Use cached data if available

        Returns:
            WeatherData object with current conditions
        """
        # Check cache first
        cache_key = self._get_cache_key(latitude, longitude)
        if use_cache and self._is_cache_valid(cache_key):
            weather_data, _ = self._cache[cache_key]
            return weather_data

        # Use mock data if requested
        if self.use_mock_data:
            weather_data = self._generate_mock_weather(latitude, longitude)
            self._cache[cache_key] = (weather_data, time.time())
            return weather_data

        # Fetch from API
        if self.provider == 'openweathermap':
            weather_data = await self._fetch_openweathermap(latitude, longitude)
        elif self.provider == 'openmeteo':
            weather_data = await self._fetch_openmeteo(latitude, longitude)
        else:
            raise ValueError(f"Unsupported weather provider: {self.provider}")

        # Cache the result
        self._cache[cache_key] = (weather_data, time.time())

        return weather_data

    async def _fetch_openweathermap(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherData:
        """Fetch weather from OpenWeatherMap API"""
        if not self.api_key:
            raise ValueError("OpenWeatherMap requires an API key")

        session = await self._get_session()

        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self.api_key,
            'units': 'metric'
        }

        try:
            async with session.get(self.endpoints['openweathermap'], params=params) as response:
                response.raise_for_status()
                data = await response.json()

                # Parse OpenWeatherMap response
                main = data.get('main', {})
                weather = data.get('weather', [{}])[0]
                wind = data.get('wind', {})
                rain = data.get('rain', {})
                snow = data.get('snow', {})
                clouds = data.get('clouds', {})

                # Extract rain rate (mm/h)
                # OpenWeatherMap provides rain volume for last 1h or 3h
                rain_rate = rain.get('1h', 0.0)  # mm in last hour = mm/h
                if rain_rate == 0.0:
                    rain_rate = rain.get('3h', 0.0) / 3.0  # Average over 3h

                snow_rate = snow.get('1h', 0.0)
                if snow_rate == 0.0:
                    snow_rate = snow.get('3h', 0.0) / 3.0

                weather_data = WeatherData(
                    timestamp=datetime.fromtimestamp(data.get('dt', time.time())),
                    latitude=latitude,
                    longitude=longitude,
                    temperature_c=main.get('temp', 15.0),
                    humidity_percent=main.get('humidity', 50.0),
                    precipitation_rate_mm_h=rain_rate + snow_rate,
                    cloud_cover_percent=clouds.get('all', 0.0),
                    pressure_hpa=main.get('pressure', 1013.25),
                    wind_speed_m_s=wind.get('speed', 0.0),
                    wind_direction_deg=wind.get('deg', 0.0),
                    weather_description=weather.get('description', 'unknown'),
                    visibility_m=data.get('visibility', 10000.0),
                    dew_point_c=self._calculate_dew_point(
                        main.get('temp', 15.0),
                        main.get('humidity', 50.0)
                    ),
                    snow_rate_mm_h=snow_rate
                )

                return weather_data

        except aiohttp.ClientError as e:
            print(f"Error fetching OpenWeatherMap data: {e}")
            # Fall back to mock data
            return self._generate_mock_weather(latitude, longitude)

    async def _fetch_openmeteo(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherData:
        """Fetch weather from Open-Meteo API (free, no API key)"""
        session = await self._get_session()

        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current_weather': 'true',
            'hourly': 'temperature_2m,relativehumidity_2m,precipitation,cloudcover,pressure_msl,visibility'
        }

        try:
            async with session.get(self.endpoints['openmeteo'], params=params) as response:
                response.raise_for_status()
                data = await response.json()

                # Parse Open-Meteo response
                current = data.get('current_weather', {})
                hourly = data.get('hourly', {})

                # Get current hour index
                current_time_idx = 0

                temperature = current.get('temperature', 15.0)
                humidity = hourly['relativehumidity_2m'][current_time_idx] if 'relativehumidity_2m' in hourly else 50.0
                precipitation = hourly['precipitation'][current_time_idx] if 'precipitation' in hourly else 0.0
                cloud_cover = hourly['cloudcover'][current_time_idx] if 'cloudcover' in hourly else 0.0
                pressure = hourly['pressure_msl'][current_time_idx] if 'pressure_msl' in hourly else 1013.25
                visibility = hourly['visibility'][current_time_idx] if 'visibility' in hourly else 10000.0

                weather_data = WeatherData(
                    timestamp=datetime.now(),
                    latitude=latitude,
                    longitude=longitude,
                    temperature_c=temperature,
                    humidity_percent=humidity,
                    precipitation_rate_mm_h=precipitation,  # Already in mm/h
                    cloud_cover_percent=cloud_cover,
                    pressure_hpa=pressure,
                    wind_speed_m_s=current.get('windspeed', 0.0) / 3.6,  # km/h to m/s
                    wind_direction_deg=current.get('winddirection', 0.0),
                    weather_description='from open-meteo',
                    visibility_m=visibility,
                    dew_point_c=self._calculate_dew_point(temperature, humidity),
                    snow_rate_mm_h=0.0
                )

                return weather_data

        except Exception as e:
            print(f"Error fetching Open-Meteo data: {e}")
            # Fall back to mock data
            return self._generate_mock_weather(latitude, longitude)

    def _generate_mock_weather(
        self,
        latitude: float,
        longitude: float,
        rain_scenario: str = 'normal'
    ) -> WeatherData:
        """
        Generate mock weather data for testing

        Args:
            latitude: Latitude
            longitude: Longitude
            rain_scenario: 'clear', 'normal', 'light_rain', 'heavy_rain', 'storm'
        """
        # Vary by latitude for realism
        lat_abs = abs(latitude)

        # Temperature decreases with latitude
        temp_base = 30 - 0.5 * lat_abs

        # Rain scenarios
        rain_scenarios = {
            'clear': 0.0,
            'normal': 0.5,
            'light_rain': 5.0,
            'moderate_rain': 15.0,
            'heavy_rain': 40.0,
            'storm': 80.0
        }

        rain_rate = rain_scenarios.get(rain_scenario, 0.5)

        # Cloud cover correlates with rain
        cloud_cover = min(100.0, rain_rate * 5 + 20)

        weather_data = WeatherData(
            timestamp=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            temperature_c=temp_base,
            humidity_percent=70.0,
            precipitation_rate_mm_h=rain_rate,
            cloud_cover_percent=cloud_cover,
            pressure_hpa=1013.25,
            wind_speed_m_s=5.0,
            wind_direction_deg=180.0,
            weather_description=f'mock_{rain_scenario}',
            visibility_m=10000.0,
            dew_point_c=self._calculate_dew_point(temp_base, 70.0),
            snow_rate_mm_h=0.0
        )

        return weather_data

    def _calculate_dew_point(self, temperature_c: float, humidity_percent: float) -> float:
        """Calculate dew point using Magnus formula"""
        a = 17.27
        b = 237.7

        alpha = ((a * temperature_c) / (b + temperature_c)) + np.log(humidity_percent / 100.0)
        dew_point = (b * alpha) / (a - alpha)

        return dew_point

    def convert_to_itur_parameters(self, weather_data: WeatherData) -> Dict[str, float]:
        """
        Convert weather API data to ITU-R P.618 parameters

        Args:
            weather_data: WeatherData object

        Returns:
            Dictionary with ITU-R parameters
        """
        # Rain rate (already in mm/h)
        rain_rate_mm_h = weather_data.precipitation_rate_mm_h

        # Cloud liquid water content (estimated from cloud cover and humidity)
        # Typical values: 0.0001 to 0.001 kg/m^3
        cloud_liquid_water_kg_m3 = (
            weather_data.cloud_cover_percent / 100.0 *
            weather_data.humidity_percent / 100.0 *
            0.001
        )

        # Water vapor density (from humidity and temperature)
        # Using Magnus formula and ideal gas law
        if weather_data.dew_point_c is not None:
            # Saturation vapor pressure at dew point
            e_s = 6.112 * np.exp((17.67 * weather_data.dew_point_c) /
                                  (weather_data.dew_point_c + 243.5))
            # Water vapor density (g/m^3)
            water_vapor_density_g_m3 = (e_s * 2.16679) / (weather_data.temperature_c + 273.15)
        else:
            # Fallback estimation
            water_vapor_density_g_m3 = weather_data.humidity_percent / 100.0 * 15.0

        return {
            'rain_rate_mm_h': rain_rate_mm_h,
            'cloud_liquid_water_kg_m3': cloud_liquid_water_kg_m3,
            'water_vapor_density_g_m3': water_vapor_density_g_m3,
            'temperature_celsius': weather_data.temperature_c,
            'pressure_hpa': weather_data.pressure_hpa,
            'humidity_percent': weather_data.humidity_percent
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        valid_entries = sum(1 for key in self._cache.keys() if self._is_cache_valid(key))

        return {
            'total_cached_locations': len(self._cache),
            'valid_cached_locations': valid_entries,
            'cache_duration_sec': self.cache_duration_sec,
            'provider': self.provider
        }


# Import numpy for calculations
import numpy as np


async def main():
    """Test weather API integration"""
    print("Testing Weather API Integration")
    print("=" * 60)

    # Test with Open-Meteo (free, no API key)
    provider = WeatherDataProvider(provider='openmeteo', use_mock_data=False)

    # Test location: New York City
    latitude = 40.7128
    longitude = -74.0060

    print(f"\nFetching weather for ({latitude}, {longitude})...")

    try:
        weather = await provider.get_current_weather(latitude, longitude)

        print(f"\nWeather Data:")
        print(f"  Timestamp: {weather.timestamp}")
        print(f"  Temperature: {weather.temperature_c:.1f}°C")
        print(f"  Humidity: {weather.humidity_percent:.1f}%")
        print(f"  Rain rate: {weather.precipitation_rate_mm_h:.2f} mm/h")
        print(f"  Cloud cover: {weather.cloud_cover_percent:.1f}%")
        print(f"  Pressure: {weather.pressure_hpa:.1f} hPa")
        print(f"  Wind: {weather.wind_speed_m_s:.1f} m/s @ {weather.wind_direction_deg:.0f}°")
        print(f"  Visibility: {weather.visibility_m:.0f} m")
        print(f"  Description: {weather.weather_description}")

        # Convert to ITU-R parameters
        itur_params = provider.convert_to_itur_parameters(weather)

        print(f"\nITU-R Parameters:")
        print(f"  Rain rate: {itur_params['rain_rate_mm_h']:.2f} mm/h")
        print(f"  Cloud liquid water: {itur_params['cloud_liquid_water_kg_m3']:.6f} kg/m³")
        print(f"  Water vapor density: {itur_params['water_vapor_density_g_m3']:.2f} g/m³")

    except Exception as e:
        print(f"Error: {e}")
        print("Testing with mock data instead...")

        provider = WeatherDataProvider(use_mock_data=True)
        weather = await provider.get_current_weather(latitude, longitude)

        print(f"\nMock Weather Data:")
        print(f"  Temperature: {weather.temperature_c:.1f}°C")
        print(f"  Humidity: {weather.humidity_percent:.1f}%")
        print(f"  Rain rate: {weather.precipitation_rate_mm_h:.2f} mm/h")

    finally:
        await provider.close()

    print("\nWeather API test completed!")


if __name__ == '__main__':
    asyncio.run(main())
