# NTN Docker Quick Reference

Fast command reference for common Docker operations.

## One-Line Setup

```bash
cd docker && ./build.sh && docker-compose up -d && ./test.sh
```

## Service Management

```bash
# Start services
./run.sh start
docker-compose up -d
make start

# Stop services
./run.sh stop
docker-compose stop
make stop

# Restart services
./run.sh restart
docker-compose restart
make restart

# Show status
docker-compose ps
make ps

# Remove containers
docker-compose down
make down
```

## Building Images

```bash
# Build all
./build.sh
make build

# Build specific
docker build -f Dockerfile.e2-termination -t ntn/e2-termination ..
make build-e2

# Verbose output
./build.sh --verbose
make build-verbose

# Without cache
./build.sh --no-cache
make build-nocache

# Push to registry
./build.sh --push --registry my.registry.com
make build-push DOCKER_REGISTRY=my.registry.com
```

## Logging

```bash
# All logs
docker-compose logs
make logs

# Follow logs
docker-compose logs -f
docker-compose logs -f handover-xapp

# Last N lines
docker-compose logs --tail=100

# Timestamps
docker-compose logs -t

# Search logs
docker-compose logs | grep "ERROR"
```

## Testing

```bash
# Run all tests
./test.sh
make test

# Manual health checks
curl http://localhost:8080/health  # Handover
curl http://localhost:8081/health  # Power
curl http://localhost:8082/health  # E2
curl http://localhost:6379          # Redis

# Test connectivity
docker-compose exec handover-xapp ping redis
docker-compose exec redis redis-cli PING
```

## Shell Access

```bash
# Interactive shell
docker-compose exec handover-xapp bash
./run.sh shell
./run.sh shell power-xapp

# One-off command
docker-compose exec handover-xapp python -c "print('Hello')"
docker-compose exec handover-xapp ls -la /app

# Run script
docker-compose exec handover-xapp python script.py
```

## Resource Monitoring

```bash
# Real-time stats
docker stats
docker stats --no-stream
make stats

# Service status with size
docker-compose ps -a -s

# Disk usage
docker system df

# Container details
docker inspect ntn-handover-xapp
```

## Cleaning Up

```bash
# Remove containers
docker-compose down
make down

# Remove with volumes
docker-compose down -v
make clean

# Remove images
docker rmi ntn/e2-termination ntn/handover-xapp ntn/power-xapp

# Remove dangling images
docker image prune -f

# Remove unused resources
docker system prune -a

# Full cleanup
docker-compose down -v
docker system prune -a --volumes
```

## Debugging

```bash
# View specific logs
docker-compose logs e2-termination
docker-compose logs --tail=50 power-xapp

# List processes in container
docker-compose exec handover-xapp ps aux

# Check environment
docker-compose exec handover-xapp env

# Network diagnostics
docker-compose exec handover-xapp nslookup redis
docker-compose exec handover-xapp nc -zv redis 6379

# System info
docker-compose exec handover-xapp uname -a
docker-compose exec handover-xapp free -h
docker-compose exec handover-xapp df -h
```

## Accessing Services

| Service | URL | Port |
|---------|-----|------|
| Handover xApp | http://localhost:8080 | 8080 |
| Power Control xApp | http://localhost:8081 | 8081 |
| E2 Termination HTTP | http://localhost:8082 | 8082 |
| E2 Protocol | 127.0.0.1:36421 | 36421 |
| Redis | redis://localhost:6379 | 6379 |
| Prometheus | http://localhost:9090 | 9090 |

## Metrics Endpoints

```bash
# Handover xApp metrics
curl http://localhost:8080/metrics

# Power Control xApp metrics
curl http://localhost:8081/metrics

# E2 Termination metrics
curl http://localhost:8082/metrics

# Health checks
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
```

## Environment Configuration

```bash
# Copy example config
cp .env.example .env

# Edit configuration
vim .env

# View current configuration
cat .env
```

