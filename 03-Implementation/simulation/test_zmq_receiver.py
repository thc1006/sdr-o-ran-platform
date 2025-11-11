#!/usr/bin/env python3
"""
ZMQ Receiver for LEO NTN Simulator
Tests and analyzes satellite IQ samples
"""

import zmq
import numpy as np
import json
import time
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime


class LEOReceiver:
    def __init__(self, zmq_address='tcp://localhost:5555'):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(zmq_address)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')

        self.frame_count = 0
        self.start_time = time.time()
        self.total_samples = 0
        self.doppler_history = []
        self.delay_history = []

    def receive_frame(self):
        """Receive one frame of IQ samples with metadata"""
        try:
            # Receive metadata (JSON)
            metadata_str = self.socket.recv_string(zmq.NOBLOCK)
            metadata = json.loads(metadata_str)

            # Receive IQ samples (binary)
            iq_bytes = self.socket.recv()
            iq_samples = np.frombuffer(iq_bytes, dtype=np.complex64)

            return metadata, iq_samples
        except zmq.Again:
            return None, None

    def analyze_signal(self, iq_samples):
        """Analyze IQ sample characteristics"""
        if len(iq_samples) == 0:
            return None

        analysis = {
            'power_avg': np.mean(np.abs(iq_samples)**2),
            'power_peak': np.max(np.abs(iq_samples)**2),
            'amplitude_mean': np.mean(np.abs(iq_samples)),
            'amplitude_std': np.std(np.abs(iq_samples)),
            'phase_mean': np.mean(np.angle(iq_samples)),
            'phase_std': np.std(np.angle(iq_samples)),
        }

        # Estimate SNR from signal statistics
        signal_power = analysis['power_avg']
        # Simple SNR estimate (assuming AWGN)
        analysis['estimated_snr_db'] = 10 * np.log10(signal_power / (1 - signal_power + 1e-10))

        return analysis

    def run(self, num_frames=100):
        """Run receiver and collect statistics"""
        print("[LEO NTN] Receiver Started")
        print("[INFO] Connecting to simulator...")
        time.sleep(1)  # Wait for connection
        print("[INFO] Connected! Receiving frames...\n")

        received_frames = []

        for _ in range(num_frames):
            metadata, iq_samples = self.receive_frame()

            if metadata is not None and iq_samples is not None:
                self.frame_count += 1
                self.total_samples += len(iq_samples)
                self.doppler_history.append(metadata['doppler_hz'])
                self.delay_history.append(metadata['delay_ms'])

                # Analyze signal
                analysis = self.analyze_signal(iq_samples)

                received_frames.append({
                    'metadata': metadata,
                    'analysis': analysis,
                    'iq_samples': iq_samples[:1000]  # Keep first 1000 samples for plotting
                })

                if self.frame_count % 10 == 0:
                    print(f"Frame {self.frame_count:4d} | "
                          f"Doppler: {metadata['doppler_hz']/1e3:+6.2f} kHz | "
                          f"Delay: {metadata['delay_ms']:5.2f} ms | "
                          f"SNR: {analysis['estimated_snr_db']:5.2f} dB | "
                          f"Power: {analysis['power_avg']:.4f}")
            else:
                time.sleep(0.001)  # Wait if no data

        # Print statistics
        self.print_statistics()

        # Generate plots
        self.generate_plots(received_frames)

        return received_frames

    def print_statistics(self):
        """Print reception statistics"""
        elapsed = time.time() - self.start_time
        sample_rate = self.total_samples / elapsed / 1e6  # MSPS
        data_rate = self.total_samples * 8 / elapsed / 1e6  # Mbps (complex64 = 8 bytes)

        print(f"\n{'='*60}")
        print(f"[STATS] Reception Statistics")
        print(f"{'='*60}")
        print(f"Frames received:     {self.frame_count}")
        print(f"Total samples:       {self.total_samples:,}")
        print(f"Reception time:      {elapsed:.2f} seconds")
        print(f"Sample rate:         {sample_rate:.2f} MSPS")
        print(f"Data rate:           {data_rate:.2f} Mbps")

        if self.doppler_history:
            print(f"\nDoppler shift:")
            print(f"  Range:             {min(self.doppler_history)/1e3:.2f} to {max(self.doppler_history)/1e3:.2f} kHz")
            print(f"  Mean:              {np.mean(self.doppler_history)/1e3:.2f} kHz")
            print(f"  Std dev:           {np.std(self.doppler_history)/1e3:.2f} kHz")

        if self.delay_history:
            print(f"\nPropagation delay:")
            print(f"  Range:             {min(self.delay_history):.2f} to {max(self.delay_history):.2f} ms")
            print(f"  Mean:              {np.mean(self.delay_history):.2f} ms")
            print(f"  Std dev:           {np.std(self.delay_history):.2f} ms")

        print(f"{'='*60}\n")

    def generate_plots(self, received_frames):
        """Generate analysis plots"""
        if not received_frames:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('LEO NTN Satellite Signal Analysis', fontsize=16, fontweight='bold')

        # Plot 1: IQ Constellation
        ax1 = axes[0, 0]
        sample_iq = received_frames[0]['iq_samples']
        ax1.scatter(sample_iq.real, sample_iq.imag, alpha=0.3, s=1)
        ax1.set_xlabel('In-phase (I)')
        ax1.set_ylabel('Quadrature (Q)')
        ax1.set_title('IQ Constellation Diagram')
        ax1.grid(True, alpha=0.3)
        ax1.axis('equal')

        # Plot 2: Doppler History
        ax2 = axes[0, 1]
        doppler_khz = [d/1e3 for d in self.doppler_history]
        ax2.plot(doppler_khz, linewidth=1.5)
        ax2.set_xlabel('Frame Number')
        ax2.set_ylabel('Doppler Shift (kHz)')
        ax2.set_title('Doppler Shift Over Time')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='r', linestyle='--', alpha=0.5)

        # Plot 3: Signal Power
        ax3 = axes[1, 0]
        powers = [f['analysis']['power_avg'] for f in received_frames]
        ax3.plot(powers, linewidth=1.5, color='green')
        ax3.set_xlabel('Frame Number')
        ax3.set_ylabel('Average Power')
        ax3.set_title('Signal Power Over Time')
        ax3.grid(True, alpha=0.3)

        # Plot 4: Delay Distribution
        ax4 = axes[1, 1]
        ax4.hist(self.delay_history, bins=20, color='orange', edgecolor='black', alpha=0.7)
        ax4.set_xlabel('Delay (ms)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Propagation Delay Distribution')
        ax4.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        # Save plot
        output_file = f'leo_ntn_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"[PLOT] Analysis plot saved to: {output_file}")

    def close(self):
        """Clean up resources"""
        self.socket.close()
        self.context.term()


def main():
    receiver = LEOReceiver(zmq_address='tcp://localhost:5555')

    try:
        # Receive and analyze 100 frames
        frames = receiver.run(num_frames=100)
        print(f"[SUCCESS] Received and analyzed {len(frames)} frames")

    except KeyboardInterrupt:
        print("\n[WARNING] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        receiver.close()
        print("[INFO] Receiver closed")


if __name__ == '__main__':
    main()
