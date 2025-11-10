from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CompressionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[CompressionType]
    ZSTD: _ClassVar[CompressionType]
    LZ4: _ClassVar[CompressionType]
NONE: CompressionType
ZSTD: CompressionType
LZ4: CompressionType

class IQSampleBatch(_message.Message):
    __slots__ = ("station_id", "band", "timestamp_ns", "sequence_number", "center_frequency_hz", "sample_rate", "samples", "compressed_samples", "snr_db", "receive_power_dbm", "agc_locked", "doppler_shift_hz")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    BAND_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    CENTER_FREQUENCY_HZ_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    SAMPLES_FIELD_NUMBER: _ClassVar[int]
    COMPRESSED_SAMPLES_FIELD_NUMBER: _ClassVar[int]
    SNR_DB_FIELD_NUMBER: _ClassVar[int]
    RECEIVE_POWER_DBM_FIELD_NUMBER: _ClassVar[int]
    AGC_LOCKED_FIELD_NUMBER: _ClassVar[int]
    DOPPLER_SHIFT_HZ_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    band: str
    timestamp_ns: int
    sequence_number: int
    center_frequency_hz: float
    sample_rate: float
    samples: _containers.RepeatedScalarFieldContainer[float]
    compressed_samples: bytes
    snr_db: float
    receive_power_dbm: float
    agc_locked: bool
    doppler_shift_hz: float
    def __init__(self, station_id: _Optional[str] = ..., band: _Optional[str] = ..., timestamp_ns: _Optional[int] = ..., sequence_number: _Optional[int] = ..., center_frequency_hz: _Optional[float] = ..., sample_rate: _Optional[float] = ..., samples: _Optional[_Iterable[float]] = ..., compressed_samples: _Optional[bytes] = ..., snr_db: _Optional[float] = ..., receive_power_dbm: _Optional[float] = ..., agc_locked: bool = ..., doppler_shift_hz: _Optional[float] = ...) -> None: ...

class IQAck(_message.Message):
    __slots__ = ("acked_sequence", "packets_received", "packets_lost", "processing_latency_ms")
    ACKED_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    PACKETS_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    PACKETS_LOST_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    acked_sequence: int
    packets_received: int
    packets_lost: int
    processing_latency_ms: float
    def __init__(self, acked_sequence: _Optional[int] = ..., packets_received: _Optional[int] = ..., packets_lost: _Optional[int] = ..., processing_latency_ms: _Optional[float] = ...) -> None: ...

class StreamConfig(_message.Message):
    __slots__ = ("station_id", "band", "center_frequency_hz", "sample_rate", "batch_size_samples", "enable_compression", "compression")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    BAND_FIELD_NUMBER: _ClassVar[int]
    CENTER_FREQUENCY_HZ_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_FIELD_NUMBER: _ClassVar[int]
    BATCH_SIZE_SAMPLES_FIELD_NUMBER: _ClassVar[int]
    ENABLE_COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    band: str
    center_frequency_hz: float
    sample_rate: float
    batch_size_samples: int
    enable_compression: bool
    compression: CompressionType
    def __init__(self, station_id: _Optional[str] = ..., band: _Optional[str] = ..., center_frequency_hz: _Optional[float] = ..., sample_rate: _Optional[float] = ..., batch_size_samples: _Optional[int] = ..., enable_compression: bool = ..., compression: _Optional[_Union[CompressionType, str]] = ...) -> None: ...

class StreamStopRequest(_message.Message):
    __slots__ = ("station_id",)
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    def __init__(self, station_id: _Optional[str] = ...) -> None: ...

class StreamResponse(_message.Message):
    __slots__ = ("success", "message", "start_time_ns")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    start_time_ns: int
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., start_time_ns: _Optional[int] = ...) -> None: ...

class DopplerUpdate(_message.Message):
    __slots__ = ("station_id", "doppler_shift_hz", "doppler_rate_hz_s", "timestamp_ns")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    DOPPLER_SHIFT_HZ_FIELD_NUMBER: _ClassVar[int]
    DOPPLER_RATE_HZ_S_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    doppler_shift_hz: float
    doppler_rate_hz_s: float
    timestamp_ns: int
    def __init__(self, station_id: _Optional[str] = ..., doppler_shift_hz: _Optional[float] = ..., doppler_rate_hz_s: _Optional[float] = ..., timestamp_ns: _Optional[int] = ...) -> None: ...

class StreamStatsRequest(_message.Message):
    __slots__ = ("station_id",)
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    def __init__(self, station_id: _Optional[str] = ...) -> None: ...

