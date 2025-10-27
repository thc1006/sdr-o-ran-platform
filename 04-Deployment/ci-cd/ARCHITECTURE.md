# CI/CD Pipeline Architecture

**Version:** 1.0.0
**Date:** 2025-10-27
**Author:** thc1006@ieee.org

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Developer Workflow                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ git push
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Source Code Repository                              │
│                      (GitHub / GitLab / Bitbucket)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│      GitLab CI/CD            │        │     GitHub Actions           │
│  (.gitlab-ci.yml)            │        │  (.github/workflows/ci.yml)  │
└──────────────────────────────┘        └──────────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│      Build Stage             │        │     Test Stage               │
│  - Docker Build (BuildKit)   │        │  - Pytest (Unit)             │
│  - Multi-arch (amd64/arm64)  │        │  - Integration Tests         │
│  - Image signing (Cosign)    │        │  - PQC Validation            │
│  - SBOM generation           │        │  - DRL Model Tests           │
└──────────────────────────────┘        └──────────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Security Scanning                                   │
│  - Trivy (Container Vulnerabilities)                                        │
│  - Bandit (Python SAST)                                                     │
│  - Gitleaks (Secret Detection)                                              │
│  - Grype (Additional Vulnerability Scanner)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Container Registry (OCI)                                │
│                  (GHCR / GitLab Registry / Harbor)                          │
│  - Signed images (Cosign)                                                   │
│  - SBOM attached                                                            │
│  - Multi-arch manifests                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│   Staging Environment        │        │   Production Environment      │
│   (sdr-staging namespace)    │        │   (sdr-production namespace) │
│                              │        │                              │
│  - Auto-deployment           │        │  - Manual approval           │
│  - Integration tests         │        │  - Blue-green deployment     │
│  - Performance tests (K6)    │        │  - Canary deployment         │
│  - Lower resources           │        │  - High availability         │
└──────────────────────────────┘        └──────────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ArgoCD (GitOps)                                     │
│  - Declarative deployment                                                   │
│  - Automated sync                                                           │
│  - Self-healing                                                             │
│  - Rollback capability                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Monitoring & Observability                              │
│  - Prometheus (Metrics)                                                     │
│  - Grafana (Dashboards)                                                     │
│  - OpenTelemetry (Tracing)                                                  │
│  - ELK Stack (Logging)                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Stages Detail

### Stage 1: Code Validation

```
Developer Push
     │
     ▼
┌─────────────────────┐
│   Lint & Format     │
│   - Black           │
│   - isort           │
│   - Pylint          │
│   - Hadolint        │
│   - YAML Lint       │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Secret Scanning   │
│   - Gitleaks        │
└─────────────────────┘
```

### Stage 2: Build

```
Source Code
     │
     ▼
┌─────────────────────────────────┐
│   Docker Build (BuildKit)       │
│   - Multi-stage build           │
│   - Cache optimization          │
│   - Build args                  │
│   - Platform: linux/amd64,arm64 │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│   Image Signing (Cosign)        │
│   - Keyless signing (OIDC)      │
│   - Signature attached          │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│   SBOM Generation               │
│   - Syft (Anchore)              │
│   - SPDX format                 │
│   - Attested to image           │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│   Push to Registry              │
│   - Tagged: SHA, branch, latest │
│   - Multi-arch manifest         │
└─────────────────────────────────┘
```

### Stage 3: Test

```
Built Images
     │
     ├─────────────────┬──────────────────┬─────────────────┐
     │                 │                  │                 │
     ▼                 ▼                  ▼                 ▼
┌──────────┐   ┌──────────┐      ┌──────────┐     ┌──────────┐
│  Unit    │   │  PQC     │      │   DRL    │     │  gRPC    │
│  Tests   │   │  Crypto  │      │  Models  │     │  Tests   │
│          │   │  Tests   │      │  Tests   │     │          │
│ - Pytest │   │ - Kyber  │      │- TF/PyTorch│   │- E2AP    │
│ - Coverage│  │- Dilithium│     │- Inference│    │- Health  │
└──────────┘   └──────────┘      └──────────┘     └──────────┘
```

### Stage 4: Security Scan

