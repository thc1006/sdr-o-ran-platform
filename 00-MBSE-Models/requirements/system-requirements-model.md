# System Requirements Model (SysML-based)
# 系統需求模型（基於 SysML）

**Project**: SDR-O-RAN Integration for NTN Communications
**MBSE Tool**: SysML v2 (anticipated Summer 2025 release) / SysML v1.6 (current)
**Date**: 2025-10-27
**Author**: 蔡秀吉

---

## Introduction to MBSE for This Project

### What is MBSE?

**Model-Based Systems Engineering (MBSE)** is a formalized methodology that uses visual system models as the primary means of information exchange, rather than traditional document-centric approaches. MBSE enables:

1. **Traceability**: Requirements → Architecture → Implementation → Testing
2. **Consistency**: Single source of truth prevents inconsistencies
3. **Automation**: Model-driven code generation and validation
4. **Communication**: Visual models improve stakeholder understanding

### Why MBSE for SDR-O-RAN Integration?

This project is inherently complex:
- **Multi-domain**: RF engineering, cloud-native software, telecommunications
- **Multi-stakeholder**: Satellite operators, telecom carriers, equipment vendors
- **High integration complexity**: SDR ↔ O-RAN ↔ Cloud platforms
- **Evolving standards**: 3GPP Release 18/19, O-RAN specifications

MBSE provides the rigor needed to manage this complexity and ensure all requirements are met.

### SysML Diagram Types Used

This requirements model uses the following SysML diagrams:

| **Diagram Type** | **Purpose** | **Location** |
|------------------|-------------|--------------|
| **Requirement Diagram** | Capture functional & non-functional requirements | This document |
| **Use Case Diagram** | Define system usage scenarios | ../behavior/ |
| **Block Definition Diagram** | Define system structure | ../architecture/ |
| **Sequence Diagram** | Define system interactions | ../behavior/ |
| **Parametric Diagram** | Define constraints and equations | ../parametric/ |

---

## Stakeholder Needs

### Primary Stakeholders

1. **Satellite Operators**
   - Need: Flexible ground station infrastructure
   - Pain Point: High CAPEX for frequency-specific equipment
   - Success Criteria: 50% cost reduction vs. traditional ground stations

2. **Telecom Carriers (MNOs)**
   - Need: Seamless NTN-TN integration for 5G coverage extension
   - Pain Point: Vendor lock-in, complex integration
   - Success Criteria: O-RAN compliant, multi-vendor support

3. **Ground Station Operators**
   - Need: Easy deployment, low operational overhead
   - Pain Point: Complex orchestration systems
   - Success Criteria: <1 week deployment time

4. **End Users**
   - Need: Ubiquitous 5G coverage (urban + remote areas)
   - Pain Point: Coverage gaps in rural/maritime/aerial scenarios
   - Success Criteria: <100ms latency, >10Mbps throughput

---

## System Requirements Hierarchy

```
System: SDR-O-RAN-NTN Platform
│
├─ FR (Functional Requirements)
│  ├─ FR-SDR: SDR Platform Functions
│  ├─ FR-ORAN: O-RAN Functions
│  ├─ FR-ORCH: Orchestration Functions
│  └─ FR-INT: Integration Functions
│
├─ NFR (Non-Functional Requirements)
│  ├─ NFR-PERF: Performance
│  ├─ NFR-REL: Reliability
│  ├─ NFR-SEC: Security
│  ├─ NFR-SCAL: Scalability
│  └─ NFR-MAINT: Maintainability
│
└─ CR (Constraint Requirements)
   ├─ CR-STD: Standards Compliance
   ├─ CR-HW: Hardware Constraints
   └─ CR-ENV: Environmental Constraints
```

---

## Functional Requirements (FR)

### FR-SDR: SDR Platform Functional Requirements

#### FR-SDR-001: Multi-Band Signal Reception
**ID**: FR-SDR-001
**Priority**: Critical
**Source**: Stakeholder Need SN-001 (Satellite Operators)

