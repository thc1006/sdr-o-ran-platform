"""
E2 Service Model - Non-Terrestrial Networks (E2SM-NTN v1.0)
Based on E2SM-NTN-SPECIFICATION.md and O-RAN E2 standards

This module implements the E2SM-NTN service model for integrating NTN metrics
into the O-RAN E2 Interface.
"""

import json
import struct
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np

try:
    from .asn1_codec import E2SM_NTN_ASN1_Codec, ASN1CodecError
except ImportError:
    # Handle direct execution (non-package import)
    try:
        from asn1_codec import E2SM_NTN_ASN1_Codec, ASN1CodecError
    except ImportError:
        # ASN.1 codec not available
        E2SM_NTN_ASN1_Codec = None
        ASN1CodecError = Exception


class OrbitType(Enum):
    """Satellite orbit type classification"""
    LEO = "LEO"  # Low Earth Orbit (600-1200 km)
    MEO = "MEO"  # Medium Earth Orbit (7000-25000 km)
    GEO = "GEO"  # Geostationary Orbit (35786 km)


class NTNEventTrigger(Enum):
    """Event trigger types for NTN"""
    PERIODIC = 1
    ELEVATION_THRESHOLD = 2
    HANDOVER_IMMINENT = 3
    LINK_QUALITY_ALERT = 4
    DOPPLER_THRESHOLD = 5
    RAIN_FADE_DETECTED = 6


class NTNControlAction(Enum):
    """Control action types for NTN"""
    POWER_CONTROL = 1
    TRIGGER_HANDOVER = 2
    DOPPLER_COMPENSATION = 3
    LINK_ADAPTATION = 4
    BEAM_SWITCH = 5
    ACTIVATE_FADE_MITIGATION = 6


@dataclass
class SatelliteMetrics:
    """Satellite identification and orbital metrics"""
    satellite_id: str
    orbit_type: str
    beam_id: int
    elevation_angle: float  # degrees
    azimuth_angle: float  # degrees
    slant_range_km: float
    satellite_velocity: float  # km/s
    angular_velocity: float  # deg/s


@dataclass
class ChannelQuality:
    """Channel quality metrics"""
    rsrp: float  # dBm
    rsrq: float  # dB
    sinr: float  # dB
    bler: float  # Block Error Rate (0-1)
    cqi: int  # Channel Quality Indicator (0-15)


@dataclass
class NTNImpairments:
    """NTN-specific impairment metrics"""
    doppler_shift_hz: float
    doppler_rate_hz_s: float
    propagation_delay_ms: float
    path_loss_db: float
    rain_attenuation_db: float
    atmospheric_loss_db: float


@dataclass
class LinkBudget:
    """Link budget metrics"""
    tx_power_dbm: float
    rx_power_dbm: float
    link_margin_db: float
    snr_db: float
    required_snr_db: float


@dataclass
class HandoverPrediction:
    """Handover prediction metrics"""
    time_to_handover_sec: float
    handover_trigger_threshold: float  # degrees
    next_satellite_id: Optional[str]
    next_satellite_elevation: float
    handover_probability: float


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    throughput_dl_mbps: float
    throughput_ul_mbps: float
    latency_rtt_ms: float
    packet_loss_rate: float


@dataclass
class NTNIndicationMessage:
    """Complete NTN indication message"""
    timestamp_ns: int
    ue_id: str
    satellite_metrics: SatelliteMetrics
    channel_quality: ChannelQuality
    ntn_impairments: NTNImpairments
    link_budget: LinkBudget
    handover_prediction: HandoverPrediction
    performance: PerformanceMetrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp_ns": self.timestamp_ns,
            "ue_id": self.ue_id,
            "satellite_metrics": asdict(self.satellite_metrics),
            "channel_quality": asdict(self.channel_quality),
            "ntn_impairments": asdict(self.ntn_impairments),
            "link_budget": asdict(self.link_budget),
            "handover_prediction": asdict(self.handover_prediction),
            "performance": asdict(self.performance)
        }

    def encode(self) -> bytes:
        """Encode to bytes (JSON encoding for simplicity)"""
        return json.dumps(self.to_dict()).encode('utf-8')


