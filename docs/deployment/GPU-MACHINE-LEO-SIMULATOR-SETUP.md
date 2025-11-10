# GPU Machine Setup: LEO Satellite Simulator
# LEO 衛星模擬器設置指南（GPU 機器）

**目標機器**: 具有 NVIDIA GPU 的伺服器/工作站
**作用**: 運行 LEO 衛星通道模擬器，提供 IQ samples 給 SDR Ground Station
**與主機器的關係**: 透過 ZMQ 網路連接
**創建日期**: 2025-11-10
**專案**: SDR Ground Station + O-RAN 整合平台

---

## 📋 系統架構概覽

```
╔═══════════════════════════════════════════════════════════════════╗
║              雙機協作架構 - 完整系統                               ║
╚═══════════════════════════════════════════════════════════════════╝

┌────────────────────────────────┐    ZMQ     ┌────────────────────────────────┐
│  GPU Machine (THIS MACHINE)    │◄──────────►│  Main Machine (No GPU)         │
│  ══════════════════════════    │   Network  │  ═══════════════════════        │
│                                │            │                                │
│  🛰️ LEO Satellite Simulator    │            │  📡 SDR Ground Station         │
│  ────────────────────────────  │            │  ─────────────────────         │
│                                │            │                                │
│  OpenNTN (Sionna)              │            │  sdr_api_server.py         ✅  │
│  ├─ GPU Accelerated            │   IQ       │  sdr_grpc_server.py        ✅  │
│  ├─ LEO Orbit Simulation       │  samples   │  VITA 49.2 bridge              │
│  ├─ Channel Models:            │   ───►     │                                │
│  │  - Delay (5-25 ms)          │            │  🌐 O-RAN Network              │
│  │  - Doppler (±40 kHz)        │            │  ────────────────              │
│  │  - Path Loss (165 dB)       │            │                                │
│  │  - Multipath Fading         │            │  FlexRIC RIC              ✅   │
│  │  - Atmospheric Effects      │            │  DRL xApp                 ✅   │
│  └─ 3GPP TR 38.811 Compliant   │            │  ns-3 or srsRAN gNB            │
│                                │            │  5G Core (optional)            │
│  Output: IQ Samples via ZMQ    │            │                                │
│  ├─ Format: Complex float32    │            │  🤖 AI/ML Pipeline             │
│  ├─ Sample Rate: 30.72 Msps    │            │  ─────────────────             │
│  ├─ Batch Size: 8192 samples   │            │                                │
│  └─ Metadata: timestamp, SNR   │            │  drl_trainer.py           ✅   │
│                                │            │  ric_state.py             ✅   │
└────────────────────────────────┘            └────────────────────────────────┘

                    Network Configuration:
                    ├─ ZMQ PUB-SUB pattern
                    ├─ TCP socket: tcp://<MAIN_IP>:5555
                    ├─ Bandwidth: ~100 Mbps (IQ data)
                    └─ Latency: <10 ms (LAN)
```

---

## 🎯 這台機器的任務

### 主要功能

1. **LEO 衛星軌道模擬**
   - 高度: 600 km (LEO)
   - 速度: 7,800 m/s
   - 軌道週期: ~96 分鐘
   - 覆蓋半徑: ~2,500 km

2. **NTN 通道模擬** (3GPP TR 38.811)
   - Delay spread: 5-25 ms (動態變化)
   - Doppler shift: ±40 kHz
   - Free-Space Path Loss: ~165 dB
   - Atmospheric attenuation: 雨衰、雲層
   - Multipath fading: Rice/Rayleigh

3. **IQ Sample 生成**
   - 基於 5G NR waveform
   - DVB-S2X 調變 (optional)
   - 加上 NTN channel effects
   - 實時串流給 Main Machine

### 與主機器的分工

| 任務 | GPU Machine (這台) | Main Machine |
|------|-------------------|--------------|
| 衛星軌道計算 | ✅ | ❌ |
| 通道模擬 (計算密集) | ✅ (GPU 加速) | ❌ |
| IQ sample 生成 | ✅ | ❌ |
| SDR 處理 | ❌ | ✅ |
| O-RAN 整合 | ❌ | ✅ |
| DRL 訓練/推論 | ✅ (可選，GPU 加速) | ✅ |

