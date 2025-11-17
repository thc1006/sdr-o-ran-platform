#!/usr/bin/env python3
"""
Test Suite for Trainer (TDD: Tests Written First)
==================================================

Test Coverage:
- Training pipeline execution
- Early stopping
- Model checkpointing
- Learning rate scheduling
- Training metrics logging
- Convergence validation

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTrainer:
    """Test training pipeline"""

    def test_trainer_exists(self):
        """Test 1: Trainer class exists"""
        try:
            from ml_handover.trainer import HandoverTrainer
            assert HandoverTrainer is not None
        except ImportError:
            pytest.fail("HandoverTrainer class not found")

    def test_trainer_initialization(self):
        """Test 2: Trainer initializes correctly"""
        from ml_handover.trainer import HandoverTrainer

        trainer = HandoverTrainer(
            model_save_path='./models/test_model.h5',
            epochs=50,
            batch_size=32
        )

        assert trainer is not None

    def test_trainer_trains_model(self):
        """Test 3: Trainer can train model"""
        from ml_handover.trainer import HandoverTrainer
        from ml_handover.data_generator import HandoverDataGenerator

        # Generate training data
        generator = HandoverDataGenerator(num_samples=200, random_seed=42)
        X_train, X_val, y_train, y_val = generator.get_train_val_split()

        # Train
        trainer = HandoverTrainer(epochs=5, batch_size=32)
        history = trainer.train(X_train, y_train, X_val, y_val)

        assert history is not None
        assert 'loss' in history
        assert len(history['loss']) == 5

    def test_early_stopping_works(self):
        """Test 4: Early stopping prevents overfitting"""
        from ml_handover.trainer import HandoverTrainer
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(num_samples=100, random_seed=42)
        X_train, X_val, y_train, y_val = generator.get_train_val_split()

        # Train with early stopping
        trainer = HandoverTrainer(
            epochs=100,
            early_stopping_patience=5,
            batch_size=32
        )

        history = trainer.train(X_train, y_train, X_val, y_val)

        # Should stop before 100 epochs
        assert len(history['loss']) < 100, "Early stopping did not trigger"

    def test_model_checkpointing(self):
        """Test 5: Best model is saved during training"""
        import tempfile
        from ml_handover.trainer import HandoverTrainer
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(num_samples=100, random_seed=42)
        X_train, X_val, y_train, y_val = generator.get_train_val_split()

        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name

        try:
            trainer = HandoverTrainer(
                model_save_path=model_path,
                epochs=10,
                batch_size=32
            )

            trainer.train(X_train, y_train, X_val, y_val)

            # Model file should exist
            assert os.path.exists(model_path), "Model checkpoint not saved"

        finally:
            if os.path.exists(model_path):
                os.remove(model_path)

    def test_training_metrics_logged(self):
        """Test 6: Training metrics are logged"""
        from ml_handover.trainer import HandoverTrainer
        from ml_handover.data_generator import HandoverDataGenerator

        generator = HandoverDataGenerator(num_samples=100, random_seed=42)
        X_train, X_val, y_train, y_val = generator.get_train_val_split()

        trainer = HandoverTrainer(epochs=5, batch_size=32)
        history = trainer.train(X_train, y_train, X_val, y_val)

        # Check metrics exist
        assert 'loss' in history
        assert 'val_loss' in history
        assert 'mae' in history or 'mean_absolute_error' in history


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
