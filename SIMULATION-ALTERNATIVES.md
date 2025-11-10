# Simulation Alternatives for SDR-O-RAN Platform

Last Updated: 2025-11-10
Research Date: 2025-11-10

This document outlines simulation alternatives to enable testing and development without expensive hardware or complex infrastructure.

---

## Executive Summary

The SDR-O-RAN platform requires three major categories of hardware/infrastructure:
1. **SDR Hardware** (USRP X310, ~$7,500)
2. **O-RAN Infrastructure** (Near-RT RIC, E2 interface)
3. **Network Simulation** (5G RAN, satellite links)

This document provides concrete alternatives for each category based on recent research (2024).

---

## 1. Network Simulation: ns-O-RAN

### Overview
**ns-O-RAN** is the first open-source simulation platform combining a functional 4G/5G protocol stack in ns-3 with an O-RAN-compliant E2 interface.

### Key Features
- Full 4G/5G RAN simulation
- O-RAN-compliant E2 interface (v1.01, v2.0, v3.0)
- Support for KPM v3 and pre-RC v1.01
- Integration with real Near-RT RIC
- No hardware required

### Developers
- Institute for the Wireless Internet of Things (WIoT), Northeastern University
- Sapienza University of Rome
- University of Padova
- Mavenir

### Installation

```bash
# Clone ns-O-RAN repository
git clone https://github.com/wineslab/ns-o-ran-ns3-mmwave.git
cd ns-o-ran-ns3-mmwave

# Or use O-RAN SC official version
git clone https://github.com/o-ran-sc/sim-ns3-o-ran-e2.git
cd sim-ns3-o-ran-e2

# Build ns-3 with O-RAN module
./ns3 configure --enable-examples --enable-tests
./ns3 build
```

### Use Cases for Our Project
1. **xApp Testing**: Test Traffic Steering xApp with simulated E2 KPM indications
2. **DRL Training**: Generate realistic datasets for training
3. **Performance Validation**: Measure latency, throughput without hardware
4. **Integration Testing**: Verify E2 interface compliance

### Integration with SDR-O-RAN Platform

```python
# Example: Connect DRL Trainer to ns-O-RAN simulation
# 1. Run ns-O-RAN simulation with E2 interface
# 2. Connect our xApp to simulated RIC
# 3. Train DRL model with simulated data
# 4. Export model for production use
```

### Publications
- "ns-O-RAN: Simulating O-RAN 5G Systems in ns-3" (ACM WNS3 2023)
  - DOI: 10.1145/3592149.3592161
- "Programmable and Customized Intelligence for Traffic Steering in 5G Networks Using Open RAN Architectures" (IEEE TMC 2024)
  - DOI: 10.1109/TMC.2023.3266642

### Resources
- GitHub: https://github.com/wineslab/ns-o-ran-ns3-mmwave
- O-RAN SC: https://github.com/o-ran-sc/sim-ns3-o-ran-e2
- OpenRAN Gym: https://openrangym.com/tutorials/ns-o-ran
- Paper: https://arxiv.org/abs/2305.06906

---

## 2. SDR Simulation: DAWN + RadioConda

### DAWN (Distributed Analysis of Wireless at Nextscale)

**Overview**:
DAWN is a novel simulation framework for large-scale design space exploration (DSE) of unmodified SDR applications in a scalable, high-fidelity, virtual physics environment.

**Key Features**:
- Simulates electromagnetic environment
- Runs unmodified GNU Radio applications
- Software-defined physics simulation
- Hardware emulation capabilities
- Presented at GNU Radio Conference 2024

**Use Cases**:
- Test GNU Radio flowgraphs without USRP
- Simulate multiple SDR stations
- Validate signal processing algorithms
- Develop without $7,500 hardware

**Status**: Cutting-edge (2024), may require contact with developers

### RadioConda

**Overview**:
Conda-based virtual environment with comprehensive SDR packages pre-installed.

**Included Packages**:
- GNU Radio
- RF applications
- SDR hardware support (drivers)
- Key out-of-tree modules
- USRP simulation support

**Installation**:

```bash
# Install RadioConda
wget https://github.com/ryanvolz/radioconda/releases/latest/download/radioconda-Linux-x86_64.sh
bash radioconda-Linux-x86_64.sh

# Activate environment
conda activate base

# Verify GNU Radio installation
gnuradio-config-info --version
```

**Use Cases**:
- Development environment without hardware
- Testing GNU Radio blocks
- Prototyping signal processing
- CI/CD integration

**Integration with Our Platform**:

```bash
# Use RadioConda for GNU Radio development
conda activate base

# Run our DVB-S2 receiver in simulation mode
cd 03-Implementation/sdr-platform/gnuradio-flowgraphs
python3 dvbs2_multiband_receiver.py --simulate
```

### Hardware Emulation: Aldec HES + GNU Radio

**Overview**:
Aldec HES (Hardware Emulation System) boards integrate with GNU Radio and USRP, providing FPGA-based emulation.

**Features**:
- HES Proto-AXI interface
- Integration with GNU Radio framework
- HDL simulator connection
- Perfect for design prototyping

