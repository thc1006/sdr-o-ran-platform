#!/bin/bash
# NTN xApps Docker Build Script
# Builds and optimizes all Docker images for the NTN simulation platform

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VERBOSE=0
PUSH=0
REGISTRY=""
NO_CACHE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -p|--push)
            PUSH=1
            shift
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -v, --verbose    Verbose output"
            echo "  -p, --push       Push images to registry"
            echo "  -r, --registry   Docker registry URL"
            echo "  --no-cache       Build without using cache"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=== NTN xApps Docker Build Script ===${NC}"
echo -e "${BLUE}Project root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}Docker context: $SCRIPT_DIR${NC}"
echo ""

# Build arguments
BUILD_ARGS=""
[ $NO_CACHE -eq 1 ] && BUILD_ARGS="--no-cache"
[ $VERBOSE -eq 1 ] && BUILD_ARGS="$BUILD_ARGS --progress=plain"

cd "$SCRIPT_DIR" || exit 1

# Function to build an image
build_image() {
    local dockerfile=$1
    local image_name=$2
    local version=${3:-latest}

    echo -e "${YELLOW}Building: $image_name:$version${NC}"
    echo "Dockerfile: $dockerfile"

    docker build $BUILD_ARGS \
        -f "$dockerfile" \
        -t "$image_name:$version" \
        -t "$image_name:latest" \
        "$PROJECT_ROOT"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully built $image_name:$version${NC}"
    else
        echo -e "${RED}✗ Failed to build $image_name:$version${NC}"
        return 1
    fi

    # Show image size
    local size=$(docker images --format "{{.Size}}" "$image_name:$version")
    echo -e "${BLUE}Image size: $size${NC}"
    echo ""
}

# Build all images
echo -e "${BLUE}Stage 1: Building Docker images...${NC}"
echo ""

build_image "Dockerfile.e2-termination" "ntn/e2-termination" "1.0.0" || exit 1
build_image "Dockerfile.handover-xapp" "ntn/handover-xapp" "1.0.0" || exit 1
build_image "Dockerfile.power-xapp" "ntn/power-xapp" "1.0.0" || exit 1

# List built images
echo -e "${BLUE}Stage 2: Listing all built images...${NC}"
docker images | grep ntn/
echo ""

# Calculate total size
echo -e "${BLUE}Stage 3: Image Statistics${NC}"
TOTAL_SIZE=0
for image in "ntn/e2-termination:latest" "ntn/handover-xapp:latest" "ntn/power-xapp:latest"; do
    SIZE=$(docker inspect "$image" --format='{{.Size}}')
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "$image: ${SIZE_MB}MB"
    TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
done

TOTAL_SIZE_MB=$((TOTAL_SIZE / 1024 / 1024))
echo -e "${GREEN}Total size of all images: ${TOTAL_SIZE_MB}MB${NC}"
echo ""

# Validate images
echo -e "${BLUE}Stage 4: Validating images...${NC}"
for image in "ntn/e2-termination:latest" "ntn/handover-xapp:latest" "ntn/power-xapp:latest"; do
    echo "Validating $image..."
    docker inspect "$image" > /dev/null && echo -e "${GREEN}✓ $image is valid${NC}" || echo -e "${RED}✗ $image is invalid${NC}"
done
echo ""

# Push if requested
if [ $PUSH -eq 1 ]; then
    if [ -z "$REGISTRY" ]; then
        echo -e "${RED}Error: Registry URL required for push (use -r flag)${NC}"
        exit 1
    fi

    echo -e "${BLUE}Stage 5: Pushing images to registry...${NC}"
    for image in "ntn/e2-termination" "ntn/handover-xapp" "ntn/power-xapp"; do
        docker tag "${image}:latest" "${REGISTRY}/${image}:latest"
        docker push "${REGISTRY}/${image}:latest"
        echo -e "${GREEN}✓ Pushed ${REGISTRY}/${image}:latest${NC}"
    done
fi

echo -e "${GREEN}=== Build Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Run 'docker-compose up -d' to start services"
echo "  2. Check service health: 'docker-compose ps'"
echo "  3. View logs: 'docker-compose logs -f'"
echo "  4. Access dashboards:"
echo "     - Prometheus: http://localhost:9090"
echo "     - E2 Termination: http://localhost:8082"
echo "     - Handover xApp: http://localhost:8080"
echo "     - Power Control xApp: http://localhost:8081"
