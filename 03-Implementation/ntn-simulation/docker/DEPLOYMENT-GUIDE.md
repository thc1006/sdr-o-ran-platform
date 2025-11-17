# NTN xApps Docker Deployment Guide

Complete step-by-step guide for deploying NTN xApps in production environments.

## Pre-Deployment Checklist

- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] At least 20GB free disk space
- [ ] 8GB+ RAM available
- [ ] 4+ CPU cores
- [ ] Network connectivity (for pulling base images)
- [ ] Git repository cloned
- [ ] Port 8080, 8081, 8082, 36421, 6379, 9090 available

## Step 1: Environment Preparation

### 1.1 Install Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

**CentOS/RHEL:**
```bash
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

**macOS:**
```bash
# Using Homebrew
brew install --cask docker
# Or download from https://www.docker.com/products/docker-desktop
```

### 1.2 Verify Installation

```bash
docker --version        # Should be 20.10.0 or higher
docker-compose --version  # Should be 2.0.0 or higher
docker run hello-world  # Should run without errors
```

## Step 2: Prepare NTN Codebase

### 2.1 Clone Repository

```bash
git clone <repository-url>
cd sdr-o-ran-platform/03-Implementation/ntn-simulation
```

### 2.2 Verify Directory Structure

```bash
ls -la
# Expected directories:
# - xapps/
# - e2_ntn_extension/
# - OpenNTN/
# - orbit_propagation/
# - docker/
```

### 2.3 Check Requirements

```bash
cat requirements.txt
# Should contain all necessary Python packages
```

## Step 3: Build Docker Images

### 3.1 Navigate to Docker Directory

```bash
cd docker
pwd  # Should end with /docker
```

### 3.2 Build All Images

**Method 1: Using build.sh script**
```bash
./build.sh

# With options:
./build.sh --verbose           # Show build details
./build.sh --no-cache          # Force rebuild
./build.sh --push --registry my.registry.com  # Push to registry
```

**Method 2: Using Makefile**
```bash
cd ..
make -C docker build

# With options:
make -C docker build-verbose
make -C docker build-nocache
make -C docker build-push DOCKER_REGISTRY=my.registry.com
```

**Method 3: Using docker-compose**
```bash
docker-compose build
docker-compose build --no-cache
```

### 3.3 Verify Build Success

```bash
docker images | grep ntn/

# Expected output:
# ntn/e2-termination        latest      <hash>    850MB
# ntn/e2-termination        1.0.0       <hash>    850MB
# ntn/handover-xapp         latest      <hash>    850MB
# ntn/handover-xapp         1.0.0       <hash>    850MB
# ntn/power-xapp            latest      <hash>    850MB
# ntn/power-xapp            1.0.0       <hash>    850MB
```

### 3.4 Check Image Details

```bash
# Inspect specific image
docker inspect ntn/e2-termination:latest

# Get image size
docker images --format "table {{.Repository}}\t{{.Size}}" | grep ntn/

# View image layers
docker history ntn/e2-termination:latest
```

## Step 4: Configure Deployment

### 4.1 Create Environment File

```bash
cd docker
cp .env.example .env
vim .env  # Edit as needed
```

### 4.2 Update Configuration

Edit `.env` for your environment:

```bash
# Logging
LOG_LEVEL=INFO

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# E2 Termination
E2_TERMINATION_PORT=36421

# Resource limits (optional)
MEMORY_LIMIT=2g
CPU_LIMIT=2
```

### 4.3 Customize docker-compose.yml

Optional customizations:

```yaml
# Change port mappings
services:
  handover-xapp:
    ports:
      - "9080:8080"  # External:Internal

# Add resource limits
services:
  handover-xapp:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Step 5: Start Services

### 5.1 Start in Background

```bash
docker-compose up -d

# Verify containers are running
docker-compose ps

# Expected status: Up
```

### 5.2 Wait for Services to Be Ready

```bash
# Monitor startup
docker-compose logs -f

# Wait about 10-15 seconds for all services to start
sleep 15

# Check health
docker-compose ps
```

### 5.3 Verify Service Connectivity

```bash
# Check Redis connection
redis-cli -h localhost ping

# Check E2 Termination port
nc -zv localhost 36421

# Check HTTP endpoints
curl http://localhost:8080/health  # Handover xApp
curl http://localhost:8081/health  # Power xApp
curl http://localhost:8082/health  # E2 Termination
curl http://localhost:9090         # Prometheus
```

## Step 6: Test Deployment

### 6.1 Run Test Suite

```bash
./test.sh

# Expected output: "All tests passed!"
```

### 6.2 Manual Testing

```bash
# Test handover xApp
docker-compose exec handover-xapp python -c "print('Handover xApp is running')"

# Test power xApp
docker-compose exec power-xapp python -c "print('Power xApp is running')"

# Test E2 Termination
docker-compose exec e2-termination python -c "print('E2 Termination is running')"

# Test Redis connectivity
docker-compose exec redis redis-cli PING
```

### 6.3 View Service Logs

```bash
# All services
docker-compose logs

# Tail logs
docker-compose logs -f

# Specific service
docker-compose logs -f handover-xapp

# Last N lines
docker-compose logs --tail=100 e2-termination

# With timestamps
docker-compose logs -t
```

## Step 7: Monitor and Validate

### 7.1 Check Container Health

```bash
# Real-time monitoring
docker stats

# Container information
docker-compose ps -a

# Inspect specific container
docker inspect ntn-handover-xapp
```

### 7.2 Monitor Logs for Errors

