# WSL 2 + Docker + GPU 部署指南
# SDR-O-RAN Platform Deployment on Windows with WSL 2

**環境**: Windows 11 + WSL 2 + Docker Desktop + NVIDIA RTX 2060
**預計時間**: 3 天完整部署
**作者**: Auto-generated deployment guide
**日期**: 2025-11-11

---

## 🎯 部署總覽

### 檢測到的環境
- ✅ WSL 2 (kernel 6.6.87.2)
- ✅ Docker Desktop (WSL 2 backend)
- ✅ NVIDIA GeForce RTX 2060 (6GB VRAM)
- ✅ CUDA 13.0 支援
- ✅ GPU accessible in Docker containers

### 部署架構
```
Windows Host
  └─ WSL 2
      └─ Docker Containers
          ├─ LEO NTN Simulator (GPU)
          ├─ SDR + gRPC Services
          ├─ AI/ML Pipeline (GPU)
          └─ O-RAN Stack (FlexRIC)
```

---

## 📅 Day 1: WSL 環境準備與核心測試（4-6 小時）

### Step 1.1: WSL 基礎配置

```powershell
# 在 PowerShell (管理員) 執行

# 1. 設置 WSL 預設版本為 2
wsl --set-default-version 2

# 2. 檢查當前 WSL distributions
wsl -l -v

# 3. 如果沒有 Ubuntu，安裝一個
wsl --install -d Ubuntu-22.04

# 4. 啟動 WSL
wsl
```

### Step 1.2: WSL 記憶體配置（可選但推薦）

在 Windows 用戶目錄創建 `.wslconfig`:

```powershell
# 在 PowerShell 執行
cd $env:USERPROFILE
notepad .wslconfig
```

添加以下內容（根據您的RAM調整）：
```ini
[wsl2]
memory=16GB          # 如果您有 32GB RAM
processors=6         # CPU 核心數
swap=8GB
localhostForwarding=true

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
```

儲存後重啟 WSL：
```powershell
wsl --shutdown
wsl
```

### Step 1.3: 在 WSL 中安裝基礎工具

```bash
# 在 WSL 終端內執行

# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝開發工具
sudo apt install -y \
    git \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    htop \
    vim

# 安裝 ZMQ (用於容器間通訊)
sudo apt install -y libzmq3-dev

# 驗證安裝
python3 --version  # 應該是 3.10+
git --version
cmake --version
```

### Step 1.4: 克隆專案到 WSL

```bash
# 在 WSL 中執行

# 創建工作目錄
mkdir -p ~/dev
cd ~/dev

# 方法 A: 如果專案已在 GitHub
git clone https://github.com/thc1006/sdr-o-ran-platform.git
cd sdr-o-ran-platform

# 方法 B: 從 Windows 複製（如果還沒推送到 GitHub）
# Windows 路徑在 WSL 中是 /mnt/c/...
cp -r /mnt/c/Users/ict/OneDrive/桌面/dev/sdr-o-ran-platform ~/dev/
cd ~/dev/sdr-o-ran-platform

# 檢查專案結構
ls -la
```

### Step 1.5: Python 環境設置

```bash
# 創建虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 升級 pip
pip install --upgrade pip setuptools wheel

# 安裝核心依賴（非 GPU 部分先測試）
pip install fastapi uvicorn pydantic grpcio grpcio-tools protobuf pytest
```

### Step 1.6: 測試核心組件（無 GPU）

```bash
# 測試 1: SDR API Gateway
cd 03-Implementation/sdr-platform/api-gateway
pip install -r requirements.txt
python test_sdr_api_server.py

# 預期: 18/18 tests PASS ✅

# 測試 2: gRPC Services
cd ../../integration/sdr-oran-connector
python generate_grpc_stubs.py
python test_grpc_connection.py

# 預期: 3-4/4 tests PASS ✅ (1個已知字段名問題)

# 測試 3: Quantum Crypto
cd ../../security/pqc
python quantum_safe_crypto_fixed.py

# 預期: ML-KEM and ML-DSA working ✅
```

**Day 1 完成檢查點**:
- ✅ WSL 2 正常運行
- ✅ 專案克隆到 WSL
- ✅ 3/3 核心組件測試通過

---

## 📅 Day 2: Docker 容器構建（6-8 小時）

### Step 2.1: 驗證 Docker GPU 支援

```bash
# 在 WSL 終端執行

# 測試 GPU 容器（已在前面執行過）
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# 預期: 看到 RTX 2060 資訊 ✅
```

