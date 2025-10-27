#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VITA 49.2 to gRPC Bridge
Receives VITA Radio Transport (VRT) packets from USRP and forwards to O-RAN via gRPC

Implements:
- VITA 49.0/49.2 packet parsing
- Context packet handling (frequency, bandwidth, timestamps)
- Data packet buffering and aggregation
- gRPC streaming to O-RAN

Standards:
- ANSI/VITA 49.0-2015: Radio Transport (VRT)
- ANSI/VITA 49.2-2017: Spectrum Survey
- O-RAN.WG4.CUS: Control, User and Synchronization Plane

Author: thc1006@ieee.org
Version: 1.0.0
Date: 2025-10-27

🟡 PRODUCTION: Requires USRP configured with VRT output
"""

import socket
import struct
import numpy as np
import time
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
import grpc
from concurrent import futures

# 🟡 Import gRPC stubs (after protoc generation)
# import sdr_oran_pb2
# import sdr_oran_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class VRTHeader:
    """VITA 49.0 VRT packet header"""
    packet_type: int              # 0=IF Data, 1=IF Context, 4=Signal Data, 5=Signal Context
    class_id_present: bool
    trailer_present: bool
    timestamp_integer_present: bool
    timestamp_fractional_present: bool
    packet_count: int
    packet_size: int               # In 32-bit words
    stream_id: int


@dataclass
class VRTContextPacket:
    """VITA 49.0 IF Context Packet (Type 1)"""
    stream_id: int
    timestamp_sec: int             # Integer timestamp (seconds since epoch)
    timestamp_frac: int            # Fractional timestamp (picoseconds)

    # IF Context Fields (when present)
    center_frequency_hz: Optional[float] = None
    sample_rate_hz: Optional[float] = None
    bandwidth_hz: Optional[float] = None
    rf_reference_level_dbm: Optional[float] = None
    gain_db: Optional[float] = None


@dataclass
class VRTDataPacket:
    """VITA 49.0 IF Data Packet (Type 0)"""
    stream_id: int
    packet_count: int
    timestamp_sec: int
    timestamp_frac: int
    iq_samples: np.ndarray         # Complex64 array


class VITA49Receiver:
    """
    VITA 49.0/49.2 UDP receiver with gRPC forwarding

    Workflow:
    1. Receive VRT packets via UDP (from USRP)
    2. Parse VRT headers and payloads
    3. Maintain stream context (frequency, sample rate, etc.)
    4. Buffer data packets
    5. Forward aggregated IQ samples to O-RAN via gRPC
    """

    def __init__(self,
                 listen_ip: str = "0.0.0.0",
                 listen_port: int = 4991,
                 grpc_endpoint: str = "localhost:50051",
                 buffer_size: int = 8192):

        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.grpc_endpoint = grpc_endpoint
        self.buffer_size = buffer_size

        # UDP socket for VRT packets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16*1024*1024)  # 16 MB buffer
        self.sock.bind((self.listen_ip, self.listen_port))

        # Stream context (from IF Context packets)
        self.stream_context = {}

        # Data buffer for aggregation
        self.data_buffer = []

        # gRPC client
        # 🟡 Uncomment after protoc generation
        # channel = grpc.insecure_channel(grpc_endpoint)
        # self.grpc_stub = sdr_oran_pb2_grpc.IQStreamServiceStub(channel)

        logger.info(f"VITA 49 Receiver listening on {listen_ip}:{listen_port}")
        logger.info(f"gRPC endpoint: {grpc_endpoint}")

    def parse_vrt_header(self, data: bytes) -> Tuple[VRTHeader, int]:
        """
        Parse VITA 49.0 VRT packet header (first 4-16 bytes)

        Header Word 0 (32 bits):
        - Bits 31-28: Packet type (0=IF Data, 1=IF Context, ...)
        - Bit 27: Class ID present
        - Bit 26: Trailer present
        - Bits 25-24: Reserved
        - Bits 23-20: Timestamp mode
        - Bits 19-16: Packet count (sequence)
        - Bits 15-0: Packet size (in 32-bit words)
        """
        if len(data) < 4:
            raise ValueError("Packet too short for VRT header")

        word0 = struct.unpack('>I', data[0:4])[0]

        packet_type = (word0 >> 28) & 0x0F
        class_id_present = bool((word0 >> 27) & 0x01)
        trailer_present = bool((word0 >> 26) & 0x01)
        timestamp_mode = (word0 >> 20) & 0x0F
        packet_count = (word0 >> 16) & 0x0F
        packet_size = word0 & 0xFFFF

        # Parse timestamp flags
        timestamp_integer_present = bool(timestamp_mode & 0x04)
        timestamp_fractional_present = bool(timestamp_mode & 0x02)

        # Parse Stream ID (Word 1)
        stream_id = struct.unpack('>I', data[4:8])[0]

        header = VRTHeader(
            packet_type=packet_type,
            class_id_present=class_id_present,
            trailer_present=trailer_present,
            timestamp_integer_present=timestamp_integer_present,
            timestamp_fractional_present=timestamp_fractional_present,
            packet_count=packet_count,
            packet_size=packet_size,
            stream_id=stream_id
        )

        # Calculate header size
        header_size = 8  # Word 0 + Word 1 (Stream ID)

        if class_id_present:
            header_size += 8  # Class ID (2 words)

        if timestamp_integer_present:
            header_size += 4  # Integer timestamp

        if timestamp_fractional_present:
            header_size += 8  # Fractional timestamp

        return header, header_size

    def parse_context_packet(self, data: bytes, header: VRTHeader, header_size: int) -> VRTContextPacket:
        """Parse VITA 49.0 IF Context Packet (Type 1)"""

        offset = 8  # After Stream ID

        # Parse timestamps if present
        timestamp_sec = 0
        timestamp_frac = 0

        if header.timestamp_integer_present:
            timestamp_sec = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4

        if header.timestamp_fractional_present:
            timestamp_frac = struct.unpack('>Q', data[offset:offset+8])[0]
            offset += 8

        # Parse Context Indicator Field (CIF) - Word after timestamps
        cif = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4

        context = VRTContextPacket(
            stream_id=header.stream_id,
            timestamp_sec=timestamp_sec,
            timestamp_frac=timestamp_frac
        )

        # Parse context fields based on CIF bits
        if cif & (1 << 20):  # RF Reference Frequency
            rf_ref_int, rf_ref_frac = struct.unpack('>IQ', data[offset:offset+12])
            context.center_frequency_hz = rf_ref_int + (rf_ref_frac / (2**20))
            offset += 12

        if cif & (1 << 19):  # IF Reference Frequency (not needed for baseband)
            offset += 12

        if cif & (1 << 18):  # IF Band Offset (not needed)
            offset += 8

        if cif & (1 << 17):  # Reference Level
            level = struct.unpack('>h', data[offset:offset+2])[0]
            context.rf_reference_level_dbm = level / 128.0  # Fixed point: 7-bit fractional
            offset += 2

        if cif & (1 << 13):  # Gain/Attenuation
            gain1, gain2 = struct.unpack('>hh', data[offset:offset+4])
            context.gain_db = (gain1 / 128.0) + (gain2 / 128.0)  # Stage 1 + Stage 2
            offset += 4

        if cif & (1 << 7):  # Sample Rate
            sample_rate_int, sample_rate_frac = struct.unpack('>IQ', data[offset:offset+12])
            context.sample_rate_hz = sample_rate_int + (sample_rate_frac / (2**20))
            offset += 12

        if cif & (1 << 6):  # Bandwidth
            bw_int, bw_frac = struct.unpack('>IQ', data[offset:offset+12])
            context.bandwidth_hz = bw_int + (bw_frac / (2**20))
            offset += 12

        logger.info(f"Context packet: Fc={context.center_frequency_hz/1e9:.4f} GHz, "
                   f"SR={context.sample_rate_hz/1e6:.2f} MSPS, "
                   f"BW={context.bandwidth_hz/1e6:.2f} MHz")

        return context

    def parse_data_packet(self, data: bytes, header: VRTHeader, header_size: int) -> VRTDataPacket:
        """Parse VITA 49.0 IF Data Packet (Type 0)"""

        offset = 8  # After Stream ID

        # Parse timestamps
        timestamp_sec = 0
        timestamp_frac = 0

        if header.timestamp_integer_present:
            timestamp_sec = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4

        if header.timestamp_fractional_present:
            timestamp_frac = struct.unpack('>Q', data[offset:offset+8])[0]
            offset += 8

        # Payload starts after header
        payload_offset = header_size
        payload_size = (header.packet_size * 4) - header_size  # Size in bytes

        # Parse IQ samples (16-bit I, 16-bit Q, interleaved)
        num_samples = payload_size // 4  # Each sample is 4 bytes (I+Q)

        iq_data = np.frombuffer(data[payload_offset:payload_offset+payload_size], dtype=np.int16)

        # De-interleave I and Q
        i_samples = iq_data[0::2].astype(np.float32) / 32768.0  # Normalize to [-1, 1]
        q_samples = iq_data[1::2].astype(np.float32) / 32768.0

        iq_complex = i_samples + 1j * q_samples

        return VRTDataPacket(
            stream_id=header.stream_id,
            packet_count=header.packet_count,
            timestamp_sec=timestamp_sec,
            timestamp_frac=timestamp_frac,
            iq_samples=iq_complex
        )

    def forward_to_grpc(self, data_packets: list):
        """
        Aggregate buffered data packets and forward to O-RAN via gRPC
        """
        if not data_packets:
            return

        # Concatenate IQ samples
        all_samples = np.concatenate([pkt.iq_samples for pkt in data_packets])

        # Get stream context
        stream_id = data_packets[0].stream_id
        context = self.stream_context.get(stream_id)

        if not context:
            logger.warning(f"No context for stream {stream_id}, skipping")
            return

        # Convert to timestamp in nanoseconds
        timestamp_ns = (data_packets[0].timestamp_sec * 1_000_000_000) + \
                      (data_packets[0].timestamp_frac // 1000)  # Convert ps to ns

        # 🟡 Uncomment after protoc generation
        # batch = sdr_oran_pb2.IQSampleBatch(
        #     station_id="vita49-bridge",
        #     band="Ku-band",  # From context
        #     timestamp_ns=timestamp_ns,
        #     sequence_number=data_packets[0].packet_count,
        #     center_frequency_hz=context.center_frequency_hz,
        #     sample_rate=context.sample_rate_hz,
        #     samples=np.column_stack((all_samples.real, all_samples.imag)).flatten().tolist(),
        #     receive_power_dbm=context.rf_reference_level_dbm or -70,
        #     agc_locked=True
        # )

        # Send via gRPC
        # response = self.grpc_stub.StreamIQ(iter([batch]))

        logger.debug(f"Forwarded {len(all_samples)} samples to gRPC "
                    f"(Fc={context.center_frequency_hz/1e9:.4f} GHz)")

    def run(self):
        """Main receive loop"""
        logger.info("Starting VITA 49 receiver...")

        try:
            while True:
                # Receive VRT packet
                data, addr = self.sock.recvfrom(65536)

                # Parse header
                header, header_size = self.parse_vrt_header(data)

                # Handle different packet types
                if header.packet_type == 1:  # IF Context packet
                    context = self.parse_context_packet(data, header, header_size)
                    self.stream_context[header.stream_id] = context

                elif header.packet_type == 0:  # IF Data packet
                    data_pkt = self.parse_data_packet(data, header, header_size)
                    self.data_buffer.append(data_pkt)

                    # Forward when buffer reaches target size
                    if len(self.data_buffer) >= 100:  # 100 packets ~= 8192 samples
                        self.forward_to_grpc(self.data_buffer)
                        self.data_buffer = []

                else:
                    logger.warning(f"Unknown packet type: {header.packet_type}")

        except KeyboardInterrupt:
            logger.info("Stopping VITA 49 receiver...")
        finally:
            self.sock.close()


def main():
    """Example usage"""

    logger.info("="*60)
    logger.info("VITA 49.2 to gRPC Bridge")
    logger.info("="*60)

    receiver = VITA49Receiver(
        listen_ip="0.0.0.0",
        listen_port=4991,  # USRP default VRT port
        grpc_endpoint="localhost:50051"
    )

    receiver.run()


if __name__ == '__main__':
    main()


# =============================================================================
# USRP Configuration for VITA 49.2 Output:
# =============================================================================
"""
1. UHD Configuration (for USRP X310/N320):

   # Enable VRT in UHD
   uhd_usrp_probe --args="type=x310,addr=192.168.10.2"

   # In GNU Radio flowgraph, configure USRP Source:
   - Device Args: "type=x310,addr=192.168.10.2,send_buff_size=16e6,recv_buff_size=16e6"
   - Stream Args: "vita_enable=1,vita_port=4991"

2. Verify VRT packets:

   sudo tcpdump -i any -n udp port 4991 -X

   # Expected: VRT packets with 0x18... header (IF Data) and 0x58... (IF Context)

3. Performance Tuning:

   # Increase UDP buffer
   sudo sysctl -w net.core.rmem_max=536870912

   # Disable CPU frequency scaling
   sudo cpupower frequency-set -g performance

4. Alternative: Use gr-vita49 OOT module

   git clone https://github.com/ghostop14/gr-vita49.git
   cd gr-vita49 && mkdir build && cd build && cmake .. && make && sudo make install

Reference:
- ANSI/VITA 49.0-2015: https://www.vita.com/Standards/VITA-49.0
- ANSI/VITA 49.2-2017: https://www.vita.com/Standards/VITA-49.2
- UHD VITA 49: https://files.ettus.com/manual/page_usrp_x3x0.html#x3x0_usage_rtp_vrt
"""
