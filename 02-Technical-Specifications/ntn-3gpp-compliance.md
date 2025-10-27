# 3GPP Release 19 NTN Compliance Documentation

## Document Information

**Version:** 1.0
**Date:** October 2025
**Target Release:** 3GPP Release 19
**Status:** Development Phase
**Compliance Level:** Full Specification Adherence

---

## Executive Summary

This document outlines the compliance requirements and implementation roadmap for Non-Terrestrial Networks (NTN) based on 3GPP Release 19 specifications. As Release 19 progresses toward its December 2025 completion, this documentation provides comprehensive guidance for NTN system implementation, focusing on satellite-based 5G NR deployments for rural connectivity, IoT applications, and advanced coverage scenarios.

3GPP Release 19 represents a significant evolution in NTN capabilities, building upon the foundational work of Release 17 and 18 while introducing critical enhancements for regenerative payloads, improved coverage, and expanded IoT support. This document serves as the authoritative reference for ensuring full compliance with Release 19 NTN specifications.

---

## 1. Release 19 Timeline and Development Status

### 1.1 Official Release Schedule

3GPP Release 19 follows a structured development timeline with multiple freeze stages:

**RAN Working Group Freeze Schedule:**
- **RAN1 Functional Freeze:** June 2025
  - Physical layer specifications
  - Radio resource management procedures
  - Frame structure and waveform definitions

- **RAN2/3/4 Functional Freeze:** September 2025
  - RAN2: Radio interface protocols and procedures
  - RAN3: Network architecture and interfaces
  - RAN4: Radio frequency and conformance testing

- **Final Completion:** December 2025
  - Complete specification set publication
  - Technical reports finalized
  - Conformance test specifications approved

### 1.2 Development Completion Status

As of September 2024, the NTN work items show the following completion rates:

**NTN for NR Enhancements:**
- **Current Status:** 45% complete
- **Target Completion:** December 2025
- **Key Focus Areas:**
  - Rural and remote area coverage optimization
  - GSO (Geostationary Orbit) constellation support
  - NGSO (Non-Geostationary Orbit) constellation support
  - Inter-satellite handover procedures
  - Advanced beam management techniques

**NTN IoT Phase 3:**
- **Current Status:** 30% complete
- **Target Completion:** December 2025
- **Key Focus Areas:**
  - Downlink coverage enhancements for IoT devices
  - Power consumption optimization
  - FR1-NTN (Frequency Range 1) support
  - FR2-NTN (Frequency Range 2) support
  - Massive IoT connectivity scenarios

### 1.3 Work Item Dependencies

The Release 19 NTN work builds upon previous releases:

- **Release 17 Foundation:** Basic NTN support, transparent payload
- **Release 18 Enhancements:** IoT-NTN Phase 2, coverage improvements
- **Release 19 Advancement:** Regenerative payload, full-duplex RedCap, enhanced IoT

---

## 2. NTN for NR Enhancements (Release 19)

### 2.1 Coverage for Rural and Remote Areas

Release 19 introduces significant enhancements specifically designed for rural and remote area connectivity:

**Coverage Enhancement Techniques:**

1. **Extended Cell Radius Support**
   - Maximum cell radius: Up to 1,000 km for GEO satellites
   - LEO satellite cell radius: Up to 500 km
   - Dynamic cell sizing based on satellite altitude and beam configuration

2. **Beam Management Improvements**
   - Multi-beam coordination for seamless coverage
   - Adaptive beam steering for optimal coverage
   - Interference mitigation between adjacent beams
   - Support for both spot beams and shaped beams

3. **Link Budget Optimization**
   - Enhanced power control mechanisms
   - Improved receiver sensitivity requirements
   - Advanced coding schemes for challenging propagation conditions
   - Support for higher order modulation in favorable conditions

**Target Deployment Scenarios:**
- Remote agricultural regions
- Maritime communications beyond terrestrial coverage
- Aviation connectivity for polar and oceanic routes
- Emergency services in disaster-affected areas
- Military and defense applications in remote theaters

### 2.2 GSO and NGSO Constellation Support

Release 19 provides comprehensive support for both GSO and NGSO satellite systems:

**GSO (Geostationary Orbit) Characteristics:**
- **Altitude:** 35,786 km above Earth's equator
- **Orbital Period:** 24 hours (appears stationary)
- **Coverage Area:** Approximately 1/3 of Earth's surface per satellite
- **Propagation Delay:** ~250 ms one-way, ~500 ms round-trip
- **Doppler Shift:** Minimal (near-zero for fixed ground stations)

**GSO Implementation Requirements:**
- Static satellite position compensation
- Long propagation delay handling (up to 550 ms RTT)
- Infrequent timing advance updates
- Simplified handover procedures (rare or non-existent)
- Large cell footprint management

