#!/bin/bash
# NTN Docker Compose Management Script
# Simplified commands for common tasks

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse command
COMMAND=${1:-help}

case $COMMAND in
    start)
        echo -e "${BLUE}Starting NTN services...${NC}"
        docker-compose up -d
        echo -e "${GREEN}Services started. Use 'docker-compose ps' to check status.${NC}"
        ;;

    stop)
        echo -e "${BLUE}Stopping NTN services...${NC}"
        docker-compose stop
        echo -e "${GREEN}Services stopped.${NC}"
        ;;

    restart)
        echo -e "${BLUE}Restarting NTN services...${NC}"
        docker-compose restart
        echo -e "${GREEN}Services restarted.${NC}"
        ;;

    down)
        echo -e "${BLUE}Stopping and removing containers...${NC}"
        docker-compose down
        echo -e "${GREEN}Containers removed.${NC}"
        ;;

    clean)
        echo -e "${YELLOW}WARNING: This will remove containers, volumes, and images.${NC}"
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker rmi ntn/e2-termination ntn/handover-xapp ntn/power-xapp
            echo -e "${GREEN}Cleanup complete.${NC}"
        fi
        ;;

    logs)
        SERVICE=${2:-}
        if [ -z "$SERVICE" ]; then
            docker-compose logs -f
        else
            docker-compose logs -f "$SERVICE"
        fi
        ;;

    ps)
        docker-compose ps
        ;;

    build)
        echo -e "${BLUE}Building Docker images...${NC}"
        "$SCRIPT_DIR/build.sh" "${@:2}"
        ;;

    test)
        echo -e "${BLUE}Running tests...${NC}"
        "$SCRIPT_DIR/test.sh"
        ;;

    shell)
        SERVICE=${2:-handover-xapp}
        echo -e "${BLUE}Opening shell in $SERVICE...${NC}"
        docker-compose exec "$SERVICE" bash
        ;;

    health)
        echo -e "${BLUE}Checking service health...${NC}"
        docker-compose ps
        echo ""
        echo -e "${BLUE}Health endpoints:${NC}"
        for port in 8080 8081 8082; do
            echo -n "Port $port: "
            curl -s -f "http://localhost:$port/health" > /dev/null && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAIL${NC}"
        done
        ;;

    stats)
        echo -e "${BLUE}Container resource usage:${NC}"
        docker stats --no-stream
        ;;

    help|"")
        cat << EOF
${BLUE}NTN Docker Compose Management${NC}

Usage: $0 COMMAND [OPTIONS]

Commands:
  start           Start all services
  stop            Stop all services (containers remain)
  restart         Restart all services
  down            Stop and remove containers
  clean           Remove containers, volumes, and images (careful!)
  logs [SERVICE]  View logs (optional: specific service)
  ps              Show running containers
  build           Build Docker images
  test            Run comprehensive tests
  shell [SERVICE] Open shell in container (default: handover-xapp)
  health          Check health of all services
  stats           Show resource usage
  help            Show this help message

Examples:
  $0 start              # Start all services
  $0 logs handover-xapp # View handover xApp logs
  $0 shell power-xapp   # Open shell in power control xApp
  $0 build --verbose    # Rebuild images with verbose output
  $0 test               # Run all tests

EOF
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