class StreamStatsResponse(_message.Message):
    __slots__ = ("station_id", "total_samples_sent", "total_bytes_sent", "average_throughput_mbps", "average_latency_ms", "packets_sent", "packets_acked", "packets_lost", "packet_loss_rate", "uptime_seconds")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_SAMPLES_SENT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BYTES_SENT_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_THROUGHPUT_MBPS_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    PACKETS_SENT_FIELD_NUMBER: _ClassVar[int]
    PACKETS_ACKED_FIELD_NUMBER: _ClassVar[int]
    PACKETS_LOST_FIELD_NUMBER: _ClassVar[int]
    PACKET_LOSS_RATE_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    total_samples_sent: int
    total_bytes_sent: int
    average_throughput_mbps: float
    average_latency_ms: float
    packets_sent: int
    packets_acked: int
    packets_lost: int
    packet_loss_rate: float
    uptime_seconds: int
    def __init__(self, station_id: _Optional[str] = ..., total_samples_sent: _Optional[int] = ..., total_bytes_sent: _Optional[int] = ..., average_throughput_mbps: _Optional[float] = ..., average_latency_ms: _Optional[float] = ..., packets_sent: _Optional[int] = ..., packets_acked: _Optional[int] = ..., packets_lost: _Optional[int] = ..., packet_loss_rate: _Optional[float] = ..., uptime_seconds: _Optional[int] = ...) -> None: ...

class SpectrumRequest(_message.Message):
    __slots__ = ("station_id", "center_frequency_hz", "span_hz", "fft_size", "averaging")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    CENTER_FREQUENCY_HZ_FIELD_NUMBER: _ClassVar[int]
    SPAN_HZ_FIELD_NUMBER: _ClassVar[int]
    FFT_SIZE_FIELD_NUMBER: _ClassVar[int]
    AVERAGING_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    center_frequency_hz: float
    span_hz: float
    fft_size: int
    averaging: int
    def __init__(self, station_id: _Optional[str] = ..., center_frequency_hz: _Optional[float] = ..., span_hz: _Optional[float] = ..., fft_size: _Optional[int] = ..., averaging: _Optional[int] = ...) -> None: ...

class SpectrumData(_message.Message):
    __slots__ = ("station_id", "timestamp_ns", "center_frequency_hz", "span_hz", "fft_size", "magnitude_dbm", "frequencies_hz", "peak_frequency_hz", "peak_power_dbm")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    CENTER_FREQUENCY_HZ_FIELD_NUMBER: _ClassVar[int]
    SPAN_HZ_FIELD_NUMBER: _ClassVar[int]
    FFT_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAGNITUDE_DBM_FIELD_NUMBER: _ClassVar[int]
    FREQUENCIES_HZ_FIELD_NUMBER: _ClassVar[int]
    PEAK_FREQUENCY_HZ_FIELD_NUMBER: _ClassVar[int]
    PEAK_POWER_DBM_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    timestamp_ns: int
    center_frequency_hz: float
    span_hz: float
    fft_size: int
    magnitude_dbm: _containers.RepeatedScalarFieldContainer[float]
    frequencies_hz: _containers.RepeatedScalarFieldContainer[float]
    peak_frequency_hz: float
    peak_power_dbm: float
    def __init__(self, station_id: _Optional[str] = ..., timestamp_ns: _Optional[int] = ..., center_frequency_hz: _Optional[float] = ..., span_hz: _Optional[float] = ..., fft_size: _Optional[int] = ..., magnitude_dbm: _Optional[_Iterable[float]] = ..., frequencies_hz: _Optional[_Iterable[float]] = ..., peak_frequency_hz: _Optional[float] = ..., peak_power_dbm: _Optional[float] = ...) -> None: ...

class AntennaPointingRequest(_message.Message):
    __slots__ = ("station_id", "azimuth_deg", "elevation_deg", "polarization_deg")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    AZIMUTH_DEG_FIELD_NUMBER: _ClassVar[int]
    ELEVATION_DEG_FIELD_NUMBER: _ClassVar[int]
    POLARIZATION_DEG_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    azimuth_deg: float
    elevation_deg: float
    polarization_deg: float
    def __init__(self, station_id: _Optional[str] = ..., azimuth_deg: _Optional[float] = ..., elevation_deg: _Optional[float] = ..., polarization_deg: _Optional[float] = ...) -> None: ...

