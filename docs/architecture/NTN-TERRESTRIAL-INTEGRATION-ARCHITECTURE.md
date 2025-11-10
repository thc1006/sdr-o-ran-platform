# NTN-Terrestrial Integration Architecture
# 基於雲原生之 SDR 基頻處理地面站和 O-RAN 基站整合應用於 NTN 通訊

**日期**: 2025-11-10
**架構**: Satellite Gateway with O-RAN Integration
**符合標準**: 3GPP TR 38.821 (NTN Solutions)

---

## 📋 專案核心目標（重新確認）

實現 **LEO 衛星 → SDR Ground Station (Gateway) → O-RAN 地面網路** 的完整整合架構。

### 關鍵創新點

1. **SDR Ground Station 作為 Satellite Gateway**
   - 使用 USRP X310 接收 LEO 衛星訊號
   - 雲原生基頻處理（Cloud-Native Baseband Processing）
   - 整合到 O-RAN 地面網路

2. **NTN-Terrestrial 混合網路**
   - LEO 衛星段：提供覆蓋（特別是偏遠地區）
   - Ground Station：Gateway + Baseband Processing
   - O-RAN 地面段：標準 5G 網路 + RIC + AI/ML

3. **智能資源管理**
   - DRL xApp 優化 NTN ↔ Terrestrial 流量分配
   - 動態切換和負載平衡
   - QoS 保證

---

## 🏗️ 完整架構設計

### Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    End-to-End System Architecture                     ║
╚═══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────┐
│  SPACE SEGMENT (太空段)                                              │
└─────────────────────────────────────────────────────────────────────┘

                         🛰️  LEO Satellite
                            Altitude: 600 km
                            Orbit: Polar/Sun-synchronous

                         Payload: Transparent Bent-Pipe
                         ├─ Receive: Ka-band uplink
                         ├─ Amplify & Frequency convert
                         └─ Transmit: Ka-band downlink

                              ↓ Feeder Link ↓
                         (27-31 GHz downlink)
                         • Delay: 5-25 ms
                         • Doppler: ±40 kHz
                         • FSPL: ~165 dB

┌─────────────────────────────────────────────────────────────────────┐
│  GROUND STATION SEGMENT (地面站段) ★ 核心創新 ★                      │
└─────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │         SDR Ground Station (Satellite Gateway)          │
    │                                                         │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │  Hardware Layer                                   │  │
    │  │  ┌─────────────┐      ┌──────────────┐          │  │
    │  │  │ USRP X310   │◄────►│ Ka-band      │          │  │
    │  │  │             │      │ Antenna      │          │  │
    │  │  │ 2x TwinRX   │      │ (Parabolic)  │          │  │
    │  │  │ 10-6000 MHz │      │ 1.2m dish    │          │  │
    │  │  └─────────────┘      └──────────────┘          │  │
    │  └──────────────────────────────────────────────────┘  │
    │                           ↕                             │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │  Cloud-Native Baseband Processing (CNF)          │  │
    │  │                                                   │  │
    │  │  ┌─────────────────────────────────────────┐    │  │
    │  │  │  RAN Protocol Stack Container           │    │  │
    │  │  │                                          │    │  │
    │  │  │  ┌────────────────────────────────────┐ │    │  │
    │  │  │  │ PHY Layer (5G NR)                  │ │    │  │
    │  │  │  │ • IQ sample processing             │ │    │  │
    │  │  │  │ • OFDM modulation/demodulation     │ │    │  │
    │  │  │  │ • Channel estimation & equalization│ │    │  │
    │  │  │  │ • NTN-specific:                    │ │    │  │
    │  │  │  │   - Doppler pre-compensation       │ │    │  │
    │  │  │  │   - Timing Advance (large delay)   │ │    │  │
    │  │  │  └────────────────────────────────────┘ │    │  │
    │  │  │                  ↕                        │    │  │
    │  │  │  ┌────────────────────────────────────┐ │    │  │
    │  │  │  │ MAC Layer                          │ │    │  │
    │  │  │  │ • Scheduling (NTN-aware)           │ │    │  │
    │  │  │  │ • HARQ (extended timeout)          │ │    │  │
    │  │  │  │ • Random Access (PRACH for NTN)    │ │    │  │
    │  │  │  └────────────────────────────────────┘ │    │  │
    │  │  │                  ↕                        │    │  │
    │  │  │  ┌────────────────────────────────────┐ │    │  │
    │  │  │  │ RLC/PDCP                           │ │    │  │
    │  │  │  │ • Segmentation & reassembly        │ │    │  │
    │  │  │  │ • Ciphering & integrity protection │ │    │  │
    │  │  │  └────────────────────────────────────┘ │    │  │
    │  │  └─────────────────────────────────────────┘    │  │
    │  └──────────────────────────────────────────────────┘  │
    │                           ↕                             │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │  Gateway Function (NTN ↔ Terrestrial)            │  │
    │  │                                                   │  │
    │  │  • Protocol conversion                            │  │
    │  │  • Traffic aggregation                            │  │
    │  │  • QoS mapping (NTN → Terrestrial)                │  │
    │  │  • Handover management (satellite beam → cell)    │  │
    │  │  • E2 interface (to RIC)                          │  │
    │  └──────────────────────────────────────────────────┘  │
    │                                                         │
    │  Orchestration: Kubernetes + Nephio                     │
    │  Deployment: Cloud-Native CNF                           │
    └────────────────────────────────────────────────────────┘
                              ↓
                        S1/N2 Interface
                              ↓

