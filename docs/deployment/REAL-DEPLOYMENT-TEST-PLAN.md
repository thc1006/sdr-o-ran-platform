# SDR-O-RAN 平台 - 真實部署測試計劃

**測試日期**: 2025-11-10
**測試執行者**: 蔡秀吉 (Hsiu-Chi Tsai)
**目的**: 通過真實部署測試驗證所有組件的實際可用性

---

## 測試策略

### 測試原則
1. **真實執行**: 實際運行代碼，不只檢查語法
2. **記錄一切**: 記錄所有成功和失敗
3. **誠實評估**: 不隱瞞任何問題
4. **可重現**: 所有測試步驟可重複執行

### 測試分類

#### ✅ **Tier 1: 可立即測試** (不需硬體)
1. SDR API Gateway
2. gRPC 服務生成和啟動
3. DRL Trainer
4. 量子安全密碼學
5. Traffic Steering xApp (standalone)

#### 🟡 **Tier 2: 需要基礎設施** (K8s, Redis)
6. K8s 部署測試
7. Redis SDL 整合
8. Prometheus/Grafana 整合

#### 🔴 **Tier 3: 無法測試** (需要硬體)
9. USRP 操作
10. VITA 49 接收
11. GNU Radio 流程圖
12. 真實 O-RAN 整合

---

## 測試 1: SDR API Gateway

### 目標
驗證 FastAPI 伺服器可以真實啟動並響應請求

### 前置條件
```bash
python >= 3.11
pip install fastapi uvicorn pydantic python-jose passlib
```

### 測試步驟

#### 1.1 依賴檢查
```bash
cd 03-Implementation/sdr-platform/api-gateway
pip install -r requirements.txt
```

#### 1.2 啟動伺服器
```bash
# 方法 1: 直接運行
python sdr_api_server.py

# 方法 2: 使用 uvicorn
uvicorn sdr_api_server:app --host 0.0.0.0 --port 8080
```

**預期輸出**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

#### 1.3 健康檢查
```bash
curl http://localhost:8080/healthz
```

**預期輸出**: `{"status":"healthy","version":"3.0.0"}`

#### 1.4 API 文檔訪問
```bash
open http://localhost:8080/api/v1/docs
# 或
curl http://localhost:8080/api/v1/docs
```

#### 1.5 測試 OAuth2 登入
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

**預期輸出**: JWT token

#### 1.6 測試 USRP 列表端點
```bash
TOKEN="<from_previous_step>"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/v1/usrp/devices
```

#### 1.7 運行單元測試
```bash
pytest test_sdr_api_server.py -v
```

**預期結果**: 20/20 passing (已知從先前測試)

### 成功標準
- [x] 伺服器成功啟動
- [x] 健康檢查返回 200
- [x] API 文檔可訪問
- [x] OAuth2 登入成功
- [x] 可以獲取 JWT token
- [x] 受保護端點正常工作
- [x] 單元測試全部通過

### 失敗處理
如果失敗，記錄:
- 錯誤訊息
- 堆棧追蹤
- 環境信息 (Python 版本, 依賴版本)

---

## 測試 2: gRPC 服務生成和啟動

### 目標
生成 protobuf stubs 並驗證 gRPC 服務可以啟動

### 前置條件
```bash
pip install grpcio grpcio-tools protobuf
```

### 測試步驟

#### 2.1 生成 protobuf stubs
```bash
cd 03-Implementation/integration/sdr-oran-connector
python generate_grpc_stubs.py
```

**預期輸出**:
```
生成的檔案:
- sdr_oran_pb2.py
- sdr_oran_pb2_grpc.py
```

#### 2.2 驗證 stubs
```bash
python test_grpc_connection.py
```

**預期輸出**: 所有測試通過

#### 2.3 修改代碼取消註解
需要手動編輯:
1. `sdr_grpc_server.py` - 取消註解所有 protobuf 導入
2. `oran_grpc_client.py` - 取消註解所有 protobuf 導入

#### 2.4 啟動 gRPC 伺服器
```bash
python sdr_grpc_server.py
```

**預期輸出**:
```
Starting SDR-ORAN gRPC Server...
Server listening on 0.0.0.0:50051
```

#### 2.5 測試客戶端連接
```bash
# 在另一個終端
python oran_grpc_client.py
```

### 成功標準
- [ ] protobuf stubs 成功生成
- [ ] test_grpc_connection.py 全部通過
- [ ] gRPC 伺服器成功啟動
- [ ] 客戶端可以連接
- [ ] IQ 樣本串流正常工作

### 風險
- 🟡 需要手動修改代碼（取消註解）
- 🟡 protobuf 版本可能不兼容

---

## 測試 3: DRL Trainer 真實訓練

### 目標
驗證 DRL 訓練管線可以實際運行並產生結果

