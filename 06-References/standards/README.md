# Standards and Specifications References
# SDR-O-RAN Platform

**Last Updated**: 2025-10-27
**Purpose**: Complete catalog of standards, specifications, and technical documents

---

## 1. 3GPP Standards (Release 19)

### 1.1 NTN (Non-Terrestrial Networks)

| Document | Title | Release | Status | Link |
|----------|-------|---------|--------|------|
| **TS 38.300** | NR and NG-RAN Overall Description | Rel-19 | Freeze: Dec 2025 | [3GPP Portal](https://www.3gpp.org/DynaReport/38300.htm) |
| **TS 38.821** | Solutions for NR to support non-terrestrial networks (NTN) | Rel-19 | 45% complete | [3GPP Portal](https://www.3gpp.org/DynaReport/38821.htm) |
| **TS 38.101-5** | NR; User Equipment (UE) radio transmission and reception; Part 5: Satellite access Radio Frequency (RF) and performance requirements | Rel-19 | Ongoing | [3GPP Portal](https://www.3gpp.org/DynaReport/38101-5.htm) |
| **TS 38.211** | NR; Physical channels and modulation | Rel-19 | Stable | [3GPP Portal](https://www.3gpp.org/DynaReport/38211.htm) |
| **TS 38.212** | NR; Multiplexing and channel coding | Rel-19 | Stable | [3GPP Portal](https://www.3gpp.org/DynaReport/38212.htm) |
| **TS 38.213** | NR; Physical layer procedures for control | Rel-19 | Stable | [3GPP Portal](https://www.3gpp.org/DynaReport/38213.htm) |
| **TS 38.214** | NR; Physical layer procedures for data | Rel-19 | Stable | [3GPP Portal](https://www.3gpp.org/DynaReport/38214.htm) |
| **TS 38.215** | NR; Physical layer measurements | Rel-19 | Stable | [3GPP Portal](https://www.3gpp.org/DynaReport/38215.htm) |

**Key NTN Parameters** (Release 19):
- `cellSpecificKoffset_r17`: Scheduling offset for timing relationships (0-2.5ms range for NTN)
- `ta-Common_r17`: Common timing advance for propagation delay compensation (0-25.6ms for GEO)
- Autonomous TA updates: Based on DL time drift for LEO satellite movement
- NTN IoT Phase 3: 30% complete as of Sept 2024

**Timeline**:
- RAN1 Functional Freeze: **June 2025**
- RAN2/3/4 Functional Freeze: **September 2025**
- Final Completion: **December 2025**

### 1.2 5G Core Network

| Document | Title | Release | Description |
|----------|-------|---------|-------------|
| **TS 23.501** | System architecture for the 5G System (5GS) | Rel-19 | 5G architecture |
| **TS 23.502** | Procedures for the 5G System (5GS) | Rel-19 | Call flows, procedures |
| **TS 38.401** | NG-RAN; Architecture description | Rel-19 | RAN architecture |
| **TS 38.470** | NG-RAN; F1 general aspects and principles | Rel-19 | O-DU ↔ O-CU interface |

---

## 2. O-RAN Alliance Specifications

### 2.1 Latest Release (March 2025)

**Total Documents**: 134 titles (current version), 830 documents overall
**Last Release**: **60 new/updated documents since March 2025**

### 2.2 Working Group 1 (Use Cases and Architecture)

| Document | Version | Date | Description |
|----------|---------|------|-------------|
| **O-RAN.WG1.O-RAN Architecture Description** | v12.00 | 2025-03 | Overall O-RAN architecture |
| **O-RAN.WG1.Use Cases and Deployment Scenarios** | v08.00 | 2025-03 | Energy savings, AI/ML use cases |
| **O-RAN.WG1.Slicing Architecture** | v07.00 | 2025-03 | Network slicing |

**Key Features** (v12.00):
- Updated functional splits (Option 2, 7.2x)
- Multi-vendor interoperability
- Cloud-native CNF architecture
- Energy efficiency enhancements

### 2.3 Working Group 2 (Non-RT RIC and A1)

| Document | Version | Date | Description |
|----------|---------|------|-------------|
| **O-RAN.WG2.Non-RT-RIC-Architecture** | v06.00 | 2025-03 | Non-RT RIC architecture |
| **O-RAN.WG2.A1-Interface** | v06.00 | 2025-03 | A1 policy interface |
| **O-RAN.WG2.AI-ML-Workflow-Description** | v03.00 | 2025-03 | AI/ML training and inference |
| **O-RAN.WG2.rApp-Guide** | v03.00 | 2025-03 | rApp development |

**Phase-2 Enhancements** (2025):
- AI/ML security requirements
- Enhanced A1 Policy for energy savings
- SME and SMOS communication security

### 2.4 Working Group 3 (Near-RT RIC and E2)

| Document | Version | Date | Description |
|----------|---------|------|-------------|
| **O-RAN.WG3.E2AP** | v03.00 | 2025-03 | E2 Application Protocol |
| **O-RAN.WG3.E2SM-KPM** | v03.00 | 2025-03 | **KPM Service Model (Key Performance Measurement)** |
| **O-RAN.WG3.E2SM-RC** | v03.00 | 2025-03 | **RC Service Model (RAN Control)** |
| **O-RAN.WG3.E2SM-NI** | v01.00 | 2024-11 | Network Interface Service Model |
| **O-RAN.WG3.RIC-Arch** | v03.00 | 2025-03 | RIC architecture |
| **O-RAN.WG3.xApp-SDK** | v02.00 | 2025-03 | xApp development SDK |

**Critical Implementation Notes**:
- **E2SM-KPM v03.00**: Adds UE-level throughput, BLER, latency measurements
- **E2SM-RC v03.00**: Handover control, QoS policy enforcement, PRB allocation
- **E2 Scalability**: Support for 100+ xApps per RIC
- **E2 Failover**: Redundant E2 connections for high availability

### 2.5 Working Group 4 (Open Fronthaul)

| Document | Version | Date | Description |
|----------|---------|------|-------------|
| **O-RAN.WG4.CUS** | v13.00 | 2025-03 | Control, User, and Synchronization Plane Specification |
| **O-RAN.WG4.MP** | v13.00 | 2025-03 | Management Plane Specification |
| **O-RAN.WG4.IOT** | v08.00 | 2025-03 | Interoperability Test Specifications |

### 2.6 Security Specifications

| Document | Version | Date | Description |
|----------|---------|------|-------------|
| **O-RAN.SEC.Security-Specifications** | v12.00 | 2025-03 | **Complete security framework** |

**v12.00 Updates**:
- ✅ ETSI and BSI corrections incorporated
- ✅ **NEW**: AI/ML security requirements (model integrity, adversarial defense)
- ✅ **NEW**: MACsec for Shared O-RU
- ✅ Enhanced O1/O2 security with refined terms
- ✅ Updated Y1, Near-RT RIC, A1 security
- ✅ SBOM (Software Bill of Materials) requirements
- ✅ Enhanced certificate management (automated rotation)

### 2.7 Energy Savings White Paper

| Document | Date | Description |
|----------|------|-------------|
| **O-RAN.SuFG.Potential Energy Savings Features in O-RAN** | 2025-01 | Energy efficiency features |

**Key Features**:
- Phase-2 WG2/WG3 enhancements for A1 Policy and E2-SM CCC
- Cell DTX, sleep modes, carrier shutdown strategies
- AI/ML-based energy optimization
- Integration with renewable energy sources

---

## 3. NIST Post-Quantum Cryptography Standards

### 3.1 Published FIPS Standards (August 2024)

| Standard | Algorithm | Published | Description |
|----------|-----------|-----------|-------------|
| **FIPS 203** | **ML-KEM** (Module-Lattice-Based Key-Encapsulation Mechanism) | 2024-08-13 | Formerly CRYSTALS-Kyber |
| **FIPS 204** | **ML-DSA** (Module-Lattice-Based Digital Signature Algorithm) | 2024-08-13 | Formerly CRYSTALS-Dilithium |
| **FIPS 205** | **SLH-DSA** (Stateless Hash-Based Digital Signature Algorithm) | 2024-08-13 | Formerly SPHINCS+ |

**Implementation Details**:

#### FIPS 203 (ML-KEM)
- **Variants**: ML-KEM-512, ML-KEM-768, **ML-KEM-1024** (our implementation)
- **Security Level**: NIST Level 3 (AES-192 equivalent)
- **Key Sizes**:
  - Public Key: 1,568 bytes
  - Secret Key: 3,168 bytes
  - Ciphertext: 1,568 bytes
  - Shared Secret: 32 bytes (for AES-256-GCM)
- **Use Case**: TLS 1.3 key exchange, gRPC encryption, E2AP security

#### FIPS 204 (ML-DSA)
- **Variants**: ML-DSA-44, ML-DSA-65, **ML-DSA-87** (our implementation = Dilithium5)
- **Security Level**: NIST Level 5 (AES-256 equivalent)
- **Key Sizes**:
  - Public Key: 2,592 bytes
  - Secret Key: 4,864 bytes
  - Signature: ~4,595 bytes
- **Use Case**: E2AP message authentication, X.509 certificates, code signing

### 3.2 Additional Standards (2025)

| Standard | Status | Date | Description |
|----------|--------|------|-------------|
| **HQC** | Selected for standardization | 2025-03-11 | Hamming Quasi-Cyclic (alternative KEM) |
| **NIST IR 8545** | Published | 2025 | Fourth Round PQC Standardization Status Report |

**Migration Timeline**:
- 2024-08-13: FIPS 203/204/205 published
- 2025-2030: **Transition period** for commercial and government systems
- 2030-2035: Full PQC migration required (estimated)

---

## 4. SDR and RF Standards

### 4.1 VITA Standards

| Standard | Title | Date | Description |
|----------|-------|------|-------------|
| **ANSI/VITA 49.0-2015** | VRT (VITA Radio Transport) Protocol | 2015 | Original VRT |
| **ANSI/VITA 49.2-2017** | VRT Signal Data Packet Standard | 2017 | **Used in our implementation** |

**Key Features** (VITA 49.2):
- IF Data Packets (Type 1) with IQ samples
- Context Packets (Type 4) with metadata
- Timestamp precision: 2⁻⁶⁴ seconds (picosecond resolution)
- UDP/IP transport
- Real-time streaming capabilities

### 4.2 Ethernet Standards

| Standard | Description |
|----------|-------------|
| **IEEE 802.3ae** | 10 Gigabit Ethernet (10GBASE-SR/LR) |
| **IEEE 1588** | Precision Time Protocol (PTP) for synchronization |

---

## 5. Cloud-Native and Kubernetes Standards

### 5.1 Kubernetes

| Version | Release Date | Status | Key Features |
|---------|--------------|--------|--------------|
| **1.31** | 2024-08 | Stable | AppArmor GA, AI/ML ImageVolume (alpha) |
| **1.32** | 2024-12 | Stable | Asynchronous Preemption (beta) |
| **1.33** | 2025-04 | **Current** | **ClusterTrustBundle (beta), 64 enhancements** |

**1.33 Highlights**:
- 18 features graduated to Stable
- 20 features entered Beta
- 24 features entered Alpha
- Asynchronous Preemption for faster scheduling
- ClusterTrustBundle for X.509 trust anchors (PQC certificates)

### 5.2 Container Standards

| Standard | Organization | Description |
|----------|--------------|-------------|
| **OCI Image Spec** | OCI | Container image format |
| **OCI Runtime Spec** | OCI | Container runtime interface |
| **CNI** | CNCF | Container Network Interface |
| **CSI** | CNCF | Container Storage Interface |

---

## 6. Networking Standards

### 6.1 gRPC and Protocol Buffers

| Technology | Version | Description |
|------------|---------|-------------|
| **gRPC** | 1.60+ | HTTP/2-based RPC framework |
| **Protocol Buffers** | v3 | Serialization protocol |
| **TLS 1.3** | RFC 8446 | Transport Layer Security |
| **HPKE** | RFC 9180 | Hybrid Public Key Encryption (PQC-ready) |

### 6.2 Security Standards

| Standard | Description |
|----------|-------------|
| **RFC 9325** | TLS 1.3 Recommendations for Networking Equipment |
| **RFC 8446** | TLS 1.3 Protocol Specification |
| **NIST SP 800-207** | Zero Trust Architecture |
| **NIST SP 800-131A** | Transitioning the Use of Cryptographic Algorithms |

---

## 7. Testing and Compliance Standards

### 7.1 O-RAN Testing

| Document | Description |
|----------|-------------|
| **O-RAN.WG6.IOT** | Interoperability and O-DU Testing |
| **O-RAN.WG5.E2E** | End-to-End Testing |

### 7.2 3GPP Conformance

| Standard | Description |
|----------|-------------|
| **TS 38.521-5** | NR; User Equipment (UE) conformance specification; Part 5: Satellite access Radio Frequency (RF) test cases |

---

## 8. Industry Standards Organizations

### 8.1 Membership and Access

| Organization | Website | Membership Required? | Cost |
|--------------|---------|---------------------|------|
| **3GPP** | [www.3gpp.org](https://www.3gpp.org) | No | Free for specs |
| **O-RAN Alliance** | [www.o-ran.org](https://www.o-ran.org) | Yes (for contributions) | Member fees apply |
| **NIST** | [csrc.nist.gov](https://csrc.nist.gov) | No | Free |
| **IETF** | [www.ietf.org](https://www.ietf.org) | No | Free for RFCs |
| **IEEE** | [www.ieee.org](https://www.ieee.org) | Yes (for some docs) | Varies |

---

## 9. Quick Reference Links

### 9.1 3GPP

- **Portal**: https://www.3gpp.org
- **Specification Search**: https://www.3gpp.org/DynaReport/SpecList.htm
- **Release 19 Overview**: https://www.3gpp.org/technologies/ran-rel-19
- **NTN Overview**: https://www.3gpp.org/technologies/ntn-overview

### 9.2 O-RAN Alliance

- **Main Site**: https://www.o-ran.org
- **Specifications**: https://www.o-ran.org/specifications
- **Working Groups**: https://www.o-ran.org/workgroups
- **PlugFests**: https://www.o-ran.org/plugfests

### 9.3 NIST PQC

- **PQC Project**: https://csrc.nist.gov/projects/post-quantum-cryptography
- **FIPS 203**: https://doi.org/10.6028/NIST.FIPS.203
- **FIPS 204**: https://doi.org/10.6028/NIST.FIPS.204
- **FIPS 205**: https://doi.org/10.6028/NIST.FIPS.205

### 9.4 Kubernetes

- **Releases**: https://kubernetes.io/releases/
- **Changelog**: https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/
- **v1.33 Blog**: https://kubernetes.io/blog/2025/04/23/kubernetes-v1-33-release/

---

## 10. Document Versions Used in This Project

| Component | Standard/Spec | Version | Date |
|-----------|---------------|---------|------|
| **NTN** | 3GPP TS 38.821 | Rel-19 (45% complete) | Freeze: Dec 2025 |
| **O-RAN Architecture** | O-RAN.WG1 | v12.00 | 2025-03 |
| **E2 KPM** | O-RAN.WG3.E2SM-KPM | v03.00 | 2025-03 |
| **E2 RC** | O-RAN.WG3.E2SM-RC | v03.00 | 2025-03 |
| **PQC KEM** | FIPS 203 (ML-KEM) | 1.0 | 2024-08-13 |
| **PQC Signatures** | FIPS 204 (ML-DSA) | 1.0 | 2024-08-13 |
| **VITA VRT** | ANSI/VITA 49.2 | 2017 | 2017 |
| **Kubernetes** | K8s | 1.33 | 2025-04 |
| **TLS** | RFC 8446 | 1.3 | 2018 |

---

## 11. Compliance Checklist

- ✅ **3GPP Release 19 NTN**: cellSpecificKoffset_r17, ta-Common_r17, autonomous TA
- ✅ **O-RAN Alliance**: E2SM-KPM v03.00, E2SM-RC v03.00, Security v12.00
- ✅ **NIST PQC**: FIPS 203 (ML-KEM-1024), FIPS 204 (ML-DSA-87/Dilithium5)
- ✅ **VITA 49.2**: IF Data + Context packets, nanosecond timestamps
- ✅ **Kubernetes 1.33**: ClusterTrustBundle for PQC certificates
- ✅ **TLS 1.3**: RFC 8446 with ML-KEM key exchange

---

**Last Updated**: 2025-10-27
**Maintained by**: thc1006@ieee.org
**Status**: ✅ Production-Ready

**Next Review**: Quarterly (or upon new standard releases)
