# CI/CD Pipeline Quick Start Guide

**Version:** 1.0.0
**Date:** 2025-10-27
**For:** SDR-O-RAN Platform

---

## 5-Minute Quick Setup

### Prerequisites Checklist

- [ ] Docker installed and running
- [ ] kubectl configured for your cluster
- [ ] Helm 3.14+ installed
- [ ] Git repository access
- [ ] Container registry credentials (GitHub, GitLab, or Docker Hub)

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/sdr-oran/sdr-platform.git
cd sdr-platform/04-Deployment/ci-cd

# Set environment variables
export DOCKER_USERNAME="your-username"
export DOCKER_PASSWORD="your-token"
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"  # For GitHub Actions
export GITLAB_REGISTRATION_TOKEN="xxxx"  # For GitLab CI

# Run automated setup
./setup-cicd.sh --all

# Expected time: 5-10 minutes
```

### Option 2: Manual Setup

#### Step 1: Create Kubernetes Namespaces

```bash
kubectl create namespace sdr-staging
kubectl create namespace sdr-production
kubectl create namespace argocd
```

#### Step 2: Configure Docker Registry

```bash
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_TOKEN \
  --namespace=sdr-staging

kubectl create secret docker-registry docker-registry-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_TOKEN \
  --namespace=sdr-production
```

#### Step 3: Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

#### Step 4: Configure CI/CD Platform

**For GitLab CI/CD:**

1. Go to your GitLab project → Settings → CI/CD → Variables
2. Add the following variables:
   - `KUBE_URL`: Your Kubernetes API server URL
   - `KUBE_TOKEN`: Service account token (see below)
   - `CI_REGISTRY_USER`: Your container registry username
   - `CI_REGISTRY_PASSWORD`: Your container registry token

**For GitHub Actions:**

1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `AWS_ROLE_ARN`: AWS IAM role for OIDC (if using EKS)
   - `DOCKER_USERNAME`: Container registry username
   - `DOCKER_PASSWORD`: Container registry token
   - `SLACK_WEBHOOK`: (Optional) Slack webhook URL

#### Step 5: Get Kubernetes Service Account Token

```bash
# Create service account
kubectl create serviceaccount gitlab-ci -n sdr-production

# Create cluster role binding
kubectl create clusterrolebinding gitlab-ci-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=sdr-production:gitlab-ci

# Get token (Kubernetes 1.24+)
kubectl create token gitlab-ci -n sdr-production --duration=8760h
```

---

## First Deployment

### GitLab CI/CD

```bash
# Push to trigger pipeline
git add .
git commit -m "feat: initial deployment"
git push origin main

# Monitor pipeline
# Go to: https://gitlab.com/your-org/sdr-platform/-/pipelines
```

### GitHub Actions

```bash
# Push to trigger workflow
git add .
git commit -m "feat: initial deployment"
git push origin main

# Monitor workflow
# Go to: https://github.com/your-org/sdr-platform/actions
```

### ArgoCD (GitOps)

```bash
# Apply ArgoCD application
kubectl apply -f 04-Deployment/ci-cd/argocd-application.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser: https://localhost:8080
# Username: admin
# Password: (from Step 3 above)

# Sync application
argocd app sync sdr-platform
```

---

## Verify Deployment

### Check Pipeline Status

```bash
# GitLab CI/CD
curl -H "PRIVATE-TOKEN: YOUR_TOKEN" \
  "https://gitlab.com/api/v4/projects/PROJECT_ID/pipelines"

# GitHub Actions
gh workflow view
gh run list
```

### Check Kubernetes Deployment

```bash
# Check all resources
kubectl get all -n sdr-staging
kubectl get all -n sdr-production

# Check pods
kubectl get pods -n sdr-staging -l app=sdr-api-gateway

# Check logs
kubectl logs -n sdr-staging -l app=sdr-api-gateway --tail=50

# Check service endpoints
kubectl get svc -n sdr-staging
```

### Test API Gateway

```bash
# Port-forward to test locally
kubectl port-forward -n sdr-staging svc/sdr-api-gateway 8080:8080

# Test health endpoint
curl http://localhost:8080/healthz

# Test metrics endpoint
curl http://localhost:8080/metrics
```

---

## Common Tasks

### Deploy to Staging

```bash
# GitLab: Push to main branch
git push origin main

# GitHub: Push to main branch
git push origin main

# ArgoCD: Manual sync
argocd app sync sdr-platform
```

### Deploy to Production

```bash
# GitLab: Create tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# GitHub: Create release
gh release create v1.0.0 --title "Release v1.0.0" --notes "Production release"

# ArgoCD: Update image tag in application
kubectl patch application sdr-platform -n argocd --type merge -p '{"spec":{"source":{"helm":{"parameters":[{"name":"global.imageTag","value":"v1.0.0"}]}}}}'
```

### Rollback Deployment

```bash
# Helm rollback
helm rollback sdr-platform -n sdr-production

# Kubernetes rollback
kubectl rollout undo deployment/sdr-api-gateway -n sdr-production