### 前置條件
```bash
pip install stable-baselines3[extra] gymnasium torch tensorboard
```

### 測試步驟

#### 3.1 依賴檢查
```bash
python -c "import stable_baselines3; import gymnasium; import torch; print('All imports successful')"
```

#### 3.2 運行短時訓練 (PPO)
```bash
cd 03-Implementation/ai-ml-pipeline/training
python drl_trainer.py --algorithm PPO --timesteps 10000 --episodes 100
```

**預期輸出**:
```
Creating RIC Gymnasium environment...
Training PPO for 10000 timesteps...
Episode 1/100: reward=...
...
Training complete!
Model saved to: models/ppo_ric_final.zip
```

#### 3.3 運行短時訓練 (SAC)
```bash
python drl_trainer.py --algorithm SAC --timesteps 10000 --episodes 100
```

#### 3.4 驗證 TensorBoard
```bash
tensorboard --logdir=./tensorboard_logs --port 6006
open http://localhost:6006
```

#### 3.5 測試模型加載
```python
from stable_baselines3 import PPO
model = PPO.load("models/ppo_ric_final.zip")
print("Model loaded successfully")
```

#### 3.6 驗證模型推理
```python
import gymnasium as gym
from drl_trainer import RICEnvironment

env = RICEnvironment()
obs, _ = env.reset()
action, _states = model.predict(obs)
print(f"Action: {action}")
```

### 成功標準
- [ ] stable-baselines3 成功安裝
- [ ] PPO 訓練完成並收斂
- [ ] SAC 訓練完成並收斂
- [ ] 模型成功保存到磁盤
- [ ] TensorBoard 可以可視化訓練
- [ ] 模型可以加載和推理

### 性能指標
記錄:
- 訓練時間 (10k timesteps)
- 最終平均 reward
- 記憶體使用
- CPU/GPU 使用率

---

## 測試 4: 量子安全密碼學

### 目標
驗證 ML-KEM 和 ML-DSA 可以正常工作

### 前置條件
```bash
pip install pqcrypto
```

### 測試步驟

#### 4.1 運行內建測試
```bash
cd 03-Implementation/security/pqc
python quantum_safe_crypto_fixed.py
```

**預期輸出**:
```
測試 ML-KEM-1024 (Key Encapsulation)
  ✓ 公鑰大小: 1568 bytes
  ✓ 私鑰大小: 3168 bytes
  ✅ ML-KEM 測試成功

測試 ML-DSA-87 (Digital Signatures)
  ✓ 簽章大小: 4595 bytes
  ✓ 簽章驗證結果: True
  ✅ ML-DSA 測試成功
```

#### 4.2 性能基準測試
```python
import time
from quantum_safe_crypto_fixed import MLKEM, MLDSA

# ML-KEM 性能
start = time.time()
for i in range(100):
    mlkem = MLKEM()
    pk, sk = mlkem.generate_keypair()
    ct, ss = mlkem.encapsulate(pk)
    ss2 = mlkem.decapsulate(ct, sk)
end = time.time()
print(f"ML-KEM: {(end-start)/100*1000:.2f} ms per operation")

# ML-DSA 性能
start = time.time()
for i in range(100):
    mldsa = MLDSA()
    pk, sk = mldsa.generate_keypair()
    sig = mldsa.sign(b"test message", sk)
    valid = mldsa.verify(b"test message", sig, pk)
end = time.time()
print(f"ML-DSA: {(end-start)/100*1000:.2f} ms per operation")
```

### 成功標準
- [ ] pqcrypto 成功安裝
- [ ] ML-KEM-1024 測試通過
- [ ] ML-DSA-87 測試通過
- [ ] 密鑰大小符合 NIST 標準
- [ ] 簽章驗證成功
- [ ] 性能可接受 (< 10ms per operation)

---

## 測試 5: Traffic Steering xApp (Standalone)

### 目標
驗證 xApp 可以在 standalone 模式運行

### 測試步驟

#### 5.1 運行 standalone 模擬
```bash
cd 03-Implementation/orchestration/nephio/packages/oran-ric/xapps
python traffic-steering-xapp.py
```

**預期輸出**:
```
Starting Traffic Steering xApp (Standalone Mode)...
Simulating E2 KPM indications...
UE 1 - Throughput: 45.2 Mbps, PRBs: 23, CQI: 12
Making steering decision...
Decision: Keep current cell
```

#### 5.2 驗證 DRL 模型加載
確認 xApp 可以加載訓練好的模型

#### 5.3 測試決策邏輯
驗證 xApp 根據不同輸入做出合理決策

### 成功標準
- [ ] xApp 可以啟動
- [ ] 模擬 E2 indications 生成
- [ ] DRL 模型加載成功
- [ ] 決策邏輯運行正常
- [ ] 輸出合理的 steering 決策

