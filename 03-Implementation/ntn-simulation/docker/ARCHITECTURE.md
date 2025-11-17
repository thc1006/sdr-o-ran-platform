# NTN Docker Architecture

Comprehensive documentation of the Docker architecture for NTN xApps.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Docker Host Environment                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Docker Network: ntn-network               │  │
│  │                    Type: bridge (172.20.0.0/16)              │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                 │  │
│  │  │ ntn-handover-xapp│  │ ntn-power-xapp   │                 │  │
│  │  │ User: xapp:1000  │  │ User: xapp:1000  │                 │  │
│  │  │ Port: 8080       │  │ Port: 8081       │                 │  │
│  │  │ Memory: 2GB      │  │ Memory: 2GB      │                 │  │
│  │  │ CPU: 2           │  │ CPU: 2           │                 │  │
│  │  └────────┬─────────┘  └────────┬─────────┘                 │  │
│  │           │                     │                            │  │
│  │           └─────────┬───────────┘                            │  │
│  │                     │                                        │  │
│  │           ┌─────────▼──────────┐                             │  │
│  │           │ ntn-e2-termination │                             │  │
│  │           │ User: e2term:1000  │                             │  │
│  │           │ Port: 36421 (E2)   │                             │  │
│  │           │ Port: 8082 (HTTP)  │                             │  │
│  │           │ Memory: 2GB        │                             │  │
│  │           │ CPU: 2             │                             │  │
│  │           └─────────┬──────────┘                             │  │
│  │                     │                                        │  │
│  │           ┌─────────┴──────────┐                             │  │
│  │           │                    │                             │  │
│  │     ┌─────▼──────┐      ┌──────▼────────┐                   │  │
│  │     │  ntn-redis │      │ ntn-prometheus│                   │  │
│  │     │  Port: 6379│      │ Port: 9090    │                   │  │
│  │     │  Memory: 1G│      │ Memory: 1GB   │                   │  │
│  │     │  Volume:   │      │ Volume:       │                   │  │
│  │     │  redis_data│      │prometheus_data│                   │  │
│  │     └────────────┘      └───────────────┘                   │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                         Host Volumes                         │  │
│  │                                                               │  │
│  │  - ntn_logs: /var/lib/docker/volumes/ntn_logs/_data         │  │
│  │  - redis_data: /var/lib/docker/volumes/ntn_redis_data/_data │  │
│  │  - prometheus_data: /.../ntn_prometheus_data/_data          │  │
│  │  - ntn-simulation code: /path/to/ntn-simulation mounted at  │  │
│  │    /app in each xApp container                              │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Container Details

### E2 Termination Service

**Image**: `ntn/e2-termination:1.0.0`

**Dockerfile**: `Dockerfile.e2-termination`

**Characteristics**:
- Base: `python:3.12-slim`
- User: Non-root (e2term:1000)
- Ports: 36421 (E2 protocol), 8082 (HTTP)
- Entry Point: `python -m e2_ntn_extension.ntn_e2_bridge`

**Responsibilities**:
- E2SM-NTN message serialization/deserialization
- RIC subscription management
- Metric collection and reporting
- E2 protocol interface implementation

**Dependencies**:
- asn1tools (ASN.1 encoding/decoding)
- redis (state management)
- prometheus-client (metrics)
- All dependencies from requirements.txt

### Handover xApp

**Image**: `ntn/handover-xapp:1.0.0`

**Dockerfile**: `Dockerfile.handover-xapp`

**Characteristics**:
- Base: `python:3.12-slim`
- User: Non-root (xapp:1000)
- Port: 8080 (HTTP API)
- Entry Point: `python -m xapps.ntn_handover_xapp`

**Responsibilities**:
- Monitor time-to-handover metrics
- Predict next satellite
- Trigger handover commands
- Track handover success rates

**Dependencies**:
- redis (state management)
- All dependencies from requirements.txt

### Power Control xApp

**Image**: `ntn/power-xapp:1.0.0`

**Dockerfile**: `Dockerfile.power-xapp`

**Characteristics**:
- Base: `python:3.12-slim`
- User: Non-root (xapp:1000)
- Port: 8081 (HTTP API)
- Entry Point: `python -m xapps.ntn_power_control_xapp`

**Responsibilities**:
- Monitor link budget metrics
- Recommend power adjustments
- Mitigate rain fade effects
- Optimize power efficiency vs. quality

