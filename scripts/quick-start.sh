#!/bin/bash
#
# Quick Start Script - Minimal setup for immediate testing
#

set -e

echo "=========================================="
echo "  SDR-O-RAN Quick Start"
echo "=========================================="
echo ""

# Navigate to project
cd "$(dirname "$0")/.."

# Start containers
echo "🚀 Starting all containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "✅ Quick Start Complete!"
echo ""
echo "Access your services:"
echo "  - SDR API:     http://localhost:8000/docs"
echo "  - TensorBoard: http://localhost:6006"
echo "  - Health:      curl http://localhost:8000/healthz"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