**NGSO (Non-Geostationary Orbit) Characteristics:**
- **Altitude Range:** 500 km - 2,000 km (LEO constellation focus)
- **Orbital Period:** 90-120 minutes (LEO)
- **Coverage Area:** Smaller, dynamic footprints
- **Propagation Delay:** 5-20 ms one-way for LEO
- **Doppler Shift:** Significant (up to ±40 kHz at L-band)

**NGSO Implementation Requirements:**
- Dynamic satellite tracking and beam switching
- Frequent handover support (satellite-to-satellite and beam-to-beam)
- Continuous Doppler compensation
- Autonomous timing advance updates
- Constellation coordination for continuous coverage
- Inter-satellite link support (for regenerative payloads)

### 2.3 Technical Objectives and Enhancements

**Downlink Coverage Enhancements:**

Release 19 introduces several mechanisms to improve DL coverage:

1. **Enhanced Reference Signal Design**
   - Higher density reference signals for improved channel estimation
   - Optimized SSB (Synchronization Signal Block) transmission
   - Support for additional DMRS (Demodulation Reference Signal) patterns

2. **Advanced Receiver Techniques**
   - Improved HARQ (Hybrid Automatic Repeat Request) procedures
   - Enhanced blind decoding capabilities
   - Support for advanced interference cancellation

3. **Adaptive Transmission Schemes**
   - Dynamic MCS (Modulation and Coding Scheme) selection
   - Adaptive bandwidth allocation
   - Load-based resource optimization

**Uplink Capacity Enhancements:**

UL capacity is critical for IoT and interactive services:

1. **Grant-Free Transmission Support**
   - Configured grant for periodic traffic
   - Random access optimization for sporadic transmissions
   - Collision resolution mechanisms

2. **Power Control Improvements**
   - Advanced open-loop power control
   - Closed-loop power control refinements
   - Path loss compensation for satellite links

3. **Multi-Connectivity Support**
   - Dual connectivity between terrestrial and NTN
   - Multi-satellite connectivity for improved reliability
   - Load balancing across multiple access points

**Regenerative Payload Support:**

Release 19 introduces comprehensive support for regenerative (processing) payloads:

1. **Architecture Requirements**
   - On-board signal processing capabilities
   - Demodulation and re-modulation on satellite
   - Protocol termination at satellite level
   - Inter-satellite link support

2. **Protocol Stack Modifications**
   - Split protocol architecture support
   - RLC (Radio Link Control) termination options
   - PDCP (Packet Data Convergence Protocol) routing decisions
   - Enhanced ARQ procedures

3. **Advantages Over Transparent Payloads**
   - Reduced end-to-end latency
   - Improved spectral efficiency
   - Enhanced quality of service control
   - Better resource utilization

4. **Implementation Considerations**
   - Increased satellite complexity and cost
   - Higher power consumption on satellite
   - Enhanced satellite processing capabilities required
   - Software-defined payload flexibility

**RedCap Full-Duplex and Half-Duplex Support:**

Release 19 extends NTN support to Reduced Capability (RedCap) devices:

1. **Full-Duplex RedCap**
   - Simultaneous transmit and receive capability
   - Improved latency performance
   - Higher data throughput potential
   - Suitable for advanced IoT applications

2. **Half-Duplex RedCap**
   - Simplified device architecture
   - Lower cost and power consumption
   - TDD (Time Division Duplex) operation
   - Ideal for battery-powered IoT devices

3. **RedCap Device Categories**
   - Category A: Higher capability, full-duplex support
   - Category B: Medium capability, half-duplex operation
   - Category C: Basic capability, simplified operation

---

## 3. NTN IoT Phase 3 Enhancements

### 3.1 Development Status and Objectives

**Phase 3 Status:** 30% complete as of September 2024

**Primary Objectives:**
- Extend NTN support to massive IoT deployments
- Enhance coverage for IoT devices in extreme conditions
- Optimize power consumption for battery-operated sensors
- Support diverse IoT use cases across FR1 and FR2

### 3.2 Downlink Coverage Enhancements for IoT

IoT devices typically have limited transmit power and antenna capabilities, making DL coverage critical:

**Enhanced Coverage Techniques:**

1. **Repetition and Redundancy**
   - Support for up to 256 repetitions for critical messages
   - Incremental redundancy for improved reliability
   - Adaptive repetition based on channel conditions

2. **Extended HARQ Processes**
   - Longer HARQ RTT (Round Trip Time) support
   - Increased number of HARQ processes
   - Asynchronous HARQ for flexibility

3. **Power Boosting Mechanisms**
   - Enhanced power allocation for control channels
   - Prioritized resource allocation for IoT traffic
   - Support for higher EIRP (Effective Isotropic Radiated Power)

### 3.3 FR1-NTN and FR2-NTN Support

**FR1-NTN (Frequency Range 1):**
- **Frequency Range:** 410 MHz - 7.125 GHz
- **Typical NTN Bands:** S-band (2 GHz), L-band (1.5 GHz)
- **Characteristics:**
  - Better propagation characteristics
  - Lower path loss
  - Suitable for wide-area coverage
  - Optimal for IoT and mobile broadband

