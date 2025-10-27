# SDR-O-RAN Infrastructure Architecture

This document describes the architectural design of the SDR-O-RAN platform infrastructure on AWS.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud (us-east-1)                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    VPC (10.0.0.0/16)                                  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Availability Zone 1 (us-east-1a)                               │ │ │
│  │  │  ┌──────────────────┐  ┌──────────────────┐                    │ │ │
│  │  │  │  Public Subnet   │  │  Private Subnet  │                    │ │ │
│  │  │  │  10.0.0.0/20     │  │  10.0.16.0/20    │                    │ │ │
│  │  │  │                  │  │                  │                    │ │ │
│  │  │  │  ┌────────────┐  │  │  ┌────────────┐ │                    │ │ │
│  │  │  │  │ NAT Gateway│  │  │  │ EKS Node 1 │ │                    │ │ │
│  │  │  │  └────────────┘  │  │  │ m5.2xlarge │ │                    │ │ │
│  │  │  │                  │  │  └────────────┘ │                    │ │ │
│  │  │  └──────────────────┘  └──────────────────┘                    │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Availability Zone 2 (us-east-1b)                               │ │ │
│  │  │  ┌──────────────────┐  ┌──────────────────┐                    │ │ │
│  │  │  │  Public Subnet   │  │  Private Subnet  │                    │ │ │
│  │  │  │  10.0.32.0/20    │  │  10.0.48.0/20    │                    │ │ │
│  │  │  │                  │  │                  │                    │ │ │
│  │  │  │  ┌────────────┐  │  │  ┌────────────┐ │                    │ │ │
│  │  │  │  │ NAT Gateway│  │  │  │ EKS Node 2 │ │                    │ │ │
│  │  │  │  └────────────┘  │  │  │ m5.2xlarge │ │                    │ │ │
│  │  │  │                  │  │  └────────────┘ │                    │ │ │
│  │  │  └──────────────────┘  └──────────────────┘                    │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Availability Zone 3 (us-east-1c)                               │ │ │
│  │  │  ┌──────────────────┐  ┌──────────────────┐                    │ │ │
│  │  │  │  Public Subnet   │  │  Private Subnet  │                    │ │ │
│  │  │  │  10.0.64.0/20    │  │  10.0.80.0/20    │                    │ │ │
│  │  │  │                  │  │                  │                    │ │ │
│  │  │  │  ┌────────────┐  │  │  ┌────────────┐ │                    │ │ │
│  │  │  │  │ NAT Gateway│  │  │  │ EKS Node 3 │ │                    │ │ │
│  │  │  │  └────────────┘  │  │  │ m5.2xlarge │ │                    │ │ │
│  │  │  │                  │  │  └────────────┘ │                    │ │ │
│  │  │  └──────────────────┘  └──────────────────┘                    │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    Internet Gateway                              │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      EKS Control Plane                                │ │
│  │                      (Managed by AWS)                                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │ │
│  │  │ API Server  │  │  Scheduler  │  │  Controller │                  │ │
│  │  └─────────────┘  └─────────────┘  │  Manager    │                  │ │
│  │                                     └─────────────┘                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        AWS Services                                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │ │
│  │  │   KMS    │  │CloudWatch│  │    IAM   │  │    S3    │             │ │
│  │  │Encryption│  │   Logs   │  │   IRSA   │  │ Backend  │             │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Network Architecture

### VPC Design

```
VPC CIDR: 10.0.0.0/16 (65,536 IPs)
│
├── Availability Zone 1 (us-east-1a)
│   ├── Public Subnet: 10.0.0.0/20 (4,096 IPs)
│   │   └── NAT Gateway, ALB/NLB
│   └── Private Subnet: 10.0.16.0/20 (4,096 IPs)
│       └── EKS Worker Nodes, Pods
│
├── Availability Zone 2 (us-east-1b)
│   ├── Public Subnet: 10.0.32.0/20 (4,096 IPs)
│   │   └── NAT Gateway, ALB/NLB
│   └── Private Subnet: 10.0.48.0/20 (4,096 IPs)
│       └── EKS Worker Nodes, Pods
│
└── Availability Zone 3 (us-east-1c)
    ├── Public Subnet: 10.0.64.0/20 (4,096 IPs)
    │   └── NAT Gateway, ALB/NLB
    └── Private Subnet: 10.0.80.0/20 (4,096 IPs)
        └── EKS Worker Nodes, Pods

Total: 24,576 IPs allocated, 40,960 IPs reserved for future expansion
```

