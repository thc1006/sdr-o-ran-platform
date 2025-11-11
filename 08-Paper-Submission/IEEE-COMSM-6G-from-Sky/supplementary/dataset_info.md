# Dataset and Reproducibility Information

## Dataset Availability Statement

To support reproducibility and enable further research, all datasets, source code, and supplementary materials associated with this manuscript will be made publicly available upon paper acceptance.

---

## Source Code Repository

**GitHub Repository:** https://github.com/thc1006/sdr-o-ran-platform

**License:** Apache License 2.0

**Contents:**
- Complete SDR platform implementation (3,142 lines)
- O-RAN components (Near-RT RIC, xApps) (2,487 lines)
- DRL training framework (PPO/SAC agents) (1,856 lines)
- Infrastructure-as-Code (Terraform, Kubernetes manifests) (1,329 lines)
- CI/CD pipelines (GitHub Actions workflows)
- Comprehensive documentation and API references

**Codebase Statistics:**
- Total Production Code: 8,814 lines
- Total Including Tests: 12,450 lines
- Languages: Python, Go, YAML, HCL (Terraform)
- Frameworks: FastAPI, gRPC, Kubernetes, Terraform

**Key Directories:**
```
sdr-o-ran-platform/
├── src/
│   ├── sdr-platform/              # VITA 49.2, gRPC, FastAPI
│   ├── oran-components/           # gNB, RIC, xApps
│   ├── drl-optimization/          # PPO/SAC training
│   └── security/                  # PQC implementation
├── infrastructure/
│   ├── terraform/                 # AWS EKS infrastructure
│   └── kubernetes/                # Deployment manifests
├── tests/                         # Unit and integration tests
├── docs/                          # API documentation
└── examples/                      # Usage examples
```

---

## Performance Evaluation Dataset

**Dataset DOI:** [To be assigned upon Zenodo publication after paper acceptance]

**Zenodo Repository:** https://zenodo.org/

**Dataset Description:**
Complete performance evaluation data from LEO, MEO, and GEO satellite scenarios.

**Included Data:**

### 1. Latency Measurements
- **File:** `latency_measurements.csv`
- **Format:** CSV with headers
- **Columns:**
  - `timestamp`: ISO 8601 timestamp
  - `orbit_type`: LEO/MEO/GEO
  - `satellite_altitude_km`: Altitude in kilometers
  - `elevation_angle_deg`: Elevation angle (10-90 degrees)
  - `propagation_delay_ms`: One-way propagation delay
  - `processing_delay_ms`: Ground station processing delay
  - `e2e_latency_ms`: End-to-end latency
  - `jitter_ms`: Latency jitter (standard deviation)
- **Size:** ~50 MB
- **Records:** 1,000,000+ measurements over 30-day period

### 2. Throughput Data
- **File:** `throughput_measurements.csv`
- **Format:** CSV with headers
- **Columns:**
  - `timestamp`: ISO 8601 timestamp
  - `elevation_angle_deg`: Satellite elevation angle
  - `dl_throughput_mbps`: Downlink throughput (Mbps)
  - `ul_throughput_mbps`: Uplink throughput (Mbps)
  - `sinr_db`: Signal-to-Interference-plus-Noise Ratio (dB)
  - `rsrp_dbm`: Reference Signal Received Power (dBm)
  - `rsrq_db`: Reference Signal Received Quality (dB)
  - `mcs_index`: Modulation and Coding Scheme index (0-28)
  - `prb_utilization`: Physical Resource Block utilization (0-1)
- **Size:** ~80 MB
- **Records:** 2,000,000+ measurements

### 3. DRL Training Data
- **File:** `drl_training_logs.jsonl`
- **Format:** JSON Lines (one JSON object per line)
- **Fields:**
  - `episode`: Episode number
  - `step`: Step within episode
  - `state`: Observation vector (RSRP, SINR, PRB utilization, elevation)
  - `action`: Action taken (beam, MCS, power)
  - `reward`: Reward received
  - `done`: Episode termination flag
  - `info`: Additional metrics (throughput, latency, packet loss)
- **Size:** ~200 MB
- **Episodes:** 10,000 training episodes (PPO) + 10,000 (SAC)

### 4. Cryptographic Performance
- **File:** `pqc_performance_benchmark.csv`
- **Format:** CSV with headers
- **Columns:**
  - `operation`: Operation type (keygen, encaps, decaps, sign, verify)
  - `algorithm`: Algorithm name (ML-KEM-1024, ML-DSA-87, X25519, Ed25519)
  - `iteration`: Test iteration number
  - `latency_us`: Operation latency (microseconds)
  - `cpu_cycles`: CPU cycles consumed
  - `memory_kb`: Peak memory usage (KB)
- **Size:** ~10 MB
- **Records:** 100,000+ benchmark runs