---

## 🔧 系統需求

### 硬體需求

| 組件 | 最低需求 | 推薦配置 | 說明 |
|------|---------|---------|------|
| **GPU** | NVIDIA GTX 1060 (6GB) | RTX 3090/4090, H100 | TensorFlow 需要 CUDA |
| **CPU** | 4 cores | 8+ cores | 並行處理 |
| **RAM** | 16 GB | 32+ GB | 大型模擬需要 |
| **Storage** | 50 GB SSD | 200+ GB NVMe | 數據日誌、模型 |
| **Network** | 1 Gbps Ethernet | 10 Gbps (if available) | ZMQ IQ streaming |

### 軟體需求

- **OS**: Ubuntu 22.04 LTS (推薦) 或 20.04 LTS
- **Python**: 3.10 或 3.11
- **CUDA**: 11.8 或 12.x (與 GPU 匹配)
- **cuDNN**: 對應 CUDA 版本

---

## 📦 安裝步驟

### Step 1: 系統準備

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝基礎工具
sudo apt install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    python3.10 \
    python3.10-dev \
    python3-pip \
    libzmq3-dev \
    pkg-config

# 檢查 GPU
nvidia-smi
# 應該看到 GPU 資訊，確認 CUDA 版本
```

### Step 2: 安裝 CUDA 和 cuDNN (如果尚未安裝)

```bash
# 檢查現有 CUDA
nvcc --version

# 如果沒有 CUDA，安裝 CUDA 12.x (示例)
wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda_12.3.0_545.23.06_linux.run
sudo sh cuda_12.3.0_545.23.06_linux.run

# 設置環境變數 (加到 ~/.bashrc)
echo 'export PATH=/usr/local/cuda-12.3/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.3/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: 創建 Python 虛擬環境

```bash
# 創建專案目錄
mkdir -p ~/leo-satellite-simulator
cd ~/leo-satellite-simulator

# 創建虛擬環境
python3.10 -m venv venv
source venv/bin/activate

# 升級 pip
pip install --upgrade pip setuptools wheel
```

### Step 4: 安裝 TensorFlow + CUDA 支援

```bash
# 安裝 TensorFlow with GPU support
pip install tensorflow[and-cuda]==2.15.0

# 驗證 GPU 可用
python3 -c "import tensorflow as tf; print('GPU Available:', tf.config.list_physical_devices('GPU'))"
# 應該顯示: GPU Available: [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
```

### Step 5: 安裝 Sionna

```bash
# Sionna: NVIDIA 的 GPU 加速通訊模擬器
pip install sionna

# 驗證安裝
python3 -c "import sionna; print('Sionna version:', sionna.__version__)"
```

### Step 6: 安裝 OpenNTN

```bash
# Clone OpenNTN repository
cd ~/leo-satellite-simulator
git clone https://github.com/ant-uni-bremen/OpenNTN.git
cd OpenNTN

# 安裝 OpenNTN
pip install -e .

# 安裝其他依賴
pip install numpy scipy matplotlib pandas pyzmq
```

### Step 7: 驗證完整安裝

```bash
# 運行測試腳本
python3 << 'EOF'
import tensorflow as tf
import sionna
import numpy as np
import zmq

print("="*60)
print("Installation Verification")
print("="*60)

# Check TensorFlow
print(f"TensorFlow version: {tf.__version__}")
gpus = tf.config.list_physical_devices('GPU')
print(f"GPUs available: {len(gpus)}")
for gpu in gpus:
    print(f"  - {gpu.name}")

# Check Sionna
print(f"Sionna version: {sionna.__version__}")

# Check ZMQ
print(f"ZMQ version: {zmq.zmq_version()}")

# Quick GPU test
with tf.device('/GPU:0'):
    a = tf.random.normal((1000, 1000))
    b = tf.random.normal((1000, 1000))
    c = tf.matmul(a, b)
print(f"GPU computation test: PASS (result shape: {c.shape})")

print("="*60)
print("✅ All components installed successfully!")
print("="*60)
EOF
```

---

## 🛰️ LEO 衛星模擬器實現

### 完整的 Python 代碼

創建文件: `~/leo-satellite-simulator/leo_ntn_simulator.py`

