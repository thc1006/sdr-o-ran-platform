# NTN xApps Docker Documentation

Production-grade Docker containers for NTN (Non-Terrestrial Network) xApps and supporting services in the O-RAN platform.

## Overview

This Docker setup provides containerized deployment for:

- **E2 Termination Service**: E2SM-NTN interface for RIC communication
- **NTN Handover xApp**: Predictive handover optimization for satellite networks
- **NTN Power Control xApp**: Intelligent power management for satellite links
- **Supporting Services**: Redis (state), Prometheus (metrics)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Compose Stack                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Handover xApp   │  │   Power xApp     │                 │
│  │   (8080/tcp)     │  │   (8081/tcp)     │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                            │
│           └─────────┬───────────┘                            │
│                     │                                        │
│           ┌─────────▼──────────┐                             │
│           │ E2 Termination     │                             │
│           │ (36421/tcp E2 IF)  │                             │
│           │ (8082/tcp HTTP)    │                             │
│           └─────────┬──────────┘                             │
│                     │                                        │
│           ┌─────────┴──────────┐                             │
│           │                    │                             │
│     ┌─────▼──────┐      ┌──────▼────────┐                   │
│     │   Redis    │      │  Prometheus   │                   │
│     │ (6379/tcp) │      │  (9090/tcp)   │                   │
│     └────────────┘      └───────────────┘                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## System Requirements

### Minimum Specifications
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 20GB available space
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Recommended Specifications
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Disk**: 50GB+ available space
- **Network**: 1Gbps bandwidth

## Image Sizes

| Service | Base | Built | Compressed |
|---------|------|-------|------------|
| E2 Termination | python:3.12-slim | ~850MB | ~300MB |
| Handover xApp | python:3.12-slim | ~850MB | ~300MB |
| Power Control xApp | python:3.12-slim | ~850MB | ~300MB |
| Redis | redis:7-alpine | ~36MB | ~12MB |
| Prometheus | prom/prometheus:latest | ~200MB | ~70MB |

**Total Stack**: ~3.8GB disk space for all images

## Quick Start

### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Build Docker Images

```bash
cd docker

# Build all images
./build.sh

# Build with verbose output
./build.sh --verbose

# Build without cache
./build.sh --no-cache

# Push to registry
./build.sh --push --registry my-registry.com
```

### Start Services

```bash
cd docker

# Start all services in background
docker-compose up -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f handover-xapp
```

### Test Deployment

```bash
cd docker

# Run comprehensive tests
./test.sh

# Test services are healthy
docker-compose ps

# Manual health checks
curl http://localhost:8080/health   # Handover xApp
curl http://localhost:8081/health   # Power Control xApp
curl http://localhost:8082/health   # E2 Termination
curl http://localhost:6379          # Redis (should get NOAUTH error if no auth)
curl http://localhost:9090          # Prometheus
```

### Stop Services

```bash
cd docker

# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove all data
docker-compose down -v

# Remove all NTN images
docker rmi ntn/e2-termination ntn/handover-xapp ntn/power-xapp
```

## Configuration

### Environment Variables

#### Global (docker-compose.yml)

```yaml
PYTHONUNBUFFERED=1          # Unbuffered Python output
PYTHONDONTWRITEBYTECODE=1   # Don't create .pyc files
LOG_LEVEL=INFO              # Logging level (DEBUG, INFO, WARNING, ERROR)
```

#### E2 Termination

```yaml
E2_TERMINATION_PORT=36421   # E2 interface port (3GPP standard)
REDIS_HOST=redis            # Redis hostname
REDIS_PORT=6379             # Redis port
```

#### xApps (Handover & Power Control)

```yaml
E2_TERMINATION_HOST=e2-termination  # E2 service hostname
E2_TERMINATION_PORT=36421            # E2 service port
REDIS_HOST=redis                     # Redis hostname
REDIS_PORT=6379                      # Redis port
```

### Volume Mounts

```yaml
# Application code (read-write)
- ../:/app

# Logs (persistent)
- ntn_logs:/var/log/ntn

# Redis data (persistent)
- redis_data:/data

# Prometheus data (persistent)
- prometheus_data:/prometheus
```

