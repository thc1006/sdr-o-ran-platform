#!/usr/bin/env python3
"""
NTN Handover Optimization xApp
Predictive handover management for satellite networks using E2SM-NTN

This xApp:
1. Subscribes to E2SM-NTN for periodic NTN metrics
2. Monitors time_to_handover_sec for all UEs
3. Triggers predictive handover when < 30 seconds to satellite handover
4. Selects next satellite based on elevation and link quality
5. Sends RIC Control Request to execute handover
6. Collects statistics on handover success rate and prediction accuracy
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import sys
import os

# Add e2_ntn_extension to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'e2_ntn_extension'))

from e2sm_ntn import (
    E2SM_NTN, NTNControlAction, NTNEventTrigger,
    NTNIndicationMessage, LinkBudget, HandoverPrediction
)


@dataclass
class UEHandoverContext:
    """Track UE handover state"""
    ue_id: str
    current_satellite_id: str
    elevation_angle: float
    time_to_handover_sec: float
    last_update_time: float
    handover_count: int = 0
    last_handover_time: Optional[float] = None
    handover_preparation_started: bool = False
    handover_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HandoverDecision:
    """Handover decision record"""
    timestamp: float
    ue_id: str
    trigger_reason: str
    source_satellite_id: str
    target_satellite_id: str
    time_to_handover: float
    source_elevation: float
    target_elevation: float
    link_margin_db: float
    success: bool = False
    execution_time_ms: Optional[float] = None


class NTNHandoverXApp:
    """
    NTN Handover Optimization xApp

    Implements intelligent, predictive handover for LEO/MEO/GEO satellite networks.
    Uses E2SM-NTN metrics to predict satellite handovers and trigger them proactively
    before link quality degrades.

    Features:
    - Predictive handover based on satellite geometry
    - Multi-criteria handover decision (elevation, link quality, Doppler)
    - Handover preparation and execution tracking
    - Performance statistics and analytics
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize NTN Handover xApp

        Args:
            config: Configuration dictionary with thresholds and parameters
        """
        # Configuration
        self.config = config or {}
        self.handover_threshold_sec = self.config.get('handover_threshold_sec', 30.0)
        self.min_elevation_threshold = self.config.get('min_elevation_deg', 10.0)
        self.preparation_threshold_sec = self.config.get('preparation_threshold_sec', 60.0)
        self.min_target_elevation = self.config.get('min_target_elevation_deg', 20.0)
        self.subscription_period_ms = self.config.get('subscription_period_ms', 1000)

        # E2SM-NTN service model
        self.e2sm_ntn = E2SM_NTN()

        # UE contexts
        self.ue_contexts: Dict[str, UEHandoverContext] = {}

        # Handover decisions and statistics
        self.handover_decisions: List[HandoverDecision] = []
        self.statistics = {
            'total_indications': 0,
            'total_handovers_triggered': 0,
            'successful_handovers': 0,
            'failed_handovers': 0,
            'predictive_handovers': 0,
            'reactive_handovers': 0,
            'average_prediction_time_sec': 0.0,
            'average_execution_time_ms': 0.0
        }

        # Running state
        self.running = False
        self.start_time = time.time()

        print(f"[NTN-HO-xApp] Initialized with config:")
        print(f"  - Handover threshold: {self.handover_threshold_sec} sec")
        print(f"  - Min elevation: {self.min_elevation_threshold}°")
        print(f"  - Preparation threshold: {self.preparation_threshold_sec} sec")
        print(f"  - Subscription period: {self.subscription_period_ms} ms")

    async def start(self):
        """Start the xApp"""
        self.running = True
        print(f"[NTN-HO-xApp] Started at {datetime.now().isoformat()}")

    async def stop(self):
        """Stop the xApp"""
        self.running = False
        print(f"[NTN-HO-xApp] Stopped. Final statistics:")
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
            handover_pred = ntn_data['handover_prediction']
            link_budget = ntn_data['link_budget']

            # Update or create UE context
            if ue_id not in self.ue_contexts:
                self.ue_contexts[ue_id] = UEHandoverContext(
                    ue_id=ue_id,
                    current_satellite_id=sat_metrics['satellite_id'],
                    elevation_angle=sat_metrics['elevation_angle'],
                    time_to_handover_sec=handover_pred['time_to_handover_sec'],
                    last_update_time=time.time()
                )
                print(f"[NTN-HO-xApp] Registered new UE: {ue_id}")

            context = self.ue_contexts[ue_id]

            # Update context
            context.current_satellite_id = sat_metrics['satellite_id']
            context.elevation_angle = sat_metrics['elevation_angle']
            context.time_to_handover_sec = handover_pred['time_to_handover_sec']
            context.last_update_time = time.time()

            # Check if handover preparation needed
            if (handover_pred['time_to_handover_sec'] < self.preparation_threshold_sec and
                not context.handover_preparation_started):
                await self.start_handover_preparation(
                    ue_id=ue_id,
                    ntn_data=ntn_data
                )
                context.handover_preparation_started = True

            # Check if handover should be triggered
            if (handover_pred['time_to_handover_sec'] < self.handover_threshold_sec and
                handover_pred['handover_probability'] > 0.7):
                await self.trigger_handover(
                    ue_id=ue_id,
                    ntn_data=ntn_data
                )

        except Exception as e:
            print(f"[NTN-HO-xApp] Error processing indication: {e}")

    async def start_handover_preparation(
        self,
        ue_id: str,
        ntn_data: Dict[str, Any]
    ):
        """
        Start handover preparation phase

        Args:
            ue_id: UE identifier
            ntn_data: NTN metrics data
        """
        handover_pred = ntn_data['handover_prediction']
        sat_metrics = ntn_data['satellite_metrics']

        print(f"[NTN-HO-xApp] Handover preparation for {ue_id}:")
        print(f"  - Current satellite: {sat_metrics['satellite_id']}")
        print(f"  - Elevation: {sat_metrics['elevation_angle']:.1f}°")
        print(f"  - Time to handover: {handover_pred['time_to_handover_sec']:.1f} sec")
        print(f"  - Next satellite: {handover_pred['next_satellite_id']}")
        print(f"  - Next elevation: {handover_pred['next_satellite_elevation']:.1f}°")

    async def trigger_handover(
        self,
        ue_id: str,
        ntn_data: Dict[str, Any]
    ):
        """
        Trigger satellite handover

        Args:
            ue_id: UE identifier
            ntn_data: NTN metrics data
        """
        context = self.ue_contexts[ue_id]
        sat_metrics = ntn_data['satellite_metrics']
        handover_pred = ntn_data['handover_prediction']
        link_budget = ntn_data['link_budget']

        # Determine handover trigger reason
        if handover_pred['time_to_handover_sec'] < 10.0:
            trigger_reason = "IMMINENT_LOSS_OF_COVERAGE"
        elif sat_metrics['elevation_angle'] < self.min_elevation_threshold + 5:
            trigger_reason = "LOW_ELEVATION"
        else:
            trigger_reason = "PREDICTIVE"

        # Select target satellite
        target_satellite_id = handover_pred.get('next_satellite_id', f"SAT-LEO-{context.handover_count + 2:03d}")
        target_elevation = handover_pred.get('next_satellite_elevation', 45.0)

        # Validate target satellite
        if target_elevation < self.min_target_elevation:
            print(f"[NTN-HO-xApp] Target satellite elevation too low ({target_elevation:.1f}°), delaying handover")
            return

        # Create handover decision record
        decision = HandoverDecision(
            timestamp=time.time(),
            ue_id=ue_id,
            trigger_reason=trigger_reason,
            source_satellite_id=sat_metrics['satellite_id'],
            target_satellite_id=target_satellite_id,
            time_to_handover=handover_pred['time_to_handover_sec'],
            source_elevation=sat_metrics['elevation_angle'],
            target_elevation=target_elevation,
            link_margin_db=link_budget['link_margin_db']
        )

        # Execute handover
        execution_start = time.time()
        success = await self.execute_handover(
            ue_id=ue_id,
            target_satellite_id=target_satellite_id,
            handover_type=trigger_reason,
            preparation_time_ms=5000
        )
        execution_time_ms = (time.time() - execution_start) * 1000.0

        # Update decision record
        decision.success = success
        decision.execution_time_ms = execution_time_ms
        self.handover_decisions.append(decision)

        # Update context
        if success:
            context.handover_count += 1
            context.last_handover_time = time.time()
            context.handover_preparation_started = False
            context.handover_history.append({
                'timestamp': time.time(),
                'source': sat_metrics['satellite_id'],
                'target': target_satellite_id,
                'reason': trigger_reason
            })

        # Update statistics
        self.statistics['total_handovers_triggered'] += 1
        if success:
            self.statistics['successful_handovers'] += 1
        else:
            self.statistics['failed_handovers'] += 1

        if trigger_reason == "PREDICTIVE":
            self.statistics['predictive_handovers'] += 1
        else:
            self.statistics['reactive_handovers'] += 1

        # Print handover event
        status = "SUCCESS" if success else "FAILED"
        print(f"[NTN-HO-xApp] Handover {status} for {ue_id}:")
        print(f"  - Trigger: {trigger_reason}")
        print(f"  - Source: {sat_metrics['satellite_id']} (elev={sat_metrics['elevation_angle']:.1f}°)")
        print(f"  - Target: {target_satellite_id} (elev={target_elevation:.1f}°)")
        print(f"  - Predicted time: {handover_pred['time_to_handover_sec']:.1f} sec")
        print(f"  - Execution time: {execution_time_ms:.2f} ms")
        print(f"  - Total handovers: {context.handover_count}")

    async def execute_handover(
        self,
        ue_id: str,
        target_satellite_id: str,
        handover_type: str,
        preparation_time_ms: int = 5000
    ) -> bool:
        """
        Execute handover via RIC Control Request

        Args:
            ue_id: UE identifier
            target_satellite_id: Target satellite ID
            handover_type: Type of handover (PREDICTIVE, etc.)
            preparation_time_ms: Preparation time in milliseconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create RIC Control message
            control_params = {
                'target_satellite_id': target_satellite_id,
                'handover_type': handover_type,
                'preparation_time_ms': preparation_time_ms,
                'ue_id': ue_id
            }

            control_msg = self.e2sm_ntn.create_control_message(
                action_type=NTNControlAction.TRIGGER_HANDOVER,
                ue_id=ue_id,
                parameters=control_params
            )

            # In real xApp, would send via E2 interface:
            # await self.e2_manager.send_control_request(control_msg)

            # Simulate control execution
            await asyncio.sleep(0.001)  # Simulate E2 latency

            return True

        except Exception as e:
            print(f"[NTN-HO-xApp] Handover execution error: {e}")
            return False

    def collect_statistics(self) -> Dict[str, Any]:
        """
        Collect handover performance statistics

        Returns:
            Dictionary with performance metrics
        """
        # Calculate averages
        if self.handover_decisions:
            total_prediction_time = sum(
                d.time_to_handover for d in self.handover_decisions
            )
            self.statistics['average_prediction_time_sec'] = \
                total_prediction_time / len(self.handover_decisions)

            successful_decisions = [d for d in self.handover_decisions if d.success]
            if successful_decisions:
                total_exec_time = sum(
                    d.execution_time_ms for d in successful_decisions
                    if d.execution_time_ms is not None
                )
                self.statistics['average_execution_time_ms'] = \
                    total_exec_time / len(successful_decisions)

        # Calculate success rate
        if self.statistics['total_handovers_triggered'] > 0:
            success_rate = (self.statistics['successful_handovers'] /
                          self.statistics['total_handovers_triggered'] * 100.0)
        else:
            success_rate = 0.0

        # Calculate predictive ratio
        if self.statistics['total_handovers_triggered'] > 0:
            predictive_ratio = (self.statistics['predictive_handovers'] /
                              self.statistics['total_handovers_triggered'] * 100.0)
        else:
            predictive_ratio = 0.0

        return {
            **self.statistics,
            'success_rate_percent': success_rate,
            'predictive_ratio_percent': predictive_ratio,
            'active_ues': len(self.ue_contexts),
            'uptime_seconds': time.time() - self.start_time
        }

    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.collect_statistics()

        print("\n" + "="*70)
        print("NTN Handover xApp - Performance Statistics")
        print("="*70)
        print(f"Uptime:                    {stats['uptime_seconds']:.1f} seconds")
        print(f"Active UEs:                {stats['active_ues']}")
        print(f"Total Indications:         {stats['total_indications']}")
        print(f"\nHandover Statistics:")
        print(f"  Total Triggered:         {stats['total_handovers_triggered']}")
        print(f"  Successful:              {stats['successful_handovers']}")
        print(f"  Failed:                  {stats['failed_handovers']}")
        print(f"  Success Rate:            {stats['success_rate_percent']:.1f}%")
        print(f"\nHandover Types:")
        print(f"  Predictive:              {stats['predictive_handovers']} ({stats['predictive_ratio_percent']:.1f}%)")
        print(f"  Reactive:                {stats['reactive_handovers']}")
        print(f"\nPerformance:")
        print(f"  Avg Prediction Time:     {stats['average_prediction_time_sec']:.1f} sec")
        print(f"  Avg Execution Time:      {stats['average_execution_time_ms']:.2f} ms")
        print("="*70 + "\n")

    def get_ue_context(self, ue_id: str) -> Optional[UEHandoverContext]:
        """Get UE handover context"""
        return self.ue_contexts.get(ue_id)

    def get_handover_history(self, ue_id: Optional[str] = None) -> List[HandoverDecision]:
        """
        Get handover history

        Args:
            ue_id: Optional UE ID to filter by

        Returns:
            List of handover decisions
        """
        if ue_id:
            return [d for d in self.handover_decisions if d.ue_id == ue_id]
        return self.handover_decisions


