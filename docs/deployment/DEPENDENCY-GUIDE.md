# SDR-O-RAN Platform 依賴套件安裝指南

**版本**: 1.0.0
**最後更新**: 2025-11-17
**適用環境**: Ubuntu 22.04 / WSL2 / Linux
**Python 版本**: 3.11+ (當前系統: Python 3.12.3)

---

## 🚨 當前系統狀態

**檢測到的問題**:
```bash
✅ Python 3.12.3 已安裝: /usr/bin/python3
❌ pip 模組未安裝
❌ protobuf、grpcio 等套件無法導入
```

---

## 📦 安裝步驟

### 步驟 1：安裝 pip

```bash
# 方法 1：使用系統套件管理器（推薦）
sudo apt update
sudo apt install -y python3-pip python3-venv

# 驗證安裝
python3 -m pip --version
# 預期輸出: pip 24.x.x from ...
```

如果上述方法不可行：

```bash
# 方法 2：使用 get-pip.py（備用方案）
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
rm get-pip.py

# 添加到 PATH（添加到 ~/.bashrc）
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 驗證
python3 -m pip --version
```

---

### 步驟 2：建立虛擬環境（強烈建議）

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform

# 建立虛擬環境
python3 -m venv venv

# 啟用虛擬環境
source venv/bin/activate

# 驗證（應該看到 (venv) 前綴）
which python3
# 預期輸出: /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/python3
```

**重要**: 每次開啟新終端都需要執行 `source venv/bin/activate`

---

### 步驟 3：安裝核心依賴套件

#### 3.1 gRPC 和 Protobuf

```bash
# 確保在虛擬環境中（看到 (venv) 前綴）
pip install --upgrade pip setuptools wheel

# 安裝 gRPC 相關套件
pip install grpcio==1.60.0 grpcio-tools==1.60.0 protobuf==4.25.2

# 驗證安裝
python3 -c "import grpc; print('✅ grpcio:', grpc.__version__)"
python3 -c "import google.protobuf; print('✅ protobuf:', google.protobuf.__version__)"
```

#### 3.2 FastAPI 和 Web 框架

```bash
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 pydantic==2.5.0

# 驗證
python3 -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
```

#### 3.3 認證與安全

```bash
pip install python-jose[cryptography]==3.3.0 passlib[argon2]==1.7.4 \
            argon2-cffi==23.1.0 python-multipart==0.0.6

# 驗證
python3 -c "from passlib.hash import argon2; print('✅ Argon2 available')"
```

#### 3.4 監控與可觀測性

```bash
pip install prometheus-client==0.19.0 \
            opentelemetry-api==1.22.0 \
            opentelemetry-sdk==1.22.0 \
            opentelemetry-instrumentation-fastapi==0.43b0

# 驗證
python3 -c "from prometheus_client import Counter; print('✅ Prometheus client available')"
```

#### 3.5 ZMQ 和 NumPy

```bash
pip install pyzmq==25.1.2 numpy==1.24.3

# 驗證
python3 -c "import zmq; print('✅ ZMQ:', zmq.zmq_version())"
python3 -c "import numpy as np; print('✅ NumPy:', np.__version__)"
```

#### 3.6 AI/ML 套件（可選，用於 DRL Trainer）

```bash
# 基礎 ML 套件
pip install torch torchvision  # PyTorch（較大，需要時間）
pip install stable-baselines3 gymnasium

# Redis 客戶端（用於 SDL）
pip install redis

# 驗證
python3 -c "import torch; print('✅ PyTorch:', torch.__version__)"
python3 -c "from stable_baselines3 import PPO; print('✅ Stable-Baselines3 available')"
```

#### 3.7 後量子密碼學（可選）

```bash
pip install pqcrypto

# 驗證
python3 -c "from pqcrypto.kem.kyber1024 import generate_keypair; print('✅ PQCrypto available')"
```

---

### 步驟 4：從 requirements.txt 安裝（整合安裝）

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform

# 安裝 API Gateway 依賴
cd 03-Implementation/sdr-platform/api-gateway
pip install -r requirements.txt

# 回到根目錄
cd ../../..

# 驗證所有導入
python3 << EOF
import grpc
import fastapi
import zmq
import numpy as np
from google.protobuf import descriptor
print("✅ 所有核心依賴套件已成功安裝")
EOF
```

---

### 步驟 5：測試 gRPC Stubs 導入

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector

# 測試導入
python3 -c "import sdr_oran_pb2, sdr_oran_pb2_grpc; print('✅ gRPC stubs 導入成功')"
```

**預期輸出**: `✅ gRPC stubs 導入成功`

如果失敗，重新生成 stubs：

```bash
python3 -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/sdr_oran.proto
```

---

## 🔧 完整安裝腳本（一鍵安裝）

建立並執行以下腳本：

```bash
cat > /home/gnb/thc1006/sdr-o-ran-platform/install-dependencies.sh << 'EOF'
#!/bin/bash
# SDR-O-RAN Platform 依賴套件自動安裝腳本
# 版本: 1.0.0
# 日期: 2025-11-17

set -e  # 遇到錯誤立即退出

echo "🚀 SDR-O-RAN Platform 依賴套件安裝"
echo "=================================="

# 檢查 Python 版本
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"

# 安裝 pip（如果未安裝）
if ! python3 -m pip --version &> /dev/null; then
    echo "📦 安裝 pip..."
    sudo apt update
    sudo apt install -y python3-pip python3-venv