┌─────────────────────────────────────────────────────────────────────┐
│  TERRESTRIAL SEGMENT (地面網路段)                                    │
└─────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │              O-RAN 5G Network                           │
    │                                                         │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │  O-RAN gNB (Terrestrial)                         │  │
    │  │  • Standard 5G NR (sub-6 GHz or mmWave)          │  │
    │  │  • CU-DU split architecture                      │  │
    │  │  • E2 agent (connect to RIC)                     │  │
    │  └──────────────────────────────────────────────────┘  │
    │                           ↕ E2                          │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │  Near-RT RIC (FlexRIC)                           │  │
    │  │                                                   │  │
    │  │  ┌────────────────────────────────────────────┐  │  │
    │  │  │  E2 Service Models                         │  │  │
    │  │  │  • E2SM-KPM: Metrics from both NTN & Terr │  │  │
    │  │  │  • E2SM-RC: Control both segments          │  │  │
    │  │  └────────────────────────────────────────────┘  │  │
    │  │                                                   │  │
    │  │  ┌────────────────────────────────────────────┐  │  │
    │  │  │  DRL xApp (Traffic Steering) ★             │  │  │
    │  │  │                                            │  │  │
    │  │  │  State (11-dim):                          │  │  │
    │  │  │  • NTN metrics: delay, Doppler, RSRP      │  │  │
    │  │  │  • Terrestrial metrics: throughput, load  │  │  │
    │  │  │  • User distribution                       │  │  │
    │  │  │                                            │  │  │
    │  │  │  Action (5-dim):                          │  │  │
    │  │  │  • NTN/Terrestrial split ratio           │  │  │
    │  │  │  • Handover threshold                     │  │  │
    │  │  │  • QoS parameter adjustment               │  │  │
    │  │  │                                            │  │  │
    │  │  │  Reward:                                   │  │  │
    │  │  │  • Network throughput (40%)               │  │  │
    │  │  │  • Latency (30%)                          │  │  │
    │  │  │  • Coverage (20%)                         │  │  │
    │  │  │  • Energy efficiency (10%)                │  │  │
    │  │  └────────────────────────────────────────────┘  │  │
    │  └──────────────────────────────────────────────────┘  │
    │                           ↕ N2/N3                       │
    │  ┌──────────────────────────────────────────────────┐  │
    │  │  5G Core Network                                 │  │
    │  │  • AMF (Access & Mobility Management)            │  │
    │  │  • SMF (Session Management)                      │  │
    │  │  • UPF (User Plane Function)                     │  │
    │  │  • NRF, AUSF, UDM...                             │  │
    │  └──────────────────────────────────────────────────┘  │
    └────────────────────────────────────────────────────────┘
                              ↓
                         Internet / DN
```

---

## 🔄 數據流程詳解

### Downlink (User in satellite beam → Internet)

```
Step 1: User Equipment (UE) in satellite beam
    ↓ Uplink (S-band/Ka-band, 1-2 GHz or 20-30 GHz)

Step 2: LEO Satellite
    • Receive UE signal
    • Transparent relay (no processing)
    • Frequency conversion
    ↓ Feeder Link Downlink (27-31 GHz)

