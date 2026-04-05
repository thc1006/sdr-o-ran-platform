#!/usr/bin/env python3
"""
Baseline Comparison Fairness Tests (Task #9)
=============================================
Detects hardcoded bias in comparative_simulation.py.

The gold standard for a fair comparison:
  If reactive_system == predictive_system (same algorithm),
  the measured "improvement" must be statistically indistinguishable from 0%.

Previously observed bias patterns:
  1. RSRP uses non-physics formula: rsrp = -70 - (90 - elevation) * 0.5
  2. Throughput hardcoded: reactive → 0.85x, predictive → 0.95x on handover
  3. Rain fade hardcoded: reactive → 0.7x, predictive → 0.9x at >5 dB
  4. Latency hardcoded: reactive +50 ms, predictive +10 ms on handover
  5. Packet loss hardcoded: reactive 8%, predictive 1% in rain

These are not measured outcomes — they are predetermined results.

Author: thc1006
Date: 2026-04-05
"""

import pytest
import os

# Path to comparative_simulation.py
COMP_SIM_PATH = os.path.join(
    os.path.dirname(__file__),
    '../../03-Implementation/ntn-simulation/baseline/comparative_simulation.py'
)


# =============================================================================
# Substring matching: detect hardcoded bias patterns directly in source code
# =============================================================================

@pytest.fixture(scope='module')
def comp_sim_source():
    """Return source code of comparative_simulation.py as a string."""
    with open(COMP_SIM_PATH, 'r') as f:
        return f.read()


class TestHardcodedBiasPatterns:
    """
    Detect hardcoded if-system_type-reactive-vs-predictive branches.

    These branches guarantee the paper result before any experiment runs.
    They must be replaced with actual algorithm-driven outcomes.
    """

    def test_no_hardcoded_reactive_throughput_penalty(self, comp_sim_source):
        """
        The line `if system_type == 'reactive': base_throughput *= 0.85` must
        not exist. Throughput degradation should come from actual algorithm
        performance, not a predetermined multiplier.
        """
        # Check for the specific pattern: reactive throughput bias
        assert 'base_throughput *= 0.85' not in comp_sim_source, (
            "HARDCODED BIAS DETECTED: 'base_throughput *= 0.85' found in "
            "comparative_simulation.py. This gives reactive system a fixed 15% "
            "throughput penalty regardless of algorithm behavior. "
            "Remove and replace with measured outcomes."
        )

    def test_no_hardcoded_predictive_throughput_bonus(self, comp_sim_source):
        """
        The line `base_throughput *= 0.95` as a predictive-system bonus
        must not exist.
        """
        # The 0.95x is only used for predictive in handover context
        # We check for the asymmetric pair
        assert 'base_throughput *= 0.95' not in comp_sim_source, (
            "HARDCODED BIAS DETECTED: 'base_throughput *= 0.95' gives predictive "
            "system a guaranteed throughput advantage. Replace with measured data."
        )

    def test_no_hardcoded_reactive_rain_penalty(self, comp_sim_source):
        """
        'base_throughput *= 0.7' as a rain penalty only for reactive system
        must not exist.
        """
        assert 'base_throughput *= 0.7' not in comp_sim_source, (
            "HARDCODED BIAS DETECTED: 'base_throughput *= 0.7' hardcodes that "
            "reactive system loses 30% throughput in rain — without any actual "
            "simulation of algorithm behavior."
        )

    def test_no_hardcoded_latency_asymmetry(self, comp_sim_source):
        """
        Latency penalty 'base_latency += 50' for reactive vs 'base_latency += 10'
        for predictive must not be hardcoded.
        """
        assert 'base_latency += 50' not in comp_sim_source, (
            "HARDCODED BIAS DETECTED: 'base_latency += 50' forces reactive system "
            "to have 50 ms extra handover latency as a constant, not a measured value."
        )
        assert 'base_latency += 10' not in comp_sim_source, (
            "HARDCODED BIAS DETECTED: 'base_latency += 10' forces predictive system "
            "to always have only 10 ms extra latency, regardless of algorithm."
        )

    def test_no_hardcoded_packet_loss_asymmetry(self, comp_sim_source):
        """
        Packet loss 'base_loss = 0.08' for reactive vs 'base_loss = 0.01' for
        predictive in rain must not be hardcoded.
        """
        assert 'base_loss = 0.08' not in comp_sim_source, (
            "HARDCODED BIAS DETECTED: 'base_loss = 0.08' hardcodes 8% packet loss "
            "for reactive in rain — this is a predetermined result, not a measurement."
        )
        assert 'base_loss = 0.01' not in comp_sim_source, (
            "HARDCODED BIAS DETECTED: 'base_loss = 0.01' hardcodes 1% packet loss "
            "for predictive in rain — this is a predetermined result, not a measurement."
        )


