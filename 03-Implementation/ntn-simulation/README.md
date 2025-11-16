# NTN (Non-Terrestrial Networks) GPU-Accelerated Simulation

## Quick Start - 立即開始 NTN 研究

這個目錄包含我們的 NTN (衛星) 模擬研究實作。

### 安裝步驟

```bash
# 1. 安裝 TensorFlow (Sionna 需求)
pip install tensorflow==2.15.0

# 2. 安裝 Sionna
pip install sionna

# 3. Clone OpenNTN
git clone https://github.com/ant-uni-bremen/OpenNTN.git
cd OpenNTN
pip install -r requirements.txt

# 4. 驗證 GPU
python -c "import tensorflow as tf; print('GPUs:', tf.config.list_physical_devices('GPU'))"
```

### 目錄結構

```
ntn-simulation/
├── README.md                        # 本文件
├── requirements.txt                 # Python 依賴
├── openNTN_integration/             # OpenNTN 整合
│   ├── leo_channel.py              # LEO 通道模型
│   ├── meo_channel.py              # MEO 通道模型
│   └── geo_channel.py              # GEO 通道模型
├── sionna_raytracing/              # Sionna 射線追蹤
│   ├── urban_scene.py              # 城市場景建模
│   └── satellite_link.py           # 衛星鏈路模擬
├── drl_constellation/              # DRL 星座優化
│   ├── leo_env.py                  # LEO 環境
│   ├── multi_agent_dqn.py          # Multi-Agent DQN
│   └── train.py                    # 訓練腳本
├── e2_ntn_extension/               # E2 Interface NTN 擴展
│   ├── e2sm_ntn.py                 # E2SM-NTN 服務模型
│   └── ntn_xapp.py                 # NTN-aware xApp
└── demos/                          # Demo 範例
    ├── demo_1_basic_ntn.py         # 基礎 NTN 模擬
    ├── demo_2_ray_tracing.py       # Ray Tracing 展示
    └── demo_3_drl_training.py      # DRL 訓練展示
```

## 研究方向

參見: `RESEARCH-PROPOSAL-NTN-GPU-SIMULATION.md`

### 五大研究方向:

1. **OpenNTN + O-RAN 整合** - 3GPP TR38.811 通道模型
2. **Sionna GPU Ray Tracing** - 衛星-地面精確傳播
3. **大規模 LEO 星座 DRL** - 1000+ 衛星資源優化
4. **再生式酬載模擬** - 衛星上的 gNB
5. **Hybrid TN-NTN AI 整合** - 地面與衛星網路融合

## 快速 Demo

```bash
# 運行基礎 NTN 模擬
python demos/demo_1_basic_ntn.py

# 運行 Ray Tracing (需要 GPU)
python demos/demo_2_ray_tracing.py

# 訓練 DRL agent (需要 GPU)
python demos/demo_3_drl_training.py
```

## GPU 硬體需求

- **最低**: 1 x RTX 3090 (24GB VRAM)
- **推薦**: 1 x RTX 4090 (24GB VRAM)
- **理想**: 8 x A100 (80GB VRAM)

## 授權

MIT License - 開源研究專案
