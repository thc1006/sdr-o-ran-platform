# SDR-Based Cloud-Native Satellite Ground Station & O-RAN Integration for NTN Communications

**Author**: Hsiu-Chi Tsai (thc1006@ieee.org)
**Project Type**: Research & Development Platform
**Last Updated**: 2025-11-12
**Version**: 3.0.0

[![CI/CD](https://github.com/thc1006/sdr-o-ran-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/thc1006/sdr-o-ran-platform/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Research-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

---

## Project Overview

This project is a research and development platform integrating Software-Defined Radio (SDR) satellite ground stations with cloud-native O-RAN architecture for Non-Terrestrial Network (NTN) communications. The project follows Model-Based Systems Engineering (MBSE) methodology and employs 2025 state-of-the-art technologies.

### Key Objectives

1. Demonstrate SDR-based satellite ground station integration with O-RAN architecture
2. Apply Model-Based Systems Engineering (MBSE) methodology throughout
3. Evaluate multiple integration architectures with comprehensive analysis
4. Provide working implementation examples where feasible
5. Maintain compliance with 3GPP Release 18/19 and O-RAN Alliance specifications
6. Document gaps and limitations transparently

---

## Project Status

**Overall Completion**: Approximately 65-70% (Code complete, testing and hardware integration pending)

### Component Status

| Component | Implementation | Testing | Hardware Required | Status |
|-----------|---------------|---------|-------------------|--------|
| SDR API Gateway | Complete (685 lines) | 18/18 tests pass | USRP X310 ($7.5k) | Code operational, hardware simulated |
| gRPC Services | Complete (1,157 lines) | 3/4 tests pass | No | Server functional, minor test issue |
| DRL Trainer | Complete (649 lines) | Training successful | No | PPO model trained |
| Quantum Security | Complete (584 lines) | Both algorithms working | No | ML-KEM-1024 & ML-DSA-87 functional |
| Traffic Steering xApp | Complete (481 lines) | Partial | RIC framework | Code valid, requires framework |
| LEO NTN Simulator | Complete (102 lines) | Operational | No | ZMQ streaming verified |
| O-RAN gNB | Complete (1,147 lines) | Not tested | Yes | Code exists, requires validation |
| Near-RT RIC | Complete (891 lines) | Not tested | Partial | Requires RIC framework |
| Orchestration | Complete (743 lines) | K8s manifests created | K8s cluster | Deployment not verified |

**Total Lines of Code**: 6,337 lines of production Python code

### What Works

- LEO NTN Simulator with ZeroMQ streaming (249M+ IQ samples transferred, 30.72 MSPS)
- SDR API Gateway with 18 endpoints (FastAPI + OAuth2)
- gRPC bidirectional streaming services (port 50051)
- DRL training pipeline (PPO/SAC algorithms, 1000 timesteps)
- Post-Quantum Cryptography implementation (NIST-approved algorithms)
- CI/CD pipeline with automated testing and security scanning
- Comprehensive documentation (95+ markdown files)

### What Requires Work

- Unit test coverage currently at ~15% (target: 60-80%)
- Hardware integration requires USRP X310 (not available, $7,500)
- Traffic Steering xApp needs O-RAN SC ricxappframe
- End-to-end integration testing not yet performed
- Production hardening and security audit needed
- Performance benchmarking on actual hardware

### Recent Updates (2025-11-11)

- LEO-SDR integration completed with real-time IQ sample processing
- ZeroMQ streaming operational with 0% packet loss in testing
- Security fixes applied (removed hardcoded credentials, added input validation)
- Documentation reorganized for improved clarity

**Detailed Reports**:
- [LEO-SDR Integration Report](docs/reports/LEO-SDR-INTEGRATION-REPORT.md)
- [Deployment Test Report](docs/deployment/REAL-DEPLOYMENT-TEST-REPORT.md)
- [Known Issues](docs/testing/KNOWN-ISSUES.md)

---

## Quick Start

### Prerequisites

**For Full Deployment** (not currently available):
- USRP X310 with GPSDO and antenna system ($7,500)
- 3x servers with 32GB RAM, 8-core CPU, 1TB SSD each
- 10 GbE networking equipment
- Kubernetes cluster (v1.28+)

**For Development/Testing** (simulation mode):
- Docker and Docker Compose
- Python 3.11+
- 16GB RAM, 4-core CPU minimum
- WSL2 (for Windows) with GPU support recommended

### Installation

#### Option 1: Quick Start (Simulation Mode)

```bash
# Clone repository
git clone https://github.com/thc1006/sdr-o-ran-platform.git
cd sdr-o-ran-platform

# Run quick start script (Linux/WSL)
./scripts/quick-start.sh

# Or use PowerShell for Windows
.\scripts\DEPLOY-NOW.ps1
```

#### Option 2: Manual Setup

```bash
# 1. Generate gRPC stubs
cd 03-Implementation/integration/sdr-oran-connector
python generate_grpc_stubs.py

# 2. Start services with Docker Compose
cd ../../..
docker-compose up -d

# 3. Verify services
docker-compose ps
curl http://localhost:8000/health
```

#### Option 3: Full Deployment Guide

See comprehensive deployment documentation:
- [Deployment Guide](docs/deployment/DEPLOYMENT-GUIDE.md)
- [WSL2 GPU Setup](docs/deployment/DEPLOYMENT-WSL2-GPU.md)
- [Quick Start Guide](START-HERE.md)

---

## Project Structure

```
sdr-o-ran-platform/
├── README.md                          # This file
├── START-HERE.md                      # Quick start guide
├── docker-compose.yml                 # Container orchestration
├── pyproject.toml                     # Python project configuration
├── CITATION.cff                       # Academic citation format
│
├── 00-MBSE-Models/                    # Model-Based Systems Engineering models
├── 01-Architecture-Analysis/          # Architecture comparison and analysis
├── 02-Technical-Specifications/       # Complete technical specifications
├── 03-Implementation/                 # All source code implementations
│   ├── sdr-platform/                 # SDR platform (API gateway, gRPC)
│   ├── simulation/                   # LEO NTN simulator
│   ├── integration/                  # System integration components
│   ├── oran-cnfs/                    # O-RAN network functions
│   ├── ai-ml-pipeline/               # AI/ML training and inference
│   ├── orchestration/                # Kubernetes/Nephio orchestration
│   └── security/                     # Post-Quantum Cryptography
│
├── 04-Deployment/                     # Infrastructure and deployment
│   ├── infrastructure/               # Terraform IaC (AWS EKS)
│   ├── kubernetes/                   # Kubernetes manifests
│   ├── ci-cd/                        # CI/CD pipeline configs
│   └── monitoring/                   # Prometheus, Grafana dashboards
│
├── 05-Documentation/                  # Technical documentation
├── 06-Deployment-Operations/          # Operations and maintenance guides
├── 06-References/                     # Standards and research references
├── 07-Legacy-Docs/                    # Historical documents
├── 08-Paper-Submission/               # IEEE paper submission materials
│
├── docs/                              # Project management documentation
│   ├── deployment/                   # Deployment guides and reports
│   ├── reports/                      # Technical reports and analysis
│   ├── architecture/                 # Architecture documentation
│   ├── planning/                     # Development planning
│   ├── summaries/                    # Progress summaries
│   ├── testing/                      # Test reports and results
│   └── verification/                 # Verification reports
│
├── scripts/                           # Automation scripts
│   ├── auto-deploy.sh               # Automated deployment
│   ├── quick-start.sh               # Quick start script
│   ├── DEPLOY-NOW.ps1               # Windows deployment
│   ├── test-all.sh                  # Test suite runner
│   ├── stop-all.sh                  # Stop all services
│   └── monitor.sh                   # Monitoring dashboard
│
└── tests/                             # Automated tests
    └── infrastructure/               # Infrastructure tests
```

---

## Technology Stack

### SDR Platform
- **Hardware**: USRP X310 with GPSDO (simulated in current implementation)
- **Protocols**: VITA 49.2 (VRT), gRPC bidirectional streaming
- **APIs**: FastAPI (REST), WebSocket (real-time IQ streaming)
- **Languages**: Python 3.11, Protocol Buffers

### O-RAN Components
- **gNB**: OpenAirInterface (OAI) 5G-NTN
- **Interfaces**: FAPI P5/P7, F1, E2, A1, O1
- **RIC**: OSC Near-RT RIC architecture
- **SMO**: Service Management and Orchestration

### AI/ML Framework
- **Training**: Stable Baselines3 (PPO, SAC algorithms)
- **Environment**: Gymnasium (custom RIC environment)
- **Inference**: ONNX Runtime
- **Explainability**: SHAP (SHapley Additive exPlanations)
- **Storage**: Redis SDL (Shared Data Layer)

### Security
- **Post-Quantum KEM**: ML-KEM-1024 (formerly CRYSTALS-Kyber)
- **Post-Quantum Signatures**: ML-DSA-87 (formerly CRYSTALS-Dilithium)
- **Hybrid Approach**: PQC + X25519 combined via HKDF
- **Library**: pqcrypto (NIST-approved implementations)

### Infrastructure
- **Orchestration**: Kubernetes 1.28+, Nephio R1
- **Containers**: Docker, containerd
- **CI/CD**: GitHub Actions, ArgoCD
- **Monitoring**: Prometheus, Grafana, Loki, TensorBoard
- **IaC**: Terraform (AWS EKS deployment)

### Standards Compliance
- **3GPP**: Release 18 (NTN baseline), Release 19 (RedCap, ISL)
- **O-RAN**: Alliance specifications (WG1-WG4)
- **NIST**: Post-Quantum Cryptography standards
- **ETSI**: NFV MANO standards

---

## Documentation

### Essential Guides
- [Quick Start Guide](START-HERE.md) - Get started in 5 minutes
- [Deployment Guide](docs/deployment/DEPLOYMENT-GUIDE.md) - Comprehensive deployment instructions
- [WSL2 GPU Setup](docs/deployment/DEPLOYMENT-WSL2-GPU.md) - Windows deployment with GPU acceleration

### Technical Documentation
- [Technical Whitepaper](05-Documentation/whitepaper.md) - Main technical document
- [Architecture Analysis](05-Documentation/deep-dive-technical-analysis.md) - Detailed architecture analysis
- [System Requirements](02-Technical-Specifications/system-requirements.md) - System requirements specification
- [Interface Specifications](02-Technical-Specifications/interface-specifications.md) - Interface control document

### Implementation Documentation
- [SDR API Server](03-Implementation/sdr-platform/api-gateway/sdr_api_server.py) - FastAPI REST implementation
- [gRPC Streaming](03-Implementation/integration/sdr-oran-connector/sdr_grpc_server.py) - Bidirectional IQ streaming
- [LEO Simulator](03-Implementation/simulation/leo_ntn_simulator.py) - LEO NTN satellite simulator
- [DRL Trainer](03-Implementation/ai-ml-pipeline/training/drl_trainer.py) - Deep reinforcement learning pipeline
- [Traffic Steering xApp](03-Implementation/orchestration/nephio/packages/oran-ric/xapps/traffic-steering-xapp.py) - Intelligent xApp
- [Quantum Security](03-Implementation/security/pqc/quantum_safe_crypto.py) - NIST PQC implementation

### Reports and Analysis
- [LEO-SDR Integration](docs/reports/LEO-SDR-INTEGRATION-REPORT.md) - Integration implementation report
- [Architecture Compliance](docs/reports/ARCHITECTURE-COMPLIANCE-REPORT.md) - Architecture validation
- [Data Analysis Report](docs/reports/DETAILED-DATA-ANALYSIS-REPORT.md) - Performance analysis
- [Deployment Test Results](docs/deployment/REAL-DEPLOYMENT-TEST-REPORT.md) - Actual test results
- [Known Issues](docs/testing/KNOWN-ISSUES.md) - Documented limitations and bugs

---

## Development Workflow

### CI/CD Pipeline

Every commit triggers automated validation through GitHub Actions:

| Stage | Duration | Description |
|-------|----------|-------------|
| Code Quality | 22s | Black, isort, Pylint, Bandit security scanning |
| Infrastructure | 18s | Terraform syntax validation |
| Unit Tests | 18s | Pytest with syntax checks |
| PQC Tests | 10s | Post-Quantum Cryptography compliance |
| Docker Build | 1m35s | Multi-arch container build |
| Security Scan | 15s | Trivy vulnerability scanning |

**Total Pipeline Duration**: ~3 minutes

### Testing Strategy

```bash
# Run all tests
./scripts/test-all.sh

# Run specific component tests
cd tests/infrastructure
pytest test_core_services.py -v

# Run linting and formatting
pre-commit run --all-files
```

### Monitoring

```bash
# Start monitoring dashboard
./scripts/monitor.sh

# View service logs
docker-compose logs -f sdr-gateway

# Check service health
curl http://localhost:8000/health
```

---

## Limitations and Considerations

### Current Limitations

**Hardware Dependencies**:
- USRP X310 required for actual SDR operations ($7,500, not included)
- All SDR functionality currently uses simulated data
- Real signal processing cannot be validated without hardware

**Testing Coverage**:
- Unit test coverage at ~15% (target: 60-80%)
- Integration tests not fully implemented
- Performance metrics are theoretical, not measured on hardware
- End-to-end system testing pending

**Implementation Status**:
- Traffic Steering xApp requires O-RAN SC ricxappframe
- Some O-RAN components not validated on actual RIC
- Kubernetes deployments created but not fully tested
- Production security hardening needed

### Performance Notes

**Expected Performance** (theoretical, based on specifications):
- E2E Latency: 47-73ms (LEO), 267-283ms (GEO) - from 3GPP calculations
- Throughput: 80-95 Mbps sustained - estimated from DVB-S2 specs
- Packet Loss: <0.01% target
- Availability: 99.9% target

**Note**: These are theoretical estimates. Actual performance requires hardware validation.

### Cost Analysis

**Initial Investment** (estimated):
- USRP X310 with GPSDO and antenna: $23,500
- Server infrastructure: $12,000
- Networking equipment: $4,000
- Installation and configuration: $10,000
- **Total CAPEX**: ~$50,000

**Annual Operating Costs** (estimated):
- Cloud services (AWS EKS): $6,000
- Power and cooling: $3,600
- Network bandwidth: $2,400
- Satellite data subscription: $12,000
- Personnel (1 FTE): $80,000
- Maintenance and licenses: $10,000
- **Total Annual OPEX**: ~$114,000

**3-Year TCO**: Approximately $400,000

### Recommended Use Cases

**Suitable For**:
- Academic research and study
- Architecture reference and learning
- Concept validation and prototyping
- Development starting point for custom implementations

**Not Recommended For**:
- Immediate production deployment without further development
- Mission-critical applications without thorough testing
- Environments requiring certified hardware and software

---

## Contributing

This is a research project. For questions, collaboration, or contributions:

**Contact**: Hsiu-Chi Tsai
- Email: thc1006@ieee.org, hctsai@linux.com
- Facebook: https://www.facebook.com/thc1006

---

## Citation

If you use this project in your research, please cite:

```bibtex
@software{tsai2025sdr,
  title = {SDR-Based Cloud-Native Satellite Ground Station & O-RAN Integration},
  author = {Tsai, Hsiu-Chi},
  year = {2025},
  version = {3.0.0},
  url = {https://github.com/thc1006/sdr-o-ran-platform}
}
```

See [CITATION.cff](CITATION.cff) for detailed citation information.

---

## License

This project is a research and development platform. Licensing terms are subject to determination based on future requirements.

---

## Version History

| Version | Date | Key Features |
|---------|------|-------------|
| v0.1.0 | 2023-09 | Initial research and RunSpace competition submission |
| v2.0.0 | 2025-10-26 | MBSE models, SDR platform, O-RAN integration baseline |
| v3.0.0 | 2025-11-12 | LEO-SDR integration, AI/ML pipeline, quantum security, documentation reorganization |

---

**Last Updated**: 2025-11-12
**Maintained By**: Hsiu-Chi Tsai (thc1006@ieee.org)