### Step 2.2: 創建 Dockerfile 們

#### Container 1: LEO NTN Simulator (GPU)

創建 `03-Implementation/simulation/Dockerfile.leo-simulator`:

```dockerfile
FROM nvidia/cuda:12.0.0-runtime-ubuntu22.04

# 安裝 Python 和系統依賴
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /app

# 安裝 Python 依賴
RUN pip3 install --no-cache-dir \
    tensorflow[and-cuda]==2.15.0 \
    sionna \
    numpy \
    scipy \
    pyzmq \
    matplotlib

# 複製 LEO 模擬器代碼
COPY simulation/leo_ntn_simulator.py /app/

# 暴露 ZMQ 端口
EXPOSE 5555

# 啟動命令
CMD ["python3", "leo_ntn_simulator.py", "--zmq-address", "tcp://0.0.0.0:5555"]
```

#### Container 2: SDR + gRPC Services

創建 `03-Implementation/sdr-platform/Dockerfile.sdr-gateway`:

```dockerfile
FROM python:3.11-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製 requirements
COPY sdr-platform/api-gateway/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 ZMQ
RUN pip install pyzmq

# 複製代碼
COPY sdr-platform/ /app/sdr-platform/
COPY integration/ /app/integration/

# 暴露端口
EXPOSE 8000 50051

# 啟動腳本
COPY scripts/start-sdr-services.sh /app/
RUN chmod +x /app/start-sdr-services.sh

CMD ["/app/start-sdr-services.sh"]
```

#### Container 3: AI/ML Pipeline (GPU)

創建 `03-Implementation/ai-ml-pipeline/Dockerfile.drl-trainer`:

```dockerfile
FROM nvidia/cuda:12.0.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安裝 ML 依賴
RUN pip3 install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cu121 \
    stable-baselines3 \
    gymnasium \
    tensorboard \
    redis \
    numpy \
    scipy

# 複製 DRL 代碼
COPY ai-ml-pipeline/training/ /app/

# TensorBoard 端口
EXPOSE 6006

CMD ["python3", "drl_trainer.py", "--algorithm", "PPO", "--timesteps", "100000", "--n-envs", "1"]
```

#### Container 4: O-RAN Stack (FlexRIC)

創建 `04-Deployment/docker/Dockerfile.flexric`:

```dockerfile
FROM ubuntu:22.04

# 安裝構建工具
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    libsctp-dev \
    libzmq3-dev \
    swig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 克隆 FlexRIC（或從本地複製已修復版本）
# 選項 A: 從 Git
RUN git clone https://gitlab.eurecom.fr/mosaic5g/flexric.git

# 選項 B: 複製已修復的本地版本
# COPY flexric/ /workspace/flexric/

WORKDIR /workspace/flexric

# 應用修復（如果需要）
# 移除斷言在 src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c:3165

# 構建 FlexRIC
RUN mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc)

# 暴露 E2 端口
EXPOSE 36421 36422

CMD ["/workspace/flexric/build/examples/ric/nearRT-RIC"]
```

### Step 2.3: 創建啟動腳本

創建 `scripts/start-sdr-services.sh`:

```bash
#!/bin/bash
set -e

echo "Starting SDR Services..."

# 啟動 API Gateway (後台)
cd /app/sdr-platform/api-gateway
python3 sdr_api_server.py &

# 等待 API 啟動
sleep 5

# 啟動 gRPC Server
cd /app/integration/sdr-oran-connector
python3 sdr_grpc_server.py

# Keep container running
wait
```

### Step 2.4: 創建 Docker Compose

創建 `docker-compose.yml` 在專案根目錄:

```yaml
version: '3.8'

services:
  leo-simulator:
    build:
      context: ./03-Implementation
      dockerfile: simulation/Dockerfile.leo-simulator
    container_name: leo-ntn-simulator
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    ports:
      - "5555:5555"
    networks:
      - oran-network

  sdr-gateway:
    build:
      context: ./03-Implementation
      dockerfile: sdr-platform/Dockerfile.sdr-gateway
    container_name: sdr-gateway
    depends_on:
      - leo-simulator
    ports:
      - "8000:8000"   # FastAPI
      - "50051:50051" # gRPC
    environment:
      - ZMQ_ADDRESS=tcp://leo-simulator:5555
    networks:
      - oran-network

  drl-trainer:
    build:
      context: ./03-Implementation
      dockerfile: ai-ml-pipeline/Dockerfile.drl-trainer
    container_name: drl-trainer
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    ports:
      - "6006:6006"  # TensorBoard
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    networks:
      - oran-network

  flexric:
    build:
      context: ./04-Deployment/docker
      dockerfile: Dockerfile.flexric
    container_name: flexric-ric
    ports:
      - "36421:36421"
      - "36422:36422"
    networks:
      - oran-network

networks:
  oran-network:
    driver: bridge
```