# Main function for standalone testing
async def main():
    """Test the NTN Handover xApp"""
    print("NTN Handover Optimization xApp - Test Mode")
    print("="*70)

    # Create xApp with test configuration
    config = {
        'handover_threshold_sec': 30.0,
        'min_elevation_deg': 10.0,
        'preparation_threshold_sec': 60.0,
        'min_target_elevation_deg': 20.0,
        'subscription_period_ms': 1000
    }

    xapp = NTNHandoverXApp(config=config)
    await xapp.start()

    # Simulate E2 indications
    print("\nSimulating E2 Indications...")

    # Test scenario: UE approaching handover threshold
    test_scenarios = [
        {
            'name': 'Normal operation',
            'time_to_handover': 120.0,
            'elevation': 60.0,
            'next_elevation': 45.0
        },
        {
            'name': 'Preparation phase',
            'time_to_handover': 50.0,
            'elevation': 35.0,
            'next_elevation': 40.0
        },
        {
            'name': 'Handover trigger',
            'time_to_handover': 25.0,
            'elevation': 15.0,
            'next_elevation': 50.0
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
                'rain_attenuation_db': 0.0,
                'atmospheric_loss_db': 0.5
            },
            'link_budget': {
                'tx_power_dbm': 23.0,
                'rx_power_dbm': -85.0,
                'link_margin_db': 25.0,
                'snr_db': 15.0,
                'required_snr_db': 9.0
            },
            'handover_prediction': {
                'time_to_handover_sec': scenario['time_to_handover'],
                'handover_trigger_threshold': 10.0,
                'next_satellite_id': 'SAT-LEO-002',
                'next_satellite_elevation': scenario['next_elevation'],
                'handover_probability': 0.95 if scenario['time_to_handover'] < 30 else 0.5
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