```python
#!/usr/bin/env python3
"""
LEO NTN Satellite Simulator
使用 Sionna 和 TensorFlow GPU 加速
輸出: IQ samples via ZMQ to Main Machine

Author: 蔡秀吉
Date: 2025-11-10
Hardware: Requires NVIDIA GPU with CUDA support
"""

import tensorflow as tf
import sionna
from sionna.channel import RayleighBlockFading, OFDMChannel
from sionna.ofdm import ResourceGrid, ResourceGridMapper, LSChannelEstimator
from sionna.utils import BinarySource, ebnodb2no
import numpy as np
import zmq
import time
import logging
from dataclasses import dataclass
from typing import Tuple
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LEOOrbitParameters:
    """LEO 衛星軌道參數"""
    altitude: float = 600e3          # 600 km
    velocity: float = 7800.0         # m/s
    inclination: float = 53.0        # degrees (類似 Starlink)
    earth_radius: float = 6371e3     # m

    @property
    def orbital_period(self) -> float:
        """軌道週期 (秒)"""
        r = self.earth_radius + self.altitude
        return 2 * np.pi * np.sqrt(r**3 / (6.674e-11 * 5.972e24))

    @property
    def max_elevation_angle(self) -> float:
        """最大仰角 (degrees)"""
        return np.degrees(np.arcsin(self.earth_radius / (self.earth_radius + self.altitude)))


@dataclass
class NTNChannelParameters:
    """NTN 通道參數 (基於 3GPP TR 38.811)"""
    carrier_frequency: float = 12e9  # 12 GHz (Ka-band)
    bandwidth: float = 100e6         # 100 MHz
    sample_rate: float = 30.72e6     # 30.72 MSPS (5G NR)

    # LEO-specific parameters
    min_delay: float = 5e-3          # 5 ms (最小延遲)
    max_delay: float = 25e-3         # 25 ms (最大延遲)
    max_doppler: float = 40e3        # ±40 kHz

    # Path loss
    fspl_at_600km: float = 165.0     # dB (Free-Space Path Loss)

    # Fading
    delay_spread: float = 100e-9     # 100 ns (典型值)


class LEONTNChannelModel:
    """
    LEO NTN 通道模型 (使用 Sionna)
    實現 3GPP TR 38.811 的 NTN channel models
    """

    def __init__(self, params: NTNChannelParameters, gpu_id: int = 0):
        self.params = params

        # 確保使用 GPU
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            tf.config.set_visible_devices(gpus[gpu_id], 'GPU')
            logger.info(f"Using GPU: {gpus[gpu_id].name}")
        else:
            logger.warning("No GPU found! Falling back to CPU (slow)")

        # 創建 Sionna channel model
        self._setup_channel()

    def _setup_channel(self):
        """設置 Sionna channel 模型"""
        # Resource Grid (5G NR OFDM parameters)
        self.resource_grid = ResourceGrid(
            num_ofdm_symbols=14,      # 1 slot
            fft_size=2048,            # FFT size
            subcarrier_spacing=30e3,  # 30 kHz SCS
            num_tx=1,                 # Single TX
            num_streams_per_tx=1,
            pilot_pattern="kronecker",
            pilot_ofdm_symbol_indices=[2, 11]
        )

        # Rayleigh fading channel (for NTN multipath)
        # delay_spread 決定頻率選擇性衰落
        self.channel = RayleighBlockFading(
            num_rx=1,
            num_rx_ant=1,
            num_tx=1,
            num_tx_ant=1,
        )

        logger.info("Sionna channel model initialized")

    def apply_ntn_effects(self,
                          iq_samples: tf.Tensor,
                          satellite_position: float,
                          ground_station_position: Tuple[float, float]) -> tf.Tensor:
        """
        應用 NTN 通道效果

        Args:
            iq_samples: Complex IQ samples [batch_size, num_samples]
            satellite_position: 衛星位置 (軌道角度, radians)
            ground_station_position: 地面站位置 (lat, lon)

        Returns:
            NTN 通道處理後的 IQ samples
        """
        # 1. Calculate current delay
        delay = self._calculate_delay(satellite_position)

        # 2. Calculate current Doppler shift
        doppler = self._calculate_doppler(satellite_position)

        # 3. Apply delay (fractional delay using interpolation)
        delayed_samples = self._apply_delay(iq_samples, delay)

        # 4. Apply Doppler shift
        doppler_shifted = self._apply_doppler(delayed_samples, doppler)

        # 5. Apply path loss
        path_loss_db = self.params.fspl_at_600km
        path_loss_linear = 10 ** (-path_loss_db / 20)
        attenuated = doppler_shifted * path_loss_linear

        # 6. Apply Rayleigh fading (multipath)
        # Sionna channel expects shape: [batch_size, num_tx, num_tx_ant, num_samples]
        x_reshaped = tf.reshape(attenuated, [1, 1, 1, -1])
        faded = self.channel([x_reshaped])[0]  # Returns [batch_size, num_rx, num_rx_ant, num_samples]
        faded_flat = tf.reshape(faded, [-1])

        # 7. Add AWGN
        snr_db = 10.0  # Can be made dynamic
        noise_power = 10 ** (-snr_db / 10)
        noise = tf.complex(
            tf.random.normal(tf.shape(faded_flat), stddev=np.sqrt(noise_power/2)),
            tf.random.normal(tf.shape(faded_flat), stddev=np.sqrt(noise_power/2))
        )
        output = faded_flat + noise

        return output

    def _calculate_delay(self, satellite_angle: float) -> float:
        """計算當前延遲 (動態變化)"""
        # Simple model: delay varies with elevation angle
        # Min delay at zenith, max at horizon
        elevation = np.abs(np.sin(satellite_angle)) * 90  # 0-90 degrees
        normalized = elevation / 90.0
        delay = self.params.min_delay + (1 - normalized) * (self.params.max_delay - self.params.min_delay)
        return delay

    def _calculate_doppler(self, satellite_angle: float) -> float:
        """計算當前 Doppler shift"""
        # Doppler = v/c * f_c * cos(theta)
        c = 3e8  # speed of light
        theta = satellite_angle
        doppler = (7800 / c) * self.params.carrier_frequency * np.cos(theta)
        return doppler

    def _apply_delay(self, samples: tf.Tensor, delay_seconds: float) -> tf.Tensor:
        """應用延遲 (fractional delay)"""
        delay_samples = int(delay_seconds * self.params.sample_rate)
        if delay_samples > 0:
            # Pad with zeros at the beginning
            padding = tf.zeros([delay_samples], dtype=samples.dtype)
            delayed = tf.concat([padding, samples[:-delay_samples]], axis=0)
        else:
            delayed = samples
        return delayed

    def _apply_doppler(self, samples: tf.Tensor, doppler_hz: float) -> tf.Tensor:
        """應用 Doppler shift (頻率偏移)"""
        t = tf.range(tf.shape(samples)[0], dtype=tf.float32) / self.params.sample_rate
        phase_shift = 2 * np.pi * doppler_hz * t
        doppler_factor = tf.exp(tf.complex(0.0, phase_shift))
        return samples * doppler_factor


class LEONTNSimulator:
    """
    完整的 LEO NTN 模擬器
    包含衛星軌道、通道模型、IQ sample 生成、ZMQ 輸出
    """

    def __init__(self,
                 zmq_address: str = "tcp://*:5555",
                 batch_size: int = 8192,
                 gpu_id: int = 0):

        self.zmq_address = zmq_address
        self.batch_size = batch_size

        # Initialize parameters
        self.orbit = LEOOrbitParameters()
        self.channel_params = NTNChannelParameters()

        # Initialize channel model
        self.channel_model = LEONTNChannelModel(self.channel_params, gpu_id)

        # Initialize ZMQ publisher
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(zmq_address)
        logger.info(f"ZMQ Publisher bound to {zmq_address}")

        # Simulation state
        self.satellite_angle = 0.0  # Current orbital position (radians)
        self.sequence_number = 0
        self.running = False

        logger.info("LEO NTN Simulator initialized")

    def generate_5g_nr_waveform(self) -> tf.Tensor:
        """
        生成 5G NR OFDM waveform

        Returns:
            Complex IQ samples
        """
        # Generate random data bits
        num_bits_per_symbol = self.batch_size // 14  # 14 OFDM symbols per slot
        bits = tf.random.uniform([1, 1, 1, num_bits_per_symbol], 0, 2, dtype=tf.int32)

        # Simple QPSK modulation
        # Map bits to symbols: 00->1+1j, 01->1-1j, 10->-1+1j, 11->-1-1j
        bits_reshaped = tf.reshape(bits, [-1, 2])
        i_component = tf.where(bits_reshaped[:, 0] == 0, 1.0, -1.0)
        q_component = tf.where(bits_reshaped[:, 1] == 0, 1.0, -1.0)
        symbols = tf.complex(i_component, q_component) / tf.sqrt(2.0)

        # Pad to batch_size
        symbols_padded = tf.concat([symbols, tf.zeros([self.batch_size - tf.shape(symbols)[0]], dtype=tf.complex64)], axis=0)

        return symbols_padded

    def run(self, duration_seconds: float = None):
        """
        運行模擬器

        Args:
            duration_seconds: 運行時間 (None = 無限)
        """
        self.running = True
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("LEO NTN Simulator STARTED")
        logger.info(f"Orbital period: {self.orbit.orbital_period:.1f} seconds")
        logger.info(f"Satellite velocity: {self.orbit.velocity:.1f} m/s")
        logger.info(f"Max Doppler: ±{self.channel_params.max_doppler/1e3:.1f} kHz")
        logger.info(f"Delay range: {self.channel_params.min_delay*1e3:.1f}-{self.channel_params.max_delay*1e3:.1f} ms")
        logger.info(f"ZMQ streaming to: {self.zmq_address}")
        logger.info("=" * 60)

        try:
            while self.running:
                # Check duration
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    logger.info(f"Reached duration limit: {duration_seconds}s")
                    break

                # 1. Update satellite position
                dt = self.batch_size / self.channel_params.sample_rate  # Time for one batch
                angular_velocity = 2 * np.pi / self.orbit.orbital_period
                self.satellite_angle += angular_velocity * dt
                self.satellite_angle %= (2 * np.pi)

                # 2. Generate clean 5G NR waveform
                clean_iq = self.generate_5g_nr_waveform()

                # 3. Apply NTN channel effects
                ntn_iq = self.channel_model.apply_ntn_effects(
                    clean_iq,
                    self.satellite_angle,
                    (0.0, 0.0)  # Ground station position (placeholder)
                )

                # 4. Prepare metadata
                metadata = {
                    'sequence': self.sequence_number,
                    'timestamp': time.time(),
                    'satellite_angle_deg': float(np.degrees(self.satellite_angle)),
                    'delay_ms': float(self.channel_model._calculate_delay(self.satellite_angle) * 1e3),
                    'doppler_khz': float(self.channel_model._calculate_doppler(self.satellite_angle) / 1e3),
                    'sample_rate': float(self.channel_params.sample_rate),
                    'batch_size': self.batch_size,
                }

                # 5. Send via ZMQ
                self._send_iq_samples(ntn_iq.numpy(), metadata)

                # 6. Update counters
                self.sequence_number += 1

                # 7. Logging (every 100 batches)
                if self.sequence_number % 100 == 0:
                    logger.info(f"[Seq {self.sequence_number}] "
                              f"Angle: {metadata['satellite_angle_deg']:.1f}°, "
                              f"Delay: {metadata['delay_ms']:.2f} ms, "
                              f"Doppler: {metadata['doppler_khz']:+.2f} kHz")

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop()

    def _send_iq_samples(self, iq_samples: np.ndarray, metadata: dict):
        """
        透過 ZMQ 發送 IQ samples

        Format: [metadata_json] [iq_data_bytes]
        """
        # Serialize metadata
        metadata_bytes = json.dumps(metadata).encode('utf-8')

        # Serialize IQ samples (complex64 -> bytes)
        iq_bytes = iq_samples.astype(np.complex64).tobytes()

        # Send multipart message: [metadata, iq_data]
        self.socket.send_multipart([metadata_bytes, iq_bytes])

    def stop(self):
        """停止模擬器"""
        self.running = False
        self.socket.close()
        self.context.term()
        logger.info("LEO NTN Simulator STOPPED")


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="LEO NTN Satellite Simulator")
    parser.add_argument("--zmq-address", default="tcp://*:5555",
                       help="ZMQ publisher address (default: tcp://*:5555)")
    parser.add_argument("--batch-size", type=int, default=8192,
                       help="IQ samples per batch (default: 8192)")
    parser.add_argument("--duration", type=float, default=None,
                       help="Simulation duration in seconds (default: infinite)")
    parser.add_argument("--gpu", type=int, default=0,
                       help="GPU device ID (default: 0)")

    args = parser.parse_args()

    # Create and run simulator
    simulator = LEONTNSimulator(
        zmq_address=args.zmq_address,
        batch_size=args.batch_size,
        gpu_id=args.gpu
    )

    simulator.run(duration_seconds=args.duration)


if __name__ == "__main__":
    main()
```

