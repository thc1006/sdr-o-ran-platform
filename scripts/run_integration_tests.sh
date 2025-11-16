#!/bin/bash
# Integration test runner for SDR-O-RAN Platform
# Runs end-to-end tests across all components

set -e  # Exit on error

echo "SDR-O-RAN Platform - Integration Test Suite"
echo "=============================================="

PROJECT_ROOT="/home/gnb/thc1006/sdr-o-ran-platform"
cd "$PROJECT_ROOT"

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Test 1: gRPC Connection Test
echo ""
echo "Test 1: gRPC Protobuf Stubs"
echo "----------------------------"
cd 03-Implementation/integration/sdr-oran-connector
python3 test_grpc_connection.py
if [ $? -eq 0 ]; then
    echo "gRPC stubs test PASSED"
else
    echo "gRPC stubs test FAILED"
    exit 1
fi

# Test 2: TLS Connection Test (if implemented)
echo ""
echo "Test 2: TLS Encrypted Connection"
echo "---------------------------------"
if [ -f "test_tls_connection.py" ] && [ -d "certs" ]; then
    python3 test_tls_connection.py
    if [ $? -eq 0 ]; then
        echo "TLS connection test PASSED"
    else
        echo "TLS connection test FAILED (may need running server)"
    fi
else
    echo "TLS tests not yet available"
fi

# Test 3: Infrastructure Tests
echo ""
echo "Test 3: Infrastructure Test Suite"
echo "----------------------------------"
cd "$PROJECT_ROOT"
if [ -d "tests/infrastructure" ]; then
    pytest tests/infrastructure/ -v --tb=short
    if [ $? -eq 0 ]; then
        echo "Infrastructure tests PASSED"
    else
        echo "Infrastructure tests FAILED"
        exit 1
    fi
else
    echo "Infrastructure tests not found, skipping"
fi

# Test 4: Unit Tests (if they exist)
echo ""
echo "Test 4: Unit Test Suite"
echo "-----------------------"
if [ -d "tests/unit" ]; then
    pytest tests/unit/ -v --tb=short
    if [ $? -eq 0 ]; then
        echo "Unit tests PASSED"
    else
        echo "Unit tests FAILED"
        exit 1
    fi
else
    echo "Unit tests not found, skipping"
fi

# Test 5: Integration Tests (if they exist)
echo ""
echo "Test 5: Integration Test Suite"
echo "-------------------------------"
if [ -d "tests/integration" ]; then
    pytest tests/integration/ -v --tb=short
    if [ $? -eq 0 ]; then
        echo "Integration tests PASSED"
    else
        echo "Integration tests FAILED"
        exit 1
    fi
else
    echo "Integration tests not found, skipping"
fi

# Test 6: Code Coverage Analysis (if pytest-cov is installed)
echo ""
echo "Test 6: Code Coverage Analysis"
echo "-------------------------------"
if python3 -c "import pytest_cov" 2>/dev/null; then
    pytest tests/ --cov=03-Implementation --cov-report=term-missing --cov-report=html
    echo "Coverage report generated at htmlcov/index.html"
else
    echo "pytest-cov not installed, skipping coverage analysis"
fi

# Test 7: Critical Import Tests
echo ""
echo "Test 7: Critical Import Tests"
echo "------------------------------"
python3 << 'EOF'
import sys
sys.path.insert(0, '03-Implementation/integration/sdr-oran-connector')

try:
    import sdr_oran_pb2
    import sdr_oran_pb2_grpc
    print("gRPC stubs import successful")
except ImportError as e:
    print(f"gRPC stubs import failed: {e}")
    sys.exit(1)

try:
    import grpc
    import fastapi
    import zmq
    import numpy as np
    print("Core dependencies import successful")
except ImportError as e:
    print(f"Core dependencies import failed: {e}")
    sys.exit(1)

print("All imports successful")
EOF

# Summary
echo ""
echo "=============================================="
echo "Integration Test Suite Complete"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Review coverage report: htmlcov/index.html"
echo "  2. Start gRPC server: cd 03-Implementation/integration/sdr-oran-connector && python3 sdr_grpc_server.py"
echo "  3. Deploy with Docker: docker-compose up -d"
echo ""
