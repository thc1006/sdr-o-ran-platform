"""
OpenNTN Integration Package
============================

High-level wrappers for OpenNTN 3GPP TR38.811 channel models for SDR-O-RAN platform.

Provides simplified interfaces for LEO, MEO, and GEO satellite channel modeling.
"""

__version__ = "1.0.0"
__author__ = "OpenNTN Integration Specialist"

from .leo_channel import LEOChannelModel
from .meo_channel import MEOChannelModel
from .geo_channel import GEOChannelModel

__all__ = [
    'LEOChannelModel',
    'MEOChannelModel',
    'GEOChannelModel'
]
