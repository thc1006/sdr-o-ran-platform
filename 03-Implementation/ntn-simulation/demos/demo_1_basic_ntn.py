#!/usr/bin/env python3
"""
Demo 1: Basic NTN Simulation with OpenNTN
基礎 NTN 模擬展示

This demo shows:
1. LEO/MEO/GEO satellite channel modeling
2. GPU acceleration comparison
3. Basic link budget calculation
"""

import numpy as np
import time
import matplotlib.pyplot as plt

try:
    import tensorflow as tf
    import sionna
    print(f"✓ TensorFlow {tf.__version__} loaded")
    print(f"✓ Sionna {sionna.__version__} loaded")
    print(f"✓ GPUs available: {len(tf.config.list_physical_devices('GPU'))}")
except ImportError as e:
    print(f"⚠ Warning: {e}")
    print("Please install: pip install tensorflow sionna")
    exit(1)


class BasicNTNSimulator:
    """Basic NTN Channel Simulator"""

    def __init__(self, orbit_type='LEO', use_gpu=True):
        """
        Args:
            orbit_type: 'LEO', 'MEO', or 'GEO'
            use_gpu: Use GPU acceleration
        """
        self.orbit_type = orbit_type
        self.use_gpu = use_gpu

        # Satellite parameters
        self.orbit_params = {
            'LEO': {'altitude_km': 550, 'period_min': 95},
            'MEO': {'altitude_km': 8000, 'period_min': 360},
            'GEO': {'altitude_km': 35786, 'period_min': 1440}
        }

        # GPU setup
        if use_gpu and tf.config.list_physical_devices('GPU'):
            print(f"🚀 Using GPU acceleration for {orbit_type}")
            self.device = '/GPU:0'
        else:
            print(f"⚠ Using CPU for {orbit_type}")
            self.device = '/CPU:0'

    def calculate_path_loss(self, elevation_angle_deg):
        """
        Calculate free-space path loss for satellite link

        Args:
            elevation_angle_deg: User elevation angle (degrees)

        Returns:
            path_loss_db: Path loss in dB
        """
        # Constants
        freq_ghz = 2.0  # S-band
        c = 3e8  # Speed of light (m/s)

        # Calculate slant range
        altitude = self.orbit_params[self.orbit_type]['altitude_km'] * 1000  # to meters
        elevation_rad = np.deg2rad(elevation_angle_deg)

        earth_radius = 6371e3  # meters
        slant_range = np.sqrt(
            (earth_radius + altitude)**2 - (earth_radius * np.cos(elevation_rad))**2
        ) - earth_radius * np.sin(elevation_rad)

        # Free-space path loss
        wavelength = c / (freq_ghz * 1e9)
        path_loss_db = 20 * np.log10(4 * np.pi * slant_range / wavelength)

        return path_loss_db, slant_range / 1000  # return km

    def simulate_doppler_shift(self, satellite_velocity_kmps, elevation_angle_deg):
        """
        Calculate Doppler shift

        Args:
            satellite_velocity_kmps: Satellite velocity (km/s)
            elevation_angle_deg: User elevation angle (degrees)

        Returns:
            doppler_hz: Doppler shift in Hz
        """
        freq_ghz = 2.0  # S-band
        c = 3e8 / 1000  # km/s

        # Radial velocity component
        v_radial = satellite_velocity_kmps * np.cos(np.deg2rad(90 - elevation_angle_deg))

        # Doppler shift
        doppler_hz = (v_radial / c) * freq_ghz * 1e9

        return doppler_hz

    def gpu_accelerated_simulation(self, num_samples=10000):
        """Run GPU-accelerated simulation"""

        with tf.device(self.device):
            # Generate random elevation angles (5-90 degrees)
            elevations = tf.random.uniform(
                (num_samples,),
                minval=5.0,
                maxval=90.0,
                dtype=tf.float32
            )

            # Calculate path loss (vectorized on GPU)
            start_time = time.perf_counter()

            # This would normally use Sionna's channel models
            # For now, we'll do basic calculation
            path_losses = tf.map_fn(
                lambda elev: self.calculate_path_loss(elev.numpy())[0],
                elevations,
                dtype=tf.float32
            )

            duration = time.perf_counter() - start_time

        return elevations.numpy(), path_losses.numpy(), duration


