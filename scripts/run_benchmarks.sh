#!/bin/bash
# Performance benchmark runner

echo "SDR-O-RAN Platform - Performance Benchmarks"
echo "=============================================="

cd /home/gnb/thc1006/sdr-o-ran-platform
source venv/bin/activate

echo ""
echo "Running gRPC performance tests..."
pytest tests/performance/ -v --tb=short

echo ""
echo "Benchmark complete!"