class TestRSRPPhysics:
    """
    RSRP in comparative_simulation.py must use a physics-based formula,
    not the linear heuristic: rsrp = -70.0 - (90 - elevation) * 0.5
    """

    def test_no_hardcoded_rsrp_formula(self, comp_sim_source):
        """
        The non-physical formula `rsrp = -70.0 - (90 - elevation) * 0.5`
        must not exist.

        This formula gives -70 dBm at 90° and -82.5 dBm at 45°, regardless
        of slant range, frequency, Tx power, or antenna gain. It's a linear
        approximation with no physical basis.
        """
        assert 'rsrp = -70.0 - (90 - elevation)' not in comp_sim_source, (
            "NON-PHYSICAL RSRP FORMULA DETECTED: "
            "'rsrp = -70.0 - (90 - elevation) * 0.5' ignores slant range, "
            "frequency, Tx power, and antenna gain. "
            "Replace with: RSRP = Tx_power + antenna_gain - FSPL - losses"
        )

    def test_rsrp_formula_uses_fspl(self, comp_sim_source):
        """
        The RSRP calculation must use FSPL (free space path loss) which
        requires both frequency and distance/slant_range.
        """
        # If we see 'fspl_db' in the context of RSRP calculation, that's good
        # This is a positive assertion — fspl_db variable must be in the file
        assert 'fspl_db' in comp_sim_source, (
            "comparative_simulation.py must compute FSPL to calculate RSRP. "
            "Use: fspl_db = 92.45 + 20*log10(freq_ghz) + 20*log10(slant_range_km)"
        )


