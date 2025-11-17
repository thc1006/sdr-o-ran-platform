#!/usr/bin/env python3
"""
LSTM Trainer for Handover Prediction
=====================================

Training pipeline with early stopping, model checkpointing,
and learning rate scheduling.

Features:
- Early stopping to prevent overfitting
- Model checkpointing (save best model)
- Learning rate reduction on plateau
- TensorBoard logging
- Training history export

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import numpy as np
from typing import Optional, Dict, List, Any, Tuple
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from ml_handover.lstm_model import HandoverLSTMModel


class HandoverTrainer:
    """
    Training pipeline for handover prediction LSTM

    Handles complete training workflow including data validation,
    model training, checkpointing, and metrics logging.
    """

    def __init__(
        self,
        model: Optional[HandoverLSTMModel] = None,
        model_save_path: str = './models/handover_lstm_best.h5',
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        early_stopping_patience: int = 10,
        reduce_lr_patience: int = 5,
        reduce_lr_factor: float = 0.5,
        min_learning_rate: float = 1e-6,
        tensorboard_log_dir: Optional[str] = None
    ):
        """
        Initialize trainer

        Args:
            model: Pre-built model (if None, creates default)
            model_save_path: Path to save best model
            epochs: Maximum number of training epochs
            batch_size: Batch size
            learning_rate: Initial learning rate
            early_stopping_patience: Epochs to wait before early stopping
            reduce_lr_patience: Epochs to wait before reducing LR
            reduce_lr_factor: Factor to reduce LR by
            min_learning_rate: Minimum learning rate
            tensorboard_log_dir: TensorBoard log directory
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow not available. Install with: pip install tensorflow>=2.15.0")

        self.model = model
        self.model_save_path = model_save_path
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.early_stopping_patience = early_stopping_patience
        self.reduce_lr_patience = reduce_lr_patience
        self.reduce_lr_factor = reduce_lr_factor
        self.min_learning_rate = min_learning_rate
        self.tensorboard_log_dir = tensorboard_log_dir

        # Create model directory if doesn't exist
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)

        # Training history
        self.history: Optional[keras.callbacks.History] = None

    def _create_callbacks(self) -> List[Any]:
        """
        Create training callbacks

        Returns:
            List of Keras callbacks
        """
        callbacks = []

        # Early stopping
        if self.early_stopping_patience > 0:
            early_stop = keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=self.early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            )
            callbacks.append(early_stop)

        # Model checkpoint (save best model)
        checkpoint = keras.callbacks.ModelCheckpoint(
            self.model_save_path,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
        callbacks.append(checkpoint)

        # Reduce learning rate on plateau
        if self.reduce_lr_patience > 0:
            reduce_lr = keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=self.reduce_lr_factor,
                patience=self.reduce_lr_patience,
                min_lr=self.min_learning_rate,
                verbose=1
            )
            callbacks.append(reduce_lr)

        # TensorBoard logging
        if self.tensorboard_log_dir:
            log_dir = os.path.join(
                self.tensorboard_log_dir,
                datetime.now().strftime("%Y%m%d-%H%M%S")
            )
            tensorboard = keras.callbacks.TensorBoard(
                log_dir=log_dir,
                histogram_freq=1
            )
            callbacks.append(tensorboard)

        return callbacks

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        verbose: int = 1
    ) -> Dict[str, List[float]]:
        """
        Train model

        Args:
            X_train: Training features (samples, sequence_length, features)
            y_train: Training labels (samples, 2)
            X_val: Validation features
            y_val: Validation labels
            verbose: Verbosity level

        Returns:
            Training history dictionary
        """
        # Create model if not provided
        if self.model is None:
            print("Creating default model...")
            self.model = HandoverLSTMModel(
                sequence_length=X_train.shape[1],
                num_features=X_train.shape[2],
                lstm_units=64,
                num_layers=2,
                dropout_rate=0.2
            )
            self.model.build()
            self.model.compile(optimizer='adam', learning_rate=self.learning_rate)

        # Prepare validation data
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)

        # Create callbacks
        callbacks = self._create_callbacks()

        # Train
        print(f"Training model for up to {self.epochs} epochs...")
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=self.epochs,
            batch_size=self.batch_size,
            verbose=verbose,
            callbacks=callbacks
        )

        # Save training history
        self._save_history()

        # Return history as dictionary
        return self.history.history

    def _save_history(self):
        """Save training history to JSON"""
        if self.history is None:
            return

        history_path = self.model_save_path.rsplit('.', 1)[0] + '_history.json'

        history_dict = {
            key: [float(v) for v in values]
            for key, values in self.history.history.items()
        }

        with open(history_path, 'w') as f:
            json.dump(history_dict, f, indent=2)

        print(f"Training history saved to: {history_path}")

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """
        Evaluate model on test data

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Dictionary of evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        metrics = self.model.evaluate(X_test, y_test, batch_size=self.batch_size)

        return metrics

    def get_training_summary(self) -> Dict[str, Any]:
        """
        Get training summary

        Returns:
            Summary dictionary
        """
        if self.history is None:
            return {}

        history = self.history.history

        summary = {
            'total_epochs': len(history['loss']),
            'best_epoch': int(np.argmin(history['val_loss'])) + 1 if 'val_loss' in history else len(history['loss']),
            'best_val_loss': float(np.min(history['val_loss'])) if 'val_loss' in history else None,
            'final_train_loss': float(history['loss'][-1]),
            'final_val_loss': float(history['val_loss'][-1]) if 'val_loss' in history else None,
            'converged': len(history['loss']) < self.epochs
        }

        return summary


def train_default_model(
    num_samples: int = 10000,
    validation_split: float = 0.2,
    epochs: int = 50,
    model_save_path: str = './models/handover_lstm_best.h5'
) -> Tuple[HandoverTrainer, Dict[str, Any]]:
    """
    Train model with default configuration

    Args:
        num_samples: Number of training samples to generate
        validation_split: Validation split ratio
        epochs: Training epochs
        model_save_path: Path to save model

    Returns:
        Trainer instance and training summary
    """
    from ml_handover.data_generator import HandoverDataGenerator

    print("Generating training data...")
    generator = HandoverDataGenerator(
        num_samples=num_samples,
        sequence_length=10,
        use_mock_data=True,
        augment_data=True,
        random_seed=42
    )

    X_train, X_val, y_train, y_val = generator.get_train_val_split(
        validation_split=validation_split
    )

    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Validation set: {X_val.shape[0]} samples")

    # Create trainer
    trainer = HandoverTrainer(
        model_save_path=model_save_path,
        epochs=epochs,
        batch_size=32,
        learning_rate=0.001,
        early_stopping_patience=10
    )

    # Train
    history = trainer.train(X_train, y_train, X_val, y_val)

    # Get summary
    summary = trainer.get_training_summary()

    print("\n" + "=" * 70)
    print("Training Summary:")
    print("=" * 70)
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print("=" * 70)

    return trainer, summary


if __name__ == '__main__':
    print("Handover LSTM Trainer - Test Mode")
    print("=" * 70)

    # Train model
    trainer, summary = train_default_model(
        num_samples=1000,  # Small for testing
        epochs=10,
        model_save_path='./models/test_model.h5'
    )

    print("\nTraining complete!")