**Key FR1-NTN Parameters:**
- Maximum channel bandwidth: 100 MHz
- Subcarrier spacing: 15 kHz, 30 kHz
- Optimized for coverage and capacity balance
- Support for both TDD and FDD operation

**FR2-NTN (Frequency Range 2):**
- **Frequency Range:** 24.25 GHz - 71 GHz
- **Typical NTN Bands:** Ka-band (26 GHz, 40 GHz)
- **Characteristics:**
  - Higher bandwidth availability
  - Increased atmospheric attenuation
  - Suitable for high-capacity backhaul
  - Weather-dependent performance

**Key FR2-NTN Parameters:**
- Maximum channel bandwidth: 400 MHz
- Subcarrier spacing: 60 kHz, 120 kHz
- High-throughput applications
- Beam-forming essential for link closure

### 3.4 IoT Use Case Support

Release 19 NTN IoT Phase 3 addresses multiple vertical markets:

**Agricultural IoT:**
- Soil moisture sensors
- Livestock tracking
- Equipment monitoring
- Precision agriculture applications

**Maritime IoT:**
- Vessel tracking and monitoring
- Environmental sensors
- Cargo monitoring
- Safety and security systems

**Energy Sector IoT:**
- Remote pipeline monitoring
- Oil and gas field sensors
- Renewable energy farm monitoring
- Grid infrastructure monitoring

**Environmental Monitoring:**
- Weather stations
- Wildlife tracking
- Disaster warning systems
- Pollution monitoring

---

## 4. NTN-Specific Parameters and Procedures

### 4.1 Timing and Synchronization Parameters

**cellSpecificKoffset_r17:**
- **Purpose:** Compensates for satellite-specific timing offsets
- **Range:** 0 to 1023 (representing 0 to 33.28 ms in steps of 32.5 μs)
- **Application:** Broadcast in SIB19-NTN
- **Usage:** UE applies offset during initial synchronization
- **Update Frequency:** Varies based on satellite orbit type
  - GSO: Infrequent updates (hours to days)
  - LEO: Frequent updates (minutes to hours)

**Implementation Requirements:**
```
K_offset_actual = cellSpecificKoffset_r17 × 32.5 μs
T_total = T_measured + K_offset_actual
```

**ta-Common_r17 (Common Timing Advance):**
- **Purpose:** Compensates for propagation delay to satellite
- **Calculation:** Based on satellite ephemeris data and UE location
- **Range:** 0 to 20,512 μs (for GEO) or extended range for specific orbits
- **Broadcast:** System Information Block (SIB19-NTN)
- **UE Application:** Used for initial random access timing

**Calculation Method:**
```
TA_common = 2 × distance / speed_of_light
where distance = satellite_altitude / cos(elevation_angle)
```

**For GEO Satellite Example:**
- Altitude: 35,786 km
- Minimum elevation: 10 degrees
- Maximum TA_common: ~242 ms

**For LEO Satellite Example:**
- Altitude: 600 km
- Minimum elevation: 10 degrees
- Maximum TA_common: ~4 ms

### 4.2 Autonomous Timing Advance Updates

Due to satellite motion (especially for NGSO), timing advance must be continuously updated:

**Doppler-Based TA Adjustment:**

1. **UE-Based Autonomous Updates**
   - UE calculates satellite velocity from ephemeris
   - Derives Doppler shift and applies frequency compensation
   - Updates TA autonomously without network signaling
   - Reduces signaling overhead significantly

2. **Update Frequency Requirements**
   - LEO satellites: Every 1-5 seconds
   - MEO satellites: Every 10-30 seconds
   - GEO satellites: Rarely (quasi-static)

3. **Ephemeris Data Provision**
   - Broadcast via SIB19-NTN
   - Contains satellite position and velocity vectors
   - Valid for specific time windows (typically 3-6 hours)
   - Requires periodic refresh

**TA Update Algorithm:**
```
TA(t+Δt) = TA(t) + (Δd / c) × 2
where:
  Δd = change in satellite distance
  c = speed of light (3 × 10^8 m/s)
```

### 4.3 Doppler Compensation

**Frequency Offset Characteristics:**

For L-band (1.5 GHz) NTN:
- **LEO Maximum Doppler:** ±40 kHz
- **MEO Maximum Doppler:** ±15 kHz
- **GEO Maximum Doppler:** <100 Hz

**Compensation Mechanisms:**

1. **Pre-Compensation at UE**
   - UE calculates expected Doppler shift
   - Adjusts transmit frequency accordingly
   - Ensures signal arrives at satellite with correct frequency

2. **Common Doppler Compensation**
   - Network broadcasts common Doppler reference
   - Reduces per-UE compensation requirements
   - Effective for spot beam centers

3. **Residual Doppler Handling**
   - Receiver must handle remaining frequency offset
   - Typically ±2-5 kHz after pre-compensation
   - Standard NR receivers can accommodate this range

