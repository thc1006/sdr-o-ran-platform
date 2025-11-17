"""
E2SM-NTN Extension Package
===========================

E2 Service Model for Non-Terrestrial Networks (NTN)

This package provides:
1. E2SM-NTN service model implementation
2. NTN-E2 bridge for OpenNTN integration
3. NTN-specific KPM definitions
4. E2 message formats for satellite communications

Components:
- e2sm_ntn.py: Core E2SM-NTN service model
- ntn_e2_bridge.py: Bridge between OpenNTN and E2 Interface
- test_e2sm_ntn.py: Comprehensive test scenarios

Documentation:
- E2SM-NTN-SPECIFICATION.md: Service model specification
- E2SM-NTN-ARCHITECTURE.md: Architecture and data flow diagrams
"""

__version__ = "1.0.0"
__author__ = "E2SM-NTN Service Model Architect"

from .e2sm_ntn import (
    E2SM_NTN,
    OrbitType,
    NTNEventTrigger,
    NTNControlAction,
    SatelliteMetrics,
    ChannelQuality,
    NTNImpairments,
    LinkBudget,
    HandoverPrediction,
    PerformanceMetrics,
    NTNIndicationMessage,
    NTNIndicationHeader,
    NTNControlMessage
)

from .ntn_e2_bridge import (
    NTN_E2_Bridge,
    UEContext
)

__all__ = [
    # Main classes
    'E2SM_NTN',
    'NTN_E2_Bridge',

    # Enums
    'OrbitType',
    'NTNEventTrigger',
    'NTNControlAction',

    # Data classes
    'SatelliteMetrics',
    'ChannelQuality',
    'NTNImpairments',
    'LinkBudget',
    'HandoverPrediction',
    'PerformanceMetrics',
    'UEContext',

    # Message types
    'NTNIndicationMessage',
    'NTNIndicationHeader',
    'NTNControlMessage'
]