### Traffic Flow

```
Internet
   │
   ▼
Internet Gateway
   │
   ▼
Public Subnets
   │
   ├─── Network/Application Load Balancer ───┐
   │                                          │
   └─── NAT Gateways                          │
           │                                  │
           ▼                                  ▼
    Private Subnets ◄──────────────────── Kubernetes
           │                               Services
           ▼
    EKS Worker Nodes
           │
           ├─── System Pods (kube-system)
           ├─── Monitoring (prometheus, grafana)
           └─── Application Pods (ricplt)
```

## Compute Architecture

### EKS Cluster

```
┌─────────────────────────────────────────────────────────────┐
│                    EKS Control Plane                        │
│                    (AWS Managed)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Server  │  │  etcd Store  │  │  Scheduler   │      │
│  │  (HA 3x)     │  │  (HA 3x)     │  │  (HA 3x)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Controller  │  │  Cloud Ctrl  │  │   Addons     │      │
│  │  Manager     │  │  Manager     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker Node Group                        │
│                    (Customer Managed)                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Node 1 (m5.2xlarge)                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │  │
│  │  │   kubelet    │  │  kube-proxy  │  │ containerd │ │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │  │
│  │  8 vCPU, 32GB RAM, 100GB gp3 Storage               │  │
│  │  Pods: 110 max                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Node 2 (m5.2xlarge) - Same configuration           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Node 3 (m5.2xlarge) - Same configuration           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Auto-scaling: 3-10 nodes                                  │
└─────────────────────────────────────────────────────────────┘
```

### Node Specifications

| Component | Specification |
|-----------|--------------|
| Instance Type | m5.2xlarge |
| vCPUs | 8 per node (24 total) |
| Memory | 32GB per node (96GB total) |
| Network | Up to 10 Gbps |
| Storage | 100GB gp3 per node |
| IOPS | 3,000 baseline, 16,000 max |
| Throughput | 125 MB/s |
| Max Pods | 110 per node |
| Max Nodes | 10 (scalable) |

## Storage Architecture

### EBS Volume Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              EBS CSI Driver                          │  │
│  │              (AWS Managed)                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Storage Classes                              │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐   │  │
│  │  │  gp3-default   │  │  redis-sdl-storage       │   │  │
│  │  │  (General)     │  │  (High Performance)      │   │  │
│  │  │  3K IOPS       │  │  16K IOPS                │   │  │
│  │  │  125 MB/s      │  │  1000 MB/s               │   │  │
│  │  └────────────────┘  └──────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Persistent Volumes                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │  │
│  │  │ Node OS Disk │  │ Redis SDL PV │  │  App PVs  │  │  │
│  │  │   100GB gp3  │  │   50GB gp3   │  │  Variable │  │  │
│  │  │   Per Node   │  │   16K IOPS   │  │           │  │  │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              KMS Encryption                          │  │
│  │              (AES-256)                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Storage Performance

