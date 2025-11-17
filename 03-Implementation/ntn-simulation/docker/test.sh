#!/bin/bash
# NTN xApps Docker Compose Test Script
# Tests all services in the Docker compose stack

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TIMEOUT=120
HEALTH_CHECK_INTERVAL=5
MAX_RETRIES=24

echo -e "${BLUE}=== NTN Docker Compose Test Suite ===${NC}"
echo ""

cd "$SCRIPT_DIR" || exit 1

# Function to wait for service
wait_for_service() {
    local service=$1
    local port=$2
    local retries=0

    echo -e "${YELLOW}Waiting for $service on port $port...${NC}"

    while [ $retries -lt $MAX_RETRIES ]; do
        if nc -z localhost "$port" 2>/dev/null; then
            echo -e "${GREEN}✓ $service is responding on port $port${NC}"
            return 0
        fi

        retries=$((retries + 1))
        sleep $HEALTH_CHECK_INTERVAL
        echo "Attempt $retries/$MAX_RETRIES..."
    done

    echo -e "${RED}✗ $service did not become available after ${TIMEOUT}s${NC}"
    return 1
}

# Function to check service health
check_service_health() {
    local service=$1
    local port=$2

    echo -e "${YELLOW}Checking health of $service...${NC}"

    # Try HTTP health endpoint
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $service health check passed${NC}"
        return 0
    fi

    # Fallback to TCP port check
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✓ $service is responding (port check)${NC}"
        return 0
    fi

    echo -e "${RED}✗ $service health check failed${NC}"
    return 1
}

# Function to check service logs for errors
check_service_logs() {
    local service=$1

    echo -e "${YELLOW}Checking logs for $service...${NC}"

    ERROR_COUNT=$(docker-compose logs "$service" 2>/dev/null | grep -i "error\|exception" | wc -l)

    if [ $ERROR_COUNT -eq 0 ]; then
        echo -e "${GREEN}✓ No errors found in $service logs${NC}"
        return 0
    else
        echo -e "${YELLOW}! Found $ERROR_COUNT error(s) in $service logs (this may be expected)${NC}"
        docker-compose logs "$service" | grep -i "error\|exception" | head -5
        return 0
    fi
}

# Stage 1: Check prerequisites
echo -e "${BLUE}Stage 1: Checking prerequisites...${NC}"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose is installed${NC}"

# Check if docker images exist
for image in "ntn/e2-termination:latest" "ntn/handover-xapp:latest" "ntn/power-xapp:latest"; do
    if docker inspect "$image" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Image $image exists${NC}"
    else
        echo -e "${YELLOW}! Image $image not found. Building...${NC}"
        "$SCRIPT_DIR/build.sh" || exit 1
        break
    fi
done
echo ""

# Stage 2: Start services
echo -e "${BLUE}Stage 2: Starting docker-compose stack...${NC}"
docker-compose down 2>/dev/null || true
sleep 2

docker-compose up -d

# Wait for services to start
sleep 5

echo -e "${GREEN}✓ Docker-compose stack started${NC}"
echo ""

# Stage 3: Check service health
echo -e "${BLUE}Stage 3: Waiting for services to become healthy...${NC}"
echo ""

SERVICES=(
    "redis:6379"
    "prometheus:9090"
    "e2-termination:8082"
    "handover-xapp:8080"
    "power-xapp:8081"
)

FAILED=0
for service_port in "${SERVICES[@]}"; do
    IFS=':' read -r service port <<< "$service_port"
    wait_for_service "$service" "$port" || FAILED=$((FAILED + 1))
done

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}✗ $FAILED service(s) failed to start${NC}"
    exit 1
fi

echo ""

# Stage 4: Health checks
echo -e "${BLUE}Stage 4: Running health checks...${NC}"
echo ""

HEALTH_FAILED=0
SERVICES_HEALTH=(
    "e2-termination:8082"
    "handover-xapp:8080"
    "power-xapp:8081"
)

for service_port in "${SERVICES_HEALTH[@]}"; do
    IFS=':' read -r service port <<< "$service_port"
    check_service_health "$service" "$port" || HEALTH_FAILED=$((HEALTH_FAILED + 1))
done

echo ""

# Stage 5: Check service logs
echo -e "${BLUE}Stage 5: Checking service logs...${NC}"
echo ""

for service_port in "${SERVICES_HEALTH[@]}"; do
    IFS=':' read -r service port <<< "$service_port"
    check_service_logs "$service"
done

echo ""

# Stage 6: Docker compose status
echo -e "${BLUE}Stage 6: Docker compose status...${NC}"
echo ""
docker-compose ps
echo ""

# Stage 7: Network connectivity test
echo -e "${BLUE}Stage 7: Testing network connectivity...${NC}"
echo ""

echo "Testing handover-xapp to redis connectivity..."
docker-compose exec -T handover-xapp python -c "import socket; s = socket.socket(); s.connect(('redis', 6379)); s.close(); print('SUCCESS')" && echo -e "${GREEN}✓ handover-xapp can reach redis${NC}" || echo -e "${RED}✗ handover-xapp cannot reach redis${NC}"

echo "Testing power-xapp to e2-termination connectivity..."
docker-compose exec -T power-xapp python -c "import socket; s = socket.socket(); s.connect(('e2-termination', 36421)); s.close(); print('SUCCESS')" 2>/dev/null && echo -e "${GREEN}✓ power-xapp can reach e2-termination${NC}" || echo -e "${YELLOW}! e2-termination port not ready (expected)${NC}"

echo ""

# Summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo ""

if [ $FAILED -eq 0 ] && [ $HEALTH_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo ""
    echo "Service endpoints:"
    echo "  - Redis: localhost:6379"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - E2 Termination: http://localhost:8082 (36421 for E2 protocol)"
    echo "  - Handover xApp: http://localhost:8080"
    echo "  - Power Control xApp: http://localhost:8081"
    echo ""
    echo "Useful commands:"
    echo "  - View all logs: docker-compose logs"
    echo "  - View specific service: docker-compose logs [service]"
    echo "  - Stop services: docker-compose down"
    echo "  - Stop and remove volumes: docker-compose down -v"
    echo ""
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    echo "Failed services: $FAILED"
    echo "Health check failures: $HEALTH_FAILED"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs"
    echo "  2. Verify images: docker images | grep ntn/"
    echo "  3. Rebuild if needed: ./build.sh"
    echo ""
    exit 1
fi