**Doppler Calculation Formula:**
```
f_doppler = (v_radial / c) × f_carrier
where:
  v_radial = radial velocity component
  c = speed of light
  f_carrier = carrier frequency
```

### 4.4 HARQ and ARQ Adaptations

**HARQ RTT Adjustments:**

Standard terrestrial NR assumes 8 ms HARQ RTT. NTN requires extensions:

- **LEO NTN:** 10-40 ms HARQ RTT
- **GEO NTN:** 500-550 ms HARQ RTT

**Consequences:**
- Increased number of HARQ processes required
- Larger buffer requirements at transmitter and receiver
- Modified scheduling algorithms to account for long delays

**RLC ARQ Enhancements:**
- Longer timer values for acknowledgment waiting
- Increased window sizes for sustained throughput
- Optimized polling mechanisms

---

## 5. Satellite Types and Orbit Characteristics

### 5.1 Low Earth Orbit (LEO) Satellites

**Orbital Parameters:**
- **Altitude Range:** 500 km - 2,000 km
- **Typical Altitude:** 600 km (Starlink), 1,200 km (OneWeb)
- **Orbital Period:** 90-120 minutes
- **Velocity:** ~7.5 km/s at 600 km altitude
- **Coverage Duration:** 5-15 minutes per pass (depending on altitude)

**Link Characteristics:**
- **One-Way Propagation Delay:** 3-20 ms
- **Round-Trip Time (RTT):** 6-40 ms
- **Path Loss (L-band, 600 km):** ~165 dB
- **Doppler Shift (1.5 GHz):** ±35 kHz maximum

**Implementation Considerations:**
- Frequent handovers required (inter-satellite, inter-beam)
- Continuous tracking and ephemeris updates
- Significant Doppler compensation needed
- Constellation coordination essential for coverage
- Lower latency enables interactive services

**LEO Constellation Examples:**
- **Starlink:** ~12,000 planned satellites at 550-1,200 km
- **OneWeb:** ~650 satellites at 1,200 km
- **Kuiper (Amazon):** ~3,200 satellites at 590-630 km

### 5.2 Geostationary Orbit (GEO) Satellites

**Orbital Parameters:**
- **Altitude:** 35,786 km above Earth's equator
- **Orbital Period:** 24 hours (synchronous with Earth rotation)
- **Velocity:** ~3.07 km/s
- **Coverage Area:** ~1/3 of Earth's surface per satellite
- **Visibility:** Continuous for ground stations within coverage

**Link Characteristics:**
- **One-Way Propagation Delay:** ~250 ms
- **Round-Trip Time (RTT):** ~500-550 ms
- **Path Loss (L-band):** ~188 dB
- **Doppler Shift:** <100 Hz (minimal for stationary observers)

**Implementation Considerations:**
- High latency impacts interactive applications
- Suitable for broadcast and streaming services
- Minimal handover requirements
- Simpler tracking (nearly stationary relative to ground)
- Requires higher transmit power due to greater distance

**GEO Satellite Examples:**
- **Inmarsat:** Global maritime and aviation services
- **Intelsat:** Broadband and media distribution
- **Eutelsat:** European coverage with Ka-band capacity

### 5.3 Medium Earth Orbit (MEO) Satellites

While not the primary focus of Release 19, MEO deserves mention:

**Orbital Parameters:**
- **Altitude Range:** 2,000 km - 35,786 km
- **Typical Altitude:** 8,000-20,000 km
- **Orbital Period:** 2-12 hours
- **Coverage Duration:** 2-8 hours per pass

**Link Characteristics:**
- **One-Way Propagation Delay:** 40-150 ms
- **Doppler Shift:** ±5-15 kHz
- **Balance:** Between LEO agility and GEO coverage duration

**MEO Examples:**
- **O3b (SES):** 8,000 km altitude, equatorial constellation
- **GPS/Galileo:** Navigation systems at ~20,000 km

---

## 6. Compliance Matrix and 3GPP Specifications

### 6.1 Core NTN Architecture Specifications

**TS 38.300: NR and NG-RAN Overall Description**
- **Release:** 19 (expected v19.0.0 by Dec 2025)
- **Scope:** Architecture principles for NTN integration
- **Key Sections:**
  - Section 5.x: NTN deployment scenarios
  - Section 6.x: Protocol architecture adaptations
  - Section 16: NTN-specific procedures
- **Compliance Requirements:**
  - Understand overall NR architecture
  - Implement NTN-specific architectural elements
  - Support transparent and regenerative payload modes
  - Enable satellite-terrestrial interworking

**TS 38.821: Solutions for NR to Support Non-Terrestrial Networks**
- **Release:** Technical Report (informative)
- **Scope:** Solutions study and feasibility analysis
- **Key Content:**
  - Deployment scenarios and use cases
  - Link budget analysis
  - Timing and synchronization solutions
  - Mobility and handover procedures
- **Compliance Requirements:**
  - Reference for implementation decisions
  - Understanding of trade-offs and design choices
  - Baseline for optimization strategies

