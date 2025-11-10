# SDR-O-RAN 平台實施路線圖
## 使用最新技術達成原始目標

**創建日期**: 2025-11-10
**目標**: 使專案盡可能符合原始 README.md 的聲稱
**方法**: 整合最新的開源技術和模擬工具

---

## 執行摘要

**當前狀態**: 60-65% 完成（主要是架構和部分代碼）
**目標狀態**: 95% 完成（接近生產就緒，但使用模擬代替真實硬體）
**預估時間**: 3-4 個月（全職開發）
**預估成本**: $0（全部使用開源工具，無需硬體）

**關鍵策略**:
- 使用 ns-3 + ns-O-RAN 模擬完整的 5G NR 網路
- 整合真實的 OSC RIC 與模擬的 RAN
- 使用 GNU Radio 模擬 SDR 信號處理
- 實現真實的 DRL 訓練（PPO/SAC）
- 在 Kubernetes 上完整部署

---

## 第一階段：硬體模擬替代方案（2週）

### 目標：用軟體模擬替代 USRP X310 硬體

#### 1.1 ns-3 + ns-O-RAN 整合 ✅ 可行

**技術方案**:
```bash
# 使用最新的 ns-3 + ns-O-RAN 模組
git clone https://github.com/wineslab/ns-o-ran-ns3-mmwave.git
git clone https://gitlab.com/cttc-lena/nr.git  # 5G-LENA
```

**功能**:
- 模擬多個 5G NR 基站（gNB）
- 實現真實的 E2 介面
- 支援 E2SM KPM（性能指標）和 E2SM RC（RAN 控制）
- 與真實的 OSC near-RT RIC 整合

**輸出**:
- 真實的網路流量和性能指標
- 可測量的延遲、吞吐量、封包遺失率
- 不再是"理論值"，而是"模擬測量值"

**實施步驟**:
1. 安裝 ns-3.43（最新版本）
2. 整合 5G-LENA 模組
3. 安裝 ns-O-RAN 模組
4. 配置多個 gNB 場景
5. 連接到 OSC RIC

**驗證標準**:
- [ ] ns-3 成功運行 5G NR 場景
- [ ] E2 介面成功連接到 RIC
- [ ] 可以獲取真實的 KPM 指標

---

#### 1.2 GNU Radio SDR 信號處理模擬 ✅ 可行

**技術方案**:
```python
# 使用 GNU Radio Python API
from gnuradio import gr, blocks, analog, digital

class SDRSimulator(gr.top_block):
    """模擬 SDR 信號處理鏈"""
    def __init__(self):
        gr.top_block.__init__(self, "SDR Simulator")
        # 生成測試信號
        self.source = analog.sig_source_c(...)
        # QPSK 調變
        self.modulator = digital.psk_mod(...)
        # 添加雜訊
        self.noise = analog.noise_source_c(...)
        # 解調
        self.demodulator = digital.psk_demod(...)
```

**功能**:
- 模擬完整的發送/接收信號鏈
- QPSK、16-QAM、64-QAM 調變
- 真實的 SNR、EbN0 計算
- 可配置的雜訊和衰落

**輸出**:
- 真實的信號處理性能指標
- BER (Bit Error Rate)、PER (Packet Error Rate)
- SNR、EbN0 測量值

**實施步驟**:
1. 安裝 GNU Radio 3.10+
2. 創建 Python flowgraph
3. 實現 QPSK/QAM 調變/解調
4. 添加通道模型（AWGN、Rayleigh）
5. 整合到現有的 API Gateway

**驗證標準**:
- [ ] 成功生成和接收測試信號
- [ ] 可以測量 BER/PER
- [ ] 可以調整 SNR 並觀察影響

---

#### 1.3 VITA 49.2 資料流模擬 ✅ 可行

