"""
E2AP (E2 Application Protocol) Message Definitions
Based on O-RAN WG3 E2AP v2.0 specification

Implements:
- E2 Setup Request/Response
- RIC Subscription Request/Response
- RIC Indication
- RIC Control Request/Response
- E2 Service Update
"""

import struct
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class E2APProcedureCode(Enum):
    """E2AP Procedure Codes (from O-RAN E2AP v2.0)"""
    E2_SETUP = 1
    ERROR_INDICATION = 2
    RESET = 3
    RIC_CONTROL = 4
    RIC_INDICATION = 5
    RIC_SERVICE_QUERY = 6
    RIC_SERVICE_UPDATE = 7
    RIC_SUBSCRIPTION = 8
    RIC_SUBSCRIPTION_DELETE = 9


class E2APMessageType(Enum):
    """E2AP Message Types"""
    INITIATING_MESSAGE = 0
    SUCCESSFUL_OUTCOME = 1
    UNSUCCESSFUL_OUTCOME = 2


class E2APCause(Enum):
    """E2AP Cause Values"""
    RIC_REQUEST = 1
    RIC_SERVICE = 2
    TRANSPORT = 3
    PROTOCOL = 4
    MISC = 5


@dataclass
class E2APMessageHeader:
    """E2AP Message Header (Common to all messages)"""
    procedure_code: int
    criticality: int  # 0=reject, 1=ignore, 2=notify
    message_type: int  # 0=initiating, 1=successful, 2=unsuccessful
    transaction_id: int = 0

    def encode(self) -> bytes:
        """Encode header to bytes (simplified encoding)"""
        # In real implementation, this would use ASN.1 PER encoding
        # Format: [proc_code(1), criticality(1), msg_type(1), trans_id(4)]
        return struct.pack('>BBBI',
                          self.procedure_code,
                          self.criticality,
                          self.message_type,
                          self.transaction_id)

    @staticmethod
    def decode(data: bytes) -> 'E2APMessageHeader':
        """Decode header from bytes"""
        proc_code, criticality, msg_type, trans_id = struct.unpack('>BBBI', data[:7])
        return E2APMessageHeader(proc_code, criticality, msg_type, trans_id)

    @staticmethod
    def header_size() -> int:
        """Get header size in bytes"""
        return 7


@dataclass
class RANFunctionDefinition:
    """RAN Function Definition (E2SM-specific)"""
    ran_function_id: int
    ran_function_revision: int
    ran_function_oid: str
    ran_function_description: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.ran_function_id,
            "revision": self.ran_function_revision,
            "oid": self.ran_function_oid,
            "description": self.ran_function_description
        }


@dataclass
class E2SetupRequest:
    """E2 Setup Request Message"""
    global_e2_node_id: str
    ran_functions: List[RANFunctionDefinition]
    e2_node_component_config: Optional[Dict[str, Any]] = None

    def encode(self) -> bytes:
        """Encode E2 Setup Request"""
        header = E2APMessageHeader(
            procedure_code=E2APProcedureCode.E2_SETUP.value,
            criticality=0,  # reject
            message_type=E2APMessageType.INITIATING_MESSAGE.value,
            transaction_id=int(time.time() * 1000) & 0xFFFFFFFF
        )

        payload = {
            "globalE2NodeID": self.global_e2_node_id,
            "ranFunctions": [rf.to_dict() for rf in self.ran_functions]
        }

        if self.e2_node_component_config:
            payload["e2NodeComponentConfig"] = self.e2_node_component_config

        payload_bytes = json.dumps(payload).encode('utf-8')
        length = len(payload_bytes)

        # Format: [header][length(4)][payload]
        return header.encode() + struct.pack('>I', length) + payload_bytes

    @staticmethod
    def decode(data: bytes) -> 'E2SetupRequest':
        """Decode E2 Setup Request"""
        header = E2APMessageHeader.decode(data)
        offset = E2APMessageHeader.header_size()

        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        payload = json.loads(data[offset:offset+length].decode('utf-8'))

        ran_functions = [
            RANFunctionDefinition(
                ran_function_id=rf["id"],
                ran_function_revision=rf["revision"],
                ran_function_oid=rf["oid"],
                ran_function_description=rf["description"]
            )
            for rf in payload.get("ranFunctions", [])
        ]

        return E2SetupRequest(
            global_e2_node_id=payload["globalE2NodeID"],
            ran_functions=ran_functions,
            e2_node_component_config=payload.get("e2NodeComponentConfig")
        )


