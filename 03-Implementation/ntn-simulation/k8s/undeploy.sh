#!/bin/bash

# NTN-O-RAN Kubernetes Undeployment Script
# This script removes the NTN-O-RAN platform from Kubernetes

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

confirm_deletion() {
    echo ""
    log_warn "This will delete ALL resources in namespace: $NAMESPACE"
    log_warn "This action CANNOT be undone!"
    echo ""
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
    echo
    if [[ ! $REPLY == "yes" ]]; then
        log_info "Undeployment cancelled"
        exit 0
    fi
}

backup_resources() {
    log_info "Creating backup of resources..."

    BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p $BACKUP_DIR

    kubectl get all -n $NAMESPACE -o yaml > $BACKUP_DIR/all-resources.yaml
    kubectl get configmap -n $NAMESPACE -o yaml > $BACKUP_DIR/configmaps.yaml
    kubectl get secret -n $NAMESPACE -o yaml > $BACKUP_DIR/secrets.yaml
    kubectl get pvc -n $NAMESPACE -o yaml > $BACKUP_DIR/pvcs.yaml

    log_info "Backup saved to: $BACKUP_DIR"
}

undeploy_with_helm() {
    log_info "Uninstalling Helm release..."

    if helm list -n $NAMESPACE | grep -q ntn-oran; then
        helm uninstall ntn-oran -n $NAMESPACE
        log_info "Helm release uninstalled"
    else
        log_warn "Helm release 'ntn-oran' not found"
    fi
}

delete_kubernetes_resources() {
    log_info "Deleting Kubernetes resources..."

    # Delete in reverse order of dependencies

    log_info "Deleting HPA and PDB..."
    kubectl delete -f hpa.yaml --ignore-not-found=true
    kubectl delete -f pdb.yaml --ignore-not-found=true

    log_info "Deleting Ingress..."
    kubectl delete -f ingress.yaml --ignore-not-found=true

    log_info "Deleting monitoring stack..."
    kubectl delete -f monitoring/grafana/ --ignore-not-found=true
    kubectl delete -f monitoring/prometheus/ --ignore-not-found=true

    log_info "Deleting logging stack..."
    kubectl delete -f logging/filebeat/ --ignore-not-found=true
    kubectl delete -f logging/kibana/ --ignore-not-found=true
    kubectl delete -f logging/logstash/ --ignore-not-found=true
    kubectl delete -f logging/elasticsearch/ --ignore-not-found=true

    log_info "Deleting core services..."
    kubectl delete -f services/ --ignore-not-found=true
    kubectl delete -f deployments/ --ignore-not-found=true

    log_info "Deleting ConfigMaps and Secrets..."
    kubectl delete -f configmap.yaml --ignore-not-found=true
    kubectl delete -f secrets.yaml --ignore-not-found=true

    log_info "Waiting for pods to terminate..."
    kubectl wait --for=delete pod --all -n $NAMESPACE --timeout=5m || true
}

delete_pvcs() {
    log_info "Checking for persistent volume claims..."

    if kubectl get pvc -n $NAMESPACE &> /dev/null; then
        echo ""
        log_warn "Found persistent volume claims. Deleting these will PERMANENTLY delete data!"
        read -p "Delete PVCs? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kubectl delete pvc --all -n $NAMESPACE
            log_info "PVCs deleted"
        else
            log_info "PVCs preserved"
        fi
    fi
}

delete_namespace() {
    log_info "Deleting namespace..."

    if kubectl get namespace $NAMESPACE &> /dev/null; then
        kubectl delete namespace $NAMESPACE
        log_info "Namespace deleted"
    else
        log_warn "Namespace not found"
    fi
}

verify_cleanup() {
    log_info "Verifying cleanup..."

    if kubectl get namespace $NAMESPACE &> /dev/null; then
        log_warn "Namespace still exists (may be in terminating state)"
        kubectl get all -n $NAMESPACE 2>/dev/null || true
    else
        log_info "Namespace successfully removed"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "  NTN-O-RAN Kubernetes Undeployment"
    echo "=========================================="
    echo ""

    # Check if namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_error "Namespace '$NAMESPACE' not found"
        exit 1
    fi

    confirm_deletion
    backup_resources

    if [ "$DEPLOYMENT_TYPE" == "helm" ]; then
        undeploy_with_helm
    else
        delete_kubernetes_resources
    fi

    delete_pvcs
    delete_namespace
    verify_cleanup

    echo ""
    log_info "Undeployment complete!"
    echo ""
    log_info "Backup location: $BACKUP_DIR"
    echo ""
}

# Run main function
main
