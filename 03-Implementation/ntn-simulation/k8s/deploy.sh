#!/bin/bash

# NTN-O-RAN Kubernetes Deployment Script
# This script deploys the complete NTN-O-RAN platform to Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="ntn-oran"
DEPLOYMENT_TYPE="${1:-manual}"  # manual or helm

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    # Check Helm (if needed)
    if [ "$DEPLOYMENT_TYPE" == "helm" ] && ! command -v helm &> /dev/null; then
        log_error "Helm not found. Please install Helm or use manual deployment."
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
        exit 1
    fi

    log_info "Prerequisites check passed"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    kubectl apply -f namespace.yaml
}

deploy_secrets() {
    log_info "Deploying secrets..."

    if [ ! -f "secrets.yaml" ]; then
        log_warn "secrets.yaml not found. Creating from template..."
        if [ -f "secrets.yaml.template" ]; then
            log_error "Please create secrets.yaml from secrets.yaml.template and configure actual secrets"
            exit 1
        fi
    fi

    kubectl apply -f secrets.yaml
}

deploy_configmaps() {
    log_info "Deploying ConfigMaps..."
    kubectl apply -f configmap.yaml
}

deploy_storage() {
    log_info "Deploying persistent volumes..."
    # PVCs are included in deployment manifests
}

deploy_redis() {
    log_info "Deploying Redis..."
    kubectl apply -f deployments/redis-deployment.yaml
    kubectl apply -f services/redis-service.yaml

    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=5m
}

deploy_core_services() {
    log_info "Deploying core services..."

    kubectl apply -f deployments/e2-termination-deployment.yaml
    kubectl apply -f deployments/handover-xapp-deployment.yaml
    kubectl apply -f deployments/power-xapp-deployment.yaml
    kubectl apply -f deployments/weather-service-deployment.yaml
    kubectl apply -f deployments/orbit-service-deployment.yaml

    kubectl apply -f services/e2-termination-service.yaml
    kubectl apply -f services/handover-xapp-service.yaml
    kubectl apply -f services/power-xapp-service.yaml
    kubectl apply -f services/weather-service.yaml
    kubectl apply -f services/orbit-service.yaml

    log_info "Waiting for core services to be ready..."
    kubectl wait --for=condition=ready pod -l component=ric -n $NAMESPACE --timeout=5m || true
    kubectl wait --for=condition=ready pod -l component=xapp -n $NAMESPACE --timeout=5m || true
}

deploy_monitoring() {
    log_info "Deploying monitoring stack..."

    # Prometheus
    kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml
    kubectl apply -f monitoring/prometheus/prometheus-service.yaml

    # Grafana
    kubectl apply -f monitoring/grafana/grafana-deployment.yaml
    kubectl apply -f monitoring/grafana/grafana-service.yaml

    log_info "Waiting for monitoring to be ready..."
    kubectl wait --for=condition=ready pod -l app=prometheus -n $NAMESPACE --timeout=5m || true
    kubectl wait --for=condition=ready pod -l app=grafana -n $NAMESPACE --timeout=5m || true
}

deploy_logging() {
    read -p "Deploy ELK logging stack? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deploying logging stack..."

        kubectl apply -f logging/elasticsearch/elasticsearch-deployment.yaml
        kubectl apply -f logging/logstash/logstash-deployment.yaml
        kubectl apply -f logging/kibana/kibana-deployment.yaml
        kubectl apply -f logging/filebeat/filebeat-daemonset.yaml

        log_info "Logging stack deployed (may take several minutes to be ready)"
    fi
}

deploy_ingress_hpa_pdb() {
    log_info "Deploying Ingress, HPA, and PDB..."

    # Check if ingress controller is installed
    if kubectl get ingressclass nginx &> /dev/null; then
        kubectl apply -f ingress.yaml
    else
        log_warn "Nginx ingress controller not found. Skipping ingress deployment."
    fi

    # Check if metrics-server is available for HPA
    if kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        kubectl apply -f hpa.yaml
    else
        log_warn "metrics-server not found. Skipping HPA deployment."
    fi

    kubectl apply -f pdb.yaml
}

verify_deployment() {
    log_info "Verifying deployment..."

    echo ""
    echo "=== Pods Status ==="
    kubectl get pods -n $NAMESPACE

    echo ""
    echo "=== Services Status ==="
    kubectl get services -n $NAMESPACE

    echo ""
    echo "=== HPA Status ==="
    kubectl get hpa -n $NAMESPACE 2>/dev/null || log_warn "HPA not available"

    echo ""
    echo "=== PDB Status ==="
    kubectl get pdb -n $NAMESPACE
}

print_access_info() {
    log_info "Deployment complete!"

    echo ""
    echo "=== Access Information ==="
    echo ""
    echo "Grafana:"
    echo "  kubectl port-forward -n $NAMESPACE svc/grafana-service 3000:3000"
    echo "  Then access: http://localhost:3000"
    echo ""
    echo "Prometheus:"
    echo "  kubectl port-forward -n $NAMESPACE svc/prometheus-service 9090:9090"
    echo "  Then access: http://localhost:9090"
    echo ""
    echo "Kibana (if deployed):"
    echo "  kubectl port-forward -n $NAMESPACE svc/kibana 5601:5601"
    echo "  Then access: http://localhost:5601"
    echo ""
    echo "E2 Termination:"
    echo "  kubectl port-forward -n $NAMESPACE svc/e2-termination-service 8082:8082"
    echo ""
    echo "For more information, see: README.md"
}

deploy_with_helm() {
    log_info "Deploying with Helm..."

    helm upgrade --install ntn-oran ./helm/ntn-oran \
        --namespace $NAMESPACE \
        --create-namespace \
        --wait \
        --timeout 15m

    verify_deployment
    print_access_info
}

deploy_manually() {
    log_info "Starting manual deployment..."

    create_namespace
    deploy_configmaps
    deploy_secrets
    deploy_redis
    deploy_core_services
    deploy_monitoring
    deploy_logging
    deploy_ingress_hpa_pdb
    verify_deployment
    print_access_info
}

# Main execution
main() {
    echo "=========================================="
    echo "  NTN-O-RAN Kubernetes Deployment"
    echo "=========================================="
    echo ""

    check_prerequisites

    if [ "$DEPLOYMENT_TYPE" == "helm" ]; then
        deploy_with_helm
    else
        deploy_manually
    fi
}

# Run main function
main