| Storage Type | Use Case | IOPS | Throughput | Encryption |
|-------------|----------|------|------------|------------|
| Node OS Disk | System | 3,000 | 125 MB/s | KMS |
| Redis SDL | Database | 16,000 | 1000 MB/s | KMS |
| App Storage | General | 3,000-16,000 | 125-1000 MB/s | KMS |

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Stack                           │
│                                                             │
│  Layer 1: Network Security                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │  Security  │  │   NACLs    │  │  Network   │     │  │
│  │  │   Groups   │  │            │  │  Policies  │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Layer 2: Identity & Access                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │    IAM     │  │    IRSA    │  │    RBAC    │     │  │
│  │  │   Roles    │  │            │  │            │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Layer 3: Data Security                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │    KMS     │  │  Secrets   │  │    TLS     │     │  │
│  │  │ Encryption │  │ Encryption │  │   Certs    │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Layer 4: Application Security                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │    PSS     │  │   Policy   │  │   Service  │     │  │
│  │  │  Standards │  │   Engine   │  │    Mesh    │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Layer 5: Monitoring & Audit                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ CloudWatch │  │   Audit    │  │  Security  │     │  │
│  │  │    Logs    │  │    Logs    │  │   Alerts   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### IAM Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IAM Roles                                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  EKS Cluster Role                                    │  │
│  │  • AmazonEKSClusterPolicy                            │  │
│  │  • AmazonEKSVPCResourceController                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  EKS Node Role                                       │  │
│  │  • AmazonEKSWorkerNodePolicy                         │  │
│  │  • AmazonEKS_CNI_Policy                              │  │
│  │  • AmazonEC2ContainerRegistryReadOnly                │  │
│  │  • AmazonEBSCSIDriverPolicy                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Service Account Roles (IRSA)                        │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐   │  │
│  │  │  VPC CNI Role  │  │  EBS CSI Driver Role     │   │  │
│  │  └────────────────┘  └──────────────────────────┘   │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐   │  │
│  │  │  ALB Ctrl Role │  │  Cluster Autoscaler Role │   │  │
│  │  └────────────────┘  └──────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Monitoring Stack                           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Collection                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │  │
│  │  │  CloudWatch  │  │  Container   │  │   Node   │   │  │
│  │  │    Agent     │  │   Insights   │  │ Exporter │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Processing                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │  │
│  │  │  CloudWatch  │  │  Prometheus  │  │   Loki   │   │  │
│  │  │     Logs     │  │    Server    │  │          │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Visualization                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │  │
│  │  │  CloudWatch  │  │   Grafana    │  │   EKS    │   │  │
│  │  │  Dashboard   │  │  Dashboard   │  │ Console  │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Alerting                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │  │
│  │  │  CloudWatch  │  │  AlertManager│  │   SNS    │   │  │
│  │  │    Alarms    │  │              │  │          │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## High Availability Architecture

### Multi-AZ Deployment

```
                    Application Load Balancer
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
      AZ-1 (33%)        AZ-2 (33%)        AZ-3 (34%)
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │  Node 1  │      │  Node 2  │      │  Node 3  │
    │          │      │          │      │          │
    │ ┌──────┐ │      │ ┌──────┐ │      │ ┌──────┐ │
    │ │E2Term│ │      │ │E2Term│ │      │ │E2Term│ │
    │ │ Pod  │ │      │ │ Pod  │ │      │ │ Pod  │ │
    │ └──────┘ │      │ └──────┘ │      │ └──────┘ │
    │          │      │          │      │          │
    │ ┌──────┐ │      │ ┌──────┐ │      │ ┌──────┐ │
    │ │Redis │ │      │ │Redis │ │      │ │Redis │ │
    │ │ SDL  │ │      │ │ SDL  │ │      │ │ SDL  │ │
    │ └──────┘ │      │ └──────┘ │      │ └──────┘ │
    └──────────┘      └──────────┘      └──────────┘
```

### Failure Scenarios

| Scenario | Impact | Recovery |
|----------|--------|----------|
| Single Node Failure | 33% capacity loss | Auto-scaling creates new node (5 min) |
| AZ Failure | 33% capacity loss | Traffic routes to other 2 AZs (instant) |
| Pod Failure | Minimal | Kubernetes restarts pod (30 sec) |
| Control Plane Issue | None (AWS managed) | AWS handles recovery |

## Scaling Architecture

### Auto-Scaling Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Auto-Scaling Stack                         │
│                                                             │
│  Horizontal Pod Autoscaler (HPA)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Metrics Server → CPU/Memory → Scale Pods            │  │
│  │  Target: 70% CPU utilization                         │  │
│  │  Min Pods: 3 | Max Pods: 30                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  Cluster Autoscaler (CA)                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pod Scheduling → Node Capacity → Scale Nodes        │  │
│  │  Min Nodes: 3 | Max Nodes: 10                        │  │
│  │  Scale-up: When pods pending > 30 sec                │  │
│  │  Scale-down: When node utilization < 50% for 10 min  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  Vertical Pod Autoscaler (VPA) - Optional                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Resource Usage → Right-size Requests/Limits         │  │
│  │  Mode: Recommendation                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### Request Flow