**技術方案**:
```python
# 使用現有的 Python VITA 49.2 庫
import vita49

class VITA49Simulator:
    """模擬 VITA 49.2 資料流"""
    def generate_context_packet(self):
        # 生成 Context Packet
        packet = vita49.ContextPacket()
        packet.stream_id = 0x12345678
        packet.frequency = 12.5e9  # 12.5 GHz
        packet.sample_rate = 10e6  # 10 MSPS
        return packet

    def generate_data_packet(self, samples):
        # 生成 Data Packet
        packet = vita49.DataPacket()
        packet.stream_id = 0x12345678
        packet.samples = samples
        return packet
```

**功能**:
- 生成符合標準的 VITA 49.2 封包
- Context Packet（配置資訊）
- Data Packet（IQ 樣本）
- 通過 gRPC 串流傳輸

**實施步驟**:
1. 使用 GNU Radio 生成 IQ 樣本
2. 打包成 VITA 49.2 格式
3. 通過 gRPC 傳輸
4. 在接收端解析和處理

**驗證標準**:
- [ ] 成功生成 VITA 49.2 封包
- [ ] gRPC 串流正常工作
- [ ] 接收端正確解析封包

---

## 第二階段：O-RAN RIC 實現（3週）

### 目標：部署真實的 near-RT RIC 並實現 E2 介面

#### 2.1 部署 OSC near-RT RIC ✅ 可行

**技術方案**:
```bash
# 使用 O-RAN Software Community RIC
git clone "https://gerrit.o-ran-sc.org/r/ric-plt/ric-dep"
cd ric-dep

# 在 Kubernetes 部署
./install_k8s_and_helm.sh
./install -f ../RECIPE_EXAMPLE/PLATFORM/example_recipe_oran_e_release.yaml
```

**組件**:
- E2 Manager（E2 連接管理）
- Subscription Manager（訂閱管理）
- A1 Mediator（A1 介面）
- xApp Framework（xApp 運行環境）
- Conflict Mitigation（衝突處理）

**輸出**:
- 完整的 near-RT RIC 平台
- E2 和 A1 介面
- xApp 運行環境

**實施步驟**:
1. 準備 Kubernetes 集群（您已有）
2. 安裝 Helm charts
3. 部署 RIC 組件
4. 驗證所有 pod 運行正常
5. 測試 E2 連接

**驗證標準**:
- [ ] 所有 RIC 組件成功部署
- [ ] E2 Manager 可以接受連接
- [ ] A1 介面正常工作

---

#### 2.2 實現 xApp Framework ✅ 可行

**技術方案**:
```python
# 使用 OSC xApp Python SDK
from ricxappframe.xapp_frame import XappFrame

class TrafficSteeringXapp:
    """流量控制 xApp"""
    def __init__(self):
        self.xapp = XappFrame(...)
        self.xapp.register_callback(self.handle_e2_message)

    def handle_e2_message(self, summary, sbuf):
        # 處理 E2 訊息
        kpm_data = self.parse_kpm(sbuf)
        # 執行 DRL 決策
        action = self.drl_agent.predict(kpm_data)
        # 發送控制訊息
        self.send_rc_message(action)
```

**功能**:
- 接收 E2SM KPM 指標
- 執行 DRL 決策
- 發送 E2SM RC 控制訊息
- 與 RIC 框架整合

**實施步驟**:
1. 使用 xApp Python SDK
2. 實現 E2 訊息處理
3. 整合 DRL agent
4. 部署到 RIC

**驗證標準**:
- [ ] xApp 成功註冊到 RIC
- [ ] 可以接收 KPM 指標
- [ ] 可以發送控制訊息

---

## 第三階段：DRL 訓練整合（2週）

### 目標：實現真實的 PPO/SAC 訓練並整合到 xApp

#### 3.1 使用 REAL Framework ✅ 最新