**Cost**: More affordable than USRP X310 but still requires hardware

---

## 3. O-RAN RIC Simulation: FlexRIC + RIC-TaaP

### FlexRIC

**Overview**:
O-RAN SC project providing a flexible Near-RT RIC implementation for testing.

**Key Features**:
- E2AP v1.01, v2.0, v3.0 support
- KPM v3.0 service model
- RC (RAN Control) pre-standard
- Works with srsRAN Project
- No expensive hardware required

**Installation**:

```bash
# Install FlexRIC
git clone https://gitlab.eurecom.fr/mosaic5g/flexric.git
cd flexric
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

**Use with Our xApp**:

```bash
# 1. Start FlexRIC Near-RT RIC
./flexric

# 2. Run srsRAN gNB with E2 agent
cd srsRAN_Project
gnb -c config.yml

# 3. Deploy our Traffic Steering xApp
cd 03-Implementation/orchestration/nephio/packages/oran-ric/xapps
# Modify to connect to FlexRIC endpoint
python3 traffic-steering-xapp.py --ric-endpoint localhost:36421
```

**Documentation**: https://docs.srsran.com/projects/project/en/latest/tutorials/source/near-rt-ric/

### RIC Testing as a Platform (RIC-TaaP)

**Overview**:
Open-source initiative by Orange for streamlined xApp/rApp testing using digital twins.

**Key Features**:
- Digital twin of real networks
- Simulates terrain, traffic, configuration
- Controlled, simulated environment
- No need for expensive testbeds
- Functional and operational testing

**Benefits**:
- Faster xApp development
- Proven digital-twin networks
- Innovation without infrastructure
- Cost-effective testing

**Resources**:
- Blog: https://hellofuture.orange.com/en/ric-testing-as-a-platform
- GitHub: https://github.com/Orange-OpenSource/ns-O-RAN-flexric

**Integration**:

```bash
# Clone Orange's ns-O-RAN-flexric
git clone https://github.com/Orange-OpenSource/ns-O-RAN-flexric.git
cd ns-O-RAN-flexric

# Run RAN simulator with FlexRIC
# This provides E2 termination compliant with FlexRIC
./run_simulation.sh
```

---

## 4. Complete Simulation Stack for SDR-O-RAN

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4: xApp Testing                                   │
│ - Our Traffic Steering xApp                             │
│ - DRL Model Loading                                     │
│ - Decision Logic Testing                                │
└─────────────────────────────────────────────────────────┘
                          ↓ E2 Interface
┌─────────────────────────────────────────────────────────┐
│ Layer 3: RIC Simulation                                 │
│ - FlexRIC Near-RT RIC                                   │
│ - E2 Termination                                        │
│ - SDL (Redis)                                           │
└─────────────────────────────────────────────────────────┘
                          ↓ E2AP
┌─────────────────────────────────────────────────────────┐
│ Layer 2: RAN Simulation                                 │
│ - ns-O-RAN (ns-3 based)                                 │
│ - 5G NR stack                                           │
│ - Multiple UEs and cells                                │
└─────────────────────────────────────────────────────────┘
                          ↓ Data samples
┌─────────────────────────────────────────────────────────┐
│ Layer 1: SDR Simulation                                 │
│ - DAWN simulation framework                             │
│ - GNU Radio (RadioConda)                                │
│ - Virtual USRP                                          │
└─────────────────────────────────────────────────────────┘
```

### Setup Steps

#### Step 1: Install ns-O-RAN

```bash
# Clone and build
git clone https://github.com/wineslab/ns-o-ran-ns3-mmwave.git
cd ns-o-ran-ns3-mmwave
./ns3 configure --enable-examples
./ns3 build

# Run example scenario
./ns3 run "oran-scenario --simTime=10 --numUes=5"
```

#### Step 2: Install FlexRIC

```bash
git clone https://gitlab.eurecom.fr/mosaic5g/flexric.git
cd flexric
mkdir build && cd build
cmake .. -DRIC_AGENT=OFF
make -j$(nproc)
sudo make install
```

#### Step 3: Connect Components

```bash
# Terminal 1: Start FlexRIC RIC
flexric

# Terminal 2: Start ns-O-RAN with E2 agent
cd ns-o-ran-ns3-mmwave
./ns3 run "oran-scenario --e2-term-ip=127.0.0.1 --e2-term-port=36422"

# Terminal 3: Deploy our xApp
cd 03-Implementation/orchestration/nephio/packages/oran-ric/xapps
python3 traffic-steering-xapp.py --simulate
```

#### Step 4: Run DRL Training with Simulated Data

```bash
# Terminal 4: Train DRL model
cd 03-Implementation/ai-ml-pipeline/training
python3 drl_trainer.py \
  --algorithm PPO \
  --timesteps 100000 \
  --data-source simulation \
  --ns3-endpoint localhost:50051
```

---

## 5. Cost-Benefit Analysis

### Hardware-Based Approach

```
USRP X310 with GPSDO: $7,500
Antenna system: Included
Server infrastructure: $12,000
Total CAPEX: $19,500

Operational complexity: High
Setup time: Weeks
Flexibility: Low (tied to hardware)
```