class AntennaPointingResponse(_message.Message):
    __slots__ = ("success", "message", "actual_azimuth_deg", "actual_elevation_deg", "pointing_error_deg")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_AZIMUTH_DEG_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_ELEVATION_DEG_FIELD_NUMBER: _ClassVar[int]
    POINTING_ERROR_DEG_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    actual_azimuth_deg: float
    actual_elevation_deg: float
    pointing_error_deg: float
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., actual_azimuth_deg: _Optional[float] = ..., actual_elevation_deg: _Optional[float] = ..., pointing_error_deg: _Optional[float] = ...) -> None: ...

class AntennaStatusRequest(_message.Message):
    __slots__ = ("station_id",)
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    def __init__(self, station_id: _Optional[str] = ...) -> None: ...

class AntennaStatus(_message.Message):
    __slots__ = ("station_id", "timestamp_ns", "current_azimuth_deg", "current_elevation_deg", "current_polarization_deg", "is_tracking", "target_satellite", "tracking_error_deg", "azimuth_motor_ok", "elevation_motor_ok", "azimuth_motor_current_a", "elevation_motor_current_a", "wind_speed_ms", "temperature_c")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_AZIMUTH_DEG_FIELD_NUMBER: _ClassVar[int]
    CURRENT_ELEVATION_DEG_FIELD_NUMBER: _ClassVar[int]
    CURRENT_POLARIZATION_DEG_FIELD_NUMBER: _ClassVar[int]
    IS_TRACKING_FIELD_NUMBER: _ClassVar[int]
    TARGET_SATELLITE_FIELD_NUMBER: _ClassVar[int]
    TRACKING_ERROR_DEG_FIELD_NUMBER: _ClassVar[int]
    AZIMUTH_MOTOR_OK_FIELD_NUMBER: _ClassVar[int]
    ELEVATION_MOTOR_OK_FIELD_NUMBER: _ClassVar[int]
    AZIMUTH_MOTOR_CURRENT_A_FIELD_NUMBER: _ClassVar[int]
    ELEVATION_MOTOR_CURRENT_A_FIELD_NUMBER: _ClassVar[int]
    WIND_SPEED_MS_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_C_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    timestamp_ns: int
    current_azimuth_deg: float
    current_elevation_deg: float
    current_polarization_deg: float
    is_tracking: bool
    target_satellite: str
    tracking_error_deg: float
    azimuth_motor_ok: bool
    elevation_motor_ok: bool
    azimuth_motor_current_a: float
    elevation_motor_current_a: float
    wind_speed_ms: float
    temperature_c: float
    def __init__(self, station_id: _Optional[str] = ..., timestamp_ns: _Optional[int] = ..., current_azimuth_deg: _Optional[float] = ..., current_elevation_deg: _Optional[float] = ..., current_polarization_deg: _Optional[float] = ..., is_tracking: bool = ..., target_satellite: _Optional[str] = ..., tracking_error_deg: _Optional[float] = ..., azimuth_motor_ok: bool = ..., elevation_motor_ok: bool = ..., azimuth_motor_current_a: _Optional[float] = ..., elevation_motor_current_a: _Optional[float] = ..., wind_speed_ms: _Optional[float] = ..., temperature_c: _Optional[float] = ...) -> None: ...

class TrackingUpdate(_message.Message):
    __slots__ = ("station_id", "timestamp_ns", "satellite_name", "tle_line1", "tle_line2", "predicted_azimuth_deg", "predicted_elevation_deg", "predicted_range_km", "predicted_doppler_hz")
    STATION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    SATELLITE_NAME_FIELD_NUMBER: _ClassVar[int]
    TLE_LINE1_FIELD_NUMBER: _ClassVar[int]
    TLE_LINE2_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_AZIMUTH_DEG_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_ELEVATION_DEG_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_RANGE_KM_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_DOPPLER_HZ_FIELD_NUMBER: _ClassVar[int]
    station_id: str
    timestamp_ns: int
    satellite_name: str
    tle_line1: str
    tle_line2: str
    predicted_azimuth_deg: float
    predicted_elevation_deg: float
    predicted_range_km: float
    predicted_doppler_hz: float
    def __init__(self, station_id: _Optional[str] = ..., timestamp_ns: _Optional[int] = ..., satellite_name: _Optional[str] = ..., tle_line1: _Optional[str] = ..., tle_line2: _Optional[str] = ..., predicted_azimuth_deg: _Optional[float] = ..., predicted_elevation_deg: _Optional[float] = ..., predicted_range_km: _Optional[float] = ..., predicted_doppler_hz: _Optional[float] = ...) -> None: ...