@dataclass
class E2SetupResponse:
    """E2 Setup Response Message"""
    transaction_id: int
    global_ric_id: str
    ran_functions_accepted: List[int]
    ran_functions_rejected: Optional[List[Tuple[int, str]]] = None

    def encode(self) -> bytes:
        """Encode E2 Setup Response"""
        header = E2APMessageHeader(
            procedure_code=E2APProcedureCode.E2_SETUP.value,
            criticality=0,
            message_type=E2APMessageType.SUCCESSFUL_OUTCOME.value,
            transaction_id=self.transaction_id
        )

        payload = {
            "globalRICID": self.global_ric_id,
            "ranFunctionsAccepted": self.ran_functions_accepted
        }

        if self.ran_functions_rejected:
            payload["ranFunctionsRejected"] = [
                {"id": rf_id, "cause": cause}
                for rf_id, cause in self.ran_functions_rejected
            ]

        payload_bytes = json.dumps(payload).encode('utf-8')
        length = len(payload_bytes)

        return header.encode() + struct.pack('>I', length) + payload_bytes

    @staticmethod
    def decode(data: bytes) -> 'E2SetupResponse':
        """Decode E2 Setup Response"""
        header = E2APMessageHeader.decode(data)
        offset = E2APMessageHeader.header_size()

        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        payload = json.loads(data[offset:offset+length].decode('utf-8'))

        ran_functions_rejected = None
        if "ranFunctionsRejected" in payload:
            ran_functions_rejected = [
                (rf["id"], rf["cause"])
                for rf in payload["ranFunctionsRejected"]
            ]

        return E2SetupResponse(
            transaction_id=header.transaction_id,
            global_ric_id=payload["globalRICID"],
            ran_functions_accepted=payload["ranFunctionsAccepted"],
            ran_functions_rejected=ran_functions_rejected
        )


@dataclass
class RICSubscriptionRequest:
    """RIC Subscription Request Message"""
    ric_request_id: int
    ran_function_id: int
    ric_event_trigger_definition: bytes
    ric_actions: List[Dict[str, Any]]

    def encode(self) -> bytes:
        """Encode RIC Subscription Request"""
        header = E2APMessageHeader(
            procedure_code=E2APProcedureCode.RIC_SUBSCRIPTION.value,
            criticality=0,
            message_type=E2APMessageType.INITIATING_MESSAGE.value,
            transaction_id=self.ric_request_id
        )

        payload = {
            "ricRequestID": self.ric_request_id,
            "ranFunctionID": self.ran_function_id,
            "ricEventTriggerDefinition": self.ric_event_trigger_definition.hex(),
            "ricActions": self.ric_actions
        }

        payload_bytes = json.dumps(payload).encode('utf-8')
        length = len(payload_bytes)

        return header.encode() + struct.pack('>I', length) + payload_bytes

    @staticmethod
    def decode(data: bytes) -> 'RICSubscriptionRequest':
        """Decode RIC Subscription Request"""
        header = E2APMessageHeader.decode(data)
        offset = E2APMessageHeader.header_size()

        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        payload = json.loads(data[offset:offset+length].decode('utf-8'))

        return RICSubscriptionRequest(
            ric_request_id=payload["ricRequestID"],
            ran_function_id=payload["ranFunctionID"],
            ric_event_trigger_definition=bytes.fromhex(payload["ricEventTriggerDefinition"]),
            ric_actions=payload["ricActions"]
        )


@dataclass
class RICSubscriptionResponse:
    """RIC Subscription Response Message"""
    ric_request_id: int
    ran_function_id: int
    ric_actions_admitted: List[int]
    ric_actions_not_admitted: Optional[List[Tuple[int, str]]] = None

    def encode(self) -> bytes:
        """Encode RIC Subscription Response"""
        header = E2APMessageHeader(
            procedure_code=E2APProcedureCode.RIC_SUBSCRIPTION.value,
            criticality=0,
            message_type=E2APMessageType.SUCCESSFUL_OUTCOME.value,
            transaction_id=self.ric_request_id
        )

        payload = {
            "ricRequestID": self.ric_request_id,
            "ranFunctionID": self.ran_function_id,
            "ricActionsAdmitted": self.ric_actions_admitted
        }

        if self.ric_actions_not_admitted:
            payload["ricActionsNotAdmitted"] = [
                {"id": action_id, "cause": cause}
                for action_id, cause in self.ric_actions_not_admitted
            ]

        payload_bytes = json.dumps(payload).encode('utf-8')
        length = len(payload_bytes)

        return header.encode() + struct.pack('>I', length) + payload_bytes

    @staticmethod
    def decode(data: bytes) -> 'RICSubscriptionResponse':
        """Decode RIC Subscription Response"""
        header = E2APMessageHeader.decode(data)
        offset = E2APMessageHeader.header_size()

        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        payload = json.loads(data[offset:offset+length].decode('utf-8'))

        ric_actions_not_admitted = None
        if "ricActionsNotAdmitted" in payload:
            ric_actions_not_admitted = [
                (action["id"], action["cause"])
                for action in payload["ricActionsNotAdmitted"]
            ]

        return RICSubscriptionResponse(
            ric_request_id=payload["ricRequestID"],
            ran_function_id=payload["ranFunctionID"],
            ric_actions_admitted=payload["ricActionsAdmitted"],
            ric_actions_not_admitted=ric_actions_not_admitted
        )