### Simulation-Based Approach

```
Software costs: $0 (all open source)
Server infrastructure: $2,000 (commodity server)
Total CAPEX: $2,000

Operational complexity: Medium
Setup time: Days
Flexibility: High (easy to modify scenarios)
Scalability: Excellent (run multiple simulations)
CI/CD integration: Easy
```

**Savings**: $17,500 (90% cost reduction)

---

## 6. Validation Strategy

### Simulation Validation

```
1. Develop with simulation
   ↓
2. Validate algorithms with synthetic data
   ↓
3. Benchmark against literature results
   ↓
4. Generate test cases for hardware
   ↓
5. Deploy on real hardware (when available)
```

### Confidence Building

```
- Unit tests: Run in CI/CD with simulation
- Integration tests: Verify E2 interface compliance
- Performance tests: Measure latency, throughput in simulation
- Stress tests: Scale to 100s of UEs
- Regression tests: Detect algorithm changes
```

---

## 7. Implementation Roadmap

### Phase 1: Core Simulation Setup (1 week)

```
Week 1:
- Install ns-O-RAN
- Install FlexRIC
- Set up RadioConda
- Verify connectivity between components
- Document setup procedure
```

### Phase 2: Component Integration (2 weeks)

```
Week 2-3:
- Connect xApp to FlexRIC
- Integrate DRL trainer with ns-O-RAN data
- Validate E2 interface messages
- Test end-to-end data flow
```

### Phase 3: Validation and Testing (2 weeks)

```
Week 4-5:
- Create test scenarios
- Benchmark against literature
- Performance profiling
- Bug fixing
- Documentation
```

### Phase 4: Production Preparation (1 week)

```
Week 6:
- CI/CD integration
- Deployment automation
- Monitoring setup
- User documentation
```

**Total Time**: 6 weeks to full simulation capability

---

## 8. References and Resources

### Academic Papers

1. Lacava et al., "ns-O-RAN: Simulating O-RAN 5G Systems in ns-3", ACM WNS3, 2023
2. Polese et al., "Understanding O-RAN: Architecture, Interfaces, Algorithms, Security, and Research Challenges", IEEE Communications Surveys & Tutorials, 2023
3. Bonati et al., "OpenRAN Gym: AI/ML Development, Data Collection, and Testing for O-RAN on PAWR Platforms", Computer Networks, 2023

### GitHub Repositories

- ns-O-RAN: https://github.com/wineslab/ns-o-ran-ns3-mmwave
- O-RAN SC sim: https://github.com/o-ran-sc/sim-ns3-o-ran-e2
- FlexRIC: https://gitlab.eurecom.fr/mosaic5g/flexric
- Orange ns-O-RAN-flexric: https://github.com/Orange-OpenSource/ns-O-RAN-flexric
- srsRAN Project: https://github.com/srsran/srsRAN_Project
- RadioConda: https://github.com/ryanvolz/radioconda

### Documentation

- ns-3: https://www.nsnam.org/
- O-RAN SC: https://docs.o-ran-sc.org/
- FlexRIC: https://gitlab.eurecom.fr/mosaic5g/flexric/-/wikis/home
- OpenRAN Gym: https://openrangym.com/
- GNU Radio: https://wiki.gnuradio.org/

### Tutorials

- "5G ns-3 with O-RAN near-RT RIC bronze version": https://openrangym.com/tutorials/ns-o-ran
- "O-RAN NearRT-RIC and xApp — srsRAN": https://docs.srsran.com/projects/project/en/latest/tutorials/source/near-rt-ric/
- GNU Radio Conference 2024: https://events.gnuradio.org/event/24/

---

## 9. Support and Community

### Getting Help

1. **ns-O-RAN**: GitHub issues or email authors
2. **FlexRIC**: GitLab issues or mailing list
3. **GNU Radio**: Discuss mailing list
4. **O-RAN SC**: Slack channels

### Contributing Back

If you develop improvements:
1. Open pull requests to upstream projects
2. Share scenarios and configurations
3. Document integration challenges
4. Publish validation results

---

## 10. Next Steps

To implement simulation for this project:

1. **Immediate (This Sprint)**:
   - Install ns-O-RAN and FlexRIC
   - Run example scenarios
   - Document setup process

2. **Short-term (Next Sprint)**:
   - Integrate xApp with FlexRIC
   - Connect DRL trainer to simulation data
   - Create test scenarios

3. **Medium-term (Next Month)**:
   - Full validation with simulated data
   - Performance benchmarking
   - CI/CD integration

4. **Long-term (Next Quarter)**:
   - Prepare for hardware transition
   - Document simulation→hardware migration
   - Maintain both paths (simulation + hardware)

---

**Status**: Research complete, ready for implementation
**Cost**: $0 (all open source)
**Time to implement**: 6 weeks
**Benefit**: Full testing capability without $19,500 hardware

**Maintainer**: Hsiu-Chi Tsai (thc1006@ieee.org)
**Last Updated**: 2025-11-10