Step 3: SDR Ground Station (USRP X310)
    ┌─────────────────────────────────────────┐
    │ 1. RF Reception (Ka-band antenna)       │
    │    • 27-31 GHz downlink                 │
    │    • Signal: -100 to -120 dBm           │
    │                                         │
    │ 2. Frequency Downconversion (USRP)      │
    │    • Ka-band → IF → Baseband            │
    │    • IQ samples @ 30.72 Msps            │
    │                                         │
    │ 3. Baseband Processing (CNF)            │
    │    a. Doppler Compensation              │
    │       • Estimate: ±40 kHz shift         │
    │       • Correct frequency offset        │
    │                                         │
    │    b. OFDM Demodulation                 │
    │       • FFT (2048/4096 points)          │
    │       • Channel estimation              │
    │       • Equalization                    │
    │                                         │
    │    c. Demodulation & Decoding           │
    │       • QAM demapping                   │
    │       • LDPC decoding                   │
    │       • CRC check                       │
    │                                         │
    │    d. MAC Processing                    │
    │       • Extract transport blocks        │
    │       • HARQ processing                 │
    │       • Reassembly                      │
    │                                         │
    │    e. RLC/PDCP                          │
    │       • Deciphering                     │
    │       • Integrity verification          │
    │       • Header decompression            │
    │                                         │
    │ 4. Gateway Function                     │
    │    • Extract IP packets                 │
    │    • QoS mapping                        │
    │    • Routing decision (via RIC xApp)    │
    └─────────────────────────────────────────┘
    ↓ S1/N2 interface

Step 4: O-RAN Terrestrial Network
    • 5G Core processes packets
    • Forward to Internet/DN
    ↓

Step 5: Destination (Internet)
```

### Uplink (Internet → User in satellite beam)

```
Step 1: Internet / Data Network
    ↓

Step 2: 5G Core
    • UPF receives packets
    • SMF session management
    ↓ N3 interface

Step 3: O-RAN gNB (or SDR Ground Station)
    • RIC xApp decides routing:
      Option A: Via terrestrial gNB (if UE in terrestrial coverage)
      Option B: Via satellite (if UE only in satellite coverage)
    ↓ (Assuming Option B: Satellite)

Step 4: SDR Ground Station
    ┌─────────────────────────────────────────┐
    │ 1. Receive IP packets (from Core)       │
    │                                         │
    │ 2. RLC/PDCP Processing                  │
    │    • Ciphering                          │
    │    • Header compression                 │
    │    • Segmentation                       │
    │                                         │
    │ 3. MAC Processing                       │
    │    • Scheduler allocates resources      │
    │    • HARQ setup                         │
    │    • Create transport blocks            │
    │                                         │
    │ 4. Baseband Processing                  │
    │    a. Channel Coding                    │
    │       • CRC attachment                  │
    │       • LDPC encoding                   │
    │                                         │
    │    b. Modulation                        │
    │       • QAM mapping (16QAM/64QAM)       │
    │       • Layer mapping                   │
    │                                         │
    │    c. OFDM Modulation                   │
    │       • Resource element mapping        │
    │       • IFFT                            │
    │       • Cyclic prefix insertion         │
    │                                         │
    │    d. Doppler Pre-compensation          │
    │       • Calculate satellite position    │
    │       • Estimate Doppler shift          │
    │       • Pre-shift frequency             │
    │                                         │
    │ 5. RF Transmission (USRP X310)          │
    │    • IQ samples → DAC                   │
    │    • Upconvert to Ka-band (27-31 GHz)   │
    │    • Transmit via parabolic antenna     │
    └─────────────────────────────────────────┘
    ↓ Feeder Link Uplink (27-31 GHz)

Step 5: LEO Satellite
    • Receive ground station signal
    • Amplify & frequency convert
    • Transmit to UE beam
    ↓ Downlink (S-band/Ka-band)

Step 6: User Equipment (UE)
    • Receive & decode
