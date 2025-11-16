"""
E2 Service Model - Key Performance Metrics (E2SM-KPM v3.0)
Based on ETSI TS 104 040 V4.0.0
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class MeasurementType(Enum):
    """Measurement Types for KPM"""
    DRB_UE_THROUGHPUT_DL = "DRB.UEThpDl"
    DRB_UE_THROUGHPUT_UL = "DRB.UEThpUl"
    RRC_CONN_ESTAB_SUCC = "RRC.ConnEstabSucc"
    RRC_CONN_ESTAB_ATT = "RRC.ConnEstabAtt"
    HANDOVER_SUCC_RATE = "HANDOVER.SuccRate"


@dataclass
class MeasurementRecord:
    """Single measurement record"""
    measurement_type: MeasurementType
    value: float
    timestamp: int  # Unix timestamp in nanoseconds
    ue_id: Optional[str] = None
    cell_id: Optional[str] = None


@dataclass
class KPMIndicationHeader:
    """E2SM-KPM Indication Header"""
    collection_start_time: int
    granularity_period: int  # milliseconds

    def encode(self) -> bytes:
        """Encode to bytes (simplified, real implementation uses ASN.1)"""
        # Simplified encoding for demo
        import struct
        return struct.pack('>QI', self.collection_start_time, self.granularity_period)


@dataclass
class KPMIndicationMessage:
    """E2SM-KPM Indication Message"""
    measurement_records: List[MeasurementRecord]

    def encode(self) -> bytes:
        """Encode to bytes (simplified)"""
        import json
        data = {
            "measurements": [
                {
                    "type": m.measurement_type.value,
                    "value": m.value,
                    "timestamp": m.timestamp,
                    "ueId": m.ue_id,
                    "cellId": m.cell_id
                }
                for m in self.measurement_records
            ]
        }
        return json.dumps(data).encode('utf-8')


class E2SM_KPM:
    """E2 Service Model - KPM"""

    RAN_FUNCTION_ID = 1
    RAN_FUNCTION_DEFINITION = {
        "ranFunctionId": 1,
        "ranFunctionDefinition": {
            "ranFunctionName": {
                "ranFunctionShortName": "ORAN-E2SM-KPM",
                "ranFunctionE2SMOid": "1.3.6.1.4.1.53148.1.1.2.3"
            },
            "ricEventTriggerStyle": [
                {
                    "ricEventTriggerStyleType": 1,
                    "ricEventTriggerFormatType": 1,
                    "ricEventTriggerStyleName": "Periodic"
                }
            ],
            "ricReportStyle": [
                {
                    "ricReportStyleType": 1,
                    "ricReportStyleName": "UE Throughput Report",
                    "ricIndicationHeaderFormatType": 1,
                    "ricIndicationMessageFormatType": 1
                }
            ]
        }
    }

    @staticmethod
    def create_event_trigger(period_ms: int) -> bytes:
        """Create event trigger definition for periodic reporting"""
        import struct
        # Simplified: real implementation uses ASN.1
        return struct.pack('>I', period_ms)

    @staticmethod
    def create_indication(measurements: List[MeasurementRecord]) -> tuple:
        """Create indication header and message"""
        import time

        header = KPMIndicationHeader(
            collection_start_time=int(time.time() * 1e9),
            granularity_period=1000  # 1 second
        )

        message = KPMIndicationMessage(
            measurement_records=measurements
        )

        return header.encode(), message.encode()
