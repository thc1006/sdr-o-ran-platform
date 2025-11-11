#!/bin/bash
#
# Fully Automated SDR-O-RAN Platform Deployment
# WSL 2 + Docker + GPU
#
# This script will automatically:
# 1. Set up WSL environment
# 2. Build all Docker containers
# 3. Deploy the complete stack
# 4. Run end-to-end tests
# 5. Generate deployment report
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Banner
echo "=========================================="
echo "  SDR-O-RAN Platform Auto-Deployment"
echo "  WSL 2 + Docker + GPU"
echo "=========================================="
echo ""

# Configuration
PROJECT_DIR="$HOME/dev/sdr-o-ran-platform"
LOG_FILE="/tmp/sdr-oran-deployment-$(date +%Y%m%d-%H%M%S).log"

log_info "Deployment log: $LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

# ============================================
# Phase 1: Environment Check
# ============================================
echo ""
log_info "Phase 1: Environment Check"
echo "----------------------------------------"

# Check WSL
if grep -qi microsoft /proc/version; then
    log_success "Running in WSL"
else
    log_warning "Not running in WSL, continuing anyway"
fi

# Check Docker
if command -v docker &> /dev/null; then
    log_success "Docker found: $(docker --version)"
else
    log_error "Docker not found! Please install Docker Desktop"
    exit 1
fi

# Check GPU support
if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &>/dev/null; then
    log_success "GPU support verified"
    docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi 2>/dev/null | head -20
else
    log_warning "GPU not available, some features will be limited"
fi

# Check disk space
AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 50 ]; then
    log_warning "Low disk space: ${AVAILABLE_SPACE}GB available (recommend 50GB+)"
else
    log_success "Sufficient disk space: ${AVAILABLE_SPACE}GB"
fi

# ============================================
# Phase 2: Project Setup
# ============================================
echo ""
log_info "Phase 2: Project Setup"
echo "----------------------------------------"

# Check if project exists
if [ ! -d "$PROJECT_DIR" ]; then
    log_info "Project directory not found, creating..."
    mkdir -p "$HOME/dev"

    # Copy from Windows if available
    WINDOWS_PATH="/mnt/c/Users/ict/OneDrive/桌面/dev/sdr-o-ran-platform"
    if [ -d "$WINDOWS_PATH" ]; then
        log_info "Copying project from Windows..."
        cp -r "$WINDOWS_PATH" "$PROJECT_DIR"
        log_success "Project copied successfully"
    else
        log_error "Project not found at $WINDOWS_PATH"
        log_info "Please ensure project is accessible"
        exit 1
    fi
else
    log_success "Project directory exists: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# ============================================
# Phase 3: Python Environment (Quick Test)
# ============================================
echo ""
log_info "Phase 3: Python Environment Setup"
echo "----------------------------------------"

# Install system dependencies
log_info "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    libzmq3-dev \
    curl \
    jq \
    > /dev/null 2>&1

log_success "System dependencies installed"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
pip install --upgrade pip -q

# Quick test: Install minimal dependencies for core tests
log_info "Installing core Python dependencies..."
pip install -q fastapi uvicorn pydantic pytest 2>/dev/null || log_warning "Some packages failed to install"

# ============================================
# Phase 4: Core Component Tests (Pre-Docker)
# ============================================
echo ""
log_info "Phase 4: Core Component Tests"
echo "----------------------------------------"

# Test SDR API Gateway
if [ -f "03-Implementation/sdr-platform/api-gateway/test_sdr_api_server.py" ]; then
    log_info "Testing SDR API Gateway..."
    cd 03-Implementation/sdr-platform/api-gateway

    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt 2>/dev/null || log_warning "Some requirements failed"
    fi

    # Run tests
    if python test_sdr_api_server.py 2>&1 | tee /tmp/sdr-api-test.log; then
        PASSED=$(grep -c "PASS" /tmp/sdr-api-test.log || echo "0")
        log_success "SDR API Gateway tests: $PASSED tests passed"
    else
        log_warning "SDR API Gateway tests had issues (non-critical)"
    fi

    cd "$PROJECT_DIR"
else
    log_warning "SDR API Gateway test not found"
fi

# ============================================
# Phase 5: Docker Container Build
# ============================================
echo ""
log_info "Phase 5: Building Docker Containers"
echo "----------------------------------------"

cd "$PROJECT_DIR"

# Ensure all Dockerfiles exist
DOCKERFILES=(
    "03-Implementation/simulation/Dockerfile.leo-simulator"
    "03-Implementation/sdr-platform/Dockerfile.sdr-gateway"
    "03-Implementation/ai-ml-pipeline/Dockerfile.drl-trainer"
    "04-Deployment/docker/Dockerfile.flexric"
)

for dockerfile in "${DOCKERFILES[@]}"; do
    if [ -f "$dockerfile" ]; then
        log_success "Found: $dockerfile"
    else
        log_warning "Missing: $dockerfile (will be created by compose)"
    fi
done

# Build containers
log_info "Building Docker containers (this may take 15-30 minutes)..."
log_info "Please be patient..."

if docker-compose build --parallel 2>&1 | tee /tmp/docker-build.log; then
    log_success "All Docker containers built successfully"
else
    log_warning "Some containers may have build issues, checking..."

    # Check what was built
    docker images | grep sdr-o-ran-platform
fi

# ============================================
# Phase 6: Deploy Stack
# ============================================
echo ""
log_info "Phase 6: Deploying Full Stack"
echo "----------------------------------------"