```

---

## 💡 DRL xApp 智能整合

### State Space (11 dimensions)

```python
state = {
    # NTN Segment Metrics
    'ntn_delay': 5-25,              # ms, LEO round-trip delay
    'ntn_doppler': ±40,             # kHz, frequency shift
    'ntn_rsrp': -120 to -100,       # dBm, signal strength
    'ntn_throughput': 0-100,        # Mbps, current throughput

    # Terrestrial Segment Metrics
    'terr_delay': 10-50,            # ms, terrestrial latency
    'terr_load': 0-100,             # %, cell load
    'terr_throughput': 0-1000,      # Mbps, cell throughput

    # User Distribution
    'users_ntn_only': 0-1000,       # Users only in satellite coverage
    'users_both': 0-5000,           # Users in both coverages
    'users_terr_only': 0-10000,     # Users only in terrestrial

    # Network-wide
    'total_traffic': 0-10000,       # Mbps, total network traffic
}
```

### Action Space (5 dimensions)

```python
action = {
    # Traffic Steering
    'ntn_terr_split': 0.0-1.0,          # Ratio of traffic via NTN vs Terrestrial

    # Handover Control
    'handover_threshold_rsrp': -120 to -80,  # dBm, when to handover
    'handover_hysteresis': 0-10,             # dB, prevent ping-pong

    # QoS Adjustment
    'ntn_qos_priority': 0-9,            # QCI for NTN traffic
    'ntn_max_bitrate': 1-100,           # Mbps, cap per UE
}
```

### Reward Function

```python
reward = (
    0.40 * normalized_total_throughput +      # Network capacity
    0.30 * (1 - normalized_avg_latency) +     # Low latency
    0.20 * coverage_ratio +                   # Coverage (especially remote areas)
    0.10 * (1 - normalized_energy_consumption) # Energy efficiency
)

# Penalties
reward -= 0.5 * handover_failure_rate         # Penalize failed handovers
reward -= 0.3 * radio_link_failure_rate       # Penalize RLF
```

### DRL Algorithm: PPO (Proximal Policy Optimization)

**Why PPO?**
- ✅ Stable training (important for network control)
- ✅ Sample efficient (don't need millions of steps)
- ✅ Works well with continuous action spaces
- ✅ Handles non-stationary environments (satellite movement)

---

## 🛠️ 實施方案

### 方案 A: 完全模擬（本地，0 成本）⭐ 推薦起步

**架構**:
```
┌─────────────────────────────────────────────────────┐
│           您的本地電腦（單機）                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [LEO Sat Simulator]  ←→  [NTN Channel Model]      │
│         (ns-3)              (OpenNTN/Sionna)        │
│                                  ↓                  │
│  [Virtual SDR Ground Station]                       │
│      (srsRAN gNB - NTN mode)                        │
│                                  ↓                  │
│  [Gateway Function]                                 │
│      (Python/C++ bridge)                            │
│                                  ↓                  │
│  [O-RAN Terrestrial]                                │
│      • FlexRIC Near-RT RIC                          │
│      • DRL xApp (your code)                         │
│      • srsRAN gNB (terrestrial)                     │
│      • Open5GS Core                                 │
│                                  ↓                  │
│  [Virtual UE]                                       │
│      (srsUE or ns-3 UE)                             │
│                                                     │
│  通訊方式：                                          │
│  • ZMQ (IQ samples transfer)                        │
│  • TCP/IP (control plane)                           │
│  • Shared memory (low latency)                      │
└─────────────────────────────────────────────────────┘
```

**實施步驟**:

1. **Week 1: LEO + NTN Channel 模擬**
   ```bash
   # 安裝 OpenNTN
   pip install sionna tensorflow
   git clone https://github.com/ant-uni-bremen/OpenNTN.git

   # 配置 LEO channel model
   python3 setup_leo_channel.py --altitude 600e3 --velocity 7800
   ```

2. **Week 2: SDR Ground Station 虛擬化**
   ```bash
   # 安裝 srsRAN
   git clone https://github.com/srsran/srsRAN_Project.git
   cd srsRAN_Project && mkdir build && cd build
   cmake -DENABLE_NTN=ON ..
   make -j$(nproc)

   # 配置 gNB (NTN mode)
   cp configs/gnb_ntn_zmq.yml gnb.yml
   # 編輯: 設定 NTN parameters (SIB19, TA, etc.)
   ```

3. **Week 3: Gateway 功能實現**
   ```python
   # gateway_bridge.py

   class NTN_Terrestrial_Gateway:
       def __init__(self):
           # ZMQ sockets
           self.ntn_rx = zmq.Context().socket(zmq.SUB)
           self.terr_tx = zmq.Context().socket(zmq.PUB)

           # E2 interface to RIC
           self.e2_agent = E2Agent()

       def forward_traffic(self, ntn_data):
           """
           NTN → Terrestrial gateway function
           """
           # 1. Extract IP packets from NTN PHY/MAC
           ip_packets = self.extract_from_ntn(ntn_data)

           # 2. Query RIC for routing decision
           routing = self.e2_agent.query_xapp("drl", ip_packets)

           # 3. Forward to terrestrial network or process locally
           if routing['path'] == 'terrestrial':
               self.send_to_terrestrial(ip_packets)
           else:
               self.process_local(ip_packets)
   ```

4. **Week 4: O-RAN + DRL 整合**
   - FlexRIC Near-RT RIC
   - DRL xApp (already implemented!)
   - E2 subscription: 從 NTN gateway 和 terrestrial gNB

5. **Week 5: 端到端測試**
   - 模擬 UE 在衛星覆蓋區
   - 流量從 LEO → Ground Station → O-RAN → Core
   - 測量：throughput, latency, handover success rate

**成本**: $0
**時間**: 5 週
**完成度**: 70-75%（純模擬）
**論文**: 2-3 篇 IEEE/Access 會議論文

---

### 方案 B: Powder 平台（真實硬體，0 成本）⭐⭐⭐⭐⭐ 最佳

**架構**:
```
┌──────────────────────────────────────────────────────┐
│            Powder 平台 (免費使用！)                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Node 1: LEO Satellite Simulator                     │
│  ├─ High-performance server                          │
│  ├─ OpenNTN (GPU accelerated with H100)              │
│  └─ Output: IQ samples with NTN channel              │
│       ↓ (ZMQ over 10 Gbps network)                   │
│                                                      │
│  Node 2: SDR Ground Station ★ REAL HARDWARE ★        │
│  ├─ USRP X310 (真實的！)                             │
│  ├─ Ka-band frontend (如果有) or ZMQ (模擬 RF)        │
│  ├─ srsRAN gNB (NTN mode)                            │
│  ├─ Docker container: baseband processing CNF        │
│  └─ Gateway function                                 │
│       ↓ (10 Gbps Ethernet)                           │
│                                                      │
│  Node 3: O-RAN Near-RT RIC + Terrestrial gNB         │
│  ├─ FlexRIC (compiled)                               │
│  ├─ DRL xApp                                         │
│  ├─ srsRAN gNB (terrestrial mode)                    │
│  └─ USRP N300/B210 (for terrestrial UE)              │
│       ↓                                              │
│                                                      │
│  Node 4: 5G Core Network                             │
│  └─ Open5GS (all NFs in containers)                  │
│                                                      │
│  Node 5 (optional): User Equipment                   │
│  └─ USRP B210 + srsUE or COTS UE                     │
└──────────────────────────────────────────────────────┘
```

**實施步驟**:

**Week 1: Powder 環境設置**
```bash
# 1. 預約資源 (您已有帳號！)
# https://www.powderwireless.net/