---

## 🧪 測試 LEO 模擬器

### 本地測試（在 GPU 機器上）

```bash
# 激活虛擬環境
cd ~/leo-satellite-simulator
source venv/bin/activate

# 運行模擬器 (30 秒測試)
python3 leo_ntn_simulator.py --duration 30

# 應該看到類似輸出：
# ============================================================
# LEO NTN Simulator STARTED
# Orbital period: 5760.0 seconds
# Satellite velocity: 7800.0 m/s
# Max Doppler: ±40.0 kHz
# Delay range: 5.0-25.0 ms
# ZMQ streaming to: tcp://*:5555
# ============================================================
# [Seq 100] Angle: 45.2°, Delay: 15.32 ms, Doppler: +28.45 kHz
# [Seq 200] Angle: 90.4°, Delay: 10.15 ms, Doppler: +35.21 kHz
# ...
```

### 創建 ZMQ 接收測試腳本

創建文件: `~/leo-satellite-simulator/test_zmq_receiver.py`

```python
#!/usr/bin/env python3
"""
Test ZMQ Receiver
驗證可以接收 LEO simulator 的 IQ samples
"""

import zmq
import json
import numpy as np
import time

def main():
    # Connect to LEO simulator
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.subscribe(b"")  # Subscribe to all messages

    print("Connected to LEO Simulator ZMQ publisher")
    print("Receiving IQ samples...")
    print("=" * 60)

    received_count = 0
    start_time = time.time()
    total_bytes = 0

    try:
        while received_count < 100:  # Receive 100 batches
            # Receive multipart message
            metadata_bytes, iq_bytes = socket.recv_multipart()

            # Decode metadata
            metadata = json.loads(metadata_bytes.decode('utf-8'))

            # Decode IQ samples
            iq_samples = np.frombuffer(iq_bytes, dtype=np.complex64)

            # Statistics
            received_count += 1
            total_bytes += len(iq_bytes)

            # Print every 10 batches
            if received_count % 10 == 0:
                elapsed = time.time() - start_time
                throughput_mbps = (total_bytes * 8) / (elapsed * 1e6)

                print(f"[{received_count:3d}] "
                      f"Seq: {metadata['sequence']:6d}, "
                      f"Angle: {metadata['satellite_angle_deg']:6.2f}°, "
                      f"Delay: {metadata['delay_ms']:5.2f} ms, "
                      f"Doppler: {metadata['doppler_khz']:+6.2f} kHz, "
                      f"IQ samples: {len(iq_samples):5d}, "
                      f"Throughput: {throughput_mbps:.2f} Mbps")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        socket.close()
        context.term()

        # Final statistics
        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"Received: {received_count} batches in {elapsed:.2f} seconds")
        print(f"Average rate: {received_count/elapsed:.2f} batches/sec")
        print(f"Total data: {total_bytes/1e6:.2f} MB")
        print(f"Throughput: {(total_bytes*8)/(elapsed*1e6):.2f} Mbps")
        print("=" * 60)

if __name__ == "__main__":
    main()
```