# ArgoCD rollback
argocd app rollback sdr-platform
```

### View Logs

```bash
# Real-time logs
kubectl logs -f -n sdr-staging -l app=sdr-api-gateway

# Previous pod logs
kubectl logs -n sdr-staging POD_NAME --previous

# All logs from last hour
kubectl logs -n sdr-staging -l app=sdr-api-gateway --since=1h
```

---

## Monitoring

### Access Grafana

```bash
# Port-forward
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Open: http://localhost:3000
# Username: admin
# Password: admin (change after first login)
```

### Access Prometheus

```bash
# Port-forward
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open: http://localhost:9090
```

### View Metrics

```bash
# API Gateway metrics
curl http://sdr-api-gateway.sdr-staging:8080/metrics

# gRPC server metrics
grpcurl -plaintext sdr-grpc-server.sdr-staging:50051 grpc.health.v1.Health/Check
```

---

## Troubleshooting

### Pipeline Fails

```bash
# GitLab: View pipeline logs
# https://gitlab.com/your-org/sdr-platform/-/pipelines/PIPELINE_ID

# GitHub: View workflow logs
gh run view RUN_ID --log

# Check CI/CD runner
kubectl get pods -n gitlab  # GitLab
kubectl get pods -n github-runner  # GitHub
```

### Deployment Fails

```bash
# Check pod status
kubectl get pods -n sdr-staging

# Describe pod for errors
kubectl describe pod POD_NAME -n sdr-staging

# Check events
kubectl get events -n sdr-staging --sort-by='.lastTimestamp'

# Check Helm release
helm list -n sdr-staging
helm status sdr-platform -n sdr-staging
```

### Image Pull Errors

```bash
# Check image pull secret
kubectl get secret docker-registry-secret -n sdr-staging

# Test image pull locally
docker pull ghcr.io/sdr-oran/api-gateway:latest

# Recreate secret
kubectl delete secret docker-registry-secret -n sdr-staging
kubectl create secret docker-registry docker-registry-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_TOKEN \
  --namespace=sdr-staging
```

---

## Security Checklist

- [ ] All secrets stored in Kubernetes secrets (not in git)
- [ ] Docker images scanned with Trivy (no HIGH/CRITICAL vulnerabilities)
- [ ] Python code scanned with Bandit
- [ ] No hardcoded passwords in code
- [ ] RBAC configured for service accounts
- [ ] Network policies configured
- [ ] TLS enabled for all external endpoints
- [ ] PQC certificates configured (for production)

---

## Performance Benchmarks

Run K6 performance tests:

```bash
# Install K6
# macOS: brew install k6
# Linux: sudo apt install k6
# Windows: choco install k6

# Run performance test
export SDR_API_URL="https://sdr-staging.example.com"
k6 run 04-Deployment/ci-cd/k6-performance-test.js

# Run with custom parameters
k6 run --vus 100 --duration 5m k6-performance-test.js
```

**Expected Results:**
- API latency (p95): < 500ms
- API latency (p99): < 1000ms
- Error rate: < 1%
- gRPC latency (p95): < 200ms

---

## Next Steps

1. **Configure Monitoring Alerts**
   - Set up Prometheus alerting rules
   - Configure Slack/PagerDuty notifications

2. **Enable HTTPS**
   - Install cert-manager
   - Configure Let's Encrypt

3. **Set Up Backups**
   - Install Velero
   - Schedule daily backups

4. **Performance Tuning**
   - Configure HPA (Horizontal Pod Autoscaler)
   - Optimize resource requests/limits

5. **Security Hardening**
   - Enable Pod Security Standards
   - Configure OPA/Gatekeeper policies

---

## Getting Help

- **Documentation:** [README.md](./README.md)
- **Issues:** https://github.com/sdr-oran/sdr-platform/issues
- **Email:** thc1006@ieee.org
- **Slack:** #sdr-platform-ci-cd

---

## Useful Commands Cheat Sheet

```bash
# CI/CD Setup
./setup-cicd.sh --all                    # Full setup
./setup-cicd.sh --validate               # Validate setup

# Kubernetes
kubectl get all -n sdr-staging           # View all resources
kubectl describe pod POD -n sdr-staging  # Pod details
kubectl logs -f -n sdr-staging POD       # Stream logs
kubectl exec -it POD -n sdr-staging -- bash  # Shell into pod

# Helm
helm list -n sdr-staging                 # List releases
helm status sdr-platform -n sdr-staging  # Release status
helm rollback sdr-platform -n sdr-staging  # Rollback

# ArgoCD
argocd app list                          # List applications
argocd app sync sdr-platform             # Sync application
argocd app get sdr-platform              # Get app details
argocd app rollback sdr-platform         # Rollback

# Docker
docker build -t sdr-api:latest .         # Build image
docker push ghcr.io/sdr-oran/api:latest  # Push image
docker scan sdr-api:latest               # Scan for vulnerabilities

# Git
git tag -a v1.0.0 -m "Release"           # Create tag
git push origin v1.0.0                   # Push tag
git push --force-with-lease              # Safe force push
```

---

**Last Updated:** 2025-10-27
**Status:** ✅ Production-Ready
