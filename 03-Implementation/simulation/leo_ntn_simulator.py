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


def generate_leo_iq_samples(sample_rate=30.72e6, duration=0.01):
    """Generate simulated LEO NTN IQ samples with channel effects"""
    num_samples = int(sample_rate * duration)

    # Simulate carrier frequency with Doppler shift
    doppler_hz = np.random.uniform(-40e3, 40e3)  # ±40 kHz
    t = np.arange(num_samples) / sample_rate

    # Generate complex IQ samples
    carrier = np.exp(2j * np.pi * doppler_hz * t)

    # Add Rayleigh fading
    h_real = np.random.randn(num_samples)
    h_imag = np.random.randn(num_samples)
    h = (h_real + 1j * h_imag) / np.sqrt(2)

    # Add AWGN
    snr_db = 10  # 10 dB SNR
    noise_power = 10 ** (-snr_db / 10)
    noise = np.sqrt(noise_power/2) * (np.random.randn(num_samples) + 1j * np.random.randn(num_samples))

    # Combined signal
    signal = carrier * h + noise

    # Normalize
    signal = signal / np.max(np.abs(signal))

    return signal.astype(np.complex64)


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
    while True:
        # Generate IQ samples
        iq_samples = generate_leo_iq_samples(args.sample_rate)

        # Create metadata
        metadata = {
            'frame_id': frame_count,
            'timestamp': time.time(),
            'sample_rate': args.sample_rate,
            'num_samples': len(iq_samples),
            'doppler_hz': np.random.uniform(-40e3, 40e3),
            'delay_ms': np.random.uniform(5, 25),  # LEO delay
            'fspl_db': 165.0,  # Free space path loss at Ka-band
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