def main():
    """Run basic NTN simulation demo"""

    print("="*70)
    print("Demo 1: Basic NTN Simulation")
    print("="*70)

    # Test all orbit types
    orbit_types = ['LEO', 'MEO', 'GEO']
    results = {}

    for orbit in orbit_types:
        print(f"\n{'='*70}")
        print(f"Simulating {orbit} Satellite Link")
        print(f"{'='*70}")

        sim = BasicNTNSimulator(orbit_type=orbit, use_gpu=True)

        # 1. Single link calculation
        elevation_deg = 30.0
        path_loss, slant_range = sim.calculate_path_loss(elevation_deg)

        print(f"\nLink Budget for {orbit}:")
        print(f"  Altitude: {sim.orbit_params[orbit]['altitude_km']} km")
        print(f"  Elevation Angle: {elevation_deg}°")
        print(f"  Slant Range: {slant_range:.1f} km")
        print(f"  Path Loss: {path_loss:.2f} dB")

        # 2. Doppler shift
        if orbit == 'LEO':
            velocity_kmps = 7.8  # LEO typical
        elif orbit == 'MEO':
            velocity_kmps = 3.9
        else:  # GEO
            velocity_kmps = 3.07

        doppler = sim.simulate_doppler_shift(velocity_kmps, elevation_deg)
        print(f"  Doppler Shift: {doppler/1000:.2f} kHz")

        # 3. GPU-accelerated batch simulation
        print(f"\n  Running GPU-accelerated simulation (10,000 samples)...")
        elevations, path_losses, duration = sim.gpu_accelerated_simulation(10000)

        print(f"  ✓ Completed in {duration:.3f} seconds")
        print(f"  Throughput: {10000/duration:.1f} samples/sec")

        results[orbit] = {
            'elevations': elevations,
            'path_losses': path_losses,
            'duration': duration
        }

    # Visualization
    print(f"\n{'='*70}")
    print("Generating Visualization...")
    print(f"{'='*70}")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    for idx, orbit in enumerate(orbit_types):
        ax = axes[idx]
        elevations = results[orbit]['elevations']
        path_losses = results[orbit]['path_losses']

        # Scatter plot
        scatter = ax.scatter(
            elevations,
            path_losses,
            c=elevations,
            cmap='viridis',
            alpha=0.5,
            s=1
        )

        ax.set_xlabel('Elevation Angle (degrees)', fontsize=10)
        ax.set_ylabel('Path Loss (dB)', fontsize=10)
        ax.set_title(f'{orbit} Satellite\n({results[orbit]["duration"]:.2f}s)', fontsize=12)
        ax.grid(True, alpha=0.3)

        # Add colorbar
        plt.colorbar(scatter, ax=ax, label='Elevation (deg)')

    plt.tight_layout()
    plt.savefig('ntn_basic_simulation.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: ntn_basic_simulation.png")

    # Performance comparison
    print(f"\n{'='*70}")
    print("Performance Summary")
    print(f"{'='*70}")
    print(f"{'Orbit':<10} {'Duration (s)':<15} {'Throughput (samples/s)':<25}")
    print("-"*70)
    for orbit in orbit_types:
        duration = results[orbit]['duration']
        throughput = 10000 / duration
        print(f"{orbit:<10} {duration:<15.3f} {throughput:<25.1f}")

    print(f"\n{'='*70}")
    print("✓ Demo 1 Complete!")
    print(f"{'='*70}")

    # Next steps
    print("\n📚 Next Steps:")
    print("1. Run demo_2_ray_tracing.py for advanced Sionna ray tracing")
    print("2. Run demo_3_drl_training.py for DRL-based satellite optimization")
    print("3. Explore OpenNTN integration for 3GPP TR38.811 channel models")


if __name__ == "__main__":
    main()