**Requirement**:
> The SDR platform SHALL support simultaneous signal reception from multiple satellite frequency bands including C-band (4-8 GHz), Ku-band (12-18 GHz), and Ka-band (26.5-40 GHz).

**Rationale**: Different satellite constellations use different frequency bands. A multi-band capable ground station can serve multiple satellites without hardware changes.

**Verification Method**: Test
**Acceptance Criteria**:
- [ ] Successfully receives C-band signals at 6 GHz ± 500 MHz
- [ ] Successfully receives Ku-band signals at 14 GHz ± 1 GHz
- [ ] Successfully receives Ka-band signals at 28 GHz ± 2 GHz
- [ ] Supports band switching within <5 seconds

**Derived Requirements**: FR-SDR-001.1 (Antenna Control), FR-SDR-001.2 (RF Front-End)

**SysML Representation**:
```sysml
requirement FR_SDR_001 {
    id = "FR-SDR-001"
    text = "The SDR platform SHALL support simultaneous signal reception from C, Ku, and Ka bands"

    derived requirement FR_SDR_001_1 {
        text = "The antenna subsystem SHALL support phased array beam steering for C/Ku/Ka bands"
    }

    derived requirement FR_SDR_001_2 {
        text = "The RF front-end SHALL provide >60dB dynamic range"
    }
}
```

---

#### FR-SDR-002: Software-Defined Baseband Processing
**ID**: FR-SDR-002
**Priority**: Critical
**Source**: Stakeholder Need SN-001

**Requirement**:
> The SDR platform SHALL perform baseband signal processing using software-defined algorithms implemented on general-purpose computing platforms (GPP) or FPGAs.

**Rationale**: Software-defined processing enables flexible modulation scheme support and remote reconfiguration without hardware changes.

**Verification Method**: Demonstration
**Acceptance Criteria**:
- [ ] Supports QPSK, 8PSK, 16APSK, 32APSK modulation schemes
- [ ] Supports DVB-S2/S2X standard
- [ ] Configurable via API (gRPC or REST)
- [ ] Processing latency <10ms for 100 Msps sample rate

**SysML Representation**:
```sysml
requirement FR_SDR_002 {
    id = "FR-SDR-002"
    text = "The SDR platform SHALL perform baseband processing using software-defined algorithms"

    refine FR_SDR_001  // Refines multi-band reception

    satisfy {
        subject = GNU_Radio_Platform
        kind = implementation
    }
}
```

---

#### FR-SDR-003: USRP Hardware Support
**ID**: FR-SDR-003
**Priority**: High
**Source**: Technology Selection

**Requirement**:
> The SDR platform SHALL support Ettus Research USRP B210, X310, and N320 series software-defined radio devices.

**Rationale**: USRP devices are industry-standard, well-supported SDR hardware with proven reliability.

**Verification Method**: Inspection + Test
**Acceptance Criteria**:
- [ ] USRP B210 driver integration tested (10 MHz - 6 GHz)
- [ ] USRP X310 driver integration tested (DC - 6 GHz, with optional daughterboards)
- [ ] USRP N320 driver integration tested (10 MHz - 6 GHz, 100 MHz bandwidth)
- [ ] UHD (USRP Hardware Driver) version 4.6+ supported

---

#### FR-SDR-004: Cloud-Native Deployment
**ID**: FR-SDR-004
**Priority**: Critical
**Source**: Architecture Decision

**Requirement**:
> The SDR platform components SHALL be deployable as Kubernetes CNFs (Cloud-Native Network Functions) with standardized lifecycle management.

**Rationale**: Cloud-native deployment enables scalability, automated operations, and integration with modern orchestration platforms.

**Verification Method**: Demonstration
**Acceptance Criteria**:
- [ ] SDR components packaged as OCI-compliant container images
- [ ] Kubernetes Deployment manifests provided
- [ ] Health check endpoints implemented (liveness, readiness)
- [ ] Supports horizontal pod autoscaling based on workload
- [ ] Compatible with Kubernetes 1.28+