```
Container Images
     │
     ├─────────────────┬──────────────────┬─────────────────┐
     │                 │                  │                 │
     ▼                 ▼                  ▼                 ▼
┌──────────┐   ┌──────────┐      ┌──────────┐     ┌──────────┐
│  Trivy   │   │  Grype   │      │  Bandit  │     │  Safety  │
│          │   │          │      │          │     │          │
│ - OS CVEs│   │- Library │      │- Python  │     │- Deps    │
│ - Config │   │  CVEs    │      │  SAST    │     │  Vulns   │
└──────────┘   └──────────┘      └──────────┘     └──────────┘
     │                 │                  │                 │
     └─────────────────┴──────────────────┴─────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  SARIF Upload    │
                   │  (GitHub/GitLab) │
                   └──────────────────┘
```

### Stage 5: Deploy

```
                    Approved Images
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│    Staging       │          │   Production     │
│                  │          │                  │
│ ┌──────────────┐ │          │ ┌──────────────┐ │
│ │ Helm Install │ │          │ │ Blue-Green   │ │
│ └──────────────┘ │          │ │ Deployment   │ │
│         │        │          │ └──────────────┘ │
│         ▼        │          │         │        │
│ ┌──────────────┐ │          │         ▼        │
│ │ Integration  │ │          │ ┌──────────────┐ │
│ │ Tests        │ │          │ │ Green Deploy │ │
│ └──────────────┘ │          │ │ (New Version)│ │
│         │        │          │ └──────────────┘ │
│         ▼        │          │         │        │
│ ┌──────────────┐ │          │         ▼        │
│ │ Performance  │ │          │ ┌──────────────┐ │
│ │ Tests (K6)   │ │          │ │ Health Check │ │
│ └──────────────┘ │          │ └──────────────┘ │
└──────────────────┘          │         │        │
                              │         ▼        │
                              │ ┌──────────────┐ │
                              │ │ Switch       │ │
                              │ │ Traffic      │ │
                              │ └──────────────┘ │
                              └──────────────────┘
```

---

## Deployment Strategies

### Rolling Update

```
┌────────────────────────────────────────────────────┐
│              Initial State (v1.0)                  │
│  [Pod 1] [Pod 2] [Pod 3] [Pod 4] [Pod 5]         │
└────────────────────────────────────────────────────┘
                    │
                    ▼ Start rolling update
┌────────────────────────────────────────────────────┐
│              Step 1: Terminate Pod 1               │
│  [----] [Pod 2] [Pod 3] [Pod 4] [Pod 5]          │
└────────────────────────────────────────────────────┘
                    │
                    ▼ Wait for ready
┌────────────────────────────────────────────────────┐
│              Step 2: Create new Pod 1              │
│  [Pod 1 v1.1] [Pod 2] [Pod 3] [Pod 4] [Pod 5]    │
└────────────────────────────────────────────────────┘
                    │
                    ▼ Repeat
┌────────────────────────────────────────────────────┐
│              Final State (v1.1)                    │
│  [Pod 1] [Pod 2] [Pod 3] [Pod 4] [Pod 5]         │
│   v1.1    v1.1    v1.1    v1.1    v1.1           │
└────────────────────────────────────────────────────┘

maxSurge: 1        # Max pods above desired count
maxUnavailable: 1  # Max pods below desired count
```

### Blue-Green Deployment

```
┌────────────────────────────────────────────────────┐
│              Blue Environment (v1.0)               │
│        [Pod 1] [Pod 2] [Pod 3]                    │
│              ▲                                     │
│              │ 100% traffic                        │
│        [Load Balancer]                            │
└────────────────────────────────────────────────────┘
                    │
                    ▼ Deploy green
┌────────────────────────────────────────────────────┐
│         Blue (v1.0)    │    Green (v1.1)          │
│    [Pod 1] [Pod 2]    │    [Pod 4] [Pod 5]       │
│         ▲             │                            │
│         │ 100%        │    0% (testing)            │
│    [Load Balancer]    │                            │
└────────────────────────────────────────────────────┘
                    │
                    ▼ Switch traffic
┌────────────────────────────────────────────────────┐
│         Blue (v1.0)    │    Green (v1.1)          │
│    [Pod 1] [Pod 2]    │    [Pod 4] [Pod 5]       │
│                       │         ▲                  │
│         0%            │         │ 100%             │
│                       │    [Load Balancer]         │
└────────────────────────────────────────────────────┘
                    │
                    ▼ Delete blue (after verification)
┌────────────────────────────────────────────────────┐
│              Green Environment (v1.1)              │
│        [Pod 4] [Pod 5] [Pod 6]                    │
│              ▲                                     │
│              │ 100% traffic                        │
│        [Load Balancer]                            │
└────────────────────────────────────────────────────┘
```

