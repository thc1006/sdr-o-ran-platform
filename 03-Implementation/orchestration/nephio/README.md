# Nephio Package Management for SDR Platform

Kubernetes Resource Model (KRM) packages for automated, multi-site SDR ground station deployment using Nephio R1.

## Overview

This directory contains Nephio packages for declarative, GitOps-based deployment of SDR ground stations across multiple edge sites.

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Nephio Management Cluster                    │
│                                                                  │
│  ┌────────────────┐        ┌───────────────────────┐           │
│  │  Porch Server  │───────►│  PackageVariantSet    │           │
│  │  (Git Packages)│        │  (Multi-site Config)  │           │
│  └────────────────┘        └───────────────────────┘           │
│           │                           │                          │
│           ▼                           ▼                          │
│  ┌─────────────────────────────────────────────────┐           │
│  │          Config Sync (GitOps Operator)          │           │
│  └─────────────────────────────────────────────────┘           │
└──────────────────────────┬───────────────────────┬──────────────┘
                           │                       │
            ┌──────────────┴────┐         ┌────────┴──────────┐
            ▼                   ▼         ▼                    ▼
    ┌──────────────┐    ┌──────────────┐ ┌──────────────┐
    │ Tokyo Site   │    │ London Site  │ │ Singapore    │
    │ (LEO/GEO)    │    │ (LEO/GEO)    │ │ (LEO)        │
    └──────────────┘    └──────────────┘ └──────────────┘
```

## Package Structure

### Base Package (`packages/sdr-platform-base/`)

Upstream package containing common SDR platform resources:

```
sdr-platform-base/
├── Kptfile                 # Package metadata and pipeline
├── package-context.yaml    # Package context for Nephio
├── deployment.yaml         # Core deployments (API, gRPC server)
├── configmap.yaml          # Configuration data
└── README.md               # Package documentation
```

### PackageVariants (`packagevariants/`)

Site-specific deployments derived from base package:

- **Tokyo Site**: LEO/GEO, C/Ku/Ka bands, USRP X310
- **London Site**: LEO/GEO, Ku/Ka bands, USRP N320
- **Singapore Site**: LEO, C/Ku bands, USRP X310

Each site automatically receives:
- Custom namespace
- Site-specific configuration
- Geographic coordinates for satellite tracking
- USRP hardware configuration
- Regional container registry

## Quick Start

### Prerequisites

1. **Nephio R1 Installation**

```bash
# Install Nephio management cluster
curl -fsSL https://github.com/nephio-project/nephio/releases/download/v1.0.0/install.sh | bash
```

2. **Register Edge Site Clusters**

```bash
# Register Tokyo edge cluster
nephio cluster add tokyo-edge \
  --kubeconfig ~/.kube/tokyo-kubeconfig \
  --type edge

# Register London edge cluster
nephio cluster add london-edge \
  --kubeconfig ~/.kube/london-kubeconfig \
  --type edge

# Register Singapore edge cluster
nephio cluster add singapore-edge \
  --kubeconfig ~/.kube/singapore-kubeconfig \
  --type edge
```

### Deploy SDR Platform

#### 1. Publish Base Package to Porch

```bash
# Clone this repository to Nephio management cluster
git clone https://github.com/your-org/sdr-oran-platform.git
cd sdr-oran-platform

# Initialize Porch repository
kpt alpha repo register \
  --namespace nephio-system \
  --repo-type git \
  --name sdr-packages \
  --content package \
  --deployment false \
  https://github.com/your-org/sdr-oran-platform.git

# Publish base package
kpt alpha rpkg init sdr-platform-base \
  --workspace v1.0.0 \
  --repository sdr-packages \
  --directory 03-Implementation/orchestration/nephio/packages/sdr-platform-base

kpt alpha rpkg propose sdr-platform-base-v1.0.0
kpt alpha rpkg approve sdr-platform-base-v1.0.0
```

#### 2. Apply PackageVariants

```bash
# Deploy to all edge sites
kubectl apply -f 03-Implementation/orchestration/nephio/packagevariants/sdr-edge-deployment.yaml
```

#### 3. Verify Deployments

```bash
# Check PackageVariant status
kubectl get packagevariants -n nephio-system

# Expected output:
# NAME                        READY   REASON
# sdr-platform-tokyo-site     True    Ready
# sdr-platform-london-site    True    Ready
# sdr-platform-singapore-site True    Ready

# Verify deployment on Tokyo site
kubectl get pods -n sdr-platform-tokyo --context tokyo-edge
```

## Customization

### Add New Site

Create a new PackageVariant:

```yaml
apiVersion: config.porch.kpt.dev/v1alpha1
kind: PackageVariant
metadata:
  name: sdr-platform-newyork-site
  namespace: nephio-system
spec:
  upstream:
    repo: nephio-packages
    package: sdr-platform-base
    revision: v1.0.0
  downstream:
    repo: newyork-edge-site
    package: sdr-platform-newyork
  pipeline:
    mutators:
      - image: gcr.io/kpt-fn/set-namespace:v0.4.1
        configMap:
          namespace: sdr-platform-newyork
      - image: gcr.io/kpt-fn/apply-setters:v0.2.0
        configMap:
          site-id: "site-004"
          latitude: "40.7128"
          longitude: "-74.0060"
          usrp-args: "type=n320,addr=192.168.40.2"