# 選擇 Profile:
# - 5x d430 nodes (high-performance servers)
# - 2x USRP X310
# - 2x USRP B210 或 N300
# - 10 Gbps network

# 2. SSH 進入節點
ssh username@node1.powderwireless.net

# 3. 安裝基礎軟體
sudo apt update && sudo apt install -y \
    build-essential cmake git docker.io \
    uhd-host libuhd-dev python3-pip
```

**Week 2: 部署組件**

Node 1 (LEO Simulator):
```bash
# Install OpenNTN with GPU support
pip install sionna tensorflow-gpu
# Configure LEO channel
python3 setup_leo.py --gpu --output-zmq tcp://10.0.0.2:5555
```

Node 2 (SDR Ground Station) - **核心節點**:
```bash
# Install srsRAN
git clone https://github.com/srsran/srsRAN_Project.git
cd srsRAN_Project && mkdir build && cd build
cmake -DENABLE_NTN=ON -DENABLE_ZMQ=ON ..
make -j$(nproc)

# Configure USRP X310
uhd_find_devices  # Should see USRP X310

# Run gNB in NTN mode
./gnb -c configs/gnb_ntn_zmq.yml

# In gnb_ntn_zmq.yml:
# ru_sdr:
#   device_driver: uhd
#   device_args: type=x300
#   srate: 30.72
#   tx_gain: 60
#   rx_gain: 40
#
# ntn:
#   enabled: true
#   satellite_altitude: 600e3
#   k_offset: 600
#   sib19:
#     enabled: true
#     ephemeris: ...
```

Node 3 (RIC + Terrestrial gNB):
```bash
# FlexRIC
cd /opt/flexric && ./build/examples/ric/nearRT-RIC

# Your DRL xApp
cd /opt/flexric/build/examples/xApp/c/drl
./xapp_drl_policy

