#!/bin/bash
# Health check for all SDR-O-RAN services

echo "SDR-O-RAN Platform - Service Health Check"
echo "============================================="

PROJECT_ROOT="/home/gnb/thc1006/sdr-o-ran-platform"

# Check 1: Virtual Environment
echo ""
echo "Check 1: Python Virtual Environment"
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "Virtual environment exists"
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "Python version: $(python3 --version)"
else
    echo "Virtual environment not found"
    exit 1
fi

# Check 2: Dependencies
echo ""
echo "Check 2: Core Dependencies"
python3 << 'EOF'
import importlib
deps = ['grpc', 'google.protobuf', 'fastapi', 'zmq', 'numpy']
all_ok = True
for dep in deps:
    try:
        mod = importlib.import_module(dep)
        version = getattr(mod, '__version__', 'unknown')
        print(f"{dep}: {version}")
    except ImportError:
        print(f"{dep}: NOT INSTALLED")
        all_ok = False
exit(0 if all_ok else 1)
EOF

# Check 3: Certificates (if TLS is enabled)
echo ""
echo "Check 3: TLS Certificates"
CERT_DIR="$PROJECT_ROOT/03-Implementation/integration/sdr-oran-connector/certs"
if [ -d "$CERT_DIR" ]; then
    echo "Certificate directory exists"
    for cert in ca.crt server.crt server.key client.crt client.key; do
        if [ -f "$CERT_DIR/$cert" ]; then
            echo "  $cert found"
        else
            echo "  $cert missing"
        fi
    done
else
    echo "TLS certificates not yet generated"
fi

# Check 4: gRPC Stubs
echo ""
echo "Check 4: gRPC Protobuf Stubs"
STUB_DIR="$PROJECT_ROOT/03-Implementation/integration/sdr-oran-connector"
if [ -f "$STUB_DIR/sdr_oran_pb2.py" ] && [ -f "$STUB_DIR/sdr_oran_pb2_grpc.py" ]; then
    echo "gRPC stubs generated"
else
    echo "gRPC stubs missing"
    exit 1
fi

# Check 5: Port Availability
echo ""
echo "Check 5: Port Availability"
for port in 50051 8000 6379 5555; do
    if ! lsof -i :$port > /dev/null 2>&1; then
        echo "Port $port available"
    else
        echo "Port $port in use"
    fi
done

# Check 6: Docker Status
echo ""
echo "Check 6: Docker Status"
if command -v docker &> /dev/null; then
    echo "Docker installed: $(docker --version)"
    if docker info &> /dev/null; then
        echo "Docker daemon running"
    else
        echo "Docker daemon not running"
    fi
else
    echo "Docker not installed"
fi

# Check 7: Directory Structure
echo ""
echo "Check 7: Directory Structure"
for dir in "03-Implementation/integration/sdr-oran-connector" \
           "03-Implementation/simulation" \
           "03-Implementation/sdr-platform" \
           "03-Implementation/ai-ml-pipeline"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        echo "$dir exists"
    else
        echo "$dir missing"
    fi
done

echo ""
echo "=============================================="
echo "Health Check Complete"
echo "=============================================="