```bash
# Check for errors
docker-compose logs | grep -i error

# Monitor specific level
docker-compose logs --tail=50 | grep -i warning
```

### 7.3 Access Monitoring Dashboards

Open in browser:
- **Prometheus**: http://localhost:9090
- **Redis Commander** (if installed): http://localhost:8081
- **xApp APIs**:
  - http://localhost:8080/metrics (Handover)
  - http://localhost:8081/metrics (Power)
  - http://localhost:8082/metrics (E2)

### 7.4 Test Network Connectivity

```bash
# Test xApp to Redis connectivity
docker-compose exec handover-xapp ping redis

# Test xApp to E2 Termination
docker-compose exec power-xapp python -c "
import socket
try:
    s = socket.socket()
    s.connect(('e2-termination', 36421))
    s.close()
    print('Successfully connected to e2-termination:36421')
except Exception as e:
    print(f'Connection failed: {e}')
"

# Test E2 to Redis
docker-compose exec e2-termination python -c "
import socket
try:
    s = socket.socket()
    s.connect(('redis', 6379))
    s.close()
    print('Successfully connected to redis:6379')
except Exception as e:
    print(f'Connection failed: {e}')
"
```

## Step 8: Production Hardening

### 8.1 Enable Resource Limits

Add to docker-compose.yml:

```yaml
services:
  handover-xapp:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
  power-xapp:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
  e2-termination:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 8.2 Configure Log Rotation

Already configured in docker-compose.yml:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 8.3 Set Up Data Persistence

```bash
# Create volume for backups
mkdir -p /var/ntn/backups

# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Backup Prometheus data
docker run --rm -v ntn_prometheus_data:/data -v /var/ntn/backups:/backup \
  alpine tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz -C /data .
```

### 8.4 Configure Monitoring Alerts

Edit `prometheus.yml` to add alerting rules:

```yaml
rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093
```

### 8.5 Enable Container Restart Policy

Already configured (restart: unless-stopped), but can be verified:

```bash
docker inspect ntn-handover-xapp | grep -A 5 RestartPolicy
```

## Step 9: Maintenance and Updates

### 9.1 Regular Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/ntn/backups"

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
sleep 2
docker cp ntn-redis:/data/dump.rdb "$BACKUP_DIR/redis-$DATE.rdb"

# Backup Prometheus
docker run --rm -v ntn_prometheus_data:/data -v "$BACKUP_DIR":/backup \
  alpine tar czf "/backup/prometheus-$DATE.tar.gz" -C /data .

echo "Backup completed: $DATE"
```

### 9.2 Update Dependencies

```bash
# Pull latest base images
docker pull python:3.12-slim
docker pull redis:7-alpine
docker pull prom/prometheus:latest

# Rebuild images
./build.sh --no-cache

# Restart services
docker-compose up -d
```

### 9.3 Update Application Code

```bash
# Pull latest code
git pull origin main

# Rebuild Docker images
./build.sh --no-cache

# Restart services
docker-compose down
docker-compose up -d

# Verify health
./test.sh
```

### 9.4 Monitor Disk Usage

```bash
# Check Docker disk usage
docker system df

# Remove dangling images
docker image prune -a

# Remove unused volumes
docker volume prune

# Clean up old logs
docker-compose logs --tail=0 -f > /dev/null
```

## Step 10: Troubleshooting

### 10.1 Service Not Starting

```bash
# Check logs
docker-compose logs <service>

# Common issues:
# 1. Port already in use
lsof -i :8080

# 2. Insufficient memory
free -h

# 3. Docker daemon not running
sudo systemctl status docker
```

### 10.2 Network Issues

```bash
# Test DNS resolution
docker-compose exec handover-xapp nslookup redis
docker-compose exec handover-xapp nslookup e2-termination

# Test network connectivity
docker-compose exec handover-xapp ping redis

# Check network
docker network inspect ntn-network
```

### 10.3 Performance Issues

```bash
# Monitor resource usage
docker stats

# Check container size
docker ps -as

# View logs for performance warnings
docker-compose logs | grep -i slow
```

### 10.4 Reset Everything

```bash
# Complete reset
docker-compose down -v
docker rmi ntn/e2-termination ntn/handover-xapp ntn/power-xapp
docker volume prune -f
docker network prune -f

# Full clean rebuild
./build.sh --no-cache
docker-compose up -d
./test.sh
```

## Operations Cheat Sheet

```bash
# Start/Stop
docker-compose up -d      # Start
docker-compose stop       # Stop
docker-compose restart    # Restart
docker-compose down       # Remove containers

# Monitoring
docker-compose ps         # Status
docker stats              # Resource usage
docker-compose logs -f    # Live logs
docker-compose logs e2-termination  # Service logs

# Testing
./test.sh                 # Full test suite
docker-compose exec <service> bash  # Shell access
curl http://localhost:<port>/health # Health check

# Maintenance
docker-compose up -d      # Pull and update (if rebuilding)
docker volume ls          # List volumes
docker volume inspect <name>  # Inspect volume
redis-cli -h localhost FLUSHDB  # Clear Redis

# Cleanup
docker system prune       # Remove unused resources
docker image prune -a     # Remove unused images
docker volume prune       # Remove unused volumes
```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify health: `./test.sh`
3. Review troubleshooting section above
4. Check Docker daemon status
5. Verify network connectivity
6. Check resource availability

## Next Steps

1. Monitor services regularly
2. Set up automated backups
3. Configure alerting
4. Plan capacity upgrades
5. Document custom configurations
6. Train operations team
7. Establish runbooks for common tasks