### 6.2 Physical Layer Specifications

**TS 38.211: Physical Channels and Modulation**
- **NTN Considerations:**
  - Extended cyclic prefix for long delays
  - Modified resource mapping for NTN scenarios
  - Timing advance range extensions
- **Compliance Points:**
  - Support for NTN-specific frame structures
  - Proper handling of extended delay scenarios

**TS 38.212: Multiplexing and Channel Coding**
- **NTN Considerations:**
  - Enhanced LDPC coding for poor link conditions
  - Polar code adaptations for control channels
- **Compliance Points:**
  - Support for increased code block sizes
  - Repetition and redundancy mechanisms

**TS 38.213: Physical Layer Procedures for Control**
- **NTN Considerations:**
  - Modified PDCCH monitoring patterns
  - Enhanced random access procedures
  - Timing advance reporting extensions
- **Compliance Points:**
  - Implement NTN-specific RACH procedures
  - Support extended TA reporting ranges

**TS 38.214: Physical Layer Procedures for Data**
- **NTN Considerations:**
  - Extended HARQ processes
  - Modified CSI reporting for satellite channels
- **Compliance Points:**
  - Support for increased HARQ RTT
  - Adapt link adaptation for NTN propagation

**TS 38.215: Physical Layer Measurements**
- **NTN Considerations:**
  - Satellite-specific measurement reporting
  - Ephemeris-aided measurements
- **Compliance Points:**
  - Implement NTN measurement procedures
  - Support satellite tracking measurements

### 6.3 Protocol Stack Specifications

**TS 38.321: Medium Access Control (MAC)**
- **NTN Adaptations:**
  - Modified HARQ procedures for extended RTT
  - Enhanced random access procedures
  - Timing advance maintenance mechanisms
- **Compliance Requirements:**
  - Support for NTN-specific MAC CE (Control Elements)
  - Implement autonomous TA adjustment procedures
  - Handle extended HARQ feedback delays

**TS 38.322: Radio Link Control (RLC)**
- **NTN Adaptations:**
  - Extended timer values for NTN delays
  - Modified window sizes for throughput optimization
  - Enhanced status reporting mechanisms
- **Compliance Requirements:**
  - Configure appropriate RLC timers for NTN
  - Support increased sequence number ranges
  - Implement efficient ARQ for long delays

**TS 38.323: Packet Data Convergence Protocol (PDCP)**
- **NTN Adaptations:**
  - Reordering timer extensions
  - Duplicate detection enhancements
  - Efficient header compression for satellite links
- **Compliance Requirements:**
  - Support NTN-specific PDCP configurations
  - Implement satellite-aware ROHC (Robust Header Compression)

**TS 38.331: Radio Resource Control (RRC)**
- **NTN Enhancements:**
  - SIB19-NTN for NTN-specific system information
  - Ephemeris data distribution
  - NTN capability signaling
  - Enhanced mobility procedures
- **Compliance Requirements:**
  - Broadcast and receive SIB19-NTN
  - Parse and apply ephemeris data
  - Support NTN-specific RRC procedures
  - Implement satellite-specific measurements and reporting

### 6.4 Radio Frequency Specifications

**TS 38.101-5: User Equipment Radio Transmission and Reception for NTN**
- **Scope:** NTN-specific UE RF requirements
- **Key Content:**
  - Operating bands for NTN (S-band, L-band, Ka-band)
  - Transmit power requirements
  - Receiver sensitivity specifications
  - Spurious emissions limits
  - Timing advance capabilities

**NTN Operating Bands (Examples):**

| Band | Frequency Range | Mode | Typical Use |
|------|----------------|------|-------------|
| n255 | 2.5-2.7 GHz (UL/DL) | TDD | S-band NTN |
| n256 | 2.0-2.2 GHz (UL/DL) | TDD | S-band NTN |
| n23 | 2.0-2.2 GHz (UL), 2.18-2.2 GHz (DL) | FDD | S-band NTN |
| n40 | 2.3-2.4 GHz (UL/DL) | TDD | S-band NTN |
| n77 | 3.3-4.2 GHz (UL/DL) | TDD | C-band NTN |
| n258 | 24.25-27.5 GHz (UL/DL) | TDD | Ka-band NTN |

**Compliance Requirements:**
- Support for specified NTN bands
- Meet transmit power specifications
- Achieve required receiver sensitivity
- Support extended timing advance ranges (up to 20,512 μs)
- Implement Doppler pre-compensation capabilities

**TS 38.104: Base Station Radio Transmission and Reception**
- **NTN Considerations:**
  - Satellite gateway RF requirements
  - Feeder link specifications
  - Service link specifications
- **Compliance Points:**
  - Gateway transmit power and EIRP
  - Receiver sensitivity for satellite signals
  - Spurious emissions limits

### 6.5 Network Architecture Specifications