**技術方案**:
```python
# 基於 2025 年 2 月發布的 REAL framework
# 論文：arXiv:2502.00715

from stable_baselines3 import PPO
from gymnasium import Env

class ORANEnv(Env):
    """O-RAN Gymnasium 環境"""
    def __init__(self, ns3_connector):
        self.ns3 = ns3_connector
        self.observation_space = ...
        self.action_space = ...

    def step(self, action):
        # 發送控制到 ns-3/RIC
        self.ns3.send_control(action)
        # 獲取新的觀察
        obs = self.ns3.get_kpm()
        # 計算獎勵
        reward = self.compute_reward(obs)
        return obs, reward, done, info

# 訓練 PPO agent
env = ORANEnv(...)
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100000)
```

**功能**:
- 真實的 ns-3 環境互動
- PPO 和 SAC 訓練
- 線上和離線學習
- 模型保存和載入

**輸出**:
- 訓練好的 DRL 模型
- 訓練曲線和性能指標
- 可部署到 xApp 的模型

**實施步驟**:
1. 創建 Gymnasium 環境（連接到 ns-3）
2. 實現獎勵函數
3. 訓練 PPO agent
4. 訓練 SAC agent
5. 比較性能
6. 整合到 xApp

**驗證標準**:
- [ ] PPO 訓練成功收斂
- [ ] SAC 訓練成功收斂
- [ ] 模型可以部署到 xApp
- [ ] 在模擬中提升網路性能

---

## 第四階段：Kubernetes 編排（1週）

### 目標：完整的雲原生部署

#### 4.1 Kubernetes 部署清單 ✅ 可行

**技術方案**:
```yaml
# sdr-platform-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdr-api-gateway
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api-gateway
        image: sdr-platform/api-gateway:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**組件**:
- API Gateway (FastAPI)
- gRPC Server
- DRL Trainer
- RIC xApps
- Monitoring (Prometheus + Grafana)
- Logging (ELK Stack)

**實施步驟**:
1. 創建 Docker 映像檔
2. 編寫 Kubernetes manifests
3. 配置 Service、Ingress
4. 部署到集群
5. 配置監控和日誌

**驗證標準**:
- [ ] 所有服務成功部署
- [ ] 健康檢查正常
- [ ] 服務間通訊正常
- [ ] 監控儀表板運行

---

## 第五階段：性能測試和驗證（2週）

### 目標：獲得真實的性能指標

#### 5.1 性能測試計劃

**延遲測試**:
```python
# 測試 API 回應時間
import time
import requests

def test_api_latency():
    latencies = []
    for i in range(1000):
        start = time.time()
        response = requests.get("http://api-gateway/api/v1/stations")
        latency = time.time() - start
        latencies.append(latency * 1000)  # ms

    print(f"Mean latency: {np.mean(latencies):.2f} ms")
    print(f"P95 latency: {np.percentile(latencies, 95):.2f} ms")
    print(f"P99 latency: {np.percentile(latencies, 99):.2f} ms")
```

**吞吐量測試**:
```bash
# 使用 wrk 進行負載測試
wrk -t12 -c400 -d30s http://api-gateway/api/v1/stations
```

**ns-3 模擬性能**:
```python
# 從 ns-3 獲取網路性能
def measure_network_performance():
    # 運行 ns-3 場景
    ns3_results = run_ns3_simulation({
        'num_ues': 100,
        'traffic_model': 'ftp',
        'duration': 60  # seconds
    })

    print(f"Average throughput: {ns3_results['throughput']:.2f} Mbps")
    print(f"Average latency: {ns3_results['latency']:.2f} ms")
    print(f"Packet loss rate: {ns3_results['plr']:.4f}")
```

**DRL 性能**:
```python
# 測試 DRL agent 的性能提升
def evaluate_drl_performance():
    # 基準（無 DRL）
    baseline = run_simulation(use_drl=False)
    # 使用 DRL
    with_drl = run_simulation(use_drl=True)

    improvement = {
        'throughput': (with_drl['thr'] - baseline['thr']) / baseline['thr'] * 100,
        'latency': (baseline['lat'] - with_drl['lat']) / baseline['lat'] * 100,
    }

    print(f"Throughput improvement: {improvement['throughput']:.1f}%")
    print(f"Latency improvement: {improvement['latency']:.1f}%")
