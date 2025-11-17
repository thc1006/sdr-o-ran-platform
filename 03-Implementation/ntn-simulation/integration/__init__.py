"""
Integration Test Suite for NTN-O-RAN Platform
==============================================

This package contains integration tests that verify API harmonization
across all Week 2 components.

Test-Driven Development (TDD) Approach:
1. Write tests FIRST to define expected APIs
2. Run tests to identify API mismatches
3. Fix implementations to match test expectations
4. Verify all tests pass

Test Modules:
- test_channel_models: OpenNTN channel model APIs
- test_e2sm_ntn: E2SM-NTN service model APIs
- test_sgp4: SGP4 orbit propagator APIs
- test_weather: ITU-R P.618 weather APIs
- test_optimizations: Optimized component APIs
- test_baseline: Baseline system APIs
- test_e2e: End-to-end integration

Author: Software Integration Specialist
Date: 2025-11-17
"""

__version__ = "1.0.0"
__all__ = [
    "test_channel_models",
    "test_e2sm_ntn",
    "test_sgp4",
    "test_weather",
    "test_optimizations",
    "test_baseline",
    "test_e2e"
]