class TestFairnessWithIdenticalAlgorithms:
    """
    If both systems use the same decision algorithm, their measured performance
    must be statistically indistinguishable.

    This is the null hypothesis check: a fair comparison framework must not
    produce systematic "improvements" when both systems are identical.
    """

    def test_no_system_type_conditional_in_metrics(self, comp_sim_source):
        """
        _create_metrics_record must not branch on system_type to set
        performance metrics. The system's actual decisions should determine
        metrics, not labels.

        Checks for the pattern: if system_type == 'reactive': [performance penalty]
        """
        # Count occurrences of system_type checks in metrics calculation context
        # We expect 0 occurrences that directly set performance values
        lines = comp_sim_source.split('\n')
        bias_lines = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if ('system_type' in stripped and
                    ('*= 0.' in stripped or '+= 50' in stripped or
                     '+= 10' in stripped or '= 0.08' in stripped or
                     '= 0.01' in stripped)):
                bias_lines.append(f"Line {i}: {stripped}")

        assert len(bias_lines) == 0, (
            f"Found {len(bias_lines)} hardcoded system_type performance branches:\n"
            + "\n".join(bias_lines) +
            "\n\nThese guarantee predetermined results. Remove all system_type-based "
            "performance modifiers from _create_metrics_record."
        )

    def test_metrics_record_inputs_determine_outputs(self):
        """
        _create_metrics_record must produce the same distribution for
        both system types given the same ntn_metrics and actions inputs.
        The system_type label must not change the output values.

        Calls _create_metrics_record twice with the same inputs and a fixed
        seed, once with system_type='reactive' and once with 'predictive',
        and asserts the numeric outputs are close.
        """
        import importlib
        import sys
        import types
        import unittest.mock as mock
        import numpy as np
        from datetime import datetime

        sim_dir = os.path.join(
            os.path.dirname(__file__),
            '../../03-Implementation/ntn-simulation'
        )
        abs_sim_dir = os.path.abspath(sim_dir)

        # Stub out heavy transitive dependencies so we can import
        # comparative_simulation without requiring sgp4, etc.
        stubs = {}
        for mod_name in [
            'sgp4', 'sgp4.api',
            'orbit_propagation', 'orbit_propagation.sgp4_propagator',
            'orbit_propagation.tle_manager',
            'orbit_propagation.constellation_simulator',
            'baseline.reactive_system', 'baseline.predictive_system',
        ]:
            stubs[mod_name] = types.ModuleType(mod_name)

        # Provide dummy classes expected at import time
        stubs['orbit_propagation'].TLEManager = type('TLEManager', (), {})
        stubs['orbit_propagation.tle_manager'].TLEManager = stubs['orbit_propagation'].TLEManager
        stubs['orbit_propagation'].SGP4Propagator = type('SGP4Propagator', (), {})
        stubs['orbit_propagation.sgp4_propagator'].SGP4Propagator = stubs['orbit_propagation'].SGP4Propagator
        stubs['orbit_propagation'].ConstellationSimulator = type('ConstellationSimulator', (), {})
        stubs['orbit_propagation.constellation_simulator'].ConstellationSimulator = stubs['orbit_propagation'].ConstellationSimulator
        stubs['baseline.reactive_system'].ReactiveNTNSystem = type('ReactiveNTNSystem', (), {})
        stubs['baseline.predictive_system'].PredictiveNTNSystem = type('PredictiveNTNSystem', (), {})

        with mock.patch.dict(sys.modules, stubs):
            if abs_sim_dir not in sys.path:
                sys.path.insert(0, abs_sim_dir)
            # Force a fresh import
            mod = importlib.import_module('baseline.comparative_simulation')
            ComparativeSimulator = mod.ComparativeSimulator

        simulator = ComparativeSimulator.__new__(ComparativeSimulator)
        ntn_metrics = {
            'satellite_metrics': {'elevation_angle': 45.0, 'slant_range_km': 800.0},
            'channel_quality': {'rsrp': -90.0, 'sinr': 12.0},
            'link_budget': {'tx_power_dbm': 20.0, 'link_margin_db': 5.0},
            'ntn_impairments': {'rain_attenuation_db': 2.0},
        }
        actions = {}  # no handover or power events
        ts = datetime(2026, 1, 1, 0, 0, 0)

        np.random.seed(42)
        reactive = simulator._create_metrics_record(
            'UE-0001', 'test', 'reactive', ntn_metrics, actions, ts
        )
        np.random.seed(42)
        predictive = simulator._create_metrics_record(
            'UE-0001', 'test', 'predictive', ntn_metrics, actions, ts
        )

        assert abs(reactive.throughput_mbps - predictive.throughput_mbps) < 1e-6, (
            f"throughput differs: reactive={reactive.throughput_mbps}, "
            f"predictive={predictive.throughput_mbps}"
        )
        assert abs(reactive.latency_ms - predictive.latency_ms) < 1e-6, (
            f"latency differs: reactive={reactive.latency_ms}, "
            f"predictive={predictive.latency_ms}"
        )
        assert abs(reactive.packet_loss_rate - predictive.packet_loss_rate) < 1e-6, (
            f"packet_loss differs: reactive={reactive.packet_loss_rate}, "
            f"predictive={predictive.packet_loss_rate}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
