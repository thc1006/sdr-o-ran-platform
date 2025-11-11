#!/bin/bash
#
# Test All Components
#

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "  Component Testing Suite"
echo "=========================================="
echo ""

# Test 1: SDR API
echo "[1/6] Testing SDR API Gateway..."
if curl -s http://localhost:8000/healthz | grep -q "healthy"; then
    echo "  ✅ API Gateway: PASS"
else
    echo "  ❌ API Gateway: FAIL"
fi

# Test 2: Swagger UI
echo "[2/6] Testing Swagger UI..."
if curl -s http://localhost:8000/docs | grep -q "swagger"; then
    echo "  ✅ Swagger UI: PASS"
else
    echo "  ❌ Swagger UI: FAIL"
fi

# Test 3: Metrics
echo "[3/6] Testing Prometheus Metrics..."
if curl -s http://localhost:8000/metrics | grep -q "process"; then
    echo "  ✅ Metrics: PASS"
else
    echo "  ❌ Metrics: FAIL"
fi

# Test 4: LEO Simulator
echo "[4/6] Testing LEO Simulator..."
if docker logs leo-ntn-simulator 2>&1 | grep -q "started"; then
    echo "  ✅ LEO Simulator: PASS"
else
    echo "  ❌ LEO Simulator: FAIL"
fi

# Test 5: DRL Trainer GPU
echo "[5/6] Testing DRL Trainer GPU..."
if docker exec drl-trainer python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
    echo "  ✅ DRL Trainer GPU: PASS"
else
    echo "  ⚠️  DRL Trainer GPU: WARN (may be on CPU)"
fi

# Test 6: FlexRIC
echo "[6/6] Testing FlexRIC RIC..."
if docker logs flexric-ric 2>&1 | grep -qE "(RIC|Mock)"; then
    echo "  ✅ FlexRIC: PASS"
else
    echo "  ❌ FlexRIC: FAIL"
fi

echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo ""
echo "Check individual logs for details:"
echo "  docker-compose logs leo-simulator"
echo "  docker-compose logs sdr-gateway"
echo "  docker-compose logs drl-trainer"
echo "  docker-compose logs flexric"
echo ""
