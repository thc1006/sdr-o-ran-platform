#!/usr/bin/env python3
"""
RIC State Data Structure for DRL Training
Separated module to enable proper pickling for multiprocessing

Author: thc1006@ieee.org
Date: 2025-11-10
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass(frozen=True)
class RICState:
    """RIC environment state from E2 KPM indications

    frozen=True ensures immutability for safe multiprocessing
    """
    # UE metrics
    ue_throughput_dl_mbps: float
    ue_throughput_ul_mbps: float
    ue_buffer_status_dl_kb: float
    ue_buffer_status_ul_kb: float

    # Cell metrics
    prb_utilization_dl_percent: float
    prb_utilization_ul_percent: float
    active_ues: int

    # Radio quality
    cqi_dl: float  # Channel Quality Indicator (0-15)
    rsrp_dbm: float  # Reference Signal Received Power
    rsrq_db: float  # Reference Signal Received Quality
    sinr_db: float  # Signal-to-Interference-plus-Noise Ratio

    # Latency
    e2e_latency_ms: float
    rlc_latency_ms: float
    mac_latency_ms: float

    # Block Error Rate
    bler_dl: float
    bler_ul: float

    # Timestamp
    timestamp_ns: int

    def __getstate__(self) -> Dict:
        """Custom serialization for pickling"""
        return asdict(self)

    def __setstate__(self, state: Dict):
        """Custom deserialization for unpickling"""
        # Since dataclass is frozen, we need to use object.__setattr__
        for key, value in state.items():
            object.__setattr__(self, key, value)

    def to_numpy(self):
        """Convert to numpy array for DRL input"""
        import numpy as np
        return np.array([
            self.ue_throughput_dl_mbps / 100.0,  # Normalize to ~[0, 1]
            self.ue_throughput_ul_mbps / 50.0,
            self.prb_utilization_dl_percent / 100.0,
            self.prb_utilization_ul_percent / 100.0,
            self.active_ues / 10.0,
            self.cqi_dl / 15.0,
            self.rsrp_dbm / -70.0,  # Typical range: -140 to -70 dBm
            self.sinr_db / 30.0,    # Typical range: -10 to 30 dB
            self.e2e_latency_ms / 100.0,
            self.bler_dl * 10.0,  # Typical: 0.001 - 0.1
            self.bler_ul * 10.0
        ], dtype=np.float32)
