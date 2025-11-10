#!/usr/bin/env bash
#
# Setup Kubernetes namespaces for SDR-O-RAN Platform
#
# REQ-INFRA-002: Cluster must have dedicated namespaces for isolation
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Namespaces configuration
declare -A NAMESPACES=(
    ["sdr-oran-ntn"]="purpose=research"
    ["monitoring"]="purpose=observability"
    ["oran-ric"]="purpose=ran-intelligence"
)

COMMON_LABEL="managed-by=sdr-oran-platform"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot access Kubernetes cluster.${NC}"
    exit 1
fi

echo "Setting up Kubernetes namespaces..."

# Create namespaces
for namespace in "${!NAMESPACES[@]}"; do
    if kubectl get namespace "$namespace" &> /dev/null; then
        echo -e "${YELLOW}Namespace '$namespace' already exists, skipping creation${NC}"
    else
        kubectl create namespace "$namespace"
        echo -e "${GREEN}Created namespace '$namespace'${NC}"
    fi

    # Apply labels
    purpose_label="${NAMESPACES[$namespace]}"
    kubectl label namespace "$namespace" \
        "$COMMON_LABEL" \
        "$purpose_label" \
        --overwrite

    echo -e "${GREEN}Applied labels to '$namespace'${NC}"
done

echo ""
echo -e "${GREEN}All namespaces configured successfully!${NC}"
echo ""
echo "Verify with: kubectl get namespaces --show-labels"