### Resource Limits

Edit `docker-compose.yml` to add resource constraints:

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
```

## Service Details

### E2 Termination Service

**Purpose**: Bridges the E2SM-NTN interface for RIC communication

**Port Mapping**:
- `36421/tcp` - E2 protocol interface (3GPP standard)
- `8082/tcp` - HTTP management interface

**Health Check**:
```bash
curl http://localhost:8082/health
```

**Key Features**:
- ASN.1 encoding/decoding
- E2 message serialization
- RIC subscription management
- Metric collection and reporting

### NTN Handover xApp

**Purpose**: Predictive handover optimization for satellite networks

**Port Mapping**:
- `8080/tcp` - HTTP API and metrics

**Health Check**:
```bash
curl http://localhost:8080/health
```

**Features**:
- Time-to-handover prediction
- Next satellite selection (elevation/link quality)
- Handover preparation and execution
- Handover success rate tracking

### NTN Power Control xApp

**Purpose**: Intelligent power management for satellite links

**Port Mapping**:
- `8081/tcp` - HTTP API and metrics

**Health Check**:
```bash
curl http://localhost:8081/health
```

**Features**:
- Link budget monitoring
- Power control recommendations
- Rain fade mitigation
- Power efficiency optimization
- Link quality maximization

### Redis

**Purpose**: Distributed state management and caching

**Port Mapping**:
- `6379/tcp` - Redis protocol

**Health Check**:
```bash
redis-cli ping
# or
echo PING | nc localhost 6379
```

**Data**:
- Persistent storage in `redis_data` volume
- Automatic backup with AOF (Append-Only File)

### Prometheus

**Purpose**: Metrics collection and visualization

**Port Mapping**:
- `9090/tcp` - Prometheus web interface

**Access**: http://localhost:9090

**Metrics Targets**:
- `localhost:8082/metrics` - E2 Termination
- `localhost:8080/metrics` - Handover xApp
- `localhost:8081/metrics` - Power Control xApp

**Configuration**: `prometheus.yml`

## Monitoring and Debugging

### View Logs

```bash
# All services
docker-compose logs

# Tail logs
docker-compose logs -f

# Specific service
docker-compose logs -f handover-xapp

# Last N lines
docker-compose logs --tail=100

# Show timestamps
docker-compose logs -t
```

### Service Status

```bash
# List all containers
docker-compose ps

# Detailed container info
docker inspect ntn-handover-xapp

# View container stats
docker stats ntn-handover-xapp ntn-power-xapp ntn-e2-termination
```

### Verify Network Connectivity

```bash
# Exec into container
docker-compose exec handover-xapp bash

# Test Redis connection
redis-cli -h redis ping

# Test E2 Termination
curl http://e2-termination:8082/health

# Check DNS resolution
nslookup redis
nslookup e2-termination
```

### Access Redis CLI

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Useful commands
KEYS *                    # List all keys
GET key_name              # Get value
MONITOR                   # Real-time command monitor
INFO                      # Server info
FLUSHDB                   # Clear current database
```

### Prometheus Queries

Open http://localhost:9090 and try:

```
# CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes

# Network I/O
rate(container_network_transmit_bytes_total[5m])

# Container restarts
rate(container_last_seen[5m])
```

## Troubleshooting

### Services Not Starting

```bash
# Check Docker daemon
sudo systemctl status docker

# View detailed logs
docker-compose logs --tail=50 handover-xapp

# Check resource availability
free -h
df -h

# Rebuild images
./build.sh --no-cache
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Reduce memory-intensive operations
# Edit docker-compose.yml and add memory limits

# Restart services
docker-compose restart
```

### Network Connectivity Issues

```bash
# Test network
docker-compose exec handover-xapp ping redis

# Inspect network
docker network inspect ntn-network

# Check host DNS
nslookup localhost
```

### Port Conflicts

If ports are already in use:

```bash
# Find which process uses port
lsof -i :8080
sudo fuser -k 8080/tcp

# Or change ports in docker-compose.yml
# Modify port mappings like: "8080:8080" -> "9080:8080"
```

### Container Crashes

