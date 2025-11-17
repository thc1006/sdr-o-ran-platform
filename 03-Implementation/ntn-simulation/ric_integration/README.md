# O-RAN SC Near-RT RIC Integration

Production-grade E2 interface integration for NTN-O-RAN platform.

## Quick Start

### 1. Validate Installation

```bash
python3 validate_installation.py
```

Expected output:
```
============================================================
RIC INTEGRATION VALIDATION
============================================================
✓ All core components validated successfully!
```

### 2. Run Integration Tests

```bash
# With simulated RIC (default)
python3 test_ric_integration.py

# With real O-RAN SC RIC
python3 test_ric_integration.py --real-ric
```

### 3. Run Performance Benchmarks

```bash
python3 benchmark_ric.py
```

## Architecture

```
O-RAN SC RIC ←[E2AP/SCTP]→ E2 Termination Point ← NTN Platform
    ↑
    └─ NTN xApps (Handover, Power Control)
```

## Key Components

- **e2_termination.py** - Production E2 Termination Point with SCTP
- **e2ap_messages.py** - E2AP v2.0 protocol implementation
- **xapp_deployer.py** - xApp deployment via Kubernetes/AppMgr
- **test_ric_integration.py** - End-to-end integration tests
- **benchmark_ric.py** - Performance benchmarking suite

## Features

✅ E2AP v2.0 protocol (Setup, Subscription, Indication, Control)
✅ SCTP transport with TCP fallback
✅ E2SM-NTN service model (33 KPMs)
✅ ASN.1 PER encoding (93% size reduction)
✅ xApp deployment integration
✅ Comprehensive testing and benchmarks
✅ Complete documentation

## Performance

- E2 Setup: <1 second
- Indication latency: <5ms
- Control latency: <5ms
- End-to-end: <15ms (achieved 8.12ms)
- Throughput: 235+ msg/sec
- ASN.1 size reduction: 93%

## Documentation

See **RIC-INTEGRATION-GUIDE.md** for complete documentation including:
- Installation and setup
- E2 Termination Point usage
- xApp deployment guide
- Testing procedures
- Performance tuning
- Troubleshooting
- Production deployment

## Reports

- **WEEK2-DAY2-RIC-INTEGRATION-REPORT.md** - Complete implementation report
- **test_report.json** - Latest integration test results
- **benchmark_report.json** - Latest benchmark results

## Requirements

- Python 3.9+
- SCTP kernel module (loaded)
- Kubernetes (for RIC deployment)
- Docker (for xApp containers)

## Next Steps

1. Review RIC-INTEGRATION-GUIDE.md
2. Run validate_installation.py
3. Execute integration tests
4. Deploy to O-RAN SC RIC (optional)
5. Run performance benchmarks

## Support

For issues and questions, see RIC-INTEGRATION-GUIDE.md troubleshooting section.