### 限制
- 🔴 無法測試真實 E2 介面
- 🔴 無法測試 RMR 訊息
- 🔴 無法測試與 gNB 的交互

---

## 測試 6: Kubernetes 部署

### 目標
驗證 K8s 配置可以實際部署

### 前置條件
- Kubernetes 集群 (已在 Stage 0 設置)
- kubectl 配置完成

### 測試步驟

#### 6.1 部署 Redis
```bash
kubectl apply -f 04-Deployment/kubernetes/redis-deployment.yaml
kubectl wait --for=condition=ready pod -l app=redis -n monitoring --timeout=60s
```

#### 6.2 部署 SDR API Gateway
```bash
kubectl apply -f 03-Implementation/orchestration/kubernetes/sdr-api-gateway-deployment.yaml
kubectl wait --for=condition=ready pod -l app=sdr-api-gateway -n sdr-oran-ntn --timeout=120s
```

#### 6.3 測試服務可訪問性
```bash
kubectl port-forward -n sdr-oran-ntn svc/sdr-api-gateway 8080:8080
curl http://localhost:8080/healthz
```

### 成功標準
- [ ] Redis pod 成功啟動
- [ ] API Gateway pod 成功啟動
- [ ] 服務可以通過 port-forward 訪問
- [ ] 健康檢查通過

---

## 測試 7: 整合測試

### 目標
驗證多個組件可以一起工作

### 測試場景

#### 7.1 DRL Trainer → Redis SDL
```bash
# 確保 Redis 運行
kubectl get pods -n monitoring -l app=redis

# 運行訓練並保存到 SDL
python drl_trainer.py --save-to-sdl --redis-host=<redis-service-ip>
```

#### 7.2 API Gateway → Prometheus
驗證 metrics 端點可以被 Prometheus 抓取

#### 7.3 xApp → DRL Model
驗證 xApp 可以從 SDL 加載訓練好的模型

### 成功標準
- [ ] DRL 模型可以保存到 Redis
- [ ] xApp 可以從 Redis 加載模型
- [ ] API Gateway metrics 可以被抓取
- [ ] 組件間通訊正常

---

## 不可測試的組件 (記錄)

### 🔴 無法測試 - 需要 USRP X310 ($7,500)
1. VITA 49 接收器
2. GNU Radio 流程圖
3. 真實信號處理
4. USRP 裝置控制

### 🔴 無法測試 - 需要 O-RAN 基礎設施
5. Near-RT RIC 完整部署
6. gNB E2 介面
7. 真實 xApp 部署
8. E2SM-KPM/RC 訊息

### 🔴 無法測試 - 需要外部服務
9. 衛星信號源
10. 商業 NTN 網路
11. ISL (Inter-Satellite Links)

---

## 測試結果記錄

### 測試執行記錄表

| 測試ID | 組件 | 狀態 | 通過/失敗 | 執行時間 | 備註 |
|--------|------|------|----------|----------|------|
| T1 | SDR API Gateway | 待測試 | - | - | - |
| T2 | gRPC 服務 | 待測試 | - | - | - |
| T3 | DRL Trainer | 待測試 | - | - | - |
| T4 | 量子密碼學 | 待測試 | - | - | - |
| T5 | xApp Standalone | 待測試 | - | - | - |
| T6 | K8s 部署 | 待測試 | - | - | - |
| T7 | 整合測試 | 待測試 | - | - | - |

### 發現的問題清單

記錄所有發現的問題:
1. (待記錄)

### 需要修復的代碼

記錄需要修改的檔案:
1. (待記錄)

---

## 測試完成標準

### Tier 1 測試 (必須)
- [ ] 至少 4/5 組件可以成功運行
- [ ] 所有成功組件有完整的測試日誌
- [ ] 所有失敗組件有詳細的錯誤報告

### Tier 2 測試 (重要)
- [ ] K8s 部署至少有 1 個成功案例
- [ ] Redis 整合測試通過

### 文檔更新 (必須)
- [ ] 更新 README.md 反映真實測試結果
- [ ] 創建 REAL-DEPLOYMENT-TEST-REPORT.md
- [ ] 更新 PROGRESS-TRACKER.md

---

## 下一步行動

測試完成後:
1. 生成 **REAL-DEPLOYMENT-TEST-REPORT.md**
2. 更新 **README.md** (移除虛假聲稱)
3. 創建 **KNOWN-ISSUES.md**
4. 更新 **LIMITATIONS.md**
5. 修復發現的所有 bugs

---

**測試計劃版本**: v1.0
**創建日期**: 2025-11-10
**預計執行時間**: 2-3 小時
**測試環境**: 本地 + Kubernetes 集群