# Terrestrial gNB (standard 5G)
cd /opt/srsran && ./build/apps/gnb/gnb -c configs/gnb.yml
```

Node 4 (5G Core):
```bash
# Open5GS
docker-compose up -d
```

**Week 3-4: 整合測試與優化**

**成本**: $0（Powder 免費！）
**時間**: 4-6 週
**完成度**: 85-90%（真實硬體！）
**論文**: 3-5 篇，包含頂級期刊（IEEE JSAC, TWC, TCOM）

---

## 📊 關鍵性能指標 (KPIs)

### 測試場景

| 場景 | UE 位置 | 預期路徑 | KPI |
|------|---------|---------|-----|
| 1. 純衛星覆蓋 | 偏遠地區 | LEO → GS → Terr → Core | Latency: 50-80ms, Throughput: 20-50 Mbps |
| 2. 混合覆蓋 | 城市邊緣 | DRL 決定 NTN/Terr split | Handover success: >95%, Latency: 30-60ms |
| 3. 純地面覆蓋 | 市中心 | Terrestrial only | Latency: 10-30ms, Throughput: 100-500 Mbps |
| 4. 移動中切換 | 車輛移動 | Terr → NTN → Terr | Handover latency: <500ms, No packet loss |

### 成功標準

- ✅ **NTN Gateway 功能**: 成功接收 LEO 訊號並轉發到地面網路
- ✅ **基頻處理**: BLER < 1% @ SNR > 5 dB
- ✅ **E2 整合**: FlexRIC 可從 Gateway 接收 KPM metrics
- ✅ **DRL 優化**: 吞吐量提升 >15% compared to static routing
- ✅ **端到端延遲**: <100ms (95th percentile) for NTN path
- ✅ **覆蓋增強**: 地面網路覆蓋提升 >30% (by adding satellite)

---

## 📚 技術標準參考

### 3GPP Standards

- **TS 38.300**: NR overall description (NTN architecture)
- **TS 38.821**: Solutions for NR to support non-terrestrial networks
- **TS 38.211**: Physical channels and modulation (NTN-specific PRACH)
- **TS 38.214**: Physical layer procedures for data (TA for NTN)
- **TS 38.331**: RRC protocol (SIB19 for satellite parameters)

### O-RAN Specifications

- **O-RAN.WG3.E2AP**: E2 interface
- **O-RAN.WG3.E2SM-KPM**: KPM service model (可用於 NTN metrics)
- **O-RAN.WG3.E2SM-RC**: RC service model (控制 Gateway routing)

### ITU-R Recommendations

- **ITU-R S.1325**: Satellite systems to provide non-geostationary-satellite service
- **ITU-R M.1654**: Methodology for calculation of spectrum requirements for mobile satellite systems

---

## 🎯 論文發表策略

### Paper 1: Architecture & Integration (會議)
**Title**: "Cloud-Native SDR Ground Station for NTN-Terrestrial O-RAN Integration"
**Target**: IEEE GLOBECOM / ICC
**Focus**: 架構設計、Gateway 實現、初步結果

### Paper 2: DRL Optimization (期刊)
**Title**: "Deep Reinforcement Learning for Intelligent Traffic Steering in Hybrid NTN-Terrestrial Networks"
**Target**: IEEE Transactions on Wireless Communications
**Focus**: DRL 算法、性能提升、詳細分析

### Paper 3: System Performance (期刊)
**Title**: "Performance Analysis of Integrated Satellite-Terrestrial O-RAN System with AI-driven Resource Management"
**Target**: IEEE Journal on Selected Areas in Communications
**Focus**: 端到端性能、真實測試數據（Powder 平台）

---

## ✅ 下一步行動

### 立即可做（今天）

1. **確認需求** ✅（本文檔）
2. **選擇起步方案**:
   - 方案 A: 本地模擬（5 週，學習曲線平緩）
   - 方案 B: Powder 平台（6 週，成果更佳）
   - 混合: Week 1-2 本地測試 → Week 3+ Powder

### 本週（選擇方案 A）

1. 修復 FlexRIC（我立即幫您做）
2. 安裝 OpenNTN
3. 配置 srsRAN (NTN mode)
4. 運行第一個 NTN-Terrestrial gateway 測試

### 本週（選擇方案 B）

1. 在 Powder 預約資源
2. 準備配置文件
3. 閱讀 srsRAN NTN tutorial
4. 設計詳細實施計劃

---

**結論**: 這個重新設計的架構完全符合您的需求：LEO 衛星 → SDR Ground Station (Gateway with Baseband Processing) → O-RAN Terrestrial Network。這是一個非常有創新性和實用價值的研究方向！

**您想從哪個方案開始？我現在就可以幫您啟動！**
