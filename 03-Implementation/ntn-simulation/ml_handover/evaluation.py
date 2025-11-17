#!/usr/bin/env python3
"""
Handover Prediction Evaluation
===============================

Comprehensive evaluation comparing ML-based handover prediction
against baseline orbital mechanics approach.

Metrics:
- Accuracy (MAE, RMSE, MAPE)
- Statistical significance (t-test, p-value)
- Improvement over baseline
- Confusion matrices
- Performance benchmarks

Author: ML/Deep Learning Specialist
Date: 2025-11-17
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class EvaluationResults:
    """Evaluation results container"""
    mae: float
    rmse: float
    mape: float
    accuracy_percent: float
    avg_error: float
    std_error: float
    median_error: float
    max_error: float


class HandoverEvaluator:
    """
    Evaluate handover prediction performance

    Compares ML-based predictions against baseline and
    computes comprehensive performance metrics.
    """

    def __init__(self):
        """Initialize evaluator"""
        self.results: Optional[Dict[str, Any]] = None

    def compute_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute prediction metrics

        Args:
            y_true: True values (samples, 2) [time, confidence]
            y_pred: Predicted values (samples, 2)

        Returns:
            Dictionary of metrics
        """
        # Focus on time to handover (first column)
        true_time = y_true[:, 0]
        pred_time = y_pred[:, 0]

        # Mean Absolute Error
        mae = np.mean(np.abs(true_time - pred_time))

        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((true_time - pred_time) ** 2))

        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((true_time - pred_time) / (true_time + 1e-8))) * 100

        # Accuracy (within threshold)
        threshold = 0.1  # 10% of normalized range
        correct = np.sum(np.abs(true_time - pred_time) < threshold)
        accuracy_percent = (correct / len(true_time)) * 100

        # Error statistics
        errors = np.abs(true_time - pred_time)
        avg_error = np.mean(errors)
        std_error = np.std(errors)
        median_error = np.median(errors)
        max_error = np.max(errors)

        metrics = {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'accuracy_percent': float(accuracy_percent),
            'avg_error': float(avg_error),
            'std_error': float(std_error),
            'median_error': float(median_error),
            'max_error': float(max_error)
        }

        # Confidence metrics (second column)
        true_conf = y_true[:, 1]
        pred_conf = y_pred[:, 1]

        metrics['confidence_mae'] = float(np.mean(np.abs(true_conf - pred_conf)))
        metrics['confidence_accuracy'] = float(np.mean(np.abs(true_conf - pred_conf) < 0.1) * 100)

        return metrics

    def compare_with_baseline(
        self,
        ml_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Compare ML performance with baseline

        Args:
            ml_metrics: ML model metrics
            baseline_metrics: Baseline system metrics

        Returns:
            Comparison results
        """
        comparison = {}

        # Calculate improvements
        for key in ml_metrics:
            if key in baseline_metrics:
                ml_val = ml_metrics[key]
                baseline_val = baseline_metrics[key]

                # Calculate improvement
                if baseline_val != 0:
                    improvement_pct = ((baseline_val - ml_val) / baseline_val) * 100

                    # For accuracy metrics, higher is better
                    if 'accuracy' in key.lower():
                        improvement_pct = ((ml_val - baseline_val) / baseline_val) * 100

                    comparison[f'{key}_improvement'] = improvement_pct

        # Specific comparisons for handover metrics
        if 'accuracy_percent' in ml_metrics and 'accuracy_percent' in baseline_metrics:
            comparison['accuracy_improvement'] = ml_metrics['accuracy_percent'] - baseline_metrics['accuracy_percent']

        if 'avg_interruption_ms' in ml_metrics and 'avg_interruption_ms' in baseline_metrics:
            improvement = baseline_metrics['avg_interruption_ms'] - ml_metrics['avg_interruption_ms']
            reduction_pct = (improvement / baseline_metrics['avg_interruption_ms']) * 100
            comparison['interruption_reduction'] = improvement
            comparison['interruption_reduction_percent'] = reduction_pct

        if 'prediction_horizon_sec' in ml_metrics and 'prediction_horizon_sec' in baseline_metrics:
            improvement = ml_metrics['prediction_horizon_sec'] - baseline_metrics['prediction_horizon_sec']
            improvement_pct = (improvement / baseline_metrics['prediction_horizon_sec']) * 100
            comparison['prediction_horizon_improvement'] = improvement
            comparison['prediction_horizon_improvement_percent'] = improvement_pct

        return comparison

    def test_statistical_significance(
        self,
        ml_results: np.ndarray,
        baseline_results: np.ndarray,
        alpha: float = 0.05
    ) -> float:
        """
        Test statistical significance using t-test

        Args:
            ml_results: ML model results array
            baseline_results: Baseline results array
            alpha: Significance level

        Returns:
            p-value
        """
        # Perform paired t-test
        if len(ml_results) == len(baseline_results):
            # Paired t-test (same samples)
            t_stat, p_value = stats.ttest_rel(ml_results, baseline_results)
        else:
            # Independent t-test
            t_stat, p_value = stats.ttest_ind(ml_results, baseline_results)

        return float(p_value)

    def generate_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        threshold: float = 0.1
    ) -> np.ndarray:
        """
        Generate confusion matrix for handover predictions

        Args:
            y_true: True values
            y_pred: Predicted values
            threshold: Error threshold for "correct" classification

        Returns:
            Confusion matrix (2x2)
        """
        errors = np.abs(y_true[:, 0] - y_pred[:, 0])

        # Classify predictions
        true_positive = np.sum((errors < threshold) & (y_true[:, 0] < 0.5))  # Correct early handover
        false_positive = np.sum((errors >= threshold) & (y_true[:, 0] < 0.5))  # Incorrect early handover
        true_negative = np.sum((errors < threshold) & (y_true[:, 0] >= 0.5))  # Correct late handover
        false_negative = np.sum((errors >= threshold) & (y_true[:, 0] >= 0.5))  # Incorrect late handover

        confusion_matrix = np.array([
            [true_positive, false_positive],
            [false_negative, true_negative]
        ])

        return confusion_matrix

    def evaluate_full_pipeline(
        self,
        y_true: np.ndarray,
        y_pred_ml: np.ndarray,
        y_pred_baseline: np.ndarray
    ) -> Dict[str, Any]:
        """
        Full evaluation pipeline

        Args:
            y_true: Ground truth
            y_pred_ml: ML predictions
            y_pred_baseline: Baseline predictions

        Returns:
            Complete evaluation results
        """
        # Compute ML metrics
        ml_metrics = self.compute_metrics(y_true, y_pred_ml)

        # Compute baseline metrics
        baseline_metrics = self.compute_metrics(y_true, y_pred_baseline)

        # Compare
        comparison = self.compare_with_baseline(ml_metrics, baseline_metrics)

        # Statistical significance
        ml_errors = np.abs(y_true[:, 0] - y_pred_ml[:, 0])
        baseline_errors = np.abs(y_true[:, 0] - y_pred_baseline[:, 0])
        p_value = self.test_statistical_significance(ml_errors, baseline_errors)

        # Confusion matrices
        ml_confusion = self.generate_confusion_matrix(y_true, y_pred_ml)
        baseline_confusion = self.generate_confusion_matrix(y_true, y_pred_baseline)

        results = {
            'ml_metrics': ml_metrics,
            'baseline_metrics': baseline_metrics,
            'comparison': comparison,
            'p_value': p_value,
            'statistically_significant': p_value < 0.05,
            'ml_confusion_matrix': ml_confusion.tolist(),
            'baseline_confusion_matrix': baseline_confusion.tolist()
        }

        self.results = results

        return results

    def print_summary(self):
        """Print evaluation summary"""
        if self.results is None:
            print("No evaluation results available")
            return

        print("\n" + "=" * 80)
        print("ML-BASED HANDOVER PREDICTION - EVALUATION SUMMARY")
        print("=" * 80)

        print("\nML Model Performance:")
        print("-" * 80)
        ml_metrics = self.results['ml_metrics']
        print(f"  Accuracy: {ml_metrics['accuracy_percent']:.2f}%")
        print(f"  MAE: {ml_metrics['mae']:.4f}")
        print(f"  RMSE: {ml_metrics['rmse']:.4f}")
        print(f"  MAPE: {ml_metrics['mape']:.2f}%")
        print(f"  Confidence Accuracy: {ml_metrics['confidence_accuracy']:.2f}%")

        print("\nBaseline Performance:")
        print("-" * 80)
        baseline_metrics = self.results['baseline_metrics']
        print(f"  Accuracy: {baseline_metrics['accuracy_percent']:.2f}%")
        print(f"  MAE: {baseline_metrics['mae']:.4f}")
        print(f"  RMSE: {baseline_metrics['rmse']:.4f}")
        print(f"  MAPE: {baseline_metrics['mape']:.2f}%")

        print("\nComparison (ML vs Baseline):")
        print("-" * 80)
        comparison = self.results['comparison']
        for key, value in comparison.items():
            if 'improvement' in key or 'reduction' in key:
                print(f"  {key}: {value:+.2f}{'%' if 'percent' in key else ''}")

        print("\nStatistical Significance:")
        print("-" * 80)
        print(f"  p-value: {self.results['p_value']:.6f}")
        print(f"  Significant (p<0.05): {self.results['statistically_significant']}")

        print("\n" + "=" * 80)


if __name__ == '__main__':
    print("Handover Evaluator - Test Mode")
    print("=" * 70)

    # Create mock data
    n_samples = 1000

    # Ground truth
    y_true = np.random.rand(n_samples, 2)
    y_true[:, 0] = y_true[:, 0]  # Time to handover (normalized)
    y_true[:, 1] = 0.8 + 0.2 * np.random.rand(n_samples)  # High confidence

    # ML predictions (better than baseline)
    y_pred_ml = y_true + np.random.normal(0, 0.05, (n_samples, 2))
    y_pred_ml = np.clip(y_pred_ml, 0, 1)

    # Baseline predictions (worse)
    y_pred_baseline = y_true + np.random.normal(0, 0.1, (n_samples, 2))
    y_pred_baseline = np.clip(y_pred_baseline, 0, 1)

    # Evaluate
    evaluator = HandoverEvaluator()
    results = evaluator.evaluate_full_pipeline(y_true, y_pred_ml, y_pred_baseline)

    # Print summary
    evaluator.print_summary()

    print("\nTest completed!")