**Dependencies**:
- redis (state management)
- All dependencies from requirements.txt

### Redis Service

**Image**: `redis:7-alpine`

**Port**: 6379

**Characteristics**:
- Minimal footprint (alpine base)
- Persistent storage (AOF)
- Volume: redis_data

**Responsibilities**:
- Distributed state management
- Caching for metrics
- Session storage
- Inter-service communication

### Prometheus Service

**Image**: `prom/prometheus:latest`

**Port**: 9090

**Configuration**: `prometheus.yml`

**Characteristics**:
- Metrics scraping
- 15-day retention (default)
- Web UI

**Targets**:
- E2 Termination (8082/metrics)
- Handover xApp (8080/metrics)
- Power Control xApp (8081/metrics)

## Multi-Stage Build Strategy

### Stage 1: Builder

```dockerfile
FROM python:3.12-slim as builder

# System dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    pkg-config \
    libopenblas-dev

# Create virtual environment
RUN python -m venv /opt/venv

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
```

**Purpose**:
- Compile dependencies from source (if needed)
- Create optimized virtual environment
- Reduce final image size by excluding build tools

**Size Impact**: ~2GB (builder image, discarded)

### Stage 2: Runtime

```dockerfile
FROM python:3.12-slim

# Runtime dependencies only
RUN apt-get install -y libopenblas0 libgomp1

# Copy pre-built venv
COPY --from=builder /opt/venv /opt/venv

# Non-root user
RUN useradd -m -u 1000 xapp

# Application code
COPY . /app
```

**Purpose**:
- Minimal runtime environment
- Only necessary system libraries
- Non-root execution

**Size Impact**: ~850MB per image (optimized from potential 1.5GB+)

## Networking Architecture

### Docker Network: ntn-network

**Type**: Bridge

**Subnet**: 172.20.0.0/16

**Services on Network**:
- ntn-handover-xapp (172.20.0.x)
- ntn-power-xapp (172.20.0.x)
- ntn-e2-termination (172.20.0.x)
- ntn-redis (172.20.0.x)
- ntn-prometheus (172.20.0.x)

**Communication**:
- All containers can reach each other by service name (DNS)
- xApps communicate with E2 Termination over port 36421
- All services access Redis on port 6379
- Prometheus scrapes metrics endpoints

**Port Mapping**:

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| E2 Termination | 36421 | 36421 | E2 (TCP) |
| E2 Termination | 8082 | 8082 | HTTP |
| Handover xApp | 8080 | 8080 | HTTP |
| Power xApp | 8081 | 8081 | HTTP |
| Redis | 6379 | 6379 | TCP |
| Prometheus | 9090 | 9090 | HTTP |

## Volume Architecture

### Volume Types

**Named Volumes** (Persistent):
```yaml
redis_data:
  driver: local
  # Location: /var/lib/docker/volumes/ntn_redis_data/_data

prometheus_data:
  driver: local
  # Location: /var/lib/docker/volumes/ntn_prometheus_data/_data

ntn_logs:
  driver: local
  # Location: /var/lib/docker/volumes/ntn_logs/_data
```

**Bind Mounts** (Development):
```yaml
volumes:
  - ../:/app  # Host project directory mounted at /app
```

### Data Persistence

**Redis Persistence**:
```bash
redis-server --appendonly yes
# Saves to appendonly.aof in redis_data volume
```

**Prometheus Persistence**:
```
# TSDB data saved in prometheus_data volume
# Format: TSDB blocks (each ~2 hours)
```

**Application Logs**:
```
# Mounted at /var/log/ntn in containers
# Mapped to ntn_logs volume
# Centralized log storage
```

## Security Architecture

### Non-Root User Execution

Each container runs as non-root user:
- **E2 Termination**: e2term:1000
- **xApps**: xapp:1000

**Benefits**:
- Prevents privilege escalation
- Limits damage if container is compromised
- Compliance with security best practices

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

**Prevents**:
- One container consuming all resources
- Denial of service within host
- Resource exhaustion attacks

### Network Isolation

- Custom bridge network (ntn-network)
- Containers isolated from default bridge
- External services must be explicitly exposed via port mappings
- No inter-network communication by default

### Log Rotation

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Prevents**:
- Logs consuming all disk space
- Unbounded disk usage growth

## Health Check Architecture

**Config Pattern**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

**States**:
- Starting: Waiting for start_period
- Healthy: Health check passed
- Unhealthy: Repeated failures
- None: No health check defined

