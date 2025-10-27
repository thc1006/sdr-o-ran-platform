# CI/CD Pipeline Documentation

**Version:** 2.0.0
**Date:** 2025-10-27
**Author:** thc1006@ieee.org
**Status:** ✅ Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [CI/CD Platforms](#cicd-platforms)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Strategies](#deployment-strategies)
6. [Security & Compliance](#security--compliance)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring & Observability](#monitoring--observability)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

This document describes the CI/CD pipeline for the **SDR-O-RAN Platform**, implementing 2025 best practices for cloud-native deployments with:

- **GitOps**: ArgoCD/Flux for declarative deployments
- **Security-First**: Container scanning, SAST/DAST, secret management
- **Multi-Cloud**: Support for AWS EKS, Google GKE, Azure AKS
- **Zero-Downtime**: Blue-green and canary deployment strategies
- **PQC Integration**: Post-Quantum Cryptography validation in CI
- **AI/ML Testing**: Automated DRL model validation

### Key Features

- 🐳 **Multi-stage Docker builds** with BuildKit optimization
- 🔒 **Security scanning** at every stage (Trivy, Bandit, Gitleaks)
- 🧪 **Comprehensive testing** (unit, integration, E2E, performance)
- 📦 **Helm chart packaging** with OCI registry support
- 🚀 **Multiple deployment strategies** (rolling, blue-green, canary)
- 📊 **Observability** with OpenTelemetry and Prometheus
- 🔄 **Automated rollbacks** with health checks
- 🛡️ **Image signing** with Cosign and SBOM generation

---

## Pipeline Architecture

### GitLab CI/CD Pipeline

```
┌─────────────┐
│  Validate   │  Lint Python, Docker, YAML
└──────┬──────┘
       │
┌──────▼──────┐
│    Build    │  Multi-stage Docker builds
└──────┬──────┘
       │
┌──────▼──────┐
│    Test     │  Pytest, gRPC, DRL models
└──────┬──────┘
       │
┌──────▼──────────┐
│ Security Scan   │  Trivy, Bandit, Gitleaks
└──────┬──────────┘
       │
┌──────▼──────┐
│   Package   │  Helm charts to OCI registry
└──────┬──────┘
       │
┌──────▼────────────┐
│ Deploy Staging    │  Kubernetes staging namespace
└──────┬────────────┘
       │
┌──────▼──────────────┐
│ Integration Tests   │  E2E, performance (K6)
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│ Deploy Production   │  Blue-Green strategy
└──────┬──────────────┘
       │
┌──────▼────────┐
│    Verify     │  Health checks, monitoring
└───────────────┘
```

### GitHub Actions Workflow

```
┌────────────────┐
│ Lint & Validate│  Code quality checks
└────────┬───────┘
         │
    ┌────▼────┐
    │  Build  │  Docker images (multi-arch)
    └────┬────┘
         │
    ┌────▼────────┐
    │   Security  │  Trivy, Grype, SBOM
    └────┬────────┘
         │
    ┌────▼─────┐
    │   Test   │  Pytest, PQC, DRL, gRPC
    └────┬─────┘
         │
    ┌────▼──────┐
    │  Package  │  Helm charts
    └────┬──────┘
         │
    ┌────▼────────┐
    │   Staging   │  EKS/GKE/AKS
    └────┬────────┘
         │
    ┌────▼──────────┐
    │  Production   │  Blue-Green
    └────┬──────────┘
         │
    ┌────▼────────┐
    │   Verify    │  Health checks
    └─────────────┘
```

---

## CI/CD Platforms

### GitLab CI/CD

**Location:** `.gitlab-ci.yml`

#### Features
- Native Docker registry integration
- Kubernetes executor support
- Built-in secret management
- Merge request pipelines
- Manual approval gates

#### Usage

```bash
# Trigger pipeline manually
git push origin main

# Trigger specific stage
curl -X POST \
  -F token=<TOKEN> \
  -F ref=main \
  https://gitlab.com/api/v4/projects/<PROJECT_ID>/trigger/pipeline
```

#### Environment Variables (GitLab Settings → CI/CD → Variables)

| Variable | Description | Example |
|----------|-------------|---------|
| `CI_REGISTRY` | Container registry | `registry.gitlab.com` |
| `KUBE_URL` | Kubernetes API server | `https://k8s.example.com:6443` |
| `KUBE_TOKEN` | K8s service account token | `eyJhbGciOi...` |
| `AWS_ACCESS_KEY_ID` | AWS credentials | `AKIAIOSFODNN7EXAMPLE` |
| `DOCKER_AUTH_CONFIG` | Docker registry credentials | `{"auths":...}` |

### GitHub Actions

**Location:** `.github/workflows/ci.yml`

#### Features
- Matrix builds for multi-service projects
- OIDC authentication (no long-lived secrets)
- GitHub Container Registry (GHCR)
- Reusable workflows
- Dependabot integration

#### Usage

```bash
# Trigger workflow
git push origin main

# Manual workflow dispatch
gh workflow run ci.yml \
  -f environment=staging \
  -f deployment_strategy=blue-green
```

#### Secrets Configuration (GitHub Settings → Secrets)

| Secret | Description | Example |
|--------|-------------|---------|
| `GITHUB_TOKEN` | Auto-generated per workflow | N/A (automatic) |
| `AWS_ROLE_ARN` | AWS IAM role for OIDC | `arn:aws:iam::123456789012:role/GitHubActions` |
| `CODECOV_TOKEN` | Code coverage upload | `a1b2c3d4-...` |
| `SLACK_WEBHOOK` | Slack notifications | `https://hooks.slack.com/services/...` |

---

## Environment Configuration

### Staging Environment

**Namespace:** `sdr-staging`
**Cluster:** `sdr-staging-cluster` (EKS/GKE/AKS)
**URL:** `https://sdr-staging.example.com`

**Characteristics:**
- Automatic deployment on `main` branch push
- Ephemeral environment (can be destroyed)
- Lower resource allocation (2 CPU, 4GB RAM per service)
- Integration tests enabled
- Non-production PQC keys

**Helm Values:** `values-staging.yaml`

```yaml
global:
  environment: staging
  imageTag: latest
  replicas: 2

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 4Gi

ingress:
  enabled: true
  host: sdr-staging.example.com
  tls:
    enabled: true
    secretName: sdr-staging-tls
```

### Production Environment

**Namespace:** `sdr-production`
**Cluster:** `sdr-production-cluster` (EKS/GKE/AKS)
**URL:** `https://sdr.example.com`

**Characteristics:**
- Manual approval required for deployment
- High availability (HA) configuration
- Blue-green deployment strategy
- Auto-scaling enabled (HPA)
- Production PQC certificates
- Multi-region failover

**Helm Values:** `values-production.yaml`

```yaml
global:
  environment: production
  imageTag: v1.2.3
  replicas: 5

resources:
  requests:
    cpu: 2000m
    memory: 4Gi
  limits:
    cpu: 8000m
    memory: 16Gi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
  targetCPU: 70
  targetMemory: 80

ingress:
  enabled: true
  host: sdr.example.com
  tls:
    enabled: true
    secretName: sdr-production-tls

pqc:
  enabled: true
  kyberKeyPath: /etc/pqc/kyber.pem
  dilithiumKeyPath: /etc/pqc/dilithium.pem
```

---

## Deployment Strategies

### 1. Rolling Deployment (Default)

**Use Case:** Standard updates with minimal risk

**Characteristics:**
- Gradual pod replacement (25% at a time)
- Zero downtime
- Automatic rollback on health check failure
- Fast deployment time

**Configuration:**

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```

**GitLab CI:**

```bash
helm upgrade --install sdr-platform \
  ./helm/sdr-platform \
  --namespace sdr-production \
  --wait \
  --timeout 10m
```

### 2. Blue-Green Deployment

**Use Case:** Critical updates requiring instant rollback capability

**Characteristics:**
- Two identical environments (blue = current, green = new)
- Instant traffic switching
- Easy rollback (switch back to blue)
- Higher resource usage (2x pods temporarily)

**Process:**

```bash
# Step 1: Deploy green environment
helm upgrade --install sdr-platform-green \
  ./helm/sdr-platform \
  --namespace sdr-production \
  --set global.deploymentColor=green \
  --wait

# Step 2: Verify green deployment
kubectl get pods -n sdr-production -l version=green
curl https://sdr-green.example.com/healthz

# Step 3: Switch traffic to green
kubectl patch service sdr-api-gateway \
  -n sdr-production \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Step 4: Monitor for 15 minutes

# Step 5: Delete blue environment (optional)
helm uninstall sdr-platform-blue -n sdr-production
```

**Rollback:**

```bash
# Instant rollback - switch traffic back to blue
kubectl patch service sdr-api-gateway \
  -n sdr-production \
  -p '{"spec":{"selector":{"version":"blue"}}}'
```

### 3. Canary Deployment

**Use Case:** Gradual rollout with risk mitigation

**Characteristics:**
- Progressive traffic shifting (5% → 25% → 50% → 100%)
- A/B testing capability
- Metrics-based promotion
- Longest deployment time

**Process:**

```bash
# Step 1: Deploy canary with 5% traffic
helm upgrade --install sdr-platform-canary \
  ./helm/sdr-platform \
  --namespace sdr-production \
  --set canary.enabled=true \
  --set canary.weight=5 \
  --wait

# Step 2: Monitor metrics for 30 minutes
kubectl top pods -n sdr-production -l version=canary

# Step 3: Increase to 25% traffic
helm upgrade sdr-platform-canary \
  ./helm/sdr-platform \
  --namespace sdr-production \
  --set canary.weight=25 \
  --reuse-values

# Repeat until 100%
```

**Automated Canary with Flagger:**

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: sdr-api-gateway
  namespace: sdr-production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sdr-api-gateway
  progressDeadlineSeconds: 600
  service:
    port: 8080
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
      - name: request-duration
        thresholdRange:
          max: 500
  webhooks:
    - name: load-test
      url: http://flagger-loadtester/
      timeout: 5s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://sdr-api-gateway-canary:8080/"
```

---

## Security & Compliance

### Container Security Scanning

#### Trivy

**Scans:** OS vulnerabilities, library vulnerabilities, IaC misconfigurations

```bash
# Scan Docker image
trivy image --severity HIGH,CRITICAL \
  ghcr.io/sdr-oran/api-gateway:latest

# Scan with SARIF output for GitHub
trivy image --format sarif \
  --output trivy-results.sarif \
  ghcr.io/sdr-oran/api-gateway:latest
```

**CI Integration (GitHub Actions):**

```yaml
- name: Run Trivy scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ghcr.io/sdr-oran/api-gateway:${{ github.sha }}'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

#### Grype (Anchore)

**Alternative scanner with OCI image support**

```bash
grype ghcr.io/sdr-oran/api-gateway:latest --fail-on high
```

### Python Security Scanning

#### Bandit

**SAST tool for Python code**

```bash
# Scan Python code for security issues
bandit -r 03-Implementation/ \
  -f json \
  -o bandit-report.json \
  -ll
```

**Common findings:**
- Hardcoded passwords
- SQL injection vulnerabilities
- Use of `eval()` or `exec()`
- Insecure random number generation

### Secret Scanning

#### Gitleaks

**Detect secrets in git history**

```bash
# Scan entire repository
gitleaks detect --source . --verbose

# Scan specific commit
gitleaks detect --source . --log-opts="--since=2025-01-01"
```

**CI Integration:**

```yaml
- name: Gitleaks scan
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Image Signing with Cosign

**Keyless signing using OIDC (Sigstore)**

```bash
# Sign container image
export COSIGN_EXPERIMENTAL=1
cosign sign ghcr.io/sdr-oran/api-gateway@sha256:abc123...

# Verify signature
cosign verify ghcr.io/sdr-oran/api-gateway:latest
```

**CI Integration:**

```yaml
- name: Sign container image
  env:
    COSIGN_EXPERIMENTAL: "true"
  run: |
    cosign sign --yes "${REGISTRY}/${IMAGE}@${DIGEST}"
```

### SBOM Generation

**Software Bill of Materials for supply chain security**

```bash
# Generate SBOM with Syft
syft ghcr.io/sdr-oran/api-gateway:latest -o spdx-json > sbom.spdx.json

# Attest SBOM with Cosign
cosign attest --predicate sbom.spdx.json \
  --type spdx \
  ghcr.io/sdr-oran/api-gateway:latest
```

### Post-Quantum Cryptography Validation

**Automated PQC testing in CI**

```bash
# Test Kyber KEM (Key Encapsulation Mechanism)
python -c "
from pqcrypto.kem.kyber1024 import generate_keypair, encrypt, decrypt
pk, sk = generate_keypair()
ct, ss = encrypt(pk)
ss_decap = decrypt(sk, ct)
assert ss == ss_decap, 'KEM verification failed'
print('✅ Kyber1024 NIST Level 3 validated')
"

# Test Dilithium signatures
python 03-Implementation/security/pqc/quantum_safe_crypto.py
```

---

## Rollback Procedures

### Automatic Rollback

**Helm automatically rolls back on failure**

```yaml
# In Helm chart, configure readiness probes
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
```

If readiness probes fail, Helm rollback is triggered automatically.

### Manual Rollback

#### Helm Rollback

```bash
# List release history
helm history sdr-platform -n sdr-production

# Rollback to previous release
helm rollback sdr-platform -n sdr-production

# Rollback to specific revision
helm rollback sdr-platform 5 -n sdr-production
```

#### Kubernetes Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/sdr-api-gateway -n sdr-production

# Rollback to specific revision
kubectl rollout undo deployment/sdr-api-gateway \
  --to-revision=3 \
  -n sdr-production

# Check rollout status
kubectl rollout status deployment/sdr-api-gateway -n sdr-production
```

#### Blue-Green Rollback

```bash
# Switch traffic back to blue environment
kubectl patch service sdr-api-gateway \
  -n sdr-production \
  -p '{"spec":{"selector":{"version":"blue"}}}'

echo "✅ Rolled back to blue environment"
```

#### ArgoCD Rollback

```bash
# Rollback via ArgoCD CLI
argocd app rollback sdr-platform --prune

# Rollback via ArgoCD UI
# Navigate to application → History → Select revision → Rollback
```

### Rollback Checklist

- [ ] Identify failing service(s)
- [ ] Check logs: `kubectl logs -n sdr-production -l app=sdr-api-gateway`
- [ ] Check events: `kubectl get events -n sdr-production`
- [ ] Trigger rollback (Helm, kubectl, or ArgoCD)
- [ ] Verify health: `curl https://sdr.example.com/healthz`
- [ ] Notify team via Slack/PagerDuty
- [ ] Create incident report
- [ ] Schedule post-mortem meeting

---

## Monitoring & Observability

### Prometheus Metrics

**Endpoint:** `https://sdr.example.com/metrics`

**Key Metrics:**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `http_requests_total` | Total HTTP requests | N/A |
| `http_request_duration_seconds` | Request latency | P95 > 500ms |
| `grpc_server_handled_total` | gRPC requests | N/A |
| `pqc_kyber_operations_total` | PQC operations | N/A |
| `drl_model_inference_duration` | DRL inference time | P99 > 100ms |

**Prometheus Alerts:**

```yaml
groups:
  - name: sdr-platform
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pod {{ $labels.pod }} is crash looping"
```

### OpenTelemetry Tracing

**Jaeger UI:** `https://jaeger.sdr.example.com`

**Instrumentation:**

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Initialize tracer
tracer = trace.get_tracer(__name__)

# Instrument FastAPI app
FastAPIInstrumentor.instrument_app(app)

# Custom span
with tracer.start_as_current_span("kyber_encapsulation"):
    ciphertext, shared_secret = kyber_encrypt(public_key)
```

### Logging (ELK Stack)

**Kibana UI:** `https://kibana.sdr.example.com`

**Log Format (JSON):**

```json
{
  "timestamp": "2025-10-27T10:30:00.123Z",
  "level": "INFO",
  "service": "api-gateway",
  "trace_id": "abc123...",
  "message": "PQC key exchange successful",
  "metadata": {
    "algorithm": "kyber1024",
    "client_ip": "192.168.1.100"
  }
}
```

### Grafana Dashboards

**URL:** `https://grafana.sdr.example.com`

**Dashboards:**
1. **SDR Platform Overview** - System health, request rates, latencies
2. **Kubernetes Cluster** - Node metrics, pod status, resource usage
3. **PQC Operations** - Kyber/Dilithium operation counts, latencies
4. **DRL Model Performance** - Inference times, model accuracy
5. **O-RAN Integration** - E2AP message rates, gRPC latencies

---

## Troubleshooting

### Common Issues

#### 1. Pipeline Fails at Build Stage

**Error:** `Docker build failed: error building image`

**Solution:**

```bash
# Check Dockerfile syntax
docker build -t test:latest -f Dockerfile .

# Check BuildKit logs
export DOCKER_BUILDKIT=1
docker build --progress=plain -t test:latest .

# Verify base image exists
docker pull python:3.11-slim
```

#### 2. Trivy Scan Fails with High Vulnerabilities

**Error:** `Trivy scan failed: 15 HIGH, 3 CRITICAL vulnerabilities found`

**Solution:**

```bash
# Update base image to latest patch version
sed -i 's/python:3.11-slim/python:3.11.8-slim/' Dockerfile

# Rebuild image
docker build -t ghcr.io/sdr-oran/api-gateway:latest .

# Re-scan
trivy image --severity HIGH,CRITICAL ghcr.io/sdr-oran/api-gateway:latest
```

#### 3. Helm Deployment Timeout

**Error:** `Error: timed out waiting for the condition`

**Solution:**

```bash
# Check pod status
kubectl get pods -n sdr-production

# Check pod logs
kubectl logs -n sdr-production -l app=sdr-api-gateway

# Describe pod for events
kubectl describe pod -n sdr-production <POD_NAME>

# Check image pull issues
kubectl get events -n sdr-production --sort-by='.lastTimestamp'

# Increase timeout
helm upgrade --install sdr-platform ./helm/sdr-platform \
  --timeout 20m
```

#### 4. PQC Library Import Fails

**Error:** `ImportError: No module named 'pqcrypto'`

**Solution:**

```bash
# Install PQC libraries
pip install pqcrypto cryptography

# Verify installation
python -c "from pqcrypto.kem.kyber1024 import generate_keypair; print('OK')"

# Update requirements.txt
echo "pqcrypto==0.1.9" >> requirements.txt
```

#### 5. gRPC Connection Refused

**Error:** `grpc._channel._InactiveRpcError: Connection refused`

**Solution:**

```bash
# Check service is running
kubectl get svc -n sdr-production sdr-grpc-server

# Check pod logs
kubectl logs -n sdr-production -l app=sdr-grpc-server

# Test connectivity from another pod
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- bash
grpcurl -plaintext sdr-grpc-server:50051 list
```

#### 6. Rollback Doesn't Restore Service

**Error:** Service still unhealthy after rollback

**Solution:**

```bash
# Check all resources
kubectl get all -n sdr-production

# Check ConfigMaps and Secrets
kubectl get configmap,secret -n sdr-production

# Force delete pods to recreate
kubectl delete pod -n sdr-production -l app=sdr-api-gateway

# If persistent issues, redeploy from scratch
helm uninstall sdr-platform -n sdr-production
helm install sdr-platform ./helm/sdr-platform -n sdr-production
```

---

## Best Practices

### 1. GitOps Workflow

**Recommended:** Use ArgoCD or Flux for continuous deployment

```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sdr-platform
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/sdr-oran/sdr-platform
    targetRevision: HEAD
    path: 04-Deployment/kubernetes/helm/sdr-platform
    helm:
      valueFiles:
        - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: sdr-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### 2. Immutable Infrastructure

- Never modify running containers
- Always deploy new versions via CI/CD
- Use immutable image tags (SHA256 digests, not `latest`)

```yaml
# Good
image: ghcr.io/sdr-oran/api-gateway@sha256:abc123...

# Bad
image: ghcr.io/sdr-oran/api-gateway:latest
```

### 3. Progressive Delivery

- Start with staging deployment
- Run integration tests
- Deploy to production canary (5%)
- Monitor metrics for 30 minutes
- Gradually increase traffic

### 4. Observability-Driven Development

- Add OpenTelemetry spans to critical paths
- Emit Prometheus metrics for business logic
- Use structured logging (JSON)
- Create Grafana dashboards before production

### 5. Secret Management

**Never commit secrets to git!**

**Use:**
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- Kubernetes External Secrets Operator

```yaml
# ExternalSecret example
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: sdr-pqc-keys
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: sdr-pqc-keys
    creationPolicy: Owner
  data:
    - secretKey: kyber-private-key
      remoteRef:
        key: sdr-production/pqc/kyber
```

### 6. Multi-Environment Configuration

**Use Helm values files for each environment:**

```
helm/sdr-platform/
├── Chart.yaml
├── values.yaml              # Default values
├── values-staging.yaml      # Staging overrides
├── values-production.yaml   # Production overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml
```

### 7. Automated Testing

**Test Pyramid:**

```
        ┌─────────┐
        │   E2E   │  10% (slow, expensive)
        ├─────────┤
        │Integration│ 30% (moderate speed)
        ├─────────┤
        │  Unit   │  60% (fast, cheap)
        └─────────┘
```

### 8. Cost Optimization

- Use spot instances for staging
- Auto-scaling based on actual load
- Clean up unused resources
- Right-size container requests/limits

```bash
# Find over-provisioned pods
kubectl top pods -n sdr-production
kubectl describe pod <POD> -n sdr-production | grep -A 5 "Limits"
```

### 9. Disaster Recovery

- **Backup strategy:** Daily Velero backups of Kubernetes resources
- **RTO (Recovery Time Objective):** < 1 hour
- **RPO (Recovery Point Objective):** < 15 minutes
- **Multi-region:** Active-passive setup with Route53 health checks

### 10. Compliance & Auditing

- All changes tracked via git commits
- CI/CD pipeline logs retained for 90 days
- Container images scanned and signed
- Access control with RBAC
- Audit logs sent to SIEM (Splunk, ELK)

---

## Appendix

### A. CI/CD Pipeline Environment Variables

#### GitLab CI/CD

```bash
# Required variables (GitLab Settings → CI/CD → Variables)
CI_REGISTRY=registry.gitlab.com
CI_REGISTRY_USER=$CI_JOB_USER
CI_REGISTRY_PASSWORD=$CI_JOB_TOKEN

KUBE_URL=https://k8s-api.example.com:6443
KUBE_TOKEN=<service-account-token>
KUBE_NAMESPACE_STAGING=sdr-staging
KUBE_NAMESPACE_PRODUCTION=sdr-production

AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
```

#### GitHub Actions

```bash
# Required secrets (GitHub Settings → Secrets and variables → Actions)
GITHUB_TOKEN=<auto-generated>
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/GitHubActionsRole
CODECOV_TOKEN=a1b2c3d4-e5f6-7890-abcd-ef1234567890
SLACK_WEBHOOK=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

### B. Kubernetes Service Account Setup

```bash
# Create service account for CI/CD
kubectl create serviceaccount gitlab-ci -n sdr-production

# Create ClusterRoleBinding
kubectl create clusterrolebinding gitlab-ci-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=sdr-production:gitlab-ci

# Get token (Kubernetes 1.24+)
kubectl create token gitlab-ci -n sdr-production --duration=8760h

# Export KUBE_TOKEN for GitLab CI/CD
```

### C. Helm Chart Structure

```
helm/sdr-platform/
├── Chart.yaml                   # Chart metadata
├── values.yaml                  # Default configuration
├── values-staging.yaml          # Staging overrides
├── values-production.yaml       # Production overrides
├── templates/
│   ├── _helpers.tpl             # Template helpers
│   ├── deployment.yaml          # Deployment manifests
│   ├── service.yaml             # Service definitions
│   ├── ingress.yaml             # Ingress rules
│   ├── configmap.yaml           # ConfigMaps
│   ├── secret.yaml              # Secrets (sealed)
│   ├── hpa.yaml                 # HorizontalPodAutoscaler
│   ├── pdb.yaml                 # PodDisruptionBudget
│   ├── networkpolicy.yaml       # Network policies
│   └── servicemonitor.yaml      # Prometheus ServiceMonitor
└── charts/                      # Sub-charts (dependencies)
```

### D. Monitoring Queries

**Prometheus Queries:**

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Pod CPU usage
rate(container_cpu_usage_seconds_total{pod=~"sdr-.*"}[5m])

# Pod memory usage
container_memory_working_set_bytes{pod=~"sdr-.*"} / 1024 / 1024
```

### E. Useful Commands

```bash
# Check all CI/CD resources
kubectl get all -n sdr-production -l managed-by=Helm

# Get Helm release history
helm history sdr-platform -n sdr-production

# Tail logs from all pods
kubectl logs -n sdr-production -l app=sdr-api-gateway -f --tail=100

# Port-forward for debugging
kubectl port-forward -n sdr-production svc/sdr-api-gateway 8080:8080

# Check resource usage
kubectl top pods -n sdr-production
kubectl top nodes

# Debug pod issues
kubectl describe pod -n sdr-production <POD_NAME>
kubectl get events -n sdr-production --sort-by='.lastTimestamp'

# Test connectivity
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- bash
```

---

## Support & Contribution

### Contact

- **Email:** thc1006@ieee.org
- **GitHub Issues:** https://github.com/sdr-oran/sdr-platform/issues
- **Slack:** #sdr-platform-ci-cd

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/ci-cd-improvement`
3. Make changes and test locally
4. Run linters: `black . && pylint 03-Implementation/`
5. Commit with meaningful message: `git commit -m "feat(ci): add canary deployment"`
6. Push and create pull request

### Documentation Updates

- Keep this README in sync with `.gitlab-ci.yml` and `.github/workflows/ci.yml`
- Document any new environment variables or secrets
- Update troubleshooting section with new issues

---

## License

Copyright (c) 2025 SDR-O-RAN Platform Project
Licensed under Apache 2.0 - see LICENSE file for details

---

**Last Updated:** 2025-10-27
**Version:** 2.0.0
**Status:** ✅ Production-Ready
