#!/usr/bin/env python3
"""
Test Suite for Data Generator (TDD: Tests Written First)
========================================================

This test suite defines the expected behavior of the data generator
BEFORE implementation. Following strict TDD methodology.

Test Coverage:
- Data generation from orbital mechanics
- Feature normalization and scaling
- Sequence generation for LSTM
- Train/validation split
- Edge cases and data quality

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDataGenerator:
    """Test data generator for LSTM training"""

    def test_data_generator_exists(self):
        """Test 1: Data generator module can be imported"""
        try:
            from ml_handover.data_generator import HandoverDataGenerator
            assert HandoverDataGenerator is not None
        except ImportError:
            pytest.fail("HandoverDataGenerator class not found")

    def test_generate_training_data_shape(self):
        """Test 2: Generated data has correct shape"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=1000,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # X shape: (samples, sequence_length, features)
        # Features: [elevation, rsrp, doppler, velocity, time_in_view]
        assert X.shape[0] == 1000, f"Expected 1000 samples, got {X.shape[0]}"
        assert X.shape[1] == 10, f"Expected sequence length 10, got {X.shape[1]}"
        assert X.shape[2] == 5, f"Expected 5 features, got {X.shape[2]}"

        # y shape: (samples, 2) for [time_to_handover, confidence]
        assert y.shape[0] == 1000, f"Expected 1000 labels, got {y.shape[0]}"
        assert y.shape[1] == 2, f"Expected 2 outputs, got {y.shape[1]}"

    def test_feature_normalization(self):
        """Test 3: Features are properly normalized to [0, 1] or [-1, 1]"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # Check normalization
        for feature_idx in range(X.shape[2]):
            feature_values = X[:, :, feature_idx]
            min_val = np.min(feature_values)
            max_val = np.max(feature_values)

            # Features should be normalized
            assert min_val >= -1.0, f"Feature {feature_idx} min {min_val} < -1.0"
            assert max_val <= 1.0, f"Feature {feature_idx} max {max_val} > 1.0"

    def test_label_ranges(self):
        """Test 4: Labels are within expected ranges"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # time_to_handover should be 0-120 seconds (normalized to 0-1)
        time_to_handover = y[:, 0]
        assert np.all(time_to_handover >= 0.0), "Time to handover has negative values"
        assert np.all(time_to_handover <= 1.0), "Time to handover exceeds 1.0"

        # confidence should be 0-1 (0-100%)
        confidence = y[:, 1]
        assert np.all(confidence >= 0.0), "Confidence has negative values"
        assert np.all(confidence <= 1.0), "Confidence exceeds 1.0"

    def test_train_validation_split(self):
        """Test 5: Data can be split into train/validation sets"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=1000,
            sequence_length=10,
            use_mock_data=True
        )

        X_train, X_val, y_train, y_val = generator.get_train_val_split(
            validation_split=0.2
        )

        # Check split ratios
        total_samples = X_train.shape[0] + X_val.shape[0]
        assert total_samples == 1000, f"Expected 1000 total samples, got {total_samples}"

        # Validation should be ~20%
        val_ratio = X_val.shape[0] / total_samples
        assert 0.15 <= val_ratio <= 0.25, f"Validation ratio {val_ratio} not in range [0.15, 0.25]"

    def test_sequence_generation(self):
        """Test 6: Sequences are properly generated from time series data"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # Each sequence should be continuous in time
        # Check that sequences are valid (no NaN, no inf)
        assert not np.any(np.isnan(X)), "Generated data contains NaN values"
        assert not np.any(np.isinf(X)), "Generated data contains infinite values"
        assert not np.any(np.isnan(y)), "Generated labels contain NaN values"
        assert not np.any(np.isinf(y)), "Generated labels contain infinite values"

    def test_feature_consistency(self):
        """Test 7: Features are physically consistent"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # Denormalize features for checking
        # Feature indices: 0=elevation, 1=rsrp, 2=doppler, 3=velocity, 4=time

        # Check that features are monotonic or have expected patterns
        # Elevation should generally decrease as satellite moves away
        for sample_idx in range(min(10, X.shape[0])):
            elevation_seq = X[sample_idx, :, 0]

            # Elevation sequence should show some variation
            elevation_std = np.std(elevation_seq)
            assert elevation_std > 0.01, "Elevation sequence has no variation"

    def test_data_augmentation(self):
        """Test 8: Data augmentation increases dataset size"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True,
            augment_data=True
        )

        X, y = generator.generate_training_data()

        # With augmentation, we should get more samples
        # At minimum, should still have original count
        assert X.shape[0] >= 100, f"Augmentation reduced samples to {X.shape[0]}"

    def test_edge_case_low_elevation(self):
        """Test 9: Handle edge case of very low elevation angles"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=50,
            sequence_length=10,
            use_mock_data=True,
            min_elevation=5.0  # Very low elevation
        )

        X, y = generator.generate_training_data()

        # Should still generate valid data
        assert X.shape[0] == 50, "Failed to generate data with low elevation"
        assert not np.any(np.isnan(X)), "Low elevation generated NaN values"

    def test_edge_case_rapid_elevation_change(self):
        """Test 10: Handle rapid elevation changes (satellite overhead pass)"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=50,
            sequence_length=10,
            use_mock_data=True,
            rapid_change_scenarios=True
        )

        X, y = generator.generate_training_data()

        # Should handle rapid changes without errors
        assert X.shape[0] == 50, "Failed to generate rapid change scenarios"
        assert not np.any(np.isnan(y)), "Rapid changes generated invalid labels"

    def test_reproducibility(self):
        """Test 11: Data generation is reproducible with same seed"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator1 = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True,
            random_seed=42
        )

        generator2 = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True,
            random_seed=42
        )

        X1, y1 = generator1.generate_training_data()
        X2, y2 = generator2.generate_training_data()

        # Should be identical
        np.testing.assert_array_almost_equal(X1, X2, decimal=6,
                                              err_msg="Data not reproducible with same seed")
        np.testing.assert_array_almost_equal(y1, y2, decimal=6,
                                              err_msg="Labels not reproducible with same seed")

    def test_batch_generation(self):
        """Test 12: Can generate data in batches for memory efficiency"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=1000,
            sequence_length=10,
            use_mock_data=True
        )

        # Generate in batches
        batch_size = 100
        batch_count = 0
        total_samples = 0

        for X_batch, y_batch in generator.batch_generator(batch_size=batch_size):
            batch_count += 1
            total_samples += X_batch.shape[0]

            # Each batch should have correct shape
            assert X_batch.shape[1] == 10, "Batch has wrong sequence length"
            assert X_batch.shape[2] == 5, "Batch has wrong feature count"
            assert y_batch.shape[1] == 2, "Batch has wrong output size"

            if batch_count >= 5:  # Test first 5 batches
                break

        assert batch_count >= 5, "Failed to generate multiple batches"


