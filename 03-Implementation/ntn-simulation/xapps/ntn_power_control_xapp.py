#!/usr/bin/env python3
"""
NTN Power Control xApp
Intelligent power management for satellite links using E2SM-NTN

This xApp:
1. Subscribes to E2SM-NTN for link budget metrics
2. Monitors link_margin_db for all UEs
3. Uses recommend_power_control() from E2SM-NTN
4. Adjusts transmit power based on link conditions
5. Implements rain fade mitigation
6. Balances power efficiency vs link quality
7. Tracks power adjustment history
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import sys
import os

# Add e2_ntn_extension to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'e2_ntn_extension'))

from e2sm_ntn import (
    E2SM_NTN, NTNControlAction, NTNEventTrigger,
    LinkBudget, NTNImpairments
)


class PowerControlMode(Enum):
    """Power control operating modes"""
    NORMAL = "NORMAL"  # Normal operation, balance power and quality
    EFFICIENCY = "EFFICIENCY"  # Maximize power efficiency
    QUALITY = "QUALITY"  # Maximize link quality
    RAIN_FADE = "RAIN_FADE"  # Rain fade mitigation active


@dataclass
class PowerAdjustmentRecord:
    """Record of power adjustment"""
    timestamp: float
    ue_id: str
    old_power_dbm: float
    new_power_dbm: float
    adjustment_db: float
    reason: str
    link_margin_before: float
    link_margin_after: Optional[float] = None
    elevation_angle: float = 0.0
    rain_attenuation_db: float = 0.0


@dataclass
class UEPowerState:
    """Track UE power control state"""
    ue_id: str
    current_power_dbm: float
    target_power_dbm: float
    link_margin_db: float
    elevation_angle: float
    rain_attenuation_db: float
    mode: PowerControlMode = PowerControlMode.NORMAL
    last_update_time: float = 0.0
    adjustment_count: int = 0
    total_power_saved_db: float = 0.0
    adjustment_history: List[PowerAdjustmentRecord] = field(default_factory=list)


class NTNPowerControlXApp:
    """
    NTN Power Control xApp

    Implements intelligent transmit power control for satellite links.
    Adapts power based on link budget, elevation angle, rain fade, and
    other NTN-specific conditions.

    Features:
    - Dynamic power adjustment based on link margin
    - Elevation-aware power control
    - Rain fade detection and mitigation
    - Power efficiency optimization
    - Comprehensive power usage statistics
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize NTN Power Control xApp

        Args:
            config: Configuration dictionary with thresholds and parameters
        """
        # Configuration
        self.config = config or {}
        self.target_margin_db = self.config.get('target_margin_db', 10.0)
        self.margin_tolerance_db = self.config.get('margin_tolerance_db', 3.0)
        self.max_power_dbm = self.config.get('max_power_dbm', 23.0)
        self.min_power_dbm = self.config.get('min_power_dbm', 0.0)
        self.max_adjustment_db = self.config.get('max_adjustment_db', 3.0)
        self.subscription_period_ms = self.config.get('subscription_period_ms', 1000)
        self.rain_fade_threshold_db = self.config.get('rain_fade_threshold_db', 3.0)
        self.efficiency_mode_enabled = self.config.get('efficiency_mode', True)

        # E2SM-NTN service model
        self.e2sm_ntn = E2SM_NTN()

        # UE power states
        self.ue_power_states: Dict[str, UEPowerState] = {}

        # Power adjustment records
        self.power_adjustments: List[PowerAdjustmentRecord] = []

        # Statistics
        self.statistics = {
            'total_indications': 0,
            'total_power_adjustments': 0,
            'power_increases': 0,
            'power_decreases': 0,
            'rain_fade_mitigations': 0,
            'total_power_saved_db': 0.0,
            'average_link_margin_db': 0.0,
            'average_power_dbm': 0.0,
            'margin_violations': 0
        }

        # Running state
        self.running = False
        self.start_time = time.time()

        print(f"[NTN-PC-xApp] Initialized with config:")
        print(f"  - Target margin: {self.target_margin_db} dB")
        print(f"  - Margin tolerance: ±{self.margin_tolerance_db} dB")
        print(f"  - Power range: {self.min_power_dbm} to {self.max_power_dbm} dBm")
        print(f"  - Max adjustment: ±{self.max_adjustment_db} dB")
        print(f"  - Rain fade threshold: {self.rain_fade_threshold_db} dB")
        print(f"  - Efficiency mode: {'Enabled' if self.efficiency_mode_enabled else 'Disabled'}")

    async def start(self):
        """Start the xApp"""
        self.running = True
        print(f"[NTN-PC-xApp] Started at {datetime.now().isoformat()}")

    async def stop(self):
        """Stop the xApp"""
        self.running = False
        print(f"[NTN-PC-xApp] Stopped. Final statistics:")
        self.print_statistics()

    def create_subscription(self) -> bytes:
        """
        Create E2 subscription for periodic NTN metrics

        Returns:
            Encoded subscription request
        """
        subscription = {
            'ran_function_id': E2SM_NTN.RAN_FUNCTION_ID,
            'event_trigger': {
                'type': NTNEventTrigger.PERIODIC.value,
                'period_ms': self.subscription_period_ms
            },
            'actions': [
                {
                    'action_id': 1,
                    'action_type': 'report',
                    'report_style': 1  # Full NTN Metrics
                }
            ]
        }

        return json.dumps(subscription).encode('utf-8')

    async def on_indication(self, indication_header: bytes, indication_message: bytes):
        """
        Process RIC Indication message from E2SM-NTN

        Args:
            indication_header: E2SM-NTN indication header
            indication_message: E2SM-NTN indication message with NTN metrics
        """
        self.statistics['total_indications'] += 1

        try:
            # Decode indication message
            ntn_data = json.loads(indication_message.decode('utf-8'))

            ue_id = ntn_data['ue_id']
            sat_metrics = ntn_data['satellite_metrics']
            link_budget = ntn_data['link_budget']
            ntn_impairments = ntn_data['ntn_impairments']

            # Update or create UE power state
            if ue_id not in self.ue_power_states:
                self.ue_power_states[ue_id] = UEPowerState(
                    ue_id=ue_id,
                    current_power_dbm=link_budget['tx_power_dbm'],
                    target_power_dbm=link_budget['tx_power_dbm'],
                    link_margin_db=link_budget['link_margin_db'],
                    elevation_angle=sat_metrics['elevation_angle'],
                    rain_attenuation_db=ntn_impairments['rain_attenuation_db'],
                    last_update_time=time.time()
                )
                print(f"[NTN-PC-xApp] Registered new UE: {ue_id}")

            state = self.ue_power_states[ue_id]

            # Update state
            state.link_margin_db = link_budget['link_margin_db']
            state.elevation_angle = sat_metrics['elevation_angle']
            state.rain_attenuation_db = ntn_impairments['rain_attenuation_db']
            state.last_update_time = time.time()

            # Check for rain fade
            if ntn_impairments['rain_attenuation_db'] > self.rain_fade_threshold_db:
                await self.activate_rain_fade_mitigation(ue_id, ntn_data)
                state.mode = PowerControlMode.RAIN_FADE
            elif state.mode == PowerControlMode.RAIN_FADE and \
                 ntn_impairments['rain_attenuation_db'] < self.rain_fade_threshold_db / 2:
                # Rain fade cleared, return to normal mode
                state.mode = PowerControlMode.NORMAL
                print(f"[NTN-PC-xApp] Rain fade cleared for {ue_id}, returning to normal mode")

            # Calculate power adjustment
            await self.optimize_power(ue_id, ntn_data)

        except Exception as e:
            print(f"[NTN-PC-xApp] Error processing indication: {e}")

    async def optimize_power(
        self,
        ue_id: str,
        ntn_data: Dict[str, Any]
    ):
        """
        Optimize transmit power for UE

        Args:
            ue_id: UE identifier
            ntn_data: NTN metrics data
        """
        state = self.ue_power_states[ue_id]
        link_budget = ntn_data['link_budget']

        # Convert link_budget dict to LinkBudget object
        link_budget_obj = LinkBudget(
            tx_power_dbm=link_budget['tx_power_dbm'],
            rx_power_dbm=link_budget['rx_power_dbm'],
            link_margin_db=link_budget['link_margin_db'],
            snr_db=link_budget['snr_db'],
            required_snr_db=link_budget['required_snr_db']
        )

        # Get power recommendation from E2SM-NTN
        recommendation = self.e2sm_ntn.recommend_power_control(
            link_budget=link_budget_obj,
            current_power_dbm=state.current_power_dbm
        )

        power_adjustment = recommendation['power_adjustment_db']
        reason = recommendation['reason']

        # Apply efficiency mode adjustments
        if self.efficiency_mode_enabled and state.mode == PowerControlMode.NORMAL:
            # If link margin is well above target, be more aggressive in reducing power
            if link_budget['link_margin_db'] > self.target_margin_db + self.margin_tolerance_db:
                power_adjustment = min(power_adjustment, -2.0)
                reason = "EFFICIENCY_OPTIMIZATION"

        # Check if adjustment needed
        if abs(power_adjustment) > 0.5:  # 0.5 dB threshold to avoid small adjustments
            await self.adjust_power(
                ue_id=ue_id,
                power_adjustment_db=power_adjustment,
                reason=reason,
                ntn_data=ntn_data
            )

    async def adjust_power(
        self,
        ue_id: str,
        power_adjustment_db: float,
        reason: str,
        ntn_data: Dict[str, Any]
    ):
        """
        Adjust UE transmit power

        Args:
            ue_id: UE identifier
            power_adjustment_db: Power adjustment in dB
            reason: Reason for adjustment
            ntn_data: NTN metrics data
        """
        state = self.ue_power_states[ue_id]
        link_budget = ntn_data['link_budget']
        sat_metrics = ntn_data['satellite_metrics']
        ntn_impairments = ntn_data['ntn_impairments']

        # Clamp adjustment
        power_adjustment_db = max(-self.max_adjustment_db,
                                  min(self.max_adjustment_db, power_adjustment_db))

        # Calculate new power
        old_power = state.current_power_dbm
        new_power = old_power + power_adjustment_db

        # Clamp to UE power limits
        new_power = max(self.min_power_dbm, min(self.max_power_dbm, new_power))
        actual_adjustment = new_power - old_power

        # Create adjustment record
        record = PowerAdjustmentRecord(
            timestamp=time.time(),
            ue_id=ue_id,
            old_power_dbm=old_power,
            new_power_dbm=new_power,
            adjustment_db=actual_adjustment,
            reason=reason,
            link_margin_before=link_budget['link_margin_db'],
            elevation_angle=sat_metrics['elevation_angle'],
            rain_attenuation_db=ntn_impairments['rain_attenuation_db']
        )

        # Execute power adjustment
        success = await self.execute_power_adjustment(
            ue_id=ue_id,
            target_power_dbm=new_power,
            reason=reason
        )

        if success:
            # Update state
            state.current_power_dbm = new_power
            state.target_power_dbm = new_power
            state.adjustment_count += 1
            state.adjustment_history.append(record)

            if actual_adjustment < 0:
                state.total_power_saved_db += abs(actual_adjustment)

            # Update statistics
            self.statistics['total_power_adjustments'] += 1
            if actual_adjustment > 0:
                self.statistics['power_increases'] += 1
            else:
                self.statistics['power_decreases'] += 1
                self.statistics['total_power_saved_db'] += abs(actual_adjustment)

            self.power_adjustments.append(record)

            # Print adjustment event
            direction = "↑" if actual_adjustment > 0 else "↓"
            print(f"[NTN-PC-xApp] Power adjustment {direction} for {ue_id}:")
            print(f"  - Reason: {reason}")
            print(f"  - Power: {old_power:.1f} → {new_power:.1f} dBm ({actual_adjustment:+.1f} dB)")
            print(f"  - Link margin: {link_budget['link_margin_db']:.1f} dB (target: {self.target_margin_db} dB)")
            print(f"  - Elevation: {sat_metrics['elevation_angle']:.1f}°")
            if ntn_impairments['rain_attenuation_db'] > 0:
                print(f"  - Rain attenuation: {ntn_impairments['rain_attenuation_db']:.1f} dB")

    async def execute_power_adjustment(
        self,
        ue_id: str,
        target_power_dbm: float,
        reason: str
    ) -> bool:
        """
        Execute power adjustment via RIC Control Request

        Args:
            ue_id: UE identifier
            target_power_dbm: Target transmit power
            reason: Reason for adjustment

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create RIC Control message
            control_params = {
                'target_tx_power_dbm': target_power_dbm,
                'reason': reason,
                'ue_id': ue_id
            }

            control_msg = self.e2sm_ntn.create_control_message(
                action_type=NTNControlAction.POWER_CONTROL,
                ue_id=ue_id,
                parameters=control_params
            )

            # In real xApp, would send via E2 interface:
            # await self.e2_manager.send_control_request(control_msg)

            # Simulate control execution
            await asyncio.sleep(0.001)  # Simulate E2 latency

            return True

        except Exception as e:
            print(f"[NTN-PC-xApp] Power adjustment execution error: {e}")
            return False

    async def activate_rain_fade_mitigation(
        self,
        ue_id: str,
        ntn_data: Dict[str, Any]
    ):
        """
        Activate rain fade mitigation

        Args:
            ue_id: UE identifier
            ntn_data: NTN metrics data
        """
        state = self.ue_power_states[ue_id]
        ntn_impairments = ntn_data['ntn_impairments']

        if state.mode == PowerControlMode.RAIN_FADE:
            # Already in rain fade mode
            return

        self.statistics['rain_fade_mitigations'] += 1

        print(f"[NTN-PC-xApp] Rain fade detected for {ue_id}:")
        print(f"  - Rain attenuation: {ntn_impairments['rain_attenuation_db']:.1f} dB")
        print(f"  - Activating mitigation...")

        # Send fade mitigation control
        try:
            control_params = {
                'rain_attenuation_db': ntn_impairments['rain_attenuation_db'],
                'mitigation_mode': 'ADAPTIVE_CODING',
                'ue_id': ue_id
            }

            control_msg = self.e2sm_ntn.create_control_message(
                action_type=NTNControlAction.ACTIVATE_FADE_MITIGATION,
                ue_id=ue_id,
                parameters=control_params
            )

            # Simulate control execution
            await asyncio.sleep(0.001)

            print(f"[NTN-PC-xApp] Rain fade mitigation activated for {ue_id}")

        except Exception as e:
            print(f"[NTN-PC-xApp] Rain fade mitigation error: {e}")

    def collect_statistics(self) -> Dict[str, Any]:
        """
        Collect power control performance statistics

        Returns:
            Dictionary with performance metrics
        """
        # Calculate averages
        if self.ue_power_states:
            total_margin = sum(s.link_margin_db for s in self.ue_power_states.values())
            total_power = sum(s.current_power_dbm for s in self.ue_power_states.values())
            num_ues = len(self.ue_power_states)

            self.statistics['average_link_margin_db'] = total_margin / num_ues
            self.statistics['average_power_dbm'] = total_power / num_ues

            # Count margin violations
            violations = sum(
                1 for s in self.ue_power_states.values()
                if s.link_margin_db < self.target_margin_db - self.margin_tolerance_db
            )
            self.statistics['margin_violations'] = violations

        # Calculate efficiency metrics
        if self.statistics['total_power_adjustments'] > 0:
            decrease_ratio = (self.statistics['power_decreases'] /
                            self.statistics['total_power_adjustments'] * 100.0)
        else:
            decrease_ratio = 0.0

        return {
            **self.statistics,
            'power_decrease_ratio_percent': decrease_ratio,
            'active_ues': len(self.ue_power_states),
            'uptime_seconds': time.time() - self.start_time
        }

    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.collect_statistics()

        print("\n" + "="*70)
        print("NTN Power Control xApp - Performance Statistics")
        print("="*70)
        print(f"Uptime:                    {stats['uptime_seconds']:.1f} seconds")
        print(f"Active UEs:                {stats['active_ues']}")
        print(f"Total Indications:         {stats['total_indications']}")
        print(f"\nPower Adjustment Statistics:")
        print(f"  Total Adjustments:       {stats['total_power_adjustments']}")
        print(f"  Power Increases:         {stats['power_increases']}")
        print(f"  Power Decreases:         {stats['power_decreases']} ({stats['power_decrease_ratio_percent']:.1f}%)")
        print(f"  Total Power Saved:       {stats['total_power_saved_db']:.1f} dB")
        print(f"\nLink Quality:")
        print(f"  Average Link Margin:     {stats['average_link_margin_db']:.1f} dB (target: {self.target_margin_db} dB)")
        print(f"  Average TX Power:        {stats['average_power_dbm']:.1f} dBm")
        print(f"  Margin Violations:       {stats['margin_violations']}")
        print(f"\nRain Fade:")
        print(f"  Mitigations Activated:   {stats['rain_fade_mitigations']}")
        print("="*70 + "\n")

    def get_ue_power_state(self, ue_id: str) -> Optional[UEPowerState]:
        """Get UE power state"""
        return self.ue_power_states.get(ue_id)

    def get_power_history(self, ue_id: Optional[str] = None) -> List[PowerAdjustmentRecord]:
        """
        Get power adjustment history

        Args:
            ue_id: Optional UE ID to filter by

        Returns:
            List of power adjustments
        """
        if ue_id:
            return [r for r in self.power_adjustments if r.ue_id == ue_id]
        return self.power_adjustments


