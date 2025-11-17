#!/usr/bin/env python3
"""
End-to-End NTN-O-RAN Integration Demo
Complete LEO satellite pass simulation with 5 UEs

This demo showcases:
1. OpenNTN channel models (LEO, 550 km altitude)
2. E2SM-NTN metrics reporting
3. NTN Handover Optimization xApp
4. NTN Power Control xApp
5. Complete satellite pass (10 minutes simulated time)
6. Multi-UE scenarios (low elevation, rain fade, handover, etc.)
7. Real-time event logging and visualization
"""

import sys
import os
import json
import time
import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'openNTN_integration'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'e2_ntn_extension'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'xapps'))

from leo_channel import LEOChannelModel
from e2sm_ntn import E2SM_NTN
from ntn_e2_bridge import NTN_E2_Bridge
from ntn_handover_xapp import NTNHandoverXApp
from ntn_power_control_xapp import NTNPowerControlXApp


class SatelliteOrbitSimulator:
    """Simulate LEO satellite orbital motion"""

    def __init__(self, altitude_km: float = 550.0, inclination_deg: float = 53.0):
        """
        Initialize satellite orbit simulator

        Args:
            altitude_km: Orbital altitude in km
            inclination_deg: Orbital inclination in degrees
        """
        self.altitude_km = altitude_km
        self.inclination_deg = inclination_deg

        # Calculate orbital parameters
        self.earth_radius_km = 6371.0
        self.orbital_radius_km = self.earth_radius_km + altitude_km

        # Orbital velocity (km/s)
        GM = 398600.4418  # Earth gravitational parameter (km^3/s^2)
        self.orbital_velocity_km_s = np.sqrt(GM / self.orbital_radius_km)

        # Orbital period (seconds)
        self.orbital_period_sec = 2 * np.pi * self.orbital_radius_km / self.orbital_velocity_km_s

        # Initial position (subsatellite point)
        self.current_latitude = 0.0
        self.current_longitude = 0.0
        self.simulation_time = 0.0

        print(f"Satellite Orbit Initialized:")
        print(f"  Altitude: {altitude_km} km")
        print(f"  Orbital velocity: {self.orbital_velocity_km_s:.2f} km/s")
        print(f"  Orbital period: {self.orbital_period_sec/60:.1f} minutes")

    def update_position(self, time_step_sec: float):
        """
        Update satellite position based on orbital mechanics

        Args:
            time_step_sec: Time step in seconds
        """
        self.simulation_time += time_step_sec

        # Angular velocity (rad/s)
        angular_velocity = 2 * np.pi / self.orbital_period_sec

        # Update longitude (satellite moves eastward)
        delta_lon = np.degrees(angular_velocity * time_step_sec)
        self.current_longitude += delta_lon

        # Wrap longitude to [-180, 180]
        if self.current_longitude > 180:
            self.current_longitude -= 360

        # Simple sinusoidal latitude variation for inclined orbit
        self.current_latitude = self.inclination_deg * np.sin(
            2 * np.pi * self.simulation_time / self.orbital_period_sec
        )

    def get_position(self) -> Tuple[float, float]:
        """
        Get current subsatellite point

        Returns:
            Tuple of (latitude, longitude) in degrees
        """
        return self.current_latitude, self.current_longitude


class UEScenario:
    """Define UE test scenario"""

    def __init__(
        self,
        ue_id: str,
        lat: float,
        lon: float,
        scenario_type: str,
        description: str
    ):
        self.ue_id = ue_id
        self.lat = lat
        self.lon = lon
        self.scenario_type = scenario_type
        self.description = description

        # Tracking
        self.measurements: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []


