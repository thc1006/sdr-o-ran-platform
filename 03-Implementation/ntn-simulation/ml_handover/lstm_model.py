#!/usr/bin/env python3
"""
LSTM Model for Handover Prediction
===================================

Implements LSTM neural network for predicting satellite handover timing
and confidence. This implementation passes all tests in test_lstm_model.py
following TDD methodology.

Architecture:
- Input: (sequence_length, num_features)
- 2x LSTM layers (64 units each) with dropout
- Dense output layer (2 units): [time_to_handover, confidence]
- Sigmoid activation on outputs to ensure [0, 1] range

Performance Requirements:
- Inference latency: < 10ms per sample
- Model size: < 10 MB
- Training convergence: Loss should decrease over epochs

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers
from typing import Optional, Dict, Any, Tuple
import os
import sys

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class HandoverLSTMModel:
    """
    LSTM model for handover prediction

    Predicts time until satellite handover and confidence level
    based on historical measurement sequences.
    """

    def __init__(
        self,
        sequence_length: int = 10,
        num_features: int = 5,
        lstm_units: int = 64,
        num_layers: int = 2,
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001
    ):
        """
        Initialize LSTM model

        Args:
            sequence_length: Length of input sequences
            num_features: Number of features per timestep
            lstm_units: Number of units in each LSTM layer
            num_layers: Number of LSTM layers
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.lstm_units = lstm_units
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate

        # Model will be built later
        self.model: Optional[keras.Model] = None
        self._is_compiled = False

    def build(self) -> keras.Model:
        """
        Build LSTM model architecture

        Returns:
            Compiled Keras model
        """
        # Input layer
        inputs = keras.Input(
            shape=(self.sequence_length, self.num_features),
            name='input_sequence'
        )

        x = inputs

        # LSTM layers
        for i in range(self.num_layers):
            return_sequences = (i < self.num_layers - 1)  # Last layer doesn't return sequences

            x = layers.LSTM(
                units=self.lstm_units,
                return_sequences=return_sequences,
                name=f'lstm_{i+1}'
            )(x)

            # Add dropout for regularization
            if self.dropout_rate > 0:
                x = layers.Dropout(self.dropout_rate, name=f'dropout_{i+1}')(x)

        # Dense output layer (2 outputs: time_to_handover, confidence)
        # Use sigmoid to ensure outputs are in [0, 1] range
        outputs = layers.Dense(
            2,
            activation='sigmoid',
            name='output'
        )(x)

        # Create model
        self.model = keras.Model(inputs=inputs, outputs=outputs, name='handover_lstm')

        return self.model

    def compile(
        self,
        optimizer: str = 'adam',
        learning_rate: Optional[float] = None,
        loss: str = 'mse'
    ):
        """
        Compile model with optimizer and loss

        Args:
            optimizer: Optimizer name ('adam', 'sgd', etc.)
            learning_rate: Learning rate (uses self.learning_rate if None)
            loss: Loss function name
        """
        if self.model is None:
            raise ValueError("Model must be built before compiling")

        if learning_rate is None:
            learning_rate = self.learning_rate

        # Create optimizer
        if optimizer.lower() == 'adam':
            opt = optimizers.Adam(learning_rate=learning_rate)
        elif optimizer.lower() == 'sgd':
            opt = optimizers.SGD(learning_rate=learning_rate)
        elif optimizer.lower() == 'rmsprop':
            opt = optimizers.RMSprop(learning_rate=learning_rate)
        else:
            opt = optimizer

        # Compile model
        self.model.compile(
            optimizer=opt,
            loss=loss,
            metrics=['mae', 'mse']
        )

        self._is_compiled = True

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        epochs: int = 10,
        batch_size: int = 32,
        verbose: int = 1,
        callbacks: Optional[list] = None
    ) -> keras.callbacks.History:
        """
        Train model

        Args:
            X: Training features (samples, sequence_length, features)
            y: Training labels (samples, 2)
            validation_data: Optional validation data (X_val, y_val)
            epochs: Number of training epochs
            batch_size: Batch size
            verbose: Verbosity level (0=silent, 1=progress bar, 2=one line per epoch)
            callbacks: List of Keras callbacks

        Returns:
            Training history
        """
        if not self._is_compiled:
            raise ValueError("Model must be compiled before training")

        history = self.model.fit(
            X, y,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=callbacks
        )

        return history

    def predict(self, X: np.ndarray, batch_size: int = 32) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Input features (samples, sequence_length, features)
            batch_size: Batch size for prediction

        Returns:
            Predictions (samples, 2) [time_to_handover, confidence]
        """
        if self.model is None:
            raise ValueError("Model must be built before prediction")

        predictions = self.model.predict(X, batch_size=batch_size, verbose=0)

        return predictions

    def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        batch_size: int = 32
    ) -> Dict[str, float]:
        """
        Evaluate model on test data

        Args:
            X: Test features
            y: Test labels
            batch_size: Batch size

        Returns:
            Dictionary with metrics
        """
        if not self._is_compiled:
            raise ValueError("Model must be compiled before evaluation")

        results = self.model.evaluate(X, y, batch_size=batch_size, verbose=0)

        # Return as dictionary
        metrics = {}
        for i, name in enumerate(self.model.metrics_names):
            metrics[name] = results[i]

        return metrics

    def save(self, filepath: str):
        """
        Save model to file

        Args:
            filepath: Path to save model (.h5 or .keras)
        """
        if self.model is None:
            raise ValueError("Model must be built before saving")

        self.model.save(filepath)

        # Also save metadata
        metadata = {
            'sequence_length': self.sequence_length,
            'num_features': self.num_features,
            'lstm_units': self.lstm_units,
            'num_layers': self.num_layers,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate
        }

        # Save metadata to companion file
        import json
        metadata_path = filepath.rsplit('.', 1)[0] + '_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'HandoverLSTMModel':
        """
        Load model from file

        Args:
            filepath: Path to saved model

        Returns:
            Loaded HandoverLSTMModel instance
        """
        # Load metadata
        import json
        metadata_path = filepath.rsplit('.', 1)[0] + '_metadata.json'

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            # Default metadata if not found
            metadata = {
                'sequence_length': 10,
                'num_features': 5,
                'lstm_units': 64,
                'num_layers': 2,
                'dropout_rate': 0.2,
                'learning_rate': 0.001
            }

        # Create instance
        instance = cls(**metadata)

        # Load Keras model
        instance.model = keras.models.load_model(filepath)
        instance._is_compiled = True

        return instance

    def get_num_layers(self) -> int:
        """
        Get number of layers in model

        Returns:
            Number of layers
        """
        if self.model is None:
            return 0

        return len(self.model.layers)

    def is_compiled(self) -> bool:
        """
        Check if model is compiled

        Returns:
            True if compiled, False otherwise
        """
        return self._is_compiled

    def summary(self):
        """Print model summary"""
        if self.model is None:
            print("Model not built yet")
            return

        self.model.summary()

    def get_config(self) -> Dict[str, Any]:
        """
        Get model configuration

        Returns:
            Configuration dictionary
        """
        return {
            'sequence_length': self.sequence_length,
            'num_features': self.num_features,
            'lstm_units': self.lstm_units,
            'num_layers': self.num_layers,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate
        }


def create_default_model() -> HandoverLSTMModel:
    """
    Create default LSTM model for handover prediction

    Returns:
        Configured HandoverLSTMModel
    """
    model = HandoverLSTMModel(
        sequence_length=10,
        num_features=5,
        lstm_units=64,
        num_layers=2,
        dropout_rate=0.2,
        learning_rate=0.001
    )

    model.build()
    model.compile(optimizer='adam')

    return model


if __name__ == '__main__':
    # Quick test
    print("Handover LSTM Model - Test Mode")
    print("=" * 70)

    # Create model
    print("Creating model...")
    model = create_default_model()

    print("\nModel architecture:")
    model.summary()

    print("\nModel configuration:")
    config = model.get_config()
    for key, value in config.items():
        print(f"  {key}: {value}")

    # Test prediction
    print("\nTesting prediction...")
    X_test = np.random.randn(10, 10, 5).astype(np.float32)
    predictions = model.predict(X_test)

    print(f"Input shape: {X_test.shape}")
    print(f"Output shape: {predictions.shape}")
    print(f"Sample predictions:")
    for i in range(min(5, len(predictions))):
        time_pred = predictions[i, 0]
        conf_pred = predictions[i, 1]
        print(f"  Sample {i+1}: time={time_pred:.3f}, confidence={conf_pred:.3f}")

    # Test training
    print("\nTesting training...")
    X_train = np.random.randn(100, 10, 5).astype(np.float32)
    y_train = np.random.rand(100, 2).astype(np.float32)

    history = model.fit(X_train, y_train, epochs=3, verbose=0)

    print(f"Training completed")
    print(f"Initial loss: {history.history['loss'][0]:.4f}")
    print(f"Final loss: {history.history['loss'][-1]:.4f}")

    print("\n" + "=" * 70)
