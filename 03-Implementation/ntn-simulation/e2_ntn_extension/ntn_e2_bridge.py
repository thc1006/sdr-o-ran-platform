"""
NTN-E2 Bridge Module
Bridges OpenNTN channel models with E2 Interface for NTN metrics reporting

This module integrates the OpenNTN 3GPP TR38.811 channel models (LEO/MEO/GEO)
with the E2SM-NTN service model to provide seamless NTN metrics to the RIC.
"""

import sys
import os
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path for package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openNTN_integration.leo_channel import LEOChannelModel
from openNTN_integration.meo_channel import MEOChannelModel
from openNTN_integration.geo_channel import GEOChannelModel
from e2_ntn_extension.e2sm_ntn import (
    E2SM_NTN, OrbitType, NTNEventTrigger, NTNControlAction,
    SatelliteMetrics, ChannelQuality
)

# Import SGP4 orbit propagation modules
try:
    from orbit_propagation import TLEManager, TLEData, SGP4Propagator
    SGP4_AVAILABLE = True
except ImportError:
    SGP4_AVAILABLE = False
    print("Warning: SGP4 orbit propagation not available. Using simplified model.")

# Import real-time weather integration
try:
    from weather.realtime_attenuation import RealtimeAttenuationCalculator
    WEATHER_AVAILABLE = True
except ImportError:
    WEATHER_AVAILABLE = False
    print("Warning: Real-time weather integration not available. Using simplified attenuation model.")


@dataclass
class UEContext:
    """User Equipment context for NTN"""
    ue_id: str
    position_lat: float
    position_lon: float
    altitude_m: float
    current_satellite_id: Optional[str] = None
    last_measurement_time: float = 0.0
    handover_count: int = 0