**TS 23.501: System Architecture for 5G**
- **NTN Integration:**
  - Section 5.x: NTN deployment architectures
  - Integration with 5GC (5G Core Network)
  - Roaming and interconnection
- **Compliance Requirements:**
  - Implement appropriate NTN deployment model
  - Support satellite gateway interfaces
  - Enable seamless terrestrial-NTN interworking

**TS 23.502: Procedures for 5G System**
- **NTN Procedures:**
  - Registration and authentication for NTN UEs
  - Session management over NTN
  - Mobility procedures
- **Compliance Requirements:**
  - Implement NTN-specific procedures
  - Handle long delay impacts on procedures
  - Support intermittent connectivity scenarios

### 6.6 Testing and Conformance Specifications

**TS 38.521-5: User Equipment Conformance Specification for NTN**
- **Expected Release:** Release 19
- **Scope:** NTN-specific conformance tests
- **Test Categories:**
  - RF conformance tests
  - RRM (Radio Resource Management) tests
  - Protocol conformance tests
  - Performance tests
- **Compliance Requirements:**
  - Pass all applicable conformance tests
  - Demonstrate NTN-specific capabilities
  - Validate timing and synchronization accuracy
  - Verify Doppler compensation performance

**TS 38.533: User Equipment Conformance Testing**
- **NTN Test Scenarios:**
  - LEO satellite scenarios
  - GEO satellite scenarios
  - Handover and mobility tests
  - Coverage enhancement tests
- **Compliance Requirements:**
  - Support for satellite emulation environments
  - Pass end-to-end connectivity tests
  - Demonstrate robust performance under NTN conditions

---

## 7. Implementation Guidelines

### 7.1 System Design Considerations

**UE Implementation:**

1. **Hardware Requirements:**
   - Support for NTN operating bands (L/S/Ka-band)
   - Extended timing advance buffer (up to 550 ms for GEO)
   - Enhanced frequency tracking for Doppler (±40 kHz range)
   - Sufficient memory for increased HARQ processes
   - Power-efficient processing for battery-operated devices

2. **Software Requirements:**
   - Ephemeris data parsing and storage
   - Autonomous TA calculation and update algorithms
   - Doppler pre-compensation algorithms
   - NTN-specific RRC and system information handling
   - Satellite tracking and beam selection logic

3. **Antenna Considerations:**
   - Elevation angle coverage (typically 10-90 degrees)
   - Polarization support (circular for mobile, linear for fixed)
   - Gain requirements (higher for Ka-band)
   - Beam steering capability (for advanced implementations)

**Network Implementation:**

1. **Satellite Payload:**
   - **Transparent Payload:**
     - Frequency translation
     - Amplification
     - Lower complexity and cost
     - Higher propagation delay to ground gateway

   - **Regenerative Payload:**
     - On-board signal processing
     - Protocol termination
     - Inter-satellite links
     - Reduced end-to-end latency
     - Higher complexity and cost

2. **Ground Segment:**
   - Satellite gateways with high-capacity feeder links
   - Core network integration (5GC connection)
   - TT&C (Telemetry, Tracking, and Command) stations
   - Network operations center for constellation management

3. **Spectrum Management:**
   - Coordination with terrestrial networks (for shared bands)
   - Interference mitigation techniques
   - Regulatory compliance for each operating region
   - Dynamic spectrum sharing capabilities

### 7.2 Testing and Validation

**Laboratory Testing:**
- Channel emulation for satellite environments
- Doppler simulation and compensation testing
- Timing advance range verification
- Protocol stack conformance testing

**Field Testing:**
- Real satellite connectivity trials
- Coverage and performance measurements
- Mobility and handover validation
- End-to-end application testing

**Performance KPIs:**
- Peak data rates (DL/UL)
- Latency (user plane and control plane)
- Coverage area and availability
- Connection success rate
- Handover success rate
- Throughput under various conditions

### 7.3 Interoperability Considerations

**Terrestrial-NTN Interworking:**
- Seamless handover between terrestrial and satellite
- Load balancing and traffic steering
- Consistent QoS across access types
- Unified authentication and security

**Multi-Satellite Connectivity:**
- Inter-satellite handover procedures
- Satellite diversity for reliability
- Constellation-level optimization
- Multi-connectivity scenarios

---

## 8. Regulatory and Spectrum Considerations

### 8.1 Frequency Allocations

NTN operates in specific frequency bands allocated by the International Telecommunication Union (ITU):

**Mobile Satellite Service (MSS) Bands:**
- **L-band:** 1.5/1.6 GHz (primary for mobile services)
- **S-band:** 2.0/2.2 GHz (supplemental mobile capacity)
- **C-band:** 3.4-4.2 GHz (emerging NTN use)
- **Ka-band:** 20/30 GHz (high-capacity services)

**Regulatory Bodies:**
- ITU (International Telecommunication Union)
- National regulators (FCC, ETSI, etc.)
- 3GPP (technical standards)

### 8.2 Compliance Requirements

