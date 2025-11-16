"""
Handover Manager xApp
Intelligent handover decision based on signal quality and load
"""

import asyncio
import sys
import os
from collections import defaultdict
from datetime import datetime
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from xapp_sdk.xapp_framework import XAppBase, XAppConfig
from xapp_sdk.sdl_client import SDLClient


class HandoverManagerXApp(XAppBase):
    """xApp for intelligent handover management"""

    RSRP_THRESHOLD_DBM = -110  # Trigger handover below this
    CELL_LOAD_THRESHOLD_PERCENT = 80  # Consider cell overloaded above this

    def __init__(self):
        config = XAppConfig(
            name="handover-manager",
            version="1.0.0",
            description="Intelligent handover decision making",
            e2_subscriptions=[
                {
                    "ran_function_id": 1,  # E2SM-KPM for metrics
                    "event_trigger": {"period_ms": 500}
                }
            ],
            sdl_namespace="handover-manager"
        )
        super().__init__(config)
        self.sdl = SDLClient(namespace=config.sdl_namespace)
        self.ue_measurements = {}
        self.cell_load = defaultdict(float)

    async def init(self):
        """Initialize xApp"""
        self.logger.info("Handover Manager xApp initializing...")

    async def handle_indication(self, indication):
        """Handle E2 indication"""
        measurements = self._parse_indication(indication)

        for m in measurements:
            ue_id = m.get("ueId")
            cell_id = m.get("cellId")

            if "rsrp" in m:
                # Signal strength measurement
                self.ue_measurements[ue_id] = {
                    "serving_cell": cell_id,
                    "rsrp_dbm": m["rsrp"],
                    "neighbor_cells": m.get("neighborCells", [])
                }

                # Check if handover needed
                await self._evaluate_handover(ue_id)

            elif "cellLoad" in m:
                # Cell load measurement
                self.cell_load[cell_id] = m["cellLoad"]

        # Update metrics
        self.update_metric("active_ues", len(self.ue_measurements))

    async def _evaluate_handover(self, ue_id: str):
        """Evaluate if handover is needed for UE"""
        ue_data = self.ue_measurements.get(ue_id)
        if not ue_data:
            return

        serving_rsrp = ue_data["rsrp_dbm"]
        serving_cell = ue_data["serving_cell"]

        # Check if signal is poor
        if serving_rsrp < self.RSRP_THRESHOLD_DBM:
            # Find best neighbor cell
            best_neighbor = self._find_best_neighbor(ue_data)

            if best_neighbor:
                await self._trigger_handover(
                    ue_id,
                    source_cell=serving_cell,
                    target_cell=best_neighbor["cell_id"],
                    reason="poor_signal"
                )

        # Check if serving cell is overloaded
        if self.cell_load[serving_cell] > self.CELL_LOAD_THRESHOLD_PERCENT:
            # Offload to less loaded neighbor
            best_neighbor = self._find_least_loaded_neighbor(ue_data)

            if best_neighbor:
                await self._trigger_handover(
                    ue_id,
                    source_cell=serving_cell,
                    target_cell=best_neighbor["cell_id"],
                    reason="load_balancing"
                )

    def _find_best_neighbor(self, ue_data: dict) -> dict:
        """Find neighbor cell with best signal"""
        neighbors = ue_data.get("neighbor_cells", [])
        if not neighbors:
            return None

        # Sort by RSRP (highest first)
        neighbors.sort(key=lambda x: x.get("rsrp", -999), reverse=True)

        best = neighbors[0]
        # Only handover if neighbor is significantly better
        if best.get("rsrp", -999) > ue_data["rsrp_dbm"] + 5:
            return best
        return None

    def _find_least_loaded_neighbor(self, ue_data: dict) -> dict:
        """Find least loaded neighbor cell"""
        neighbors = ue_data.get("neighbor_cells", [])
        if not neighbors:
            return None

        # Filter neighbors with acceptable signal
        acceptable = [
            n for n in neighbors
            if n.get("rsrp", -999) > self.RSRP_THRESHOLD_DBM + 10
        ]

        if not acceptable:
            return None

        # Find least loaded
        least_loaded = min(
            acceptable,
            key=lambda x: self.cell_load.get(x["cell_id"], 100)
        )

        return least_loaded

    async def _trigger_handover(self, ue_id: str, source_cell: str,
                               target_cell: str, reason: str):
        """Trigger handover via E2 Control"""
        self.logger.info(
            f"Triggering handover for {ue_id}: {source_cell} -> {target_cell} ({reason})"
        )

        # Store handover decision in SDL
        decision = {
            "ue_id": ue_id,
            "source_cell": source_cell,
            "target_cell": target_cell,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.sdl.set(f"handover:{ue_id}", decision)

        # Update metric
        metric_name = "handovers_triggered"
        current = self.metrics.get(metric_name, {}).get("value", 0)
        self.update_metric(metric_name, current + 1)

    def _parse_indication(self, indication) -> List[Dict]:
        """Parse indication message"""
        # Simplified parsing
        import json
        try:
            message = json.loads(indication.ric_indication_message)
            return message.get("measurements", [])
        except:
            return []


# Main entry point
async def main():
    """Run Handover Manager xApp"""
    import logging
    logging.basicConfig(level=logging.INFO)

    xapp = HandoverManagerXApp()
    await xapp.start()

    try:
        # Run until interrupted
        while xapp.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await xapp.stop()


if __name__ == "__main__":
    asyncio.run(main())
