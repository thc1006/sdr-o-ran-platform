#!/bin/bash
#
# Real-time Monitoring Dashboard
#

cd "$(dirname "$0")/.."

while true; do
    clear
    echo "=========================================="
    echo "  SDR-O-RAN Platform Monitor"
    echo "  $(date)"
    echo "=========================================="
    echo ""

    echo "📊 Container Status:"
    docker-compose ps
    echo ""

    echo "💻 Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    echo ""

    if command -v nvidia-smi &> /dev/null; then
        echo "🎮 GPU Status:"
        nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | \
            awk -F',' '{printf "  GPU %s: %s | Temp: %s°C | Util: %s%% | Mem: %s/%s MB\n", $1, $2, $3, $4, $5, $6}'
        echo ""
    fi

    echo "Press Ctrl+C to exit | Refreshing in 5 seconds..."
    sleep 5
done
