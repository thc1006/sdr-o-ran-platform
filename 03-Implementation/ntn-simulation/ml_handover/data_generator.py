#!/usr/bin/env python3
"""
Handover Data Generator for LSTM Training
==========================================

Generates synthetic training data from orbital mechanics simulation.
This implementation is driven by test_data_generator.py following TDD.

Features Generated:
1. Elevation angle (degrees) - normalized to [-1, 1]
2. RSRP (dBm) - normalized to [-1, 1]
3. Doppler shift (Hz) - normalized to [-1, 1]
4. Satellite velocity (km/s) - normalized to [0, 1]
5. Time in view (seconds) - normalized to [0, 1]

Labels:
1. Time to handover (seconds) - normalized to [0, 1]
2. Confidence level (0-1) - probability of successful handover

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import numpy as np
from typing import Tuple, Optional, Generator
from dataclasses import dataclass
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class NormalizationParams:
    """Normalization parameters for features"""
    # Elevation angle: 0-90 degrees
    elevation_min: float = 0.0
    elevation_max: float = 90.0

    # RSRP: -140 to -70 dBm (typical for satellite)
    rsrp_min: float = -140.0
    rsrp_max: float = -70.0

    # Doppler shift: -15000 to +15000 Hz (LEO at S-band)
    doppler_min: float = -15000.0
    doppler_max: float = 15000.0

    # Satellite velocity: 6-8 km/s (LEO)
    velocity_min: float = 6.0
    velocity_max: float = 8.0

    # Time in view: 0-600 seconds (10 minutes max)
    time_min: float = 0.0
    time_max: float = 600.0

    # Time to handover: 0-120 seconds
    handover_time_min: float = 0.0
    handover_time_max: float = 120.0


class HandoverDataGenerator:
    """
    Generate training data for LSTM handover prediction

    Simulates realistic satellite handover scenarios using orbital
    mechanics principles to create labeled training data.
    """

    def __init__(
        self,
        num_samples: int = 10000,
        sequence_length: int = 10,
        use_mock_data: bool = True,
        augment_data: bool = False,
        min_elevation: float = 10.0,
        rapid_change_scenarios: bool = False,
        random_seed: Optional[int] = None
    ):
        """
        Initialize data generator

        Args:
            num_samples: Number of training samples to generate
            sequence_length: Length of time sequence (timesteps)
            use_mock_data: Use mock data for testing
            augment_data: Apply data augmentation
            min_elevation: Minimum elevation angle (degrees)
            rapid_change_scenarios: Include rapid elevation change scenarios
            random_seed: Random seed for reproducibility
        """
        self.num_samples = num_samples
        self.sequence_length = sequence_length
        self.use_mock_data = use_mock_data
        self.augment_data = augment_data
        self.min_elevation = min_elevation
        self.rapid_change_scenarios = rapid_change_scenarios
        self.random_seed = random_seed

        # Set random seed if provided
        if random_seed is not None:
            np.random.seed(random_seed)

        # Normalization parameters
        self.norm_params = NormalizationParams()

        # Feature names
        self.feature_names = [
            'elevation_angle',
            'rsrp',
            'doppler_shift',
            'satellite_velocity',
            'time_in_view'
        ]

        # Number of features
        self.num_features = len(self.feature_names)

        # Generated data cache
        self._X_cache = None
        self._y_cache = None

    def _normalize_elevation(self, elevation: np.ndarray) -> np.ndarray:
        """Normalize elevation angle to [-1, 1]"""
        return 2 * (elevation - self.norm_params.elevation_min) / \
               (self.norm_params.elevation_max - self.norm_params.elevation_min) - 1

    def _normalize_rsrp(self, rsrp: np.ndarray) -> np.ndarray:
        """Normalize RSRP to [-1, 1]"""
        return 2 * (rsrp - self.norm_params.rsrp_min) / \
               (self.norm_params.rsrp_max - self.norm_params.rsrp_min) - 1

    def _normalize_doppler(self, doppler: np.ndarray) -> np.ndarray:
        """Normalize Doppler shift to [-1, 1]"""
        return doppler / self.norm_params.doppler_max

    def _normalize_velocity(self, velocity: np.ndarray) -> np.ndarray:
        """Normalize satellite velocity to [0, 1]"""
        return (velocity - self.norm_params.velocity_min) / \
               (self.norm_params.velocity_max - self.norm_params.velocity_min)

    def _normalize_time(self, time: np.ndarray) -> np.ndarray:
        """Normalize time in view to [0, 1]"""
        return time / self.norm_params.time_max

    def _normalize_handover_time(self, time: np.ndarray) -> np.ndarray:
        """Normalize time to handover to [0, 1]"""
        return time / self.norm_params.handover_time_max

    def _generate_satellite_pass(self) -> Tuple[np.ndarray, float, float]:
        """
        Generate a single satellite pass trajectory

        Returns:
            elevation_seq: Elevation angles over time (sequence_length,)
            time_to_handover: Seconds until handover needed
            confidence: Confidence in handover prediction (0-1)
        """
        # Generate realistic satellite pass
        # Satellite starts at some elevation and either:
        # 1. Rises to zenith and falls (overhead pass)
        # 2. Rises from horizon and sets (low-elevation pass)
        # 3. Starts high and sets (departing satellite)

        pass_type = np.random.choice(['overhead', 'low_pass', 'departing'])

        if pass_type == 'overhead' or self.rapid_change_scenarios:
            # Overhead pass: elevation rises quickly, peaks, then falls
            peak_elevation = np.random.uniform(60, 85)
            start_elevation = np.random.uniform(self.min_elevation, 30)

            # Time to peak
            time_to_peak = np.random.uniform(30, 60)

            # Generate elevation curve
            t = np.linspace(0, self.sequence_length - 1, self.sequence_length)
            # Parabolic trajectory
            elevation_seq = start_elevation + \
                           (peak_elevation - start_elevation) * \
                           (1 - ((t - time_to_peak) / time_to_peak) ** 2)

            # Clip to valid range
            elevation_seq = np.clip(elevation_seq, self.min_elevation, 90)

            # Time to handover: when elevation drops below min_elevation
            # Estimate from current trajectory
            current_elev = elevation_seq[-1]
            if current_elev > self.min_elevation + 20:
                time_to_handover = np.random.uniform(40, 80)
                confidence = 0.95  # High confidence - plenty of time
            else:
                time_to_handover = np.random.uniform(10, 40)
                confidence = 0.85  # Medium confidence - approaching handover

        elif pass_type == 'low_pass':
            # Low elevation pass: gradual rise and fall
            max_elevation = np.random.uniform(20, 45)
            start_elevation = np.random.uniform(self.min_elevation, 15)

            t = np.linspace(0, self.sequence_length - 1, self.sequence_length)
            # Sinusoidal trajectory
            elevation_seq = start_elevation + \
                           (max_elevation - start_elevation) * \
                           np.sin(np.pi * t / (2 * self.sequence_length))

            elevation_seq = np.clip(elevation_seq, self.min_elevation, 90)

            # Lower elevation = sooner handover
            current_elev = elevation_seq[-1]
            if current_elev < 20:
                time_to_handover = np.random.uniform(5, 30)
                confidence = 0.75  # Lower confidence - difficult geometry
            else:
                time_to_handover = np.random.uniform(20, 60)
                confidence = 0.80

        else:  # departing
            # Departing satellite: elevation steadily decreases
            start_elevation = np.random.uniform(30, 70)

            t = np.linspace(0, self.sequence_length - 1, self.sequence_length)
            # Linear decline
            decline_rate = np.random.uniform(1.5, 4.0)  # degrees per timestep
            elevation_seq = start_elevation - decline_rate * t

            elevation_seq = np.clip(elevation_seq, self.min_elevation, 90)

            # Declining elevation = imminent handover
            current_elev = elevation_seq[-1]
            if current_elev < 15:
                time_to_handover = np.random.uniform(5, 20)
                confidence = 0.90  # High confidence - predictable decline
            else:
                time_to_handover = np.random.uniform(15, 50)
                confidence = 0.88

        return elevation_seq, time_to_handover, confidence

    def _generate_rsrp_from_elevation(self, elevation: np.ndarray) -> np.ndarray:
        """
        Generate RSRP values correlated with elevation

        Higher elevation = better RSRP (shorter path, better geometry)
        """
        # Base RSRP from elevation (higher is better)
        # Free space path loss decreases with elevation
        base_rsrp = -140 + (elevation / 90) * 65  # -140 dBm to -75 dBm range

        # Add realistic noise and fading
        noise = np.random.normal(0, 3, size=elevation.shape)  # 3 dB std dev
        fading = np.random.uniform(-5, 2, size=elevation.shape)  # Fading margin

        rsrp = base_rsrp + noise + fading

        # Clip to realistic range
        rsrp = np.clip(rsrp, -140, -70)

        return rsrp

    def _generate_doppler_from_elevation(self, elevation: np.ndarray) -> np.ndarray:
        """
        Generate Doppler shift based on satellite geometry

        Doppler depends on elevation angle and satellite velocity
        Maximum Doppler at horizon, zero at zenith
        """
        # Doppler is maximum when satellite is approaching/receding (low elevation)
        # Zero when directly overhead (90 degrees)

        # Random approaching or receding
        direction = np.random.choice([-1, 1])

        # Calculate Doppler based on elevation
        # Maximum Doppler at horizon (0 degrees), zero at zenith (90 degrees)
        max_doppler = np.random.uniform(10000, 14000)  # Hz

        doppler = direction * max_doppler * np.cos(np.deg2rad(elevation))

        # Add small random variations
        noise = np.random.normal(0, 200, size=elevation.shape)
        doppler += noise

        # Clip to realistic range
        doppler = np.clip(doppler, -15000, 15000)

        return doppler

    def generate_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate training data

        Returns:
            X: Features array of shape (num_samples, sequence_length, num_features)
            y: Labels array of shape (num_samples, 2) [time_to_handover, confidence]
        """
        # Check cache
        if self._X_cache is not None and self._y_cache is not None:
            return self._X_cache, self._y_cache

        # Initialize arrays
        X = np.zeros((self.num_samples, self.sequence_length, self.num_features))
        y = np.zeros((self.num_samples, 2))

        # Generate samples
        for i in range(self.num_samples):
            # Generate satellite pass
            elevation_seq, time_to_handover, confidence = self._generate_satellite_pass()

            # Generate correlated features
            rsrp_seq = self._generate_rsrp_from_elevation(elevation_seq)
            doppler_seq = self._generate_doppler_from_elevation(elevation_seq)

            # Satellite velocity (relatively constant for LEO)
            velocity_seq = np.random.uniform(6.5, 7.5, size=self.sequence_length)

            # Time in view (increasing sequence)
            time_seq = np.linspace(0, np.random.uniform(100, 400), self.sequence_length)

            # Normalize features
            X[i, :, 0] = self._normalize_elevation(elevation_seq)
            X[i, :, 1] = self._normalize_rsrp(rsrp_seq)
            X[i, :, 2] = self._normalize_doppler(doppler_seq)
            X[i, :, 3] = self._normalize_velocity(velocity_seq)
            X[i, :, 4] = self._normalize_time(time_seq)

            # Normalize labels
            y[i, 0] = self._normalize_handover_time(time_to_handover)
            y[i, 1] = confidence

        # Apply data augmentation if enabled
        if self.augment_data:
            X, y = self._augment_data(X, y)

        # Cache data
        self._X_cache = X
        self._y_cache = y

        return X, y

    def _augment_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply data augmentation to increase dataset size

        Techniques:
        - Add small Gaussian noise
        - Time shifting
        - Scaling
        """
        # Add 20% more samples through augmentation
        num_augmented = int(self.num_samples * 0.2)

        X_aug = np.zeros((num_augmented, self.sequence_length, self.num_features))
        y_aug = np.zeros((num_augmented, 2))

        for i in range(num_augmented):
            # Select random sample
            idx = np.random.randint(0, X.shape[0])

            # Copy sample
            X_aug[i] = X[idx].copy()
            y_aug[i] = y[idx].copy()

            # Add small noise
            noise = np.random.normal(0, 0.05, size=X_aug[i].shape)
            X_aug[i] += noise

            # Clip to valid range
            X_aug[i] = np.clip(X_aug[i], -1, 1)

        # Concatenate original and augmented data
        X = np.vstack([X, X_aug])
        y = np.vstack([y, y_aug])

        return X, y

    def get_train_val_split(
        self,
        validation_split: float = 0.2
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Split data into training and validation sets

        Args:
            validation_split: Fraction of data for validation

        Returns:
            X_train, X_val, y_train, y_val
        """
        # Generate data if not cached
        X, y = self.generate_training_data()

        # Shuffle data
        indices = np.arange(X.shape[0])
        np.random.shuffle(indices)

        X = X[indices]
        y = y[indices]

        # Split
        split_idx = int(X.shape[0] * (1 - validation_split))

        X_train = X[:split_idx]
        X_val = X[split_idx:]
        y_train = y[:split_idx]
        y_val = y[split_idx:]

        return X_train, X_val, y_train, y_val

    def batch_generator(
        self,
        batch_size: int = 32
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate batches for memory-efficient training

        Args:
            batch_size: Size of each batch

        Yields:
            X_batch, y_batch
        """
        # Generate data if not cached
        X, y = self.generate_training_data()

        num_batches = int(np.ceil(X.shape[0] / batch_size))

        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, X.shape[0])

            X_batch = X[start_idx:end_idx]
            y_batch = y[start_idx:end_idx]

            yield X_batch, y_batch

    def get_normalization_params(self) -> NormalizationParams:
        """Get normalization parameters for inference"""
        return self.norm_params

    def denormalize_prediction(
        self,
        time_to_handover_norm: float,
        confidence: float
    ) -> Tuple[float, float]:
        """
        Denormalize model predictions

        Args:
            time_to_handover_norm: Normalized time to handover [0, 1]
            confidence: Confidence level [0, 1]

        Returns:
            time_to_handover_sec: Time in seconds
            confidence: Confidence (unchanged)
        """
        time_to_handover_sec = time_to_handover_norm * self.norm_params.handover_time_max
        return time_to_handover_sec, confidence


if __name__ == '__main__':
    # Quick test
    print("Handover Data Generator - Test Mode")
    print("=" * 70)

    generator = HandoverDataGenerator(
        num_samples=100,
        sequence_length=10,
        use_mock_data=True,
        random_seed=42
    )

    print(f"Generating {generator.num_samples} samples...")
    X, y = generator.generate_training_data()

    print(f"\nGenerated data:")
    print(f"  X shape: {X.shape}")
    print(f"  y shape: {y.shape}")
    print(f"  Features: {generator.feature_names}")

    print(f"\nFeature statistics:")
    for i, name in enumerate(generator.feature_names):
        feature_data = X[:, :, i]
        print(f"  {name}:")
        print(f"    Min: {np.min(feature_data):.3f}")
        print(f"    Max: {np.max(feature_data):.3f}")
        print(f"    Mean: {np.mean(feature_data):.3f}")
        print(f"    Std: {np.std(feature_data):.3f}")

    print(f"\nLabel statistics:")
    print(f"  Time to handover:")
    print(f"    Min: {np.min(y[:, 0]):.3f}")
    print(f"    Max: {np.max(y[:, 0]):.3f}")
    print(f"    Mean: {np.mean(y[:, 0]):.3f}")
    print(f"  Confidence:")
    print(f"    Min: {np.min(y[:, 1]):.3f}")
    print(f"    Max: {np.max(y[:, 1]):.3f}")
    print(f"    Mean: {np.mean(y[:, 1]):.3f}")

    print("\n" + "=" * 70)