@dataclass
class NTNIndicationHeader:
    """E2SM-NTN Indication Header"""
    timestamp_ns: int
    satellite_id: str
    orbit_type: str
    granularity_period_ms: int
    measurement_type: str  # "periodic" or "event-triggered"

    def encode(self) -> bytes:
        """Encode header to bytes (simplified encoding)"""
        header_dict = {
            "timestamp_ns": self.timestamp_ns,
            "satellite_id": self.satellite_id,
            "orbit_type": self.orbit_type,
            "granularity_period_ms": self.granularity_period_ms,
            "measurement_type": self.measurement_type
        }
        return json.dumps(header_dict).encode('utf-8')


@dataclass
class NTNControlMessage:
    """NTN Control Message (RIC Control)"""
    action_type: str
    ue_id: str
    parameters: Dict[str, Any]

    @staticmethod
    def from_bytes(data: bytes) -> 'NTNControlMessage':
        """Decode control message from bytes"""
        control_dict = json.loads(data.decode('utf-8'))
        return NTNControlMessage(
            action_type=control_dict["actionType"],
            ue_id=control_dict["ue_id"],
            parameters=control_dict["parameters"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "actionType": self.action_type,
            "ue_id": self.ue_id,
            "parameters": self.parameters
        }


class E2SM_NTN:
    """E2 Service Model for Non-Terrestrial Networks"""

    RAN_FUNCTION_ID = 10
    RAN_FUNCTION_SHORT_NAME = "ORAN-E2SM-NTN"
    RAN_FUNCTION_OID = "1.3.6.1.4.1.53148.1.1.2.10"
    VERSION = "1.0.0"

    # Physical constants
    SPEED_OF_LIGHT = 299792.458  # km/s
    EARTH_RADIUS = 6371.0  # km

    # Default thresholds
    DEFAULT_MIN_ELEVATION = 10.0  # degrees
    DEFAULT_HANDOVER_PREPARATION_TIME = 30.0  # seconds
    DEFAULT_RECEIVER_SENSITIVITY = -110.0  # dBm

    RAN_FUNCTION_DEFINITION = {
        "ranFunctionId": RAN_FUNCTION_ID,
        "ranFunctionDefinition": {
            "ranFunctionName": {
                "ranFunctionShortName": RAN_FUNCTION_SHORT_NAME,
                "ranFunctionE2SMOid": RAN_FUNCTION_OID
            },
            "ricEventTriggerStyle": [
                {
                    "ricEventTriggerStyleType": 1,
                    "ricEventTriggerFormatType": 1,
                    "ricEventTriggerStyleName": "Periodic NTN Metrics"
                },
                {
                    "ricEventTriggerStyleType": 2,
                    "ricEventTriggerFormatType": 2,
                    "ricEventTriggerStyleName": "Elevation Threshold"
                },
                {
                    "ricEventTriggerStyleType": 3,
                    "ricEventTriggerFormatType": 3,
                    "ricEventTriggerStyleName": "Handover Imminent"
                },
                {
                    "ricEventTriggerStyleType": 4,
                    "ricEventTriggerFormatType": 4,
                    "ricEventTriggerStyleName": "Link Quality Alert"
                }
            ],
            "ricReportStyle": [
                {
                    "ricReportStyleType": 1,
                    "ricReportStyleName": "Full NTN Metrics",
                    "ricIndicationHeaderFormatType": 1,
                    "ricIndicationMessageFormatType": 1
                },
                {
                    "ricReportStyleType": 2,
                    "ricReportStyleName": "Minimal NTN Report",
                    "ricIndicationHeaderFormatType": 1,
                    "ricIndicationMessageFormatType": 2
                },
                {
                    "ricReportStyleType": 3,
                    "ricReportStyleName": "Handover Preparation",
                    "ricIndicationHeaderFormatType": 1,
                    "ricIndicationMessageFormatType": 3
                }
            ]
        }
    }

    def __init__(self, channel_model=None, encoding: str = 'asn1'):
        """
        Initialize E2SM-NTN service model

        Args:
            channel_model: Optional OpenNTN channel model instance
            encoding: Message encoding format ('asn1' or 'json'). Default: 'asn1'
        """
        self.channel_model = channel_model
        self.min_elevation_threshold = self.DEFAULT_MIN_ELEVATION
        self.receiver_sensitivity = self.DEFAULT_RECEIVER_SENSITIVITY
        self.encoding = encoding

        # Initialize ASN.1 codec if using ASN.1 encoding
        if self.encoding == 'asn1':
            if E2SM_NTN_ASN1_Codec is None:
                # ASN.1 codec not available, fall back to JSON
                self.encoding = 'json'
                self.asn1_codec = None
                import logging
                logging.warning("ASN.1 codec not available, falling back to JSON encoding")
            else:
                try:
                    self.asn1_codec = E2SM_NTN_ASN1_Codec()
                except Exception as e:
                    # Fall back to JSON if ASN.1 codec fails to initialize
                    self.encoding = 'json'
                    self.asn1_codec = None
                    import logging
                    logging.warning(f"Failed to initialize ASN.1 codec, falling back to JSON: {e}")
        else:
            self.asn1_codec = None

    @staticmethod
    def create_event_trigger(trigger_type: NTNEventTrigger, **params) -> bytes:
        """
        Create event trigger definition

        Args:
            trigger_type: Type of event trigger
            **params: Trigger-specific parameters

        Returns:
            Encoded event trigger definition
        """
        trigger_def = {
            "triggerType": trigger_type.value,
            "parameters": params
        }
        return json.dumps(trigger_def).encode('utf-8')

    def create_indication_message(
        self,
        ue_id: str,
        satellite_state: Dict[str, Any],
        ue_measurements: Dict[str, float],
        report_style: int = 1
    ) -> Tuple[bytes, bytes]:
        """
        Create RIC Indication message with NTN metrics

        Args:
            ue_id: UE identifier
            satellite_state: Satellite orbital state
            ue_measurements: UE measurement report
            report_style: Report style (1=Full, 2=Minimal, 3=Handover)

        Returns:
            Tuple of (indication_header, indication_message)
        """
        timestamp_ns = int(time.time() * 1e9)

        # Extract satellite metrics
        sat_metrics = SatelliteMetrics(
            satellite_id=satellite_state.get("satellite_id", "UNKNOWN"),
            orbit_type=satellite_state.get("orbit_type", "LEO"),
            beam_id=satellite_state.get("beam_id", 1),
            elevation_angle=satellite_state.get("elevation_angle", 0.0),
            azimuth_angle=satellite_state.get("azimuth_angle", 0.0),
            slant_range_km=satellite_state.get("slant_range_km", 0.0),
            satellite_velocity=satellite_state.get("satellite_velocity", 0.0),
            angular_velocity=satellite_state.get("angular_velocity", 0.0)
        )

        # Calculate NTN KPMs
        ntn_kpms = self.calculate_ntn_kpms(
            elevation_angle=sat_metrics.elevation_angle,
            slant_range_km=sat_metrics.slant_range_km,
            measurements=ue_measurements,
            satellite_state=satellite_state
        )

        # Create indication header
        header = NTNIndicationHeader(
            timestamp_ns=timestamp_ns,
            satellite_id=sat_metrics.satellite_id,
            orbit_type=sat_metrics.orbit_type,
            granularity_period_ms=1000,
            measurement_type="periodic"
        )

        # Create indication message
        message = NTNIndicationMessage(
            timestamp_ns=timestamp_ns,
            ue_id=ue_id,
            satellite_metrics=sat_metrics,
            channel_quality=ntn_kpms["channel_quality"],
            ntn_impairments=ntn_kpms["ntn_impairments"],
            link_budget=ntn_kpms["link_budget"],
            handover_prediction=ntn_kpms["handover_prediction"],
            performance=ntn_kpms["performance"]
        )

        # Encode based on selected encoding
        if self.encoding == 'asn1' and self.asn1_codec is not None:
            # Use ASN.1 PER encoding
            message_dict = message.to_dict()
            encoded_msg, _ = self.asn1_codec.encode_indication_message(message_dict, format_type=1)
            return header.encode(), encoded_msg
        else:
            # Use JSON encoding (default fallback)
            return header.encode(), message.encode()

    def calculate_ntn_kpms(
        self,
        elevation_angle: float,
        slant_range_km: float,
        measurements: Dict[str, float],
        satellite_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate all NTN-specific KPMs

        Args:
            elevation_angle: Current elevation angle (degrees)
            slant_range_km: Slant range to satellite (km)
            measurements: UE measurements (RSRP, SINR, etc.)
            satellite_state: Satellite state information

        Returns:
            Dictionary containing all calculated KPMs
        """
        # Channel quality metrics
        rsrp = measurements.get("rsrp", -100.0)
        rsrq = measurements.get("rsrq", -15.0)
        sinr = measurements.get("sinr", 10.0)
        bler = measurements.get("bler", 0.01)
        cqi = self._calculate_cqi(sinr)

        channel_quality = ChannelQuality(
            rsrp=rsrp,
            rsrq=rsrq,
            sinr=sinr,
            bler=bler,
            cqi=cqi
        )

        # NTN impairments
        doppler_shift = self._calculate_doppler_shift(
            satellite_velocity=satellite_state.get("satellite_velocity", 7.5),
            elevation_angle=elevation_angle,
            carrier_frequency_ghz=satellite_state.get("carrier_frequency_ghz", 2.1)
        )

        propagation_delay = self._calculate_propagation_delay(slant_range_km)
        path_loss = self._calculate_path_loss(slant_range_km, elevation_angle)
        rain_attenuation = measurements.get("rain_attenuation_db", 0.0)
        atmospheric_loss = measurements.get("atmospheric_loss_db", 0.5)

        ntn_impairments = NTNImpairments(
            doppler_shift_hz=doppler_shift,
            doppler_rate_hz_s=satellite_state.get("doppler_rate", -45.0),
            propagation_delay_ms=propagation_delay,
            path_loss_db=path_loss,
            rain_attenuation_db=rain_attenuation,
            atmospheric_loss_db=atmospheric_loss
        )

        # Link budget
        tx_power = measurements.get("tx_power_dbm", 23.0)
        rx_power = rsrp
        link_margin = self._calculate_link_margin(rx_power, self.receiver_sensitivity)
        snr = sinr
        required_snr = self._calculate_required_snr(bler)

        link_budget = LinkBudget(
            tx_power_dbm=tx_power,
            rx_power_dbm=rx_power,
            link_margin_db=link_margin,
            snr_db=snr,
            required_snr_db=required_snr
        )

        # Handover prediction
        handover_metrics = self.predict_handover_time(
            current_elevation=elevation_angle,
            satellite_velocity=satellite_state.get("satellite_velocity", 7.5),
            angular_velocity=satellite_state.get("angular_velocity", 0.5)
        )

        handover_prediction = HandoverPrediction(
            time_to_handover_sec=handover_metrics["time_to_handover_sec"],
            handover_trigger_threshold=self.min_elevation_threshold,
            next_satellite_id=satellite_state.get("next_satellite_id"),
            next_satellite_elevation=satellite_state.get("next_satellite_elevation", 5.0),
            handover_probability=handover_metrics["handover_probability"]
        )

        # Performance metrics
        performance = PerformanceMetrics(
            throughput_dl_mbps=measurements.get("throughput_dl_mbps", 50.0),
            throughput_ul_mbps=measurements.get("throughput_ul_mbps", 10.0),
            latency_rtt_ms=propagation_delay * 2 + 5.0,  # 2x prop delay + processing
            packet_loss_rate=measurements.get("packet_loss_rate", 0.01)
        )

        return {
            "channel_quality": channel_quality,
            "ntn_impairments": ntn_impairments,
            "link_budget": link_budget,
            "handover_prediction": handover_prediction,
            "performance": performance
        }

    def _calculate_doppler_shift(
        self,
        satellite_velocity: float,
        elevation_angle: float,
        carrier_frequency_ghz: float
    ) -> float:
        """
        Calculate Doppler shift in Hz

        Formula: doppler = (v/c) * f * cos(elevation)
        """
        elevation_rad = np.radians(elevation_angle)
        doppler_shift = (satellite_velocity / self.SPEED_OF_LIGHT) * \
                       (carrier_frequency_ghz * 1e9) * np.cos(elevation_rad)
        return float(doppler_shift)

    def _calculate_propagation_delay(self, slant_range_km: float) -> float:
        """Calculate one-way propagation delay in milliseconds"""
        delay_ms = slant_range_km / self.SPEED_OF_LIGHT * 1000.0
        return float(delay_ms)

    def _calculate_path_loss(self, slant_range_km: float, elevation_angle: float) -> float:
        """
        Calculate free-space path loss in dB

        Formula: PL = 32.45 + 20*log10(d_km) + 20*log10(f_MHz)
        """
        # Assuming 2.1 GHz carrier
        frequency_mhz = 2100.0
        path_loss = 32.45 + 20 * np.log10(slant_range_km) + 20 * np.log10(frequency_mhz)

        # Add atmospheric loss (simple model)
        atmospheric_factor = 1.0 / np.sin(np.radians(max(elevation_angle, 5.0)))
        atmospheric_loss = 0.5 * atmospheric_factor

        return float(path_loss + atmospheric_loss)

    def _calculate_link_margin(self, rx_power_dbm: float, sensitivity_dbm: float) -> float:
        """Calculate link margin in dB"""
        return float(rx_power_dbm - sensitivity_dbm)

    def _calculate_cqi(self, sinr_db: float) -> int:
        """Map SINR to CQI (0-15)"""
        # Simplified CQI mapping
        if sinr_db < -6.0:
            return 0
        elif sinr_db > 22.0:
            return 15
        else:
            # Linear mapping from -6 dB to 22 dB
            cqi = int((sinr_db + 6.0) / 28.0 * 15)
            return max(0, min(15, cqi))

    def _calculate_required_snr(self, target_bler: float) -> float:
        """Calculate required SNR for target BLER"""
        # Simplified: assuming QPSK 1/2
        # Real implementation would use link adaptation tables
        if target_bler <= 0.001:
            return 12.0
        elif target_bler <= 0.01:
            return 9.0
        elif target_bler <= 0.1:
            return 6.0
        else:
            return 3.0

    def predict_handover_time(
        self,
        current_elevation: float,
        satellite_velocity: float,
        angular_velocity: float
    ) -> Dict[str, float]:
        """
        Predict when handover will be needed

        Args:
            current_elevation: Current elevation angle (degrees)
            satellite_velocity: Satellite velocity (km/s)
            angular_velocity: Angular velocity as seen from UE (deg/s)

        Returns:
            Dictionary with time_to_handover_sec and handover_probability
        """
        if angular_velocity >= 0:
            # Satellite is rising, no immediate handover
            time_to_handover = 999999.0
            probability = 0.0
        else:
            # Satellite is setting, calculate time to minimum elevation
            elevation_delta = current_elevation - self.min_elevation_threshold
            time_to_handover = abs(elevation_delta / angular_velocity)

            # Calculate handover probability based on margin
            if time_to_handover < 10.0:
                probability = 0.99
            elif time_to_handover < 30.0:
                probability = 0.95
            elif time_to_handover < 60.0:
                probability = 0.80
            else:
                probability = 0.50

        return {
            "time_to_handover_sec": float(time_to_handover),
            "handover_probability": float(probability)
        }

    def recommend_power_control(
        self,
        link_budget: LinkBudget,
        current_power_dbm: float
    ) -> Dict[str, Any]:
        """
        Recommend transmit power adjustment

        Args:
            link_budget: Current link budget
            current_power_dbm: Current transmit power

        Returns:
            Power control recommendation
        """
        target_margin = 8.0  # Target 8 dB link margin
        margin_error = link_budget.link_margin_db - target_margin

        # Calculate power adjustment
        if margin_error > 5.0:
            # Too much margin, reduce power
            adjustment = min(-3.0, -margin_error / 2)
            reason = "LINK_MARGIN_EXCESSIVE"
        elif margin_error < -3.0:
            # Insufficient margin, increase power
            adjustment = min(3.0, abs(margin_error))
            reason = "LINK_MARGIN_LOW"
        else:
            # Margin is acceptable
            adjustment = 0.0
            reason = "LINK_MARGIN_OK"

        target_power = current_power_dbm + adjustment
        # Clamp to UE power limits
        target_power = max(0.0, min(23.0, target_power))

        return {
            "target_tx_power_dbm": target_power,
            "power_adjustment_db": target_power - current_power_dbm,
            "reason": reason,
            "current_margin_db": link_budget.link_margin_db,
            "target_margin_db": target_margin
        }

    def parse_control_message(self, control_msg_bytes: bytes) -> NTNControlMessage:
        """
        Parse RIC Control message for NTN actions

        Args:
            control_msg_bytes: Encoded control message

        Returns:
            Parsed NTN control message
        """
        return NTNControlMessage.from_bytes(control_msg_bytes)

    def create_control_message(
        self,
        action_type: NTNControlAction,
        ue_id: str,
        parameters: Dict[str, Any]
    ) -> bytes:
        """
        Create RIC Control message for NTN action

        Args:
            action_type: Type of control action
            ue_id: Target UE identifier
            parameters: Action-specific parameters

        Returns:
            Encoded control message
        """
        control_msg = NTNControlMessage(
            action_type=action_type.name,
            ue_id=ue_id,
            parameters=parameters
        )

        # Encode based on selected encoding
        if self.encoding == 'asn1' and self.asn1_codec is not None:
            # Use ASN.1 PER encoding
            control_dict = control_msg.to_dict()
            encoded_msg, _ = self.asn1_codec.encode_control_message(control_dict)
            return encoded_msg
        else:
            # Use JSON encoding (default fallback)
            return json.dumps(control_msg.to_dict()).encode('utf-8')

    def validate_indication_message(self, message_bytes: bytes) -> bool:
        """
        Validate NTN indication message format

        Args:
            message_bytes: Encoded indication message

        Returns:
            True if valid, False otherwise
        """
        try:
            data = json.loads(message_bytes.decode('utf-8'))

            # Check required fields
            required_fields = [
                "timestamp_ns", "ue_id", "satellite_metrics",
                "channel_quality", "ntn_impairments", "link_budget"
            ]

            for field in required_fields:
                if field not in data:
                    return False

            # Validate elevation angle range
            elevation = data["satellite_metrics"]["elevation_angle"]
            if not (0.0 <= elevation <= 90.0):
                return False

            # Validate azimuth range
            azimuth = data["satellite_metrics"]["azimuth_angle"]
            if not (0.0 <= azimuth <= 360.0):
                return False

            return True

        except (json.JSONDecodeError, KeyError, TypeError):
            return False

    def get_ran_function_definition(self) -> Dict[str, Any]:
        """Get RAN function definition for E2 Setup"""
        return self.RAN_FUNCTION_DEFINITION

    def get_encoding_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Get ASN.1 encoding/decoding statistics

        Returns:
            Statistics dictionary or None if not using ASN.1
        """
        if self.encoding == 'asn1' and self.asn1_codec is not None:
            return self.asn1_codec.get_statistics()
        return None

    def get_encoding_type(self) -> str:
        """Get current encoding type ('asn1' or 'json')"""
        return self.encoding
