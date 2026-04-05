#!/usr/bin/env python3
"""
LEO NTN Simulator with GPU Acceleration
Generates realistic satellite IQ samples with channel effects
"""

import zmq
import numpy as np
import time
import json
import argparse


def generate_leo_iq_samples(sample_rate=30.72e6, duration=0.01, elevation_deg=45.0,
                            pass_progress=0.5):
    """Generate simulated LEO NTN IQ samples with channel effects."""
    num_samples = int(sample_rate * duration)

    # Doppler shift from satellite geometry (3GPP TR 38.821)
    R_e = 6371.0  # Earth radius (km)
    h = 600.0     # LEO altitude (km)
    v_sat = 7.56  # Orbital velocity (km/s)
    f_carrier = 2e9
    c = 299792458.0

    el_rad = np.radians(elevation_deg)
    v_radial = v_sat * 1000 * R_e * np.cos(el_rad) / (R_e + h)  # m/s
    doppler_hz = v_radial / c * f_carrier
    # Sign: approaching in first half, receding in second half
    if pass_progress > 0.5:
        doppler_hz = -doppler_hz

    t = np.arange(num_samples) / sample_rate
    carrier = np.exp(2j * np.pi * doppler_hz * t)

    # Rician fading (LOS satellite channel, K-factor increases with elevation)
    k_factor_db = 5.0 + 10.0 * np.sin(el_rad)  # 5-15 dB per TR 38.811
    k_factor = 10 ** (k_factor_db / 10)
    los = np.sqrt(k_factor / (k_factor + 1))
    scatter = np.sqrt(1 / (2 * (k_factor + 1)))
    channel_coeff = los + scatter * (np.random.randn(num_samples) + 1j * np.random.randn(num_samples))

    # AWGN
    snr_db = 10
    noise_power = 10 ** (-snr_db / 10)
    noise = np.sqrt(noise_power / 2) * (np.random.randn(num_samples) + 1j * np.random.randn(num_samples))

    signal = carrier * channel_coeff + noise
    signal = signal / np.max(np.abs(signal))

    return signal.astype(np.complex64), doppler_hz


def main():
    parser = argparse.ArgumentParser(description='LEO NTN Simulator with GPU acceleration')
    parser.add_argument('--zmq-address', default='tcp://0.0.0.0:5555', help='ZMQ publish address')
    parser.add_argument('--sample-rate', type=float, default=30.72e6, help='Sample rate in Hz')
    args = parser.parse_args()

    # Check GPU availability
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f'✅ GPU available: {gpus}')
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        else:
            print('⚠️  No GPU detected, running on CPU')
    except Exception as e:
        print(f'⚠️  TensorFlow GPU check failed: {e}')

    # Setup ZMQ publisher
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(args.zmq_address)
    print(f'🛰️  LEO NTN Simulator started on {args.zmq_address}')
    print(f'📡 Sample rate: {args.sample_rate/1e6:.2f} MSPS')

    time.sleep(2)  # Allow subscribers to connect

    frame_count = 0
    pass_duration_frames = 600  # 600 frames at 100 Hz = 6 seconds simulated pass
    while True:
        # Simulate satellite pass trajectory
        pass_progress = (frame_count % pass_duration_frames) / pass_duration_frames
        # Elevation follows parabolic arc: peak at 50% of pass
        elevation_deg = max(5.0, 75.0 * (1 - 4 * (pass_progress - 0.5) ** 2))

        # Slant range (3GPP formula)
        R_e, h = 6371.0, 600.0
        el_rad = np.radians(elevation_deg)
        slant_range = np.sqrt((R_e + h) ** 2 - (R_e * np.cos(el_rad)) ** 2) - R_e * np.sin(el_rad)
        fspl_db = 92.45 + 20 * np.log10(2.0) + 20 * np.log10(slant_range)
        delay_ms = slant_range / 299792.458 * 1000

        # Generate IQ samples with consistent Doppler
        iq_samples, doppler_hz = generate_leo_iq_samples(
            args.sample_rate, elevation_deg=elevation_deg, pass_progress=pass_progress)

        # Create metadata (consistent with signal)
        metadata = {
            'frame_id': frame_count,
            'timestamp': time.time(),
            'sample_rate': args.sample_rate,
            'num_samples': len(iq_samples),
            'doppler_hz': float(doppler_hz),
            'delay_ms': float(delay_ms),
            'fspl_db': float(fspl_db),
        }

        # Send metadata as JSON
        socket.send_string(json.dumps(metadata), zmq.SNDMORE)

        # Send IQ samples as binary
        socket.send(iq_samples.tobytes())

        frame_count += 1
        if frame_count % 100 == 0:
            print(f'📊 Transmitted {frame_count} frames')

        time.sleep(0.01)  # 100 Hz frame rate


if __name__ == '__main__':
    main()
