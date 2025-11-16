#!/bin/bash
# SDR-O-RAN Platform Kubernetes Deployment Script
# Usage: ./deploy-all.sh [--dry-run]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DRY_RUN=""
if [ "$1" == "--dry-run" ]; then
    DRY_RUN="--dry-run=client"
    echo -e "${YELLOW}Running in DRY-RUN mode${NC}"
fi

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}SDR-O-RAN Platform Deployment${NC}"
echo -e "${GREEN}=====================================${NC}"

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}kubectl not found. Please install kubectl first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ kubectl found${NC}"
}

# Function to check if cluster is accessible
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Kubernetes cluster accessible${NC}"
}

# Function to create namespace
create_namespace() {
    echo -e "\n${YELLOW}Creating namespace...${NC}"
    kubectl apply -f namespace.yaml $DRY_RUN
    echo -e "${GREEN}✓ Namespace created/verified${NC}"
}

# Function to deploy Redis (SDL backend)
deploy_redis() {
    echo -e "\n${YELLOW}Deploying Redis cluster...${NC}"
    kubectl apply -f redis-cluster.yaml $DRY_RUN

    if [ -z "$DRY_RUN" ]; then
        echo -e "${YELLOW}Waiting for Redis pods to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l app=redis -n sdr-oran --timeout=180s || true
    fi
    echo -e "${GREEN}✓ Redis deployed${NC}"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    echo -e "\n${YELLOW}Deploying monitoring stack (Prometheus + Grafana)...${NC}"
    kubectl apply -f monitoring-stack.yaml $DRY_RUN

    if [ -z "$DRY_RUN" ]; then
        echo -e "${YELLOW}Waiting for Prometheus pod to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l app=prometheus -n sdr-oran --timeout=180s || true

        echo -e "${YELLOW}Waiting for Grafana pod to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l app=grafana -n sdr-oran --timeout=180s || true
    fi
    echo -e "${GREEN}✓ Monitoring stack deployed${NC}"
}

# Function to deploy E2 Interface
deploy_e2_interface() {
    echo -e "\n${YELLOW}Deploying E2 Interface...${NC}"
    kubectl apply -f e2-interface-deployment.yaml $DRY_RUN

    if [ -z "$DRY_RUN" ]; then
        echo -e "${YELLOW}Waiting for E2 Interface pods to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l app=e2-interface -n sdr-oran --timeout=180s || true
    fi
    echo -e "${GREEN}✓ E2 Interface deployed${NC}"
}

# Function to deploy xApps
deploy_xapps() {
    echo -e "\n${YELLOW}Deploying xApps...${NC}"
    kubectl apply -f xapp-qos-deployment.yaml $DRY_RUN
    kubectl apply -f xapp-handover-deployment.yaml $DRY_RUN

    if [ -z "$DRY_RUN" ]; then
        echo -e "${YELLOW}Waiting for xApp pods to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l component=xapp -n sdr-oran --timeout=180s || true
    fi
    echo -e "${GREEN}✓ xApps deployed${NC}"
}

# Function to deploy gRPC server
deploy_grpc_server() {
    echo -e "\n${YELLOW}Deploying gRPC server...${NC}"
    kubectl apply -f grpc-server-deployment.yaml $DRY_RUN

    if [ -z "$DRY_RUN" ]; then
        echo -e "${YELLOW}Waiting for gRPC server pods to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l app=sdr-grpc-server -n sdr-oran --timeout=180s || true
    fi
    echo -e "${GREEN}✓ gRPC server deployed${NC}"
}

# Function to display deployment status
show_status() {
    if [ -z "$DRY_RUN" ]; then
        echo -e "\n${GREEN}=====================================${NC}"
        echo -e "${GREEN}Deployment Status${NC}"
        echo -e "${GREEN}=====================================${NC}"

        echo -e "\n${YELLOW}Pods:${NC}"
        kubectl get pods -n sdr-oran -o wide

        echo -e "\n${YELLOW}Services:${NC}"
        kubectl get svc -n sdr-oran

        echo -e "\n${YELLOW}Deployments:${NC}"
        kubectl get deployments -n sdr-oran

        echo -e "\n${YELLOW}StatefulSets:${NC}"
        kubectl get statefulsets -n sdr-oran

        echo -e "\n${GREEN}=====================================${NC}"
        echo -e "${GREEN}Access Information${NC}"
        echo -e "${GREEN}=====================================${NC}"

        # Get Grafana LoadBalancer IP
        GRAFANA_IP=$(kubectl get svc grafana-service -n sdr-oran -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
        echo -e "${YELLOW}Grafana:${NC} http://${GRAFANA_IP}:3000"
        echo -e "  Username: admin"
        echo -e "  Password: admin12345"

        # Get gRPC server LoadBalancer IP
        GRPC_IP=$(kubectl get svc sdr-grpc-server-service -n sdr-oran -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
        echo -e "\n${YELLOW}gRPC Server:${NC} ${GRPC_IP}:50051"

        echo -e "\n${YELLOW}Prometheus:${NC} kubectl port-forward -n sdr-oran svc/prometheus-service 9090:9090"

        echo -e "\n${GREEN}=====================================${NC}"
    fi
}

# Main deployment flow
main() {
    check_kubectl
    check_cluster

    echo -e "\n${YELLOW}Starting deployment...${NC}"

    create_namespace
    deploy_redis
    deploy_monitoring
    deploy_e2_interface
    deploy_xapps
    deploy_grpc_server

    show_status

    echo -e "\n${GREEN}=====================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}=====================================${NC}"

    if [ -z "$DRY_RUN" ]; then
        echo -e "\n${YELLOW}To monitor the deployment:${NC}"
        echo -e "  kubectl get pods -n sdr-oran -w"
        echo -e "\n${YELLOW}To view logs:${NC}"
        echo -e "  kubectl logs -f -n sdr-oran deployment/e2-interface"
        echo -e "  kubectl logs -f -n sdr-oran deployment/xapp-qos-optimizer"
        echo -e "\n${YELLOW}To undeploy:${NC}"
        echo -e "  kubectl delete namespace sdr-oran"
    fi
}

main "$@"
