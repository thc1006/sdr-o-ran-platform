#!/usr/bin/env python3
"""
Real-Time Handover Predictor
=============================

Provides real-time inference for handover prediction using trained LSTM model.

Features:
- Fast inference (<10ms)
- Feature normalization
- Confidence thresholding
- Fallback to baseline if ML fails

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_handover.lstm_model import HandoverLSTMModel
from ml_handover.data_generator import NormalizationParams


class HandoverPredictor:
    """
    Real-time handover prediction using trained LSTM

    Optimized for low-latency inference in production environments.
    """

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        use_fallback: bool = True
    ):
        """
        Initialize predictor

        Args:
            model_path: Path to trained model
            confidence_threshold: Minimum confidence for predictions
            use_fallback: Use baseline if ML fails
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.use_fallback = use_fallback

        # Load model
        self.model = HandoverLSTMModel.load(model_path)

        # Normalization parameters
        self.norm_params = NormalizationParams()

        print(f"[ML-Predictor] Loaded model from: {model_path}")
        print(f"[ML-Predictor] Confidence threshold: {confidence_threshold}")

    def _normalize_features(self, features: Dict[str, List[float]]) -> np.ndarray:
        """
        Normalize features for model input

        Args:
            features: Dictionary with feature lists

        Returns:
            Normalized feature array (1, sequence_length, num_features)
        """
        # Extract features
        elevation = np.array(features['elevation'])
        rsrp = np.array(features['rsrp'])
        doppler = np.array(features['doppler'])
        velocity = np.array(features['velocity'])
        time = np.array(features['time'])

        # Normalize
        elevation_norm = 2 * (elevation - self.norm_params.elevation_min) / \
                        (self.norm_params.elevation_max - self.norm_params.elevation_min) - 1

        rsrp_norm = 2 * (rsrp - self.norm_params.rsrp_min) / \
                    (self.norm_params.rsrp_max - self.norm_params.rsrp_min) - 1

        doppler_norm = doppler / self.norm_params.doppler_max

        velocity_norm = (velocity - self.norm_params.velocity_min) / \
                       (self.norm_params.velocity_max - self.norm_params.velocity_min)

        time_norm = time / self.norm_params.time_max

        # Stack features
        X = np.stack([elevation_norm, rsrp_norm, doppler_norm, velocity_norm, time_norm], axis=1)

        # Add batch dimension
        X = np.expand_dims(X, axis=0).astype(np.float32)

        return X

    def predict_handover(
        self,
        features: Dict[str, List[float]]
    ) -> Tuple[float, float]:
        """
        Predict handover timing and confidence

        Args:
            features: Dictionary with feature sequences:
                - elevation: List of elevation angles (degrees)
                - rsrp: List of RSRP values (dBm)
                - doppler: List of Doppler shifts (Hz)
                - velocity: List of satellite velocities (km/s)
                - time: List of time values (seconds)

        Returns:
            (time_to_handover_seconds, confidence)
        """
        try:
            # Normalize features
            X = self._normalize_features(features)

            # Make prediction
            pred = self.model.predict(X)

            # Denormalize time to handover
            time_to_handover_norm = pred[0, 0]
            confidence = pred[0, 1]

            time_to_handover = time_to_handover_norm * self.norm_params.handover_time_max

            # Clip to valid range
            time_to_handover = np.clip(time_to_handover, 0, 120)
            confidence = np.clip(confidence, 0, 1)

            return float(time_to_handover), float(confidence)

        except Exception as e:
            if self.use_fallback:
                # Fallback to simple baseline
                return self._baseline_prediction(features)
            else:
                raise e

    def _baseline_prediction(
        self,
        features: Dict[str, List[float]]
    ) -> Tuple[float, float]:
        """
        Fallback prediction using simple heuristics

        Args:
            features: Feature dictionary

        Returns:
            (time_to_handover, confidence)
        """
        # Use elevation trend
        elevation = features['elevation']

        if len(elevation) < 2:
            return 60.0, 0.5

        # Estimate decline rate
        decline_rate = (elevation[0] - elevation[-1]) / len(elevation)

        # Current elevation
        current_elev = elevation[-1]

        # Estimate time to 10 degrees (handover threshold)
        if decline_rate > 0.1:
            time_to_handover = max(0, (current_elev - 10) / decline_rate)
        else:
            time_to_handover = 60.0

        # Confidence based on trend consistency
        elevation_std = np.std(np.diff(elevation))
        confidence = 1.0 / (1.0 + elevation_std)

        return float(time_to_handover), float(confidence)

    def predict_batch(
        self,
        feature_list: List[Dict[str, List[float]]]
    ) -> List[Tuple[float, float]]:
        """
        Predict for batch of samples

        Args:
            feature_list: List of feature dictionaries

        Returns:
            List of (time_to_handover, confidence) tuples
        """
        results = []

        for features in feature_list:
            result = self.predict_handover(features)
            results.append(result)

        return results

    def should_trigger_handover(
        self,
        time_to_handover: float,
        confidence: float,
        preparation_time: float = 30.0
    ) -> bool:
        """
        Determine if handover should be triggered

        Args:
            time_to_handover: Predicted time to handover (seconds)
            confidence: Prediction confidence
            preparation_time: Preparation time needed (seconds)

        Returns:
            True if handover should be triggered
        """
        # Trigger if:
        # 1. Time to handover <= preparation time (need to start now)
        # 2. Confidence above threshold
        return (time_to_handover <= preparation_time and
                confidence >= self.confidence_threshold)


if __name__ == '__main__':
    print("Handover Predictor - Test Mode")
    print("=" * 70)

    # This would normally load a trained model
    # For testing, we'll show the interface

    print("Expected usage:")
    print("""
    predictor = HandoverPredictor(model_path='./models/handover_lstm_best.h5')

    features = {
        'elevation': [30, 28, 26, 24, 22, 20, 18, 16, 14, 12],
        'rsrp': [-90] * 10,
        'doppler': [5000] * 10,
        'velocity': [7.5] * 10,
        'time': list(range(10))
    }

    time_to_handover, confidence = predictor.predict_handover(features)

    if predictor.should_trigger_handover(time_to_handover, confidence):
        print("Trigger handover preparation!")
    """)

    print("=" * 70)
