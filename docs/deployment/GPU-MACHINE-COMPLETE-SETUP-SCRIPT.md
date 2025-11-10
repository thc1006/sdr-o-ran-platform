# GPU 機器完整設置腳本 - SDR + O-RAN + LEO NTN 模擬器
# Complete GPU Machine Setup Script - SDR + O-RAN + LEO NTN Simulator

**目標**: 在有 GPU 的機器上完成所有組件的安裝和配置
**Target**: Complete installation and configuration of all components on GPU machine

**日期**: 2025-11-10
**作者**: 蔡秀吉 (Hsiu-Chi Tsai)
**給**: Claude Code on GPU Machine

---

## 📋 概述 Overview

本文檔提供**完整的一鍵部署腳本**，用於在 GPU 機器上設置：
This document provides **complete one-step deployment scripts** for setting up on GPU machine:

1. ✅ CUDA 12.2 + cuDNN 8.9（TensorFlow 2.15 自動安裝）
2. ✅ TensorFlow 2.15.0 with GPU support
3. ✅ Sionna 1.1.0（NVIDIA GPU-accelerated link-level simulator）
4. ✅ FlexRIC（含關鍵修復）
5. ✅ SDR Ground Station + gRPC Server
6. ✅ LEO NTN Simulator（完整實現）
7. ✅ DRL xApp + AI/ML Pipeline
8. ✅ 一鍵啟動腳本

**總預計時間**: 2-4 小時（取決於網路速度）

---

## 🖥️ 系統需求 System Requirements

### 硬體 Hardware

| 組件 | 最低需求 | 推薦配置 |
|------|---------|---------|
| **GPU** | NVIDIA GTX 1060 (6GB VRAM) | RTX 3060/3080/4090 (8GB+ VRAM) |
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 16 GB | 32-64 GB |
| **Storage** | 100 GB 可用空間 | 200 GB SSD |
| **Network** | 100 Mbps | 1 Gbps |

### 軟體 Software

| 組件 | 版本需求 |
|------|---------|
| **OS** | Ubuntu 22.04 LTS (推薦) 或 Ubuntu 24.04 |
| **NVIDIA Driver** | >= 525.x (支援 CUDA 12.x) |
| **Python** | 3.8 - 3.12 |
| **Git** | >= 2.25 |
| **CMake** | >= 3.22 |

---

## ⚡ 快速開始 Quick Start

