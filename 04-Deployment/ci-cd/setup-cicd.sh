#!/bin/bash
# ============================================================================
# CI/CD Pipeline Setup Script for SDR-O-RAN Platform
# ============================================================================
# Version: 1.0.0
# Date: 2025-10-27
# Author: thc1006@ieee.org
#
# This script sets up the complete CI/CD infrastructure including:
# - GitLab CI/CD runner
# - GitHub Actions self-hosted runner
# - ArgoCD installation
# - Kubernetes namespaces
# - Docker registry authentication
# - Monitoring tools (Prometheus, Grafana)
#
# Usage:
#   ./setup-cicd.sh [--gitlab|--github|--argocd|--all]
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Kubernetes configuration
KUBE_CONTEXT="${KUBE_CONTEXT:-default}"
STAGING_NAMESPACE="sdr-staging"
PRODUCTION_NAMESPACE="sdr-production"
ARGOCD_NAMESPACE="argocd"

# Docker registry
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"
DOCKER_USERNAME="${DOCKER_USERNAME:-}"
DOCKER_PASSWORD="${DOCKER_PASSWORD:-}"

# GitLab configuration
GITLAB_URL="${GITLAB_URL:-https://gitlab.com}"
GITLAB_REGISTRATION_TOKEN="${GITLAB_REGISTRATION_TOKEN:-}"

# GitHub configuration
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_REPO="${GITHUB_REPO:-sdr-oran/sdr-platform}"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    check_command kubectl
    check_command helm
    check_command docker
    check_command git

    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    fi

    log_success "All prerequisites met!"
}

# ============================================================================
# Kubernetes Setup
# ============================================================================

setup_kubernetes_namespaces() {
    log_info "Setting up Kubernetes namespaces..."

    # Create staging namespace
    kubectl create namespace "${STAGING_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace "${STAGING_NAMESPACE}" environment=staging --overwrite

    # Create production namespace
    kubectl create namespace "${PRODUCTION_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace "${PRODUCTION_NAMESPACE}" environment=production --overwrite

    log_success "Namespaces created: ${STAGING_NAMESPACE}, ${PRODUCTION_NAMESPACE}"
}

setup_docker_registry_secret() {
    log_info "Setting up Docker registry authentication..."

    if [[ -z "${DOCKER_USERNAME}" ]] || [[ -z "${DOCKER_PASSWORD}" ]]; then
        log_warning "Docker credentials not provided. Skipping registry secret creation."
        return
    fi

    for namespace in "${STAGING_NAMESPACE}" "${PRODUCTION_NAMESPACE}"; do
        kubectl create secret docker-registry docker-registry-secret \
            --docker-server="${DOCKER_REGISTRY}" \
            --docker-username="${DOCKER_USERNAME}" \
            --docker-password="${DOCKER_PASSWORD}" \
            --namespace="${namespace}" \
            --dry-run=client -o yaml | kubectl apply -f -

        log_success "Docker registry secret created in ${namespace}"
    done
}

# ============================================================================
# GitLab CI/CD Setup
# ============================================================================

setup_gitlab_runner() {
    log_info "Setting up GitLab CI/CD runner..."

    if [[ -z "${GITLAB_REGISTRATION_TOKEN}" ]]; then
        log_warning "GITLAB_REGISTRATION_TOKEN not set. Skipping GitLab runner setup."
        log_info "Get your registration token from: ${GITLAB_URL}/admin/runners"
        return
    fi

    # Add GitLab Helm repository
    helm repo add gitlab https://charts.gitlab.io
    helm repo update

    # Install GitLab Runner
    helm upgrade --install gitlab-runner gitlab/gitlab-runner \
        --namespace gitlab \
        --create-namespace \
        --set gitlabUrl="${GITLAB_URL}" \
        --set runnerRegistrationToken="${GITLAB_REGISTRATION_TOKEN}" \
        --set rbac.create=true \
        --set runners.privileged=true \
        --set runners.image="ubuntu:22.04" \
        --set runners.tags="kubernetes\,docker" \
        --set runners.cache.secretName="gitlab-runner-cache" \
        --wait

    log_success "GitLab Runner installed successfully!"
    log_info "View runner status: kubectl get pods -n gitlab"
}

# ============================================================================
# GitHub Actions Setup
# ============================================================================

