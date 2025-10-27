#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GNU Radio Flowgraph: Multi-band DVB-S2 Satellite Receiver
Implements FR-SDR-002, FR-SDR-003, NFR-PERF-001

Features:
- Multi-band reception (C/Ku/Ka bands)
- Doppler compensation for LEO satellites
- DVB-S2 demodulation and FEC
- IQ sample streaming via gRPC to O-RAN
- Real-time spectrum monitoring

Author: thc1006@ieee.org
Version: 1.0.0
Date: 2025-10-27

🟡 SIMULATED: Requires USRP hardware (B210/X310/N320) for production deployment
"""

from gnuradio import gr, blocks, uhd, digital, fft, filter as gr_filter
from gnuradio.filter import firdes
import numpy as np
import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import grpc
from concurrent import futures

# Import gRPC generated stubs (to be generated from .proto)
# import sdr_oran_pb2
# import sdr_oran_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BandConfig:
    """Configuration for each frequency band"""
    name: str
    center_freq_hz: float
    bandwidth_hz: float
    sample_rate: float
    gain_db: float
    antenna: str = "RX2"


# Predefined band configurations based on deep-dive-technical-analysis.md
BAND_CONFIGS = {
    "C-band": BandConfig(
        name="C-band",
        center_freq_hz=4.0e9,  # 4 GHz downlink
        bandwidth_hz=500e6,     # 500 MHz
        sample_rate=10e6,       # 10 MSPS
        gain_db=60,
        antenna="RX2"
    ),
    "Ku-band": BandConfig(
        name="Ku-band",
        center_freq_hz=12.0e9,  # 12 GHz downlink
        bandwidth_hz=500e6,
        sample_rate=10e6,
        gain_db=55,
        antenna="RX2"
    ),
    "Ka-band": BandConfig(
        name="Ka-band",
        center_freq_hz=20.0e9,  # 20 GHz downlink
        bandwidth_hz=500e6,
        sample_rate=10e6,
        gain_db=50,
        antenna="RX2"
    )
}


class DopplerCompensator(gr.sync_block):
    """
    Real-time Doppler shift compensator for LEO satellites
    Based on TLE data and ground station location

    Implements frequency offset correction for high-velocity satellites
    Reference: deep-dive-technical-analysis.md Section 2.2
    """

    def __init__(self, sample_rate: float, initial_doppler_hz: float = 0.0):
        gr.sync_block.__init__(
            self,
            name="doppler_compensator",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )

        self.sample_rate = sample_rate
        self.doppler_hz = initial_doppler_hz
        self.phase_acc = 0.0

        logger.info(f"Doppler compensator initialized: SR={sample_rate/1e6:.2f} MSPS, "
                   f"Initial Doppler={initial_doppler_hz/1e3:.2f} kHz")

    def set_doppler(self, doppler_hz: float):
        """Update Doppler shift in Hz"""
        self.doppler_hz = doppler_hz
        logger.debug(f"Doppler updated: {doppler_hz/1e3:.2f} kHz")

    def work(self, input_items, output_items):
        """Apply phase rotation to compensate for Doppler shift"""
        in_samples = input_items[0]
        out_samples = output_items[0]

        # Calculate phase increment per sample
        phase_inc = -2.0 * np.pi * self.doppler_hz / self.sample_rate

        # Generate phase ramp
        n_samples = len(in_samples)
        phases = self.phase_acc + phase_inc * np.arange(n_samples)

        # Apply rotation
        out_samples[:] = in_samples * np.exp(1j * phases)

        # Update phase accumulator (wrap to [-π, π])
        self.phase_acc = (phases[-1] + phase_inc) % (2.0 * np.pi)

        return len(out_samples)


class MultibeamBeamformer(gr.sync_block):
    """
    Digital beamforming for multi-beam reception
    Implements 56-beam configuration from Lu et al. (2025)

    Reference: deep-dive-technical-analysis.md Section 2.1.2
    DOI: 10.1002/sat.70004
    """

    def __init__(self, n_elements: int = 108, n_beams: int = 56):
        gr.sync_block.__init__(
            self,
            name="multibeam_beamformer",
            in_sig=[np.complex64] * n_elements,
            out_sig=[np.complex64] * n_beams
        )

        self.n_elements = n_elements
        self.n_beams = n_beams

        # Initialize beamforming weights (Steering vectors)
        # 🟡 SIMULATED: Real implementation requires antenna array calibration
        self.weights = self._initialize_weights()

        logger.info(f"Beamformer initialized: {n_elements} elements → {n_beams} beams")

    def _initialize_weights(self) -> np.ndarray:
        """
        Generate beamforming weights for uniform linear array
        Returns: (n_beams, n_elements) complex weight matrix
        """
        # Beam angles from -60° to +60° (Lu et al. 2025 configuration)
        beam_angles = np.linspace(-60, 60, self.n_beams) * np.pi / 180

        # Element spacing (λ/2 for Ku-band @ 12 GHz)
        wavelength = 3e8 / 12e9  # c/f
        d = wavelength / 2

        # Steering vectors
        weights = np.zeros((self.n_beams, self.n_elements), dtype=np.complex64)
        for i, theta in enumerate(beam_angles):
            k = 2 * np.pi / wavelength
            for n in range(self.n_elements):
                # Phase shift for uniform linear array
                phase = k * n * d * np.sin(theta)
                weights[i, n] = np.exp(-1j * phase) / np.sqrt(self.n_elements)

        return weights

    def work(self, input_items, output_items):
        """Apply beamforming weights to antenna elements"""
        n_samples = len(input_items[0])

        # Stack input samples (n_elements, n_samples)
        x = np.array([input_items[i][:n_samples] for i in range(self.n_elements)])

        # Apply beamforming: y = W^H * x
        for beam_idx in range(self.n_beams):
            output_items[beam_idx][:n_samples] = np.dot(
                self.weights[beam_idx].conj(), x
            )

        return n_samples


class DVBS2Receiver(gr.top_block):
    """
    Complete DVB-S2 receiver flowgraph with multi-band support

    Signal chain:
    1. USRP Source (multi-band frontend)
    2. Doppler Compensator (LEO tracking)
    3. Multibeam Beamformer (optional)
    4. DVB-S2 Demodulator
    5. FEC Decoder (LDPC + BCH)
    6. gRPC IQ Streamer (to O-RAN DU)
    7. Spectrum Monitor

    Implements: FR-SDR-002, FR-SDR-003, NFR-PERF-001
    """

    def __init__(self,
                 band: str = "Ku-band",
                 usrp_args: str = "",
                 enable_beamforming: bool = False,
                 grpc_endpoint: str = "localhost:50051",
                 simulate: bool = True):

        gr.top_block.__init__(self, "DVB-S2 Multi-band Receiver")

        self.band = band
        self.config = BAND_CONFIGS.get(band)
        if not self.config:
            raise ValueError(f"Unknown band: {band}. Available: {list(BAND_CONFIGS.keys())}")

        self.simulate = simulate
        self.enable_beamforming = enable_beamforming
        self.grpc_endpoint = grpc_endpoint

        logger.info(f"Initializing {band} receiver (Simulated: {simulate})")

        # Build flowgraph
        self._build_flowgraph(usrp_args)

    def _build_flowgraph(self, usrp_args: str):
        """Construct GNU Radio flowgraph"""

        # =================================================================
        # 1. RF Frontend (USRP Source or File Source for simulation)
        # =================================================================
        if self.simulate:
            logger.warning("🟡 SIMULATION MODE: Using noise source instead of USRP")

            # Noise source for testing
            self.source = blocks.noise_source_c(
                blocks.GR_GAUSSIAN,
                amplitude=0.1,
                seed=0
            )

            # Throttle to prevent CPU overload
            self.throttle = blocks.throttle(
                gr.sizeof_gr_complex,
                self.config.sample_rate
            )
            self.connect(self.source, self.throttle)
            rf_output = self.throttle

        else:
            logger.info(f"Initializing USRP with args: {usrp_args}")

            # USRP Source
            self.usrp_source = uhd.usrp_source(
                ",".join(("", usrp_args)),
                uhd.stream_args(
                    cpu_format="fc32",
                    channels=list(range(1)),
                ),
            )

            # Configure USRP
            self.usrp_source.set_samp_rate(self.config.sample_rate)
            self.usrp_source.set_center_freq(self.config.center_freq_hz, 0)
            self.usrp_source.set_gain(self.config.gain_db, 0)
            self.usrp_source.set_antenna(self.config.antenna, 0)
            self.usrp_source.set_bandwidth(self.config.bandwidth_hz, 0)

            # AGC (Automatic Gain Control)
            self.agc = analog.agc_cc(1e-4, 1.0, 1.0)
            self.connect(self.usrp_source, self.agc)

            rf_output = self.agc

            logger.info(f"USRP configured: {self.config.center_freq_hz/1e9:.2f} GHz, "
                       f"{self.config.sample_rate/1e6:.2f} MSPS, {self.config.gain_db} dB")

        # =================================================================
        # 2. Doppler Compensation (for LEO satellites)
        # =================================================================
        self.doppler_comp = DopplerCompensator(
            sample_rate=self.config.sample_rate,
            initial_doppler_hz=0.0  # Will be updated via TLE tracking
        )
        self.connect(rf_output, self.doppler_comp)

        # =================================================================
        # 3. Multibeam Beamforming (optional)
        # =================================================================
        if self.enable_beamforming:
            # 🟡 SIMULATED: Requires multi-channel USRP (e.g., N320 with 2x2 MIMO)
            logger.warning("🟡 Beamforming enabled but using single-channel simulation")
            current_output = self.doppler_comp
        else:
            current_output = self.doppler_comp

        # =================================================================
        # 4. Channel Filter (Root Raised Cosine)
        # =================================================================
        # Symbol rate for DVB-S2 (example: 5 Msym/s)
        symbol_rate = 5e6
        sps = int(self.config.sample_rate / symbol_rate)  # Samples per symbol

        # RRC filter taps
        rrc_taps = firdes.root_raised_cosine(
            gain=1.0,
            sampling_freq=self.config.sample_rate,
            symbol_rate=symbol_rate,
            alpha=0.35,  # DVB-S2 roll-off
            ntaps=11 * sps
        )

        self.rrc_filter = gr_filter.fir_filter_ccf(1, rrc_taps)
        self.connect(current_output, self.rrc_filter)

        # =================================================================
        # 5. DVB-S2 Demodulator (QPSK/8PSK/16APSK/32APSK)
        # =================================================================
        # 🟡 SIMULATED: Full DVB-S2 demod requires gr-dvbs2 OOT module
        # For now, using simple QPSK constellation decoder

        # Costas loop for carrier recovery
        self.costas_loop = digital.costas_loop_cc(
            loop_bw=0.005,
            order=4,  # QPSK
            use_snr=False
        )
        self.connect(self.rrc_filter, self.costas_loop)

        # Symbol timing recovery (Mueller & Müller)
        self.clock_recovery = digital.symbol_sync_cc(
            digital.TED_MUELLER_AND_MULLER,
            sps,
            loop_bw=0.045,
            damping_factor=1.0,
            ted_gain=1.0,
            max_deviation=1.5,
            osps=1
        )
        self.connect(self.costas_loop, self.clock_recovery)

        # QPSK constellation decoder
        # Constellation points for QPSK
        qpsk_constellation = digital.constellation_qpsk().base()

        self.constellation_decoder = digital.constellation_decoder_cb(qpsk_constellation)
        self.connect(self.clock_recovery, self.constellation_decoder)

        # =================================================================
        # 6. FEC Decoder (DVB-S2 LDPC + BCH)
        # =================================================================
        # 🟡 SIMULATED: Real DVB-S2 requires gr-dvbs2rx or gr-dvbs2 module
        # Placeholder: Just unpack bits
        self.unpack = blocks.unpack_k_bits_bb(8)
        self.connect(self.constellation_decoder, self.unpack)

        # =================================================================
        # 7. Output: gRPC Streamer + File Sink
        # =================================================================
        # gRPC streamer (to be implemented)
        # 🟡 TODO: Implement gRPC vector sink for IQ streaming to O-RAN

        # File sink for offline analysis
        self.file_sink = blocks.file_sink(
            gr.sizeof_char,
            f"dvbs2_output_{self.band}_{int(time.time())}.bin",
            append=False
        )
        self.connect(self.unpack, self.file_sink)

        # =================================================================
        # 8. Spectrum Monitoring (FFT Sink)
        # =================================================================
        self.fft_sink = fft.fft_vcc(
            fft_size=2048,
            forward=True,
            window=fft.window.hann(2048),
            shift=True
        )
        self.connect(current_output, self.fft_sink)

        # Vector to stream for monitoring
        self.v2s = blocks.vector_to_stream(
            gr.sizeof_gr_complex,
            2048
        )
        self.connect(self.fft_sink, self.v2s)

        # Null sink (monitoring endpoint)
        self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)
        self.connect(self.v2s, self.null_sink)

        logger.info("Flowgraph construction complete")

    def update_doppler(self, doppler_hz: float):
        """Update Doppler compensation in real-time"""
        self.doppler_comp.set_doppler(doppler_hz)

    def get_spectrum(self) -> np.ndarray:
        """Get current spectrum snapshot"""
        # 🟡 TODO: Implement spectrum data extraction
        return np.zeros(2048, dtype=np.complex64)


def main():
    """Example usage"""

    # Configuration
    BAND = "Ku-band"
    SIMULATE = True  # Set to False for real USRP hardware
    USRP_ARGS = "type=b200"  # For USRP B210
    ENABLE_BEAMFORMING = False

    logger.info("="*60)
    logger.info("DVB-S2 Multi-band Receiver - GNU Radio Flowgraph")
    logger.info(f"Band: {BAND}")
    logger.info(f"Simulation Mode: {SIMULATE}")
    logger.info("="*60)

    # Create receiver
    receiver = DVBS2Receiver(
        band=BAND,
        usrp_args=USRP_ARGS,
        enable_beamforming=ENABLE_BEAMFORMING,
        simulate=SIMULATE
    )

    # Start flowgraph
    logger.info("Starting receiver...")
    receiver.start()

    try:
        # Simulate Doppler tracking for LEO satellite
        # Typical LEO Doppler: ±40 kHz @ 12 GHz
        logger.info("Simulating LEO Doppler tracking...")

        for t in range(60):  # Run for 60 seconds
            # Simulate Doppler shift (sinusoidal pattern)
            doppler_hz = 40e3 * np.sin(2 * np.pi * t / 600)  # 10-minute period
            receiver.update_doppler(doppler_hz)

            if t % 10 == 0:
                logger.info(f"t={t}s, Doppler={doppler_hz/1e3:.2f} kHz")

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping receiver...")

    finally:
        receiver.stop()
        receiver.wait()
        logger.info("Receiver stopped")


if __name__ == '__main__':
    main()


# =============================================================================
# Production Deployment Notes:
# =============================================================================
"""
1. Required GNU Radio OOT Modules:
   - gr-dvbs2rx: DVB-S2 receiver blocks
     Install: git clone https://github.com/drmpeg/gr-dvbs2rx.git

2. USRP Hardware Requirements:
   - USRP B210: Single-band (C/Ku with appropriate frontends)
   - USRP X310: Dual-band with UBX-160 or CBX-120 daughterboards
   - USRP N320: Multi-channel for beamforming (2x2 MIMO)

3. Antenna Requirements:
   - C-band: Parabolic dish (1.2m - 3.0m)
   - Ku-band: Parabolic dish (0.6m - 1.2m)
   - Ka-band: Parabolic dish (0.45m - 0.9m)

4. gRPC Integration:
   - Generate protobuf stubs: protoc --python_out=. sdr_oran.proto
   - Implement IQ streaming in real-time

5. Performance Optimization:
   - Use GPU acceleration (gr-clenabled) for beamforming
   - Enable SIMD instructions (VOLK)
   - Use SSD for high-speed I/Q recording

6. Monitoring Integration:
   - Export Prometheus metrics (receive power, SNR, BER)
   - Grafana dashboard for real-time visualization

Reference:
- FR-SDR-002: Multi-band signal acquisition
- FR-SDR-003: Real-time signal processing
- NFR-PERF-001: E2E latency <100ms
"""
