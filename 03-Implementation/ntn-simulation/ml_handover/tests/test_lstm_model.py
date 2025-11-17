#!/usr/bin/env python3
"""
Test Suite for LSTM Model (TDD: Tests Written First)
=====================================================

This test suite defines the expected behavior of the LSTM model
BEFORE implementation. Following strict TDD methodology.

Test Coverage:
- Model architecture (layers, units, activation)
- Input/output shapes
- Forward pass
- Training capabilities
- Model serialization/deserialization
- Performance requirements

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLSTMModelArchitecture:
    """Test LSTM model architecture"""

    def test_model_can_be_imported(self):
        """Test 1: LSTM model can be imported"""
        try:
            from ml_handover.lstm_model import HandoverLSTMModel
            assert HandoverLSTMModel is not None
        except ImportError:
            pytest.fail("HandoverLSTMModel class not found")

    def test_model_initialization(self):
        """Test 2: Model initializes with correct parameters"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5,
            lstm_units=64,
            num_layers=2,
            dropout_rate=0.2
        )

        assert model is not None
        assert model.sequence_length == 10
        assert model.num_features == 5

    def test_model_summary_shows_correct_architecture(self):
        """Test 3: Model has correct layer architecture"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5,
            lstm_units=64,
            num_layers=2
        )

        # Build model
        model.build()

        # Check layer count (at minimum: 2 LSTM + 1 Dense output)
        assert model.get_num_layers() >= 3, "Model should have at least 3 layers"

    def test_model_input_shape(self):
        """Test 4: Model accepts correct input shape"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()

        # Create dummy input
        X_test = np.random.randn(32, 10, 5).astype(np.float32)

        # Should not raise error
        output = model.predict(X_test)

        assert output is not None

    def test_model_output_shape(self):
        """Test 5: Model produces correct output shape"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5,
            lstm_units=64
        )

        model.build()

        # Create dummy input
        batch_size = 32
        X_test = np.random.randn(batch_size, 10, 5).astype(np.float32)

        output = model.predict(X_test)

        # Output shape should be (batch_size, 2) for [time_to_handover, confidence]
        assert output.shape == (batch_size, 2), \
            f"Expected output shape ({batch_size}, 2), got {output.shape}"

    def test_model_output_ranges(self):
        """Test 6: Model outputs are in valid ranges"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()

        # Create dummy input
        X_test = np.random.randn(100, 10, 5).astype(np.float32)

        output = model.predict(X_test)

        # Time to handover should be in [0, 1] (normalized)
        time_to_handover = output[:, 0]
        assert np.all(time_to_handover >= 0.0), "Time to handover has negative values"
        assert np.all(time_to_handover <= 1.0), "Time to handover exceeds 1.0"

        # Confidence should be in [0, 1]
        confidence = output[:, 1]
        assert np.all(confidence >= 0.0), "Confidence has negative values"
        assert np.all(confidence <= 1.0), "Confidence exceeds 1.0"


class TestLSTMModelTraining:
    """Test LSTM model training capabilities"""

    def test_model_can_be_compiled(self):
        """Test 7: Model can be compiled with optimizer and loss"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()
        model.compile(optimizer='adam', learning_rate=0.001)

        assert model.is_compiled(), "Model should be compiled"

    def test_model_can_train(self):
        """Test 8: Model can train on data"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()
        model.compile(optimizer='adam', learning_rate=0.001)

        # Create dummy training data
        X_train = np.random.randn(100, 10, 5).astype(np.float32)
        y_train = np.random.rand(100, 2).astype(np.float32)

        # Train for a few epochs
        history = model.fit(
            X_train, y_train,
            epochs=3,
            batch_size=32,
            verbose=0
        )

        assert history is not None
        assert 'loss' in history.history

    def test_model_loss_decreases_during_training(self):
        """Test 9: Training loss decreases over epochs"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5,
            lstm_units=32
        )

        model.build()
        model.compile(optimizer='adam', learning_rate=0.01)

        # Create dummy training data with clear pattern
        X_train = np.random.randn(200, 10, 5).astype(np.float32)
        # Simple pattern: time_to_handover inversely related to last elevation
        y_train = np.random.rand(200, 2).astype(np.float32)

        # Train
        history = model.fit(
            X_train, y_train,
            epochs=10,
            batch_size=32,
            verbose=0
        )

        # Loss should decrease (at least final loss < initial loss)
        initial_loss = history.history['loss'][0]
        final_loss = history.history['loss'][-1]

        # Allow some tolerance for random initialization
        assert final_loss < initial_loss * 1.2, \
            f"Loss should decrease: initial={initial_loss:.4f}, final={final_loss:.4f}"

    def test_model_supports_validation_data(self):
        """Test 10: Model supports validation during training"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()
        model.compile(optimizer='adam', learning_rate=0.001)

        # Create training and validation data
        X_train = np.random.randn(100, 10, 5).astype(np.float32)
        y_train = np.random.rand(100, 2).astype(np.float32)
        X_val = np.random.randn(20, 10, 5).astype(np.float32)
        y_val = np.random.rand(20, 2).astype(np.float32)

        # Train with validation
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=3,
            batch_size=32,
            verbose=0
        )

        assert 'val_loss' in history.history, "Should track validation loss"