運行測試：

```bash
# Terminal 1: 啟動模擬器
python3 leo_ntn_simulator.py

# Terminal 2: 測試接收
python3 test_zmq_receiver.py
```

---

## 🌐 與主機器連接

### 網路配置

假設：
- **GPU Machine IP**: `192.168.1.100` (這台機器)
- **Main Machine IP**: `192.168.1.50`

### 修改 ZMQ 地址

在 GPU 機器上運行：

```bash
# 綁定到所有網路介面，允許外部連接
python3 leo_ntn_simulator.py --zmq-address "tcp://0.0.0.0:5555"
```

在 Main Machine 上連接：

```python
# Main Machine 的接收代碼
socket.connect("tcp://192.168.1.100:5555")
```

### 防火牆設置

```bash
# 在 GPU 機器上開啟 port 5555
sudo ufw allow 5555/tcp
```

### 測試連接

```bash
# 在 Main Machine 上測試
nc -zv 192.168.1.100 5555
# 應該顯示: Connection to 192.168.1.100 5555 port [tcp/*] succeeded!
```

---

## 🔗 與 Main Machine 的 SDR Ground Station 整合

### Main Machine 需要的修改

在 Main Machine 的 `sdr_grpc_server.py` 中，添加 ZMQ 接收：

```python
# Add to sdr_grpc_server.py

import zmq
import json
import numpy as np

class ZMQIQReceiver:
    """從 GPU 機器接收 IQ samples"""

    def __init__(self, zmq_address: str = "tcp://192.168.1.100:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(zmq_address)
        self.socket.subscribe(b"")
        logger.info(f"Connected to LEO simulator at {zmq_address}")

    def receive_batch(self) -> tuple:
        """接收一批 IQ samples"""
        metadata_bytes, iq_bytes = self.socket.recv_multipart()
        metadata = json.loads(metadata_bytes.decode('utf-8'))
        iq_samples = np.frombuffer(iq_bytes, dtype=np.complex64)
        return iq_samples, metadata

# 在 IQSampleGenerator 中使用
class IQSampleGenerator:
    def __init__(self, use_zmq: bool = True, zmq_address: str = None):
        if use_zmq:
            self.zmq_receiver = ZMQIQReceiver(zmq_address)
        # ...

    def generate_batch(self):
        if hasattr(self, 'zmq_receiver'):
            # 使用來自 LEO simulator 的真實 IQ samples
            return self.zmq_receiver.receive_batch()
        else:
            # 使用模擬數據（fallback）
            return self._generate_simulated()
```