**SysML Representation**:
```sysml
requirement FR_SDR_004 {
    id = "FR-SDR-004"
    text = "SDR components SHALL be deployable as Kubernetes CNFs"

    constraint {
        kubernetes_version >= 1.28
        container_runtime in ["containerd", "cri-o"]
    }
}
```

---

#### FR-SDR-005: RESTful API Exposure
**ID**: FR-SDR-005
**Priority**: High
**Source**: Integration Requirement

**Requirement**:
> The SDR platform SHALL expose RESTful APIs for configuration, control, and status monitoring.

**Rationale**: Standard APIs enable integration with O-RAN and orchestration platforms.

**Verification Method**: Test
**Acceptance Criteria**:
- [ ] OpenAPI 3.0 specification provided
- [ ] APIs support authentication (OAuth 2.0 or API keys)
- [ ] APIs return responses within <200ms for 95th percentile
- [ ] Rate limiting implemented (configurable, default 100 req/s)
- [ ] Versioned API endpoints (/api/v1/, /api/v2/)

**Example Endpoints**:
```
POST /api/v1/sdr/stations/{station-id}/configure
GET  /api/v1/sdr/stations/{station-id}/status
PUT  /api/v1/sdr/stations/{station-id}/frequency
GET  /api/v1/sdr/stations/{station-id}/metrics
```

---

### FR-ORAN: O-RAN Functional Requirements

#### FR-ORAN-001: O-RAN Architecture Compliance
**ID**: FR-ORAN-001
**Priority**: Critical
**Source**: O-RAN Alliance Specifications

**Requirement**:
> The system SHALL implement O-RAN architecture with disaggregated network functions including O-DU (Distributed Unit), O-CU-CP (Control Plane Centralized Unit), O-CU-UP (User Plane Centralized Unit), and Near-RT RIC (RAN Intelligent Controller).

**Rationale**: O-RAN compliance ensures multi-vendor interoperability and future-proof architecture.

**Verification Method**: Test against O-RAN test suites
**Acceptance Criteria**:
- [ ] O-DU conforms to O-RAN.WG4 specifications
- [ ] O-CU-CP/UP conform to 3GPP + O-RAN specs
- [ ] Near-RT RIC conforms to O-RAN.WG3 specifications
- [ ] E2 interface (RIC ↔ DU/CU) implemented as per O-RAN.WG3.E2AP
- [ ] O1 interface (SMO ↔ DU/CU) implemented as per O-RAN.WG1

**SysML Representation**:
```sysml
requirement FR_ORAN_001 {
    id = "FR-ORAN-001"
    text = "System SHALL implement disaggregated O-RAN architecture"

    part : O_DU {
        requirement conforms_to {
            standard = "O-RAN.WG4.CUS.0-v10.00"
        }
    }

    part : O_CU_CP {
        requirement conforms_to {
            standard = "3GPP TS 38.401, 38.470"
        }
    }

    part : O_CU_UP {
        requirement conforms_to {
            standard = "3GPP TS 38.401, 38.460"
        }
    }

    part : Near_RT_RIC {
        requirement conforms_to {
            standard = "O-RAN.WG3.RICARCH-v04.00"
        }
    }
}
```

---

#### FR-ORAN-002: 3GPP NTN Support
**ID**: FR-ORAN-002
**Priority**: Critical
**Source**: 3GPP Release 18/19

**Requirement**:
> The O-RAN implementation SHALL support 3GPP Release 18 NTN (Non-Terrestrial Network) features including timing advance handling, Doppler shift compensation, and ephemeris-based beamforming.

**Rationale**: NTN support is essential for satellite-terrestrial integration.

