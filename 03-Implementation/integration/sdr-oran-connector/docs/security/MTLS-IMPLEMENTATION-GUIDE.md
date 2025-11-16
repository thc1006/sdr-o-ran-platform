# mTLS Implementation Guide

**SDR-to-O-RAN Platform - Mutual TLS Authentication**

Version: 1.0.0
Date: 2025-11-17
Author: thc1006@ieee.org

---

## Table of Contents

1. [Overview](#overview)
2. [TLS vs mTLS Comparison](#tls-vs-mtls-comparison)
3. [Architecture](#architecture)
4. [Certificate Requirements](#certificate-requirements)
5. [Implementation](#implementation)
6. [Configuration Examples](#configuration-examples)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## Overview

This guide documents the implementation of **mTLS (Mutual TLS)** authentication for the SDR-to-O-RAN gRPC data plane. mTLS provides bidirectional authentication between the SDR Ground Station and the O-RAN DU, ensuring both parties verify each other's identity.

### What is mTLS?

**Mutual TLS (mTLS)** is an extension of TLS where both the client and server authenticate each other using X.509 certificates. Unlike standard TLS (where only the server presents a certificate), mTLS requires the client to also present a valid certificate signed by a trusted Certificate Authority (CA).

### Why mTLS?

For the SDR-to-O-RAN platform, mTLS provides:

- **Mutual Authentication**: Both ground station and O-RAN DU verify each other's identity
- **Zero-Trust Security**: No implicit trust - every connection requires valid certificates
- **Protection Against**: Man-in-the-middle attacks, unauthorized clients, certificate spoofing
- **Compliance**: Meets NFR-SEC-001 requirements for secure communication
- **Defense in Depth**: Additional layer beyond network-level security

---

## TLS vs mTLS Comparison

| Feature | TLS (One-Way) | mTLS (Mutual) |
|---------|---------------|---------------|
| **Server Authentication** | Yes | Yes |
| **Client Authentication** | No | Yes |
| **Server Certificate Required** | Yes | Yes |
| **Client Certificate Required** | No | Yes |
| **Protection Level** | Moderate | High |
| **Use Case** | Public websites | Internal/B2B APIs |
| **Complexity** | Low | Medium |
| **Certificate Management** | Server only | Both sides |

### Authentication Flow

**TLS (One-Way):**
```
1. Client → Server: Hello
2. Server → Client: Certificate
3. Client: Verify server certificate
4. Encrypted communication begins
```

**mTLS (Mutual):**
```
1. Client → Server: Hello
2. Server → Client: Certificate + Request client cert
3. Client → Server: Client certificate
4. Server: Verify client certificate
5. Client: Verify server certificate
6. Encrypted communication begins (both authenticated)
```

---

## Architecture

### Certificate Hierarchy

```
┌─────────────────────────────────────┐
│   Certificate Authority (CA)        │
│   - ca.crt (public)                 │
│   - ca.key (private, secured)       │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────────┐   ┌───▼────────┐
│  Server    │   │  Client    │
│  Cert      │   │  Cert      │
│            │   │            │
│ server.crt │   │ client.crt │
│ server.key │   │ client.key │
└────────────┘   └────────────┘
```

### Component Interaction

```
┌──────────────────────┐           ┌──────────────────────┐
│  SDR Ground Station  │           │    O-RAN DU          │
│                      │           │                      │
│  ┌────────────────┐  │           │  ┌────────────────┐  │
│  │ gRPC Client    │  │  mTLS     │  │ gRPC Server    │  │
│  │                │  │◄─────────►│  │                │  │
│  │ client.crt     │  │           │  │ server.crt     │  │
│  │ client.key     │  │  Mutual   │  │ server.key     │  │
│  │ ca.crt         │  │   Auth    │  │ ca.crt         │  │
│  └────────────────┘  │           │  └────────────────┘  │
│                      │           │                      │
└──────────────────────┘           └──────────────────────┘
```

### Authentication Process

1. **Client Initiates Connection**
   - Loads CA certificate, client certificate, and client private key
   - Establishes secure channel with mTLS credentials

2. **SSL/TLS Handshake**
   - Server presents `server.crt`
   - Client verifies server certificate against `ca.crt`
   - Server requests client certificate
   - Client presents `client.crt`
   - Server verifies client certificate against `ca.crt`

3. **Connection Established**
   - Both parties authenticated
   - Encrypted communication channel active
   - gRPC RPCs can proceed

4. **Connection Rejection**
   - If client doesn't present certificate: `PEER_DID_NOT_RETURN_A_CERTIFICATE`
   - If certificate invalid: `CERTIFICATE_VERIFY_FAILED`
   - If certificate not trusted: `UNKNOWN_CA`

---

## Certificate Requirements

### Certificate Files

All certificates are located in: `./certs/`

| File | Type | Purpose | Access |
|------|------|---------|--------|
| `ca.crt` | Public | Root CA certificate | Both client & server |
| `ca.key` | Private | CA signing key | Secure storage only |
| `server.crt` | Public | Server certificate | Server only |
| `server.key` | Private | Server private key | Server only (0600) |
| `client.crt` | Public | Client certificate | Client only |
| `client.key` | Private | Client private key | Client only (0600) |

### Certificate Properties

All certificates must include:

- **Common Name (CN)**: `localhost` (for testing) or actual hostname/FQDN
- **Subject Alternative Names (SAN)**: `DNS:localhost`, `IP:127.0.0.1`
- **Key Usage**: `Digital Signature`, `Key Encipherment`
- **Extended Key Usage**:
  - Server: `TLS Web Server Authentication`
  - Client: `TLS Web Client Authentication`
- **Validity Period**: Recommend 1 year max
- **Key Algorithm**: RSA 4096-bit or ECDSA P-256
- **Signature Algorithm**: SHA-256

### Verification

Check certificate validity:

```bash
# Verify server certificate
openssl verify -CAfile certs/ca.crt certs/server.crt

# Verify client certificate
openssl verify -CAfile certs/ca.crt certs/client.crt

# View certificate details
openssl x509 -in certs/server.crt -text -noout
openssl x509 -in certs/client.crt -text -noout

# Check certificate expiration
openssl x509 -in certs/server.crt -noout -dates
openssl x509 -in certs/client.crt -noout -dates
```

---

## Implementation

### Server Implementation

**File:** `sdr_grpc_server.py`

#### 1. Server Credentials Function

```python
def create_server_credentials(cert_dir: str = "./certs", require_client_auth: bool = True):
    """Create gRPC server credentials with TLS/mTLS encryption.

    Args:
        cert_dir: Directory containing SSL certificates
        require_client_auth: Whether to require client certificate (mTLS)

    Returns:
        grpc.ServerCredentials object
    """
    import os

    # Read certificate files
    with open(f'{cert_dir}/server.key', 'rb') as f:
        server_key = f.read()
    with open(f'{cert_dir}/server.crt', 'rb') as f:
        server_cert = f.read()
    with open(f'{cert_dir}/ca.crt', 'rb') as f:
        ca_cert = f.read()

    # Create server credentials with optional mTLS
    server_credentials = grpc.ssl_server_credentials(
        [(server_key, server_cert)],
        root_certificates=ca_cert,
        require_client_auth=require_client_auth  # Enable mTLS
    )

    return server_credentials
```

#### 2. Server Startup

```python
def serve(port: int = 50051, use_tls: bool = True, use_mtls: bool = False, cert_dir: str = "./certs"):
    """Start gRPC server with optional TLS/mTLS encryption."""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register services
    sdr_oran_pb2_grpc.add_IQStreamServiceServicer_to_server(
        IQStreamServicer(), server
    )

    # Bind with mTLS, TLS, or insecure
    if use_mtls:
        server_credentials = create_server_credentials(cert_dir, require_client_auth=True)
        server.add_secure_port(f'[::]:{port}', server_credentials)
        logger.info(f"mTLS server listening on port {port}")
    elif use_tls:
        server_credentials = create_server_credentials(cert_dir, require_client_auth=False)
        server.add_secure_port(f'[::]:{port}', server_credentials)
        logger.info(f"TLS server listening on port {port}")
    else:
        server.add_insecure_port(f'[::]:{port}')
        logger.warning(f"INSECURE server listening on port {port}")

    server.start()
    server.wait_for_termination()
```

#### 3. Command-Line Arguments

```python
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SDR-to-O-RAN gRPC Server')
    parser.add_argument('--port', type=int, default=50051, help='Server port')
    parser.add_argument('--tls', action='store_true', default=True, help='Enable TLS')
    parser.add_argument('--mtls', action='store_true', help='Enable mTLS')
    parser.add_argument('--cert-dir', type=str, default='./certs', help='Certificate directory')
    args = parser.parse_args()

    serve(port=args.port, use_tls=args.tls, use_mtls=args.mtls, cert_dir=args.cert_dir)
```

### Client Implementation

**File:** `oran_grpc_client.py`

#### 1. Client Channel Creation

```python
def create_secure_channel(host: str, port: int, cert_dir: str = "./certs", use_mtls: bool = False):
    """Create secure gRPC channel with TLS/mTLS encryption.

    Args:
        host: Server hostname
        port: Server port
        cert_dir: Directory containing SSL certificates
        use_mtls: Whether to use mTLS (provide client certificate)

    Returns:
        grpc.Channel object
    """
    # Read CA certificate
    with open(f'{cert_dir}/ca.crt', 'rb') as f:
        ca_cert = f.read()

    if use_mtls:
        # Read client certificate and key for mTLS
        with open(f'{cert_dir}/client.crt', 'rb') as f:
            client_cert = f.read()
        with open(f'{cert_dir}/client.key', 'rb') as f:
            client_key = f.read()

        # Create mTLS credentials
        credentials = grpc.ssl_channel_credentials(
            root_certificates=ca_cert,
            private_key=client_key,
            certificate_chain=client_cert
        )

        logger.info(f"Creating mTLS channel to {host}:{port}")
    else:
        # Create TLS-only credentials
        credentials = grpc.ssl_channel_credentials(
            root_certificates=ca_cert
        )

        logger.info(f"Creating TLS channel to {host}:{port}")

    # Create secure channel
    channel = grpc.secure_channel(
        f'{host}:{port}',
        credentials,
        options=[
            ('grpc.ssl_target_name_override', 'localhost'),
        ]
    )

    return channel
```

#### 2. Client Initialization

```python
class ORANIQClient:
    def __init__(self, server_address: str, use_mtls: bool = False, cert_dir: str = "./certs"):
        # Split server address
        host, port = server_address.split(':')
        port = int(port)

        # Create secure channel with optional mTLS
        self.channel = create_secure_channel(host, port, cert_dir, use_mtls)

        # Create stubs
        self.iq_stub = sdr_oran_pb2_grpc.IQStreamServiceStub(self.channel)
```

---

## Configuration Examples

### Example 1: mTLS Server

```bash
# Start server with mTLS enforcement
cd 03-Implementation/integration/sdr-oran-connector
source ../../../venv/bin/activate
python3 sdr_grpc_server.py --mtls --port 50051 --cert-dir ./certs
```

Expected output:
```
============================================================
SDR-to-O-RAN gRPC Server
Port: 50051
Security: mTLS (Mutual Authentication)
============================================================
Secure gRPC server listening on port 50051 (mTLS enabled)
Server started. Press Ctrl+C to stop.
```

### Example 2: mTLS Client

```bash
# Connect with mTLS
python3 oran_grpc_client.py --server localhost:50051 --mtls --cert-dir ./certs
```

### Example 3: TLS-Only Server (for backward compatibility)

```bash
# Start server with TLS only (no client cert required)
python3 sdr_grpc_server.py --tls --port 50052 --cert-dir ./certs
```

### Example 4: Python Code

```python
# mTLS Server
from sdr_grpc_server import serve
serve(port=50051, use_mtls=True, cert_dir="./certs")

# mTLS Client
from oran_grpc_client import ORANIQClient
client = ORANIQClient(
    server_address="localhost:50051",
    use_mtls=True,
    cert_dir="./certs"
)
```

---

## Testing

### Test Script

**File:** `test_mtls_connection.py`

#### Run All Tests

```bash
cd 03-Implementation/integration/sdr-oran-connector
source ../../../venv/bin/activate

# Start mTLS server (in separate terminal)
python3 sdr_grpc_server.py --mtls --port 50051

# Run tests
python3 test_mtls_connection.py
```

#### Expected Output

```
+==========================================================+
|               mTLS Test Suite                           |
+==========================================================+

============================================================
mTLS Connection Test (Mutual Authentication)
============================================================
Loading certificates...
✓ Certificates loaded successfully
✓ mTLS credentials created
✓ mTLS handshake successful (client certificate verified)
✓ mTLS connection works

============================================================
Test: TLS without Client Certificate (Should Fail)
============================================================
✓ All RPC attempts failed (expected)
✓ mTLS enforcement verified

============================================================
FINAL RESULTS
============================================================
✓ mTLS with Client Certificate: PASSED
✓ Rejection without Client Cert: PASSED

✓ All mTLS tests PASSED
```

#### Server Logs (mTLS Enforcement)

When a client attempts to connect without a certificate:

```
E1117 04:09:09 ssl_transport_security.cc:1511]
  Handshake failed with fatal error SSL_ERROR_SSL:
  error:100000c0:SSL routines:OPENSSL_internal:PEER_DID_NOT_RETURN_A_CERTIFICATE.
```

This confirms mTLS is working - the server rejects the connection at the SSL handshake layer.

### Manual Testing

#### Test 1: Verify mTLS Connection

```python
import grpc
import sdr_oran_pb2_grpc
import sdr_oran_pb2

# Load certificates
with open('./certs/ca.crt', 'rb') as f:
    ca_cert = f.read()
with open('./certs/client.crt', 'rb') as f:
    client_cert = f.read()
with open('./certs/client.key', 'rb') as f:
    client_key = f.read()

# Create mTLS credentials
credentials = grpc.ssl_channel_credentials(
    root_certificates=ca_cert,
    private_key=client_key,
    certificate_chain=client_cert
)

# Connect
channel = grpc.secure_channel(
    'localhost:50051',
    credentials,
    options=[('grpc.ssl_target_name_override', 'localhost')]
)

# Test RPC
stub = sdr_oran_pb2_grpc.IQStreamServiceStub(channel)
request = sdr_oran_pb2.StreamStatsRequest(station_id="test")
response = stub.GetStreamStats(request)
print("Success:", response)
```

#### Test 2: Verify mTLS Rejection

```python
# Try to connect without client certificate
credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert)
channel = grpc.secure_channel('localhost:50051', credentials)
stub = sdr_oran_pb2_grpc.IQStreamServiceStub(channel)

try:
    response = stub.GetStreamStats(request)
    print("ERROR: Should have been rejected!")
except grpc.RpcError as e:
    print(f"Correctly rejected: {e.code()}")
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Certificate Verification Failed

**Symptom:**
```
Handshake failed: CERTIFICATE_VERIFY_FAILED
```

**Causes:**
- Client/server certificate not signed by CA
- CA certificate mismatch
- Certificate expired

**Solutions:**
```bash
# Verify certificate chain
openssl verify -CAfile certs/ca.crt certs/server.crt
openssl verify -CAfile certs/ca.crt certs/client.crt

# Check expiration
openssl x509 -in certs/server.crt -noout -dates
openssl x509 -in certs/client.crt -noout -dates

# Regenerate certificates if needed
cd certs/
./generate_certs.sh  # Or your certificate generation script
```

#### Issue 2: Hostname Mismatch

**Symptom:**
```
Handshake failed: CERTIFICATE_VERIFY_FAILED (hostname mismatch)
```

**Cause:**
- Certificate CN or SAN doesn't match server hostname

**Solutions:**
```bash
# Check certificate CN and SAN
openssl x509 -in certs/server.crt -text -noout | grep -A1 "Subject:"
openssl x509 -in certs/server.crt -text -noout | grep -A1 "Subject Alternative Name"

# Use grpc.ssl_target_name_override in client
channel = grpc.secure_channel(
    'actual-hostname:50051',
    credentials,
    options=[('grpc.ssl_target_name_override', 'localhost')]  # Override for testing
)
```

#### Issue 3: Client Certificate Not Sent

**Symptom:**
```
Server log: PEER_DID_NOT_RETURN_A_CERTIFICATE
Client: Connection refused or timeout
```

**Cause:**
- Client not providing certificate
- Client credentials missing private key

**Solutions:**
```python
# Ensure all three components are provided
credentials = grpc.ssl_channel_credentials(
    root_certificates=ca_cert,      # Required
    private_key=client_key,         # Required for mTLS
    certificate_chain=client_cert   # Required for mTLS
)

# Verify files exist and are readable
import os
assert os.path.exists('./certs/ca.crt')
assert os.path.exists('./certs/client.crt')
assert os.path.exists('./certs/client.key')
```

#### Issue 4: Permission Denied

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: './certs/client.key'
```

**Cause:**
- Private key files have incorrect permissions

**Solutions:**
```bash
# Fix permissions
chmod 600 certs/*.key
chmod 644 certs/*.crt

# Verify
ls -la certs/
# Should show:
# -rw------- client.key
# -rw------- server.key
# -rw-r--r-- client.crt
# -rw-r--r-- server.crt
# -rw-r--r-- ca.crt
```

#### Issue 5: gRPC Channel Not Ready

**Symptom:**
```
grpc.StatusCode.UNAVAILABLE: failed to connect to all addresses
```

**Causes:**
- Server not running
- Port mismatch
- Firewall blocking connection

**Solutions:**
```bash
# Check server is running
ps aux | grep sdr_grpc_server

# Check port is listening
netstat -tlnp | grep 50051
# or
ss -tlnp | grep 50051

# Test connectivity
telnet localhost 50051

# Check firewall (if applicable)
sudo ufw status
sudo iptables -L
```

### Debug Logging

Enable detailed gRPC logging:

```bash
# Environment variables for debug logging
export GRPC_VERBOSITY=DEBUG
export GRPC_TRACE=all

# Run server/client with debug output
python3 sdr_grpc_server.py --mtls
```

Python code:

```python
import logging
import grpc

# Enable gRPC debug logging
logging.basicConfig(level=logging.DEBUG)
grpc_logger = logging.getLogger('grpc')
grpc_logger.setLevel(logging.DEBUG)
```

### Verification Checklist

- [ ] CA certificate (`ca.crt`) exists and is valid
- [ ] Server certificate (`server.crt`) signed by CA
- [ ] Client certificate (`client.crt`) signed by CA
- [ ] Private keys (`*.key`) have 0600 permissions
- [ ] Certificates not expired
- [ ] CN/SAN matches hostname
- [ ] Server running with `--mtls` flag
- [ ] Client providing all three credentials (CA, cert, key)
- [ ] Port not blocked by firewall
- [ ] Certificate chain verifiable with `openssl verify`

---

## Security Best Practices

### Certificate Management

1. **Private Key Protection**
   ```bash
   # Store private keys with restricted permissions
   chmod 600 *.key

   # Never commit private keys to version control
   echo "*.key" >> .gitignore

   # Use secure key storage (HSM, KMS) in production
   ```

2. **Certificate Rotation**
   ```bash
   # Rotate certificates every 90 days
   # Use short-lived certificates (1 year max)
   # Implement automated renewal process

   # Check expiration dates regularly
   openssl x509 -in server.crt -noout -enddate
   ```

3. **Certificate Revocation**
   ```bash
   # Implement CRL (Certificate Revocation List)
   # Or use OCSP (Online Certificate Status Protocol)
   # Immediately revoke compromised certificates
   ```

### Deployment Security

1. **Environment Separation**
   - Separate certificates for dev/staging/prod
   - Different CAs for different environments
   - Never reuse production certificates in testing

2. **Secret Management**
   ```bash
   # Use Kubernetes secrets for certificates
   kubectl create secret tls grpc-mtls-certs \
     --cert=server.crt \
     --key=server.key \
     --namespace=oran

   # Or use HashiCorp Vault
   vault kv put secret/grpc/server cert=@server.crt key=@server.key
   ```

3. **Network Security**
   - Deploy behind firewall/security groups
   - Restrict port 50051 to trusted IPs only
   - Use VPN/private network for production
   - Enable mTLS + network policies (defense in depth)

### Monitoring & Auditing

1. **Connection Logging**
   ```python
   # Log all connection attempts
   logger.info(f"mTLS connection from {peer_identity}")
   logger.warning(f"Rejected connection: {error_reason}")
   ```

2. **Certificate Expiry Monitoring**
   ```bash
   # Alert 30 days before expiration
   # Prometheus metrics for cert expiry
   # Automated renewal process
   ```

3. **Audit Trail**
   - Log certificate usage
   - Track certificate issuance/revocation
   - Monitor failed authentication attempts
   - Integrate with SIEM (Security Information and Event Management)

### Compliance

- **NIST 800-52**: TLS configuration guidelines
- **NIST 800-57**: Key management recommendations
- **3GPP TS 33.310**: O-RAN security specifications
- **NFR-SEC-001**: Platform security requirements

---

## Production Deployment

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: v1
kind: Secret
metadata:
  name: grpc-mtls-certs
  namespace: oran
type: kubernetes.io/tls
data:
  ca.crt: <base64-encoded-ca-cert>
  server.crt: <base64-encoded-server-cert>
  server.key: <base64-encoded-server-key>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdr-grpc-server
  namespace: oran
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: grpc-server
        image: sdr-oran-server:latest
        command: ["python3", "sdr_grpc_server.py"]
        args: ["--mtls", "--port", "50051", "--cert-dir", "/certs"]
        volumeMounts:
        - name: certs
          mountPath: /certs
          readOnly: true
      volumes:
      - name: certs
        secret:
          secretName: grpc-mtls-certs
          defaultMode: 0600
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Copy certificates (use secrets in production)
COPY certs/ /app/certs/
RUN chmod 600 /app/certs/*.key

EXPOSE 50051
CMD ["python3", "sdr_grpc_server.py", "--mtls", "--port", "50051"]
```

```bash
# Build and run
docker build -t sdr-oran-server .
docker run -p 50051:50051 -v $(pwd)/certs:/app/certs:ro sdr-oran-server
```

---

## Conclusion

This implementation provides production-grade mTLS authentication for the SDR-to-O-RAN platform. Key achievements:

- Mutual authentication between ground station and O-RAN DU
- SSL/TLS handshake-level certificate verification
- Comprehensive testing and validation
- Production-ready deployment configurations
- Security best practices compliance

For questions or issues, contact: thc1006@ieee.org

---

## References

- [gRPC Authentication Guide](https://grpc.io/docs/guides/auth/)
- [NIST 800-52: TLS Guidelines](https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final)
- [3GPP TS 33.310: O-RAN Security](https://www.3gpp.org/DynaReport/33310.htm)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [Python gRPC Security](https://grpc.github.io/grpc/python/grpc.html#grpc.ssl_channel_credentials)

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-17 | thc1006@ieee.org | Initial release |