## Docker Compose Commands

```bash
# Build
docker-compose build

# Build specific
docker-compose build handover-xapp

# Build without cache
docker-compose build --no-cache

# Start
docker-compose up

# Start in background
docker-compose up -d

# Stop
docker-compose stop

# Start existing
docker-compose start

# Restart
docker-compose restart

# Remove
docker-compose down

# View logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Status
docker-compose ps

# Execute command
docker-compose exec <service> <command>

# Validate config
docker-compose config

# List services
docker-compose services
```

## Useful Docker Commands

```bash
# List images
docker images
docker images | grep ntn

# List containers
docker ps
docker ps -a

# Inspect container
docker inspect <name>

# View logs
docker logs <container>

# Follow logs
docker logs -f <container>

# Execute command
docker exec <container> <command>

# Interactive shell
docker exec -it <container> bash

# Get container ID
docker ps | grep <name> | awk '{print $1}'

# Stop container
docker stop <container>

# Kill container
docker kill <container>

# Remove container
docker rm <container>

# Remove image
docker rmi <image>

# Show stats
docker stats <container>

# Show events
docker events

# Prune resources
docker system prune
```

## Makefile Targets

```bash
make help              # Show all targets
make build            # Build images
make start            # Start services
make stop             # Stop services
make restart          # Restart services
make down             # Stop and remove
make logs             # View logs
make ps               # Show status
make health           # Check health
make stats            # Show resource usage
make test             # Run tests
make clean            # Full cleanup
make dev-build        # Build for development
make dev-up           # Start for development
make dev-shell        # Open dev shell
```

## Bash Script Shortcuts

```bash
# Run script
./run.sh <command>

./run.sh start         # Start services
./run.sh stop          # Stop services
./run.sh restart       # Restart services
./run.sh down          # Stop and remove
./run.sh logs          # View logs
./run.sh logs handover-xapp  # Specific service
./run.sh ps            # Status
./run.sh shell         # Open shell
./run.sh shell power-xapp    # Specific service
./run.sh health        # Health check
./run.sh stats         # Resource usage
./run.sh test          # Run tests
./run.sh clean         # Full cleanup
./run.sh build         # Build images
```

## Prometheus Queries

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

## Common Tasks

### Restart a Service
```bash
docker-compose restart handover-xapp
# or
./run.sh restart
# or
make restart
```

### Check Logs for Errors
```bash
docker-compose logs | grep ERROR
# or
docker-compose logs e2-termination | grep ERROR
```

### Clear Redis Data
```bash
docker-compose exec redis redis-cli FLUSHDB
```

### Backup Redis
```bash
docker-compose exec redis redis-cli BGSAVE
docker cp ntn-redis:/data/dump.rdb ./redis-backup.rdb
```

### Monitor Resource Usage
```bash
watch 'docker stats --no-stream'
# or
docker stats --no-stream
# or
make stats
```

### Check Network Connectivity
```bash
docker-compose exec handover-xapp ping redis
docker-compose exec handover-xapp nc -zv redis 6379
```

### Force Rebuild
```bash
docker-compose down -v
./build.sh --no-cache
docker-compose up -d
./test.sh
```

## Troubleshooting Fast Track

```bash
# Service won't start?
docker-compose logs <service>

# Can't connect?
docker-compose exec <source> ping <target>

# Port already in use?
lsof -i :8080

# No space?
docker system df

# Slow?
docker stats

# Wrong behavior?
docker-compose logs --tail=100 | tail -50
```

## Pro Tips

1. Use `docker-compose up -d` for background operation
2. Use `docker-compose logs -f` to monitor live
3. Use `docker inspect` to debug configuration
4. Use volumes for persistent data
5. Use environment files (.env) for configuration
6. Use `.dockerignore` to reduce context size
7. Use multi-stage builds for smaller images
8. Use resource limits to prevent runaway containers
9. Use health checks for reliability
10. Regular cleanup to save disk space