**Verification Method**: Test with satellite constellation simulator
**Acceptance Criteria**:
- [ ] Timing Advance up to 25.6ms supported (GEO satellite)
- [ ] Doppler frequency shift compensation ±60 kHz
- [ ] Ephemeris-based beam tracking with <1° accuracy
- [ ] Support for regenerative and transparent satellite payloads
- [ ] Complies with 3GPP TS 38.300 (NTN), TS 38.821 (NTN Solutions)

**3GPP Release 19 Features (Optional)**:
- [ ] RedCap (Reduced Capability) device support
- [ ] Inter-satellite links (ISL) support
- [ ] Enhanced power control for NTN

---

#### FR-ORAN-003: CNF-Based Deployment
**ID**: FR-ORAN-003
**Priority**: Critical
**Source**: Cloud-Native Architecture

**Requirement**:
> All O-RAN network functions SHALL be deployed as Kubernetes CNFs with Helm charts for installation and lifecycle management.

**Rationale**: CNF deployment aligns with cloud-native best practices and enables automated orchestration.

**Verification Method**: Demonstration
**Acceptance Criteria**:
- [ ] O-DU, O-CU-CP, O-CU-UP packaged as Helm charts
- [ ] Charts pass `helm lint` validation
- [ ] Supports configurable resource requests/limits
- [ ] Supports rolling updates with zero downtime
- [ ] Compatible with Helm 3.12+

---

#### FR-ORAN-004: RIC xApp Development
**ID**: FR-ORAN-004
**Priority**: Medium
**Source**: Intelligent Network Optimization

**Requirement**:
> The Near-RT RIC SHALL support deployment of custom xApps (RAN Applications) for intelligent network optimization including handover optimization, load balancing, and QoS management.

**Rationale**: xApps enable AI/ML-driven network optimization tailored for NTN scenarios.

**Verification Method**: Demonstration
**Acceptance Criteria**:
- [ ] xApp SDK provided (Python or Go)
- [ ] xApp onboarding process documented
- [ ] E2 SM (Service Model) KPM v3.0 supported
- [ ] Support for at least 10 concurrent xApps
- [ ] xApp lifecycle management via K8s operators

**Example xApps**:
1. NTN Handover Optimizer (satellite beam handover)
2. QoS-aware Scheduler (prioritize latency-sensitive traffic)
3. Energy Efficiency xApp (sleep mode for idle cells)

---

### FR-ORCH: Orchestration Functional Requirements

#### FR-ORCH-001: Multi-Cluster Management
**ID**: FR-ORCH-001
**Priority**: High
**Source**: Distributed Architecture

**Requirement**:
> The orchestration platform SHALL manage multiple Kubernetes clusters including SDR edge clusters and O-RAN edge clusters, with centralized policy and configuration distribution.

**Rationale**: SDR and O-RAN components may be deployed on separate clusters for fault isolation and resource optimization.

**Verification Method**: Demonstration
**Acceptance Criteria**:
- [ ] Supports management of ≥10 workload clusters
- [ ] Centralized cluster registration and discovery
- [ ] Policy propagation to all clusters within <60 seconds
- [ ] Support for heterogeneous clusters (x86, ARM, GPU nodes)

---

#### FR-ORCH-002: GitOps-Based Automation
**ID**: FR-ORCH-002
**Priority**: High
**Source**: DevOps Best Practices

**Requirement**:
> The orchestration platform SHALL implement GitOps methodology where Git repositories serve as the single source of truth for system configuration.

**Rationale**: GitOps enables declarative configuration, auditability, and automated rollback.

**Verification Method**: Demonstration
**Acceptance Criteria**:
- [ ] Configuration changes trigger automatic reconciliation
- [ ] Supports Git branching for staging/production environments
- [ ] Configuration drift detection and self-healing
- [ ] Rollback to previous Git commit within <5 minutes

**Recommended Tools**:
- **Nephio Approach**: Porch (Package Orchestrator) + Config Sync
- **K8s Operator Approach**: ArgoCD or Flux

---

#### FR-ORCH-003: Service Chaining
**ID**: FR-ORCH-003
**Priority**: Medium
**Source**: End-to-End Service Provisioning