**Licensing:**
- Satellite operator licenses
- Spectrum usage rights
- Landing rights in service countries
- Type approval for UE devices

**Interference Protection:**
- Coordination with terrestrial networks
- Power flux density limits
- Unwanted emissions restrictions
- Adjacent channel protection

---

## 9. Use Cases and Application Scenarios

### 9.1 Primary Use Cases

**Rural Broadband:**
- Fixed wireless access for remote homes
- Community connectivity for underserved areas
- Backhaul for local networks
- Target: 50-100 Mbps DL, 10-20 Mbps UL

**Maritime Communications:**
- Vessel tracking and monitoring
- Crew connectivity and welfare
- Weather and navigation data
- Emergency communications

**Aviation Connectivity:**
- In-flight passenger connectivity
- Aircraft operations and maintenance data
- Air traffic management communications
- Enhanced safety services

**IoT and M2M:**
- Asset tracking (containers, vehicles, equipment)
- Environmental monitoring (weather, agriculture)
- Infrastructure monitoring (pipelines, power grids)
- Emergency services (disaster response, first responders)

**Emergency and Public Safety:**
- Disaster recovery communications
- First responder networks in remote areas
- National security and defense applications
- Backup for terrestrial network failures

### 9.2 Performance Targets

**LEO Constellation Performance:**
- **Latency:** 20-40 ms end-to-end
- **Throughput:** 100 Mbps+ DL, 20 Mbps+ UL (per beam)
- **Availability:** >99% globally
- **Coverage:** Worldwide including polar regions

**GEO Satellite Performance:**
- **Latency:** 500-600 ms end-to-end
- **Throughput:** 50-200 Mbps DL, 5-20 Mbps UL (per beam)
- **Availability:** >99.5% within coverage area
- **Coverage:** Regional to continental

---

## 10. Roadmap and Future Enhancements

### 10.1 Release 19 Milestones (2025)

**Q2 2025 (June):**
- RAN1 functional freeze
- Physical layer specifications finalized
- NTN for NR enhancements 70% complete

**Q3 2025 (September):**
- RAN2/3/4 functional freeze
- Protocol and architecture specifications finalized
- NTN IoT Phase 3 80% complete

**Q4 2025 (December):**
- Release 19 final completion
- Complete specification set published
- Conformance test specifications approved
- Implementation phase begins

### 10.2 Beyond Release 19

**Release 20 and Beyond (2026+):**
- Further NTN-IoT enhancements
- Advanced regenerative payload features
- Satellite-terrestrial network slicing
- AI/ML for satellite resource optimization
- Direct device-to-satellite for smartphones
- Expanded frequency band support
- Enhanced inter-satellite link capabilities

**Industry Adoption Timeline:**
- 2025-2026: Early commercial deployments
- 2026-2027: Widespread chipset availability
- 2027-2028: Mass market device integration
- 2028+: Ubiquitous NTN capability in devices

---

## 11. Compliance Checklist

### 11.1 Mandatory Requirements

**System Information Support:**
- [ ] SIB19-NTN reception and parsing
- [ ] Ephemeris data extraction and storage
- [ ] cellSpecificKoffset_r17 application
- [ ] ta-Common_r17 application

**Timing and Synchronization:**
- [ ] Extended timing advance support (up to 20,512 μs minimum)
- [ ] Autonomous TA update implementation
- [ ] Doppler pre-compensation capability
- [ ] Satellite tracking based on ephemeris

**Physical Layer:**
- [ ] Support for NTN operating bands (at least one)
- [ ] Extended HARQ process support
- [ ] Modified RACH procedures for NTN
- [ ] Enhanced CSI reporting for satellite channels

**Protocol Stack:**
- [ ] NTN-specific MAC CE handling
- [ ] Extended RLC timer support
- [ ] PDCP reordering for long delays
- [ ] RRC procedures for NTN

**Radio Frequency:**
- [ ] Compliance with TS 38.101-5 requirements
- [ ] Transmit power and EIRP specifications
- [ ] Receiver sensitivity for NTN bands
- [ ] Spurious emissions compliance

### 11.2 Optional Features

- [ ] Regenerative payload support
- [ ] Inter-satellite handover capability
- [ ] Multi-satellite connectivity
- [ ] RedCap device support (if applicable)
- [ ] FR2-NTN support (Ka-band)
- [ ] Dual connectivity (terrestrial + NTN)

### 11.3 Conformance Testing

- [ ] RF conformance tests passed (TS 38.521-5)
- [ ] RRM conformance tests passed
- [ ] Protocol conformance tests passed
- [ ] Performance tests passed
- [ ] End-to-end connectivity demonstrated
- [ ] Interoperability testing completed

---

## 12. References

### 12.1 3GPP Technical Specifications