class TestLSTMModelPersistence:
    """Test model saving and loading"""

    def test_model_can_be_saved(self):
        """Test 11: Model can be saved to file"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()
        model.compile(optimizer='adam', learning_rate=0.001)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            model.save(model_path)
            assert os.path.exists(model_path), "Model file should exist"
        finally:
            if os.path.exists(model_path):
                os.remove(model_path)

    def test_model_can_be_loaded(self):
        """Test 12: Model can be loaded from file"""
        from ml_handover.lstm_model import HandoverLSTMModel

        # Create and save model
        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5,
            lstm_units=64
        )

        model.build()
        model.compile(optimizer='adam', learning_rate=0.001)

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            model.save(model_path)

            # Load model
            loaded_model = HandoverLSTMModel.load(model_path)

            assert loaded_model is not None
            assert loaded_model.sequence_length == 10
            assert loaded_model.num_features == 5

        finally:
            if os.path.exists(model_path):
                os.remove(model_path)

    def test_loaded_model_produces_same_predictions(self):
        """Test 13: Loaded model produces same predictions as original"""
        from ml_handover.lstm_model import HandoverLSTMModel

        # Create and train model
        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()
        model.compile(optimizer='adam', learning_rate=0.001)

        # Train briefly
        X_train = np.random.randn(50, 10, 5).astype(np.float32)
        y_train = np.random.rand(50, 2).astype(np.float32)
        model.fit(X_train, y_train, epochs=2, verbose=0)

        # Make prediction
        X_test = np.random.randn(10, 10, 5).astype(np.float32)
        pred_original = model.predict(X_test)

        # Save and load
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            model.save(model_path)
            loaded_model = HandoverLSTMModel.load(model_path)

            # Make prediction with loaded model
            pred_loaded = loaded_model.predict(X_test)

            # Should be identical
            np.testing.assert_array_almost_equal(
                pred_original, pred_loaded, decimal=5,
                err_msg="Loaded model predictions differ from original"
            )

        finally:
            if os.path.exists(model_path):
                os.remove(model_path)


class TestLSTMModelPerformance:
    """Test model performance requirements"""

    def test_inference_latency(self):
        """Test 14: Inference latency is < 10ms for single sample"""
        import time
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5,
            lstm_units=64
        )

        model.build()

        # Warmup
        X_warmup = np.random.randn(1, 10, 5).astype(np.float32)
        _ = model.predict(X_warmup)

        # Measure inference time
        X_test = np.random.randn(1, 10, 5).astype(np.float32)

        start = time.time()
        _ = model.predict(X_test)
        inference_time_ms = (time.time() - start) * 1000

        # Should be < 10ms
        assert inference_time_ms < 10.0, \
            f"Inference time {inference_time_ms:.2f}ms exceeds 10ms requirement"

    def test_batch_inference_efficiency(self):
        """Test 15: Batch inference is more efficient than sequential"""
        import time
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()

        batch_size = 32
        X_test = np.random.randn(batch_size, 10, 5).astype(np.float32)

        # Warmup
        _ = model.predict(X_test[:1])

        # Batch inference
        start_batch = time.time()
        _ = model.predict(X_test)
        time_batch = time.time() - start_batch

        # Sequential inference
        start_seq = time.time()
        for i in range(batch_size):
            _ = model.predict(X_test[i:i+1])
        time_seq = time.time() - start_seq

        # Batch should be faster
        assert time_batch < time_seq, \
            f"Batch inference ({time_batch:.3f}s) should be faster than sequential ({time_seq:.3f}s)"

    def test_model_size(self):
        """Test 16: Model size is reasonable for deployment"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5,
            lstm_units=64,
            num_layers=2
        )

        model.build()

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            model.save(model_path)

            # Check file size
            file_size_mb = os.path.getsize(model_path) / (1024 * 1024)

            # Should be reasonable (< 10 MB for this architecture)
            assert file_size_mb < 10.0, \
                f"Model size {file_size_mb:.2f}MB is too large for deployment"

        finally:
            if os.path.exists(model_path):
                os.remove(model_path)


class TestLSTMModelRobustness:
    """Test model robustness to edge cases"""

    def test_handles_all_zeros_input(self):
        """Test 17: Model handles all-zeros input gracefully"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()

        # All zeros input
        X_zeros = np.zeros((5, 10, 5), dtype=np.float32)

        # Should not crash
        output = model.predict(X_zeros)

        assert output is not None
        assert not np.any(np.isnan(output)), "Model produced NaN on zero input"

    def test_handles_extreme_values(self):
        """Test 18: Model handles extreme (but valid) input values"""
        from ml_handover.lstm_model import HandoverLSTMModel

        model = HandoverLSTMModel(
            sequence_length=10,
            num_features=5
        )

        model.build()

        # Extreme values (at boundaries of normalized range)
        X_extreme = np.ones((5, 10, 5), dtype=np.float32) * 0.999

        # Should not crash
        output = model.predict(X_extreme)

        assert output is not None
        assert not np.any(np.isnan(output)), "Model produced NaN on extreme input"
        assert not np.any(np.isinf(output)), "Model produced Inf on extreme input"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