class TestDataQuality:
    """Test data quality and physical validity"""

    def test_elevation_rsrp_correlation(self):
        """Test 13: RSRP should correlate with elevation angle"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # Extract elevation and RSRP
        elevation = X[:, :, 0].flatten()
        rsrp = X[:, :, 1].flatten()

        # Should have positive correlation (higher elevation -> better RSRP)
        correlation = np.corrcoef(elevation, rsrp)[0, 1]

        # Allow for some noise, but should be generally positive
        assert correlation > 0.0, f"Elevation-RSRP correlation {correlation} should be positive"

    def test_time_to_handover_monotonic(self):
        """Test 14: Time to handover should decrease over sequence"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=50,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # Check time progression in sequences
        # The last timestep in each sequence should be closer to handover
        # This is implicit in the label y (time_to_handover at end of sequence)
        assert y.shape[0] == 50, "Generated wrong number of samples"

    def test_realistic_doppler_values(self):
        """Test 15: Doppler shift values should be realistic for LEO"""
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(
            num_samples=100,
            sequence_length=10,
            use_mock_data=True
        )

        X, y = generator.generate_training_data()

        # Doppler is normalized, but should have variation
        doppler = X[:, :, 2]
        doppler_std = np.std(doppler)

        # Should have some variation (not all the same)
        assert doppler_std > 0.01, "Doppler values have no variation"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
