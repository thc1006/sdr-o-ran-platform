# Research Papers and Academic Publications
# SDR-O-RAN Platform

**Last Updated**: 2025-10-27
**Purpose**: Comprehensive catalog of academic research, white papers, and technical articles

---

## 1. Non-Terrestrial Networks (NTN)

### 1.1 Foundational Papers

| Title | Authors | Venue | Year | DOI/Link |
|-------|---------|-------|------|----------|
| **Non-Terrestrial Networks in the 6G Era: Challenges and Opportunities** | Giordani et al. | IEEE Network | 2021 | [10.1109/MNET.011.2000493](https://doi.org/10.1109/MNET.011.2000493) |
| **Satellite Communications Integration with Terrestrial Networks: Challenges and Opportunities** | Centenaro et al. | IEEE Access | 2021 | [10.1109/ACCESS.2021.3051252](https://doi.org/10.1109/ACCESS.2021.3051252) |
| **3GPP NTN: Enabling Satellite Communications in 5G and Beyond** | Rui et al. | IEEE Communications Magazine | 2022 | [10.1109/MCOM.001.2100869](https://doi.org/10.1109/MCOM.001.2100869) |

### 1.2 OpenAirInterface NTN Research

| Title | Authors | Venue | Year | Link |
|-------|---------|-------|------|------|
| **OpenAirInterface as a platform for 5G-NTN Research and Experimentation** | Sami et al. | ICSSC 2023 | 2023 | [IEEE Xplore](https://ieeexplore.ieee.org/document/10056682) |
| **Field Trial of a 5G Non-Terrestrial Network Using OpenAirInterface** | Bertaux et al. | IEEE PIMRC 2022 | 2022 | [ResearchGate](https://www.researchgate.net/publication/360645993) |
| **Driving Innovation in 6G Wireless Technologies: The OpenAirInterface Approach** | Nikaein et al. | arXiv | 2024 | [2412.13295](https://arxiv.org/abs/2412.13295) |

### 1.3 LEO/GEO Satellite Communications

| Title | Authors | Venue | Year | Key Contribution |
|-------|---------|-------|------|------------------|
| **Exploring the Performance of Transparent 5G NTN Architectures Based on Operational Mega-Constellations** | Azari et al. | Future Internet | 2023 | Starlink/OneWeb performance analysis |
| **5G-NTN GEO-based Over-The-Air Demonstrator** | Hofbauer et al. | ORBilu | 2023 | Real-world GEO satellite testing |
| **Latency Analysis for 5G NTN with LEO Satellites** | Wang et al. | IEEE Trans. Wireless Comm. | 2022 | Propagation delay modeling |

---

## 2. O-RAN Architecture and Optimization

### 2.1 O-RAN Fundamentals

| Title | Authors | Venue | Year | Focus Area |
|-------|---------|-------|------|------------|
| **O-RAN: Towards an Open and Smart RAN** | Polese et al. | IEEE Networks | 2020 | O-RAN overview |
| **Understanding O-RAN: Architecture, Interfaces, and Ecosystem** | Bonati et al. | IEEE Comm. Surveys | 2023 | **Comprehensive O-RAN survey (170+ pages)** |
| **Open RAN Architecture for 5G and Beyond** | Alliance O-RAN | White Paper | 2024 | Official O-RAN architecture |

### 2.2 Near-RT RIC and xApps

| Title | Authors | Venue | Year | Implementation |
|-------|---------|-------|------|----------------|
| **xApp Development for O-RAN: A Tutorial** | D'Oro et al. | IEEE Comm. Mag. | 2023 | xApp programming guide |
| **E2 Service Model Design for O-RAN** | Polese et al. | IEEE INFOCOM 2023 | 2023 | E2SM-KPM, E2SM-RC design |
| **RAN Intelligent Controller (RIC) Architecture** | Alliance O-RAN | Tech Report | 2024 | RIC platform specification |

### 2.3 Performance Optimization

| Title | Authors | Venue | Year | Optimization Target |
|-------|---------|-------|------|---------------------|
| **Traffic Steering in O-RAN: Challenges and Solutions** | Villa et al. | IEEE Trans. Network | 2024 | Handover optimization |
| **Resource Allocation in O-RAN Using AI/ML** | Chen et al. | IEEE GLOBECOM | 2023 | PRB allocation |
| **Energy Efficiency in O-RAN Networks** | O-RAN Alliance | White Paper | 2025 | Cell sleep modes, carrier shutdown |

---

## 3. AI/ML for RAN Optimization

### 3.1 Deep Reinforcement Learning (DRL)

| Title | Authors | Venue | Year | Algorithm |
|-------|---------|-------|------|-----------|
| **Deep Reinforcement Learning for Resource Management in 5G Networks** | Zhang et al. | IEEE Trans. Vehicular Tech. | 2022 | DQN, A3C |
| **Proximal Policy Optimization Algorithms** | Schulman et al. | arXiv | 2017 | **PPO (used in our implementation)** |
| **Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL** | Haarnoja et al. | ICML 2018 | 2018 | **SAC (used in our implementation)** |

### 3.2 RAN-Specific AI/ML Applications

| Title | Authors | Venue | Year | Application |
|-------|---------|-------|------|-------------|
| **Gymnasium: A Standard Interface for Reinforcement Learning Environments** | Towers et al. | arXiv | 2023 | **RL environment framework (our basis)** |
| **Stable Baselines3: Reliable RL Implementations** | Raffin et al. | JMLR | 2021 | **PPO/SAC library (our implementation)** |
| **Explainable AI for Wireless Networks: SHAP-Based Approach** | Liu et al. | IEEE Comm. Lett. | 2023 | XAI for transparency |

### 3.3 AI/ML for NTN

| Title | Authors | Venue | Year | Contribution |
|-------|---------|-------|------|---------------|
| **Machine Learning for Satellite Communications: A Survey** | Ortiz-Gomez et al. | IEEE Comm. Surveys | 2023 | ML for NTN |
| **DRL-Based Handover in LEO Satellite Networks** | Wang et al. | IEEE JSAC | 2024 | Doppler-aware handover |
| **Predictive Resource Allocation in NTN Using LSTM** | Patel et al. | IEEE Trans. Aerospace | 2024 | Time-series prediction |

---

## 4. Post-Quantum Cryptography (PQC)

### 4.1 NIST PQC Competition

| Title | Authors | Venue | Year | Algorithm |
|-------|---------|-------|------|-----------|
| **CRYSTALS-Kyber: A CCA-Secure Module-Lattice-Based KEM** | Bos et al. | Euro S&P 2018 | 2018 | **Kyber (now ML-KEM in FIPS 203)** |
| **CRYSTALS-Dilithium: A Lattice-Based Digital Signature Scheme** | Ducas et al. | IACR Trans. 2018 | 2018 | **Dilithium (now ML-DSA in FIPS 204)** |
| **SPHINCS+: A Stateless Hash-Based Signature Scheme** | Bernstein et al. | CCS 2019 | 2019 | SLH-DSA (FIPS 205) |

### 4.2 PQC Deployment

| Title | Authors | Venue | Year | Focus |
|-------|---------|-------|------|-------|
| **Hybrid Post-Quantum TLS 1.3: Combining Classical and PQC** | Stebila et al. | NDSS 2021 | 2021 | **Hybrid crypto (our approach)** |
| **Performance Analysis of NIST PQC Finalists** | Alagic et al. | NIST | 2024 | Benchmarks |
| **PQC Migration Strategies for 5G Networks** | Khan et al. | IEEE Comm. Mag. | 2024 | 5G/6G PQC deployment |

### 4.3 Lattice-Based Cryptography

| Title | Authors | Venue | Year | Theory |
|-------|---------|-------|------|--------|
| **A Decade of Lattice Cryptography** | Peikert | Foundations & Trends | 2016 | Comprehensive survey |
| **Learning With Errors: Security Foundations** | Regev | STOC 2005 | 2005 | LWE problem |
| **Module Lattices for Post-Quantum Cryptography** | Langlois & Stehlé | ASIACRYPT 2015 | 2015 | Module-LWE |

---

## 5. Software-Defined Radio (SDR)

### 5.1 SDR Platforms

| Title | Authors | Venue | Year | Platform |
|-------|---------|-------|------|----------|
| **USRP: A Universal Software Radio Peripheral** | Ettus Research | White Paper | 2023 | **USRP X310 (our hardware)** |
| **GNU Radio: The Free & Open Source Radio Ecosystem** | Rondeau | IEEE Comm. Mag. | 2013 | GNU Radio framework |
| **VITA 49 Digital IF Interoperability Standard** | VITA | Standard | 2017 | **VITA 49.2 (our protocol)** |

### 5.2 Satellite Signal Processing

| Title | Authors | Venue | Year | Application |
|-------|---------|-------|------|-------------|
| **Low-Cost Ground Station for Satellite Communications** | Kulu et al. | IEEE Access | 2021 | Amateur satellite reception |
| **Doppler Compensation Techniques for LEO Satellites** | Smith et al. | IEEE Trans. Aerospace | 2020 | Frequency correction |
| **Digital Signal Processing for Satellite Communications** | Sklar | Comm. Eng. | 2001 | Classic DSP reference |

---

## 6. Cloud-Native and Orchestration

### 6.1 Kubernetes and CNF

| Title | Authors | Venue | Year | Topic |
|-------|---------|-------|------|-------|
| **Kubernetes: Up and Running (3rd Edition)** | Hightower et al. | O'Reilly | 2022 | K8s fundamentals |
| **Cloud Native Patterns** | Davis | Manning | 2019 | Microservices patterns |
| **Nephio: Kubernetes-Based Automation for Telco** | Nephio Community | White Paper | 2024 | **Nephio orchestration (our tool)** |

### 6.2 Service Mesh

| Title | Authors | Venue | Year | Technology |
|-------|---------|-------|------|------------|
| **Istio: Service Mesh for Microservices** | Morgan & Merkel | O'Reilly | 2022 | Istio architecture |
| **Benchmarking Service Meshes** | CNCF | Tech Report | 2023 | Performance comparison |

---

## 7. gRPC and Protocol Buffers

### 7.1 gRPC Architecture

| Title | Authors | Venue | Year | Focus |
|-------|---------|-------|------|-------|
| **gRPC: A High-Performance, Open-Source RPC Framework** | Google | White Paper | 2024 | **gRPC overview (our data plane)** |
| **Protocol Buffers v3: Language Guide** | Google | Documentation | 2024 | Protobuf schema design |
| **HTTP/2 in Action** | Pollard | Manning | 2019 | HTTP/2 fundamentals |

### 7.2 Performance Optimization

| Title | Authors | Venue | Year | Optimization |
|-------|---------|-------|------|--------------|
| **gRPC Performance Best Practices** | Google Cloud | Tech Report | 2024 | Tuning guide |
| **Evaluating gRPC for High-Performance Networking** | Wang et al. | IEEE INFOCOM | 2021 | Benchmarks |

---

## 8. System Design and Performance

### 8.1 Real-Time Systems

| Title | Authors | Venue | Year | Topic |
|-------|---------|-------|------|-------|
| **Real-Time Systems Design and Analysis** | Laplante | Wiley | 2023 | RT constraints |
| **Latency Numbers Every Programmer Should Know** | Dean | Google | 2020 | Latency reference |

### 8.2 Performance Benchmarking

| Title | Authors | Venue | Year | Metrics |
|-------|---------|-------|------|---------|
| **Benchmarking 5G RAN Performance** | Nokia | White Paper | 2024 | KPIs, SLAs |
| **End-to-End Latency in 5G Networks** | Ericsson | Tech Report | 2023 | Latency breakdown |

---

## 9. White Papers and Industry Reports

### 9.1 O-RAN Alliance

| Title | Date | Topic |
|-------|------|-------|
| **O-RAN Use Cases and Deployment Scenarios** | 2025-03 | Energy savings, AI/ML |
| **Potential Energy Savings Features in O-RAN** | 2025-01 | **Energy efficiency (Phase-2)** |
| **O-RAN Security Focus Group Report** | 2025-03 | Security v12.00 updates |
| **O-RAN Testing and Integration** | 2024-11 | PlugFest results |

### 9.2 3GPP

| Title | Date | Release |
|-------|------|---------|
| **3GPP Release 19 Overview** | 2024-12 | Rel-19 features |
| **NTN for 5G Advanced and Beyond** | 2024-09 | NTN roadmap |
| **IoT-NTN Phase 3 Objectives** | 2024-06 | NTN IoT enhancements |

### 9.3 NIST

| Title | Date | Topic |
|-------|------|-------|
| **Status Report on the Fourth Round of the NIST PQC Standardization** | 2025 | **NIST IR 8545** |
| **Migration to Post-Quantum Cryptography** | 2024 | NIST SP 1800-38 |
| **PQC: Preparing for Cryptographic Agility** | 2024 | Roadmap |

---

## 10. Open-Source Projects and Documentation

### 10.1 OpenAirInterface

| Resource | Link | Description |
|----------|------|-------------|
| **OAI GitLab** | [gitlab.eurecom.fr/oai/openairinterface5g](https://gitlab.eurecom.fr/oai/openairinterface5g) | Official repository |
| **OAI 5G NR gNB Tutorial** | [openairinterface.org/oai-5g-ran-project](https://openairinterface.org/oai-5g-ran-project/) | Installation guide |
| **OAI CHANGELOG (2025.w19)** | [gitlab/CHANGELOG.md](https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/2025.w19/CHANGELOG.md) | Latest changes |

### 10.2 O-RAN Software Community (OSC)

| Resource | Link | Description |
|----------|------|-------------|
| **OSC Near-RT RIC** | [docs.o-ran-sc.org](https://docs.o-ran-sc.org/) | RIC platform documentation |
| **OSC I-Release** | [docs.o-ran-sc.org/en/i-release](https://docs.o-ran-sc.org/en/i-release/) | Latest release (I) |
| **ORAN Testbed Automation** | [github.com/usnistgov/O-RAN-Testbed-Automation](https://github.com/usnistgov/O-RAN-Testbed-Automation) | NIST testing tools |

### 10.3 AI/ML Libraries

| Project | Link | Version |
|---------|------|---------|
| **Stable Baselines3** | [stable-baselines3.readthedocs.io](https://stable-baselines3.readthedocs.io/) | **2.3.0+ (our DRL library)** |
| **Gymnasium** | [gymnasium.farama.org](https://gymnasium.farama.org/) | **0.29+ (our RL environment)** |
| **TensorFlow** | [tensorflow.org](https://tensorflow.org/) | 2.15+ |
| **PyTorch** | [pytorch.org](https://pytorch.org/) | 2.1+ |

### 10.4 Post-Quantum Cryptography

| Project | Link | Algorithm |
|---------|------|-----------|
| **pqcrypto** | [github.com/pqcrypto/pqcrypto](https://github.com/pqcrypto/pqcrypto) | **NIST PQC (our library)** |
| **liboqs** | [github.com/open-quantum-safe/liboqs](https://github.com/open-quantum-safe/liboqs) | Open Quantum Safe |
| **OQS-OpenSSL** | [github.com/open-quantum-safe/openssl](https://github.com/open-quantum-safe/openssl) | PQC for OpenSSL |

---

## 11. Conferences and Journals

### 11.1 Top-Tier Conferences

| Conference | Abbreviation | Focus Area |
|------------|--------------|------------|
| **IEEE International Conference on Communications** | ICC | Wireless communications |
| **IEEE GLOBECOM** | GLOBECOM | Global communications |
| **ACM SIGCOMM** | SIGCOMM | Computer communications |
| **USENIX NSDI** | NSDI | Networked systems design |
| **IEEE INFOCOM** | INFOCOM | Computer communications |

### 11.2 Relevant Journals

| Journal | Publisher | Impact Factor |
|---------|-----------|---------------|
| **IEEE Transactions on Wireless Communications** | IEEE | 10.4 (2023) |
| **IEEE/ACM Transactions on Networking** | IEEE/ACM | 3.7 |
| **IEEE Communications Magazine** | IEEE | 11.2 |
| **IEEE Journal on Selected Areas in Communications (JSAC)** | IEEE | 13.8 |
| **Computer Networks** | Elsevier | 5.6 |

---

## 12. Search and Discovery

### 12.1 Academic Search Engines

| Platform | Link | Description |
|----------|------|-------------|
| **Google Scholar** | [scholar.google.com](https://scholar.google.com) | Broad academic search |
| **IEEE Xplore** | [ieeexplore.ieee.org](https://ieeexplore.ieee.org) | IEEE publications |
| **ACM Digital Library** | [dl.acm.org](https://dl.acm.org) | ACM publications |
| **arXiv** | [arxiv.org](https://arxiv.org) | Preprints (cs.NI, cs.LG) |
| **ResearchGate** | [researchgate.net](https://researchgate.net) | Research collaboration |

### 12.2 Keyword Suggestions

For finding related papers:
- **NTN**: "non-terrestrial networks", "satellite 5G", "3GPP NTN", "LEO satellite communications"
- **O-RAN**: "open RAN", "RAN intelligent controller", "xApp", "E2 interface", "near-RT RIC"
- **AI/ML**: "deep reinforcement learning RAN", "PPO wireless networks", "AI/ML resource allocation"
- **PQC**: "post-quantum cryptography", "lattice-based crypto", "CRYSTALS-Kyber", "ML-KEM"
- **SDR**: "software-defined radio", "USRP", "VITA 49", "GNU Radio"

---

## 13. Citation Management

### 13.1 Recommended Tools

- **Zotero** (free, open-source): [zotero.org](https://www.zotero.org/)
- **Mendeley** (free): [mendeley.com](https://www.mendeley.com/)
- **BibTeX**: For LaTeX integration

### 13.2 Citation Format (IEEE Style)

Example for our project:

```bibtex
@misc{tsai2025sdroran,
  author       = {Tsai, Hsiu-Chi},
  title        = {{SDR-O-RAN Platform: Production-Ready Satellite Ground Station with AI/ML and Quantum Security}},
  year         = {2025},
  month        = {October},
  howpublished = {\url{https://github.com/thc1006/sdr-o-ran-platform}},
  note         = {Version 3.0.0, 100\% implementation complete}
}
```

---

## 14. Reading List (Recommended Order)

For someone new to this project:

1. **Start**: O-RAN Alliance - "Understanding O-RAN" (Bonati et al., 2023)
2. **NTN**: "OpenAirInterface as a platform for 5G-NTN Research" (Sami et al., 2023)
3. **AI/ML**: "Deep Reinforcement Learning for Resource Management" (Zhang et al., 2022)
4. **PQC**: "CRYSTALS-Kyber" and "CRYSTALS-Dilithium" papers (2018)
5. **SDR**: VITA 49.2 standard (2017)
6. **Implementation**: OpenAirInterface 5G documentation
7. **Orchestration**: "Kubernetes: Up and Running" (Hightower et al., 2022)

---

**Last Updated**: 2025-10-27
**Maintained by**: thc1006@ieee.org
**Total Papers**: 60+ citations

**Contributing**: To add a paper, submit a pull request with: Title, Authors, Venue, Year, DOI/Link, and brief description.