```

**目標指標**:
- API 延遲 < 50ms (P95)
- 系統吞吐量 > 100 Mbps（模擬）
- DRL 性能提升 > 15%
- 封包遺失率 < 1%

**驗證標準**:
- [ ] 所有性能測試完成
- [ ] 指標符合或接近目標
- [ ] 有完整的測試報告

---

## 第六階段：文檔和展示（1週）

### 目標：完整的文檔和演示

#### 6.1 技術文檔

**內容**:
1. 架構圖（更新為實際實現）
2. 部署指南（詳細步驟）
3. API 文檔（完整的 OpenAPI）
4. 配置指南
5. 故障排除
6. 性能基準測試報告

#### 6.2 演示場景

**場景 1：端到端流程**:
1. 部署 Kubernetes 集群
2. 啟動 ns-3 模擬
3. RIC 連接到 ns-3
4. xApp 接收 KPM 並執行控制
5. 觀察性能提升

**場景 2：DRL 訓練**:
1. 啟動 DRL 訓練環境
2. 觀察訓練過程
3. 部署訓練好的模型
4. 比較性能

**場景 3：API 使用**:
1. 通過 API 創建站點
2. 啟動信號處理
3. 查詢狀態和指標
4. 更新配置

---

## 成果對比

### 原始聲稱 vs 新實現

| 項目 | 原始聲稱 | 之前實際 | 新實現（使用模擬） |
|-----|---------|---------|----------------|
| **完成度** | 100% | 60-65% | 95% ✅ |
| **SDR 硬體** | USRP X310 | 無（$23.5K） | ns-3 + GNU Radio ✅ |
| **O-RAN RIC** | 自行實現 | 50% | OSC RIC（真實） ✅ |
| **E2 介面** | 已實現 | 未實現 | ns-O-RAN（真實） ✅ |
| **DRL 訓練** | PPO/SAC | 85% | REAL框架（真實） ✅ |
| **xApp** | 已實現 | 60% | OSC SDK（真實） ✅ |
| **性能測試** | 已驗證 | 0%（理論值） | 完整測試（模擬） ✅ |
| **K8s 部署** | 已部署 | 30%（配置） | 完整部署 ✅ |
| **測試覆蓋** | 驗證通過 | <5% | 60%+ ✅ |
| **API 延遲** | <1ms | 未測量 | <50ms（實測） ✅ |
| **吞吐量** | >10 Gbps | 未測量 | >100 Mbps（模擬） ⚠️ |
| **成本** | $100K | $380K | $0（開源） ✅ |

**注意**:
- ✅ 完全達成或接近
- ⚠️ 部分達成（模擬值低於理論值）
- ❌ 未達成

---

## 時間表和資源

### 全職開發時間表（3-4 個月）

**月份 1**:
- 週 1-2: 階段 1（硬體模擬）
- 週 3-5: 階段 2（RIC 實現）

**月份 2**:
- 週 1-2: 階段 3（DRL 整合）
- 週 3: 階段 4（K8s 編排）
- 週 4: 階段 5 開始（性能測試）

**月份 3**:
- 週 1: 階段 5 完成
- 週 2: 階段 6（文檔）
- 週 3-4: 整合測試和優化

**月份 4**:
- 週 1-2: 最終測試和修復
- 週 3: 文檔和演示準備
- 週 4: 最終交付

### 兼職開發時間表（6-8 個月）

按照上述時間表的 2倍時間執行。

---

## 風險和挑戰

### 技術風險

1. **ns-3 性能限制** (中)
   - 模擬可能無法達到 10 Gbps 吞吐量
   - 緩解：使用合理的目標（100 Mbps+）

2. **OSC RIC 複雜度** (高)
   - RIC 部署和配置可能複雜
   - 緩解：使用官方文檔和社群支援

3. **DRL 訓練時間** (中)
   - 訓練可能需要長時間
   - 緩解：使用預訓練模型或遷移學習

4. **整合問題** (中)
   - 多個系統整合可能有相容性問題
   - 緩解：逐步整合和測試

### 資源需求

**硬體**:
- 開發機器：16GB+ RAM, 8+ CPU cores
- Kubernetes 集群：3 nodes, 32GB+ RAM total
- （您已有）✅

**軟體**:
- 全部開源，無需授權費用 ✅

**人力**:
- 1 名全職開發人員，3-4 個月
- 或 1 名兼職開發人員，6-8 個月

---

## 最終評估

### 能否達到原始聲稱？

**完全符合** (100%): ❌ 不可能
- 原因：沒有真實 USRP 硬體
- 原因：模擬無法達到 10 Gbps 吞吐量

**接近符合** (95%): ✅ 可能
- 使用模擬替代真實硬體
- 所有軟體組件完整實現
- 真實的 RIC 和 xApp
- 完整的測試和文檔

**誠實定位**: ✅ 建議
- 名稱：「SDR-O-RAN 平台（模擬驗證版）」
- 描述：「完整實現所有軟體組件，使用 ns-3 和 GNU Radio 進行模擬驗證」
- 狀態：「95% 完成，可用於研究和開發，需要真實硬體才能投入生產」

### 建議的 README 更新

**標題**:
```markdown
# SDR-O-RAN 智慧平台（模擬驗證版）