**Docker Compose Behavior**:
```yaml
depends_on:
  redis:
    condition: service_healthy  # Wait for health check
```

## Logging Architecture

### Log Drivers

**Container Logs** (json-file):
```bash
docker-compose logs [service]
docker-compose logs -f --tail=100
```

**Log Storage**:
- JSON format with metadata
- Stored in `/var/lib/docker/containers/`
- Rotation: max 10MB, keep 3 files

**Log Aggregation** (optional):
- Central log stack (ELK, Splunk)
- Mount volume to /var/log/ntn
- Ship logs to central location

## Environment Configuration

### Environment Files

**`.env.example`**: Template for environment variables

**`.env`**: Local overrides (gitignored)

**`docker-compose.yml`**: Default values

**Priority**: `.env` > `docker-compose.yml` defaults

### Environment Variables by Service

**All Services**:
```
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
LOG_LEVEL=INFO
```

**xApps**:
```
REDIS_HOST=redis
REDIS_PORT=6379
E2_TERMINATION_HOST=e2-termination
E2_TERMINATION_PORT=36421
```

**E2 Termination**:
```
REDIS_HOST=redis
REDIS_PORT=6379
E2_TERMINATION_PORT=36421
```

## Scaling Architecture

### Horizontal Scaling

**Current**:
- 1 E2 Termination (stateless)
- 1 Handover xApp (stateless)
- 1 Power Control xApp (stateless)
- 1 Redis (shared state)
- 1 Prometheus (shared metrics)

**Future Scaling**:
```yaml
services:
  handover-xapp-1:
    ...
  handover-xapp-2:
    ...
  # Load balancer in front
  load-balancer:
    image: haproxy:latest
    ports:
      - "8080:8080"
```

### Vertical Scaling

Increase resource limits:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Was 2
      memory: 4G       # Was 2G
```

## Deployment Patterns

### Development

```bash
docker-compose up
# Containers run in foreground, code changes reflected
```

### Testing

```bash
./test.sh
# Run full test suite
```

### Production

```bash
docker-compose up -d
# Background execution
# Auto-restart enabled
# Health checks monitoring
```

### CI/CD Integration

```bash
# Build
docker build -f Dockerfile.handover-xapp -t my-registry/ntn/handover-xapp:1.0.0 .

# Push
docker push my-registry/ntn/handover-xapp:1.0.0

# Deploy
docker pull my-registry/ntn/handover-xapp:1.0.0
docker-compose up -d
```

## Monitoring and Observability

### Metrics Collection

**Prometheus Scraping**:
- E2 Termination: http://e2-termination:8082/metrics (15s interval)
- Handover xApp: http://handover-xapp:8080/metrics (15s interval)
- Power xApp: http://power-xapp:8081/metrics (15s interval)

**Key Metrics**:
- Request count
- Response time
- Error rate
- Resource usage
- Business metrics (handovers, power adjustments)

### Health Checks

- Each service exposes /health endpoint
- Docker health checks verify responsiveness
- Prometheus monitors health status
- Alerting on unhealthy services (optional)

### Log Aggregation

- Centralized in `/var/log/ntn` volume
- JSON format with timestamps
- Searchable and analyzable
- Can be shipped to central logging

## Update and Rollback Strategy

### Blue-Green Deployment

```bash
# Current (blue)
docker-compose up -d

# New version (green)
docker-compose -f docker-compose-v2.yml up -d

# Switch traffic (update port mappings)
# Rollback: restart original version
```

### Rolling Update

```bash
# Update one service at a time
docker-compose up -d handover-xapp
# Test
docker-compose up -d power-xapp
# Test
docker-compose up -d e2-termination
# Test
```

## Disaster Recovery

### Backup

```bash
# Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp ntn-redis:/data/dump.rdb backup.rdb

# Prometheus data
docker run --rm -v ntn_prometheus_data:/data \
  -v /backup:/backup alpine \
  tar czf /backup/prometheus.tar.gz -C /data .
```

### Recovery

```bash
# Restore Redis
docker cp backup.rdb ntn-redis:/data/dump.rdb

# Restart to load
docker-compose restart redis
```

## References

- 3GPP TS 37.473 - E2 Application Protocol (E2AP)
- 3GPP TR 38.811 - Non-Terrestrial Networks
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- Compose File Reference: https://docs.docker.com/compose/compose-file/