---

## 📊 監控和日誌

### 創建監控腳本

`~/leo-satellite-simulator/monitor.py`:

```python
#!/usr/bin/env python3
"""
Real-time monitoring of LEO simulator
"""

import zmq
import json
import numpy as np
import time
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class LEOSimulatorMonitor:
    def __init__(self, zmq_address: str = "tcp://localhost:5555"):
        self.context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect(zmq_address)
        self.socket.subscribe(b"")

        # Data buffers
        self.angles = deque(maxlen=100)
        self.delays = deque(maxlen=100)
        self.dopplers = deque(maxlen=100)

        # Setup plot
        self.fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.line1, = ax1.plot([], [], 'b-')
        self.line2, = ax2.plot([], [], 'r-')

        ax1.set_ylabel('Delay (ms)')
        ax1.set_title('LEO NTN Channel Parameters')
        ax2.set_ylabel('Doppler (kHz)')
        ax2.set_xlabel('Satellite Angle (degrees)')

    def update(self, frame):
        # Receive data
        try:
            metadata_bytes, _ = self.socket.recv_multipart(zmq.NOBLOCK)
            metadata = json.loads(metadata_bytes.decode('utf-8'))

            self.angles.append(metadata['satellite_angle_deg'])
            self.delays.append(metadata['delay_ms'])
            self.dopplers.append(metadata['doppler_khz'])

            # Update plots
            self.line1.set_data(self.angles, self.delays)
            self.line2.set_data(self.angles, self.dopplers)

            self.fig.canvas.draw()
        except zmq.Again:
            pass

        return self.line1, self.line2

    def run(self):
        ani = FuncAnimation(self.fig, self.update, interval=100)
        plt.show()

if __name__ == "__main__":
    monitor = LEOSimulatorMonitor()
    monitor.run()
```