```
1. User/RAN → Internet
2. Internet → Internet Gateway
3. IGW → Network Load Balancer (Public Subnet)
4. NLB → Kubernetes Service (Private Subnet)
5. Service → Pod (via kube-proxy)
6. Pod → Redis SDL (persistent storage)
7. Pod → External APIs (via NAT Gateway)
```

### Pod-to-Pod Communication

```
Pod A (10.0.16.10) → Service (ClusterIP) → Pod B (10.0.48.20)
                        │
                        └─── kube-proxy (iptables/IPVS)
                               │
                               └─── CNI (VPC-CNI)
                                      │
                                      └─── AWS ENI
```

## Disaster Recovery Architecture

### Backup Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                  Backup Architecture                        │
│                                                             │
│  Application Layer                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Velero → S3 Bucket (Application Backups)            │  │
│  │  Frequency: Daily at 2 AM UTC                        │  │
│  │  Retention: 30 days                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Infrastructure Layer                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Terraform State → S3 Bucket (with versioning)       │  │
│  │  Frequency: On every change                          │  │
│  │  Retention: Unlimited                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Data Layer                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  EBS Snapshots → S3 (Automated)                      │  │
│  │  Frequency: Daily                                    │  │
│  │  Retention: 30 days                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Recovery Time Objectives (RTO)

| Component | RTO | RPO |
|-----------|-----|-----|
| Cluster Recreation | 30 min | 24 hours |
| Application Restore | 15 min | 24 hours |
| Data Restore | 20 min | 24 hours |
| Full Recovery | 1 hour | 24 hours |

## Cost Optimization Architecture

### Resource Optimization

```
┌─────────────────────────────────────────────────────────────┐
│                Cost Optimization Layers                     │
│                                                             │
│  Compute Layer                                             │
│  • Reserved Instances (40-60% savings)                     │
│  • Spot Instances for non-critical (70-90% savings)        │
│  • Auto-scaling for off-hours                              │
│                                                             │
│  Storage Layer                                             │
│  • gp3 instead of gp2 (20% savings)                        │
│  • Lifecycle policies for old snapshots                    │
│  • Delete unused volumes                                   │
│                                                             │
│  Network Layer                                             │
│  • VPC endpoints for S3/ECR (data transfer savings)        │
│  • NAT Gateway optimization                                │
│  • CloudFront for static content                           │
│                                                             │
│  Monitoring Layer                                          │
│  • Log retention policies (cost vs. compliance)            │
│  • Metric aggregation                                      │
│  • Dashboard consolidation                                 │
└─────────────────────────────────────────────────────────────┘
```

## Performance Optimization

### Network Performance

- **Enhanced Networking**: SR-IOV for low latency
- **Placement Groups**: Cluster placement for inter-node traffic
- **MTU Size**: Jumbo frames (9001 bytes) for VPC
- **TCP Tuning**: Optimized kernel parameters

### Storage Performance

- **gp3 Volumes**: 16,000 IOPS for Redis SDL
- **EBS Optimization**: Enabled on all instances
- **Volume Throughput**: 1000 MB/s for critical workloads
- **Local NVMe**: Instance store for temporary data

### Compute Performance

- **CPU Pinning**: Isolate critical pods
- **Memory**: Huge pages for performance
- **CPU Governor**: Performance mode
- **NUMA**: Node awareness for memory access

## Compliance and Governance

### Compliance Framework

```
┌─────────────────────────────────────────────────────────────┐
│               Compliance Architecture                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Protection                                     │  │
│  │  • GDPR compliance                                   │  │
│  │  • HIPAA compliance                                  │  │
│  │  • SOC 2 Type II                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Security Standards                                  │  │
│  │  • CIS Kubernetes Benchmark                          │  │
│  │  • PCI-DSS                                           │  │
│  │  • ISO 27001                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Audit & Logging                                     │  │
│  │  • CloudTrail for API calls                          │  │
│  │  • CloudWatch for application logs                   │  │
│  │  • EKS audit logs                                    │  │
│  │  • 90-day retention minimum                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Status**: Production Ready
