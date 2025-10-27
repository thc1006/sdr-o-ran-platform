# SDR-Based Cloud-Native Satellite Ground Station & O-RAN Integration for NTN Communications
# 基於雲原生之 SDR 基頻處理地面站和 O-RAN 基站整合應用於 NTN 通訊

**Author**: 蔡秀吉 (Hsiu-Chi Tsai)
**Project Type**: MBSE-Based Technical Whitepaper & Feasibility Study
**Last Updated**: 2025-10-27
**Status**: Active Development

---

## 📋 Project Overview

This project presents a comprehensive, implementable solution for integrating Software-Defined Radio (SDR) satellite ground stations with cloud-native O-RAN architecture for Non-Terrestrial Network (NTN) communications. The project follows **Model-Based Systems Engineering (MBSE)** methodology and leverages 2025 state-of-the-art technologies.

### Key Innovations
- ✅ Cloud-native CNF-based architecture
- ✅ Multi-band phased array antenna support (C/Ku/Ka)
- ✅ USRP + GNU Radio SDR platform
- ✅ Nephio-based automation and orchestration
- ✅ O-RAN DU/CU/RIC integration
- ✅ 3GPP Release 18/19 NTN compliance
- ✅ OpenAirInterface 5G-NTN implementation

---

## 📂 Project Structure

```
SDR/
├── README.md                              # This file
├── 00-MBSE-Models/                        # MBSE system models (SysML v2)
│   ├── requirements/                      # System requirements models
│   ├── architecture/                      # System architecture models
│   ├── behavior/                          # Behavioral models & workflows
│   └── parametric/                        # Parametric models & constraints
├── 01-Architecture-Analysis/              # Multi-approach integration analysis
│   ├── approach-01-nephio-native.md       # Nephio-native approach
│   ├── approach-02-onap-orchestration.md  # ONAP orchestration approach
│   ├── approach-03-hybrid.md              # Hybrid approach
│   ├── approach-04-k8s-operator.md        # Pure K8s Operator approach
│   └── comparison-matrix.md               # Comprehensive pros/cons analysis
├── 02-Technical-Specifications/           # Detailed technical specs
│   ├── system-requirements.md             # System requirements specification
│   ├── interface-specifications.md        # API & interface specs
│   ├── sdr-specifications.md              # SDR hardware/software specs
│   ├── oran-specifications.md             # O-RAN component specs
│   └── ntn-3gpp-compliance.md             # 3GPP NTN compliance details
├── 03-Implementation/                     # Simulated & real implementations
│   ├── sdr-platform/                      # SDR implementation
│   │   ├── gnuradio-flowgraphs/          # GNU Radio signal processing
│   │   ├── usrp-configs/                 # USRP device configurations
│   │   └── api-gateway/                  # SDR API gateway
│   ├── oran-cnfs/                         # O-RAN CNF implementations
│   │   ├── o-du/                         # O-RAN DU CNF
│   │   ├── o-cu-cp/                      # O-RAN CU-CP CNF
│   │   ├── o-cu-up/                      # O-RAN CU-UP CNF
│   │   └── ric/                          # RAN Intelligent Controller
│   ├── orchestration/                     # Orchestration layer
│   │   ├── nephio/                       # Nephio configurations
│   │   ├── kubernetes/                   # K8s manifests
│   │   └── onap/                         # ONAP blueprints
│   └── integration/                       # Integration code
│       ├── sdr-oran-connector/           # SDR-to-O-RAN connector
│       └── api-adapters/                 # API adaptation layer
├── 04-Deployment/                         # Deployment configurations
│   ├── infrastructure/                    # Infrastructure as Code
│   ├── ci-cd/                            # CI/CD pipelines
│   └── monitoring/                       # Monitoring & observability
├── 05-Documentation/                      # Comprehensive documentation
│   ├── whitepaper.md                     # Main technical whitepaper
│   ├── deployment-guide.md               # Deployment guide
│   ├── operations-manual.md              # Operations manual
│   └── gap-analysis.md                   # Unimplemented components
├── 06-References/                         # Reference materials
│   ├── standards/                        # 3GPP, O-RAN specs
│   ├── research-papers/                  # Academic papers
│   └── vendor-docs/                      # Vendor documentation
└── 07-Legacy-Docs/                       # Original project documents
    ├── SDR Platform -低軌衛星地面接收站的解決方案.md
    ├── 基於雲原生之-SDN-基頻處理地面站和-O-RAN-基站整合應用於NTN-通訊 (1).pdf
    ├── 軟體自定義無線電.pdf
    ├── 20231013最終.pdf
    └── 1.pdf
```

---

## 🎯 Project Objectives

1. **Maximum Feasibility**: Ensure all proposed solutions can be implemented with 2025 technology
2. **MBSE Methodology**: Apply rigorous Model-Based Systems Engineering throughout
3. **Multi-Approach Analysis**: Evaluate multiple integration architectures with pros/cons
4. **Simulated Implementation**: Provide working code examples wherever possible
5. **Gap Analysis**: Clearly identify unimplemented components and future work
6. **Industry Standards**: Comply with 3GPP Release 18/19, O-RAN Alliance specs

---

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (v1.28+)
- USRP B210/X310 SDR hardware
- GNU Radio 3.10+
- Nephio R1 or ONAP Montreal+
- Multi-band antenna system (C/Ku/Ka)

### Installation
```bash
# Coming soon - see 05-Documentation/deployment-guide.md
```

---

## 📊 Technology Stack

### SDR Platform
- **Hardware**: USRP B210/X310
- **Software**: GNU Radio 3.10, gr-satellites
- **Languages**: Python 3.11, C++17

### O-RAN Components
- **Platform**: OpenAirInterface (OAI) 5G-NTN
- **RIC**: OSC Near-RT RIC
- **SMO**: ONAP or Nephio

### Cloud-Native Infrastructure
- **Orchestration**: Kubernetes 1.28+
- **CNF Management**: Nephio R1
- **Service Mesh**: Istio 1.20+
- **Observability**: Prometheus, Grafana, Jaeger

### Standards Compliance
- **3GPP**: Release 18 (NTN baseline), Release 19 (RedCap, ISL)
- **O-RAN**: O-RAN.WG1-4 specifications
- **ETSI**: NFV MANO standards

---

## 📖 Documentation

- [Architecture Analysis](01-Architecture-Analysis/comparison-matrix.md) - Comprehensive comparison of integration approaches
- [Technical Whitepaper](05-Documentation/whitepaper.md) - Main technical document
- [Deployment Guide](05-Documentation/deployment-guide.md) - Step-by-step deployment instructions
- [Gap Analysis](05-Documentation/gap-analysis.md) - Unimplemented components and roadmap

---

## 🤝 Contributing

This is a research and feasibility study project. For questions or collaboration:

**Contact**: 蔡秀吉 (Hsiu-Chi Tsai)
- Email: hctsai@linux.com, thc1006@ieee.org
- Facebook: https://www.facebook.com/thc1006

---

## 📜 License

This project is a technical whitepaper and research study. Specific licensing terms to be determined based on commercialization requirements.

---

## 🔖 Version History

- **v0.1.0** (2023-09): Initial RunSpace competition submission
- **v2.0.0** (2025-10-27): MBSE-based comprehensive feasibility study

---

**Note**: This project represents a comprehensive feasibility study and technical whitepaper. Implementation status is clearly marked throughout the documentation. See `05-Documentation/gap-analysis.md` for details on simulated vs. real implementations.
