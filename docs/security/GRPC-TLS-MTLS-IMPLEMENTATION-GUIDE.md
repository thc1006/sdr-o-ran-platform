# gRPC TLS/mTLS 實施指南

**文檔版本**: 1.0.0
**最後更新**: 2025-11-17
**基於標準**: 2025 年 gRPC Python 安全最佳實踐
**作者**: Claude Code Assistant

---

## 📊 2025 年最新發現

根據 2025 年 11 月的網路搜尋研究，gRPC Python TLS/mTLS 的最新狀態：

### 關鍵更新
- **mTLS TPM/OS Keystore 支援**: 截至 2025 年 7 月仍在開發中（GitHub Issue #40130）
- **目前最佳實踐**: 使用憑證檔案方式（cert/key from raw bytes）
- **建議方法**: 混合 TLS（基本加密）+ mTLS（服務間認證）

---

## 🎯 實施目標

### 階段 1：啟用基本 TLS（1-2 天）
✅ 加密客戶端-伺服器通訊
✅ 防止中間人攻擊
✅ 保護 IQ 樣本傳輸

### 階段 2：啟用 mTLS（3-5 天）
✅ 雙向身份驗證
✅ 服務間信任建立
✅ 零信任架構實現

---

## 🔒 階段 1：基本 TLS 實施

### 步驟 1.1：生成自簽證書（開發環境）

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform
mkdir -p certs

# 生成 CA 私鑰
openssl genrsa -out certs/ca.key 4096

# 生成 CA 憑證（有效期 10 年）
openssl req -new -x509 -key certs/ca.key -out certs/ca.crt -days 3650 \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=SDR-ORAN-Platform/OU=Research/CN=CA"

# 生成伺服器私鑰
openssl genrsa -out certs/server.key 4096

# 生成伺服器 CSR
openssl req -new -key certs/server.key -out certs/server.csr \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=SDR-ORAN-Platform/OU=gRPC/CN=localhost"

# 使用 CA 簽署伺服器憑證
openssl x509 -req -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -out certs/server.crt -days 365 \
  -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1")