# Main function for standalone testing
async def main():
    """Test the NTN Power Control xApp"""
    print("NTN Power Control xApp - Test Mode")
    print("="*70)

    # Create xApp with test configuration
    config = {
        'target_margin_db': 10.0,
        'margin_tolerance_db': 3.0,
        'max_power_dbm': 23.0,
        'min_power_dbm': 0.0,
        'max_adjustment_db': 3.0,
        'subscription_period_ms': 1000,
        'rain_fade_threshold_db': 3.0,
        'efficiency_mode': True
    }

    xapp = NTNPowerControlXApp(config=config)
    await xapp.start()

    # Simulate E2 indications
    print("\nSimulating E2 Indications...")

    # Test scenarios
    test_scenarios = [
        {
            'name': 'Excessive margin - reduce power',
            'link_margin': 18.0,
            'tx_power': 23.0,
            'elevation': 60.0,
            'rain_atten': 0.0
        },
        {
            'name': 'Low margin - increase power',
            'link_margin': 4.0,
            'tx_power': 15.0,
            'elevation': 20.0,
            'rain_atten': 0.0
        },
        {
            'name': 'Rain fade - mitigation needed',
            'link_margin': 5.0,
            'tx_power': 20.0,
            'elevation': 45.0,
            'rain_atten': 5.0
        },
        {
            'name': 'Optimal margin - no adjustment',
            'link_margin': 10.0,
            'tx_power': 18.0,
            'elevation': 50.0,
            'rain_atten': 0.0
        }
    ]

    for i, scenario in enumerate(test_scenarios):
        print(f"\n--- Scenario {i+1}: {scenario['name']} ---")

        # Create test indication
        ntn_data = {
            'timestamp_ns': int(time.time() * 1e9),
            'ue_id': 'UE-TEST-001',
            'satellite_metrics': {
                'satellite_id': 'SAT-LEO-001',
                'orbit_type': 'LEO',
                'beam_id': 1,
                'elevation_angle': scenario['elevation'],
                'azimuth_angle': 180.0,
                'slant_range_km': 800.0,
                'satellite_velocity': 7.5,
                'angular_velocity': -0.5
            },
            'channel_quality': {
                'rsrp': -85.0,
                'rsrq': -12.0,
                'sinr': 15.0,
                'bler': 0.01,
                'cqi': 12
            },
            'ntn_impairments': {
                'doppler_shift_hz': 15000.0,
                'doppler_rate_hz_s': -45.0,
                'propagation_delay_ms': 2.67,
                'path_loss_db': 165.0,
                'rain_attenuation_db': scenario['rain_atten'],
                'atmospheric_loss_db': 0.5
            },
            'link_budget': {
                'tx_power_dbm': scenario['tx_power'],
                'rx_power_dbm': -85.0,
                'link_margin_db': scenario['link_margin'],
                'snr_db': 15.0,
                'required_snr_db': 9.0
            },
            'handover_prediction': {
                'time_to_handover_sec': 120.0,
                'handover_trigger_threshold': 10.0,
                'next_satellite_id': 'SAT-LEO-002',
                'next_satellite_elevation': 45.0,
                'handover_probability': 0.5
            },
            'performance': {
                'throughput_dl_mbps': 50.0,
                'throughput_ul_mbps': 10.0,
                'latency_rtt_ms': 10.0,
                'packet_loss_rate': 0.01
            }
        }

        indication_msg = json.dumps(ntn_data).encode('utf-8')
        indication_hdr = json.dumps({'timestamp_ns': ntn_data['timestamp_ns']}).encode('utf-8')

        await xapp.on_indication(indication_hdr, indication_msg)
        await asyncio.sleep(0.1)

    # Print final statistics
    await xapp.stop()


if __name__ == '__main__':
    asyncio.run(main())
