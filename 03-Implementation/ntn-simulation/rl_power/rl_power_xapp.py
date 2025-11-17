#!/usr/bin/env python3
"""
RL Power Control xApp
=====================

O-RAN xApp integration for RL-based power control in NTN.

Features:
- Loads trained DQN model
- Real-time inference (<5ms)
- E2SM-NTN integration
- Fallback to rule-based control
- Performance monitoring

Author: RL Specialist
Date: 2025-11-17
"""

import json
import time
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys
import os

# Add e2_ntn_extension to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'e2_ntn_extension'))

from e2sm_ntn import (
    E2SM_NTN, NTNControlAction, NTNEventTrigger,
    LinkBudget, NTNImpairments
)

# Import RL components
from dqn_agent import DQNAgent
from evaluator import RuleBasedBaseline


@dataclass
class RLPowerAdjustmentRecord:
    """Record of RL power adjustment"""
    timestamp: float
    ue_id: str
    old_power_dbm: float
    new_power_dbm: float
    adjustment_db: float
    state: np.ndarray
    q_values: np.ndarray
    action: int
    rsrp_dbm: float
    inference_time_ms: float
    fallback_used: bool = False


class RLPowerControlXApp:
    """
    RL Power Control xApp

    Integrates trained DQN agent with O-RAN RIC for NTN power control.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RL Power Control xApp

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Model configuration
        self.model_path = Path(self.config.get('model_path', './rl_power_models/best_model.pth'))
        self.fallback_enabled = self.config.get('fallback_enabled', True)
        self.inference_timeout_ms = self.config.get('inference_timeout_ms', 5.0)

        # Power control parameters
        self.max_power_dbm = self.config.get('max_power_dbm', 23.0)
        self.min_power_dbm = self.config.get('min_power_dbm', 0.0)
        self.rsrp_threshold_dbm = self.config.get('rsrp_threshold_dbm', -90.0)
        self.target_rsrp_dbm = self.config.get('target_rsrp_dbm', -85.0)

        # E2SM-NTN service model
        self.e2sm_ntn = E2SM_NTN()

        # Load RL agent
        print(f"[RL-PC-xApp] Loading DQN model from {self.model_path}...")
        self.agent = self._load_agent()

        # Fallback controller
        if self.fallback_enabled:
            self.fallback_controller = RuleBasedBaseline(
                target_rsrp=self.target_rsrp_dbm,
                tolerance=3.0
            )
            print(f"[RL-PC-xApp] Fallback controller enabled")

        # UE state tracking
        self.ue_states: Dict[str, np.ndarray] = {}
        self.ue_power: Dict[str, float] = {}

        # Performance tracking
        self.adjustment_records: List[RLPowerAdjustmentRecord] = []
        self.statistics = {
            'total_indications': 0,
            'total_adjustments': 0,
            'rl_adjustments': 0,
            'fallback_adjustments': 0,
            'total_inference_time_ms': 0.0,
            'avg_inference_time_ms': 0.0,
            'max_inference_time_ms': 0.0,
            'inference_failures': 0
        }

        self.running = False
        self.start_time = time.time()

        print(f"[RL-PC-xApp] Initialized successfully")

    def _load_agent(self) -> DQNAgent:
        """Load trained DQN agent"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        # Create agent
        agent_config = {
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 0.0,  # No exploration in production
            'epsilon_end': 0.0,
            'epsilon_decay': 1.0,
            'target_update_freq': 100,
            'buffer_capacity': 1000
        }

        agent = DQNAgent(agent_config)

        # Load trained weights
        agent.load(self.model_path)

        # Set to evaluation mode
        agent.eval()
        agent.epsilon = 0.0

        return agent

    async def start(self):
        """Start xApp"""
        self.running = True
        print(f"[RL-PC-xApp] Started at {datetime.now().isoformat()}")

    async def stop(self):
        """Stop xApp"""
        self.running = False
        print(f"[RL-PC-xApp] Stopped. Statistics:")
        self.print_statistics()

    def create_subscription(self) -> bytes:
        """Create E2 subscription for NTN metrics"""
        subscription = {
            'ran_function_id': E2SM_NTN.RAN_FUNCTION_ID,
            'event_trigger': {
                'type': NTNEventTrigger.PERIODIC.value,
                'period_ms': 1000  # 1 Hz
            },
            'actions': [
                {
                    'action_id': 1,
                    'action_type': 'report',
                    'report_style': 1
                }
            ]
        }

        return json.dumps(subscription).encode('utf-8')

    async def on_indication(self, indication_header: bytes, indication_message: bytes):
        """
        Process RIC Indication with RL inference

        Args:
            indication_header: E2SM-NTN indication header
            indication_message: E2SM-NTN indication message
        """
        self.statistics['total_indications'] += 1
        inference_start = time.time()

        try:
            # Decode indication
            ntn_data = json.loads(indication_message.decode('utf-8'))

            ue_id = ntn_data['ue_id']
            sat_metrics = ntn_data['satellite_metrics']
            link_budget = ntn_data['link_budget']
            ntn_impairments = ntn_data['ntn_impairments']

            # Construct state vector
            # [elevation_angle, slant_range, rain_rate, current_rsrp, doppler_shift]
            state = np.array([
                sat_metrics['elevation_angle'],
                sat_metrics['slant_range_km'],
                ntn_impairments.get('rain_attenuation_db', 0.0) * 10,  # Convert to rain rate estimate
                link_budget['rx_power_dbm'],  # Use RSRP
                ntn_impairments['doppler_shift_hz']
            ], dtype=np.float32)

            # Store state
            self.ue_states[ue_id] = state
            current_power = link_budget['tx_power_dbm']
            self.ue_power[ue_id] = current_power

            # RL Inference
            fallback_used = False
            try:
                # Get action from RL agent
                action = self.agent.select_action(state, explore=False)

                # Get Q-values for monitoring
                q_values = self.agent.get_q_values(state)

                # Check inference time
                inference_time_ms = (time.time() - inference_start) * 1000

                # Timeout check
                if inference_time_ms > self.inference_timeout_ms:
                    raise TimeoutError(f"Inference timeout: {inference_time_ms:.2f} ms")

                # Track inference time
                self.statistics['total_inference_time_ms'] += inference_time_ms
                self.statistics['max_inference_time_ms'] = max(
                    self.statistics['max_inference_time_ms'],
                    inference_time_ms
                )

            except Exception as e:
                # Fallback to rule-based
                if self.fallback_enabled:
                    action = self.fallback_controller.select_action(state)
                    q_values = np.zeros(5)
                    fallback_used = True
                    self.statistics['inference_failures'] += 1
                    print(f"[RL-PC-xApp] Inference failed for {ue_id}, using fallback: {e}")
                else:
                    raise

            # Map action to power adjustment
            action_to_adjustment = {
                0: -3.0, 1: -1.0, 2: 0.0, 3: 1.0, 4: 3.0
            }
            power_adjustment_db = action_to_adjustment[action]

            # Calculate new power
            new_power = np.clip(
                current_power + power_adjustment_db,
                self.min_power_dbm,
                self.max_power_dbm
            )

            # Execute power adjustment
            if abs(new_power - current_power) > 0.1:  # Only adjust if significant
                success = await self.execute_power_adjustment(
                    ue_id=ue_id,
                    target_power_dbm=new_power,
                    action=action
                )

                if success:
                    # Record adjustment
                    record = RLPowerAdjustmentRecord(
                        timestamp=time.time(),
                        ue_id=ue_id,
                        old_power_dbm=current_power,
                        new_power_dbm=new_power,
                        adjustment_db=new_power - current_power,
                        state=state,
                        q_values=q_values,
                        action=action,
                        rsrp_dbm=state[3],
                        inference_time_ms=inference_time_ms,
                        fallback_used=fallback_used
                    )

                    self.adjustment_records.append(record)
                    self.statistics['total_adjustments'] += 1

                    if fallback_used:
                        self.statistics['fallback_adjustments'] += 1
                    else:
                        self.statistics['rl_adjustments'] += 1

                    # Update stored power
                    self.ue_power[ue_id] = new_power

                    # Log adjustment
                    direction = "↑" if new_power > current_power else "↓"
                    source = "FALLBACK" if fallback_used else "RL"
                    print(f"[RL-PC-xApp] {source} Power {direction} for {ue_id}: "
                          f"{current_power:.1f} → {new_power:.1f} dBm "
                          f"(action={action}, Q={q_values[action]:.2f}, "
                          f"inference={inference_time_ms:.2f}ms)")

        except Exception as e:
            print(f"[RL-PC-xApp] Error processing indication: {e}")

    async def execute_power_adjustment(
        self,
        ue_id: str,
        target_power_dbm: float,
        action: int
    ) -> bool:
        """Execute power adjustment via RIC Control Request"""
        try:
            # Create control message
            control_params = {
                'target_tx_power_dbm': target_power_dbm,
                'action': action,
                'ue_id': ue_id,
                'controller_type': 'RL_DQN'
            }

            control_msg = self.e2sm_ntn.create_control_message(
                action_type=NTNControlAction.POWER_CONTROL,
                ue_id=ue_id,
                parameters=control_params
            )

            # Simulate E2 control (in real xApp, send via E2 interface)
            await asyncio.sleep(0.001)

            return True

        except Exception as e:
            print(f"[RL-PC-xApp] Power adjustment error: {e}")
            return False

    def collect_statistics(self) -> Dict[str, Any]:
        """Collect performance statistics"""
        if self.statistics['total_adjustments'] > 0:
            self.statistics['avg_inference_time_ms'] = (
                self.statistics['total_inference_time_ms'] /
                self.statistics['total_adjustments']
            )

        rl_ratio = (
            self.statistics['rl_adjustments'] / self.statistics['total_adjustments'] * 100
            if self.statistics['total_adjustments'] > 0 else 0
        )

        return {
            **self.statistics,
            'rl_adjustment_ratio_percent': rl_ratio,
            'active_ues': len(self.ue_states),
            'uptime_seconds': time.time() - self.start_time
        }

    def print_statistics(self):
        """Print performance statistics"""
        stats = self.collect_statistics()

        print("\n" + "="*70)
        print("RL Power Control xApp - Performance Statistics")
        print("="*70)
        print(f"Uptime: {stats['uptime_seconds']:.1f} seconds")
        print(f"Active UEs: {stats['active_ues']}")
        print(f"Total Indications: {stats['total_indications']}")

        print(f"\nPower Adjustments:")
        print(f"  Total: {stats['total_adjustments']}")
        print(f"  RL Adjustments: {stats['rl_adjustments']} ({stats['rl_adjustment_ratio_percent']:.1f}%)")
        print(f"  Fallback Adjustments: {stats['fallback_adjustments']}")
        print(f"  Inference Failures: {stats['inference_failures']}")

        print(f"\nInference Performance:")
        print(f"  Average Time: {stats['avg_inference_time_ms']:.2f} ms")
        print(f"  Maximum Time: {stats['max_inference_time_ms']:.2f} ms")
        print(f"  Target: <{self.inference_timeout_ms} ms")

        print("="*70 + "\n")