@dataclass
class RICIndication:
    """RIC Indication Message"""
    ric_request_id: int
    ran_function_id: int
    ric_action_id: int
    ric_indication_sn: int
    ric_indication_type: int  # 0=report, 1=insert
    ric_indication_header: bytes
    ric_indication_message: bytes
    ric_call_process_id: Optional[bytes] = None

    def encode(self) -> bytes:
        """Encode RIC Indication"""
        header = E2APMessageHeader(
            procedure_code=E2APProcedureCode.RIC_INDICATION.value,
            criticality=1,  # ignore
            message_type=E2APMessageType.INITIATING_MESSAGE.value,
            transaction_id=self.ric_indication_sn
        )

        payload = {
            "ricRequestID": self.ric_request_id,
            "ranFunctionID": self.ran_function_id,
            "ricActionID": self.ric_action_id,
            "ricIndicationSN": self.ric_indication_sn,
            "ricIndicationType": self.ric_indication_type,
            "ricIndicationHeader": self.ric_indication_header.hex(),
            "ricIndicationMessage": self.ric_indication_message.hex()
        }

        if self.ric_call_process_id:
            payload["ricCallProcessID"] = self.ric_call_process_id.hex()

        payload_bytes = json.dumps(payload).encode('utf-8')
        length = len(payload_bytes)

        return header.encode() + struct.pack('>I', length) + payload_bytes

    @staticmethod
    def decode(data: bytes) -> 'RICIndication':
        """Decode RIC Indication"""
        header = E2APMessageHeader.decode(data)
        offset = E2APMessageHeader.header_size()

        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        payload = json.loads(data[offset:offset+length].decode('utf-8'))

        ric_call_process_id = None
        if "ricCallProcessID" in payload:
            ric_call_process_id = bytes.fromhex(payload["ricCallProcessID"])

        return RICIndication(
            ric_request_id=payload["ricRequestID"],
            ran_function_id=payload["ranFunctionID"],
            ric_action_id=payload["ricActionID"],
            ric_indication_sn=payload["ricIndicationSN"],
            ric_indication_type=payload["ricIndicationType"],
            ric_indication_header=bytes.fromhex(payload["ricIndicationHeader"]),
            ric_indication_message=bytes.fromhex(payload["ricIndicationMessage"]),
            ric_call_process_id=ric_call_process_id
        )


@dataclass
class RICControlRequest:
    """RIC Control Request Message"""
    ric_request_id: int
    ran_function_id: int
    ric_call_process_id: Optional[bytes]
    ric_control_header: bytes
    ric_control_message: bytes
    ric_control_ack_request: int = 1  # 0=no-ack, 1=ack, 2=nack

    def encode(self) -> bytes:
        """Encode RIC Control Request"""
        header = E2APMessageHeader(
            procedure_code=E2APProcedureCode.RIC_CONTROL.value,
            criticality=0,
            message_type=E2APMessageType.INITIATING_MESSAGE.value,
            transaction_id=self.ric_request_id
        )

        payload = {
            "ricRequestID": self.ric_request_id,
            "ranFunctionID": self.ran_function_id,
            "ricControlHeader": self.ric_control_header.hex(),
            "ricControlMessage": self.ric_control_message.hex(),
            "ricControlAckRequest": self.ric_control_ack_request
        }

        if self.ric_call_process_id:
            payload["ricCallProcessID"] = self.ric_call_process_id.hex()

        payload_bytes = json.dumps(payload).encode('utf-8')
        length = len(payload_bytes)

        return header.encode() + struct.pack('>I', length) + payload_bytes

    @staticmethod
    def decode(data: bytes) -> 'RICControlRequest':
        """Decode RIC Control Request"""
        header = E2APMessageHeader.decode(data)
        offset = E2APMessageHeader.header_size()

        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        payload = json.loads(data[offset:offset+length].decode('utf-8'))

        ric_call_process_id = None
        if "ricCallProcessID" in payload:
            ric_call_process_id = bytes.fromhex(payload["ricCallProcessID"])

        return RICControlRequest(
            ric_request_id=payload["ricRequestID"],
            ran_function_id=payload["ranFunctionID"],
            ric_call_process_id=ric_call_process_id,
            ric_control_header=bytes.fromhex(payload["ricControlHeader"]),
            ric_control_message=bytes.fromhex(payload["ricControlMessage"]),
            ric_control_ack_request=payload.get("ricControlAckRequest", 1)
        )


