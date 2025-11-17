#!/usr/bin/env python3
"""
Starlink Constellation Demo with Real SGP4 Data
==============================================

Impressive demonstration of SGP4 orbit propagation with real Starlink constellation.

Features:
- Real-time Starlink satellite tracking
- 24-hour visibility prediction
- Handover event detection
- Doppler shift timeline
- Sky map visualization
- Performance metrics

Author: SGP4 Orbit Propagation Specialist
Date: 2025-11-17
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import List, Dict
import time

from orbit_propagation import TLEManager, SGP4Propagator, ConstellationSimulator


class StarlinkDemo:
    """
    Starlink Constellation Demonstration

    Demonstrates real SGP4 orbit propagation with Starlink constellation
    """

    def __init__(
        self,
        observer_lat: float = 25.0330,
        observer_lon: float = 121.5654,
        observer_name: str = "Taipei, Taiwan",
        max_satellites: int = 200
    ):
        """
        Initialize demo

        Parameters
        ----------
        observer_lat : float
            Observer latitude [degrees]
        observer_lon : float
            Observer longitude [degrees]
        observer_name : str
            Observer location name
        max_satellites : int
            Maximum number of satellites to load
        """
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.observer_name = observer_name
        self.max_satellites = max_satellites

        print("="*70)
        print("Starlink Constellation Demo - SGP4 Orbit Propagation")
        print("="*70)
        print(f"\nObserver Location: {observer_name}")
        print(f"Coordinates: {observer_lat:.4f}°N, {observer_lon:.4f}°E")
        print(f"Max Satellites: {max_satellites}")

        # Load constellation
        print("\nLoading Starlink constellation...")
        self.constellation = ConstellationSimulator(
            'starlink',
            max_satellites=max_satellites,
            auto_load=True
        )

        print(f"Loaded {self.constellation.satellite_count} satellites")

    def demo_current_visibility(self, min_elevation: float = 10.0) -> List[Dict]:
        """
        Demo 1: Current satellite visibility

        Parameters
        ----------
        min_elevation : float
            Minimum elevation threshold [degrees]

        Returns
        -------
        List[Dict]
            Visible satellites
        """
        print("\n" + "="*70)
        print("Demo 1: Current Satellite Visibility")
        print("="*70)

        timestamp = datetime.utcnow()
        print(f"\nTime: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Min Elevation: {min_elevation}°")

        # Find visible satellites
        start_time = time.time()
        visible = self.constellation.find_visible_satellites(
            self.observer_lat,
            self.observer_lon,
            timestamp,
            min_elevation=min_elevation,
            parallel=True
        )
        elapsed = time.time() - start_time

        print(f"\nVisible Satellites: {len(visible)}")
        print(f"Computation Time: {elapsed*1000:.2f} ms")

        if visible:
            print(f"\nTop 10 Satellites by Elevation:")
            print(f"{'Rank':<6} {'Satellite ID':<20} {'Elev (°)':<10} {'Azim (°)':<10} {'Range (km)':<12} {'Doppler (kHz)':<15}")
            print("-"*70)

            for i, sat in enumerate(visible[:10]):
                print(f"{i+1:<6} {sat['satellite_id']:<20} "
                      f"{sat['elevation_deg']:<10.2f} "
                      f"{sat['azimuth_deg']:<10.2f} "
                      f"{sat['slant_range_km']:<12.2f} "
                      f"{sat['doppler_shift_hz']/1000:<15.2f}")

            # Best satellite
            best = self.constellation.select_best_satellite(visible)
            print(f"\nBest Satellite: {best['satellite_id']}")
            print(f"  Elevation: {best['elevation_deg']:.2f}°")
            print(f"  Azimuth: {best['azimuth_deg']:.2f}°")
            print(f"  Slant Range: {best['slant_range_km']:.2f} km")
            print(f"  Doppler Shift: {best['doppler_shift_hz']/1000:.2f} kHz")

        return visible

    def demo_24hour_visibility(
        self,
        min_elevation: float = 10.0,
        time_step_minutes: int = 10
    ) -> Dict:
        """
        Demo 2: 24-hour visibility prediction

        Parameters
        ----------
        min_elevation : float
            Minimum elevation threshold [degrees]
        time_step_minutes : int
            Time step for prediction [minutes]

        Returns
        -------
        dict
            Visibility timeline data
        """
        print("\n" + "="*70)
        print("Demo 2: 24-Hour Visibility Prediction")
        print("="*70)

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=24)

        print(f"\nTime Range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')} UTC")
        print(f"Time Step: {time_step_minutes} minutes")

        # Simulate 24 hours
        timestamps = []
        num_visible = []
        max_elevations = []
        avg_dopplers = []

        current_time = start_time
        step = 0
        total_steps = int(24 * 60 / time_step_minutes)

        print(f"\nSimulating {total_steps} time steps...")

        while current_time <= end_time:
            visible = self.constellation.find_visible_satellites(
                self.observer_lat,
                self.observer_lon,
                current_time,
                min_elevation=min_elevation,
                parallel=True
            )

            timestamps.append(current_time)
            num_visible.append(len(visible))

            if visible:
                max_elevations.append(visible[0]['elevation_deg'])
                avg_doppler = np.mean([abs(s['doppler_shift_hz']) for s in visible])
                avg_dopplers.append(avg_doppler / 1000)  # kHz
            else:
                max_elevations.append(0)
                avg_dopplers.append(0)

            current_time += timedelta(minutes=time_step_minutes)
            step += 1

            if step % 10 == 0:
                print(f"  Progress: {step}/{total_steps} steps ({step*100//total_steps}%)")

        # Statistics
        print("\n" + "="*70)
        print("24-Hour Statistics")
        print("="*70)
        print(f"Average visible satellites: {np.mean(num_visible):.1f}")
        print(f"Maximum visible satellites: {np.max(num_visible)}")
        print(f"Minimum visible satellites: {np.min(num_visible)}")
        print(f"Coverage time: {sum(1 for n in num_visible if n > 0) * time_step_minutes / 60:.1f} hours ({sum(1 for n in num_visible if n > 0) * 100 / len(num_visible):.1f}%)")

        return {
            'timestamps': timestamps,
            'num_visible': num_visible,
            'max_elevations': max_elevations,
            'avg_dopplers': avg_dopplers
        }

    def demo_handover_prediction(
        self,
        duration_minutes: int = 120,
        time_step_sec: int = 30
    ) -> List[Dict]:
        """
        Demo 3: Handover event prediction

        Parameters
        ----------
        duration_minutes : int
            Prediction duration [minutes]
        time_step_sec : int
            Time step for prediction [seconds]

        Returns
        -------
        List[Dict]
            Handover events
        """
        print("\n" + "="*70)
        print("Demo 3: Handover Event Prediction")
        print("="*70)

        timestamp = datetime.utcnow()
        print(f"\nPredicting handovers for {duration_minutes} minutes")
        print(f"Time step: {time_step_sec} seconds")

        start_time = time.time()
        handovers = self.constellation.predict_handovers(
            self.observer_lat,
            self.observer_lon,
            timestamp,
            duration_minutes=duration_minutes,
            time_step_sec=time_step_sec,
            min_elevation=10.0
        )
        elapsed = time.time() - start_time

        print(f"\nHandover Events: {len(handovers)}")
        print(f"Computation Time: {elapsed:.2f} seconds")

        if handovers:
            print(f"\nHandover Timeline:")
            print(f"{'Time (UTC)':<20} {'From Satellite':<25} {'To Satellite':<25} {'Reason':<25}")
            print("-"*95)

            for ho in handovers[:20]:  # Show first 20
                time_str = ho['time'].strftime('%H:%M:%S')
                from_sat = ho.get('from_satellite', 'None')[:24] if ho.get('from_satellite') else 'None'
                to_sat = ho.get('to_satellite', 'None')[:24] if ho.get('to_satellite') else 'None'
                reason = ho['reason'][:24]

                print(f"{time_str:<20} {from_sat:<25} {to_sat:<25} {reason:<25}")

            if len(handovers) > 20:
                print(f"... and {len(handovers) - 20} more handovers")

        return handovers

    def demo_doppler_timeline(
        self,
        satellite_id: str = None,
        duration_minutes: int = 60,
        time_step_sec: int = 10
    ) -> Dict:
        """
        Demo 4: Doppler shift timeline for specific satellite

        Parameters
        ----------
        satellite_id : str, optional
            Satellite ID (None = use first visible)
        duration_minutes : int
            Timeline duration [minutes]
        time_step_sec : int
            Time step [seconds]

        Returns
        -------
        dict
            Doppler timeline data
        """
        print("\n" + "="*70)
        print("Demo 4: Doppler Shift Timeline")
        print("="*70)

        # Find satellite to track
        if satellite_id is None:
            timestamp = datetime.utcnow()
            visible = self.constellation.find_visible_satellites(
                self.observer_lat,
                self.observer_lon,
                timestamp,
                min_elevation=10.0
            )

            if not visible:
                print("No satellites visible. Cannot generate Doppler timeline.")
                return {}

            # Use best visible satellite
            best = visible[0]
            satellite_id = best['satellite_id']

        print(f"\nTracking: {satellite_id}")
        print(f"Duration: {duration_minutes} minutes")

        # Find satellite propagator
        sat_propagator = None
        for sat in self.constellation.satellites:
            if sat.satellite_id == satellite_id:
                sat_propagator = sat
                break

        if sat_propagator is None:
            print(f"Satellite {satellite_id} not found in constellation")
            return {}

        # Generate timeline
        timestamps = []
        elevations = []
        dopplers = []

        start_time = datetime.utcnow()
        current_time = start_time

        for _ in range(int(duration_minutes * 60 / time_step_sec)):
            try:
                geometry = sat_propagator.get_ground_track(
                    self.observer_lat,
                    self.observer_lon,
                    0.0,
                    current_time,
                    carrier_freq_hz=2.0e9
                )

                timestamps.append((current_time - start_time).total_seconds() / 60)
                elevations.append(geometry['elevation_deg'])
                dopplers.append(geometry['doppler_shift_hz'] / 1000)  # kHz

            except Exception:
                pass

            current_time += timedelta(seconds=time_step_sec)

        print(f"\nDoppler Statistics:")
        if dopplers:
            print(f"  Max Doppler: {max(dopplers):.2f} kHz")
            print(f"  Min Doppler: {min(dopplers):.2f} kHz")
            print(f"  Doppler Range: {max(dopplers) - min(dopplers):.2f} kHz")

        return {
            'timestamps': timestamps,
            'elevations': elevations,
            'dopplers': dopplers,
            'satellite_id': satellite_id
        }

    def plot_results(
        self,
        visibility_24h: Dict,
        doppler_timeline: Dict,
        save_path: str = 'starlink_demo_results.png'
    ):
        """
        Generate visualization plots

        Parameters
        ----------
        visibility_24h : dict
            24-hour visibility data
        doppler_timeline : dict
            Doppler timeline data
        save_path : str
            Path to save figure
        """
        print("\n" + "="*70)
        print("Generating Visualizations")
        print("="*70)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Plot 1: 24-hour visibility
        if visibility_24h:
            ax = axes[0, 0]
            hours = [(t - visibility_24h['timestamps'][0]).total_seconds() / 3600
                    for t in visibility_24h['timestamps']]
            ax.plot(hours, visibility_24h['num_visible'], 'b-', linewidth=2)
            ax.set_xlabel('Time (hours)', fontsize=12)
            ax.set_ylabel('Number of Visible Satellites', fontsize=12)
            ax.set_title('24-Hour Satellite Visibility', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 24)

        # Plot 2: Maximum elevation over 24 hours
        if visibility_24h:
            ax = axes[0, 1]
            ax.plot(hours, visibility_24h['max_elevations'], 'g-', linewidth=2)
            ax.set_xlabel('Time (hours)', fontsize=12)
            ax.set_ylabel('Maximum Elevation (degrees)', fontsize=12)
            ax.set_title('Maximum Satellite Elevation', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 24)

        # Plot 3: Doppler shift timeline
        if doppler_timeline and doppler_timeline.get('dopplers'):
            ax = axes[1, 0]
            ax.plot(doppler_timeline['timestamps'], doppler_timeline['dopplers'], 'r-', linewidth=2)
            ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
            ax.set_xlabel('Time (minutes)', fontsize=12)
            ax.set_ylabel('Doppler Shift (kHz)', fontsize=12)
            ax.set_title(f'Doppler Shift Timeline\n{doppler_timeline["satellite_id"]}',
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)

        # Plot 4: Elevation vs Doppler
        if doppler_timeline and doppler_timeline.get('dopplers'):
            ax = axes[1, 1]
            sc = ax.scatter(doppler_timeline['elevations'], doppler_timeline['dopplers'],
                           c=doppler_timeline['timestamps'], cmap='viridis', s=20)
            ax.set_xlabel('Elevation (degrees)', fontsize=12)
            ax.set_ylabel('Doppler Shift (kHz)', fontsize=12)
            ax.set_title('Elevation vs Doppler Shift', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            plt.colorbar(sc, ax=ax, label='Time (minutes)')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\nVisualization saved: {save_path}")

        return fig


def main():
    """Run complete Starlink demonstration"""

    # Configuration
    OBSERVER_LAT = 25.0330
    OBSERVER_LON = 121.5654
    OBSERVER_NAME = "Taipei, Taiwan"
    MAX_SATELLITES = 200

    # Create demo
    demo = StarlinkDemo(
        observer_lat=OBSERVER_LAT,
        observer_lon=OBSERVER_LON,
        observer_name=OBSERVER_NAME,
        max_satellites=MAX_SATELLITES
    )

    # Run demonstrations
    visible = demo.demo_current_visibility(min_elevation=10.0)

    visibility_24h = demo.demo_24hour_visibility(
        min_elevation=10.0,
        time_step_minutes=10
    )

    handovers = demo.demo_handover_prediction(
        duration_minutes=120,
        time_step_sec=30
    )

    doppler_timeline = demo.demo_doppler_timeline(
        duration_minutes=60,
        time_step_sec=10
    )

    # Generate visualizations
    try:
        demo.plot_results(
            visibility_24h,
            doppler_timeline,
            save_path='demo_results/starlink_sgp4_demo.png'
        )
    except Exception as e:
        print(f"\nWarning: Could not generate plots: {e}")

    # Final summary
    print("\n" + "="*70)
    print("Starlink Demo Complete!")
    print("="*70)
    print(f"\nKey Results:")
    print(f"  Total satellites loaded: {demo.constellation.satellite_count}")
    print(f"  Currently visible: {len(visible)}")
    print(f"  24h avg visible: {np.mean(visibility_24h['num_visible']):.1f}")
    print(f"  Handover events (2h): {len(handovers)}")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