**Requirement**:
> The orchestration platform SHALL support automated service chaining to connect SDR ground station services with O-RAN network services.

**Rationale**: End-to-end service provisioning requires coordinated deployment of interdependent components.

**Verification Method**: Test
**Acceptance Criteria**:
- [ ] Dependency resolution (O-RAN DU depends on SDR baseband output)
- [ ] Ordered deployment (SDR → API Gateway → O-DU → O-CU)
- [ ] Service mesh integration (Istio or Linkerd) for traffic management
- [ ] Health-check based readiness gates

**Example Service Chain**:
```
Satellite → Antenna → USRP → SDR Baseband CNF → API Gateway → O-DU → O-CU-UP → UPF → Internet
```

---

### FR-INT: Integration Functional Requirements

#### FR-INT-001: SDR-to-O-RAN Data Plane
**ID**: FR-INT-001
**Priority**: Critical
**Source**: System Architecture

**Requirement**:
> The system SHALL provide a high-throughput, low-latency data plane interface to forward processed baseband IQ samples from the SDR platform to the O-RAN DU.

**Rationale**: The DU requires IQ samples at radio frame rate (1ms for 5G NR).

**Verification Method**: Performance Test
**Acceptance Criteria**:
- [ ] Throughput: ≥1 Gbps for 100 MHz bandwidth signal
- [ ] Latency: <5ms end-to-end (SDR output → DU input)
- [ ] Packet loss: <0.001% under normal conditions
- [ ] Interface options: gRPC streaming, shared memory, or DPDK

**SysML Representation**:
```sysml
requirement FR_INT_001 {
    id = "FR-INT-001"
    text = "High-throughput data plane from SDR to O-DU"

    constraint {
        throughput >= 1 Gbps
        latency <= 5 ms
        packet_loss <= 0.001 %
    }

    interface : DataPlane {
        protocol in ["gRPC", "shared_memory", "DPDK"]
    }
}
```

---

#### FR-INT-002: Control Plane API
**ID**: FR-INT-002
**Priority**: High
**Source**: System Architecture

**Requirement**:
> The system SHALL provide RESTful APIs to coordinate control plane operations between SDR platform and O-RAN components, including configuration synchronization and status reporting.

**Rationale**: Control plane coordination ensures consistent system state.

**Verification Method**: Test
**Acceptance Criteria**:
- [ ] API response time <200ms (95th percentile)
- [ ] Supports transactional configuration updates
- [ ] Provides event-driven notifications (WebSocket or Server-Sent Events)
- [ ] Implements retry and timeout mechanisms

**Example API Workflow**:
```
1. O-RAN SMO → SDR API: "Configure Ku-band reception for satellite X"
2. SDR Platform → Antenna Controller: "Point to azimuth 45°, elevation 30°"
3. SDR Platform → USRP: "Set center frequency to 12.5 GHz"
4. SDR Platform → O-RAN API: "Ready to receive, expect IQ stream on port 50051"
5. O-RAN DU → SDR Platform: Start IQ stream (gRPC)
```

---

#### FR-INT-003: Monitoring and Telemetry
**ID**: FR-INT-003
**Priority**: High
**Source**: Operational Requirements

**Requirement**:
> The system SHALL collect, aggregate, and expose telemetry data from both SDR and O-RAN components via standard observability protocols (Prometheus, OpenTelemetry).

**Rationale**: Unified observability enables proactive issue detection and performance optimization.

**Verification Method**: Demonstration
**Acceptance Criteria**:
- [ ] Metrics exported in Prometheus format
- [ ] Distributed tracing via OpenTelemetry
- [ ] Logs aggregated to central store (Elasticsearch, Loki)
- [ ] Pre-built Grafana dashboards for key KPIs
- [ ] Alerting rules for critical conditions (signal loss, latency spike)

**Key Metrics**:
- SDR: Signal SNR, EbN0, packet error rate, USRP temperature
- O-RAN: Active UEs, throughput, handover success rate, latency
- Integration: API response time, data plane throughput, queue depth