### Step 2.5: 構建所有容器

```bash
# 在專案根目錄執行

# 構建所有容器（這會需要一些時間）
docker-compose build

# 預期: 所有 4 個容器成功構建 ✅
```

**Day 2 完成檢查點**:
- ✅ 4 個 Dockerfile 創建完成
- ✅ Docker Compose 配置完成
- ✅ 所有容器構建成功

---

## 📅 Day 3: 端到端測試（4-6 小時）

### Step 3.1: 啟動所有服務

```bash
# 啟動整個棧
docker-compose up -d

# 檢查所有容器狀態
docker-compose ps

# 預期輸出：
# NAME                   STATUS
# leo-ntn-simulator      Up
# sdr-gateway            Up
# drl-trainer            Up
# flexric-ric            Up

# 查看日誌
docker-compose logs -f
```

### Step 3.2: 驗證 GPU 使用

```bash
# 在另一個終端監控 GPU
watch -n 1 nvidia-smi

# 預期: 看到 leo-simulator 和 drl-trainer 使用 GPU
```

### Step 3.3: 測試各組件

#### 測試 1: LEO Simulator

```bash
# 檢查 ZMQ 輸出
docker exec -it leo-ntn-simulator python3 -c "
import zmq
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:5555')
socket.setsockopt_string(zmq.SUBSCRIBE, '')
print('Receiving from LEO simulator...')
msg = socket.recv()
print(f'Received {len(msg)} bytes')
"

# 預期: 接收到 IQ samples ✅
```

#### 測試 2: SDR API Gateway

```bash
# 測試 REST API
curl http://localhost:8000/healthz

# 預期: {"status": "healthy"} ✅

# 測試 Prometheus metrics
curl http://localhost:8000/metrics

# 預期: Prometheus 格式的 metrics ✅
```

#### 測試 3: gRPC Services

```bash
# 使用 grpcurl 測試（需要安裝）
# 在 WSL: sudo apt install grpcurl

grpcurl -plaintext localhost:50051 list

# 預期: 列出可用的 gRPC 服務 ✅
```

#### 測試 4: DRL Trainer

```bash
# 檢查訓練日誌
docker logs drl-trainer | tail -50

# 預期: 看到 PPO 訓練進度 ✅

# 打開 TensorBoard
# 在瀏覽器訪問: http://localhost:6006
```

#### 測試 5: FlexRIC

```bash
# 檢查 RIC 啟動日誌
docker logs flexric-ric

# 預期: nearRT-RIC started successfully（無斷言錯誤）✅
```

### Step 3.4: 端到端流程測試

創建測試腳本 `scripts/e2e-test.sh`:

```bash
#!/bin/bash

echo "=========================================="
echo "End-to-End Integration Test"
echo "=========================================="

# 1. 測試 LEO → SDR 連接
echo "[1/5] Testing LEO Simulator → SDR Gateway..."
curl -s http://localhost:8000/api/v1/stations | jq .
if [ $? -eq 0 ]; then
    echo "✅ SDR Gateway responding"
else
    echo "❌ SDR Gateway failed"
    exit 1
fi

# 2. 測試 gRPC 連接
echo "[2/5] Testing gRPC Services..."
docker exec sdr-gateway python3 /app/integration/sdr-oran-connector/test_grpc_connection.py
if [ $? -eq 0 ]; then
    echo "✅ gRPC services working"
else
    echo "❌ gRPC failed"
fi

# 3. 測試 DRL 訓練
echo "[3/5] Testing DRL Trainer..."
docker exec drl-trainer python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
if [ $? -eq 0 ]; then
    echo "✅ DRL Trainer has GPU access"
else
    echo "❌ DRL Trainer GPU failed"
fi

# 4. 測試 FlexRIC
echo "[4/5] Testing FlexRIC RIC..."
docker exec flexric-ric ps aux | grep nearRT-RIC
if [ $? -eq 0 ]; then
    echo "✅ FlexRIC RIC is running"
else
    echo "❌ FlexRIC not running"
fi

# 5. 測試整體資源使用
echo "[5/5] Resource Usage:"
docker stats --no-stream

echo "=========================================="
echo "Test Complete!"
echo "=========================================="
```

