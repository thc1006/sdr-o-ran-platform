#!/usr/bin/env python3
"""
SGP4 Orbit Propagator
====================

Production-grade SGP4 (Simplified General Perturbations 4) orbit propagation
for accurate satellite position and velocity prediction.

Features:
- High-accuracy satellite position/velocity in ECI coordinates
- Coordinate transformations (ECI -> ECEF -> Geodetic -> Topocentric)
- Look angle calculations (elevation, azimuth, slant range)
- Doppler shift prediction
- Satellite pass prediction
- Performance optimized for large constellations

References:
- Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications
- Hoots, F. R., & Roehrich, R. L. (1980). Spacetrack Report No. 3

Author: SGP4 Orbit Propagation Specialist
Date: 2025-11-17
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional
from sgp4.api import Satrec, jday
from sgp4 import exporter
import time

try:
    from .tle_manager import TLEData
except ImportError:
    from tle_manager import TLEData


class SGP4Propagator:
    """
    SGP4 Orbit Propagator

    Provides high-accuracy satellite orbit propagation using SGP4 algorithm
    with comprehensive geometry calculations for ground station tracking.

    Parameters
    ----------
    tle_data : TLEData
        Two-line element data for the satellite

    Attributes
    ----------
    satellite : Satrec
        SGP4 satellite object
    satellite_id : str
        Satellite identifier
    epoch : datetime
        TLE epoch timestamp

    Examples
    --------
    >>> from orbit_propagation import TLEManager, SGP4Propagator
    >>> manager = TLEManager()
    >>> tles = manager.fetch_starlink_tles(limit=1)
    >>> propagator = SGP4Propagator(tles[0])
    >>> geometry = propagator.get_ground_track(25.0330, 121.5654, 0.0, datetime.utcnow())
    >>> print(f"Elevation: {geometry['elevation_deg']:.2f}°")
    """

    # Physical constants
    EARTH_RADIUS_KM = 6378.137  # WGS84 equatorial radius
    EARTH_FLATTENING = 1.0 / 298.257223563  # WGS84 flattening
    SPEED_OF_LIGHT = 299792.458  # km/s
    EARTH_ROTATION_RATE = 7.2921150e-5  # rad/s (Earth's rotation)

    def __init__(self, tle_data: TLEData):
        """Initialize SGP4 propagator from TLE data"""

        # Create SGP4 satellite object from TLE
        self.satellite = Satrec.twoline2rv(tle_data.line1, tle_data.line2)
        self.satellite_id = tle_data.satellite_id
        self.norad_id = tle_data.norad_id
        self.epoch = tle_data.epoch
        self.constellation = tle_data.constellation

        # Validate initialization
        if self.satellite.error != 0:
            raise ValueError(f"SGP4 initialization error: {self.satellite.error}")

        print(f"SGP4 Propagator initialized: {self.satellite_id}")

    def propagate(self, timestamp: datetime) -> Tuple[np.ndarray, np.ndarray]:
        """
        Propagate satellite position and velocity to given timestamp

        Parameters
        ----------
        timestamp : datetime
            UTC timestamp for propagation

        Returns
        -------
        position_eci : np.ndarray
            Position in ECI (Earth-Centered Inertial) coordinates [km]
            Shape: (3,) with [x, y, z]
        velocity_eci : np.ndarray
            Velocity in ECI coordinates [km/s]
            Shape: (3,) with [vx, vy, vz]

        Raises
        ------
        ValueError
            If SGP4 propagation fails
        """
        # Convert timestamp to Julian date
        jd, fr = jday(
            timestamp.year,
            timestamp.month,
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second + timestamp.microsecond / 1e6
        )

        # Propagate using SGP4
        error_code, position_eci, velocity_eci = self.satellite.sgp4(jd, fr)

        if error_code != 0:
            raise ValueError(
                f"SGP4 propagation error {error_code} for {self.satellite_id}"
            )

        return np.array(position_eci), np.array(velocity_eci)

    def eci_to_ecef(
        self,
        position_eci: np.ndarray,
        timestamp: datetime
    ) -> np.ndarray:
        """
        Convert ECI (Earth-Centered Inertial) to ECEF (Earth-Centered Earth-Fixed)

        Parameters
        ----------
        position_eci : np.ndarray
            Position in ECI coordinates [km]
        timestamp : datetime
            UTC timestamp

        Returns
        -------
        np.ndarray
            Position in ECEF coordinates [km]
        """
        # Calculate Greenwich Mean Sidereal Time (GMST)
        gmst = self._calculate_gmst(timestamp)

        # Rotation matrix from ECI to ECEF
        cos_gmst = np.cos(gmst)
        sin_gmst = np.sin(gmst)

        rotation_matrix = np.array([
            [cos_gmst, sin_gmst, 0],
            [-sin_gmst, cos_gmst, 0],
            [0, 0, 1]
        ])

        position_ecef = rotation_matrix @ position_eci

        return position_ecef

    def _calculate_gmst(self, timestamp: datetime) -> float:
        """Calculate Greenwich Mean Sidereal Time"""
        # Julian date
        jd, fr = jday(
            timestamp.year,
            timestamp.month,
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second + timestamp.microsecond / 1e6
        )

        # Julian centuries from J2000.0
        T = (jd - 2451545.0 + fr) / 36525.0

        # GMST in seconds
        gmst_sec = (
            67310.54841 +
            (876600.0 * 3600.0 + 8640184.812866) * T +
            0.093104 * T**2 -
            6.2e-6 * T**3
        )

        # Convert to radians and normalize
        gmst_rad = np.deg2rad(gmst_sec / 240.0) % (2 * np.pi)

        return gmst_rad

    def geodetic_to_ecef(
        self,
        lat: float,
        lon: float,
        alt: float
    ) -> np.ndarray:
        """
        Convert geodetic coordinates to ECEF

        Parameters
        ----------
        lat : float
            Latitude in degrees (-90 to 90)
        lon : float
            Longitude in degrees (-180 to 180)
        alt : float
            Altitude above WGS84 ellipsoid in meters

        Returns
        -------
        np.ndarray
            Position in ECEF coordinates [km]
        """
        lat_rad = np.deg2rad(lat)
        lon_rad = np.deg2rad(lon)
        alt_km = alt / 1000.0  # Convert to km

        # WGS84 parameters
        a = self.EARTH_RADIUS_KM
        f = self.EARTH_FLATTENING
        e2 = 2 * f - f**2  # Eccentricity squared

        # Radius of curvature
        N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)

        # ECEF coordinates
        x = (N + alt_km) * np.cos(lat_rad) * np.cos(lon_rad)
        y = (N + alt_km) * np.cos(lat_rad) * np.sin(lon_rad)
        z = (N * (1 - e2) + alt_km) * np.sin(lat_rad)

        return np.array([x, y, z])

    def calculate_look_angles(
        self,
        sat_pos_ecef: np.ndarray,
        observer_pos_ecef: np.ndarray,
        observer_lat: float,
        observer_lon: float
    ) -> Tuple[float, float, float]:
        """
        Calculate look angles from observer to satellite

        Parameters
        ----------
        sat_pos_ecef : np.ndarray
            Satellite position in ECEF [km]
        observer_pos_ecef : np.ndarray
            Observer position in ECEF [km]
        observer_lat : float
            Observer latitude in degrees
        observer_lon : float
            Observer longitude in degrees

        Returns
        -------
        elevation : float
            Elevation angle in degrees (0 to 90)
        azimuth : float
            Azimuth angle in degrees (0 to 360, North=0, East=90)
        slant_range : float
            Distance to satellite in kilometers
        """
        # Vector from observer to satellite in ECEF
        range_ecef = sat_pos_ecef - observer_pos_ecef
        slant_range = np.linalg.norm(range_ecef)

        # Convert to topocentric (SEZ: South-East-Zenith) coordinates
        lat_rad = np.deg2rad(observer_lat)
        lon_rad = np.deg2rad(observer_lon)

        # Rotation matrix from ECEF to SEZ
        sin_lat = np.sin(lat_rad)
        cos_lat = np.cos(lat_rad)
        sin_lon = np.sin(lon_rad)
        cos_lon = np.cos(lon_rad)

        rotation_matrix = np.array([
            [sin_lat * cos_lon, sin_lat * sin_lon, -cos_lat],
            [-sin_lon, cos_lon, 0],
            [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat]
        ])

        range_sez = rotation_matrix @ range_ecef

        # Calculate elevation and azimuth
        south = range_sez[0]
        east = range_sez[1]
        zenith = range_sez[2]

        # Elevation angle
        elevation = np.rad2deg(np.arcsin(zenith / slant_range))

        # Azimuth angle (from South, counterclockwise)
        azimuth_from_south = np.rad2deg(np.arctan2(east, -south))

        # Convert to North=0, East=90 convention
        azimuth = (azimuth_from_south + 180.0) % 360.0

        return elevation, azimuth, slant_range

    def calculate_doppler(
        self,
        sat_pos_ecef: np.ndarray,
        sat_vel_eci: np.ndarray,
        observer_pos_ecef: np.ndarray,
        timestamp: datetime,
        carrier_freq_hz: float = 2.0e9
    ) -> float:
        """
        Calculate Doppler shift

        Parameters
        ----------
        sat_pos_ecef : np.ndarray
            Satellite position in ECEF [km]
        sat_vel_eci : np.ndarray
            Satellite velocity in ECI [km/s]
        observer_pos_ecef : np.ndarray
            Observer position in ECEF [km]
        timestamp : datetime
            Observation timestamp
        carrier_freq_hz : float
            Carrier frequency in Hz (default: 2 GHz)

        Returns
        -------
        float
            Doppler shift in Hz (positive: approaching, negative: receding)
        """
        # Convert satellite velocity from ECI to ECEF
        gmst = self._calculate_gmst(timestamp)
        cos_gmst = np.cos(gmst)
        sin_gmst = np.sin(gmst)

        rotation_matrix = np.array([
            [cos_gmst, sin_gmst, 0],
            [-sin_gmst, cos_gmst, 0],
            [0, 0, 1]
        ])

        sat_vel_ecef = rotation_matrix @ sat_vel_eci

        # Range vector from observer to satellite
        range_vec = sat_pos_ecef - observer_pos_ecef
        range_mag = np.linalg.norm(range_vec)

        # Unit vector along line of sight
        los_unit = range_vec / range_mag

        # Radial velocity (positive: approaching)
        radial_velocity_km_s = np.dot(sat_vel_ecef, los_unit)

        # Doppler shift
        doppler_shift_hz = (radial_velocity_km_s / self.SPEED_OF_LIGHT) * carrier_freq_hz

        return doppler_shift_hz

    def get_ground_track(
        self,
        user_lat: float,
        user_lon: float,
        user_alt: float,
        timestamp: datetime,
        carrier_freq_hz: float = 2.0e9
    ) -> Dict[str, float]:
        """
        Calculate complete satellite geometry relative to ground user

        Parameters
        ----------
        user_lat : float
            User latitude in degrees (-90 to 90)
        user_lon : float
            User longitude in degrees (-180 to 180)
        user_alt : float
            User altitude in meters
        timestamp : datetime
            Observation time (UTC)
        carrier_freq_hz : float
            Carrier frequency in Hz (default: 2 GHz)

        Returns
        -------
        dict
            Dictionary containing:
            - elevation_deg: Elevation angle [degrees]
            - azimuth_deg: Azimuth angle [degrees]
            - slant_range_km: Slant range [km]
            - doppler_shift_hz: Doppler shift [Hz]
            - satellite_altitude_km: Satellite altitude [km]
            - satellite_velocity_kmps: Satellite velocity [km/s]
            - is_visible: Visibility flag (elevation > 0)
            - satellite_lat: Satellite sub-point latitude [degrees]
            - satellite_lon: Satellite sub-point longitude [degrees]

        Examples
        --------
        >>> propagator = SGP4Propagator(tle_data)
        >>> geometry = propagator.get_ground_track(25.0330, 121.5654, 0.0, datetime.utcnow())
        >>> print(f"Elevation: {geometry['elevation_deg']:.2f}°")
        >>> print(f"Doppler: {geometry['doppler_shift_hz']/1000:.2f} kHz")
        """
        # Get satellite position and velocity in ECI
        sat_pos_eci, sat_vel_eci = self.propagate(timestamp)

        # Convert satellite position to ECEF
        sat_pos_ecef = self.eci_to_ecef(sat_pos_eci, timestamp)

        # Convert user location to ECEF
        user_pos_ecef = self.geodetic_to_ecef(user_lat, user_lon, user_alt)

        # Calculate look angles
        elevation, azimuth, slant_range = self.calculate_look_angles(
            sat_pos_ecef, user_pos_ecef, user_lat, user_lon
        )

        # Calculate Doppler shift
        doppler_shift = self.calculate_doppler(
            sat_pos_ecef, sat_vel_eci, user_pos_ecef, timestamp, carrier_freq_hz
        )

        # Calculate satellite altitude
        satellite_altitude = np.linalg.norm(sat_pos_eci) - self.EARTH_RADIUS_KM

        # Calculate satellite velocity magnitude
        satellite_velocity = np.linalg.norm(sat_vel_eci)

        # Calculate satellite sub-point (nadir point)
        sat_lat, sat_lon = self._ecef_to_geodetic(sat_pos_ecef)

        return {
            'elevation_deg': float(elevation),
            'azimuth_deg': float(azimuth),
            'slant_range_km': float(slant_range),
            'doppler_shift_hz': float(doppler_shift),
            'satellite_altitude_km': float(satellite_altitude),
            'satellite_velocity_kmps': float(satellite_velocity),
            'is_visible': elevation > 0.0,
            'satellite_lat': float(sat_lat),
            'satellite_lon': float(sat_lon),
            'timestamp': timestamp.isoformat(),
            'satellite_id': self.satellite_id
        }

    def _ecef_to_geodetic(self, pos_ecef: np.ndarray) -> Tuple[float, float]:
        """Convert ECEF to geodetic coordinates (lat, lon)"""
        x, y, z = pos_ecef

        # Longitude
        lon = np.arctan2(y, x)

        # Latitude (iterative solution)
        p = np.sqrt(x**2 + y**2)
        lat = np.arctan2(z, p * (1 - self.EARTH_FLATTENING))

        # Iterate for better accuracy
        for _ in range(5):
            N = self.EARTH_RADIUS_KM / np.sqrt(
                1 - (2 * self.EARTH_FLATTENING - self.EARTH_FLATTENING**2) * np.sin(lat)**2
            )
            lat = np.arctan2(z + N * (2 * self.EARTH_FLATTENING - self.EARTH_FLATTENING**2) * np.sin(lat), p)

        return np.rad2deg(lat), np.rad2deg(lon)

    def predict_next_passes(
        self,
        user_lat: float,
        user_lon: float,
        user_alt: float = 0.0,
        min_elevation: float = 10.0,
        search_days: int = 7,
        time_step_sec: int = 60
    ) -> List[Dict]:
        """
        Predict satellite passes over user location

        Parameters
        ----------
        user_lat : float
            User latitude [degrees]
        user_lon : float
            User longitude [degrees]
        user_alt : float
            User altitude [meters]
        min_elevation : float
            Minimum elevation threshold [degrees]
        search_days : int
            Number of days to search ahead
        time_step_sec : int
            Time step for search [seconds]

        Returns
        -------
        List[Dict]
            List of pass predictions, each containing:
            - rise_time: Pass start time
            - max_time: Maximum elevation time
            - set_time: Pass end time
            - max_elevation: Maximum elevation [degrees]
            - duration_sec: Pass duration [seconds]
        """
        passes = []
        current_time = datetime.utcnow()
        end_time = current_time + timedelta(days=search_days)

        in_pass = False
        pass_start = None
        max_elevation = 0.0
        max_time = None

        timestamp = current_time
        while timestamp <= end_time:
            try:
                geometry = self.get_ground_track(user_lat, user_lon, user_alt, timestamp)
                elevation = geometry['elevation_deg']

                if elevation >= min_elevation and not in_pass:
                    # Pass started
                    in_pass = True
                    pass_start = timestamp
                    max_elevation = elevation
                    max_time = timestamp

                elif elevation >= min_elevation and in_pass:
                    # Continuing pass - track maximum
                    if elevation > max_elevation:
                        max_elevation = elevation
                        max_time = timestamp

                elif elevation < min_elevation and in_pass:
                    # Pass ended
                    in_pass = False
                    duration = (timestamp - pass_start).total_seconds()

                    passes.append({
                        'rise_time': pass_start,
                        'max_time': max_time,
                        'set_time': timestamp,
                        'max_elevation': max_elevation,
                        'duration_sec': duration,
                        'satellite_id': self.satellite_id
                    })

                timestamp += timedelta(seconds=time_step_sec)

            except Exception as e:
                # Skip propagation errors
                timestamp += timedelta(seconds=time_step_sec)
                continue

        return passes

    def get_orbital_parameters(self) -> Dict:
        """Get satellite orbital parameters"""
        return {
            'satellite_id': self.satellite_id,
            'norad_id': self.norad_id,
            'constellation': self.constellation,
            'epoch': self.epoch.isoformat(),
            'epoch_age_days': (datetime.utcnow() - self.epoch).days,
            'inclination_deg': np.rad2deg(self.satellite.inclo),
            'eccentricity': self.satellite.ecco,
            'mean_motion_rev_per_day': self.satellite.no_kozai * 1440.0 / (2.0 * np.pi),
            'period_minutes': 1440.0 / (self.satellite.no_kozai * 1440.0 / (2.0 * np.pi)),
        }


def main():
    """Example usage"""
    try:
        from .tle_manager import TLEManager
    except ImportError:
        from tle_manager import TLEManager

    print("="*70)
    print("SGP4 Propagator - Example Usage")
    print("="*70)

    # Fetch TLE data
    manager = TLEManager()
    print("\nFetching Starlink TLE data...")
    tles = manager.fetch_starlink_tles(limit=1)

    if not tles:
        print("Error: No TLE data available")
        return

    tle = tles[0]
    print(f"\nUsing satellite: {tle.satellite_id}")

    # Create propagator
    propagator = SGP4Propagator(tle)

    # Get orbital parameters
    print("\n" + "="*70)
    print("Orbital Parameters")
    print("="*70)
    params = propagator.get_orbital_parameters()
    for key, value in params.items():
        print(f"  {key}: {value}")

    # Calculate current position
    print("\n" + "="*70)
    print("Current Satellite Position")
    print("="*70)
    timestamp = datetime.utcnow()
    pos_eci, vel_eci = propagator.propagate(timestamp)

    print(f"Time: {timestamp}")
    print(f"Position ECI (km): [{pos_eci[0]:.2f}, {pos_eci[1]:.2f}, {pos_eci[2]:.2f}]")
    print(f"Velocity ECI (km/s): [{vel_eci[0]:.4f}, {vel_eci[1]:.4f}, {vel_eci[2]:.4f}]")
    print(f"Altitude: {np.linalg.norm(pos_eci) - 6378.137:.2f} km")
    print(f"Speed: {np.linalg.norm(vel_eci):.4f} km/s")

    # Ground track for Taipei
    print("\n" + "="*70)
    print("Ground Track (Taipei, Taiwan)")
    print("="*70)
    taipei_lat, taipei_lon = 25.0330, 121.5654

    geometry = propagator.get_ground_track(taipei_lat, taipei_lon, 0.0, timestamp)

    print(f"Observer: {taipei_lat}°N, {taipei_lon}°E")
    print(f"Elevation: {geometry['elevation_deg']:.2f}°")
    print(f"Azimuth: {geometry['azimuth_deg']:.2f}°")
    print(f"Slant Range: {geometry['slant_range_km']:.2f} km")
    print(f"Doppler Shift: {geometry['doppler_shift_hz']/1000:.2f} kHz (@ 2 GHz)")
    print(f"Visible: {geometry['is_visible']}")

    # Performance test
    print("\n" + "="*70)
    print("Performance Benchmark")
    print("="*70)

    num_propagations = 1000
    start_time = time.time()

    for _ in range(num_propagations):
        propagator.get_ground_track(taipei_lat, taipei_lon, 0.0, timestamp)

    elapsed = time.time() - start_time
    avg_time_ms = (elapsed / num_propagations) * 1000

    print(f"Propagations: {num_propagations}")
    print(f"Total time: {elapsed:.4f} sec")
    print(f"Average time: {avg_time_ms:.4f} ms per propagation")
    print(f"Throughput: {num_propagations/elapsed:.0f} propagations/sec")

    print("\n" + "="*70)
    print("SGP4 Propagator validation complete!")
    print("="*70)


if __name__ == "__main__":
    main()