# 設定權限
chmod 600 certs/*.key
chmod 644 certs/*.crt

echo "✅ TLS 憑證已生成於 certs/ 目錄"
```

### 步驟 1.2：修改 gRPC 伺服器啟用 TLS

**檔案**: `03-Implementation/integration/sdr-oran-connector/sdr_grpc_server.py`

在檔案末尾添加：

```python
def serve_with_tls(port: int = 50051, cert_dir: str = "../../../certs"):
    """
    Start gRPC server with TLS encryption
    Based on 2025 gRPC Python security best practices
    """
    # 讀取憑證檔案
    with open(f'{cert_dir}/server.key', 'rb') as f:
        server_key = f.read()
    with open(f'{cert_dir}/server.crt', 'rb') as f:
        server_cert = f.read()
    with open(f'{cert_dir}/ca.crt', 'rb') as f:
        ca_cert = f.read()

    # 建立 TLS 憑證
    server_credentials = grpc.ssl_server_credentials(
        [(server_key, server_cert)],
        root_certificates=ca_cert,
        require_client_auth=False  # 階段 1：不要求客戶端憑證
    )

    # 建立伺服器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 註冊服務
    service = IQStreamServicer()
    sdr_oran_pb2_grpc.add_IQStreamServiceServicer_to_server(service, server)

    # 綁定 TLS 端口
    server.add_secure_port(f'[::]:{port}', server_credentials)

    # 啟動
    server.start()
    logger.info(f"🔒 gRPC server with TLS started on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(grace=5)

if __name__ == "__main__":
    # ✅ 2025-11-17: Use TLS by default in production
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--tls', action='store_true', help='Enable TLS encryption')
    parser.add_argument('--port', type=int, default=50051, help='Server port')
    args = parser.parse_args()

    if args.tls:
        serve_with_tls(port=args.port)
    else:
        logger.warning("⚠️  Running in INSECURE mode (no TLS). Use --tls for production.")
        serve(port=args.port)  # 原有的不安全模式
```

### 步驟 1.3：修改 gRPC 客戶端啟用 TLS

**檔案**: `03-Implementation/integration/sdr-oran-connector/oran_grpc_client.py`

找到 Line 150 附近的 TODO 並替換：

```python
# ✅ 2025-11-17: Implemented TLS credential loading
def create_secure_channel(server_address: str, cert_dir: str = "../../../certs"):
    """
    Create gRPC channel with TLS encryption
    Based on 2025 gRPC Python security best practices
    """
    # 讀取 CA 憑證（信任的根憑證）
    with open(f'{cert_dir}/ca.crt', 'rb') as f:
        trusted_certs = f.read()

    # 建立 SSL 憑證
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)

    # 建立安全通道
    channel = grpc.secure_channel(server_address, credentials)

    logger.info(f"🔒 Secure gRPC channel created to {server_address}")
    return channel

# 在 ORANGrpcClient 類中添加
class ORANGrpcClient:
    def __init__(self, server_address: str = "localhost:50051", use_tls: bool = True):
        self.server_address = server_address

        if use_tls:
            self.channel = create_secure_channel(server_address)
        else:
            logger.warning("⚠️  Using INSECURE channel (no TLS)")
            self.channel = grpc.insecure_channel(server_address)

        self.stub = sdr_oran_pb2_grpc.IQStreamServiceStub(self.channel)
```

### 步驟 1.4：測試 TLS 連線

```bash
# 終端 1：啟動 TLS 伺服器
cd 03-Implementation/integration/sdr-oran-connector
python sdr_grpc_server.py --tls

# 終端 2：測試客戶端連線
python oran_grpc_client.py --tls

# 驗證輸出
# ✅ 應該看到 "🔒 Secure gRPC channel created"
# ✅ 不應該有 TLS handshake 錯誤
```

---

## 🔐 階段 2：mTLS（雙向認證）實施

### 為何需要 mTLS？

> **2025 年安全趨勢**: mTLS 是零信任架構的核心
> - 防止服務偽裝攻擊
> - 確保只有經過驗證的服務能夠通訊
> - 符合 O-RAN 安全規範

### 步驟 2.1：生成客戶端憑證

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/certs

# 生成客戶端私鑰
openssl genrsa -out client.key 4096

# 生成客戶端 CSR
openssl req -new -key client.key -out client.csr \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=SDR-ORAN-Platform/OU=O-RAN-DU/CN=oran-client"

# 使用 CA 簽署客戶端憑證
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt -days 365

chmod 600 client.key
chmod 644 client.crt

echo "✅ mTLS 客戶端憑證已生成"
```

### 步驟 2.2：伺服器啟用 mTLS

修改 `serve_with_tls` 函數：

```python
def serve_with_mtls(port: int = 50051, cert_dir: str = "../../../certs"):
    """
    Start gRPC server with mTLS (mutual TLS) authentication
    Based on 2025 gRPC Python security best practices

    Reference: https://github.com/joekottke/python-grpc-ssl
    """
    # 讀取憑證
    with open(f'{cert_dir}/server.key', 'rb') as f:
        server_key = f.read()
    with open(f'{cert_dir}/server.crt', 'rb') as f:
        server_cert = f.read()
    with open(f'{cert_dir}/ca.crt', 'rb') as f:
        ca_cert = f.read()

    # ✅ 2025-11-17: Enable client certificate verification (mTLS)
    server_credentials = grpc.ssl_server_credentials(
        [(server_key, server_cert)],
        root_certificates=ca_cert,
        require_client_auth=True  # 🔐 要求客戶端提供憑證
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = IQStreamServicer()
    sdr_oran_pb2_grpc.add_IQStreamServiceServicer_to_server(service, server)
    server.add_secure_port(f'[::]:{port}', server_credentials)
    server.start()

    logger.info(f"🔐 gRPC server with mTLS started on port {port}")
    logger.info("   ✅ Client certificate verification: ENABLED")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=5)
```

### 步驟 2.3：客戶端啟用 mTLS

修改 `create_secure_channel` 函數：

```python
def create_mtls_channel(server_address: str, cert_dir: str = "../../../certs"):
    """
    Create gRPC channel with mTLS (mutual authentication)
    Based on 2025 gRPC Python security best practices

    Reference: https://github.com/nikolskiy/python-grpc-mutual-tls-auth
    """
    # 讀取 CA 憑證
    with open(f'{cert_dir}/ca.crt', 'rb') as f:
        trusted_certs = f.read()

    # ✅ 2025-11-17: Load client certificate for mTLS
    with open(f'{cert_dir}/client.key', 'rb') as f:
        client_key = f.read()
    with open(f'{cert_dir}/client.crt', 'rb') as f:
        client_cert = f.read()

    # 建立 mTLS 憑證
    credentials = grpc.ssl_channel_credentials(
        root_certificates=trusted_certs,
        private_key=client_key,
        certificate_chain=client_cert
    )

    channel = grpc.secure_channel(server_address, credentials)
    logger.info(f"🔐 mTLS gRPC channel created to {server_address}")
    logger.info("   ✅ Client authentication: ENABLED")

    return channel
```

### 步驟 2.4：測試 mTLS

```bash
# 終端 1：啟動 mTLS 伺服器
python sdr_grpc_server.py --mtls

# 終端 2：使用 mTLS 客戶端連線
python oran_grpc_client.py --mtls

# 驗證：
# ✅ 連線應該成功
# ❌ 若客戶端沒有有效憑證，連線應該被拒絕
```

---

## 🚀 生產環境部署建議

### 1. 使用正式 CA 簽發的憑證

**推薦 CA**:
- Let's Encrypt（免費，適合公開服務）
- DigiCert / GlobalSign（商業，高信任度）
- 內部 CA（企業內網）

### 2. 憑證管理最佳實踐

```bash
# 設定憑證輪換（每 90 天）
# 使用 certbot 自動更新 Let's Encrypt 憑證
sudo certbot renew --deploy-hook "systemctl restart sdr-grpc-server"

# 使用 Kubernetes Secrets 儲存憑證
kubectl create secret tls grpc-tls-secret \
  --cert=certs/server.crt \
  --key=certs/server.key \
  -n sdr-platform

# 在 Pod 中掛載
# volumeMounts:
#   - name: tls-certs
#     mountPath: /etc/grpc/certs
#     readOnly: true
```

### 3. 監控與告警

**Prometheus 指標**:
```python
from prometheus_client import Counter, Histogram

grpc_tls_handshake_errors = Counter(
    'grpc_tls_handshake_errors_total',
    'Total TLS handshake errors'
)

grpc_tls_certificate_expiry_days = Gauge(
    'grpc_tls_certificate_expiry_days',
    'Days until TLS certificate expiry'
)

# 在連線失敗時遞增
try:
    channel = create_mtls_channel(server_address)
except grpc.RpcError as e:
    grpc_tls_handshake_errors.inc()
    raise
```

**Grafana 告警規則**:
```yaml
# prometheus-rules.yml
- alert: TLSCertificateExpiringSoon
  expr: grpc_tls_certificate_expiry_days < 30
  annotations:
    summary: "TLS certificate expiring in {{ $value }} days"

- alert: TLSHandshakeErrors
  expr: rate(grpc_tls_handshake_errors_total[5m]) > 0.1
  annotations:
    summary: "High TLS handshake error rate"
```

---

## 🔍 故障排除

### 問題 1：TLS handshake failed

**錯誤訊息**:
```
grpc._channel._InactiveRpcError: SSL_ERROR_SSL: error:14094410:SSL routines:ssl3_read_bytes:sslv3 alert handshake failure
```

**解決方案**:
```bash
# 檢查憑證有效性
openssl x509 -in certs/server.crt -text -noout

# 檢查憑證與私鑰是否匹配
openssl x509 -noout -modulus -in certs/server.crt | md5sum
openssl rsa -noout -modulus -in certs/server.key | md5sum
# 兩者應該相同

# 檢查 CA 鏈
openssl verify -CAfile certs/ca.crt certs/server.crt
```

### 問題 2：certificate verify failed

**原因**: 客戶端不信任伺服器憑證

**解決方案**:
```python
# 確保客戶端使用正確的 CA 憑證
credentials = grpc.ssl_channel_credentials(
    root_certificates=open('certs/ca.crt', 'rb').read()  # 必須與伺服器的 CA 一致
)
```

### 問題 3：mTLS 客戶端被拒絕

**錯誤訊息**:
```
grpc._channel._InactiveRpcError: SSL_ERROR_SSL: error:14094412:SSL routines:ssl3_read_bytes:sslv3 alert bad certificate
```

**解決方案**:
```bash
# 檢查客戶端憑證是否由同一 CA 簽發
openssl verify -CAfile certs/ca.crt certs/client.crt

# 檢查憑證 CN (Common Name) 是否正確
openssl x509 -in certs/client.crt -noout -subject
```

---

## 📚 參考資源

### 官方文檔
- [gRPC Python Authentication](https://grpc.io/docs/guides/auth/)
- [gRPC Python Security](https://grpc.io/docs/languages/python/basics/)

### 2025 年最佳實踐
- [Securing gRPC Client Communication in Python with SSL and Certifi](https://medium.com/@abhishek.dixit070/securing-grpc-client-communication-in-python-with-ssl-and-certifi-d71685347c0e)
- [Strengthening Microservices: Implementing mTLS over gRPC](https://medium.com/deno-the-complete-reference/strengthening-microservices-implementing-mtls-over-grpc-for-trusted-communication-946b39333880)
- [gRPC with Mutual TLS Between Go and Python](https://blog.rollie.dev/posts/grpc-with-mutual-tls-between-go-and-python/)

### 開源範例
- [python-grpc-ssl](https://github.com/joekottke/python-grpc-ssl)
- [python-grpc-mutual-tls-auth](https://github.com/nikolskiy/python-grpc-mutual-tls-auth)

---

## ✅ 檢查清單

### TLS 啟用檢查清單
- [ ] 生成 CA 憑證
- [ ] 生成伺服器憑證並由 CA 簽署
- [ ] 修改伺服器程式碼啟用 TLS
- [ ] 修改客戶端程式碼使用 TLS
- [ ] 測試 TLS 連線成功
- [ ] 驗證無法使用不安全連線
- [ ] 配置憑證輪換策略
- [ ] 設定監控與告警

### mTLS 啟用檢查清單
- [ ] 生成客戶端憑證並由 CA 簽署
- [ ] 伺服器啟用客戶端憑證驗證
- [ ] 客戶端提供憑證進行認證
- [ ] 測試 mTLS 連線成功
- [ ] 驗證無憑證客戶端被拒絕
- [ ] 實施憑證撤銷機制（CRL/OCSP）
- [ ] 文檔化憑證管理流程
- [ ] 定期安全稽核

---

**文檔維護**: 請在每次更新憑證或修改 TLS 配置後更新此文檔
**最後審查**: 2025-11-17
**下次審查**: 2026-02-17（3 個月後）