1. **TS 38.300** - NR; NR and NG-RAN Overall Description (Release 19)
2. **TS 38.821** - Solutions for NR to support non-terrestrial networks (NTN) (Technical Report)
3. **TS 38.101-5** - NR; User Equipment (UE) radio transmission and reception; Part 5: NTN
4. **TS 38.211** - NR; Physical channels and modulation
5. **TS 38.212** - NR; Multiplexing and channel coding
6. **TS 38.213** - NR; Physical layer procedures for control
7. **TS 38.214** - NR; Physical layer procedures for data
8. **TS 38.215** - NR; Physical layer measurements
9. **TS 38.321** - NR; Medium Access Control (MAC) protocol specification
10. **TS 38.322** - NR; Radio Link Control (RLC) protocol specification
11. **TS 38.323** - NR; Packet Data Convergence Protocol (PDCP) specification
12. **TS 38.331** - NR; Radio Resource Control (RRC) protocol specification
13. **TS 38.104** - NR; Base Station (BS) radio transmission and reception
14. **TS 38.521-5** - NR; User Equipment (UE) conformance specification; Part 5: NTN
15. **TS 38.533** - NR; User Equipment (UE) conformance specification
16. **TS 23.501** - System architecture for the 5G System (5GS)
17. **TS 23.502** - Procedures for the 5G System (5GS)

### 12.2 Related Work Items

1. **RP-234058** - Solutions for NR NTN (Release 19)
2. **RP-234059** - Solutions for IoT NTN Phase 3 (Release 19)
3. **RP-234060** - RedCap support for NTN (Release 19)

### 12.3 External References

1. ITU Radio Regulations - Mobile Satellite Service allocations
2. FCC Rules and Regulations - Part 25 (Satellite Communications)
3. ETSI Standards - Satellite Earth Stations and Systems
4. Satellite Industry Association - Best Practices

---

## Appendix A: Glossary

**3GPP** - 3rd Generation Partnership Project
**ARQ** - Automatic Repeat Request
**CSI** - Channel State Information
**DMRS** - Demodulation Reference Signal
**EIRP** - Effective Isotropic Radiated Power
**FDD** - Frequency Division Duplex
**FR1** - Frequency Range 1 (410 MHz - 7.125 GHz)
**FR2** - Frequency Range 2 (24.25 GHz - 71 GHz)
**GEO** - Geostationary Earth Orbit
**GSO** - Geostationary Satellite Orbit
**HARQ** - Hybrid Automatic Repeat Request
**IoT** - Internet of Things
**LEO** - Low Earth Orbit
**MAC** - Medium Access Control
**MCS** - Modulation and Coding Scheme
**MEO** - Medium Earth Orbit
**NGSO** - Non-Geostationary Satellite Orbit
**NR** - New Radio (5G)
**NTN** - Non-Terrestrial Networks
**PDCP** - Packet Data Convergence Protocol
**PDCCH** - Physical Downlink Control Channel
**RACH** - Random Access Channel
**RAN** - Radio Access Network
**RedCap** - Reduced Capability
**RLC** - Radio Link Control
**ROHC** - Robust Header Compression
**RRC** - Radio Resource Control
**RTT** - Round Trip Time
**SIB** - System Information Block
**SSB** - Synchronization Signal Block
**TA** - Timing Advance
**TDD** - Time Division Duplex
**TT&C** - Telemetry, Tracking, and Command
**UE** - User Equipment

---

## Appendix B: Calculation Examples

### B.1 Timing Advance Calculation for GEO

Given:
- Satellite altitude: 35,786 km
- Elevation angle: 30 degrees
- Speed of light: 299,792 km/s

Distance to satellite:
```
d = altitude / sin(elevation) = 35,786 / sin(30°) = 71,572 km
```

One-way propagation delay:
```
t_prop = d / c = 71,572 / 299,792 = 238.7 ms
```

Timing Advance (round-trip):
```
TA = 2 × t_prop = 477.4 ms
```

### B.2 Doppler Shift Calculation for LEO

Given:
- Satellite altitude: 600 km
- Satellite velocity: 7.5 km/s
- Carrier frequency: 2 GHz
- Maximum radial velocity: 7.5 km/s (worst case)

Maximum Doppler shift:
```
f_doppler = (v_radial / c) × f_carrier
f_doppler = (7,500 / 299,792,000) × 2,000,000,000
f_doppler = 50 kHz
```

For L-band (1.5 GHz):
```
f_doppler = (7,500 / 299,792,000) × 1,500,000,000 = 37.5 kHz
```

### B.3 HARQ Process Requirement

For LEO with 30 ms RTT and 2 ms TTI (Transmission Time Interval):

Minimum HARQ processes:
```
N_HARQ = ceil(RTT / TTI) = ceil(30 / 2) = 15 processes
```

Standard NR uses 8 processes (8 ms RTT), so LEO requires at least double.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | October 2025 | SDR Technical Team | Initial release based on 3GPP Release 19 specifications |

---

## Approval

**Prepared by:** SDR Engineering Team
**Reviewed by:** Technical Standards Committee
**Approved by:** Chief Technology Officer
**Date:** October 2025
**Next Review:** March 2026

---

**End of Document**