setup_github_runner() {
    log_info "Setting up GitHub Actions runner..."

    if [[ -z "${GITHUB_TOKEN}" ]]; then
        log_warning "GITHUB_TOKEN not set. Skipping GitHub Actions runner setup."
        log_info "Create a personal access token with 'repo' and 'admin:org' scopes"
        return
    fi

    # Create namespace for GitHub runner
    kubectl create namespace github-runner --dry-run=client -o yaml | kubectl apply -f -

    # Install GitHub Actions Runner Controller
    helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
    helm repo update

    helm upgrade --install actions-runner-controller \
        actions-runner-controller/actions-runner-controller \
        --namespace github-runner \
        --set authSecret.github_token="${GITHUB_TOKEN}" \
        --wait

    # Create RunnerDeployment
    cat <<EOF | kubectl apply -f -
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: sdr-platform-runner
  namespace: github-runner
spec:
  replicas: 2
  template:
    spec:
      repository: ${GITHUB_REPO}
      labels:
        - self-hosted
        - linux
        - x64
        - kubernetes
      dockerdWithinRunnerContainer: true
EOF

    log_success "GitHub Actions runner deployed successfully!"
    log_info "View runner status: kubectl get runners -n github-runner"
}

# ============================================================================
# ArgoCD Setup
# ============================================================================

