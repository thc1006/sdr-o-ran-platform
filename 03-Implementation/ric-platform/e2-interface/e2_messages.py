"""
O-RAN E2 Interface Protocol Messages
Based on ETSI TS 104 039 V4.0.0 (E2AP)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class E2MessageType(Enum):
    """E2AP Message Types"""
    E2_SETUP_REQUEST = 1
    E2_SETUP_RESPONSE = 2
    E2_SETUP_FAILURE = 3
    RIC_SUBSCRIPTION_REQUEST = 4
    RIC_SUBSCRIPTION_RESPONSE = 5
    RIC_SUBSCRIPTION_FAILURE = 6
    RIC_INDICATION = 7
    RIC_CONTROL_REQUEST = 8
    RIC_CONTROL_ACKNOWLEDGE = 9
    RIC_CONTROL_FAILURE = 10


class E2NodeType(Enum):
    """E2 Node Types"""
    GNB = "gNB"
    EN_GNB = "en-gNB"
    NG_ENB = "ng-eNB"
    ENB = "eNB"


@dataclass
class E2NodeComponentConfig:
    """E2 Node Component Configuration"""
    component_type: str  # E2NodeComponentType
    component_id: int
    request_id: int = 0


@dataclass
class E2SetupRequest:
    """E2 Setup Request Message"""
    transaction_id: int
    global_e2_node_id: str
    ran_functions: List[Dict]  # RAN Function definitions
    e2_node_component_config: List[E2NodeComponentConfig]

    def to_dict(self) -> Dict:
        return {
            "transactionId": self.transaction_id,
            "globalE2NodeId": self.global_e2_node_id,
            "ranFunctions": self.ran_functions,
            "e2NodeComponentConfig": [
                {
                    "componentType": c.component_type,
                    "componentId": c.component_id
                }
                for c in self.e2_node_component_config
            ]
        }


@dataclass
class E2SetupResponse:
    """E2 Setup Response Message"""
    transaction_id: int
    global_ric_id: str
    ran_functions_accepted: List[int]  # RAN Function IDs

    def to_dict(self) -> Dict:
        return {
            "transactionId": self.transaction_id,
            "globalRicId": self.global_ric_id,
            "ranFunctionsAccepted": self.ran_functions_accepted
        }


@dataclass
class RICSubscriptionRequest:
    """RIC Subscription Request"""
    ric_request_id: int
    ran_function_id: int
    ric_event_trigger_definition: bytes  # E2SM specific
    ric_action_list: List[Dict]

    def to_dict(self) -> Dict:
        return {
            "ricRequestId": self.ric_request_id,
            "ranFunctionId": self.ran_function_id,
            "ricEventTriggerDefinition": self.ric_event_trigger_definition.hex(),
            "ricActionList": self.ric_action_list
        }


@dataclass
class RICIndication:
    """RIC Indication Message"""
    ric_request_id: int
    ran_function_id: int
    ric_action_id: int
    ric_indication_header: bytes  # E2SM specific
    ric_indication_message: bytes  # E2SM specific
    ric_call_process_id: Optional[bytes] = None

    def to_dict(self) -> Dict:
        return {
            "ricRequestId": self.ric_request_id,
            "ranFunctionId": self.ran_function_id,
            "ricActionId": self.ric_action_id,
            "ricIndicationHeader": self.ric_indication_header.hex(),
            "ricIndicationMessage": self.ric_indication_message.hex()
        }


@dataclass
class RICControlRequest:
    """RIC Control Request"""
    ric_request_id: int
    ran_function_id: int
    ric_call_process_id: Optional[bytes]
    ric_control_header: bytes  # E2SM specific
    ric_control_message: bytes  # E2SM specific
    ric_control_ack_request: bool = True

    def to_dict(self) -> Dict:
        return {
            "ricRequestId": self.ric_request_id,
            "ranFunctionId": self.ran_function_id,
            "ricControlHeader": self.ric_control_header.hex(),
            "ricControlMessage": self.ric_control_message.hex(),
            "ricControlAckRequest": self.ric_control_ack_request
        }
