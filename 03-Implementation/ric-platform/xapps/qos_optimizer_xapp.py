"""
QoS Optimizer xApp
Monitors UE throughput and adjusts QoS parameters
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from xapp_sdk.xapp_framework import XAppBase, XAppConfig
from xapp_sdk.sdl_client import SDLClient

logger = logging.getLogger(__name__)


class QoSOptimizerXApp(XAppBase):
    """xApp for optimizing QoS based on UE metrics"""

    THROUGHPUT_THRESHOLD_MBPS = 10.0  # Minimum acceptable throughput

    def __init__(self):
        config = XAppConfig(
            name="qos-optimizer",
            version="1.0.0",
            description="Optimizes QoS based on UE throughput metrics",
            e2_subscriptions=[
                {
                    "ran_function_id": 1,  # E2SM-KPM
                    "event_trigger": {"period_ms": 1000}
                }
            ],
            sdl_namespace="qos-optimizer"
        )
        super().__init__(config)
        self.sdl = SDLClient(namespace=config.sdl_namespace)
        self.ue_metrics = {}

    async def init(self):
        """Initialize xApp"""
        self.logger.info("QoS Optimizer xApp initializing...")
        # Load previous state from SDL
        stored_metrics = self.sdl.get("ue_metrics")
        if stored_metrics:
            self.ue_metrics = stored_metrics
            self.logger.info(f"Loaded {len(self.ue_metrics)} UE metrics from SDL")

    async def handle_indication(self, indication):
        """Handle E2 indication with UE metrics"""
        # Parse KPM indication
        measurements = self._parse_kpm_indication(indication)

        for measurement in measurements:
            ue_id = measurement.get("ueId")
            if not ue_id:
                continue

            # Update UE metrics
            self.ue_metrics[ue_id] = {
                "throughput_dl_mbps": measurement.get("value", 0.0),
                "timestamp": measurement.get("timestamp"),
                "cell_id": measurement.get("cellId")
            }

            # Check if QoS adjustment needed
            await self._check_qos_adjustment(ue_id)

        # Store updated metrics in SDL
        self.sdl.set("ue_metrics", self.ue_metrics)

        # Update xApp metrics
        self.update_metric("ues_monitored", len(self.ue_metrics))

    async def _check_qos_adjustment(self, ue_id: str):
        """Check if QoS adjustment is needed for UE"""
        metrics = self.ue_metrics.get(ue_id)
        if not metrics:
            return

        throughput = metrics["throughput_dl_mbps"]

        if throughput < self.THROUGHPUT_THRESHOLD_MBPS:
            self.logger.warning(
                f"UE {ue_id} throughput ({throughput:.2f} Mbps) below threshold"
            )
            # Trigger QoS adjustment via E2 Control
            await self._send_qos_control(ue_id, increase_priority=True)
        elif throughput > self.THROUGHPUT_THRESHOLD_MBPS * 2:
            # Throughput is very high, can reduce priority to free resources
            await self._send_qos_control(ue_id, increase_priority=False)

    async def _send_qos_control(self, ue_id: str, increase_priority: bool):
        """Send E2 Control Request to adjust QoS"""
        action = "increase" if increase_priority else "decrease"
        self.logger.info(f"Sending QoS control to {action} priority for UE {ue_id}")

        # TODO: Implement actual E2 Control Request
        # For now, store control action in SDL for monitoring
        control_action = {
            "ue_id": ue_id,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        self.sdl.set(f"control_action:{ue_id}", control_action)

        # Update metric
        metric_name = "qos_controls_sent"
        current = self.metrics.get(metric_name, {}).get("value", 0)
        self.update_metric(metric_name, current + 1)

    def _parse_kpm_indication(self, indication) -> List[Dict]:
        """Parse KPM indication message"""
        # Simplified parsing
        import json
        try:
            message = json.loads(indication.ric_indication_message)
            return message.get("measurements", [])
        except:
            return []


# Main entry point
async def main():
    """Run QoS Optimizer xApp"""
    logging.basicConfig(level=logging.INFO)

    xapp = QoSOptimizerXApp()
    await xapp.start()

    try:
        # Run until interrupted
        while xapp.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await xapp.stop()


if __name__ == "__main__":
    asyncio.run(main())