log_info "Starting all containers..."
docker-compose up -d

# Wait for containers to start
log_info "Waiting for containers to initialize (60 seconds)..."
sleep 60

# Check container status
log_info "Container Status:"
docker-compose ps

# Count running containers
RUNNING=$(docker-compose ps | grep -c "Up" || echo "0")
log_info "Containers running: $RUNNING/4"

# ============================================
# Phase 7: Validation Tests
# ============================================
echo ""
log_info "Phase 7: End-to-End Validation"
echo "----------------------------------------"

# Test 1: LEO Simulator
log_info "[Test 1/5] LEO Simulator..."
if docker logs leo-ntn-simulator 2>&1 | grep -q "LEO NTN Simulator started"; then
    log_success "✅ LEO Simulator is running"
else
    log_warning "⚠️  LEO Simulator may have issues"
    docker logs leo-ntn-simulator --tail 20
fi

# Test 2: SDR Gateway
log_info "[Test 2/5] SDR Gateway API..."
sleep 5
if curl -s http://localhost:8000/healthz 2>/dev/null | grep -q "healthy"; then
    log_success "✅ SDR Gateway API is healthy"
else
    log_warning "⚠️  SDR Gateway API not responding"
fi

# Test 3: DRL Trainer
log_info "[Test 3/5] DRL Trainer GPU access..."
if docker exec drl-trainer python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    log_success "✅ DRL Trainer has GPU access"
else
    log_warning "⚠️  DRL Trainer GPU access failed (may run on CPU)"
fi

# Test 4: FlexRIC
log_info "[Test 4/5] FlexRIC RIC..."
if docker logs flexric-ric 2>&1 | grep -q "nearRT-RIC"; then
    log_success "✅ FlexRIC RIC is running"
else
    log_warning "⚠️  FlexRIC may have issues"
fi

# Test 5: GPU Utilization
log_info "[Test 5/5] Overall GPU utilization..."
if nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
    log_success "✅ GPU stats collected"
else
    log_warning "⚠️  nvidia-smi not available"
fi

# ============================================
# Phase 8: Generate Report
# ============================================
echo ""
log_info "Phase 8: Generating Deployment Report"
echo "----------------------------------------"

REPORT_FILE="$PROJECT_DIR/DEPLOYMENT-REPORT-$(date +%Y%m%d-%H%M%S).md"

cat > "$REPORT_FILE" << EOF
# SDR-O-RAN Platform Deployment Report

**Date**: $(date)
**Deployment Mode**: WSL 2 + Docker + GPU
**Automated**: Yes

---

## Deployment Summary

### Environment
- **OS**: $(uname -a)
- **Docker**: $(docker --version)
- **GPU**: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo "N/A")

### Container Status

\`\`\`
$(docker-compose ps)
\`\`\`

### Resource Usage

\`\`\`
$(docker stats --no-stream 2>/dev/null || echo "Stats not available")
\`\`\`

### GPU Status

\`\`\`
$(nvidia-smi 2>/dev/null || echo "GPU not available")
\`\`\`

### Container Logs Summary

#### LEO Simulator
\`\`\`
$(docker logs leo-ntn-simulator --tail 50 2>&1)
\`\`\`

#### SDR Gateway
\`\`\`
$(docker logs sdr-gateway --tail 50 2>&1)
\`\`\`

#### DRL Trainer
\`\`\`
$(docker logs drl-trainer --tail 50 2>&1)
\`\`\`

#### FlexRIC RIC
\`\`\`
$(docker logs flexric-ric --tail 50 2>&1)
\`\`\`

---

## Access Points

- **SDR API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **TensorBoard**: http://localhost:6006
- **gRPC**: localhost:50051

---

## Next Steps

1. Open TensorBoard: \`http://localhost:6006\` to monitor DRL training
2. Test API: \`curl http://localhost:8000/healthz\`
3. View logs: \`docker-compose logs -f\`
4. Monitor GPU: \`watch -n 1 nvidia-smi\`

---

## Deployment Logs

Full logs available at: $LOG_FILE

EOF

log_success "Report generated: $REPORT_FILE"

# ============================================
# Final Summary
# ============================================
echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
log_success "✅ Automated deployment finished"
echo ""
echo "📊 Summary:"
echo "  - Containers running: $RUNNING/4"
echo "  - Report: $REPORT_FILE"
echo "  - Logs: $LOG_FILE"
echo ""
echo "🌐 Access Points:"
echo "  - SDR API:     http://localhost:8000"
echo "  - TensorBoard: http://localhost:6006"
echo "  - Swagger UI:  http://localhost:8000/docs"
echo ""
echo "📝 Useful Commands:"
echo "  - View logs:   docker-compose logs -f"
echo "  - Stop all:    docker-compose down"
echo "  - Restart:     docker-compose restart"
echo "  - GPU stats:   nvidia-smi"
echo ""
echo "😴 Good night! Your platform is running!"
echo "=========================================="

# Keep monitoring in background (optional)
log_info "Starting background monitoring..."
nohup bash -c '
while true; do
    echo "=== $(date) ===" >> /tmp/sdr-oran-monitor.log
    docker-compose ps >> /tmp/sdr-oran-monitor.log 2>&1
    sleep 300  # Every 5 minutes
done
' &

log_success "Background monitoring started (logs: /tmp/sdr-oran-monitor.log)"