# Test function
async def main():
    """Test RL Power Control xApp"""
    print("RL Power Control xApp - Test Mode")
    print("="*70)

    # Create xApp
    config = {
        'model_path': './rl_power_models/best_model.pth',
        'fallback_enabled': True,
        'inference_timeout_ms': 5.0,
        'target_rsrp_dbm': -85.0,
        'rsrp_threshold_dbm': -90.0
    }

    # For testing, create a dummy model if not exists
    model_path = Path(config['model_path'])
    if not model_path.exists():
        print(f"[Test] Creating dummy model for testing...")
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Create minimal agent and save
        from dqn_agent import DQNAgent
        agent = DQNAgent({
            'state_dim': 5,
            'action_dim': 5,
            'hidden_dims': [128, 128, 64],
            'lr': 0.0001,
            'gamma': 0.99,
            'epsilon_start': 0.0,
            'epsilon_end': 0.0,
            'epsilon_decay': 1.0,
            'target_update_freq': 100,
            'buffer_capacity': 1000
        })
        agent.save(model_path)

    xapp = RLPowerControlXApp(config)
    await xapp.start()

    # Simulate E2 indications
    print("\nSimulating E2 Indications...")

    for i in range(5):
        ntn_data = {
            'timestamp_ns': int(time.time() * 1e9),
            'ue_id': f'UE-TEST-{i%2+1}',
            'satellite_metrics': {
                'satellite_id': 'SAT-LEO-001',
                'elevation_angle': 45.0 - i * 2,
                'azimuth_angle': 180.0,
                'slant_range_km': 800.0 + i * 10,
            },
            'link_budget': {
                'tx_power_dbm': 20.0,
                'rx_power_dbm': -85.0 - i,
            },
            'ntn_impairments': {
                'doppler_shift_hz': 15000.0,
                'rain_attenuation_db': 0.0 if i < 3 else 2.0
            }
        }

        indication_msg = json.dumps(ntn_data).encode('utf-8')
        indication_hdr = json.dumps({'timestamp_ns': ntn_data['timestamp_ns']}).encode('utf-8')

        await xapp.on_indication(indication_hdr, indication_msg)
        await asyncio.sleep(0.1)

    await xapp.stop()


if __name__ == '__main__':
    asyncio.run(main())