class NTN_E2_Bridge:
    """
    Bridge between OpenNTN channel models and E2 Interface

    This class:
    1. Manages OpenNTN channel model instances (LEO/MEO/GEO)
    2. Processes UE measurements and satellite states
    3. Generates E2 Indication messages with NTN metrics
    4. Executes E2 Control actions on the channel model
    5. Provides satellite visibility and handover predictions
    """

    def __init__(
        self,
        orbit_type: str = 'LEO',
        carrier_frequency_ghz: float = 2.1,
        simulation_time_step: float = 0.1,  # seconds
        use_sgp4: bool = True,
        tle_data: Optional[TLEData] = None,
        constellation_name: Optional[str] = None,
        use_realtime_weather: bool = True,
        weather_api_key: Optional[str] = None,
        weather_provider: str = 'openmeteo'
    ):
        """
        Initialize NTN-E2 Bridge

        Args:
            orbit_type: Satellite orbit type ('LEO', 'MEO', or 'GEO')
            carrier_frequency_ghz: Carrier frequency in GHz
            simulation_time_step: Simulation time step in seconds
            use_sgp4: Use real SGP4 orbit propagation (default: True)
            tle_data: TLE data for SGP4 propagation (optional)
            constellation_name: Constellation name for automatic TLE fetch (optional)
            use_realtime_weather: Use real-time weather data for attenuation (default: True)
            weather_api_key: API key for weather service (optional)
            weather_provider: Weather provider ('openmeteo', 'openweathermap')
        """
        self.orbit_type = orbit_type.upper()
        self.carrier_frequency_ghz = carrier_frequency_ghz
        self.simulation_time_step = simulation_time_step
        self.use_sgp4 = use_sgp4 and SGP4_AVAILABLE
        self.use_realtime_weather = use_realtime_weather and WEATHER_AVAILABLE

        # Initialize SGP4 propagator if requested and available
        self.sgp4_propagator = None
        if self.use_sgp4:
            if tle_data:
                self.sgp4_propagator = SGP4Propagator(tle_data)
                self.satellite_id = tle_data.satellite_id
                print(f"Using SGP4 propagation with satellite: {self.satellite_id}")
            elif constellation_name:
                # Fetch TLE data automatically
                tle_manager = TLEManager()
                tles = tle_manager.fetch_constellation_tles(constellation_name, limit=1)
                if tles:
                    self.sgp4_propagator = SGP4Propagator(tles[0])
                    self.satellite_id = tles[0].satellite_id
                    print(f"Using SGP4 propagation with satellite: {self.satellite_id}")
                else:
                    print(f"Warning: No TLE data found for {constellation_name}, using simplified model")
                    self.use_sgp4 = False

        # Initialize channel model based on orbit type (for legacy compatibility)
        if self.orbit_type == 'LEO':
            self.channel_model = LEOChannelModel()
            self.satellite_altitude_km = 600.0
            self.satellite_velocity_km_s = 7.5
        elif self.orbit_type == 'MEO':
            self.channel_model = MEOChannelModel()
            self.satellite_altitude_km = 10000.0
            self.satellite_velocity_km_s = 4.0
        elif self.orbit_type == 'GEO':
            self.channel_model = GEOChannelModel()
            self.satellite_altitude_km = 35786.0
            self.satellite_velocity_km_s = 0.0  # Geostationary
        else:
            raise ValueError(f"Invalid orbit type: {orbit_type}")

        # Initialize E2SM-NTN service model
        self.e2sm_ntn = E2SM_NTN(channel_model=self.channel_model)

        # Initialize real-time weather calculator if requested
        self.weather_calc = None
        if self.use_realtime_weather:
            try:
                self.weather_calc = RealtimeAttenuationCalculator(
                    weather_api_key=weather_api_key,
                    weather_provider=weather_provider,
                    use_mock_weather=False,
                    cache_duration_sec=300.0  # 5 minutes cache
                )
                print(f"  Real-time weather integration: ENABLED ({weather_provider})")
            except Exception as e:
                print(f"  Warning: Failed to initialize weather calculator: {e}")
                self.use_realtime_weather = False

        # UE contexts
        self.ue_contexts: Dict[str, UEContext] = {}

        # Satellite state
        self.current_time = 0.0
        if not self.sgp4_propagator:
            self.satellite_id = f"SAT-{self.orbit_type}-001"

        print(f"NTN-E2 Bridge initialized: {self.orbit_type} @ {carrier_frequency_ghz} GHz")
        print(f"  SGP4 propagation: {'ENABLED' if self.use_sgp4 else 'DISABLED'}")
        print(f"  Real-time weather: {'ENABLED' if self.use_realtime_weather else 'DISABLED'}")

    def register_ue(
        self,
        ue_id: str,
        lat: float,
        lon: float,
        altitude_m: float = 0.0
    ) -> None:
        """
        Register a UE for NTN tracking

        Args:
            ue_id: UE identifier
            lat: Latitude in degrees
            lon: Longitude in degrees
            altitude_m: Altitude in meters
        """
        context = UEContext(
            ue_id=ue_id,
            position_lat=lat,
            position_lon=lon,
            altitude_m=altitude_m,
            current_satellite_id=self.satellite_id,
            last_measurement_time=self.current_time
        )
        self.ue_contexts[ue_id] = context
        print(f"Registered UE {ue_id} at ({lat:.2f}, {lon:.2f})")

    def calculate_satellite_geometry(
        self,
        ue_lat: float,
        ue_lon: float,
        ue_alt: float = 0.0,
        timestamp: Optional[datetime] = None,
        satellite_lat: float = 0.0,
        satellite_lon: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate satellite geometry (elevation, azimuth, slant range)

        Args:
            ue_lat: UE latitude (degrees)
            ue_lon: UE longitude (degrees)
            ue_alt: UE altitude (meters)
            timestamp: Observation timestamp (UTC, None = now)
            satellite_lat: Satellite sub-point latitude (degrees) - for simplified model
            satellite_lon: Satellite sub-point longitude (degrees) - for simplified model

        Returns:
            Dictionary with elevation_angle, azimuth_angle, slant_range_km, doppler_shift_hz, etc.
        """
        # Use SGP4 if available
        if self.use_sgp4 and self.sgp4_propagator:
            if timestamp is None:
                timestamp = datetime.utcnow()

            try:
                geometry = self.sgp4_propagator.get_ground_track(
                    ue_lat, ue_lon, ue_alt, timestamp,
                    carrier_freq_hz=self.carrier_frequency_ghz * 1e9
                )

                return {
                    "elevation_angle": geometry['elevation_deg'],
                    "azimuth_angle": geometry['azimuth_deg'],
                    "slant_range_km": geometry['slant_range_km'],
                    "doppler_shift_hz": geometry['doppler_shift_hz'],
                    "satellite_altitude_km": geometry['satellite_altitude_km'],
                    "satellite_velocity_kmps": geometry['satellite_velocity_kmps'],
                    "satellite_lat": geometry['satellite_lat'],
                    "satellite_lon": geometry['satellite_lon']
                }
            except Exception as e:
                print(f"Warning: SGP4 propagation failed: {e}. Falling back to simplified model.")
                # Fall through to simplified model

        # Simplified model (legacy)
        # Convert to radians
        ue_lat_rad = np.radians(ue_lat)
        ue_lon_rad = np.radians(ue_lon)
        sat_lat_rad = np.radians(satellite_lat)
        sat_lon_rad = np.radians(satellite_lon)

        # Calculate central angle using haversine
        dlat = sat_lat_rad - ue_lat_rad
        dlon = sat_lon_rad - ue_lon_rad
        a = np.sin(dlat/2)**2 + np.cos(ue_lat_rad) * np.cos(sat_lat_rad) * np.sin(dlon/2)**2
        central_angle = 2 * np.arcsin(np.sqrt(a))

        # Earth radius
        earth_radius = 6371.0  # km

        # Calculate slant range using law of cosines
        slant_range = np.sqrt(
            earth_radius**2 +
            (earth_radius + self.satellite_altitude_km)**2 -
            2 * earth_radius * (earth_radius + self.satellite_altitude_km) * np.cos(central_angle)
        )

        # Calculate elevation angle
        sin_elevation = (
            (earth_radius + self.satellite_altitude_km) * np.sin(central_angle)
        ) / slant_range
        elevation_angle = np.degrees(np.arcsin(np.clip(sin_elevation, -1, 1)))

        # Calculate azimuth angle (simplified - assumes satellite is north of UE)
        azimuth_angle = np.degrees(np.arctan2(
            np.sin(dlon) * np.cos(sat_lat_rad),
            np.cos(ue_lat_rad) * np.sin(sat_lat_rad) -
            np.sin(ue_lat_rad) * np.cos(sat_lat_rad) * np.cos(dlon)
        ))

        # Normalize azimuth to 0-360
        azimuth_angle = (azimuth_angle + 360) % 360

        return {
            "elevation_angle": float(elevation_angle),
            "azimuth_angle": float(azimuth_angle),
            "slant_range_km": float(slant_range),
            "satellite_altitude_km": self.satellite_altitude_km,
            "satellite_velocity_kmps": self.satellite_velocity_km_s
        }

    def calculate_angular_velocity(
        self,
        slant_range_km: float,
        satellite_velocity_km_s: float,
        elevation_angle: float
    ) -> float:
        """
        Calculate angular velocity as seen from UE

        Args:
            slant_range_km: Slant range to satellite
            satellite_velocity_km_s: Satellite velocity
            elevation_angle: Elevation angle (degrees)

        Returns:
            Angular velocity in deg/s
        """
        # Tangential component of velocity
        elevation_rad = np.radians(elevation_angle)
        v_tangential = satellite_velocity_km_s * np.cos(elevation_rad)

        # Angular velocity = v_tangential / slant_range (converted to deg/s)
        angular_velocity_rad_s = v_tangential / slant_range_km
        angular_velocity_deg_s = np.degrees(angular_velocity_rad_s)

        # For descending pass, angular velocity is negative
        # Assume satellite is descending if elevation is decreasing
        # For simplicity, return negative value for LEO (always moving)
        if self.orbit_type == 'LEO':
            return -abs(float(angular_velocity_deg_s))
        else:
            return 0.0  # GEO is stationary

    def process_ue_report(
        self,
        ue_id: str,
        measurements: Dict[str, float],
        timestamp: Optional[datetime] = None,
        satellite_lat: float = 0.0,
        satellite_lon: float = 0.0
    ) -> Tuple[bytes, bytes]:
        """
        Process UE measurements and generate E2 Indication

        Args:
            ue_id: UE identifier
            measurements: UE measurement report (RSRP, SINR, etc.)
            timestamp: Observation timestamp (UTC, None = now)
            satellite_lat: Satellite sub-point latitude (for simplified model)
            satellite_lon: Satellite sub-point longitude (for simplified model)

        Returns:
            Tuple of (indication_header, indication_message)
        """
        if ue_id not in self.ue_contexts:
            raise ValueError(f"UE {ue_id} not registered")

        ue_context = self.ue_contexts[ue_id]

        if timestamp is None:
            timestamp = datetime.utcnow()

        # Calculate satellite geometry
        geometry = self.calculate_satellite_geometry(
            ue_context.position_lat,
            ue_context.position_lon,
            ue_context.altitude_m,
            timestamp,
            satellite_lat,
            satellite_lon
        )

        # Calculate angular velocity
        sat_velocity = geometry.get("satellite_velocity_kmps", self.satellite_velocity_km_s)
        angular_velocity = self.calculate_angular_velocity(
            geometry["slant_range_km"],
            sat_velocity,
            geometry["elevation_angle"]
        )

        # Build satellite state
        satellite_state = {
            "satellite_id": self.satellite_id,
            "orbit_type": self.orbit_type,
            "beam_id": 1,
            "elevation_angle": geometry["elevation_angle"],
            "azimuth_angle": geometry["azimuth_angle"],
            "slant_range_km": geometry["slant_range_km"],
            "satellite_velocity": sat_velocity,
            "satellite_altitude_km": geometry.get("satellite_altitude_km", self.satellite_altitude_km),
            "angular_velocity": angular_velocity,
            "carrier_frequency_ghz": self.carrier_frequency_ghz,
            "doppler_shift_hz": geometry.get("doppler_shift_hz", 0.0),
            "doppler_rate": -45.0,  # Simplified
            "next_satellite_id": f"SAT-{self.orbit_type}-002",
            "next_satellite_elevation": 5.0
        }

        # Generate E2 Indication message
        header, message = self.e2sm_ntn.create_indication_message(
            ue_id=ue_id,
            satellite_state=satellite_state,
            ue_measurements=measurements,
            report_style=1
        )

        # Update UE context
        ue_context.last_measurement_time = self.current_time

        return header, message

    def execute_control_action(
        self,
        action_type: str,
        ue_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute E2 control action

        Args:
            action_type: Type of control action
            ue_id: Target UE identifier
            parameters: Action-specific parameters

        Returns:
            Action execution result
        """
        if ue_id not in self.ue_contexts:
            return {"success": False, "reason": f"UE {ue_id} not registered"}

        result = {"success": False, "action": action_type, "ue_id": ue_id}

        if action_type == "POWER_CONTROL":
            # Execute power control
            target_power = parameters.get("target_tx_power_dbm", 23.0)
            result["success"] = True
            result["new_power_dbm"] = target_power
            result["message"] = f"Power adjusted to {target_power} dBm"

        elif action_type == "TRIGGER_HANDOVER":
            # Execute handover
            target_satellite = parameters.get("target_satellite_id", "UNKNOWN")
            ue_context = self.ue_contexts[ue_id]
            ue_context.current_satellite_id = target_satellite
            ue_context.handover_count += 1
            result["success"] = True
            result["new_satellite_id"] = target_satellite
            result["handover_count"] = ue_context.handover_count
            result["message"] = f"Handover to {target_satellite} completed"

        elif action_type == "DOPPLER_COMPENSATION":
            # Execute Doppler compensation
            freq_offset = parameters.get("frequency_offset_hz", 0.0)
            result["success"] = True
            result["compensation_hz"] = freq_offset
            result["message"] = f"Doppler compensation set to {freq_offset} Hz"

        elif action_type == "LINK_ADAPTATION":
            # Execute link adaptation
            target_mcs = parameters.get("target_mcs", 16)
            result["success"] = True
            result["new_mcs"] = target_mcs
            result["message"] = f"MCS adjusted to {target_mcs}"

        else:
            result["message"] = f"Unknown action type: {action_type}"

        return result

    def simulate_step(
        self,
        delta_time: Optional[float] = None
    ) -> None:
        """
        Advance simulation by one time step

        Args:
            delta_time: Time step in seconds (uses default if None)
        """
        if delta_time is None:
            delta_time = self.simulation_time_step

        self.current_time += delta_time

    def get_ue_context(self, ue_id: str) -> Optional[UEContext]:
        """Get UE context by ID"""
        return self.ue_contexts.get(ue_id)

    def get_visible_satellites(
        self,
        ue_id: str,
        min_elevation: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Get list of visible satellites for a UE

        Args:
            ue_id: UE identifier
            min_elevation: Minimum elevation threshold (degrees)

        Returns:
            List of visible satellites with their geometry
        """
        if ue_id not in self.ue_contexts:
            return []

        ue_context = self.ue_contexts[ue_id]

        # For simplicity, return current satellite if visible
        geometry = self.calculate_satellite_geometry(
            ue_context.position_lat,
            ue_context.position_lon,
            satellite_lat=0.0,
            satellite_lon=0.0
        )

        visible = []
        if geometry["elevation_angle"] >= min_elevation:
            visible.append({
                "satellite_id": self.satellite_id,
                "elevation_angle": geometry["elevation_angle"],
                "azimuth_angle": geometry["azimuth_angle"],
                "slant_range_km": geometry["slant_range_km"]
            })

        return visible

    def predict_next_handover(
        self,
        ue_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Predict next handover event for a UE

        Args:
            ue_id: UE identifier

        Returns:
            Handover prediction or None if no handover needed
        """
        if ue_id not in self.ue_contexts:
            return None

        ue_context = self.ue_contexts[ue_id]

        # Get current geometry
        geometry = self.calculate_satellite_geometry(
            ue_context.position_lat,
            ue_context.position_lon
        )

        # Calculate angular velocity
        angular_velocity = self.calculate_angular_velocity(
            geometry["slant_range_km"],
            self.satellite_velocity_km_s,
            geometry["elevation_angle"]
        )

        # Predict handover using E2SM-NTN
        handover_pred = self.e2sm_ntn.predict_handover_time(
            current_elevation=geometry["elevation_angle"],
            satellite_velocity=self.satellite_velocity_km_s,
            angular_velocity=angular_velocity
        )

        if handover_pred["time_to_handover_sec"] < 300.0:  # Within 5 minutes
            return {
                "ue_id": ue_id,
                "current_satellite": self.satellite_id,
                "next_satellite": f"SAT-{self.orbit_type}-002",
                "time_to_handover_sec": handover_pred["time_to_handover_sec"],
                "handover_probability": handover_pred["handover_probability"],
                "current_elevation": geometry["elevation_angle"]
            }

        return None

    async def calculate_link_budget(
        self,
        ue_id: str,
        timestamp: Optional[datetime] = None,
        include_weather: bool = True
    ) -> Dict[str, float]:
        """
        Calculate complete link budget including real-time weather

        Args:
            ue_id: UE identifier
            timestamp: Calculation timestamp (None = now)
            include_weather: Include real-time weather attenuation

        Returns:
            Dictionary with complete link budget
        """
        if ue_id not in self.ue_contexts:
            raise ValueError(f"UE {ue_id} not registered")

        ue_context = self.ue_contexts[ue_id]

        if timestamp is None:
            timestamp = datetime.utcnow()

        # Calculate satellite geometry
        geometry = self.calculate_satellite_geometry(
            ue_context.position_lat,
            ue_context.position_lon,
            ue_context.altitude_m,
            timestamp
        )

        # Free space path loss (Friis equation)
        freq_hz = self.carrier_frequency_ghz * 1e9
        distance_m = geometry["slant_range_km"] * 1000.0
        wavelength_m = 3e8 / freq_hz
        fspl_db = 20 * np.log10(4 * np.pi * distance_m / wavelength_m)

        # Calculate weather-related attenuation
        weather_loss_db = 0.0
        rain_attenuation = 0.0
        cloud_attenuation = 0.0
        gas_attenuation = 0.0
        weather_data = None

        if include_weather and self.use_realtime_weather and self.weather_calc:
            try:
                # Get real-time weather attenuation
                attenuation_result = await self.weather_calc.calculate_current_attenuation(
                    ue_context.position_lat,
                    ue_context.position_lon,
                    self.carrier_frequency_ghz,
                    geometry["elevation_angle"],
                    polarization='circular'
                )

                rain_attenuation = attenuation_result.rain_attenuation_db
                cloud_attenuation = attenuation_result.cloud_attenuation_db
                gas_attenuation = attenuation_result.gas_attenuation_db
                weather_loss_db = attenuation_result.total_atmospheric_loss_db

                weather_data = {
                    'rain_rate_mm_h': attenuation_result.current_rain_rate_mm_h,
                    'temperature_c': attenuation_result.temperature_c,
                    'humidity_percent': attenuation_result.humidity_percent,
                    'is_rain_fade': attenuation_result.is_rain_fade_event,
                    'fade_margin_db': attenuation_result.fade_margin_db
                }
            except Exception as e:
                print(f"Warning: Failed to calculate weather attenuation: {e}")
                # Use simplified model as fallback
                weather_loss_db = 2.0  # Typical clear-sky loss

        # Total path loss
        total_path_loss_db = fspl_db + weather_loss_db

        # Typical link parameters
        tx_power_dbm = 30.0  # Satellite EIRP
        rx_antenna_gain_dbi = 15.0  # UE antenna gain
        noise_figure_db = 3.0
        bandwidth_mhz = 20.0

        # Thermal noise
        thermal_noise_dbm = -174 + 10 * np.log10(bandwidth_mhz * 1e6) + noise_figure_db

        # Received signal strength
        rx_power_dbm = tx_power_dbm + rx_antenna_gain_dbi - total_path_loss_db

        # SNR
        snr_db = rx_power_dbm - thermal_noise_dbm

        return {
            # Link geometry
            'slant_range_km': geometry['slant_range_km'],
            'elevation_angle_deg': geometry['elevation_angle'],
            'azimuth_angle_deg': geometry['azimuth_angle'],

            # Path loss components
            'free_space_path_loss_db': fspl_db,
            'rain_attenuation_db': rain_attenuation,
            'cloud_attenuation_db': cloud_attenuation,
            'atmospheric_gas_attenuation_db': gas_attenuation,
            'total_atmospheric_loss_db': weather_loss_db,
            'total_path_loss_db': total_path_loss_db,

            # Link budget
            'tx_power_dbm': tx_power_dbm,
            'rx_antenna_gain_dbi': rx_antenna_gain_dbi,
            'rx_power_dbm': rx_power_dbm,
            'thermal_noise_dbm': thermal_noise_dbm,
            'snr_db': snr_db,

            # Weather data (if available)
            'weather_data': weather_data
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get bridge statistics"""
        stats = {
            "orbit_type": self.orbit_type,
            "carrier_frequency_ghz": self.carrier_frequency_ghz,
            "satellite_altitude_km": self.satellite_altitude_km,
            "registered_ues": len(self.ue_contexts),
            "current_time": self.current_time,
            "total_handovers": sum(
                ue.handover_count for ue in self.ue_contexts.values()
            ),
            "sgp4_enabled": self.use_sgp4,
            "weather_enabled": self.use_realtime_weather
        }

        # Add weather performance stats if available
        if self.use_realtime_weather and self.weather_calc:
            stats["weather_performance"] = self.weather_calc.get_performance_stats()

        return stats