**專案類型**: 完整實現的研究平台（使用模擬）
**狀態**: 🚀 95% 完成（可用於研究和開發）
**硬體需求**: 無（使用 ns-3 和 GNU Radio 模擬）
**部署平台**: Kubernetes
```

**關鍵特性**:
- ✅ 完整的 O-RAN near-RT RIC（OSC）
- ✅ 真實的 E2 介面（ns-O-RAN）
- ✅ 5G NR 網路模擬（ns-3 + 5G-LENA）
- ✅ SDR 信號處理模擬（GNU Radio）
- ✅ DRL 訓練和部署（PPO/SAC）
- ✅ 完整的 Kubernetes 部署
- ✅ 後量子密碼學（ML-KEM + ML-DSA）
- ⚠️ 性能指標基於模擬（非真實硬體）

**適用場景**:
- 學術研究和論文
- O-RAN 技術探索
- DRL 算法開發和測試
- 系統架構驗證
- 教育和培訓

**不適用場景**:
- 生產環境部署（需要真實硬體）
- 商業營運（需要認證和測試）
- 關鍵任務應用（需要硬體保證）

---

## 下一步行動

### 立即可做（本週）

1. **確認環境** ✅
   - 驗證 Kubernetes 集群可用
   - 驗證 Docker 可用
   - 檢查系統資源

2. **安裝基礎工具**
   ```bash
   # ns-3
   git clone https://gitlab.com/nsnam/ns-3-dev.git
   cd ns-3-dev && ./ns3 configure --enable-examples --enable-tests

   # GNU Radio
   sudo apt-get install gnuradio

   # OSC RIC（需要 K8s）
   git clone "https://gerrit.o-ran-sc.org/r/ric-plt/ric-dep"
   ```

3. **運行第一個測試**
   - ns-3 基本場景
   - GNU Radio 信號生成
   - API Gateway 測試（已完成）✅

### 本月目標

- 完成階段 1（硬體模擬）
- 開始階段 2（RIC 部署）

### 3個月目標

- 完成所有 6 個階段
- 獲得 95% 完成度
- 發布更新的 README

---

**路線圖創建日期**: 2025-11-10
**預期完成日期**: 2025-02-10（3 個月）或 2025-05-10（6 個月兼職）
**下次更新**: 完成階段 1 後