fi

# 建立虛擬環境
if [ ! -d "venv" ]; then
    echo "🔧 建立虛擬環境..."
    python3 -m venv venv
fi

# 啟用虛擬環境
source venv/bin/activate

# 升級 pip
echo "⬆️  升級 pip..."
pip install --upgrade pip setuptools wheel

# 安裝核心依賴
echo "📦 安裝核心依賴套件..."
pip install grpcio==1.60.0 grpcio-tools==1.60.0 protobuf==4.25.2
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 pydantic==2.5.0
pip install python-jose[cryptography]==3.3.0 passlib[argon2]==1.7.4
pip install pyzmq==25.1.2 numpy==1.24.3
pip install prometheus-client==0.19.0
pip install redis

# 安裝 API Gateway 依賴
echo "📦 安裝 API Gateway 依賴..."
cd 03-Implementation/sdr-platform/api-gateway
pip install -r requirements.txt
cd ../../..

# 驗證安裝
echo ""
echo "🔍 驗證安裝..."
python3 << VERIFY
import grpc
import fastapi
import zmq
import numpy as np
from google.protobuf import descriptor
print("✅ 所有核心依賴套件已成功安裝")
VERIFY

# 生成 gRPC stubs
echo ""
echo "🔧 生成 gRPC Protobuf stubs..."
cd 03-Implementation/integration/sdr-oran-connector
python3 -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/sdr_oran.proto
cd ../../..

# 驗證 gRPC stubs
echo ""
echo "🔍 驗證 gRPC stubs..."
cd 03-Implementation/integration/sdr-oran-connector
python3 -c "import sdr_oran_pb2, sdr_oran_pb2_grpc; print('✅ gRPC stubs 導入成功')"
cd ../../..

echo ""
echo "✅ 安裝完成！"
echo ""
echo "使用方法:"
echo "  1. 每次開啟新終端時執行: source venv/bin/activate"
echo "  2. 啟動 gRPC 伺服器: cd 03-Implementation/integration/sdr-oran-connector && python3 sdr_grpc_server.py"
echo ""
EOF

# 賦予執行權限
chmod +x /home/gnb/thc1006/sdr-o-ran-platform/install-dependencies.sh

# 執行安裝
/home/gnb/thc1006/sdr-o-ran-platform/install-dependencies.sh
```

---

## 🐛 常見問題排解

### 問題 1：ModuleNotFoundError: No module named 'google'

**原因**: protobuf 套件未安裝

**解決方案**:
```bash
pip install protobuf==4.25.2
```

### 問題 2：Permission denied 錯誤

**原因**: 嘗試全域安裝但沒有 sudo 權限

**解決方案 1**: 使用虛擬環境（推薦）
```bash
python3 -m venv venv
source venv/bin/activate
pip install <package>
```

**解決方案 2**: 使用 --user 標誌
```bash
pip install --user <package>
```

### 問題 3：pip 指令找不到

**原因**: pip 未安裝或不在 PATH 中

**解決方案**:
```bash
sudo apt install python3-pip
# 或
python3 -m pip install --user <package>
```

### 問題 4：Pickle 錯誤（DRL Trainer）

**原因**: 使用 Windows 或預設的 'spawn' start_method

**解決方案**: 已在程式碼中修復（使用 `start_method='fork'`）

---

## 📊 驗證安裝完整性

執行以下命令檢查所有依賴：

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform

python3 << 'VERIFY'
import sys

def check_module(module_name, import_name=None):
    if import_name is None:
        import_name = module_name
    try:
        exec(f"import {import_name}")
        print(f"✅ {module_name}")
    except ImportError:
        print(f"❌ {module_name} - MISSING")

print("🔍 檢查依賴套件...")
print("=" * 40)

# 核心套件
check_module("grpc", "grpc")
check_module("protobuf", "google.protobuf")
check_module("fastapi", "fastapi")
check_module("uvicorn", "uvicorn")
check_module("pydantic", "pydantic")

# 認證與安全
check_module("python-jose", "jose")
check_module("passlib", "passlib")
check_module("argon2-cffi", "argon2")

# 數據處理
check_module("numpy", "numpy")
check_module("pyzmq", "zmq")

# 監控
check_module("prometheus-client", "prometheus_client")
check_module("opentelemetry-api", "opentelemetry")

# 資料庫
check_module("redis", "redis")

# AI/ML（可選）
print("\n📦 可選套件:")
check_module("torch", "torch")
check_module("stable-baselines3", "stable_baselines3")
check_module("gymnasium", "gymnasium")

# PQC（可選）
check_module("pqcrypto", "pqcrypto.kem.kyber1024")

print("\n" + "=" * 40)
print("檢查完成！")
VERIFY
```

---

## 🚀 下一步

安裝完成後，您可以：

1. **測試 gRPC 服務**:
   ```bash
   cd 03-Implementation/integration/sdr-oran-connector
   python3 test_grpc_connection.py
   ```

2. **啟動 API Gateway**:
   ```bash
   cd 03-Implementation/sdr-platform/api-gateway
   python3 sdr_api_server.py
   ```

3. **運行 DRL Trainer**:
   ```bash
   cd 03-Implementation/ai-ml-pipeline/training
   python3 drl_trainer.py --algorithm PPO --timesteps 10000
   ```

---

**維護者**: SDR-O-RAN Platform Team
**支援**: thc1006@ieee.org
**最後更新**: 2025-11-17
