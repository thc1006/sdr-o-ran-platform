#!/usr/bin/env python3
"""
Reactive (Traditional) NTN System - Baseline Implementation
===========================================================

Traditional reactive approach for NTN management - used as baseline for comparison.

Characteristics:
- Threshold-based handover (reactive to RSRP degradation)
- Reactive power control (responds to SINR deviation)
- No prediction or preparation
- No weather awareness
- No satellite geometry consideration

This represents the state-of-the-art before our predictive NTN-aware approach.

Author: Baseline Comparison & Research Validation Specialist
Date: 2025-11-17
"""

import asyncio
import time
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class ReactiveHandoverEvent:
    """Record of reactive handover"""
    timestamp: float
    ue_id: str
    trigger: str
    rsrp_db: float
    source_satellite: str
    target_satellite: str
    success: bool
    execution_time_ms: float
    data_interruption_ms: float


@dataclass
class ReactivePowerEvent:
    """Record of reactive power adjustment"""
    timestamp: float
    ue_id: str
    old_power_dbm: float
    new_power_dbm: float
    adjustment_db: float
    sinr_db: float
    reason: str


class ReactiveHandoverManager:
    """
    Traditional Reactive Handover Manager

    Implements threshold-based handover without prediction.
    Triggers handover only when RSRP drops below threshold.

    Drawbacks:
    - No preparation time
    - Emergency handovers (high failure rate)
    - Long data interruption
    - No satellite geometry awareness
    """

    def __init__(
        self,
        rsrp_threshold_dbm: float = -110.0,
        hysteresis_db: float = 3.0,
        handover_threshold_db: Optional[float] = None  # Deprecated, for backward compatibility
    ):
        """
        Initialize reactive handover manager

        Args:
            rsrp_threshold_dbm: RSRP threshold for handover trigger (dBm)
            hysteresis_db: Hysteresis to prevent ping-pong
            handover_threshold_db: DEPRECATED - Use rsrp_threshold_dbm instead

        Note:
            API v1.1: Parameter renamed from handover_threshold_db to rsrp_threshold_dbm
            for consistency with validation script. Old parameter still supported.
        """
        # Support backward compatibility - use old parameter if provided
        if handover_threshold_db is not None:
            import warnings
            warnings.warn(
                "Parameter 'handover_threshold_db' is deprecated. "
                "Use 'rsrp_threshold_dbm' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self.handover_threshold = handover_threshold_db
        else:
            self.handover_threshold = rsrp_threshold_dbm

        self.hysteresis = hysteresis_db

        # State tracking
        self.ue_rsrp: Dict[str, float] = {}
        self.ue_satellite: Dict[str, str] = {}
        self.handover_events: List[ReactiveHandoverEvent] = []

        # Statistics
        self.stats = {
            'total_handovers': 0,
            'successful_handovers': 0,
            'failed_handovers': 0,
            'emergency_handovers': 0,
            'total_interruption_time_ms': 0.0,
            'avg_interruption_ms': 0.0
        }

        print(f"[Reactive-HO] Initialized: threshold={self.handover_threshold} dBm, hysteresis={hysteresis_db} dB")

    async def process_measurement(
        self,
        ue_id: str,
        current_satellite: str,
        rsrp_db: float,
        available_satellites: List[Tuple[str, float]]  # (sat_id, rsrp)
    ) -> Optional[ReactiveHandoverEvent]:
        """
        Process UE measurement and check if handover needed

        Args:
            ue_id: UE identifier
            current_satellite: Current serving satellite
            rsrp_db: Current RSRP in dB
            available_satellites: List of (satellite_id, rsrp) tuples

        Returns:
            HandoverEvent if handover triggered, None otherwise
        """
        # Update state
        self.ue_rsrp[ue_id] = rsrp_db
        self.ue_satellite[ue_id] = current_satellite

        # Check if RSRP below threshold
        if rsrp_db < self.handover_threshold:
            # EMERGENCY: Link is degrading, trigger reactive handover
            trigger = "EMERGENCY_LOW_RSRP"

            # Select best alternative satellite (highest RSRP)
            if not available_satellites:
                # No alternative - handover will fail
                return await self._execute_handover(
                    ue_id, current_satellite, None, rsrp_db, trigger, will_fail=True
                )

            # Find best satellite
            best_sat, best_rsrp = max(available_satellites, key=lambda x: x[1])

            # Check if better than current + hysteresis
            if best_rsrp > rsrp_db + self.hysteresis:
                return await self._execute_handover(
                    ue_id, current_satellite, best_sat, rsrp_db, trigger
                )

        # Check for better satellite (opportunistic handover)
        if available_satellites:
            best_sat, best_rsrp = max(available_satellites, key=lambda x: x[1])

            # Only handover if significantly better
            if best_rsrp > rsrp_db + self.hysteresis + 5.0:  # Need large margin
                return await self._execute_handover(
                    ue_id, current_satellite, best_sat, rsrp_db, "OPPORTUNISTIC"
                )

        return None

    async def _execute_handover(
        self,
        ue_id: str,
        source_sat: str,
        target_sat: Optional[str],
        rsrp_db: float,
        trigger: str,
        will_fail: bool = False
    ) -> ReactiveHandoverEvent:
        """Execute reactive handover"""
        start_time = time.time()

        # Simulate emergency handover execution
        # Reactive handovers are slower and less reliable

        if will_fail or target_sat is None:
            # Handover fails
            success = False
            execution_time_ms = 100.0  # Fast failure detection
            data_interruption_ms = 500.0  # But link is already lost
        else:
            # Simulate reactive handover (slower, unprepared)
            await asyncio.sleep(0.045)  # 45ms execution time (vs 5ms predictive)

            # Success probability depends on link quality
            # Poor RSRP = higher failure rate
            if rsrp_db < self.handover_threshold - 5:
                success_prob = 0.70  # 70% success in emergency
            elif rsrp_db < self.handover_threshold:
                success_prob = 0.85  # 85% success at threshold
            else:
                success_prob = 0.95  # 95% success when proactive

            success = np.random.random() < success_prob
            execution_time_ms = (time.time() - start_time) * 1000

            # Data interruption (reactive = no preparation)
            if success:
                # Successful but unprepared handover
                data_interruption_ms = np.random.uniform(200, 350)  # 200-350ms
            else:
                # Failed handover - longer interruption
                data_interruption_ms = np.random.uniform(400, 600)  # 400-600ms

        # Create event record
        event = ReactiveHandoverEvent(
            timestamp=time.time(),
            ue_id=ue_id,
            trigger=trigger,
            rsrp_db=rsrp_db,
            source_satellite=source_sat,
            target_satellite=target_sat or "NONE",
            success=success,
            execution_time_ms=execution_time_ms,
            data_interruption_ms=data_interruption_ms
        )

        self.handover_events.append(event)

        # Update statistics
        self.stats['total_handovers'] += 1
        if success:
            self.stats['successful_handovers'] += 1
            self.ue_satellite[ue_id] = target_sat
        else:
            self.stats['failed_handovers'] += 1

        if trigger == "EMERGENCY_LOW_RSRP":
            self.stats['emergency_handovers'] += 1

        self.stats['total_interruption_time_ms'] += data_interruption_ms
        self.stats['avg_interruption_ms'] = (
            self.stats['total_interruption_time_ms'] / self.stats['total_handovers']
        )

        return event

    def get_statistics(self) -> Dict[str, Any]:
        """Get handover statistics"""
        success_rate = (
            self.stats['successful_handovers'] / self.stats['total_handovers'] * 100
            if self.stats['total_handovers'] > 0 else 0.0
        )

        emergency_rate = (
            self.stats['emergency_handovers'] / self.stats['total_handovers'] * 100
            if self.stats['total_handovers'] > 0 else 0.0
        )

        return {
            **self.stats,
            'success_rate_percent': success_rate,
            'emergency_rate_percent': emergency_rate,
            'failure_rate_percent': 100 - success_rate
        }


class ReactivePowerControl:
    """
    Traditional Reactive Power Control

    Adjusts power only in response to SINR deviation from target.
    No prediction, no weather awareness, no geometry consideration.

    Drawbacks:
    - Reactive to link degradation (already lost quality)
    - No weather fade anticipation
    - Inefficient power usage
    - Slow response to rain fades
    """

    def __init__(
        self,
        target_sinr_db: float = 10.0,
        sinr_tolerance_db: float = 3.0,
        max_power_dbm: float = 23.0,
        min_power_dbm: float = 0.0,
        step_size_db: float = 3.0
    ):
        """
        Initialize reactive power control

        Args:
            target_sinr_db: Target SINR
            sinr_tolerance_db: SINR tolerance before adjustment
            max_power_dbm: Maximum transmit power
            min_power_dbm: Minimum transmit power
            step_size_db: Power adjustment step size
        """
        self.target_sinr = target_sinr_db
        self.tolerance = sinr_tolerance_db
        self.max_power = max_power_dbm
        self.min_power = min_power_dbm
        self.step_size = step_size_db

        # State tracking
        self.ue_power: Dict[str, float] = {}
        self.ue_sinr: Dict[str, float] = {}
        self.power_events: List[ReactivePowerEvent] = []

        # Statistics
        self.stats = {
            'total_adjustments': 0,
            'power_increases': 0,
            'power_decreases': 0,
            'total_power_waste_db': 0.0,
            'rain_fade_failures': 0
        }

        print(f"[Reactive-PC] Initialized: target_sinr={target_sinr_db} dB, tolerance=±{sinr_tolerance_db} dB")

    async def process_measurement(
        self,
        ue_id: str,
        current_power_dbm: float,
        sinr_db: float,
        rain_attenuation_db: float = 0.0
    ) -> Optional[ReactivePowerEvent]:
        """
        Process UE measurement and adjust power if needed

        Args:
            ue_id: UE identifier
            current_power_dbm: Current transmit power
            sinr_db: Current SINR
            rain_attenuation_db: Rain attenuation (ignored by reactive)

        Returns:
            PowerEvent if adjustment made, None otherwise
        """
        # Update state
        self.ue_power[ue_id] = current_power_dbm
        self.ue_sinr[ue_id] = sinr_db

        # Calculate SINR deviation
        sinr_deviation = sinr_db - self.target_sinr

        # Check if adjustment needed (reactive threshold-based)
        if abs(sinr_deviation) <= self.tolerance:
            # Within tolerance, no adjustment
            return None

        # Determine adjustment
        if sinr_deviation < -self.tolerance:
            # SINR too low - increase power (reactive)
            adjustment = self.step_size
            reason = "LOW_SINR"
        else:
            # SINR too high - decrease power (reactive)
            adjustment = -self.step_size
            reason = "HIGH_SINR"

        # Apply adjustment
        new_power = np.clip(
            current_power_dbm + adjustment,
            self.min_power,
            self.max_power
        )
        actual_adjustment = new_power - current_power_dbm

        # Note: Reactive system doesn't anticipate rain fades
        # By the time it reacts, link quality is already degraded
        if rain_attenuation_db > 3.0 and adjustment > 0:
            # Rain fade detected AFTER link degradation
            self.stats['rain_fade_failures'] += 1

        # Execute power change
        await asyncio.sleep(0.002)  # 2ms control latency

        # Create event record
        event = ReactivePowerEvent(
            timestamp=time.time(),
            ue_id=ue_id,
            old_power_dbm=current_power_dbm,
            new_power_dbm=new_power,
            adjustment_db=actual_adjustment,
            sinr_db=sinr_db,
            reason=reason
        )

        self.power_events.append(event)
        self.ue_power[ue_id] = new_power

        # Update statistics
        self.stats['total_adjustments'] += 1
        if actual_adjustment > 0:
            self.stats['power_increases'] += 1
        else:
            self.stats['power_decreases'] += 1
            # Track power waste (operating above needed level)
            if sinr_deviation > self.tolerance:
                self.stats['total_power_waste_db'] += abs(actual_adjustment)

        return event

    def get_statistics(self) -> Dict[str, Any]:
        """Get power control statistics"""
        avg_power_waste = (
            self.stats['total_power_waste_db'] / self.stats['power_decreases']
            if self.stats['power_decreases'] > 0 else 0.0
        )

        return {
            **self.stats,
            'avg_power_waste_db': avg_power_waste,
            'rain_fade_mitigation_failures': self.stats['rain_fade_failures']
        }


class ReactiveNTNSystem:
    """
    Complete Reactive NTN System

    Combines reactive handover and power control for baseline comparison.
    Represents traditional approach without prediction or NTN awareness.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize reactive NTN system"""
        config = config or {}

        self.handover_mgr = ReactiveHandoverManager(
            handover_threshold_db=config.get('handover_threshold_db', -100.0),
            hysteresis_db=config.get('hysteresis_db', 3.0)
        )

        self.power_ctrl = ReactivePowerControl(
            target_sinr_db=config.get('target_sinr_db', 10.0),
            sinr_tolerance_db=config.get('sinr_tolerance_db', 3.0),
            step_size_db=config.get('power_step_db', 3.0)
        )

        self.running = False
        self.start_time = time.time()

        print("[Reactive System] Initialized - Traditional threshold-based approach")

    async def process_ue_metrics(
        self,
        ue_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process UE metrics with reactive approach

        Args:
            ue_id: UE identifier
            metrics: Dictionary with satellite_metrics, channel_quality, etc.

        Returns:
            Dictionary with actions taken
        """
        actions = {
            'handover_event': None,
            'power_event': None
        }

        # Extract metrics
        sat_metrics = metrics.get('satellite_metrics', {})
        channel = metrics.get('channel_quality', {})
        link_budget = metrics.get('link_budget', {})
        ntn_impairments = metrics.get('ntn_impairments', {})

        current_satellite = sat_metrics.get('satellite_id', 'UNKNOWN')
        rsrp_db = channel.get('rsrp', -90.0)
        sinr_db = channel.get('sinr', 10.0)
        tx_power = link_budget.get('tx_power_dbm', 20.0)
        rain_atten = ntn_impairments.get('rain_attenuation_db', 0.0)

        # Find available satellites (simulated - would come from measurements)
        # For now, generate 2-3 alternative satellites with random RSRP
        available_sats = [
            (f"SAT-ALT-{i}", rsrp_db + np.random.uniform(-10, 5))
            for i in range(np.random.randint(2, 4))
        ]

        # Process handover (reactive)
        handover_event = await self.handover_mgr.process_measurement(
            ue_id, current_satellite, rsrp_db, available_sats
        )
        actions['handover_event'] = handover_event

        # Process power control (reactive)
        power_event = await self.power_ctrl.process_measurement(
            ue_id, tx_power, sinr_db, rain_atten
        )
        actions['power_event'] = power_event

        return actions

    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        ho_stats = self.handover_mgr.get_statistics()
        pc_stats = self.power_ctrl.get_statistics()

        return {
            'system_type': 'REACTIVE',
            'uptime_seconds': time.time() - self.start_time,
            'handover_stats': ho_stats,
            'power_control_stats': pc_stats
        }

    def print_summary(self):
        """Print performance summary"""
        stats = self.get_comprehensive_statistics()

        print("\n" + "="*70)
        print("Reactive (Traditional) NTN System - Performance Summary")
        print("="*70)
        print(f"System Type: {stats['system_type']}")
        print(f"Uptime: {stats['uptime_seconds']:.1f} seconds")

        print(f"\nHandover Performance:")
        ho = stats['handover_stats']
        print(f"  Total: {ho['total_handovers']}")
        print(f"  Success Rate: {ho['success_rate_percent']:.1f}%")
        print(f"  Emergency Handovers: {ho['emergency_handovers']} ({ho['emergency_rate_percent']:.1f}%)")
        print(f"  Avg Interruption: {ho['avg_interruption_ms']:.1f} ms")

        print(f"\nPower Control Performance:")
        pc = stats['power_control_stats']
        print(f"  Total Adjustments: {pc['total_adjustments']}")
        print(f"  Power Increases: {pc['power_increases']}")
        print(f"  Power Decreases: {pc['power_decreases']}")
        print(f"  Avg Power Waste: {pc['avg_power_waste_db']:.2f} dB")
        print(f"  Rain Fade Failures: {pc['rain_fade_mitigation_failures']}")
        print("="*70 + "\n")


async def main():
    """Test reactive system"""
    print("Reactive (Traditional) NTN System - Test Mode")
    print("="*70)

    # Create reactive system
    system = ReactiveNTNSystem()

    # Simulate UE metrics over time
    print("\nSimulating UE metrics...")

    for i in range(20):
        # Generate test metrics
        metrics = {
            'satellite_metrics': {
                'satellite_id': 'SAT-LEO-001',
                'elevation_angle': 45.0 - i * 2,  # Decreasing elevation
            },
            'channel_quality': {
                'rsrp': -85.0 - i * 2,  # Degrading RSRP
                'sinr': 12.0 - i * 0.3,  # Degrading SINR
            },
            'link_budget': {
                'tx_power_dbm': 20.0,
            },
            'ntn_impairments': {
                'rain_attenuation_db': 5.0 if i > 10 else 0.0,  # Rain fade starts
            }
        }

        actions = await system.process_ue_metrics('UE-TEST-001', metrics)

        if actions['handover_event']:
            he = actions['handover_event']
            print(f"[{i}] Handover: {he.trigger}, "
                  f"RSRP={he.rsrp_db:.1f}dB, "
                  f"Success={he.success}, "
                  f"Interruption={he.data_interruption_ms:.0f}ms")

        if actions['power_event']:
            pe = actions['power_event']
            print(f"[{i}] Power: {pe.reason}, "
                  f"{pe.old_power_dbm:.1f} -> {pe.new_power_dbm:.1f} dBm "
                  f"({pe.adjustment_db:+.1f}dB), "
                  f"SINR={pe.sinr_db:.1f}dB")

        await asyncio.sleep(0.1)

    # Print summary
    system.print_summary()


if __name__ == '__main__':
    asyncio.run(main())
