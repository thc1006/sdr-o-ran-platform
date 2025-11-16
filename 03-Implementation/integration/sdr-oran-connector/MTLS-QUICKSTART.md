# mTLS Quick Start Guide

**SDR-to-O-RAN Platform - Mutual TLS Setup**

## Quick Reference

### Start mTLS Server

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate
python3 sdr_grpc_server.py --mtls --port 50051
```

### Start mTLS Client

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate
python3 oran_grpc_client.py --server localhost:50051 --mtls
```

### Run mTLS Tests

```bash
cd /home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate

# Start server in background
python3 sdr_grpc_server.py --mtls --port 50051 &

# Run tests
python3 test_mtls_connection.py

# Stop server
pkill -f sdr_grpc_server
```

## What Changed?

### Server (`sdr_grpc_server.py`)

- Added `require_client_auth` parameter to `create_server_credentials()`
- Updated `serve()` function to support `use_mtls` flag
- Added `--mtls` command-line argument
- Server now enforces client certificate verification

### Client (`oran_grpc_client.py`)

- Updated `create_secure_channel()` to support mTLS credentials
- Added `use_mtls` parameter to `ORANIQClient` class
- Client now sends certificate when mTLS is enabled
- Added `--mtls` command-line argument

### New Files

- `test_mtls_connection.py` - Automated mTLS testing
- `docs/security/MTLS-IMPLEMENTATION-GUIDE.md` - Comprehensive documentation
- `MTLS-QUICKSTART.md` - This quick reference

## Certificate Files

All certificates are in: `./certs/`

- `ca.crt` - Certificate Authority (trusted root)
- `server.crt` - Server certificate
- `server.key` - Server private key
- `client.crt` - Client certificate
- `client.key` - Client private key

## Security Modes

| Mode | Server Flag | Client Flag | Authentication |
|------|-------------|-------------|----------------|
| **Insecure** | (none) | (none) | None |
| **TLS** | `--tls` | `--tls` | Server only |
| **mTLS** | `--mtls` | `--mtls` | Mutual |

## Test Results

All tests PASSED:
- ✓ mTLS with client certificate: Connection successful
- ✓ Rejection without client cert: Server properly rejects
- ✓ SSL handshake verification: PEER_DID_NOT_RETURN_A_CERTIFICATE error logged

## For More Information

See: `docs/security/MTLS-IMPLEMENTATION-GUIDE.md`
