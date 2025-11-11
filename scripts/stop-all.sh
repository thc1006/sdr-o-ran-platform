#!/bin/bash
#
# Stop All Services
#

cd "$(dirname "$0")/.."

echo "🛑 Stopping all containers..."
docker-compose down

echo ""
echo "📊 Final container status:"
docker-compose ps

echo ""
echo "✅ All services stopped"