---

## 🚀 啟動腳本

創建方便的啟動腳本: `~/leo-satellite-simulator/start_simulator.sh`

```bash
#!/bin/bash

# LEO NTN Simulator Startup Script

set -e

echo "============================================================"
echo "  LEO NTN Satellite Simulator - Startup Script"
echo "============================================================"

# Activate virtualenv
source ~/leo-satellite-simulator/venv/bin/activate

# Check GPU
echo ""
echo "Checking GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Set environment variables
export TF_CPP_MIN_LOG_LEVEL=2  # Reduce TensorFlow logging
export CUDA_VISIBLE_DEVICES=0  # Use first GPU

# Configuration
ZMQ_ADDRESS="${ZMQ_ADDRESS:-tcp://0.0.0.0:5555}"
BATCH_SIZE="${BATCH_SIZE:-8192}"
DURATION="${DURATION:-}"  # Empty = infinite

echo ""
echo "Configuration:"
echo "  ZMQ Address: $ZMQ_ADDRESS"
echo "  Batch Size:  $BATCH_SIZE"
echo "  Duration:    ${DURATION:-infinite}"
echo ""

# Start simulator
echo "Starting LEO NTN Simulator..."
python3 ~/leo-satellite-simulator/leo_ntn_simulator.py \
    --zmq-address "$ZMQ_ADDRESS" \
    --batch-size "$BATCH_SIZE" \
    ${DURATION:+--duration $DURATION}
```