@dataclass
class RICControlAcknowledge:
    """RIC Control Acknowledge Message"""
    ric_request_id: int
    ran_function_id: int
    ric_call_process_id: Optional[bytes]
    ric_control_outcome: Optional[bytes] = None

    def encode(self) -> bytes:
        """Encode RIC Control Acknowledge"""
        header = E2APMessageHeader(
            procedure_code=E2APProcedureCode.RIC_CONTROL.value,
            criticality=0,
            message_type=E2APMessageType.SUCCESSFUL_OUTCOME.value,
            transaction_id=self.ric_request_id
        )

        payload = {
            "ricRequestID": self.ric_request_id,
            "ranFunctionID": self.ran_function_id
        }

        if self.ric_call_process_id:
            payload["ricCallProcessID"] = self.ric_call_process_id.hex()

        if self.ric_control_outcome:
            payload["ricControlOutcome"] = self.ric_control_outcome.hex()

        payload_bytes = json.dumps(payload).encode('utf-8')
        length = len(payload_bytes)

        return header.encode() + struct.pack('>I', length) + payload_bytes

    @staticmethod
    def decode(data: bytes) -> 'RICControlAcknowledge':
        """Decode RIC Control Acknowledge"""
        header = E2APMessageHeader.decode(data)
        offset = E2APMessageHeader.header_size()

        length = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        payload = json.loads(data[offset:offset+length].decode('utf-8'))

        ric_call_process_id = None
        if "ricCallProcessID" in payload:
            ric_call_process_id = bytes.fromhex(payload["ricCallProcessID"])

        ric_control_outcome = None
        if "ricControlOutcome" in payload:
            ric_control_outcome = bytes.fromhex(payload["ricControlOutcome"])

        return RICControlAcknowledge(
            ric_request_id=payload["ricRequestID"],
            ran_function_id=payload["ranFunctionID"],
            ric_call_process_id=ric_call_process_id,
            ric_control_outcome=ric_control_outcome
        )


class E2APMessageFactory:
    """Factory for creating and parsing E2AP messages"""

    @staticmethod
    def parse_message(data: bytes) -> Any:
        """
        Parse E2AP message from bytes

        Args:
            data: Raw message bytes

        Returns:
            Parsed E2AP message object
        """
        if len(data) < E2APMessageHeader.header_size():
            raise ValueError("Message too short to contain valid header")

        header = E2APMessageHeader.decode(data)

        # Route to appropriate decoder based on procedure code
        if header.procedure_code == E2APProcedureCode.E2_SETUP.value:
            if header.message_type == E2APMessageType.INITIATING_MESSAGE.value:
                return E2SetupRequest.decode(data)
            elif header.message_type == E2APMessageType.SUCCESSFUL_OUTCOME.value:
                return E2SetupResponse.decode(data)

        elif header.procedure_code == E2APProcedureCode.RIC_SUBSCRIPTION.value:
            if header.message_type == E2APMessageType.INITIATING_MESSAGE.value:
                return RICSubscriptionRequest.decode(data)
            elif header.message_type == E2APMessageType.SUCCESSFUL_OUTCOME.value:
                return RICSubscriptionResponse.decode(data)

        elif header.procedure_code == E2APProcedureCode.RIC_INDICATION.value:
            return RICIndication.decode(data)

        elif header.procedure_code == E2APProcedureCode.RIC_CONTROL.value:
            if header.message_type == E2APMessageType.INITIATING_MESSAGE.value:
                return RICControlRequest.decode(data)
            elif header.message_type == E2APMessageType.SUCCESSFUL_OUTCOME.value:
                return RICControlAcknowledge.decode(data)

        raise ValueError(f"Unknown message type: procedure={header.procedure_code}, type={header.message_type}")

    @staticmethod
    def get_message_type(data: bytes) -> Tuple[int, int]:
        """
        Get message procedure code and type without full parsing

        Returns:
            Tuple of (procedure_code, message_type)
        """
        header = E2APMessageHeader.decode(data)
        return (header.procedure_code, header.message_type)