class NTNIntegrationDemo:
    """End-to-end NTN-O-RAN integration demonstration"""

    def __init__(self):
        """Initialize the demo"""
        print("="*80)
        print("NTN-O-RAN End-to-End Integration Demo")
        print("="*80)

        # Simulation parameters
        self.simulation_duration_sec = 600.0  # 10 minutes
        self.time_step_sec = 10.0  # 10 second steps
        self.current_time = 0.0

        # Initialize components
        print("\n[1/5] Initializing LEO channel model...")
        self.leo_channel = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550.0,
            scenario='urban',
            direction='downlink'
        )

        print("[2/5] Initializing NTN-E2 Bridge...")
        self.bridge = NTN_E2_Bridge(
            orbit_type='LEO',
            carrier_frequency_ghz=2.0,
            simulation_time_step=self.time_step_sec
        )

        print("[3/5] Initializing Satellite Orbit Simulator...")
        self.satellite_sim = SatelliteOrbitSimulator(
            altitude_km=550.0,
            inclination_deg=53.0
        )

        print("[4/5] Initializing NTN xApps...")
        self.handover_xapp = NTNHandoverXApp(config={
            'handover_threshold_sec': 30.0,
            'min_elevation_deg': 10.0,
            'subscription_period_ms': 10000
        })

        self.power_xapp = NTNPowerControlXApp(config={
            'target_margin_db': 10.0,
            'margin_tolerance_db': 3.0,
            'subscription_period_ms': 10000
        })

        print("[5/5] Creating UE scenarios...")
        self.ues = self._create_ue_scenarios()

        # Results storage
        self.demo_events: List[Dict[str, Any]] = []

        print("\nDemo initialization complete!\n")

    def _create_ue_scenarios(self) -> List[UEScenario]:
        """
        Create 5 UE test scenarios

        Returns:
            List of UE scenarios
        """
        scenarios = [
            UEScenario(
                ue_id="UE-001",
                lat=45.0,   # Minneapolis area
                lon=-93.0,
                scenario_type="LOW_ELEVATION",
                description="UE at low elevation (10°) → Power increase needed"
            ),
            UEScenario(
                ue_id="UE-002",
                lat=40.7,   # New York area
                lon=-74.0,
                scenario_type="OPTIMAL",
                description="UE at optimal elevation (60°) → No action"
            ),
            UEScenario(
                ue_id="UE-003",
                lat=37.7,   # San Francisco area
                lon=-122.4,
                scenario_type="HANDOVER",
                description="UE approaching handover threshold → Handover triggered"
            ),
            UEScenario(
                ue_id="UE-004",
                lat=51.5,   # London area
                lon=-0.1,
                scenario_type="RAIN_FADE",
                description="UE experiencing rain fade → Rain mitigation activated"
            ),
            UEScenario(
                ue_id="UE-005",
                lat=35.6,   # Tokyo area
                lon=139.7,
                scenario_type="EXCESSIVE_MARGIN",
                description="UE with excessive margin → Power reduction"
            )
        ]

        # Register UEs with bridge
        for ue in scenarios:
            self.bridge.register_ue(
                ue_id=ue.ue_id,
                lat=ue.lat,
                lon=ue.lon,
                altitude_m=300.0
            )
            print(f"  Created scenario: {ue.ue_id} - {ue.description}")

        return scenarios

    def calculate_elevation_angle(
        self,
        ue_lat: float,
        ue_lon: float,
        sat_lat: float,
        sat_lon: float
    ) -> float:
        """
        Calculate elevation angle from UE to satellite

        Args:
            ue_lat: UE latitude (degrees)
            ue_lon: UE longitude (degrees)
            sat_lat: Satellite latitude (degrees)
            sat_lon: Satellite longitude (degrees)

        Returns:
            Elevation angle in degrees
        """
        geometry = self.bridge.calculate_satellite_geometry(
            ue_lat=ue_lat,
            ue_lon=ue_lon,
            satellite_lat=sat_lat,
            satellite_lon=sat_lon
        )
        return geometry['elevation_angle']

    def generate_measurements(
        self,
        ue: UEScenario,
        elevation_angle: float,
        time_step: int
    ) -> Dict[str, float]:
        """
        Generate realistic measurements for UE based on scenario

        Args:
            ue: UE scenario
            elevation_angle: Current elevation angle
            time_step: Current time step number

        Returns:
            Dictionary of measurements
        """
        # Base measurements
        link_budget = self.leo_channel.calculate_link_budget(elevation_angle)
        path_loss = link_budget['free_space_path_loss_db']

        # Calculate RSRP (assume 46 dBm EIRP from satellite)
        rsrp = 46.0 - path_loss

        # Base SINR depends on elevation
        base_sinr = 5.0 + (elevation_angle / 90.0) * 15.0  # 5-20 dB range

        # Scenario-specific adjustments
        if ue.scenario_type == "LOW_ELEVATION":
            # Lower SINR at low elevation
            sinr = base_sinr * 0.7
            tx_power = 23.0  # Max power
        elif ue.scenario_type == "OPTIMAL":
            # Good conditions
            sinr = base_sinr * 1.2
            tx_power = 18.0  # Mid power
        elif ue.scenario_type == "HANDOVER":
            # Degrading over time
            sinr = base_sinr * (1.0 - time_step * 0.02)
            tx_power = 20.0
        elif ue.scenario_type == "RAIN_FADE":
            # Rain attenuation event at t=200-400 sec
            if 200 <= self.current_time <= 400:
                rain_atten = 6.0
                sinr = base_sinr - rain_atten
            else:
                rain_atten = 0.0
                sinr = base_sinr
            tx_power = 23.0 if rain_atten > 0 else 20.0
        else:  # EXCESSIVE_MARGIN
            # Very good conditions
            sinr = base_sinr * 1.5
            tx_power = 23.0  # Will be reduced

        # Calculate other metrics
        rsrq = -10.0 - (90.0 - elevation_angle) * 0.1
        bler = max(0.001, 0.1 * np.exp(-sinr / 5.0))

        # Rain attenuation
        rain_atten = 0.0
        if ue.scenario_type == "RAIN_FADE" and 200 <= self.current_time <= 400:
            rain_atten = 6.0

        measurements = {
            'rsrp': rsrp,
            'rsrq': rsrq,
            'sinr': sinr,
            'bler': bler,
            'tx_power_dbm': tx_power,
            'rain_attenuation_db': rain_atten,
            'atmospheric_loss_db': 0.5,
            'throughput_dl_mbps': max(5.0, sinr * 3.0),
            'throughput_ul_mbps': max(1.0, sinr * 0.5),
            'packet_loss_rate': min(0.1, bler * 1.5)
        }

        return measurements

    async def run_simulation(self):
        """Run the complete satellite pass simulation"""
        print("="*80)
        print("Starting Satellite Pass Simulation")
        print(f"Duration: {self.simulation_duration_sec/60:.1f} minutes")
        print(f"Time step: {self.time_step_sec} seconds")
        print("="*80 + "\n")

        # Start xApps
        await self.handover_xapp.start()
        await self.power_xapp.start()

        time_steps = int(self.simulation_duration_sec / self.time_step_sec)

        for step in range(time_steps):
            self.current_time = step * self.time_step_sec

            print(f"\n{'─'*80}")
            print(f"Time: {self.current_time:.0f}s ({self.current_time/60:.1f} min)")
            print(f"{'─'*80}")

            # Update satellite position
            self.satellite_sim.update_position(self.time_step_sec)
            sat_lat, sat_lon = self.satellite_sim.get_position()

            print(f"Satellite position: ({sat_lat:.2f}°, {sat_lon:.2f}°)")

            # Process each UE
            for ue in self.ues:
                # Calculate elevation
                elevation = self.calculate_elevation_angle(
                    ue.lat, ue.lon, sat_lat, sat_lon
                )

                # Generate measurements
                measurements = self.generate_measurements(ue, elevation, step)

                # Store measurement
                ue.measurements.append({
                    'time': self.current_time,
                    'elevation': elevation,
                    **measurements
                })

                # Generate E2 Indication
                header, message = self.bridge.process_ue_report(
                    ue_id=ue.ue_id,
                    measurements=measurements,
                    satellite_lat=sat_lat,
                    satellite_lon=sat_lon
                )

                # Send to xApps
                await self.handover_xapp.on_indication(header, message)
                await self.power_xapp.on_indication(header, message)

                # Log key events
                ntn_data = json.loads(message.decode('utf-8'))
                handover_pred = ntn_data['handover_prediction']

                if handover_pred['time_to_handover_sec'] < 30:
                    event = {
                        'time': self.current_time,
                        'ue_id': ue.ue_id,
                        'type': 'HANDOVER_IMMINENT',
                        'details': f"Time to handover: {handover_pred['time_to_handover_sec']:.1f}s"
                    }
                    ue.events.append(event)
                    self.demo_events.append(event)

                if measurements.get('rain_attenuation_db', 0) > 3.0:
                    event = {
                        'time': self.current_time,
                        'ue_id': ue.ue_id,
                        'type': 'RAIN_FADE',
                        'details': f"Rain attenuation: {measurements['rain_attenuation_db']:.1f} dB"
                    }
                    ue.events.append(event)
                    self.demo_events.append(event)

                print(f"  {ue.ue_id}: elev={elevation:5.1f}°, SINR={measurements['sinr']:5.1f}dB, " +
                      f"margin={ntn_data['link_budget']['link_margin_db']:5.1f}dB")

            # Small delay for async processing
            await asyncio.sleep(0.01)

        print(f"\n{'='*80}")
        print("Satellite Pass Simulation Complete")
        print(f"{'='*80}\n")

        # Stop xApps
        await self.handover_xapp.stop()
        await self.power_xapp.stop()

    def generate_plots(self, output_path: str):
        """
        Generate visualization plots

        Args:
            output_path: Path to save plots
        """
        print("Generating visualizations...")

        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

        # Plot 1: Elevation vs Time
        ax1 = fig.add_subplot(gs[0, 0])
        for ue in self.ues:
            times = [m['time']/60 for m in ue.measurements]  # Convert to minutes
            elevations = [m['elevation'] for m in ue.measurements]
            ax1.plot(times, elevations, marker='o', label=ue.ue_id, markersize=3)

        ax1.axhline(y=10, color='r', linestyle='--', linewidth=1, alpha=0.5, label='Min Elevation')
        ax1.set_xlabel('Time (minutes)')
        ax1.set_ylabel('Elevation Angle (degrees)')
        ax1.set_title('Satellite Elevation vs Time (All UEs)')
        ax1.legend(loc='best', fontsize=8)
        ax1.grid(True, alpha=0.3)

        # Plot 2: RSRP vs Time
        ax2 = fig.add_subplot(gs[0, 1])
        for ue in self.ues:
            times = [m['time']/60 for m in ue.measurements]
            rsrp = [m['rsrp'] for m in ue.measurements]
            ax2.plot(times, rsrp, marker='o', label=ue.ue_id, markersize=3)

        ax2.set_xlabel('Time (minutes)')
        ax2.set_ylabel('RSRP (dBm)')
        ax2.set_title('Received Signal Power vs Time')
        ax2.legend(loc='best', fontsize=8)
        ax2.grid(True, alpha=0.3)

        # Plot 3: TX Power vs Time
        ax3 = fig.add_subplot(gs[1, 0])
        for ue in self.ues:
            times = [m['time']/60 for m in ue.measurements]
            tx_power = [m['tx_power_dbm'] for m in ue.measurements]
            ax3.plot(times, tx_power, marker='o', label=ue.ue_id, markersize=3)

        ax3.set_xlabel('Time (minutes)')
        ax3.set_ylabel('TX Power (dBm)')
        ax3.set_title('Transmit Power Adjustments vs Time')
        ax3.legend(loc='best', fontsize=8)
        ax3.grid(True, alpha=0.3)

        # Plot 4: SINR vs Time
        ax4 = fig.add_subplot(gs[1, 1])
        for ue in self.ues:
            times = [m['time']/60 for m in ue.measurements]
            sinr = [m['sinr'] for m in ue.measurements]
            ax4.plot(times, sinr, marker='o', label=ue.ue_id, markersize=3)

        ax4.set_xlabel('Time (minutes)')
        ax4.set_ylabel('SINR (dB)')
        ax4.set_title('Signal Quality (SINR) vs Time')
        ax4.legend(loc='best', fontsize=8)
        ax4.grid(True, alpha=0.3)

        # Plot 5: Events Timeline
        ax5 = fig.add_subplot(gs[2, :])
        event_types = {'HANDOVER_IMMINENT': 0, 'RAIN_FADE': 1, 'POWER_ADJUST': 2}
        colors = {'HANDOVER_IMMINENT': 'red', 'RAIN_FADE': 'blue', 'POWER_ADJUST': 'green'}

        for event in self.demo_events:
            event_type = event['type']
            if event_type in event_types:
                ax5.scatter(event['time']/60, event_types[event_type],
                          c=colors[event_type], s=100, marker='|', linewidths=3)

        ax5.set_xlabel('Time (minutes)')
        ax5.set_yticks(list(event_types.values()))
        ax5.set_yticklabels(list(event_types.keys()))
        ax5.set_title('Event Timeline')
        ax5.grid(True, alpha=0.3, axis='x')

        plt.suptitle('NTN-O-RAN Integration Demo - LEO Satellite Pass (10 minutes)',
                    fontsize=14, fontweight='bold', y=0.995)

        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plots saved to: {output_path}")
        plt.close()

    def save_results(self, output_path: str):
        """
        Save demo results to JSON

        Args:
            output_path: Path to save results
        """
        print("Saving results...")

        results = {
            'demo_info': {
                'duration_sec': self.simulation_duration_sec,
                'time_step_sec': self.time_step_sec,
                'satellite_altitude_km': 550.0,
                'carrier_frequency_ghz': 2.0,
                'timestamp': datetime.now().isoformat()
            },
            'ue_scenarios': [
                {
                    'ue_id': ue.ue_id,
                    'scenario_type': ue.scenario_type,
                    'description': ue.description,
                    'location': {'lat': ue.lat, 'lon': ue.lon},
                    'measurement_count': len(ue.measurements),
                    'event_count': len(ue.events)
                }
                for ue in self.ues
            ],
            'xapp_statistics': {
                'handover_xapp': self.handover_xapp.collect_statistics(),
                'power_xapp': self.power_xapp.collect_statistics()
            },
            'events': self.demo_events,
            'summary': {
                'total_measurements': sum(len(ue.measurements) for ue in self.ues),
                'total_events': len(self.demo_events),
                'ue_count': len(self.ues)
            }
        }

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {output_path}")

    def print_summary(self):
        """Print demo summary"""
        print("\n" + "="*80)
        print("DEMO SUMMARY")
        print("="*80)

        print("\nUE Scenarios:")
        for ue in self.ues:
            print(f"  {ue.ue_id}:")
            print(f"    Type: {ue.scenario_type}")
            print(f"    Description: {ue.description}")
            print(f"    Measurements: {len(ue.measurements)}")
            print(f"    Events: {len(ue.events)}")

        print(f"\nTotal Events: {len(self.demo_events)}")
        print(f"  Handover Imminent: {sum(1 for e in self.demo_events if e['type'] == 'HANDOVER_IMMINENT')}")
        print(f"  Rain Fade: {sum(1 for e in self.demo_events if e['type'] == 'RAIN_FADE')}")

        print("\n" + "="*80 + "\n")


async def main():
    """Main demo function"""
    print("\n" + "="*80)
    print("NTN-O-RAN Platform - End-to-End Integration Demo")
    print("Demonstrating complete LEO satellite pass with multi-UE scenarios")
    print("="*80 + "\n")

    # Create demo instance
    demo = NTNIntegrationDemo()

    # Run simulation
    await demo.run_simulation()

    # Generate outputs
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'demo_results')
    os.makedirs(output_dir, exist_ok=True)

    plot_path = os.path.join(output_dir, 'ntn_o_ran_integration_plots.png')
    results_path = os.path.join(output_dir, 'ntn_o_ran_integration_results.json')

    demo.generate_plots(plot_path)
    demo.save_results(results_path)
    demo.print_summary()

    print("\n" + "="*80)
    print("Demo Complete!")
    print("="*80)
    print(f"\nOutput files:")
    print(f"  Plots:   {plot_path}")
    print(f"  Results: {results_path}")
    print("\n")


if __name__ == '__main__':
    asyncio.run(main())