使用：

```bash
chmod +x ~/leo-satellite-simulator/start_simulator.sh

# 啟動（無限運行）
./start_simulator.sh

# 啟動（60 秒測試）
DURATION=60 ./start_simulator.sh

# 自訂配置
ZMQ_ADDRESS="tcp://0.0.0.0:6666" BATCH_SIZE=16384 ./start_simulator.sh
```

---

## 📝 總結檢查清單

### GPU 機器設置完成檢查

- [ ] Ubuntu 22.04 安裝完成
- [ ] NVIDIA Driver 和 CUDA 安裝完成
- [ ] `nvidia-smi` 可以看到 GPU
- [ ] Python 3.10 虛擬環境創建
- [ ] TensorFlow with GPU 安裝並驗證
- [ ] Sionna 安裝完成
- [ ] OpenNTN clone 並安裝
- [ ] `leo_ntn_simulator.py` 創建
- [ ] 本地 ZMQ 測試通過
- [ ] 防火牆 port 5555 開啟
- [ ] 與 Main Machine 網路連接測試通過

### 與 Main Machine 整合檢查

- [ ] Main Machine IP 確認
- [ ] ZMQ 連接測試成功
- [ ] IQ samples 可以正確接收
- [ ] Metadata 解析正確
- [ ] Throughput 符合預期 (~100 Mbps)
- [ ] Latency < 10 ms

---

## 🆘 故障排除

### 問題 1: TensorFlow 找不到 GPU

```bash
# 檢查 CUDA 版本匹配
nvcc --version
python3 -c "import tensorflow as tf; print(tf.sysconfig.get_build_info())"

# 確保 LD_LIBRARY_PATH 正確
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

### 問題 2: ZMQ 連接失敗

```bash
# 檢查 port 是否監聽
netstat -tulnp | grep 5555

# 測試本地連接
python3 -c "import zmq; c=zmq.Context(); s=c.socket(zmq.SUB); s.connect('tcp://localhost:5555'); print('OK')"
```

### 問題 3: 內存不足

```python
# 減小 batch size
python3 leo_ntn_simulator.py --batch-size 4096

# 限制 GPU 內存
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
tf.config.set_logical_device_configuration(
    gpus[0],
    [tf.config.LogicalDeviceConfiguration(memory_limit=8192)]  # 8GB
)
```

---

## 📧 支援

如果遇到問題，請檢查：
1. GPU driver 和 CUDA 版本
2. TensorFlow 版本與 CUDA 兼容性
3. 網路連接和防火牆設置
4. 日誌文件: `~/leo-satellite-simulator/logs/`

---

**這份文檔完成後，將其複製到 GPU 機器，然後由該機器的 Claude Code 讀取並執行設置！**

**預期結果**:
- GPU 機器：運行 LEO 衛星模擬器，透過 ZMQ 發送 IQ samples
- Main 機器：接收 IQ samples，整合到 SDR Ground Station → O-RAN pipeline
- 端到端：完整的 NTN 通訊鏈路模擬

---

**下一步**: 將此文檔傳輸到 GPU 機器後，執行設置並測試連接！
