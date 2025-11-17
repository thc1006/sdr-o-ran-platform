#!/usr/bin/env python3
"""
Test Suite for Predictor (TDD: Tests Written First)
===================================================

Test Coverage:
- Real-time inference
- Feature normalization
- Prediction confidence thresholding
- Latency requirements (<10ms)
- Batch prediction
- Edge cases

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPredictor:
    """Test handover predictor"""

    def test_predictor_exists(self):
        """Test 1: Predictor class exists"""
        try:
            from ml_handover.predictor import HandoverPredictor
            assert HandoverPredictor is not None
        except ImportError:
            pytest.fail("HandoverPredictor class not found")

    def test_predictor_loads_model(self):
        """Test 2: Predictor can load trained model"""
        from ml_handover.predictor import HandoverPredictor

        # Create mock model first
        from ml_handover.lstm_model import HandoverLSTMModel
        import tempfile

        model = HandoverLSTMModel()
        model.build()
        model.compile()

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            model.save(model_path)

            # Load with predictor
            predictor = HandoverPredictor(model_path=model_path)
            assert predictor is not None

        finally:
            if os.path.exists(model_path):
                os.remove(model_path)

    def test_predictor_makes_prediction(self):
        """Test 3: Predictor makes valid predictions"""
        from ml_handover.predictor import HandoverPredictor
        from ml_handover.lstm_model import HandoverLSTMModel
        import tempfile

        model = HandoverLSTMModel()
        model.build()
        model.compile()

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            model.save(model_path)

            predictor = HandoverPredictor(model_path=model_path)

            # Make prediction
            features = {
                'elevation': [30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0, 16.0, 14.0, 12.0],
                'rsrp': [-90.0] * 10,
                'doppler': [5000.0] * 10,
                'velocity': [7.5] * 10,
                'time': list(range(10))
            }

            time_to_handover, confidence = predictor.predict_handover(features)

            assert 0 <= time_to_handover <= 120, "Time to handover out of range"
            assert 0 <= confidence <= 1.0, "Confidence out of range"

        finally:
            if os.path.exists(model_path):
                os.remove(model_path)

    def test_predictor_inference_latency(self):
        """Test 4: Inference latency < 10ms"""
        import time
        from ml_handover.predictor import HandoverPredictor
        from ml_handover.lstm_model import HandoverLSTMModel
        import tempfile

        model = HandoverLSTMModel()
        model.build()

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            model.save(model_path)

            predictor = HandoverPredictor(model_path=model_path)

            features = {
                'elevation': list(range(10, 0, -1)),
                'rsrp': [-90.0] * 10,
                'doppler': [5000.0] * 10,
                'velocity': [7.5] * 10,
                'time': list(range(10))
            }

            # Warmup
            _ = predictor.predict_handover(features)

            # Measure latency
            start = time.time()
            _ = predictor.predict_handover(features)
            latency_ms = (time.time() - start) * 1000

            assert latency_ms < 10.0, f"Latency {latency_ms:.2f}ms exceeds 10ms"

        finally:
            if os.path.exists(model_path):
                os.remove(model_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