### Canary Deployment

```
Phase 1: Initial (100% stable)
┌─────────────────────────────────────────┐
│     Stable (v1.0)     │   Canary (v1.1) │
│  [Pod1][Pod2][Pod3]  │                  │
│         100%          │        0%        │
└─────────────────────────────────────────┘

Phase 2: Canary introduction (95% / 5%)
┌─────────────────────────────────────────┐
│     Stable (v1.0)     │   Canary (v1.1) │
│  [Pod1][Pod2][Pod3]  │     [Pod4]       │
│         95%           │        5%        │
└─────────────────────────────────────────┘
         │
         ▼ Monitor metrics (15 min)

Phase 3: Increase canary (75% / 25%)
┌─────────────────────────────────────────┐
│     Stable (v1.0)     │   Canary (v1.1) │
│    [Pod1][Pod2]      │   [Pod3][Pod4]   │
│         75%           │       25%        │
└─────────────────────────────────────────┘
         │
         ▼ Monitor metrics (15 min)

Phase 4: Equal split (50% / 50%)
┌─────────────────────────────────────────┐
│     Stable (v1.0)     │   Canary (v1.1) │
│      [Pod1]          │   [Pod2][Pod3]   │
│         50%           │       50%        │
└─────────────────────────────────────────┘
         │
         ▼ Monitor metrics (30 min)

Phase 5: Full rollout (0% / 100%)
┌─────────────────────────────────────────┐
│     Stable (v1.0)     │   Canary (v1.1) │
│                       │ [Pod1][Pod2][Pod3]│
│          0%           │      100%        │
└─────────────────────────────────────────┘

Automated rollback if:
- Error rate > 1%
- Latency p95 > 500ms
- Failed health checks
```

---

## GitOps Flow with ArgoCD

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Repository                            │
│  - Helm charts                                              │
│  - Kubernetes manifests                                     │
│  - Application configuration                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ ArgoCD watches
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    ArgoCD Controller                         │
│  - Detects changes in git                                   │
│  - Compares desired state vs. actual state                  │
│  - Generates sync plan                                      │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼ Sync                              ▼ Out of sync
┌─────────────────────┐          ┌─────────────────────┐
│   Automated Sync    │          │   Manual Approval   │
│   (if enabled)      │          │   (production)      │
└─────────────────────┘          └─────────────────────┘
        │                                   │
        └─────────────────┬─────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Apply to Kubernetes                         │
│  - Create/update resources                                  │
│  - Health check                                             │
│  - Prune deleted resources                                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Self-Healing                               │
│  - Detect drift                                             │
│  - Auto-correct to desired state                            │
│  - Send notifications                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Scanning Flow

```
┌──────────────────┐
│  Source Code     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│              Static Analysis (SAST)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Bandit    │  │  Pylint    │  │  Gitleaks  │        │
│  │  (Python)  │  │  (Quality) │  │  (Secrets) │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Docker Build    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│         Container Vulnerability Scanning                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   Trivy    │  │   Grype    │  │  Syft      │        │
│  │   (CVEs)   │  │  (Anchore) │  │  (SBOM)    │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│              Signing & Attestation                        │
│  ┌────────────┐  ┌────────────┐                         │
│  │   Cosign   │  │  Notary    │                         │
│  │  (Sigstore)│  │  (CNCF)    │                         │
│  └────────────┘  └────────────┘                         │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Registry Push   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│         Runtime Security (Deployed)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   Falco    │  │  OPA/GK    │  │   KubeArmor│        │
│  │  (Runtime) │  │  (Policy)  │  │  (Behavior)│        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
```

