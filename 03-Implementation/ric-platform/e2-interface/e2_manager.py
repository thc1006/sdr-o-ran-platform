"""
E2 Interface Manager for Near-RT RIC
Manages E2 connections and subscriptions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from e2_messages import (
    E2SetupRequest, E2SetupResponse,
    RICSubscriptionRequest, RICIndication,
    RICControlRequest
)
from e2sm_kpm import E2SM_KPM, MeasurementRecord

logger = logging.getLogger(__name__)


@dataclass
class E2Node:
    """Connected E2 Node"""
    node_id: str
    node_type: str
    ran_functions: List[int]
    connected_at: datetime
    last_seen: datetime


@dataclass
class E2Subscription:
    """Active E2 Subscription"""
    subscription_id: int
    node_id: str
    ran_function_id: int
    callback: Callable
    created_at: datetime


class E2InterfaceManager:
    """Manages E2 interface connections and subscriptions"""

    def __init__(self):
        self.connected_nodes: Dict[str, E2Node] = {}
        self.subscriptions: Dict[int, E2Subscription] = {}
        self.next_subscription_id = 1
        self.running = False

    async def start(self):
        """Start E2 interface manager"""
        self.running = True
        logger.info("E2 Interface Manager started")
        # Start background tasks
        asyncio.create_task(self._health_check_loop())

    async def stop(self):
        """Stop E2 interface manager"""
        self.running = False
        logger.info("E2 Interface Manager stopped")

    async def handle_e2_setup(self, request: E2SetupRequest) -> E2SetupResponse:
        """Handle E2 Setup Request from E2 Node"""
        logger.info(f"E2 Setup Request from {request.global_e2_node_id}")

        # Register node
        node = E2Node(
            node_id=request.global_e2_node_id,
            node_type="gNB",  # Parse from node ID
            ran_functions=[rf["ranFunctionId"] for rf in request.ran_functions],
            connected_at=datetime.now(),
            last_seen=datetime.now()
        )

        self.connected_nodes[node.node_id] = node

        # Accept all RAN functions
        response = E2SetupResponse(
            transaction_id=request.transaction_id,
            global_ric_id="RIC-001",
            ran_functions_accepted=node.ran_functions
        )

        logger.info(f"E2 Setup successful for {node.node_id}")
        return response

    async def create_subscription(
        self,
        node_id: str,
        ran_function_id: int,
        callback: Callable
    ) -> int:
        """Create RIC subscription"""
        subscription_id = self.next_subscription_id
        self.next_subscription_id += 1

        subscription = E2Subscription(
            subscription_id=subscription_id,
            node_id=node_id,
            ran_function_id=ran_function_id,
            callback=callback,
            created_at=datetime.now()
        )

        self.subscriptions[subscription_id] = subscription

        # Send subscription request to E2 Node
        request = RICSubscriptionRequest(
            ric_request_id=subscription_id,
            ran_function_id=ran_function_id,
            ric_event_trigger_definition=E2SM_KPM.create_event_trigger(1000),
            ric_action_list=[{"ricActionId": 1, "ricActionType": "REPORT"}]
        )

        logger.info(f"Created subscription {subscription_id} for {node_id}")
        return subscription_id

    async def handle_ric_indication(self, indication: RICIndication):
        """Handle RIC Indication from E2 Node"""
        subscription_id = indication.ric_request_id

        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            await subscription.callback(indication)
        else:
            logger.warning(f"Received indication for unknown subscription {subscription_id}")

    async def send_control_request(
        self,
        node_id: str,
        ran_function_id: int,
        control_header: bytes,
        control_message: bytes
    ) -> bool:
        """Send RIC Control Request to E2 Node"""
        request = RICControlRequest(
            ric_request_id=0,
            ran_function_id=ran_function_id,
            ric_call_process_id=None,
            ric_control_header=control_header,
            ric_control_message=control_message
        )

        logger.info(f"Sending control request to {node_id}")
        # TODO: Implement actual sending via SCTP
        return True

    async def _health_check_loop(self):
        """Periodic health check for connected nodes"""
        while self.running:
            await asyncio.sleep(30)
            now = datetime.now()

            for node in self.connected_nodes.values():
                delta = (now - node.last_seen).total_seconds()
                if delta > 60:
                    logger.warning(f"Node {node.node_id} not seen for {delta}s")