---

## Non-Functional Requirements (NFR)

### NFR-PERF: Performance Requirements

#### NFR-PERF-001: End-to-End Latency
**ID**: NFR-PERF-001
**Priority**: Critical

**Requirement**:
> The system SHALL achieve end-to-end latency from satellite signal reception to user data delivery of <100ms for 95th percentile under normal conditions.

**Rationale**: Low latency is critical for real-time applications (VoIP, gaming, IoT).

**Breakdown**:
- Satellite propagation: ~25-30ms (LEO) or ~240ms (GEO)
- SDR processing: <10ms
- O-RAN processing: <20ms
- Transport network: <20ms
- **Total (LEO)**: ~75-80ms ✅
- **Total (GEO)**: ~290ms (within 300ms target for GEO)

---

#### NFR-PERF-002: Throughput
**ID**: NFR-PERF-002
**Priority**: High

**Requirement**:
> The system SHALL support aggregate throughput of ≥1 Gbps per ground station for downlink traffic.

**Rationale**: Support high-bandwidth applications (video streaming, backhaul).

**Verification Method**: Load Test

---

#### NFR-PERF-003: Scalability
**ID**: NFR-PERF-003
**Priority**: High

**Requirement**:
> The orchestration platform SHALL scale to manage ≥100 ground stations and ≥1000 O-RAN cells without performance degradation.

**Rationale**: Commercial deployment requires large-scale management.

**Verification Method**: Stress Test

---

### NFR-REL: Reliability Requirements

#### NFR-REL-001: Availability
**ID**: NFR-REL-001
**Priority**: Critical

**Requirement**:
> The system SHALL achieve 99.9% availability (max 8.76 hours downtime per year) for critical path components (SDR platform, O-DU, O-CU).

**Rationale**: High availability is essential for carrier-grade service.

**Strategies**:
- Redundant hardware (active-standby USRP)
- CNF anti-affinity rules (no single point of failure)
- Automated health checks and failover

---

#### NFR-REL-002: Fault Tolerance
**ID**: NFR-REL-002
**Priority**: High

**Requirement**:
> The system SHALL automatically recover from single-node failures within <60 seconds without operator intervention.

**Rationale**: Self-healing reduces operational burden.

**Verification Method**: Chaos Engineering Tests

---

### NFR-SEC: Security Requirements

#### NFR-SEC-001: Authentication & Authorization
**ID**: NFR-SEC-001
**Priority**: Critical

**Requirement**:
> All API endpoints SHALL require authentication (OAuth 2.0 or mTLS) and implement role-based access control (RBAC).

**Verification Method**: Security Audit

---

#### NFR-SEC-002: Data Encryption
**ID**: NFR-SEC-002
**Priority**: Critical

**Requirement**:
> All inter-component communication SHALL be encrypted using TLS 1.3 or IPsec.

**Verification Method**: Traffic Analysis

---

### NFR-MAINT: Maintainability Requirements

#### NFR-MAINT-001: Remote Management
**ID**: NFR-MAINT-001
**Priority**: High

**Requirement**:
> All system components SHALL be remotely manageable via standard APIs without requiring physical access.

**Rationale**: Ground stations may be in remote locations.

---

#### NFR-MAINT-002: Software Updates
**ID**: NFR-MAINT-002
**Priority**: High

**Requirement**:
> The system SHALL support rolling updates of CNFs with zero downtime.

**Verification Method**: Update Test

---

## Constraint Requirements (CR)

### CR-STD: Standards Compliance

#### CR-STD-001: 3GPP Compliance
**Requirement**: System SHALL comply with 3GPP Release 18 (baseline) and support Release 19 features where feasible.

#### CR-STD-002: O-RAN Compliance
**Requirement**: System SHALL pass O-RAN OTIC (O-RAN Test and Integration Center) conformance tests.

---

### CR-HW: Hardware Constraints

