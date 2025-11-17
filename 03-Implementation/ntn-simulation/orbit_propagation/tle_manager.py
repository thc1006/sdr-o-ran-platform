#!/usr/bin/env python3
"""
TLE Data Manager for Satellite Constellations
=============================================

Manages Two-Line Element (TLE) data for various satellite constellations
including Starlink, OneWeb, Iridium NEXT, and custom LEO satellites.

Features:
- Automatic TLE fetching from CelesTrak
- Local caching with expiration
- Support for multiple constellations
- TLE validation and parsing
- Age tracking for propagation accuracy

Author: SGP4 Orbit Propagation Specialist
Date: 2025-11-17
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import re


@dataclass
class TLEData:
    """Two-Line Element data for a satellite"""
    satellite_id: str           # Satellite identifier (e.g., "STARLINK-1007")
    norad_id: int              # NORAD catalog number
    line0: str                 # Name line (line 0)
    line1: str                 # TLE line 1
    line2: str                 # TLE line 2
    epoch: datetime            # TLE epoch timestamp
    constellation: str         # Constellation name (e.g., "starlink")
    fetch_time: datetime       # When TLE was fetched

    def is_fresh(self, max_age_days: float = 7.0) -> bool:
        """Check if TLE is fresh enough for accurate propagation"""
        age = (datetime.utcnow() - self.epoch).total_seconds() / 86400.0
        return age < max_age_days

    def get_age_days(self) -> float:
        """Get TLE age in days"""
        return (datetime.utcnow() - self.epoch).total_seconds() / 86400.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['epoch'] = self.epoch.isoformat()
        data['fetch_time'] = self.fetch_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'TLEData':
        """Create from dictionary"""
        data['epoch'] = datetime.fromisoformat(data['epoch'])
        data['fetch_time'] = datetime.fromisoformat(data['fetch_time'])
        return cls(**data)


class TLEManager:
    """
    TLE Data Manager for Satellite Constellations

    Handles fetching, parsing, caching, and managing TLE data from CelesTrak
    and other sources.

    Parameters
    ----------
    cache_dir : str
        Directory for TLE cache storage (default: 'tle_cache')
    cache_expiry_hours : float
        Cache expiration time in hours (default: 24.0)
    auto_refresh : bool
        Automatically refresh stale cache (default: True)

    Examples
    --------
    >>> manager = TLEManager()
    >>> tles = manager.fetch_starlink_tles(limit=100)
    >>> print(f"Fetched {len(tles)} Starlink satellites")
    >>> manager.cache_tles('starlink', tles)
    """

    # CelesTrak URLs for constellation TLE data
    TLE_SOURCES = {
        'starlink': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',
        'oneweb': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle',
        'iridium-next': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=tle',
        'galileo': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle',
        'gps-ops': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle',
        'glonass-ops': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=glonass-ops&FORMAT=tle',
        'beidou': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=beidou&FORMAT=tle',
    }

    def __init__(
        self,
        cache_dir: str = 'tle_cache',
        cache_expiry_hours: float = 24.0,
        auto_refresh: bool = True
    ):
        """Initialize TLE Manager"""
        self.cache_dir = cache_dir
        self.cache_expiry_hours = cache_expiry_hours
        self.auto_refresh = auto_refresh
        self.tle_database: Dict[str, List[TLEData]] = {}

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

        print(f"TLE Manager initialized:")
        print(f"  Cache directory: {self.cache_dir}")
        print(f"  Cache expiry: {self.cache_expiry_hours} hours")
        print(f"  Auto refresh: {self.auto_refresh}")

    def fetch_constellation_tles(
        self,
        constellation: str,
        limit: Optional[int] = None,
        force_refresh: bool = False
    ) -> List[TLEData]:
        """
        Fetch TLE data for a constellation

        Parameters
        ----------
        constellation : str
            Constellation name ('starlink', 'oneweb', 'iridium-next', etc.)
        limit : int, optional
            Limit number of satellites to fetch
        force_refresh : bool
            Force refresh even if cache is valid

        Returns
        -------
        List[TLEData]
            List of TLE data for constellation satellites
        """
        constellation = constellation.lower()

        # Check cache first
        if not force_refresh:
            cached = self.load_cached_tles(constellation)
            if cached and self._is_cache_valid(constellation):
                print(f"Using cached TLEs for {constellation} ({len(cached)} satellites)")
                if limit:
                    return cached[:limit]
                return cached

        # Fetch from network
        print(f"Fetching TLEs for {constellation} from CelesTrak...")

        if constellation not in self.TLE_SOURCES:
            raise ValueError(
                f"Unknown constellation: {constellation}. "
                f"Available: {list(self.TLE_SOURCES.keys())}"
            )

        url = self.TLE_SOURCES[constellation]

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            tle_text = response.text

            # Parse TLE data
            tles = self._parse_tle_text(tle_text, constellation)

            print(f"Successfully fetched {len(tles)} satellites for {constellation}")

            # Cache the results
            self.cache_tles(constellation, tles)

            if limit:
                return tles[:limit]
            return tles

        except requests.RequestException as e:
            print(f"Error fetching TLEs: {e}")
            # Try cache as fallback
            cached = self.load_cached_tles(constellation)
            if cached:
                print(f"Using cached TLEs as fallback ({len(cached)} satellites)")
                if limit:
                    return cached[:limit]
                return cached
            raise

    def fetch_starlink_tles(self, limit: Optional[int] = None) -> List[TLEData]:
        """Fetch Starlink constellation TLE data"""
        return self.fetch_constellation_tles('starlink', limit=limit)

    def fetch_oneweb_tles(self, limit: Optional[int] = None) -> List[TLEData]:
        """Fetch OneWeb constellation TLE data"""
        return self.fetch_constellation_tles('oneweb', limit=limit)

    def fetch_iridium_tles(self, limit: Optional[int] = None) -> List[TLEData]:
        """Fetch Iridium NEXT constellation TLE data"""
        return self.fetch_constellation_tles('iridium-next', limit=limit)

    def parse_tle_from_lines(
        self,
        line0: str,
        line1: str,
        line2: str,
        constellation: str = 'custom'
    ) -> TLEData:
        """
        Parse TLE from three lines

        Parameters
        ----------
        line0 : str
            Satellite name line
        line1 : str
            TLE line 1
        line2 : str
            TLE line 2
        constellation : str
            Constellation name

        Returns
        -------
        TLEData
            Parsed TLE data
        """
        # Extract satellite name
        satellite_id = line0.strip()

        # Extract NORAD ID from line 1
        norad_id = int(line1[2:7].strip())

        # Parse epoch from line 1
        # Format: YYDdd.dddddddd (year and day of year)
        epoch_str = line1[18:32].strip()
        year_prefix = int(epoch_str[0:2])
        year = 2000 + year_prefix if year_prefix < 57 else 1900 + year_prefix
        day_of_year = float(epoch_str[2:])

        epoch = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)

        return TLEData(
            satellite_id=satellite_id,
            norad_id=norad_id,
            line0=line0.strip(),
            line1=line1.strip(),
            line2=line2.strip(),
            epoch=epoch,
            constellation=constellation,
            fetch_time=datetime.utcnow()
        )

    def _parse_tle_text(self, text: str, constellation: str) -> List[TLEData]:
        """Parse TLE text into TLEData objects"""
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]

        tles = []
        i = 0
        while i < len(lines) - 2:
            line0 = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]

            # Validate TLE format
            if line1.startswith('1 ') and line2.startswith('2 '):
                try:
                    tle = self.parse_tle_from_lines(line0, line1, line2, constellation)
                    tles.append(tle)
                except Exception as e:
                    print(f"Warning: Failed to parse TLE for {line0}: {e}")

            i += 3

        return tles

    def cache_tles(self, constellation: str, tles: List[TLEData]) -> None:
        """
        Cache TLE data locally

        Parameters
        ----------
        constellation : str
            Constellation name
        tles : List[TLEData]
            TLE data to cache
        """
        cache_file = os.path.join(self.cache_dir, f"{constellation}.json")

        # Convert to serializable format
        data = {
            'constellation': constellation,
            'fetch_time': datetime.utcnow().isoformat(),
            'count': len(tles),
            'tles': [tle.to_dict() for tle in tles]
        }

        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Cached {len(tles)} TLEs for {constellation}")

    def load_cached_tles(self, constellation: str) -> Optional[List[TLEData]]:
        """
        Load cached TLE data

        Parameters
        ----------
        constellation : str
            Constellation name

        Returns
        -------
        Optional[List[TLEData]]
            Cached TLE data or None if not found
        """
        cache_file = os.path.join(self.cache_dir, f"{constellation}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            tles = [TLEData.from_dict(tle_dict) for tle_dict in data['tles']]
            return tles

        except Exception as e:
            print(f"Error loading cache for {constellation}: {e}")
            return None

    def _is_cache_valid(self, constellation: str) -> bool:
        """Check if cache is still valid"""
        cache_file = os.path.join(self.cache_dir, f"{constellation}.json")

        if not os.path.exists(cache_file):
            return False

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            fetch_time = datetime.fromisoformat(data['fetch_time'])
            age_hours = (datetime.utcnow() - fetch_time).total_seconds() / 3600.0

            return age_hours < self.cache_expiry_hours

        except Exception:
            return False

    def get_tle_by_id(
        self,
        constellation: str,
        satellite_id: str
    ) -> Optional[TLEData]:
        """
        Get TLE for specific satellite by ID

        Parameters
        ----------
        constellation : str
            Constellation name
        satellite_id : str
            Satellite identifier (name or NORAD ID)

        Returns
        -------
        Optional[TLEData]
            TLE data or None if not found
        """
        tles = self.fetch_constellation_tles(constellation)

        # Try exact match first
        for tle in tles:
            if tle.satellite_id == satellite_id:
                return tle
            if str(tle.norad_id) == str(satellite_id):
                return tle

        # Try partial match
        for tle in tles:
            if satellite_id.lower() in tle.satellite_id.lower():
                return tle

        return None

    def get_fresh_tles(
        self,
        constellation: str,
        max_age_days: float = 7.0
    ) -> List[TLEData]:
        """
        Get only fresh TLEs (within age threshold)

        Parameters
        ----------
        constellation : str
            Constellation name
        max_age_days : float
            Maximum TLE age in days

        Returns
        -------
        List[TLEData]
            Fresh TLE data
        """
        tles = self.fetch_constellation_tles(constellation)
        fresh = [tle for tle in tles if tle.is_fresh(max_age_days)]

        print(f"Fresh TLEs: {len(fresh)}/{len(tles)} within {max_age_days} days")

        return fresh

    def get_statistics(self, constellation: str) -> Dict:
        """Get statistics for constellation TLEs"""
        tles = self.load_cached_tles(constellation)

        if not tles:
            return {'constellation': constellation, 'count': 0}

        ages = [tle.get_age_days() for tle in tles]

        return {
            'constellation': constellation,
            'count': len(tles),
            'avg_age_days': sum(ages) / len(ages),
            'min_age_days': min(ages),
            'max_age_days': max(ages),
            'fresh_count_7d': sum(1 for age in ages if age < 7.0),
            'fresh_count_30d': sum(1 for age in ages if age < 30.0),
        }

    def clear_cache(self, constellation: Optional[str] = None) -> None:
        """Clear TLE cache"""
        if constellation:
            cache_file = os.path.join(self.cache_dir, f"{constellation}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print(f"Cleared cache for {constellation}")
        else:
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))
            print("Cleared all cache")


def main():
    """Example usage"""
    print("="*70)
    print("TLE Manager - Example Usage")
    print("="*70)

    # Create TLE manager
    manager = TLEManager(cache_dir='tle_cache')

    # Fetch Starlink TLEs
    print("\n" + "="*70)
    print("Fetching Starlink TLEs")
    print("="*70)
    starlink_tles = manager.fetch_starlink_tles(limit=10)

    print(f"\nFetched {len(starlink_tles)} Starlink satellites:")
    for i, tle in enumerate(starlink_tles[:5]):
        print(f"\n{i+1}. {tle.satellite_id}")
        print(f"   NORAD ID: {tle.norad_id}")
        print(f"   Epoch: {tle.epoch}")
        print(f"   Age: {tle.get_age_days():.2f} days")
        print(f"   Fresh: {tle.is_fresh()}")

    # Get statistics
    print("\n" + "="*70)
    print("Starlink TLE Statistics")
    print("="*70)
    stats = manager.get_statistics('starlink')
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Try other constellations
    print("\n" + "="*70)
    print("Other Constellations")
    print("="*70)

    for constellation in ['oneweb', 'iridium-next']:
        try:
            tles = manager.fetch_constellation_tles(constellation, limit=5)
            print(f"\n{constellation.upper()}: {len(tles)} satellites fetched")
            if tles:
                print(f"  Example: {tles[0].satellite_id}")
        except Exception as e:
            print(f"\n{constellation.upper()}: Error - {e}")

    print("\n" + "="*70)
    print("TLE Manager validation complete!")
    print("="*70)


if __name__ == "__main__":
    main()