---

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │API Gateway│  │gRPC Server│  │DRL Trainer│ │PQC Service│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Prometheus  │ │ OpenTelemetry│ │  FluentBit   │
│  (Metrics)   │ │  (Traces)    │ │  (Logs)      │
└──────────────┘ └──────────────┘ └──────────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Grafana    │ │    Jaeger    │ │     ELK      │
│  (Dashboards)│ │   (Tracing)  │ │  (Logging)   │
└──────────────┘ └──────────────┘ └──────────────┘
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 Alerting & Notifications                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │AlertManager│ │  Slack   │ │ PagerDuty│ │   Email  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Git → Production

```
1. Developer commits code
         │
         ▼
2. Git webhook triggers CI/CD
         │
         ▼
3. Pipeline runs
   ├── Lint & validate
   ├── Build Docker images
   ├── Run tests
   └── Security scanning
         │
         ▼
4. Push to container registry
         │
         ▼
5. Update Helm chart values
         │
         ▼
6. Commit updated manifests to git
         │
         ▼
7. ArgoCD detects change
         │
         ▼
8. ArgoCD syncs to Kubernetes
         │
         ▼
9. Health checks & monitoring
         │
         ▼
10. Notify team (Slack/Email)
```

---

## Disaster Recovery Flow

```
                    ┌─────────────────┐
                    │   Disaster!     │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  Automatic       │          │   Manual         │
    │  Rollback        │          │   Intervention   │
    └────────┬─────────┘          └────────┬─────────┘
             │                              │
             ▼                              ▼
    ┌──────────────────┐          ┌──────────────────┐
    │ Helm/ArgoCD      │          │ Restore from     │
    │ Rollback         │          │ Velero Backup    │
    └────────┬─────────┘          └────────┬─────────┘
             │                              │
             └──────────────┬───────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ Verify Health    │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ Notify Team      │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ Post-Mortem      │
                   └──────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Source Control** | Git (GitHub/GitLab) | Version control |
| **CI/CD** | GitLab CI, GitHub Actions | Automation |
| **Build** | Docker BuildKit | Container images |
| **Registry** | GHCR, GitLab Registry | Image storage |
| **Orchestration** | Kubernetes 1.29+ | Container orchestration |
| **GitOps** | ArgoCD | Declarative deployment |
| **Package Manager** | Helm 3.14+ | Kubernetes packages |
| **Security Scanning** | Trivy, Bandit, Gitleaks | Vulnerability detection |
| **Image Signing** | Cosign (Sigstore) | Supply chain security |
| **SBOM** | Syft (Anchore) | Software bill of materials |
| **Monitoring** | Prometheus, Grafana | Metrics & dashboards |
| **Tracing** | OpenTelemetry, Jaeger | Distributed tracing |
| **Logging** | FluentBit, ELK Stack | Log aggregation |
| **Alerting** | Alertmanager, Slack | Notifications |
| **Performance** | K6 | Load testing |
| **Backup** | Velero | Disaster recovery |

---

## Key Design Principles

1. **Immutable Infrastructure**: Never modify running containers
2. **GitOps**: Git as single source of truth
3. **Security First**: Scan everything, sign all images
4. **Progressive Delivery**: Gradual rollouts with automated rollback
5. **Observability**: Metrics, logs, and traces for all services
6. **Infrastructure as Code**: Everything defined in code
7. **Self-Healing**: Automatic recovery from failures
8. **Multi-Environment**: Staging mirrors production
9. **Compliance**: Audit trails for all changes
10. **Zero-Downtime**: Rolling updates and blue-green deployments

---

## SLOs (Service Level Objectives)

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| API Availability | 99.9% | < 99.5% |
| API Latency (p95) | < 500ms | > 1000ms |
| Deployment Success Rate | > 95% | < 90% |
| Deployment Time (Staging) | < 5 min | > 10 min |
| Deployment Time (Production) | < 15 min | > 30 min |
| Test Coverage | > 80% | < 70% |
| Security Scan Pass Rate | > 95% | < 90% |
| Container Vulnerability (Critical) | 0 | > 0 |
| Mean Time to Recovery (MTTR) | < 15 min | > 30 min |

---

**Last Updated:** 2025-10-27
**Status:** ✅ Production-Ready