#### CR-HW-001: USRP Compatibility
**Requirement**: System SHALL operate with USRP B210 (minimum), X310 (recommended), or N320.

#### CR-HW-002: Antenna Constraints
**Requirement**: System SHALL support phased array antennas with electronic beam steering (e.g., Kymeta u8).

---

### CR-ENV: Environmental Constraints

#### CR-ENV-001: Operating Temperature
**Requirement**: System SHALL operate in -40°C to +60°C (outdoor ground station deployment).

#### CR-ENV-002: Power Consumption
**Requirement**: Total system power consumption SHALL NOT exceed 10kW per ground station.

---

## Requirements Traceability Matrix (RTM)

| **Requirement ID** | **Derived From** | **Verified By** | **Implemented In** | **Status** |
|--------------------|------------------|-----------------|--------------------|-|
| FR-SDR-001 | SN-001 (Satellite Operators) | Test Report TR-001 | 03-Implementation/sdr-platform/ | ⏳ Pending |
| FR-SDR-002 | SN-001 | Demo Video DV-001 | 03-Implementation/sdr-platform/gnuradio-flowgraphs/ | ⏳ Pending |
| FR-SDR-004 | Architecture Decision | Integration Test IT-001 | 03-Implementation/sdr-platform/api-gateway/ | ⏳ Pending |
| FR-ORAN-001 | O-RAN Alliance | OTIC Test Report | 03-Implementation/oran-cnfs/ | ⏳ Pending |
| FR-ORAN-002 | 3GPP TS 38.300 | NTN Simulator Test | 03-Implementation/oran-cnfs/o-du/ | ⏳ Pending |
| FR-INT-001 | System Architecture | Performance Test PT-001 | 03-Implementation/integration/sdr-oran-connector/ | ⏳ Pending |
| NFR-PERF-001 | Stakeholder Need | Load Test LT-001 | Full System | ⏳ Pending |
| NFR-REL-001 | SLA Requirements | Availability Monitoring | Infrastructure | ⏳ Pending |

---

## Verification and Validation Plan

### Verification Methods

1. **Inspection**: Document review, code review
2. **Analysis**: Mathematical modeling, simulation
3. **Test**: Unit tests, integration tests, system tests
4. **Demonstration**: Proof-of-concept, pilot deployment

### Validation Scenarios

#### Scenario 1: LEO Satellite Coverage Extension
**Objective**: Validate system provides seamless 5G coverage using LEO satellite backhaul

**Steps**:
1. Deploy SDR ground station with Ku-band antenna
2. Configure for LEO satellite constellation (e.g., Starlink, OneWeb)
3. Deploy O-RAN DU/CU connected to SDR
4. Establish 5G connection with UE
5. Measure latency, throughput, handover success

**Success Criteria**: Latency <100ms, Throughput >50Mbps, Handover success >95%

---

#### Scenario 2: Multi-Band Operation
**Objective**: Validate simultaneous multi-band operation

**Steps**:
1. Configure SDR for dual-band (Ku + Ka)
2. Receive signals from two different satellites
3. Verify independent signal processing chains
4. Measure crosstalk and interference

**Success Criteria**: <0.5dB SNR degradation due to multi-band operation

---

## Next Steps

1. ✅ Requirements defined in this document
2. ⏳ Architecture models (Block Definition Diagrams) → See `../architecture/`
3. ⏳ Behavioral models (Sequence Diagrams) → See `../behavior/`
4. ⏳ Implementation (Code artifacts) → See `../../03-Implementation/`
5. ⏳ Verification tests → See `../../04-Deployment/` test plans

---

## Document Control

| **Version** | **Date** | **Author** | **Changes** |
|-------------|----------|------------|-------------|
| 1.0 | 2025-10-27 | 蔡秀吉 | Initial MBSE requirements model |

---

**Status**: ✅ Complete (Initial Version)
**Review Status**: ⏳ Pending Technical Review
**Approval**: ⏳ Pending Stakeholder Approval
