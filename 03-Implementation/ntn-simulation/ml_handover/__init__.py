"""
ML-Based Handover Prediction for LEO Satellite Networks
========================================================

This module implements LSTM-based handover prediction to improve upon
the baseline orbital mechanics approach (99% success rate).

Target Improvement: 5-10% accuracy increase, 50% longer prediction horizon

Components:
- data_generator.py: Generate training data from orbital mechanics
- lstm_model.py: LSTM neural network architecture
- trainer.py: Model training pipeline
- predictor.py: Real-time inference
- evaluation.py: Performance comparison vs. baseline
- ml_handover_xapp.py: Integration with O-RAN xApp

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

__version__ = "1.0.0"
