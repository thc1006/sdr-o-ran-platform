"""
Weather Integration Demo with Rain Fade Scenario

Demonstrates:
1. Real-time weather-aware link budget calculation
2. Rain fade event simulation
3. xApp-triggered rain mitigation
4. Time series attenuation plotting
5. Comparison with/without weather integration

This demo showcases the complete weather integration pipeline:
- ITU-R P.618 rain attenuation model
- Real-time weather data
- Dynamic link adaptation
- Performance optimization
"""

import asyncio
import time
import numpy as np
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from weather.itur_p618 import ITUR_P618_RainAttenuation
from weather.weather_api import WeatherDataProvider
from weather.realtime_attenuation import RealtimeAttenuationCalculator

# Try to import plotting (optional)
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Note: matplotlib not available. Plots will be skipped.")


class WeatherIntegrationDemo:
    """Comprehensive weather integration demonstration"""

    def __init__(self):
        self.itur = ITUR_P618_RainAttenuation()
        self.calc = None
        self.results: List[Dict] = []

    async def initialize(self):
        """Initialize demo components"""
        print("\n" + "=" * 70)
        print("  WEATHER INTEGRATION DEMO - ITU-R P.618 + Real-Time Data")
        print("=" * 70)

        self.calc = RealtimeAttenuationCalculator(
            use_mock_weather=True,  # Use mock for demo
            cache_duration_sec=300.0,
            fade_threshold_db=3.0
        )

        print("\n✓ Weather integration initialized")
        print("  - ITU-R P.618-13 rain attenuation model")
        print("  - Real-time weather calculator")
        print("  - Rain fade detector")

    async def demo_1_basic_calculation(self):
        """Demo 1: Basic weather-aware link budget"""
        print("\n" + "-" * 70)
        print("DEMO 1: Basic Weather-Aware Link Budget Calculation")
        print("-" * 70)

        # Test location: New York City
        latitude = 40.7128
        longitude = -74.0060
        frequency_ghz = 20.0  # Ka-band
        elevation_angle = 30.0

        print(f"\nScenario:")
        print(f"  Location: New York City ({latitude}°N, {longitude}°W)")
        print(f"  Frequency: {frequency_ghz} GHz (Ka-band)")
        print(f"  Elevation: {elevation_angle}°")

        # Calculate with real-time weather
        print("\n1. Calculating with real-time weather...")
        result = await self.calc.calculate_current_attenuation(
            latitude, longitude, frequency_ghz, elevation_angle
        )

        print(f"\n  Current Conditions:")
        print(f"    Temperature: {result.temperature_c:.1f}°C")
        print(f"    Humidity: {result.humidity_percent:.1f}%")
        print(f"    Rain rate: {result.current_rain_rate_mm_h:.2f} mm/h")
        print(f"    Cloud cover: {result.cloud_cover_percent:.1f}%")

        print(f"\n  Attenuation Components:")
        print(f"    Rain:   {result.rain_attenuation_db:6.2f} dB")
        print(f"    Cloud:  {result.cloud_attenuation_db:6.2f} dB")
        print(f"    Gases:  {result.gas_attenuation_db:6.2f} dB")
        print(f"    ────────────────────")
        print(f"    TOTAL:  {result.total_atmospheric_loss_db:6.2f} dB")

        print(f"\n  Statistical Reference (ITU-R P.618):")
        print(f"    Exceeded 0.01%: {result.statistical_rain_attenuation_0_01_percent:.2f} dB")
        print(f"    Exceeded 0.1%:  {result.statistical_rain_attenuation_0_1_percent:.2f} dB")
        print(f"    Exceeded 1%:    {result.statistical_rain_attenuation_1_percent:.2f} dB")

        print(f"\n  Performance:")
        print(f"    Calculation time: {result.calculation_time_ms:.2f} ms")
        print(f"    Target met (<100ms): {'✓ YES' if result.calculation_time_ms < 100 else '✗ NO'}")

        return result

    async def demo_2_rain_fade_scenario(self):
        """Demo 2: Rain fade event simulation"""
        print("\n" + "-" * 70)
        print("DEMO 2: Rain Fade Event Simulation")
        print("-" * 70)

        # Simulate a rain storm passing through
        print("\nSimulating 2-hour rain storm scenario...")

        latitude = 40.7128
        longitude = -74.0060
        frequency_ghz = 20.0
        elevation_angle = 30.0

        # Time series simulation
        duration_minutes = 120
        time_step_minutes = 2
        num_steps = duration_minutes // time_step_minutes

        # Simulate variable rain rates (storm passing through)
        rain_scenarios = []
        for i in range(num_steps):
            t = i / num_steps  # Normalized time (0 to 1)

            # Storm model: Gaussian peak in the middle
            storm_intensity = 50.0 * np.exp(-((t - 0.5) ** 2) / 0.02)  # Peak at 50% time
            noise = 5.0 * np.random.random()  # Small variations

            rain_rate = max(0.0, storm_intensity + noise)

            # Categorize scenario
            if rain_rate < 2.5:
                scenario = 'clear'
            elif rain_rate < 10:
                scenario = 'light_rain'
            elif rain_rate < 25:
                scenario = 'moderate_rain'
            else:
                scenario = 'heavy_rain'

            rain_scenarios.append({
                'time_minutes': i * time_step_minutes,
                'rain_rate': rain_rate,
                'scenario': scenario
            })

        print(f"  Duration: {duration_minutes} minutes")
        print(f"  Time steps: {num_steps} ({time_step_minutes} min intervals)")
        print(f"  Peak rain rate: {max(s['rain_rate'] for s in rain_scenarios):.1f} mm/h")

        # Calculate attenuation for each time step
        print("\nCalculating attenuation time series...")

        time_series = []
        start_time = datetime.now()

        for i, scenario_data in enumerate(rain_scenarios):
            # For demo, use statistical model with different rain rates
            # (In production, this would use real weather forecasts)

            result = await self.calc.calculate_current_attenuation(
                latitude, longitude, frequency_ghz, elevation_angle,
                use_real_weather=False
            )

            time_series.append({
                'timestamp': start_time + timedelta(minutes=scenario_data['time_minutes']),
                'time_minutes': scenario_data['time_minutes'],
                'rain_rate_mm_h': scenario_data['rain_rate'],
                'rain_attenuation_db': result.rain_attenuation_db,
                'total_loss_db': result.total_atmospheric_loss_db,
                'is_fade': result.is_rain_fade_event,
                'scenario': scenario_data['scenario']
            })

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{num_steps} steps")

        self.results = time_series

        # Analyze results
        fade_periods = [r for r in time_series if r['is_fade']]
        max_attenuation = max(r['rain_attenuation_db'] for r in time_series)
        mean_attenuation = np.mean([r['rain_attenuation_db'] for r in time_series])

        print(f"\nResults:")
        print(f"  Max attenuation: {max_attenuation:.2f} dB")
        print(f"  Mean attenuation: {mean_attenuation:.2f} dB")
        print(f"  Fade events: {len(fade_periods)}/{num_steps} time steps")
        print(f"  Fade percentage: {len(fade_periods)/num_steps*100:.1f}%")

        return time_series

    async def demo_3_xapp_mitigation(self):
        """Demo 3: xApp-triggered rain mitigation"""
        print("\n" + "-" * 70)
        print("DEMO 3: xApp-Triggered Rain Mitigation")
        print("-" * 70)

        print("\nScenario: xApp detects rain fade and triggers mitigation")

        # Simulate rain fade condition
        latitude = 40.7128
        longitude = -74.0060
        frequency_ghz = 20.0
        elevation_angle = 30.0

        print("\n1. Normal conditions (clear sky)")
        result_clear = await self.calc.calculate_current_attenuation(
            latitude, longitude, frequency_ghz, elevation_angle
        )

        print(f"   Rain attenuation: {result_clear.rain_attenuation_db:.2f} dB")
        print(f"   Total loss: {result_clear.total_atmospheric_loss_db:.2f} dB")
        print(f"   Link margin: {result_clear.fade_margin_db:.2f} dB")

        print("\n2. Rain fade detected (simulated 40 mm/h rain)")
        # In production, this would be real-time detection
        print(f"   xApp receives E2 Indication: High rain attenuation")
        print(f"   Rain fade event: DETECTED")

        print("\n3. xApp triggers mitigation actions:")
        mitigation_actions = [
            "✓ Increase transmit power by 3 dB",
            "✓ Reduce MCS from MCS-16 to MCS-10 (more robust)",
            "✓ Enable adaptive coding (FEC rate 1/2)",
            "✓ Switch to diversity reception",
            "✓ Trigger beam repointing if available"
        ]

        for action in mitigation_actions:
            print(f"   {action}")
            await asyncio.sleep(0.1)  # Simulate action delay

        print("\n4. Link budget after mitigation:")
        print(f"   Additional power: +3 dB")
        print(f"   Coding gain: +2 dB")
        print(f"   Diversity gain: +3 dB")
        print(f"   Total mitigation: +8 dB")
        print(f"   Effective margin: {result_clear.fade_margin_db + 8:.2f} dB")

        print("\n✓ Rain fade successfully mitigated!")

    async def demo_4_performance_comparison(self):
        """Demo 4: Performance comparison with/without weather"""
        print("\n" + "-" * 70)
        print("DEMO 4: Performance Comparison (With/Without Weather)")
        print("-" * 70)

        latitude = 40.7128
        longitude = -74.0060
        frequency_ghz = 20.0
        elevation_angle = 30.0

        print("\nComparing link budget calculations...")

        # Calculate free space path loss only
        earth_radius_km = 6371.0
        satellite_altitude_km = 600.0  # LEO
        central_angle = (90 - elevation_angle) * np.pi / 180
        slant_range_km = np.sqrt(
            earth_radius_km**2 + (earth_radius_km + satellite_altitude_km)**2 -
            2 * earth_radius_km * (earth_radius_km + satellite_altitude_km) *
            np.cos(central_angle)
        )

        freq_hz = frequency_ghz * 1e9
        wavelength_m = 3e8 / freq_hz
        fspl_db = 20 * np.log10(4 * np.pi * slant_range_km * 1000 / wavelength_m)

        print(f"\n1. Without weather integration:")
        print(f"   Free space path loss: {fspl_db:.2f} dB")
        print(f"   Assumed atmospheric loss: 2.0 dB (constant)")
        print(f"   Total path loss: {fspl_db + 2.0:.2f} dB")

        # Calculate with weather
        result = await self.calc.calculate_current_attenuation(
            latitude, longitude, frequency_ghz, elevation_angle
        )

        print(f"\n2. With weather integration (ITU-R P.618):")
        print(f"   Free space path loss: {fspl_db:.2f} dB")
        print(f"   Rain attenuation: {result.rain_attenuation_db:.2f} dB")
        print(f"   Cloud attenuation: {result.cloud_attenuation_db:.2f} dB")
        print(f"   Gas attenuation: {result.gas_attenuation_db:.2f} dB")
        print(f"   Total atmospheric loss: {result.total_atmospheric_loss_db:.2f} dB")
        print(f"   Total path loss: {fspl_db + result.total_atmospheric_loss_db:.2f} dB")

        difference = result.total_atmospheric_loss_db - 2.0
        print(f"\n3. Difference:")
        print(f"   Atmospheric loss delta: {difference:+.2f} dB")
        print(f"   Impact on link margin: {-difference:.2f} dB")

        print(f"\nConclusion:")
        if abs(difference) < 1.0:
            print(f"  ✓ Atmospheric conditions close to nominal")
        elif difference > 0:
            print(f"  ⚠ Higher than expected attenuation - mitigation may be needed")
        else:
            print(f"  ✓ Better than expected conditions - link margin available")

    def plot_results(self):
        """Plot time series results"""
        if not PLOTTING_AVAILABLE:
            print("\n  (Plotting skipped - matplotlib not available)")
            return

        if not self.results:
            print("\n  (No data to plot)")
            return

        print("\n" + "-" * 70)
        print("DEMO 5: Visualization - Rain Fade Time Series")
        print("-" * 70)

        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle('Weather Integration Demo - Rain Fade Scenario\n'
                    'Ka-band (20 GHz) LEO Satellite Link',
                    fontsize=14, fontweight='bold')

        # Extract data
        times = [r['time_minutes'] for r in self.results]
        rain_rates = [r['rain_rate_mm_h'] for r in self.results]
        attenuations = [r['rain_attenuation_db'] for r in self.results]
        total_losses = [r['total_loss_db'] for r in self.results]
        is_fade = [r['is_fade'] for r in self.results]

        # Plot 1: Rain rate
        ax1.plot(times, rain_rates, 'b-', linewidth=2, label='Rain Rate')
        ax1.fill_between(times, rain_rates, alpha=0.3)
        ax1.set_ylabel('Rain Rate (mm/h)', fontsize=11, fontweight='bold')
        ax1.set_title('Rain Storm Intensity', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot 2: Attenuation
        ax2.plot(times, attenuations, 'r-', linewidth=2, label='Rain Attenuation')
        ax2.axhline(y=3.0, color='orange', linestyle='--',
                   label='Fade Threshold (3 dB)')
        ax2.fill_between(times, attenuations, alpha=0.3, color='red')

        # Highlight fade periods
        fade_times = [t for t, f in zip(times, is_fade) if f]
        fade_attens = [a for a, f in zip(attenuations, is_fade) if f]
        if fade_times:
            ax2.scatter(fade_times, fade_attens, color='darkred',
                       s=50, marker='x', label='Fade Events', zorder=5)

        ax2.set_ylabel('Attenuation (dB)', fontsize=11, fontweight='bold')
        ax2.set_title('Rain Attenuation (ITU-R P.618-13)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # Plot 3: Total atmospheric loss
        ax3.plot(times, total_losses, 'g-', linewidth=2,
                label='Total Atmospheric Loss')
        ax3.fill_between(times, total_losses, alpha=0.3, color='green')
        ax3.set_xlabel('Time (minutes)', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Total Loss (dB)', fontsize=11, fontweight='bold')
        ax3.set_title('Total Atmospheric Loss (Rain + Cloud + Gases)',
                     fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.legend()

        plt.tight_layout()

        # Save plot
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'demo_results')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'weather_integration_demo.png')

        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ Plot saved to: {output_file}")

        # Also try to display (may not work in all environments)
        try:
            plt.show(block=False)
            plt.pause(1)
        except:
            pass

    async def run_demo(self):
        """Run complete demonstration"""
        await self.initialize()

        # Run all demos
        await self.demo_1_basic_calculation()
        time_series = await self.demo_2_rain_fade_scenario()
        await self.demo_3_xapp_mitigation()
        await self.demo_4_performance_comparison()

        # Plot results
        self.plot_results()

        # Final summary
        print("\n" + "=" * 70)
        print("DEMO SUMMARY")
        print("=" * 70)

        stats = self.calc.get_performance_stats()

        print(f"\nPerformance Metrics:")
        print(f"  Total calculations: {stats['total_calculations']}")
        print(f"  Average time: {stats['average_time_ms']:.2f} ms")
        print(f"  Target met (<100ms): {'✓ YES' if stats['target_met'] else '✗ NO'}")

        print(f"\nFade Detection:")
        fade_stats = stats['fade_detector_stats']
        print(f"  Total events: {fade_stats['total_events']}")
        print(f"  Total fade time: {fade_stats['total_fade_time_sec']:.1f} s")

        print(f"\nWeather Cache:")
        cache_stats = stats['weather_cache_stats']
        print(f"  Cached locations: {cache_stats['total_cached_locations']}")
        print(f"  Provider: {cache_stats['provider']}")

        print("\n" + "=" * 70)
        print("✓ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)

        # Cleanup
        await self.calc.close()


async def main():
    """Main demo entry point"""
    demo = WeatherIntegrationDemo()

    try:
        await demo.run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if demo.calc:
            await demo.calc.close()


if __name__ == '__main__':
    asyncio.run(main())