### 5. System Resource Metrics
- **File:** `system_metrics.parquet`
- **Format:** Apache Parquet (compressed columnar format)
- **Columns:**
  - `timestamp`: ISO 8601 timestamp
  - `component`: Component name (gNB, RIC, xApp, SDR)
  - `cpu_usage_percent`: CPU utilization (0-100%)
  - `memory_usage_mb`: Memory usage (MB)
  - `network_rx_mbps`: Network receive throughput (Mbps)
  - `network_tx_mbps`: Network transmit throughput (Mbps)
  - `disk_io_mbps`: Disk I/O throughput (Mbps)
  - `gpu_usage_percent`: GPU utilization for DRL inference (0-100%)
- **Size:** ~150 MB (compressed)
- **Records:** 5,000,000+ time-series measurements (1-second granularity)

---

## Experimental Configuration

**Hardware Setup:**
- **SDR:** Ettus USRP X310 with GPSDO
- **Antenna:** Multi-band (C/Ku/Ka) with azimuth/elevation tracking
- **Compute:** 3× servers (32-core, 128GB RAM, 10 GbE networking)
- **Cloud:** AWS EKS (m5.2xlarge nodes × 6)

**Software Versions:**
- OpenAirInterface 5G-NTN: v2.1.0
- O-RAN SC Near-RT RIC: Release H
- Kubernetes: v1.33
- Nephio: Release 2
- Stable Baselines3: v2.5.0
- liboqs (PQC): v0.12.0

**Satellite Parameters:**
- **LEO:** 600 km altitude, 10 MHz bandwidth, TDD configuration
- **MEO:** 10,000 km altitude, 10 MHz bandwidth, TDD
- **GEO:** 35,786 km altitude, 10 MHz bandwidth, TDD
- **Channel Model:** ITU-R P.681-12 (propagation) + 3GPP TR 38.811 (NTN)

---

## Reproducibility Instructions

**Step 1: Clone Repository**
```bash
git clone https://github.com/thc1006/sdr-o-ran-platform.git
cd sdr-o-ran-platform
```

**Step 2: Install Dependencies**
```bash
# Python dependencies
pip install -r requirements.txt

# System dependencies (Ubuntu 22.04)
sudo apt-get install -y build-essential cmake libboost-all-dev \
    libusb-1.0-0-dev uhd-host libuhd-dev
```

**Step 3: Deploy Infrastructure**
```bash
# AWS EKS cluster (requires AWS credentials)
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# Configure kubectl
aws eks update-kubeconfig --name sdr-oran-ntn-cluster --region us-west-2
```

**Step 4: Deploy O-RAN Components**
```bash
cd infrastructure/kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f near-rt-ric/
kubectl apply -f xapps/
kubectl apply -f monitoring/
```

**Step 5: Run SDR Platform**
```bash
cd src/sdr-platform
python3 sdr_receiver.py --config config/usrp_x310.yaml

# In another terminal
python3 grpc_server.py --port 50051

# In another terminal
python3 rest_gateway.py --port 8000
```

**Step 6: Run Experiments**
```bash
# Latency evaluation
python3 experiments/measure_latency.py --orbit LEO --duration 3600

# Throughput evaluation
python3 experiments/measure_throughput.py --elevation-range 10-90

# DRL training
python3 experiments/train_drl_agent.py --algorithm PPO --episodes 10000

# PQC benchmarks
python3 experiments/benchmark_pqc.py --iterations 1000
```

**Step 7: Analyze Results**
```bash
# Generate figures and tables
python3 analysis/generate_figures.py --input data/ --output figures/

# Statistical analysis
python3 analysis/statistical_tests.py --input data/ --output results/
```

---

## Data Access and License

**Access:** All datasets will be published on Zenodo with open access (CC BY 4.0 license) upon paper acceptance.

**Citation:**
```bibtex
@dataset{tsai2026sdr_oran_ntn_dataset,
  author = {Tsai, Hsiu-Chi},
  title = {Performance Evaluation Dataset for Cloud-Native SDR-O-RAN Platform for Non-Terrestrial Networks},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

**Contact for Data:**
- Email: hctsai@linux.com
- GitHub Issues: https://github.com/thc1006/sdr-o-ran-platform/issues

---

## Ethical Considerations

- All experiments were conducted in compliance with FCC regulations (Part 5 Experimental License)
- No human subjects were involved in this research
- No personally identifiable information (PII) is included in datasets
- All network traffic in datasets has been anonymized
- Cloud resources were provisioned in accordance with AWS Acceptable Use Policy

---

## Acknowledgments

This work builds upon the following open-source projects:
- OpenAirInterface Software Alliance (https://openairinterface.org/)
- O-RAN Software Community (https://o-ran-sc.org/)
- Kubernetes and Cloud Native Computing Foundation
- Linux Foundation Nephio Project
- Open Quantum Safe (liboqs) project

---

**Last Updated:** 2025-10-27
**Status:** Datasets will be published on Zenodo upon paper acceptance
**Estimated Dataset Publication:** June 2026 (concurrent with paper publication)