```bash
# View exit code
docker inspect ntn-handover-xapp | grep ExitCode

# Restart service
docker-compose restart handover-xapp

# Check for dependency issues
docker-compose logs --tail=100 handover-xapp
```

## Production Deployment

### Security Considerations

1. **Run as Non-Root**: All containers run as non-root user (uid 1000)

2. **Resource Limits**: Add to docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

3. **Network Security**: Update docker-compose.yml:
```yaml
networks:
  ntn-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

4. **Secrets Management**: Use Docker secrets:
```bash
echo "my-password" | docker secret create redis-password -
```

5. **Read-Only Filesystems** (optional):
```yaml
read_only: true
tmpfs:
  - /tmp
  - /var/tmp
```

### Health Checks

All services include health checks configured in docker-compose.yml:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

### Logging Configuration

Production logging setup (json-file driver):

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Backup Strategy

```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Backup volumes
docker run --rm -v ntn_redis_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Backup Prometheus data
docker run --rm -v ntn_prometheus_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup.tar.gz -C /data .
```

### Update Images

```bash
# Pull latest base images
docker-compose pull

# Rebuild custom images
./build.sh --no-cache

# Restart services
docker-compose up -d

# Verify health
docker-compose ps
```

## Development Workflow

### Local Development

For development with live code updates:

```bash
# Clone repository
git clone <repo-url>
cd ntn-simulation/docker

# Build development images
./build.sh --verbose

# Start with volume mounts
docker-compose up -d

# Code changes are reflected immediately (if using proper volume mounts)
```

### Testing Changes

```bash
# Run tests
./test.sh

# Manual testing
docker-compose exec handover-xapp python -m pytest tests/

# Interactive debugging
docker-compose exec handover-xapp python -i
```

### Building for Multiple Architectures

```bash
# Enable buildx
docker buildx create --name ntn-builder --use

# Build and push for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myregistry/ntn/handover-xapp:latest \
  -f docker/Dockerfile.handover-xapp \
  --push .
```

## Performance Tuning

### CPU Optimization

```yaml
environment:
  - OMP_NUM_THREADS=4  # For NumPy/OpenBLAS
  - OPENBLAS_NUM_THREADS=4
```

### Memory Optimization

1. Use slim base images (already done)
2. Multi-stage builds (already configured)
3. Minimal dependencies (optimize requirements.txt)

### Network Optimization

```yaml
networks:
  ntn-network:
    driver: bridge
    driver_opts:
      com.docker.network.driver.mtu: 1500
```

## Cleanup and Maintenance

### Remove Unused Resources

```bash
# Stop all services
docker-compose down

# Remove dangling images
docker image prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Full cleanup (be careful!)
docker system prune -a --volumes
```

### Disk Space Management

```bash
# Check Docker disk usage
docker system df

# Limit log file size (already configured in docker-compose.yml)
# Log rotation: max-size: 10m, max-file: 3
```

## API Endpoints

### E2 Termination (8082)

```
GET  /health                 - Health status
GET  /metrics                - Prometheus metrics
POST /e2/subscribe           - Subscribe to E2 events
POST /e2/control             - Send control commands
GET  /statistics             - Service statistics
```

### Handover xApp (8080)

```
GET  /health                 - Health status
GET  /metrics                - Prometheus metrics
POST /predict-handover       - Predict handover
GET  /ue/{ue_id}/handovers   - UE handover history
GET  /statistics             - Handover statistics
```

### Power Control xApp (8081)

```
GET  /health                 - Health status
GET  /metrics                - Prometheus metrics
POST /recommend-power        - Get power recommendation
GET  /ue/{ue_id}/power       - UE power history
GET  /statistics             - Power control statistics
```

## Support and Contribution

For issues, questions, or contributions:

1. Check logs: `docker-compose logs`
2. Review troubleshooting section above
3. Submit issues with docker version and logs

## License

See main project LICENSE file.

## References

- Docker Documentation: https://docs.docker.com
- Docker Compose: https://docs.docker.com/compose
- 3GPP E2 Standard: 3GPP TS 37.473
- NTN Specifications: 3GPP TR 38.811
