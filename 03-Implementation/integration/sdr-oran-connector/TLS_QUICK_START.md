# TLS Quick Start Guide
## SDR-O-RAN gRPC Services

**Version**: 1.0.0
**Last Updated**: 2025-11-17

---

## Quick Commands

### Start TLS Server

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate
python3 sdr_grpc_server.py --tls
```

### Start TLS Client

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate
python3 oran_grpc_client.py --tls
```

### Test TLS Connection

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate
python3 test_tls_connection.py
```

---

## Command-Line Arguments

### Server (`sdr_grpc_server.py`)

| Argument | Default | Description |
|----------|---------|-------------|
| `--port` | 50051 | Server port |
| `--workers` | 10 | Max worker threads |
| `--tls` | False | Enable TLS encryption |
| `--cert-dir` | ./certs | Certificate directory |

**Example:**
```bash
python3 sdr_grpc_server.py --tls --port 50052 --workers 20 --cert-dir /path/to/certs
```

### Client (`oran_grpc_client.py`)

| Argument | Default | Description |
|----------|---------|-------------|
| `--server` | localhost:50051 | Server address |
| `--station-id` | ground-station-1 | Station identifier |
| `--tls` | False | Enable TLS encryption |
| `--cert-dir` | ./certs | Certificate directory |

**Example:**
```bash
python3 oran_grpc_client.py --tls --server 192.168.1.100:50051 --station-id gs-2
```

### Test Script (`test_tls_connection.py`)

| Argument | Default | Description |
|----------|---------|-------------|
| `--server` | localhost:50051 | Server address |
| `--cert-dir` | ./certs | Certificate directory |
| `--skip-insecure-test` | False | Skip insecure rejection test |

**Example:**
```bash
python3 test_tls_connection.py --server localhost:50051 --cert-dir ./certs
```

---

## Certificate Files

All certificates are located in `./certs/` directory:

| File | Type | Permissions | Purpose |
|------|------|-------------|---------|
| `ca.crt` | Certificate | 644 | Certificate Authority (trusted root) |
| `ca.key` | Private Key | 600 | CA signing key |
| `server.crt` | Certificate | 644 | Server certificate |
| `server.key` | Private Key | 600 | Server private key |
| `client.crt` | Certificate | 644 | Client certificate (for mTLS) |
| `client.key` | Private Key | 600 | Client private key (for mTLS) |

---

## Regenerate Certificates

If certificates expire or need to be regenerated:

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector/certs

# 1. Generate CA
openssl req -x509 -newkey rsa:4096 -days 365 -nodes \
  -keyout ca.key -out ca.crt \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=SDR-ORAN/OU=Research/CN=SDR-ORAN-CA"

# 2. Generate Server Certificate
openssl req -newkey rsa:4096 -nodes \
  -keyout server.key -out server.csr \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=SDR-ORAN/OU=gRPC-Server/CN=localhost"

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365

# 3. Generate Client Certificate
openssl req -newkey rsa:4096 -nodes \
  -keyout client.key -out client.csr \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=SDR-ORAN/OU=gRPC-Client/CN=oran-client"

openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt -days 365

# 4. Set permissions
chmod 600 *.key
chmod 644 *.crt
```

---

## Verify Certificates

```bash
cd certs

# Verify server certificate
openssl verify -CAfile ca.crt server.crt

# Verify client certificate
openssl verify -CAfile ca.crt client.crt

# Check expiry dates
openssl x509 -in server.crt -noout -dates
openssl x509 -in client.crt -noout -dates

# View certificate details
openssl x509 -in server.crt -text -noout
```

---

## Troubleshooting

### Problem: Certificate not found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: './certs/ca.crt'
```

**Solution:**
```bash
# Make sure you're in the correct directory
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector

# Or specify cert-dir explicitly
python3 sdr_grpc_server.py --tls --cert-dir /absolute/path/to/certs
```

### Problem: TLS handshake failed

**Error:**
```
grpc._channel._InactiveRpcError: SSL_ERROR_SSL
```

**Solution:**
1. Verify certificates are valid:
   ```bash
   openssl verify -CAfile certs/ca.crt certs/server.crt
   ```

2. Check certificate/key match:
   ```bash
   openssl x509 -noout -modulus -in certs/server.crt | md5sum
   openssl rsa -noout -modulus -in certs/server.key | md5sum
   # Should be identical
   ```

3. Regenerate certificates if needed

### Problem: Permission denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: './certs/server.key'
```

**Solution:**
```bash
# Fix permissions
chmod 600 certs/*.key
chmod 644 certs/*.crt
```

### Problem: Server already running

**Error:**
```
RuntimeError: Failed to bind to address [::]50051
```

**Solution:**
```bash
# Find and kill existing server
pkill -f "python3 sdr_grpc_server.py"

# Or use different port
python3 sdr_grpc_server.py --tls --port 50052
```

---

## Development vs Production

### Development (Current Setup)

- Self-signed certificates
- Valid for 365 days
- CN=localhost for server
- Suitable for testing and development

### Production (Recommended)

1. **Use CA-issued certificates**
   - Let's Encrypt (free)
   - DigiCert, GlobalSign (commercial)
   - Internal enterprise CA

2. **Update server certificate CN**
   - Use actual domain name or IP
   - Add Subject Alternative Names (SAN)

3. **Implement certificate rotation**
   - Automated renewal (e.g., certbot)
   - Hot-reload without service interruption

4. **Enable mTLS**
   - Mutual authentication
   - Zero-trust architecture

---

## Python Code Examples

### Import TLS Functions

```python
# Server-side
from sdr_grpc_server import create_server_credentials, serve

# Client-side
from oran_grpc_client import create_secure_channel
```

### Create TLS Server (Programmatic)

```python
import grpc
from concurrent import futures
from sdr_grpc_server import create_server_credentials
import sdr_oran_pb2_grpc

# Create server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

# Add services
# sdr_oran_pb2_grpc.add_IQStreamServiceServicer_to_server(servicer, server)

# Create TLS credentials
credentials = create_server_credentials(cert_dir="./certs")

# Bind with TLS
server.add_secure_port('[::]:50051', credentials)

# Start
server.start()
server.wait_for_termination()
```

### Create TLS Client (Programmatic)

```python
from oran_grpc_client import create_secure_channel
import sdr_oran_pb2_grpc

# Create secure channel
channel = create_secure_channel(
    host="localhost",
    port=50051,
    cert_dir="./certs"
)

# Create stub
stub = sdr_oran_pb2_grpc.IQStreamServiceStub(channel)

# Make RPC calls
# response = stub.GetStreamStats(request)
```

---

## Monitoring

### Check TLS Connection

```bash
# Using OpenSSL
openssl s_client -connect localhost:50051 -CAfile certs/ca.crt

# Should show:
# - Certificate chain
# - Verify return code: 0 (ok)
```

### Monitor Server Logs

```bash
# Server logs show TLS status
tail -f /path/to/server.log | grep TLS
```

### Test Connection

```bash
# Quick test
python3 test_tls_connection.py

# Should show:
# TLS connection test PASSED
```

---

## Additional Resources

- **Implementation Guide**: `/home/gnb/thc1006/sdr-o-ran-platform/docs/security/GRPC-TLS-MTLS-IMPLEMENTATION-GUIDE.md`
- **Implementation Report**: `./TLS_IMPLEMENTATION_REPORT.md`
- **gRPC Security Docs**: https://grpc.io/docs/guides/auth/
- **OpenSSL Docs**: https://www.openssl.org/docs/

---

**Last Updated**: 2025-11-17
**Maintainer**: thc1006@ieee.org