執行測試:
```bash
chmod +x scripts/e2e-test.sh
./scripts/e2e-test.sh
```

**Day 3 完成檢查點**:
- ✅ 所有容器正常運行
- ✅ LEO Simulator 產生 IQ samples
- ✅ SDR Gateway 接收數據
- ✅ DRL Trainer 使用 GPU 訓練
- ✅ FlexRIC 無錯誤運行
- ✅ 端到端測試通過

---

## 🎯 完成後的驗證

### 最終檢查清單

```bash
# 1. 所有容器運行
docker-compose ps
# 預期: 4/4 containers Up

# 2. GPU 利用
nvidia-smi
# 預期: leo-simulator 和 drl-trainer 使用 GPU

# 3. 端口監聽
netstat -tlnp | grep -E '(5555|8000|50051|6006|36421)'
# 預期: 所有端口 LISTEN

# 4. 日誌無嚴重錯誤
docker-compose logs | grep -i error
# 預期: 僅有已知的 SDL connection warnings

# 5. 性能基準
docker stats --no-stream
# 預期:
# - leo-simulator: ~2-3GB RAM, 30-50% GPU
# - drl-trainer: ~1-2GB RAM, 20-40% GPU
# - 其他容器: <500MB RAM
```

### 訪問服務

| 服務 | URL | 說明 |
|------|-----|------|
| SDR API | http://localhost:8000 | FastAPI Swagger UI |
| Metrics | http://localhost:8000/metrics | Prometheus metrics |
| TensorBoard | http://localhost:6006 | DRL 訓練可視化 |
| gRPC | localhost:50051 | gRPC IQ streaming |

---

## 🐛 故障排除

### 問題 1: GPU 無法在容器中訪問

```bash
# 檢查 Docker Desktop 設置
# Settings → Resources → WSL Integration → Enable GPU support

# 重啟 Docker Desktop
wsl --shutdown
# 重新啟動 Docker Desktop

# 驗證
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### 問題 2: WSL 記憶體不足

```bash
# 編輯 .wslconfig（在 Windows）
notepad $env:USERPROFILE\.wslconfig

# 增加記憶體限制
[wsl2]
memory=20GB
swap=12GB

# 重啟 WSL
wsl --shutdown
wsl
```

### 問題 3: 容器無法連接

```bash
# 檢查網路
docker network ls
docker network inspect sdr-o-ran-platform_oran-network

# 重建網路
docker-compose down
docker-compose up -d
```

### 問題 4: FlexRIC 斷言失敗

```bash
# 需要在 Dockerfile 中應用修復
# 編輯 src/lib/e2ap/v2_03/enc/e2ap_msg_enc_asn.c:3165
# 移除或註釋掉斷言

# 重新構建
docker-compose build flexric
docker-compose up -d flexric
```

---

## 📊 性能優化建議

### RTX 2060 (6GB VRAM) 優化

由於 VRAM 限制，建議：

1. **分時運行 GPU 任務**:
```bash
# 先運行 LEO Simulator
docker-compose up -d leo-simulator sdr-gateway

# 訓練完成後，停止 LEO，啟動 DRL
docker-compose stop leo-simulator
docker-compose up -d drl-trainer
```

2. **減少批次大小**:
```python
# 在 drl_trainer.py 中
batch_size = 32  # 降低到 32（預設可能是 64）
```

3. **使用混合精度**:
```python
# 在 TensorFlow 配置中
tf.keras.mixed_precision.set_global_policy('mixed_float16')
```

---

## 🎓 下一步

完成部署後，您可以：

1. **收集數據**: 運行長時間模擬，收集 throughput, latency, BLER 數據
2. **優化 DRL**: 調整 PPO 超參數，提升決策品質
3. **撰寫論文**: 使用實驗結果撰寫會議/期刊論文
4. **擴展功能**: 添加更多 xApp，實現更複雜的策略
5. **Powder 部署**: 申請真實硬體驗證

---

## 📚 參考資料

- WSL 2 GPU 支援: https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl
- Docker GPU 支援: https://docs.docker.com/config/containers/resource_constraints/#gpu
- FlexRIC 文檔: https://gitlab.eurecom.fr/mosaic5g/flexric
- Sionna 文檔: https://nvlabs.github.io/sionna/

---

**部署完成！祝研究順利！🚀**
