"""
NTN-Aware xApps Package
Intelligent xApps for Non-Terrestrial Network optimization in O-RAN
"""

from .ntn_handover_xapp import NTNHandoverXApp, UEHandoverContext, HandoverDecision
from .ntn_power_control_xapp import NTNPowerControlXApp, UEPowerState, PowerAdjustmentRecord, PowerControlMode

__all__ = [
    'NTNHandoverXApp',
    'UEHandoverContext',
    'HandoverDecision',
    'NTNPowerControlXApp',
    'UEPowerState',
    'PowerAdjustmentRecord',
    'PowerControlMode'
]

__version__ = '1.0.0'
__author__ = 'Agent 3: NTN xApp Developer & Integration Engineer'
