# NTN Docker Testing Guide

Complete guide for testing Docker containers and services.

## Table of Contents

1. [Automated Testing](#automated-testing)
2. [Manual Testing](#manual-testing)
3. [Integration Testing](#integration-testing)
4. [Performance Testing](#performance-testing)
5. [Security Testing](#security-testing)

## Automated Testing

### Run Complete Test Suite

```bash
cd docker
./test.sh
```

This executes:
1. Prerequisite checks (Docker, docker-compose)
2. Image existence verification
3. Service startup
4. Service health checks
5. Network connectivity tests
6. Log analysis

### Expected Output

```
=== NTN Docker Compose Test Suite ===

Stage 1: Checking prerequisites...
✓ Docker is running
✓ docker-compose is installed
✓ Image ntn/e2-termination:latest exists
...

Stage 2: Starting docker-compose stack...
✓ Docker-compose stack started

Stage 3: Waiting for services to become healthy...
✓ redis is responding on port 6379
✓ prometheus is responding on port 9090
✓ e2-termination is responding on port 8082
✓ handover-xapp is responding on port 8080
✓ power-xapp is responding on port 8081

=== Test Summary ===
All tests passed!
```

## Manual Testing

### 1. Service Status

```bash
# Check all containers
docker-compose ps

# Expected: All containers "Up" with healthy status
# CONTAINER ID    IMAGE             STATUS
# <id>  ntn/e2-termination:latest     Up 5 seconds (healthy)
# <id>  ntn/handover-xapp:latest      Up 5 seconds (healthy)
# <id>  ntn/power-xapp:latest         Up 5 seconds (healthy)
# <id>  redis:7-alpine                Up 5 seconds (healthy)
# <id>  prom/prometheus:latest        Up 5 seconds (healthy)
```

### 2. Health Endpoint Testing

```bash
# Test all health endpoints
for port in 8080 8081 8082; do
    echo "Testing port $port..."
    curl -i http://localhost:$port/health
done

# Expected response:
# HTTP/1.1 200 OK
# Content-Type: application/json
# {
#   "status": "healthy",
#   "timestamp": "2024-01-01T00:00:00Z"
# }
```

### 3. Individual Service Testing

#### Test E2 Termination

```bash
# Health check
curl http://localhost:8082/health

# Metrics endpoint
curl http://localhost:8082/metrics

# Check logs
docker-compose logs e2-termination

# Test E2 protocol port
nc -zv localhost 36421
```

#### Test Handover xApp

```bash
# Health check
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics

# Logs
docker-compose logs handover-xapp

# Execute shell command
docker-compose exec handover-xapp python -c "print('Handover xApp running')"
```

#### Test Power Control xApp

```bash
# Health check
curl http://localhost:8081/health

# Metrics
curl http://localhost:8081/metrics

# Logs
docker-compose logs power-xapp

# Execute shell command
docker-compose exec power-xapp python -c "print('Power xApp running')"
```

#### Test Redis

```bash
# Connection test
redis-cli -h localhost ping

# Or from container
docker-compose exec redis redis-cli PING

# Check data
redis-cli -h localhost DBSIZE

# List all keys
redis-cli -h localhost KEYS '*'
```

#### Test Prometheus

```bash
# Web interface
curl http://localhost:9090

# Query API
curl "http://localhost:9090/api/v1/query?query=up"

# List targets
curl "http://localhost:9090/api/v1/targets"
```

## Integration Testing

### 1. Cross-Service Communication

```bash
# Test xApp can reach E2 Termination
docker-compose exec handover-xapp python << EOF
import socket
import sys

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('e2-termination', 36421))
    s.close()
    print("✓ Handover xApp -> E2 Termination: OK")
except Exception as e:
    print(f"✗ Handover xApp -> E2 Termination: FAILED - {e}")
    sys.exit(1)
EOF

# Test xApp can reach Redis
docker-compose exec power-xapp python << EOF
import redis
try:
    r = redis.Redis(host='redis', port=6379, socket_connect_timeout=5)
    r.ping()
    print("✓ Power xApp -> Redis: OK")
except Exception as e:
    print(f"✗ Power xApp -> Redis: FAILED - {e}")
EOF

# Test E2 Termination can reach Redis
docker-compose exec e2-termination python << EOF
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('redis', 6379))
    s.close()
    print("✓ E2 Termination -> Redis: OK")
except Exception as e:
    print(f"✗ E2 Termination -> Redis: FAILED - {e}")
EOF
```

### 2. Data Flow Testing

```bash
# Store data in Redis from one xApp
docker-compose exec handover-xapp python << EOF
import redis
r = redis.Redis(host='redis', port=6379)
r.set('test_key', 'test_value')
print("Data stored")
EOF

# Retrieve data from another xApp
docker-compose exec power-xapp python << EOF
import redis
r = redis.Redis(host='redis', port=6379)
value = r.get('test_key')
if value == b'test_value':
    print("✓ Data flow test: OK")
else:
    print("✗ Data flow test: FAILED")
EOF
```

### 3. End-to-End Flow Testing

```bash
# Simulate complete workflow
docker-compose exec handover-xapp python << EOF
import redis
import json
import socket

# Test 1: Redis connectivity
try:
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print("✓ Step 1: Redis connection - OK")
except Exception as e:
    print(f"✗ Step 1: {e}")

# Test 2: E2 Termination connectivity
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('e2-termination', 36421))
    s.close()
    print("✓ Step 2: E2 Termination connection - OK")
except Exception as e:
    print(f"✗ Step 2: {e}")

# Test 3: Data storage
try:
    r.set('workflow_test', json.dumps({'status': 'active'}))
    print("✓ Step 3: Data storage - OK")
except Exception as e:
    print(f"✗ Step 3: {e}")

# Test 4: Data retrieval
try:
    data = r.get('workflow_test')
    if data:
        print("✓ Step 4: Data retrieval - OK")
    else:
        print("✗ Step 4: Data not found")
except Exception as e:
    print(f"✗ Step 4: {e}")

print("\n✓ End-to-end flow test: PASSED")
EOF
```

## Performance Testing

### 1. Container Resource Usage

```bash
# Monitor resource usage
docker stats --no-stream

# Expected output:
# CONTAINER         CPU %    MEM USAGE / LIMIT
# ntn-handover-xapp  0.5%     250MB / 2GB
# ntn-power-xapp     0.3%     200MB / 2GB
# ntn-e2-termination 0.2%     180MB / 2GB
# ntn-redis          0.1%     50MB / 1GB
# ntn-prometheus     0.5%     100MB / 1GB
```

### 2. Response Time Testing

```bash
# Test health endpoint response time
time curl http://localhost:8080/health

# Bulk request test
for i in {1..100}; do
    curl -s http://localhost:8080/health > /dev/null
done
echo "100 requests completed"

# Using Apache Bench (if installed)
ab -n 100 -c 10 http://localhost:8080/health/

# Expected: < 100ms response time
```

### 3. Network Performance

```bash
# Measure bandwidth between containers
docker-compose exec handover-xapp bash << EOF
# Install iperf3 or use dd
apt-get update && apt-get install -y iperf3
# Start server in e2-termination
# Client: iperf3 -c e2-termination
EOF
```

### 4. Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 20 http://localhost:8080/health

# Using curl in loop
#!/bin/bash
START=$(date +%s)
for i in {1..100}; do
    curl -s http://localhost:8080/health > /dev/null &
done
wait
END=$(date +%s)
DURATION=$((END - START))
echo "100 concurrent requests completed in ${DURATION}s"

# Using GNU parallel (if installed)
seq 1 100 | parallel -j 20 "curl -s http://localhost:8080/health > /dev/null"
```

## Security Testing

### 1. Container Security

```bash
# Check if running as root
docker-compose exec handover-xapp whoami
# Expected: xapp (not root)

# Verify non-root user
docker-compose exec handover-xapp id
# Expected: uid=1000(xapp) gid=1000(xapp) groups=1000(xapp)

# Check if running read-only (if configured)
docker inspect ntn-handover-xapp | grep -i "readonly"
```

### 2. Network Security

```bash
# Check exposed ports
docker inspect ntn-handover-xapp | grep -A 5 "ExposedPorts"

# Verify network isolation
docker network inspect ntn-network

# Test DNS resolution
docker-compose exec handover-xapp nslookup localhost
docker-compose exec handover-xapp nslookup external-host  # Should fail (if isolated)
```

### 3. Image Security

```bash
# Scan for vulnerabilities (if using trivy)
trivy image ntn/e2-termination:latest

# Check image layers
docker history ntn/e2-termination:latest

# Check for secrets in image
docker save ntn/e2-termination | tar x -O | grep -i "password\|secret\|key"
```

### 4. Environment Variable Security

```bash
# Check for exposed secrets
docker-compose exec handover-xapp env | grep -i "password\|token\|key\|secret"

# Verify sensitive data not in logs
docker-compose logs | grep -i "password\|token\|key\|secret"
```

## Test Scenarios

### Scenario 1: Service Restart

```bash
# Stop a service
docker-compose stop handover-xapp

# Verify it's stopped
docker-compose ps | grep handover-xapp
# Expected: Exited

# Restart
docker-compose start handover-xapp

# Verify it's back
docker-compose ps | grep handover-xapp
# Expected: Up

# Test functionality
curl http://localhost:8080/health
# Expected: 200 OK
```

### Scenario 2: Data Persistence

```bash
# Store data
docker-compose exec redis redis-cli SET test_key test_value

# Stop Redis
docker-compose stop redis

# Start Redis
docker-compose start redis

# Verify data persists
docker-compose exec redis redis-cli GET test_key
# Expected: test_value
```

### Scenario 3: Network Isolation

```bash
# Try to access from outside Docker network
curl http://internal-service:8080/health
# Expected: Connection refused

# Access from Docker container
docker-compose exec handover-xapp curl http://localhost:8080/health
# Expected: 200 OK
```

### Scenario 4: Resource Limits

```bash
# Monitor during load
docker stats --no-stream

# Run stress test
docker-compose exec handover-xapp python << EOF
# Create memory/CPU intensive task
data = []
for i in range(1000000):
    data.append([j for j in range(1000)])
EOF

# Verify limits are enforced
docker stats --no-stream
# Memory should not exceed limit
```

## Test Results Logging

```bash
# Save test results
./test.sh > test_results.txt 2>&1

# Review results
cat test_results.txt

# Compare with previous run
diff test_results_v1.txt test_results_v2.txt

# Archive results
tar czf test_results_$(date +%Y%m%d).tar.gz test_results.txt
```

## Continuous Testing

Create a cron job for regular testing:

```bash
# Add to crontab
crontab -e

# Add line (run tests daily at 2 AM)
0 2 * * * cd /path/to/docker && ./test.sh >> test_results.log 2>&1

# Monitor results
tail -f test_results.log
```

## Reporting Test Results

Template for test report:

```markdown
# Docker Testing Report - [Date]

## Test Environment
- Docker Version: $(docker --version)
- Docker Compose: $(docker-compose --version)
- Host OS: $(uname -a)
- Available Memory: $(free -h)
- Available Disk: $(df -h)

## Test Results Summary
- Automated Tests: PASSED / FAILED
- Manual Tests: PASSED / FAILED
- Integration Tests: PASSED / FAILED
- Performance Tests: PASSED / FAILED
- Security Tests: PASSED / FAILED

## Detailed Results
### Service Status
- E2 Termination: HEALTHY/UNHEALTHY
- Handover xApp: HEALTHY/UNHEALTHY
- Power Control xApp: HEALTHY/UNHEALTHY
- Redis: HEALTHY/UNHEALTHY
- Prometheus: HEALTHY/UNHEALTHY

### Performance Metrics
- Avg Response Time: Xms
- Max Memory Usage: XGB
- Avg CPU Usage: X%

### Issues Found
- Issue 1: Description, Severity: LOW/MEDIUM/HIGH
- Issue 2: ...

## Recommendations
- Recommendation 1
- Recommendation 2
- ...

## Sign-off
- Tested By: [Name]
- Date: [Date]
- Approved By: [Name]
```

## Troubleshooting Tests

If tests fail:

1. Check logs: `docker-compose logs`
2. Check status: `docker-compose ps`
3. Verify ports: `netstat -tlnp | grep LISTEN`
4. Check resources: `docker stats`
5. Review troubleshooting guide: `TROUBLESHOOTING.md`
