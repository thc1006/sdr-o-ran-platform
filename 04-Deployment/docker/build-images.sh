#!/bin/bash
# Build Docker images for SDR-O-RAN Platform
# Usage: ./build-images.sh [--push] [--registry REGISTRY]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
REGISTRY=""
PUSH=false
VERSION="1.0.0"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set image names
if [ -n "$REGISTRY" ]; then
    PREFIX="${REGISTRY}/"
else
    PREFIX=""
fi

E2_IMAGE="${PREFIX}sdr-oran/e2-interface:${VERSION}"
QOS_IMAGE="${PREFIX}sdr-oran/xapp-qos-optimizer:${VERSION}"
HANDOVER_IMAGE="${PREFIX}sdr-oran/xapp-handover-manager:${VERSION}"
GRPC_IMAGE="${PREFIX}sdr-oran/grpc-server:${VERSION}"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Building SDR-O-RAN Docker Images${NC}"
echo -e "${GREEN}=====================================${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$PROJECT_ROOT"

# Build E2 Interface
echo -e "\n${YELLOW}Building E2 Interface image...${NC}"
docker build -f 04-Deployment/docker/e2-interface.Dockerfile \
    -t "$E2_IMAGE" \
    -t "${PREFIX}sdr-oran/e2-interface:latest" \
    .
echo -e "${GREEN}✓ E2 Interface image built${NC}"

# Build QoS xApp
echo -e "\n${YELLOW}Building QoS Optimizer xApp image...${NC}"
docker build -f 04-Deployment/docker/xapp-qos.Dockerfile \
    -t "$QOS_IMAGE" \
    -t "${PREFIX}sdr-oran/xapp-qos-optimizer:latest" \
    .
echo -e "${GREEN}✓ QoS xApp image built${NC}"

# Build Handover xApp
echo -e "\n${YELLOW}Building Handover Manager xApp image...${NC}"
docker build -f 04-Deployment/docker/xapp-handover.Dockerfile \
    -t "$HANDOVER_IMAGE" \
    -t "${PREFIX}sdr-oran/xapp-handover-manager:latest" \
    .
echo -e "${GREEN}✓ Handover xApp image built${NC}"

# List images
echo -e "\n${GREEN}Built images:${NC}"
docker images | grep sdr-oran

# Push if requested
if [ "$PUSH" = true ]; then
    echo -e "\n${YELLOW}Pushing images to registry...${NC}"

    docker push "$E2_IMAGE"
    docker push "${PREFIX}sdr-oran/e2-interface:latest"

    docker push "$QOS_IMAGE"
    docker push "${PREFIX}sdr-oran/xapp-qos-optimizer:latest"

    docker push "$HANDOVER_IMAGE"
    docker push "${PREFIX}sdr-oran/xapp-handover-manager:latest"

    echo -e "${GREEN}✓ All images pushed${NC}"
fi

echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