setup_argocd() {
    log_info "Setting up ArgoCD for GitOps..."

    # Create ArgoCD namespace
    kubectl create namespace "${ARGOCD_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

    # Install ArgoCD
    kubectl apply -n "${ARGOCD_NAMESPACE}" -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

    log_info "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n "${ARGOCD_NAMESPACE}"

    # Get ArgoCD admin password
    ARGOCD_PASSWORD=$(kubectl -n "${ARGOCD_NAMESPACE}" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

    log_success "ArgoCD installed successfully!"
    log_info "ArgoCD admin password: ${ARGOCD_PASSWORD}"
    log_info "Access ArgoCD UI via port-forward:"
    log_info "  kubectl port-forward svc/argocd-server -n ${ARGOCD_NAMESPACE} 8080:443"
    log_info "  Then open: https://localhost:8080"

    # Install ArgoCD CLI
    if command -v argocd &> /dev/null; then
        log_info "Logging in to ArgoCD..."
        kubectl port-forward svc/argocd-server -n "${ARGOCD_NAMESPACE}" 8080:443 &
        PORT_FORWARD_PID=$!
        sleep 5

        argocd login localhost:8080 \
            --username admin \
            --password "${ARGOCD_PASSWORD}" \
            --insecure

        # Apply ArgoCD application
        if [[ -f "${SCRIPT_DIR}/argocd-application.yaml" ]]; then
            kubectl apply -f "${SCRIPT_DIR}/argocd-application.yaml"
            log_success "ArgoCD application configured!"
        fi

        kill ${PORT_FORWARD_PID}
    else
        log_warning "ArgoCD CLI not installed. Install from: https://argo-cd.readthedocs.io/en/stable/cli_installation/"
    fi
}

# ============================================================================
# Monitoring Setup
# ============================================================================

setup_monitoring() {
    log_info "Setting up monitoring stack (Prometheus + Grafana)..."

    # Add Prometheus Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update

    # Install Prometheus Operator
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set grafana.adminPassword=admin \
        --wait

    log_success "Prometheus and Grafana installed!"
    log_info "Access Grafana:"
    log_info "  kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    log_info "  Username: admin, Password: admin"
}

# ============================================================================
# Security Scanning Tools
# ============================================================================

setup_security_tools() {
    log_info "Setting up security scanning tools..."

    # Install Trivy Operator
    helm repo add aqua https://aquasecurity.github.io/helm-charts/
    helm repo update

    helm upgrade --install trivy-operator aqua/trivy-operator \
        --namespace trivy-system \
        --create-namespace \
        --set="trivy.ignoreUnfixed=true" \
        --wait

    log_success "Trivy Operator installed for continuous vulnerability scanning!"
}

# ============================================================================
# Validation
# ============================================================================

validate_setup() {
    log_info "Validating CI/CD setup..."

    local errors=0

    # Check namespaces
    for ns in "${STAGING_NAMESPACE}" "${PRODUCTION_NAMESPACE}" "${ARGOCD_NAMESPACE}"; do
        if kubectl get namespace "${ns}" &> /dev/null; then
            log_success "Namespace ${ns} exists"
        else
            log_error "Namespace ${ns} not found"
            ((errors++))
        fi
    done

    # Check ArgoCD
    if kubectl get deployment argocd-server -n "${ARGOCD_NAMESPACE}" &> /dev/null; then
        log_success "ArgoCD is deployed"
    else
        log_warning "ArgoCD is not deployed"
    fi

    # Check monitoring
    if kubectl get deployment prometheus-grafana -n monitoring &> /dev/null; then
        log_success "Monitoring stack is deployed"
    else
        log_warning "Monitoring stack is not deployed"
    fi

    if [[ ${errors} -eq 0 ]]; then
        log_success "CI/CD setup validation passed!"
        return 0
    else
        log_error "CI/CD setup validation failed with ${errors} errors"
        return 1
    fi
}

# ============================================================================
# Main Setup Functions
# ============================================================================

setup_all() {
    log_info "Starting complete CI/CD setup..."

    check_prerequisites
    setup_kubernetes_namespaces
    setup_docker_registry_secret
    setup_gitlab_runner
    setup_github_runner
    setup_argocd
    setup_monitoring
    setup_security_tools
    validate_setup

    log_success "CI/CD setup complete! 🎉"
    print_summary
}

print_summary() {
    echo ""
    echo "========================================================================"
    echo "                    CI/CD Setup Summary"
    echo "========================================================================"
    echo ""
    echo "✅ Kubernetes namespaces:"
    echo "   - Staging: ${STAGING_NAMESPACE}"
    echo "   - Production: ${PRODUCTION_NAMESPACE}"
    echo ""
    echo "✅ ArgoCD:"
    echo "   - Namespace: ${ARGOCD_NAMESPACE}"
    echo "   - Access: kubectl port-forward svc/argocd-server -n ${ARGOCD_NAMESPACE} 8080:443"
    echo "   - URL: https://localhost:8080"
    echo ""
    echo "✅ Monitoring:"
    echo "   - Prometheus: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
    echo "   - Grafana: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Configure GitLab/GitHub secrets (see README.md)"
    echo "   2. Push code to trigger CI/CD pipeline"
    echo "   3. Monitor deployment via ArgoCD UI"
    echo "   4. Check application health in Grafana dashboards"
    echo ""
    echo "========================================================================"
}

# ============================================================================
# Command-line Interface
# ============================================================================

show_help() {
    cat <<EOF
SDR-O-RAN Platform CI/CD Setup Script

Usage: $0 [OPTIONS]

Options:
    --all               Set up everything (default)
    --namespaces        Set up Kubernetes namespaces only
    --gitlab            Set up GitLab CI/CD runner
    --github            Set up GitHub Actions runner
    --argocd            Set up ArgoCD for GitOps
    --monitoring        Set up Prometheus and Grafana
    --security          Set up security scanning tools
    --validate          Validate existing setup
    -h, --help          Show this help message

Environment Variables:
    KUBE_CONTEXT                Kubernetes context to use
    DOCKER_REGISTRY             Docker registry URL (default: ghcr.io)
    DOCKER_USERNAME             Docker registry username
    DOCKER_PASSWORD             Docker registry password
    GITLAB_URL                  GitLab URL (default: https://gitlab.com)
    GITLAB_REGISTRATION_TOKEN   GitLab runner registration token
    GITHUB_TOKEN                GitHub personal access token
    GITHUB_REPO                 GitHub repository (default: sdr-oran/sdr-platform)

Examples:
    # Set up everything
    ./setup-cicd.sh --all

    # Set up only ArgoCD
    ./setup-cicd.sh --argocd

    # Set up with custom Docker registry
    DOCKER_REGISTRY=registry.example.com \\
    DOCKER_USERNAME=myuser \\
    DOCKER_PASSWORD=mypassword \\
    ./setup-cicd.sh --namespaces

For more information, see README.md
EOF
}

main() {
    if [[ $# -eq 0 ]]; then
        setup_all
        exit 0
    fi

    case "$1" in
        --all)
            setup_all
            ;;
        --namespaces)
            check_prerequisites
            setup_kubernetes_namespaces
            setup_docker_registry_secret
            ;;
        --gitlab)
            check_prerequisites
            setup_gitlab_runner
            ;;
        --github)
            check_prerequisites
            setup_github_runner
            ;;
        --argocd)
            check_prerequisites
            setup_argocd
            ;;
        --monitoring)
            check_prerequisites
            setup_monitoring
            ;;
        --security)
            check_prerequisites
            setup_security_tools
            ;;
        --validate)
            validate_setup
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

# ============================================================================
# End of Setup Script
# ============================================================================