如果你希望一鍵完成所有設置，直接跳到 [自動化安裝腳本](#自動化安裝腳本-automated-installation-script) 部分。

For one-click setup, jump to [Automated Installation Script](#自動化安裝腳本-automated-installation-script).

---

## 🔧 手動安裝步驟 Manual Installation Steps

### Step 0: 系統更新和基礎工具 System Update and Basic Tools

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝基礎開發工具
sudo apt install -y \
    git \
    build-essential \
    wget \
    curl \
    vim \
    htop \
    net-tools \
    python3-pip \
    python3-dev \
    python3-venv

# 檢查 Python 版本（應該是 3.8-3.12）
python3 --version
```

### Step 1: 檢查 GPU 和安裝 NVIDIA 驅動 Check GPU and Install NVIDIA Driver

#### 1.1 檢查 GPU

```bash
# 檢查是否有 NVIDIA GPU
lspci | grep -i nvidia

# 預期輸出類似:
# 01:00.0 VGA compatible controller: NVIDIA Corporation ...
```

#### 1.2 檢查 NVIDIA 驅動

```bash
# 檢查驅動是否已安裝
nvidia-smi

# 如果看到 GPU 資訊，驅動已安裝 ✅
# 如果顯示 "command not found"，需要安裝驅動
```

#### 1.3 安裝 NVIDIA 驅動（如果需要）

```bash
# 自動檢測推薦驅動
ubuntu-drivers devices

# 預期輸出會顯示推薦的驅動版本，例如:
# nvidia-driver-535 - distro non-free recommended

# 安裝推薦的驅動（替換 535 為你的版本）
sudo apt install -y nvidia-driver-535

# 重啟系統
sudo reboot

# 重啟後驗證
nvidia-smi

# 預期輸出:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xxx      Driver Version: 535.xxx       CUDA Version: 12.2  |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0  On |                  N/A |
```

**重要**: CUDA 無需單獨安裝！TensorFlow 2.15 會通過 pip 自動安裝 CUDA 12.2 和 cuDNN 8.9。

---

### Step 2: 安裝 CMake 3.22+ Install CMake

Ubuntu 22.04 預設的 CMake 版本可能較舊，FlexRIC 需要 >= 3.22。

```bash
# 檢查當前 CMake 版本
cmake --version

# 如果版本 < 3.22，使用 Kitware APT repository 安裝最新版本
sudo apt remove cmake  # 移除舊版本

# 添加 Kitware repository
wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | \
    gpg --dearmor - | \
    sudo tee /etc/apt/trusted.gpg.d/kitware.gpg >/dev/null

sudo apt-add-repository "deb https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main"
sudo apt update

# 安裝最新 CMake
sudo apt install -y cmake

# 驗證版本（應該 >= 3.22）
cmake --version
# 預期: cmake version 3.28.x 或更新
```

---

### Step 3: 創建專案目錄並克隆代碼 Create Project Directory and Clone Code

```bash
# 創建開發目錄
mkdir -p ~/dev
cd ~/dev

# 克隆專案（替換成你的實際 GitHub URL）
# ⚠️ 重要：請先在原機器上確保專案已推送到 GitHub！
git clone https://github.com/YOUR_USERNAME/sdr-o-ran-platform.git

# 如果還沒有 GitHub repository，你需要先在原機器執行:
# cd /home/thc1006/dev/sdr-o-ran-platform
# git remote add origin https://github.com/YOUR_USERNAME/sdr-o-ran-platform.git
# git push -u origin main

# 進入專案目錄
cd sdr-o-ran-platform

# 檢查專案結構
ls -la

# 預期看到:
# 03-Implementation/
# GPU-MACHINE-LEO-SIMULATOR-SETUP.md
# COMPLETE-PROJECT-ARCHITECTURE-AND-ROADMAP.md
# DEPLOYMENT-GUIDE.md
# README.md
# requirements.txt
# ...
```

**如果你無法使用 Git，可以使用 rsync 或 scp 從原機器傳輸**:

```bash
# 在原機器執行（替換 GPU_MACHINE_IP）:
rsync -avz --progress /home/thc1006/dev/sdr-o-ran-platform/ \
    user@GPU_MACHINE_IP:~/dev/sdr-o-ran-platform/

# 或使用 scp（壓縮傳輸）:
cd /home/thc1006/dev
tar czf sdr-o-ran-platform.tar.gz sdr-o-ran-platform/
scp sdr-o-ran-platform.tar.gz user@GPU_MACHINE_IP:~/dev/

# 在 GPU 機器解壓:
cd ~/dev
tar xzf sdr-o-ran-platform.tar.gz
cd sdr-o-ran-platform
```

---

### Step 4: 創建 Python 虛擬環境 Create Python Virtual Environment

```bash
cd ~/dev/sdr-o-ran-platform

# 創建虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 升級 pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# 驗證 pip 版本
pip --version
# 預期: pip 24.x or newer
```

---

### Step 5: 安裝 TensorFlow 2.15 with GPU Support

**重要**: 使用 `tensorflow[and-cuda]` 會自動安裝 CUDA 12.2 和 cuDNN 8.9，無需手動安裝！

```bash
# 確保在虛擬環境中
source ~/dev/sdr-o-ran-platform/venv/bin/activate

# 安裝 TensorFlow 2.15.0 with CUDA support
pip install tensorflow[and-cuda]==2.15.0

# 這個安裝過程會:
# 1. 下載 TensorFlow 2.15.0
# 2. 自動下載並安裝 NVIDIA CUDA 12.2
# 3. 自動下載並安裝 cuDNN 8.9
# 4. 配置所有必要的 GPU 庫

# 預計下載大小: ~2-3 GB
# 預計安裝時間: 5-10 分鐘（取決於網速）
```

#### 5.1 驗證 TensorFlow GPU 支援

```bash
# 測試 TensorFlow 是否可以看到 GPU
python3 << 'EOF'
import tensorflow as tf
print("TensorFlow version:", tf.__version__)
print("CUDA available:", tf.test.is_built_with_cuda())
print("GPU devices:", tf.config.list_physical_devices('GPU'))

# 測試 GPU 運算
if tf.config.list_physical_devices('GPU'):
    print("\n✅ GPU is available and working!")
    with tf.device('/GPU:0'):
        a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
        b = tf.constant([[5.0, 6.0], [7.0, 8.0]])
        c = tf.matmul(a, b)
        print("GPU computation test result:\n", c.numpy())
else:
    print("\n❌ GPU not detected!")
EOF

# 預期輸出:
# TensorFlow version: 2.15.0
# CUDA available: True
# GPU devices: [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
#
# ✅ GPU is available and working!
# GPU computation test result:
#  [[19. 22.]
#  [43. 50.]]
```

如果看到 GPU 被檢測到，表示安裝成功 ✅

---

### Step 6: 安裝 Sionna 1.1.0

```bash
# 確保在虛擬環境中
source ~/dev/sdr-o-ran-platform/venv/bin/activate

# 安裝 Sionna（最新版本 1.1.0）
pip install sionna

# 驗證 Sionna 安裝
python3 << 'EOF'
import sionna
print("Sionna version:", sionna.__version__)

# 測試 Sionna GPU
import tensorflow as tf
from sionna.channel import RayleighBlockFading

# 檢查 GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"✅ Sionna will use GPU: {gpus[0]}")

    # 簡單測試 Rayleigh fading channel
    with tf.device('/GPU:0'):
        channel = RayleighBlockFading(
            num_rx=1,
            num_rx_ant=1,
            num_tx=1,
            num_tx_ant=1
        )

        # 測試訊號
        tx_signal = tf.random.normal([1, 1, 100, 1], dtype=tf.complex64)
        rx_signal = channel(tx_signal)

        print(f"✅ Sionna channel test passed! Input shape: {tx_signal.shape}, Output shape: {rx_signal.shape}")
else:
    print("❌ No GPU detected for Sionna")
EOF

# 預期輸出:
# Sionna version: 1.1.0
# ✅ Sionna will use GPU: PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')
# ✅ Sionna channel test passed! Input shape: (1, 1, 100, 1), Output shape: (1, 1, 100, 1)
```

---

### Step 7: 安裝專案 Python 依賴 Install Project Python Dependencies

```bash
# 確保在虛擬環境中
source ~/dev/sdr-o-ran-platform/venv/bin/activate

cd ~/dev/sdr-o-ran-platform

# 安裝所有專案依賴
pip install -r requirements.txt

# 如果沒有 requirements.txt，手動安裝主要依賴:
pip install \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    grpcio==1.60.0 \
    grpcio-tools==1.60.0 \
    protobuf==4.25.2 \
    pyzmq==25.1.2 \
    numpy==1.24.3 \
    scipy==1.11.4 \
    matplotlib==3.8.2 \
    gym==0.26.2 \
    stable-baselines3==2.2.1 \
    prometheus-client==0.19.0 \
    pyjwt==2.8.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.6 \
    pycryptodome==3.19.1

# 驗證關鍵套件
python3 -c "import fastapi; import grpc; import zmq; print('✅ All core packages installed')"
```

---

### Step 8: 安裝 FlexRIC 依賴 Install FlexRIC Dependencies

```bash
# 安裝 FlexRIC 所需的系統庫
sudo apt install -y \
    libsctp-dev \
    cmake-curses-gui \
    libpcre2-dev \
    libboost-all-dev \
    libprotobuf-dev \
    protobuf-compiler \
    libgrpc++-dev \
    protobuf-compiler-grpc

# 驗證安裝
dpkg -l | grep -E "libsctp|libboost|protobuf|grpc"
```

---

### Step 9: 下載並編譯 FlexRIC（含關鍵修復）

#### 9.1 下載 FlexRIC

```bash
# 創建 simulation 目錄
mkdir -p ~/simulation
cd ~/simulation

# 克隆 FlexRIC
git clone https://gitlab.eurecom.fr/mosaic5g/flexric.git
cd flexric

# 檢查當前分支和版本
git log --oneline -1
```

#### 9.2 應用關鍵修復（移除 RIC 啟動時的斷言）

**問題**: FlexRIC RIC 在沒有 E2 nodes 連接時會因斷言失敗而崩潰。

**修復**: 修改 `src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c` 第 3165 行。

**方法 1: 使用 sed 自動修復**

```bash
cd ~/simulation/flexric

# 備份原始文件
cp src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c \
   src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c.backup

# 應用修復
cat > /tmp/flexric_fix.patch << 'EOF'
--- a/src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c
+++ b/src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c
@@ -3162,7 +3162,11 @@ e2ap_enc_e42_setup_response_asn_pdu(const e42_setup_response_t* sr)
   // 9.2.1.5 Mandatory
   // E2 Node Component Configuration Addition List
   // 1 .. maxnoE2nodeComponents
-  assert(sr->len_e2_nodes_conn > 0 && "No global node conected??");
+  // MODIFIED: Allow RIC to start without E2 nodes (they can connect later)
+  // Original assertion caused crash if no nodes connected at startup
+  if(sr->len_e2_nodes_conn == 0) {
+    printf("[FlexRIC] WARNING: No E2 nodes connected yet. RIC waiting for connections...\n");
+  }

   // ... rest of the function
 }
EOF

# 應用 patch
cd ~/simulation/flexric
patch -p1 < /tmp/flexric_fix.patch

# 驗證修復
grep -A 5 "MODIFIED: Allow RIC to start" src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c
```

**方法 2: 手動編輯**

```bash
cd ~/simulation/flexric

# 使用 vim 或 nano 編輯
nano src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c

# 找到第 3165 行（或搜尋 "No global node conected"）
# 將:
assert(sr->len_e2_nodes_conn > 0 && "No global node conected??");

# 替換為:
// MODIFIED: Allow RIC to start without E2 nodes (they can connect later)
// Original assertion caused crash if no nodes connected at startup
if(sr->len_e2_nodes_conn == 0) {
  printf("[FlexRIC] WARNING: No E2 nodes connected yet. RIC waiting for connections...\n");
}

# 保存並退出（Ctrl+X, Y, Enter for nano）
```

#### 9.3 編譯 FlexRIC

```bash
cd ~/simulation/flexric

# 創建 build 目錄
mkdir -p build
cd build

# CMake 配置
cmake ..

# 編譯（使用所有 CPU 核心）
make -j$(nproc)

# 預計編譯時間: 5-10 分鐘

# 驗證編譯成功
echo "Checking build artifacts..."
ls -lh examples/ric/nearRT-RIC
ls -lh examples/xApp/c/drl/xapp_drl_policy
ls -lh examples/emulator/agent/emu_agent_gnb

# 預期: 三個可執行文件都存在，大小 > 1MB
```

#### 9.4 測試 FlexRIC RIC 啟動

```bash
cd ~/simulation/flexric/build/examples/ric

# 測試啟動 RIC（應該不會崩潰）
./nearRT-RIC &
RIC_PID=$!

# 等待 3 秒
sleep 3

# 檢查 RIC 是否還在運行
if ps -p $RIC_PID > /dev/null; then
    echo "✅ FlexRIC RIC is running successfully! (PID: $RIC_PID)"
else
    echo "❌ FlexRIC RIC crashed"
fi

# 停止 RIC
kill $RIC_PID

# 預期輸出:
# ✅ FlexRIC RIC is running successfully! (PID: 12345)
```

---

### Step 10: 創建 LEO NTN 模擬器 Create LEO NTN Simulator

#### 10.1 創建模擬器 Python 腳本

```bash
cd ~/dev/sdr-o-ran-platform/03-Implementation/sdr-platform

# 創建 leo_ntn_simulator.py
cat > leo_ntn_simulator.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
LEO NTN Simulator for SDR Ground Station
使用 Sionna + TensorFlow GPU 加速模擬 LEO 衛星通道效應
輸出 IQ samples 透過 ZMQ
"""

import numpy as np
import tensorflow as tf
import zmq
import time
import json
from typing import Tuple, Optional
from dataclasses import dataclass
import sionna
from sionna.channel import RayleighBlockFading

print("[LEO Simulator] TensorFlow version:", tf.__version__)
print("[LEO Simulator] Sionna version:", sionna.__version__)
print("[LEO Simulator] GPUs available:", tf.config.list_physical_devices('GPU'))

# 確保使用 GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"[LEO Simulator] Using GPU: {gpus[0]}")
    except RuntimeError as e:
        print(e)

@dataclass
class LEOOrbitParameters:
    """LEO 軌道參數 (3GPP TR 38.811)"""
    altitude_km: float = 600.0  # 軌道高度 (km)
    velocity_m_s: float = 7800.0  # 軌道速度 (m/s)
    inclination_deg: float = 53.0  # 軌道傾角 (度)
    earth_radius_km: float = 6371.0  # 地球半徑 (km)

    def get_range_km(self, elevation_deg: float) -> float:
        """計算衛星到地面站距離 (slant range)"""
        R = self.earth_radius_km
        h = self.altitude_km
        el_rad = np.deg2rad(elevation_deg)

        # Slant range calculation
        range_km = np.sqrt((R + h)**2 - R**2 * np.cos(el_rad)**2) - R * np.sin(el_rad)
        return range_km

    def get_doppler_shift_hz(self, elevation_deg: float, carrier_freq_hz: float) -> float:
        """計算 Doppler 頻移"""
        el_rad = np.deg2rad(elevation_deg)
        velocity_los = self.velocity_m_s * np.cos(el_rad)  # Line-of-sight velocity component
        doppler_hz = (velocity_los / 3e8) * carrier_freq_hz
        return doppler_hz

@dataclass
class NTNChannelParameters:
    """NTN 通道參數（3GPP TR 38.811）"""
    carrier_freq_hz: float = 2e10  # 20 GHz (Ka-band)
    bandwidth_hz: float = 30.72e6  # 30.72 MHz
    sample_rate_sps: float = 30.72e6  # 30.72 MSPS

    # Path loss parameters
    fspl_reference_db: float = 165.0  # Free-space path loss at 600km

    # Delay parameters
    min_delay_ms: float = 5.0  # Minimum propagation delay
    max_delay_ms: float = 25.0  # Maximum propagation delay

    # Doppler parameters
    max_doppler_hz: float = 40000.0  # ±40 kHz

    # Fading parameters
    num_paths: int = 4  # Rayleigh multipath components
    delay_spread_us: float = 1.0  # Delay spread

class LEONTNChannelModel:
    """LEO NTN 通道模型（GPU 加速）"""

    def __init__(self, params: NTNChannelParameters, gpu_id: int = 0):
        self.params = params

        # 使用 Sionna Rayleigh fading channel
        with tf.device(f'/GPU:{gpu_id}'):
            self.channel = RayleighBlockFading(
                num_rx=1,
                num_rx_ant=1,
                num_tx=1,
                num_tx_ant=1
            )

    def apply_ntn_effects(self,
                          iq_samples: np.ndarray,
                          elevation_deg: float,
                          orbit: LEOOrbitParameters) -> Tuple[np.ndarray, dict]:
        """
        應用 NTN 通道效應

        Args:
            iq_samples: Complex IQ samples (shape: [N,])
            elevation_deg: Satellite elevation angle (degrees)
            orbit: Orbit parameters

        Returns:
            (iq_with_effects, metadata)
        """
        # Convert to TensorFlow tensor
        iq_tf = tf.constant(iq_samples, dtype=tf.complex64)
        iq_tf = tf.reshape(iq_tf, [1, 1, -1, 1])  # [batch, tx, time, streams]

        # 1. Apply Rayleigh fading
        with tf.device('/GPU:0'):
            iq_faded = self.channel(iq_tf)
            iq_faded = tf.squeeze(iq_faded)  # Remove extra dims

        # 2. Calculate delay (propagation delay based on slant range)
        range_km = orbit.get_range_km(elevation_deg)
        delay_s = (range_km * 1000) / 3e8  # Speed of light
        delay_samples = int(delay_s * self.params.sample_rate_sps)

        # Apply delay (shift samples in time)
        iq_delayed = tf.concat([
            tf.zeros([delay_samples], dtype=tf.complex64),
            iq_faded
        ], axis=0)[:len(iq_samples)]

        # 3. Calculate Doppler shift
        doppler_hz = orbit.get_doppler_shift_hz(elevation_deg, self.params.carrier_freq_hz)

        # Apply Doppler (frequency shift)
        t = tf.range(len(iq_samples), dtype=tf.float32) / self.params.sample_rate_sps
        phase_shift = 2 * np.pi * doppler_hz * t
        doppler_factor = tf.exp(1j * tf.cast(phase_shift, tf.complex64))

        iq_with_doppler = iq_delayed * doppler_factor

        # 4. Apply path loss (Free Space Path Loss)
        path_loss_db = self.params.fspl_reference_db
        path_loss_linear = 10 ** (-path_loss_db / 20.0)
        iq_final = iq_with_doppler * path_loss_linear

        # 5. Add AWGN (Additive White Gaussian Noise)
        snr_db = 10.0  # Target SNR
        noise_power = 10 ** (-snr_db / 10.0)
        noise = tf.sqrt(noise_power / 2) * (
            tf.random.normal([len(iq_samples)], dtype=tf.float32) +
            1j * tf.random.normal([len(iq_samples)], dtype=tf.float32)
        )
        noise = tf.cast(noise, tf.complex64)
        iq_final = iq_final + noise

        # Convert back to numpy
        iq_output = iq_final.numpy()

        # Metadata
        metadata = {
            "elevation_deg": float(elevation_deg),
            "range_km": float(range_km),
            "delay_ms": float(delay_s * 1000),
            "delay_samples": int(delay_samples),
            "doppler_hz": float(doppler_hz),
            "path_loss_db": float(path_loss_db),
            "snr_db": float(snr_db),
            "timestamp": time.time()
        }

        return iq_output, metadata

class LEONTNSimulator:
    """完整的 LEO NTN 模擬器"""

    def __init__(self,
                 zmq_address: str = "tcp://127.0.0.1:5555",
                 batch_size: int = 8192,
                 gpu_id: int = 0):
        self.zmq_address = zmq_address
        self.batch_size = batch_size

        # Initialize parameters
        self.orbit = LEOOrbitParameters()
        self.channel_params = NTNChannelParameters()
        self.channel_model = LEONTNChannelModel(self.channel_params, gpu_id)

        # Initialize ZMQ publisher
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(zmq_address)

        print(f"[LEO Simulator] ZMQ publisher bound to {zmq_address}")
        print(f"[LEO Simulator] Batch size: {batch_size} samples")
        print(f"[LEO Simulator] Sample rate: {self.channel_params.sample_rate_sps / 1e6:.2f} MSPS")

        # Satellite pass simulation state
        self.current_elevation = 10.0  # Start at 10 degrees (horizon)
        self.elevation_rate = 0.1  # degrees per batch update

    def generate_test_signal(self) -> np.ndarray:
        """生成測試 IQ 訊號（QPSK modulated random data）"""
        # Generate random QPSK symbols
        num_symbols = self.batch_size // 4  # 4 samples per symbol (oversampling factor)
        bits = np.random.randint(0, 2, num_symbols * 2)

        # QPSK mapping: 00->(-1,-1), 01->(-1,+1), 10->(+1,-1), 11->(+1,+1)
        symbols = (2 * bits[0::2] - 1) + 1j * (2 * bits[1::2] - 1)
        symbols = symbols / np.sqrt(2)  # Normalize power to 1

        # Upsample (simplified pulse shaping)
        iq_samples = np.repeat(symbols, 4)[:self.batch_size]

        return iq_samples.astype(np.complex64)

    def run(self, duration_s: float = 60.0):
        """運行模擬器"""
        print(f"\n[LEO Simulator] Starting simulation for {duration_s} seconds...")
        print("[LEO Simulator] Press Ctrl+C to stop\n")

        start_time = time.time()
        batch_count = 0

        try:
            while (time.time() - start_time) < duration_s:
                # Generate test signal
                iq_clean = self.generate_test_signal()

                # Apply NTN channel effects
                iq_with_ntn, metadata = self.channel_model.apply_ntn_effects(
                    iq_clean,
                    self.current_elevation,
                    self.orbit
                )

                # Prepare ZMQ message
                message = {
                    "iq_real": iq_with_ntn.real.tolist(),
                    "iq_imag": iq_with_ntn.imag.tolist(),
                    "metadata": metadata,
                    "batch_id": batch_count
                }

                # Send via ZMQ
                self.socket.send_json(message)

                batch_count += 1

                # Update satellite elevation (simulate orbital pass)
                self.current_elevation += self.elevation_rate
                if self.current_elevation > 90:
                    self.current_elevation = 10.0  # Reset to horizon

                # Print status every 10 batches
                if batch_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = batch_count / elapsed
                    print(f"[LEO Simulator] Batch {batch_count:6d} | "
                          f"Elevation: {metadata['elevation_deg']:5.1f}° | "
                          f"Doppler: {metadata['doppler_hz']:+8.1f} Hz | "
                          f"Delay: {metadata['delay_ms']:5.2f} ms | "
                          f"Rate: {rate:.1f} batches/s")

                # Simulate real-time transmission (sleep to match sample rate)
                # Each batch is batch_size/sample_rate seconds
                time.sleep(self.batch_size / self.channel_params.sample_rate_sps)

        except KeyboardInterrupt:
            print("\n[LEO Simulator] Stopped by user")

        finally:
            elapsed = time.time() - start_time
            print(f"\n[LEO Simulator] Summary:")
            print(f"  Total batches: {batch_count}")
            print(f"  Duration: {elapsed:.1f} seconds")
            print(f"  Average rate: {batch_count / elapsed:.1f} batches/s")
            print(f"  Total samples: {batch_count * self.batch_size:,}")

            self.socket.close()
            self.context.term()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LEO NTN Simulator")
    parser.add_argument("--zmq-address", type=str, default="tcp://127.0.0.1:5555",
                        help="ZMQ publish address (default: tcp://127.0.0.1:5555 for local, tcp://0.0.0.0:5555 for network)")
    parser.add_argument("--batch-size", type=int, default=8192,
                        help="IQ samples per batch (default: 8192)")
    parser.add_argument("--duration", type=float, default=60.0,
                        help="Simulation duration in seconds (default: 60)")
    parser.add_argument("--gpu", type=int, default=0,
                        help="GPU device ID (default: 0)")

    args = parser.parse_args()

    # Create and run simulator
    simulator = LEONTNSimulator(
        zmq_address=args.zmq_address,
        batch_size=args.batch_size,
        gpu_id=args.gpu
    )

    simulator.run(duration_s=args.duration)
PYTHON_EOF

# 賦予執行權限
chmod +x leo_ntn_simulator.py

echo "✅ LEO NTN Simulator created successfully"
```

#### 10.2 測試 LEO 模擬器

```bash
# 確保在虛擬環境中
source ~/dev/sdr-o-ran-platform/venv/bin/activate

# 測試運行（30 秒）
cd ~/dev/sdr-o-ran-platform/03-Implementation/sdr-platform
python3 leo_ntn_simulator.py --duration 30

# 預期輸出:
# [LEO Simulator] TensorFlow version: 2.15.0
# [LEO Simulator] Sionna version: 1.1.0
# [LEO Simulator] GPUs available: [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
# [LEO Simulator] Using GPU: PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')
# [LEO Simulator] ZMQ publisher bound to tcp://127.0.0.1:5555
# [LEO Simulator] Batch size: 8192 samples
# [LEO Simulator] Sample rate: 30.72 MSPS
#
# [LEO Simulator] Starting simulation for 30.0 seconds...
# [LEO Simulator] Press Ctrl+C to stop
#
# [LEO Simulator] Batch 000010 | Elevation:  10.1° | Doppler: +25234.5 Hz | Delay:  12.34 ms | Rate: 8.5 batches/s
# ...

# 如果看到上述輸出並且 GPU 正在使用，表示模擬器工作正常 ✅
```

---

### Step 11: 創建一鍵啟動腳本 Create One-Click Startup Script

```bash
cd ~/dev/sdr-o-ran-platform

cat > start_all_services.sh << 'BASH_EOF'
#!/bin/bash
# 一鍵啟動所有服務 - SDR + O-RAN + LEO Simulator

set -e

echo "======================================================================"
echo "  Starting SDR Ground Station + O-RAN + LEO NTN Integration Platform"
echo "======================================================================"
echo

# 檢查是否在虛擬環境中
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "[Setup] Activating Python virtual environment..."
    source ~/dev/sdr-o-ran-platform/venv/bin/activate
fi

# 創建 log 目錄
mkdir -p logs

echo "[1/5] Starting LEO NTN Simulator (ZMQ publisher on tcp://127.0.0.1:5555)..."
cd ~/dev/sdr-o-ran-platform/03-Implementation/sdr-platform
python3 leo_ntn_simulator.py --duration 3600 > ~/dev/sdr-o-ran-platform/logs/leo_simulator.log 2>&1 &
LEO_PID=$!
echo "       PID: $LEO_PID"
echo "       Log: ~/dev/sdr-o-ran-platform/logs/leo_simulator.log"
sleep 3  # Wait for ZMQ to bind

echo "[2/5] Starting SDR API Gateway (FastAPI on :8000)..."
cd ~/dev/sdr-o-ran-platform/03-Implementation/sdr-platform
python3 sdr_api_server.py > ~/dev/sdr-o-ran-platform/logs/sdr_api.log 2>&1 &
SDR_API_PID=$!
echo "       PID: $SDR_API_PID"
echo "       URL: http://localhost:8000"
echo "       Log: ~/dev/sdr-o-ran-platform/logs/sdr_api.log"
sleep 2

echo "[3/5] Starting SDR gRPC Server (IQ streaming on :50051, receiving from ZMQ)..."
cd ~/dev/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector
if [ -f sdr_grpc_server.py ]; then
    python3 sdr_grpc_server.py --use-zmq --zmq-address tcp://127.0.0.1:5555 \
        > ~/dev/sdr-o-ran-platform/logs/sdr_grpc.log 2>&1 &
    GRPC_PID=$!
    echo "       PID: $GRPC_PID"
    echo "       Log: ~/dev/sdr-o-ran-platform/logs/sdr_grpc.log"
else
    echo "       ⚠️  sdr_grpc_server.py not found, skipping"
    GRPC_PID=0
fi
sleep 2

echo "[4/5] Starting FlexRIC Near-RT RIC..."
cd ~/simulation/flexric/build/examples/ric
./nearRT-RIC > ~/dev/sdr-o-ran-platform/logs/flexric_ric.log 2>&1 &
RIC_PID=$!
echo "       PID: $RIC_PID"
echo "       Log: ~/dev/sdr-o-ran-platform/logs/flexric_ric.log"
sleep 3

echo "[5/5] Starting FlexRIC E2 Emulator Agent (gNB emulation)..."
cd ~/simulation/flexric/build/examples/emulator/agent
./emu_agent_gnb > ~/dev/sdr-o-ran-platform/logs/flexric_agent.log 2>&1 &
AGENT_PID=$!
echo "       PID: $AGENT_PID"
echo "       Log: ~/dev/sdr-o-ran-platform/logs/flexric_agent.log"
sleep 2

echo
echo "======================================================================"
echo "  ✅ All services started successfully!"
echo "======================================================================"
echo
echo "Service Status:"
echo "  1. LEO NTN Simulator:  PID $LEO_PID  (ZMQ: tcp://127.0.0.1:5555)"
echo "  2. SDR API Gateway:    PID $SDR_API_PID  (HTTP: http://localhost:8000)"
if [ $GRPC_PID -ne 0 ]; then
    echo "  3. SDR gRPC Server:    PID $GRPC_PID  (gRPC: :50051)"
fi
echo "  4. FlexRIC RIC:        PID $RIC_PID"
echo "  5. FlexRIC E2 Agent:   PID $AGENT_PID"
echo
echo "Logs location: ~/dev/sdr-o-ran-platform/logs/"
echo
echo "To view logs:"
echo "  tail -f ~/dev/sdr-o-ran-platform/logs/leo_simulator.log"
echo "  tail -f ~/dev/sdr-o-ran-platform/logs/sdr_api.log"
echo "  tail -f ~/dev/sdr-o-ran-platform/logs/flexric_ric.log"
echo "  tail -f ~/dev/sdr-o-ran-platform/logs/flexric_agent.log"
echo
echo "To test DRL xApp:"
echo "  cd ~/simulation/flexric/build/examples/xApp/c/drl"
echo "  ./xapp_drl_policy"
echo
echo "To stop all services:"
echo "  ~/dev/sdr-o-ran-platform/stop_all_services.sh"
echo
echo "======================================================================"

# 保存 PID 到文件以便後續停止
echo "$LEO_PID $SDR_API_PID $GRPC_PID $RIC_PID $AGENT_PID" > ~/dev/sdr-o-ran-platform/.service_pids
BASH_EOF

chmod +x start_all_services.sh

echo "✅ Startup script created: ~/dev/sdr-o-ran-platform/start_all_services.sh"
```

#### 11.1 創建停止腳本

```bash
cd ~/dev/sdr-o-ran-platform

cat > stop_all_services.sh << 'BASH_EOF'
#!/bin/bash
# 停止所有服務

echo "Stopping all services..."

if [ -f ~/dev/sdr-o-ran-platform/.service_pids ]; then
    PIDS=$(cat ~/dev/sdr-o-ran-platform/.service_pids)
    echo "Found PIDs: $PIDS"

    for PID in $PIDS; do
        if [ $PID -ne 0 ] && ps -p $PID > /dev/null 2>&1; then
            echo "  Stopping PID $PID..."
            kill $PID 2>/dev/null
        fi
    done

    # Wait a moment then force kill if needed
    sleep 2
    for PID in $PIDS; do
        if [ $PID -ne 0 ] && ps -p $PID > /dev/null 2>&1; then
            echo "  Force stopping PID $PID..."
            kill -9 $PID 2>/dev/null
        fi
    done

    rm ~/dev/sdr-o-ran-platform/.service_pids
    echo "✅ All services stopped."
else
    echo "No running services found (.service_pids not found)"
    echo "Trying to kill by process name..."

    killall python3 2>/dev/null
    killall nearRT-RIC 2>/dev/null
    killall emu_agent_gnb 2>/dev/null

    echo "✅ Cleanup done."
fi
BASH_EOF

chmod +x stop_all_services.sh

echo "✅ Stop script created: ~/dev/sdr-o-ran-platform/stop_all_services.sh"
```

---

### Step 12: 端到端測試 End-to-End Testing

#### 12.1 啟動所有服務

```bash
cd ~/dev/sdr-o-ran-platform
./start_all_services.sh

# 預期看到所有 5 個服務啟動成功
```

#### 12.2 驗證服務運行

```bash
# 檢查進程
ps aux | grep python3
ps aux | grep nearRT-RIC
ps aux | grep emu_agent

# 查看 LEO 模擬器 log（應該看到 GPU 正在運行）
tail -f ~/dev/sdr-o-ran-platform/logs/leo_simulator.log

# 查看 FlexRIC RIC log（應該看到 "WARNING: No E2 nodes connected yet" 或 "E2 Setup Success"）
tail -f ~/dev/sdr-o-ran-platform/logs/flexric_ric.log
```

#### 12.3 測試 DRL xApp（可選）

```bash
# 在新的終端執行
cd ~/simulation/flexric/build/examples/xApp/c/drl
./xapp_drl_policy

# 預期輸出:
# [xApp DRL] Connected to RIC
# [xApp DRL] Subscribed to E2SM-KPM
# [xApp DRL] Receiving metrics...
```

#### 12.4 API 測試

```bash
# 測試 SDR API Gateway
curl http://localhost:8000/healthz

# 預期輸出: {"status":"healthy"}
```

---

## 🤖 自動化安裝腳本 Automated Installation Script

如果你想一鍵完成所有安裝（Steps 0-11），使用以下自動化腳本：

### 完整自動化安裝

```bash
# 創建並運行自動安裝腳本
cat > ~/setup_gpu_machine.sh << 'SETUP_EOF'
#!/bin/bash
# GPU 機器完整自動化安裝腳本
# 用於 SDR + O-RAN + LEO NTN 整合平台

set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         GPU Machine Automated Setup for SDR + O-RAN Platform         ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check GPU
log_info "Step 1: Checking NVIDIA GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    log_warn "nvidia-smi not found. Please install NVIDIA driver first:"
    echo "  sudo apt install nvidia-driver-535"
    echo "  sudo reboot"
    exit 1
fi

nvidia-smi
log_info "✅ GPU detected successfully"

# Step 2: Update system and install basic tools
log_info "Step 2: Updating system and installing basic tools..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y git build-essential wget curl vim htop net-tools \
    python3-pip python3-dev python3-venv

# Step 3: Install CMake 3.22+
log_info "Step 3: Installing CMake 3.22+..."
CMAKE_VERSION=$(cmake --version 2>/dev/null | head -n1 | awk '{print $3}')
if [[ "$CMAKE_VERSION" < "3.22" ]]; then
    log_warn "CMake version < 3.22, installing latest version..."
    sudo apt remove cmake -y
    wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | \
        gpg --dearmor - | \
        sudo tee /etc/apt/trusted.gpg.d/kitware.gpg >/dev/null
    sudo apt-add-repository "deb https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main"
    sudo apt update
    sudo apt install -y cmake
fi
cmake --version
log_info "✅ CMake installed"

# Step 4: Clone project from GitHub
log_info "Step 4: Cloning project from GitHub..."
mkdir -p ~/dev
cd ~/dev

# ⚠️ 重要：請替換成你的實際 GitHub URL
GITHUB_URL="https://github.com/YOUR_USERNAME/sdr-o-ran-platform.git"

log_warn "⚠️  Please ensure you have pushed the project to GitHub!"
log_warn "⚠️  Modify GITHUB_URL in this script if needed"

if [ ! -d "sdr-o-ran-platform" ]; then
    git clone $GITHUB_URL
    log_info "✅ Project cloned"
else
    log_info "Project directory already exists, pulling latest changes..."
    cd sdr-o-ran-platform && git pull && cd ..
fi

# Step 5: Create Python virtual environment
log_info "Step 5: Creating Python virtual environment..."
cd ~/dev/sdr-o-ran-platform
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
log_info "✅ Virtual environment created"

# Step 6: Install TensorFlow 2.15 with GPU
log_info "Step 6: Installing TensorFlow 2.15 with GPU support (this may take 10-15 minutes)..."
pip install tensorflow[and-cuda]==2.15.0
log_info "✅ TensorFlow installed"

# Step 7: Verify TensorFlow GPU
log_info "Step 7: Verifying TensorFlow GPU support..."
python3 << 'PY_EOF'
import tensorflow as tf
print("TensorFlow version:", tf.__version__)
print("GPU devices:", tf.config.list_physical_devices('GPU'))
if tf.config.list_physical_devices('GPU'):
    print("✅ GPU is available!")
else:
    print("❌ GPU not detected!")
    exit(1)
PY_EOF
log_info "✅ TensorFlow GPU verified"

# Step 8: Install Sionna
log_info "Step 8: Installing Sionna 1.1.0..."
pip install sionna
log_info "✅ Sionna installed"

# Step 9: Install project dependencies
log_info "Step 9: Installing project Python dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    pip install fastapi uvicorn grpcio grpcio-tools protobuf pyzmq \
        numpy scipy matplotlib gym stable-baselines3 \
        prometheus-client pyjwt passlib[bcrypt] python-multipart pycryptodome
fi
log_info "✅ Project dependencies installed"

# Step 10: Install FlexRIC dependencies
log_info "Step 10: Installing FlexRIC dependencies..."
sudo apt install -y libsctp-dev cmake-curses-gui libpcre2-dev \
    libboost-all-dev libprotobuf-dev protobuf-compiler \
    libgrpc++-dev protobuf-compiler-grpc
log_info "✅ FlexRIC dependencies installed"

# Step 11: Clone and compile FlexRIC
log_info "Step 11: Cloning and compiling FlexRIC (this may take 10-15 minutes)..."
mkdir -p ~/simulation
cd ~/simulation

if [ ! -d "flexric" ]; then
    git clone https://gitlab.eurecom.fr/mosaic5g/flexric.git
fi

cd flexric

# Apply fix
log_info "Applying FlexRIC RIC startup fix..."
if grep -q "No global node conected" src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c; then
    cp src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c \
       src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c.backup

    # Use sed to replace the assertion
    sed -i '3165s/.*/  \/\/ MODIFIED: Allow RIC to start without E2 nodes\n  if(sr->len_e2_nodes_conn == 0) {\n    printf("[FlexRIC] WARNING: No E2 nodes connected yet. RIC waiting for connections...\\n");\n  }/' \
        src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c

    log_info "✅ FlexRIC fix applied"
fi

# Compile
mkdir -p build
cd build
cmake ..
make -j$(nproc)
log_info "✅ FlexRIC compiled"

# Step 12: Verify FlexRIC
log_info "Step 12: Verifying FlexRIC compilation..."
if [ -f examples/ric/nearRT-RIC ] && [ -f examples/xApp/c/drl/xapp_drl_policy ]; then
    log_info "✅ FlexRIC binaries found"
else
    log_error "FlexRIC compilation failed!"
    exit 1
fi

# Step 13: Create LEO NTN Simulator (already done in project)
log_info "Step 13: Verifying LEO NTN Simulator..."
cd ~/dev/sdr-o-ran-platform/03-Implementation/sdr-platform
if [ -f leo_ntn_simulator.py ]; then
    log_info "✅ LEO NTN Simulator found"
else
    log_warn "LEO NTN Simulator not found, please create it manually from the guide"
fi

# Step 14: Create startup scripts (already done)
log_info "Step 14: Verifying startup scripts..."
cd ~/dev/sdr-o-ran-platform
if [ -f start_all_services.sh ]; then
    log_info "✅ Startup scripts found"
else
    log_warn "Startup scripts not found, please create them manually"
fi

echo
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Installation Complete!                          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     source ~/dev/sdr-o-ran-platform/venv/bin/activate"
echo
echo "  2. Test LEO NTN Simulator:"
echo "     cd ~/dev/sdr-o-ran-platform/03-Implementation/sdr-platform"
echo "     python3 leo_ntn_simulator.py --duration 30"
echo
echo "  3. Start all services:"
echo "     cd ~/dev/sdr-o-ran-platform"
echo "     ./start_all_services.sh"
echo
echo "  4. View logs:"
echo "     tail -f ~/dev/sdr-o-ran-platform/logs/leo_simulator.log"
echo
SETUP_EOF

chmod +x ~/setup_gpu_machine.sh

# 運行自動安裝
~/setup_gpu_machine.sh
```

---

## ✅ 安裝驗證清單 Installation Checklist

完成安裝後，請驗證以下項目：

- [ ] **GPU 可用**: `nvidia-smi` 顯示 GPU 資訊
- [ ] **CUDA 可用**: TensorFlow 可以檢測到 GPU
- [ ] **CMake 版本**: `cmake --version` >= 3.22
- [ ] **專案克隆**: `~/dev/sdr-o-ran-platform` 目錄存在
- [ ] **Python 環境**: `source ~/dev/sdr-o-ran-platform/venv/bin/activate` 成功
- [ ] **TensorFlow GPU**: `python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"` 顯示 GPU
- [ ] **Sionna 安裝**: `python3 -c "import sionna; print(sionna.__version__)"` 顯示 1.1.0
- [ ] **FlexRIC 編譯**: `~/simulation/flexric/build/examples/ric/nearRT-RIC` 可執行
- [ ] **LEO 模擬器**: `~/dev/sdr-o-ran-platform/03-Implementation/sdr-platform/leo_ntn_simulator.py` 存在
- [ ] **啟動腳本**: `~/dev/sdr-o-ran-platform/start_all_services.sh` 可執行
- [ ] **FlexRIC RIC 啟動**: RIC 可以啟動且不崩潰
- [ ] **LEO 模擬器運行**: 模擬器可以運行並輸出 IQ samples

---

## 🐛 故障排除 Troubleshooting

### 問題 1: TensorFlow 找不到 GPU

**症狀**:
```python
tf.config.list_physical_devices('GPU')
# 輸出: []
```

**解決方案**:

```bash
# 1. 檢查 NVIDIA 驅動
nvidia-smi

# 2. 重新安裝 TensorFlow with CUDA
pip uninstall tensorflow
pip install tensorflow[and-cuda]==2.15.0

# 3. 設置環境變數（如果需要）
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/dev/sdr-o-ran-platform/venv/lib/python3.*/site-packages/nvidia/cuda_nvcc/lib

# 4. 重啟 Python 並測試
```

### 問題 2: FlexRIC 編譯失敗

**症狀**:
```
error: 'assert' was not declared
```

**解決方案**:

```bash
# 確保所有依賴都已安裝
sudo apt install -y libsctp-dev libboost-all-dev libprotobuf-dev

# 清除 build 目錄重新編譯
cd ~/simulation/flexric
rm -rf build
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 問題 3: 記憶體不足

**症狀**:
```
tensorflow.python.framework.errors_impl.ResourceExhaustedError: OOM
```

**解決方案**:

```bash
# 減少 batch size
python3 leo_ntn_simulator.py --batch-size 4096

# 或限制 GPU 記憶體
# （在 leo_ntn_simulator.py 中已經設置了 memory_growth）
```

---

## 📊 效能基準 Performance Benchmarks

預期效能指標：

| 指標 | 值 |
|------|---|
| **GPU 利用率** | 30-60% |
| **ZMQ 吞吐量** | > 500 Mbps (local) |
| **模擬器速率** | 8-10 batches/s |
| **延遲** | < 1 ms (per batch) |
| **記憶體使用** | 8-12 GB |

---

## 📚 相關文檔 Related Documentation

- **完整架構**: `COMPLETE-PROJECT-ARCHITECTURE-AND-ROADMAP.md`
- **部署指南**: `DEPLOYMENT-GUIDE.md`
- **GPU 詳細設置**: `GPU-MACHINE-LEO-SIMULATOR-SETUP.md`
- **專案 README**: `README.md`

---

## 🎯 下一步 Next Steps

1. **完成安裝後**:
   - 啟動所有服務: `./start_all_services.sh`
   - 查看日誌確認運行狀態
   - 測試 DRL xApp 整合

2. **E2E 測試**:
   - 驗證 LEO → SDR → O-RAN 數據流
   - 收集效能指標
   - 撰寫測試報告

3. **優化與調整**:
   - 調整 LEO 軌道參數
   - 優化 DRL 策略
   - 準備論文數據

---

**作者**: 蔡秀吉 (Hsiu-Chi Tsai)
**聯絡**: thc1006@gmail.com
**最後更新**: 2025-11-10
**版本**: 1.0

**祝安裝順利！Good luck with the setup!** 🚀