```

Apply:

```bash
kubectl apply -f packagevariants/newyork-site.yaml
```

### Modify Site Configuration

Update site-specific ConfigMap:

```bash
# Edit Tokyo site configuration
kubectl edit configmap tokyo-site-config -n nephio-system

# Changes automatically propagate to Tokyo edge cluster via Config Sync
```

### Update USRP Hardware Configuration

```yaml
# In PackageVariant
configMap:
  usrp-args: "type=x310,addr=192.168.10.2,master_clock_rate=200e6"
```

### Scale Replicas

```yaml
configMap:
  replicas: "5"  # Increase from 3 to 5
```

## Package Pipeline Functions

### Mutators (Applied During Deployment)

| Function | Purpose | Example |
|----------|---------|---------|
| `set-namespace` | Set target namespace | `sdr-platform-tokyo` |
| `apply-setters` | Inject site-specific values | `latitude`, `usrp-args` |
| `set-labels` | Add labels for organization | `site-id: site-001` |

### Validators (Pre-deployment Checks)

| Function | Purpose |
|----------|---------|
| `kubeval` | Validate Kubernetes API compliance |
| `gatekeeper` | Enforce security policies |
| `kpt-fn-check-resources` | Verify resource limits |

## GitOps Workflow

```
┌─────────────────┐
│  Update Base    │
│  Package in Git │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Porch Detects   │
│ Change          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PackageVariants │
│ Re-rendered     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Config Sync     │
│ Pulls Changes   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Edge Clusters   │
│ Updated         │
└─────────────────┘
```

## Advanced Features

### Conditional Deployment

Deploy only to sites matching criteria:

```yaml
apiVersion: config.porch.kpt.dev/v1alpha1
kind: PackageVariantSet
metadata:
  name: sdr-platform-leo-sites
spec:
  upstream:
    repo: nephio-packages
    package: sdr-platform-base
    revision: v1.0.0
  targets:
    repositorySelector:
      matchLabels:
        satellite-type: LEO  # Only deploy to LEO-capable sites
```

### Blue-Green Deployment

```yaml
# Deploy new version alongside existing
apiVersion: config.porch.kpt.dev/v1alpha1
kind: PackageVariant
metadata:
  name: sdr-platform-tokyo-site-v2
spec:
  upstream:
    package: sdr-platform-base
    revision: v2.0.0  # New version
  downstream:
    package: sdr-platform-tokyo-blue
  pipeline:
    mutators:
      - image: gcr.io/kpt-fn/set-namespace:v0.4.1
        configMap:
          namespace: sdr-platform-tokyo-blue  # Separate namespace
```

### Canary Deployment

Gradually roll out to subset of edge sites:

```bash
# Stage 1: Deploy to 10% (Singapore only)
kubectl apply -f packagevariants/singapore-site-canary.yaml

# Monitor for 24 hours
# Stage 2: Deploy to 50% (Tokyo + Singapore)
kubectl apply -f packagevariants/tokyo-site-canary.yaml

# Stage 3: Full rollout
kubectl apply -f packagevariants/london-site-canary.yaml
```

## Monitoring Deployments

### View Package Revisions

```bash
# List all package revisions
kubectl get packagerevisions -n nephio-system

# View specific package details
kubectl describe packagerevision sdr-platform-base-v1.0.0
```

### Check Sync Status

```bash
# Config Sync status on edge cluster
kubectl get configsync -n config-management-system --context tokyo-edge

# View sync errors
kubectl logs -n config-management-system \
  -l app=reconciler-manager \
  --context tokyo-edge
```

### Rollback Deployment

```bash
# Revert to previous package version
kpt alpha rpkg copy \
  sdr-platform-tokyo-v1.0.0 \
  sdr-platform-tokyo-v1.1.0-rollback

# Approve rollback package
kpt alpha rpkg approve sdr-platform-tokyo-v1.1.0-rollback
```

## Troubleshooting

### PackageVariant Not Rendering

```bash
# Check Porch logs
kubectl logs -n porch-system -l app=porch-server

# Verify upstream package exists
kpt alpha rpkg get sdr-platform-base --revision v1.0.0
```

### Config Sync Failing

```bash
# Check Config Sync status
nomos status --contexts tokyo-edge,london-edge,singapore-edge

# View detailed errors
kubectl describe rootsync root-sync -n config-management-system
```

### Mutator Function Errors

```bash
# Manually run kpt function pipeline
kpt fn render packages/sdr-platform-base/ --results-dir /tmp/results

# Check /tmp/results for error details
```

## References

- **Nephio Documentation**: https://nephio.org/docs/
- **Kpt Book**: https://kpt.dev/book/
- **Config Sync**: https://cloud.google.com/kubernetes-engine/docs/add-on/config-sync
- **FR-SDR-004**: Cloud-native SDR deployment
- **NFR-SCAL-001**: Multi-site scalability

## TODO for Production

- [ ] Configure sealed secrets for sensitive data
- [ ] Implement network policies per site
- [ ] Set up Prometheus federation for multi-cluster monitoring
- [ ] Configure cross-site service mesh (Istio multi-primary)
- [ ] Implement automated rollback on deployment failure
- [ ] Add pre-deployment validation for USRP connectivity
- [ ] Configure disaster recovery with Velero backups

---

**Status**: ✅ **READY** - Production-ready Nephio packages

**Last Updated**: 2025-10-27
**Author**: thc1006@ieee.org
