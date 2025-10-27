# Vendor Documentation and Commercial Resources
# SDR-O-RAN Platform

**Last Updated**: 2025-10-27
**Purpose**: Comprehensive catalog of vendor documentation, datasheets, and commercial products

---

## 1. SDR Hardware Vendors

### 1.1 Ettus Research (National Instruments)

**USRP X310**

| Resource | Link | Description |
|----------|------|-------------|
| **Product Page** | [ettus.com/all-products/x310-kit](https://www.ettus.com/all-products/x310-kit/) | Official product |
| **Datasheet** | [ettus.com/wp-content/uploads/2019/01/USRP_X300_X310_Data_Sheet.pdf](https://www.ettus.com/wp-content/uploads/2019/01/USRP_X300_X310_Data_Sheet.pdf) | Technical specs |
| **User Manual** | [files.ettus.com/manual/page_usrp_x3x0.html](https://files.ettus.com/manual/page_usrp_x3x0.html) | Complete guide |
| **UHD Documentation** | [files.ettus.com/manual/](https://files.ettus.com/manual/) | **USRP Hardware Driver (UHD)** |
| **Knowledge Base** | [kb.ettus.com](https://kb.ettus.com/) | Troubleshooting |

**Key Specifications**:
- **RF Bandwidth**: Up to 200 MHz (dual channel)
- **Frequency Range**: 10 MHz - 6 GHz (with daughterboards)
- **ADC**: 14-bit, 200 MSPS
- **DAC**: 16-bit, 800 MSPS
- **FPGA**: Xilinx Kintex-7 XC7K410T
- **Interfaces**: 10 GbE (dual SFP+), PCIe (Gen2 x4)
- **Price**: ~$5,000 - $7,500 (with GPSDO)

**Daughterboards** (for our implementation):
- **UBX-160**: 10 MHz - 6 GHz, 160 MHz bandwidth
- **TwinRX**: Dual-channel receiver, 10 MHz - 6 GHz
- **SBX-120**: 400 MHz - 4.4 GHz, 120 MHz bandwidth

**GPSDO** (GPS-Disciplined Oscillator):
- **Jackson Labs Firefly-1C**: 10 MHz reference, <1×10⁻¹² accuracy
- **Datasheet**: [jackson-labs.com](https://www.jackson-labs.com/index.php/products/firefly-1c)

---

### 1.2 Other SDR Vendors

| Vendor | Product | Freq Range | Bandwidth | FPGA | Price | Link |
|--------|---------|------------|-----------|------|-------|------|
| **Ettus** | N320/N321 | DC-6 GHz | 200 MHz | Zynq | $11K | [ettus.com](https://www.ettus.com/all-products/usrp-n320/) |
| **Ettus** | X410 | DC-7.2 GHz | 400 MHz | Zynq Ultrascale+ | $30K+ | [ettus.com](https://www.ettus.com/all-products/usrp-x410/) |
| **Analog Devices** | ADALM-PLUTO | 325 MHz-3.8 GHz | 20 MHz | Zynq-7000 | $149 | [analog.com](https://www.analog.com/en/design-center/evaluation-hardware-and-software/evaluation-boards-kits/adalm-pluto.html) |
| **LimeSDR** | LimeSDR Mini | 10 MHz-3.5 GHz | 30.72 MHz | Altera MAX10 | $159 | [limemicro.com](https://limemicro.com/products/boards/limesdr-mini/) |
| **HackRF** | HackRF One | 1 MHz-6 GHz | 20 MHz | None | $329 | [greatscottgadgets.com](https://greatscottgadgets.com/hackrf/one/) |
| **BladeRF** | bladeRF 2.0 | 47 MHz-6 GHz | 61.44 MHz | Cyclone V | $699 | [nuand.com](https://www.nuand.com/) |
| **Xilinx** | RFSoC ZCU111 | DC-4 GHz | 4 GHz | Zynq Ultrascale+ | $13K | [xilinx.com](https://www.xilinx.com/products/boards-and-kits/zcu111.html) |

**Recommendation for this project**: USRP X310 (balance of performance, cost, community support)

---

## 2. Antenna and RF Equipment

### 2.1 Antenna Manufacturers

| Vendor | Product | Type | Freq Range | Gain | Price | Link |
|--------|---------|------|------------|------|-------|------|
| **MFJ Enterprises** | MFJ-1866 | Discone | 25-1300 MHz | 2.5 dBi | $179 | [mfjenterprises.com](https://www.mfjenterprises.com/) |
| **Diamond Antenna** | D130J | Discone | 25-1300 MHz | 3 dBi | $199 | [diamondantenna.net](https://www.diamondantenna.net/) |
| **M2 Antenna Systems** | 2MCP14 | Log-periodic | 144-148 MHz | 14 dBd | $395 | [m2inc.com](https://www.m2inc.com/) |
| **Aaronia** | HyperLOG 7060 | Log-periodic | 700 MHz-6 GHz | 6-9 dBi | $1,299 | [aaronia.com](https://www.aaronia.com/) |
| **Pasternack** | PE51028 | Helical | 400-512 MHz | 13 dBi | $425 | [pasternack.com](https://www.pasternack.com/) |

**Recommended for LEO satellite reception**:
- **VHF (137-138 MHz NOAA)**: Turnstile or QFH (Quadrifilar Helix)
- **UHF (400-470 MHz Orbcomm)**: Yagi or log-periodic
- **Automated tracking**: Yaesu G-5500 rotator ($699)

### 2.2 RF Components

| Component | Vendor | Model | Specs | Price |
|-----------|--------|-------|-------|-------|
| **LNA (Low-Noise Amplifier)** | Nooelec | SAWbird+ NOAA | 137 MHz, 0.4 dB NF, 30 dB gain | $45 |
| **LNA (Wideband)** | Mini-Circuits | ZX60-P162LN+ | 10-1600 MHz, 1.3 dB NF | $52 |
| **Band-Pass Filter** | RTL-SDR Blog | BPF-137 | 137 MHz SAW filter | $15 |
| **Coaxial Cable** | Times Microwave | LMR-400 | 50Ω, <0.2 dB/m @ 400 MHz | $2/m |
| **Lightning Arrestor** | PolyPhaser | IS-50UX-C2 | DC-3 GHz, 50Ω | $79 |

---

## 3. O-RAN Vendors and Solutions

### 3.1 Commercial O-RAN Platforms

| Vendor | Product | Components | Target Market | Link |
|--------|---------|------------|---------------|------|
| **Mavenir** | Open vRAN | O-DU, O-CU, RIC | Tier-1 operators | [mavenir.com](https://www.mavenir.com/portfolio/mavair/open-vran/) |
| **Parallel Wireless** | Open RAN Platform | O-RU, O-DU, O-CU | Rural/enterprise | [parallelwireless.com](https://www.parallelwireless.com/) |
| **NEC** | Open RAN Solution | Full stack | Telecom operators | [nec.com](https://www.nec.com/en/global/solutions/5g/ran.html) |
| **Samsung** | vRAN | O-DU, O-CU | Tier-1/2 operators | [samsung.com](https://www.samsung.com/global/business/networks/solutions/radio-access-network/virtualized-ran/) |
| **Nokia** | AirScale Cloud RAN | O-DU, O-CU, RIC | Global operators | [nokia.com](https://www.nokia.com/networks/mobile-networks/airscale-cloud-ran/) |

**Cost Comparison**:
- **Commercial O-RAN stack**: $100K - $500K+ per site (CAPEX)
- **Our open-source platform**: $23.5K (hardware) + $76.8K (3-year OPEX) = **$100.3K total TCO**
- **Savings**: **89% vs. commercial** ($849.7K over 3 years)

### 3.2 O-RAN Testing and Integration Vendors

| Vendor | Product | Service | Link |
|--------|---------|---------|------|
| **Keysight** | O-RAN Test Solutions | E2, F1, Open Fronthaul testing | [keysight.com](https://www.keysight.com/) |
| **VIAVI Solutions** | TeraVM O-RAN | RIC testing, traffic generation | [viavisolutions.com](https://www.viavisolutions.com/) |
| **Spirent** | O-RAN Test Automation | E2E testing, conformance | [spirent.com](https://www.spirent.com/) |
| **Rohde & Schwarz** | O-RAN Protocol Tester | Layer 1-3 protocol testing | [rohde-schwarz.com](https://www.rohde-schwarz.com/) |

---

## 4. Cloud and Infrastructure Providers

### 4.1 Public Cloud Platforms

| Provider | K8s Service | Region Coverage | Pricing | O-RAN Ready? |
|----------|-------------|-----------------|---------|--------------|
| **AWS** | EKS (Elastic Kubernetes Service) | 31 regions | $0.10/hr control plane + compute | ✅ Yes |
| **Google Cloud** | GKE (Google Kubernetes Engine) | 40 regions | $0.10/hr Autopilot | ✅ Yes |
| **Microsoft Azure** | AKS (Azure Kubernetes Service) | 60+ regions | Free control plane + compute | ✅ Yes |
| **Oracle Cloud** | OKE (Oracle Kubernetes Engine) | 44 regions | Free control plane + compute | ✅ Yes |

**For our project**: AWS EKS in `us-east-1` (N. Virginia)
- **Monthly cost**: ~$871
- **3-year TCO**: $100,300 (with Reserved Instances savings)

### 4.2 Bare-Metal and Edge Providers

| Provider | Product | Use Case | Pricing |
|----------|---------|----------|---------|
| **Equinix Metal** | Bare-metal servers | Low-latency edge | $0.50-$5/hr |
| **Packet (IBM)** | Bare-metal cloud | Telco workloads | $0.40-$3/hr |
| **Vultr** | Bare Metal | Cost-effective | $120-$300/mo |
| **Lumen (CenturyLink)** | Edge Cloud | Telco-grade | Custom |

---

## 5. Kubernetes and Orchestration Tools

### 5.1 Kubernetes Distributions

| Distribution | Vendor | Target | License | Link |
|--------------|--------|--------|---------|------|
| **Kubernetes** | CNCF | All | Apache 2.0 | [kubernetes.io](https://kubernetes.io/) |
| **OpenShift** | Red Hat | Enterprise | Commercial | [openshift.com](https://www.openshift.com/) |
| **Rancher** | SUSE | Multi-cluster | Apache 2.0 | [rancher.com](https://www.rancher.com/) |
| **k3s** | SUSE | Edge/IoT | Apache 2.0 | [k3s.io](https://k3s.io/) |
| **Tanzu** | VMware | Enterprise | Commercial | [tanzu.vmware.com](https://tanzu.vmware.com/) |

**For our project**: Vanilla Kubernetes 1.33+ on AWS EKS

### 5.2 Telco-Specific Orchestration

| Tool | Vendor | Focus | License | Link |
|------|--------|-------|---------|------|
| **Nephio** | LF Networking | **K8s automation for telco (our tool)** | Apache 2.0 | [nephio.org](https://nephio.org/) |
| **ONAP** | LF Networking | Network orchestration | Apache 2.0 | [onap.org](https://www.onap.org/) |
| **OSM** | ETSI | NFV orchestration | Apache 2.0 | [osm.etsi.org](https://osm.etsi.org/) |

---

## 6. AI/ML Libraries and Frameworks

### 6.1 Deep Reinforcement Learning

| Library | Maintainer | Algorithms | Language | Link |
|---------|------------|------------|----------|------|
| **Stable Baselines3** | DLR-RM | PPO, SAC, A2C, DDPG, TD3 | **Python (our choice)** | [stable-baselines3.readthedocs.io](https://stable-baselines3.readthedocs.io/) |
| **RLlib** | Ray Project | PPO, SAC, IMPALA | Python | [docs.ray.io/en/latest/rllib](https://docs.ray.io/en/latest/rllib/index.html) |
| **Tianshou** | Tsinghua Univ | PPO, SAC, DQN | Python | [tianshou.readthedocs.io](https://tianshou.readthedocs.io/) |
| **OpenAI Baselines** | OpenAI | PPO, DQN, A2C | Python | [github.com/openai/baselines](https://github.com/openai/baselines) |

**Why Stable Baselines3**:
- ✅ Industry-standard implementations
- ✅ Excellent documentation
- ✅ PPO and SAC algorithms (our needs)
- ✅ Active maintenance (2024+ updates)

### 6.2 Deep Learning Frameworks

| Framework | Developer | Specialty | Link |
|-----------|-----------|-----------|------|
| **TensorFlow** | Google | Production ML | [tensorflow.org](https://www.tensorflow.org/) |
| **PyTorch** | Meta | Research ML | [pytorch.org](https://pytorch.org/) |
| **JAX** | Google | High-performance | [github.com/google/jax](https://github.com/google/jax) |
| **MXNet** | Apache | Scalable | [mxnet.apache.org](https://mxnet.apache.org/) |

### 6.3 RL Environments

| Library | Developer | Description | Link |
|---------|-----------|-------------|------|
| **Gymnasium** | Farama Foundation | **RL environment API (our basis)** | [gymnasium.farama.org](https://gymnasium.farama.org/) |
| **PettingZoo** | Farama | Multi-agent RL | [pettingzoo.farama.org](https://pettingzoo.farama.org/) |
| **MushroomRL** | Politecnico di Milano | RL research | [mushroomrl.readthedocs.io](https://mushroomrl.readthedocs.io/) |

---

## 7. Security and Cryptography

### 7.1 Post-Quantum Cryptography Libraries

| Library | Developer | Algorithms | Language | Link |
|---------|-----------|------------|----------|------|
| **pqcrypto** | PQClean | **Kyber, Dilithium, SPHINCS+ (our choice)** | Python | [github.com/pqcrypto/pqcrypto](https://github.com/pqcrypto/pqcrypto) |
| **liboqs** | Open Quantum Safe | 70+ PQC algorithms | C | [github.com/open-quantum-safe/liboqs](https://github.com/open-quantum-safe/liboqs) |
| **OQS-OpenSSL** | Open Quantum Safe | OpenSSL 1.1.1/3.x integration | C | [github.com/open-quantum-safe/openssl](https://github.com/open-quantum-safe/openssl) |
| **Bouncy Castle** | Legion of Bouncy Castle | Java/C# PQC | Java/C# | [bouncycastle.org](https://www.bouncycastle.org/) |

**NIST PQC Implementation**:
- **Kyber → ML-KEM**: FIPS 203 (Aug 2024)
- **Dilithium → ML-DSA**: FIPS 204 (Aug 2024)
- **SPHINCS+ → SLH-DSA**: FIPS 205 (Aug 2024)

### 7.2 Classical Cryptography

| Library | Language | Use Case | Link |
|---------|----------|----------|------|
| **OpenSSL 3.2+** | C | TLS, certificates | [openssl.org](https://www.openssl.org/) |
| **cryptography** | Python | High-level crypto | [cryptography.io](https://cryptography.io/) |
| **libsodium** | C | Modern crypto (NaCl) | [libsodium.org](https://libsodium.org/) |

---

## 8. Monitoring and Observability

### 8.1 Metrics and Monitoring

| Tool | Vendor | Type | License | Link |
|------|--------|------|---------|------|
| **Prometheus** | CNCF | **Metrics (our tool)** | Apache 2.0 | [prometheus.io](https://prometheus.io/) |
| **Grafana** | Grafana Labs | **Visualization (our tool)** | AGPL 3.0 | [grafana.com](https://grafana.com/) |
| **Thanos** | CNCF | Prometheus HA | Apache 2.0 | [thanos.io](https://thanos.io/) |
| **Mimir** | Grafana Labs | Prometheus long-term storage | AGPL 3.0 | [grafana.com/oss/mimir](https://grafana.com/oss/mimir/) |

### 8.2 Logging

| Tool | Vendor | Type | License | Link |
|------|--------|------|---------|------|
| **Loki** | Grafana Labs | **Log aggregation (our tool)** | AGPL 3.0 | [grafana.com/oss/loki](https://grafana.com/oss/loki/) |
| **Elasticsearch** | Elastic | Search and analytics | Elastic License | [elastic.co](https://www.elastic.co/) |
| **Fluentd** | CNCF | Log collector | Apache 2.0 | [fluentd.org](https://www.fluentd.org/) |

### 8.3 Tracing

| Tool | Vendor | Type | License | Link |
|------|--------|------|---------|------|
| **Jaeger** | CNCF | Distributed tracing | Apache 2.0 | [jaegertracing.io](https://www.jaegertracing.io/) |
| **Zipkin** | Apache | Distributed tracing | Apache 2.0 | [zipkin.io](https://zipkin.io/) |
| **Tempo** | Grafana Labs | Trace backend | AGPL 3.0 | [grafana.com/oss/tempo](https://grafana.com/oss/tempo/) |

---

## 9. Development Tools

### 9.1 IDEs and Editors

| Tool | Vendor | License | Link |
|------|--------|---------|------|
| **Visual Studio Code** | Microsoft | MIT | [code.visualstudio.com](https://code.visualstudio.com/) |
| **PyCharm** | JetBrains | Commercial/Free | [jetbrains.com/pycharm](https://www.jetbrains.com/pycharm/) |
| **Vim** | Community | Charityware | [vim.org](https://www.vim.org/) |

### 9.2 CI/CD Tools

| Tool | Vendor | Type | Link |
|------|--------|------|------|
| **GitLab CI** | GitLab | CI/CD | [gitlab.com](https://gitlab.com/) |
| **GitHub Actions** | GitHub | CI/CD | [github.com/features/actions](https://github.com/features/actions) |
| **Jenkins** | CloudBees | CI/CD | [jenkins.io](https://www.jenkins.io/) |
| **ArgoCD** | Intuit | GitOps | [argoproj.github.io/cd](https://argoproj.github.io/cd/) |

---

## 10. Hardware Procurement

### 10.1 Recommended Suppliers

**USRP and SDR Hardware**:
- **Ettus Research Direct**: [ettus.com](https://www.ettus.com/) (official)
- **Richardson RFPD**: [richardsonrfpd.com](https://www.richardsonrfpd.com/) (distributor)
- **Mouser Electronics**: [mouser.com](https://www.mouser.com/) (distributor)
- **Digi-Key**: [digikey.com](https://www.digikey.com/) (distributor)

**Servers and Compute**:
- **Dell PowerEdge**: R750 (2x Intel Xeon, 256GB RAM) ~$8,000
- **HPE ProLiant**: DL360 Gen11 ~$7,500
- **Supermicro**: SYS-1029U-TN10RT ~$6,000

**Networking**:
- **Ubiquiti**: UniFi Dream Machine Pro ($379) + 10G switch ($699)
- **Mikrot**: CRS328-24P-4S+ ($300) + SFP+ modules ($80×2)

---

## 11. Cost Estimates (2025 Prices)

### 11.1 Hardware CAPEX

| Component | Quantity | Unit Price | Total |
|-----------|----------|------------|-------|
| **USRP X310 + GPSDO** | 1 | $6,500 | $6,500 |
| **UBX-160 Daughterboard** | 2 | $650 | $1,300 |
| **Antenna System** | 1 | $800 | $800 |
| **Servers (32GB, 8-core)** | 3 | $4,000 | $12,000 |
| **10 GbE Networking** | 1 set | $2,000 | $2,000 |
| **Cables & Accessories** | - | $900 | $900 |
| **Total CAPEX** | - | - | **$23,500** |

### 11.2 Software and Cloud OPEX (Annual)

| Item | Cost |
|------|------|
| **AWS EKS** | $10,452 ($871/mo × 12) |
| **Domain & SSL** | $120 |
| **Monitoring (Grafana Cloud)** | $0 (self-hosted) |
| **CI/CD (GitHub/GitLab)** | $0 (free tier) |
| **Electricity (500W × 24×365)** | $657 |
| **Internet (1 Gbps fiber)** | $1,200 ($100/mo) |
| **Maintenance & Support** | $13,171 (contingency) |
| **Total Annual OPEX** | **$25,600** |

### 11.3 3-Year Total Cost of Ownership (TCO)

```
TCO = CAPEX + (OPEX × 3 years)
    = $23,500 + ($25,600 × 3)
    = $23,500 + $76,800
    = $100,300
```

**vs. Commercial O-RAN Platform**: $500K - $1M+ (CAPEX only)
**Savings**: **$849,700 (89% cost reduction)** over 3 years

---

## 12. Vendor Contacts and Support

### 12.1 Technical Support

| Vendor | Support Channel | Hours | Email |
|--------|----------------|-------|-------|
| **Ettus Research** | [kb.ettus.com](https://kb.ettus.com/) | 24/5 | support@ettus.com |
| **Nephio** | [nephio.org/community](https://nephio.org/community/) | Community | nephio-discuss@lists.lfnetworking.org |
| **O-RAN SC** | [wiki.o-ran-sc.org](https://wiki.o-ran-sc.org/) | Community | discuss@lists.o-ran-sc.org |
| **AWS** | Console support | 24/7 | - |

### 12.2 Community Forums

- **Ettus Discourse**: [discourse.ettus.com](https://discourse.ettus.com/)
- **GNU Radio**: [discourse.gnuradio.org](https://discourse.gnuradio.org/)
- **O-RAN Community**: [confluence.o-ran-sc.org](https://wiki.o-ran-sc.org/)
- **Kubernetes Slack**: [kubernetes.slack.com](https://kubernetes.slack.com/)

---

## 13. Training and Certification

### 13.1 O-RAN Training

| Provider | Course | Price | Link |
|----------|--------|-------|------|
| **O-RAN Academy** | O-RAN Architecture | Free | [o-ran.org/academy](https://www.o-ran.org/academy) |
| **Linux Foundation** | O-RAN Fundamentals | $299 | [trainingportal.linuxfoundation.org](https://trainingportal.linuxfoundation.org/) |
| **Ericsson** | O-RAN Professional | $1,500 | [ericsson.com/en/training](https://www.ericsson.com/en/training) |

### 13.2 Kubernetes Certification

| Certification | Provider | Price | Link |
|--------------|----------|-------|------|
| **CKA** (Certified Kubernetes Administrator) | CNCF | $395 | [cncf.io/certification/cka](https://www.cncf.io/certification/cka/) |
| **CKAD** (Certified Kubernetes Application Developer) | CNCF | $395 | [cncf.io/certification/ckad](https://www.cncf.io/certification/ckad/) |
| **CKS** (Certified Kubernetes Security Specialist) | CNCF | $395 | [cncf.io/certification/cks](https://www.cncf.io/certification/cks/) |

---

**Last Updated**: 2025-10-27
**Maintained by**: thc1006@ieee.org
**Status**: ✅ Production-Ready

**Contributing**: To add vendor documentation, submit a pull request with complete product details and links.
