# NTN Docker Troubleshooting Guide

Comprehensive guide for diagnosing and fixing common issues in the NTN Docker deployment.

## Table of Contents

1. [Build Issues](#build-issues)
2. [Service Startup Issues](#service-startup-issues)
3. [Connectivity Issues](#connectivity-issues)
4. [Performance Issues](#performance-issues)
5. [Data and Storage Issues](#data-and-storage-issues)
6. [Logging and Debugging](#logging-and-debugging)
7. [Network Issues](#network-issues)

## Build Issues

### Issue: Docker image build fails

**Symptoms:**
- `docker build` command fails with errors
- "Step X/Y failed"

**Diagnosis:**
```bash
# View detailed build output
docker build -f Dockerfile.handover-xapp -t test:latest .. --progress=plain

# Check for specific error messages
docker logs <container_id>

# Verify requirements file
cat requirements.txt
```

**Solutions:**

1. **Out of disk space:**
```bash
# Check disk usage
df -h

# Free up space
docker system prune -a
docker volume prune

# Increase disk space if needed
```

2. **Network issues (can't download packages):**
```bash
# Test internet connectivity
curl -I https://pypi.org

# Check DNS
nslookup pypi.org

# Try with explicit DNS
docker build --build-arg="http_proxy=http://proxy:8080" \
  -f Dockerfile.handover-xapp -t test:latest ..
```

3. **Base image not found:**
```bash
# Pull base images manually
docker pull python:3.12-slim
docker pull redis:7-alpine
docker pull prom/prometheus:latest

# Verify images exist
docker images | grep -E "python|redis|prometheus"
```

4. **Python package conflicts:**
```bash
# Update pip and setuptools
RUN pip install --upgrade pip setuptools wheel

# Use specific versions in requirements.txt
# Instead of: tensorflow>=2.15.0
# Use: tensorflow==2.15.1

# Try building with --no-cache
./build.sh --no-cache
```

### Issue: Build takes too long

**Solutions:**
1. Use BuildKit for faster builds:
```bash
export DOCKER_BUILDKIT=1
docker build -f Dockerfile.handover-xapp .
```

2. Build images in parallel:
```bash
./build.sh &
# In another terminal
docker build -f Dockerfile.power-xapp . &
```

3. Use pre-built wheels:
```bash
# Download wheels and copy to Docker build context
# Update Dockerfile to COPY wheels and use --find-links
```

## Service Startup Issues

### Issue: Container exits immediately

**Symptoms:**
- `docker-compose ps` shows "Exited (1)"
- Container runs but stops after a few seconds

**Diagnosis:**
```bash
# Check exit code
docker inspect ntn-handover-xapp | grep ExitCode

# View complete logs
docker-compose logs --tail=100 handover-xapp

# Common exit codes:
# 0 = success
# 1 = general error
# 126 = permission denied
# 127 = command not found
```

**Solutions:**

1. **Module not found errors:**
```bash
# Verify PYTHONPATH
docker-compose exec handover-xapp python -c "import sys; print(sys.path)"

# Check if modules are installed
docker-compose exec handover-xapp python -c "import e2sm_ntn"

# Verify directory structure
docker-compose exec handover-xapp ls -la /app
```

2. **Permission denied:**
```bash
# Check file permissions in Dockerfile
RUN chmod +x /app/entrypoint.sh

# Verify non-root user can access files
docker-compose exec handover-xapp whoami  # Should be 'xapp'
```

3. **Port already in use:**
```bash
# Find process using port
lsof -i :8080

# Kill process
sudo fuser -k 8080/tcp

# Or change port in docker-compose.yml
# From: "8080:8080"
# To: "9080:8080"
```

### Issue: Service becomes unhealthy

**Symptoms:**
- `docker-compose ps` shows "Unhealthy"
- Health checks are failing

**Diagnosis:**
```bash
# Check health check details
docker inspect ntn-handover-xapp | grep -A 10 "State"

# View health check history
docker inspect ntn-handover-xapp | grep -A 20 "HealthCheck"

# Test health endpoint manually
curl -v http://localhost:8080/health
```

**Solutions:**

1. **Health check timeout:**
```yaml
# Increase timeout in docker-compose.yml
healthcheck:
  timeout: 15s  # Increase from 10s
```

2. **Service not responding:**
```bash
# Check if service is listening
docker-compose exec handover-xapp ss -tlnp

# Test localhost connectivity
docker-compose exec handover-xapp curl localhost:8080/health

# Check for errors in logs
docker-compose logs handover-xapp | grep -i error
```

3. **Health endpoint missing:**
```bash
# Implement health check endpoint in your application
# Example in Python Flask:
from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200
```

## Connectivity Issues

### Issue: Containers can't communicate with each other

**Symptoms:**
- "Connection refused" errors
- "Name resolution failed"
- Containers can't reach each other by hostname

**Diagnosis:**
```bash
# Test DNS resolution from container
docker-compose exec handover-xapp nslookup redis
docker-compose exec handover-xapp nslookup e2-termination

# Test connectivity with ping
docker-compose exec handover-xapp ping redis

# Test port connectivity with nc
docker-compose exec handover-xapp nc -zv redis 6379

# Check network configuration
docker network inspect ntn-network

# View running containers on network
docker network inspect ntn-network | grep -A 20 '"Containers"'
```

**Solutions:**

1. **Service name not resolving:**
```bash
# Verify service is running
docker-compose ps

# Check if service is on correct network
docker inspect ntn-handover-xapp | grep -A 10 "Networks"

# Restart services to force network re-join
docker-compose restart
```

2. **Port not exposed correctly:**
```yaml
# docker-compose.yml - check port mapping
redis:
  ports:
    - "6379:6379"  # External:Internal port

# Or use container_name and expose port internally
handover-xapp:
  environment:
    - REDIS_HOST=redis
    - REDIS_PORT=6379
```

3. **Firewall blocking:**
```bash
# Check if firewall is blocking
sudo ufw status

# Allow Docker network communication
sudo ufw allow 172.17.0.0/16

# Or disable firewall for testing (not recommended for production)
sudo systemctl stop ufw
```

### Issue: Redis connection fails

**Symptoms:**
- "Cannot connect to Redis"
- "Connection timeout"

**Diagnosis:**
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis directly
docker-compose exec redis redis-cli PING

# Test from another container
docker-compose exec handover-xapp redis-cli -h redis PING

# Check Redis logs
docker-compose logs redis
```

**Solutions:**

1. **Redis not started:**
```bash
# Restart Redis
docker-compose restart redis

# Check if Redis is listening
docker-compose exec redis ss -tlnp | grep 6379
```

2. **Wrong connection parameters:**
```bash
# Verify environment variables
docker-compose exec handover-xapp env | grep REDIS

# Check actual connection
docker-compose exec handover-xapp python << EOF
import redis
try:
    r = redis.Redis(host='redis', port=6379)
    print(r.ping())
except Exception as e:
    print(f"Error: {e}")
EOF
```

## Performance Issues

### Issue: High CPU usage

**Symptoms:**
- Container consuming excessive CPU
- System becomes slow
- `docker stats` shows >100% CPU

**Diagnosis:**
```bash
# Monitor resource usage
docker stats --no-stream

# Check which process is using CPU
docker-compose exec handover-xapp top -b -n 1

# Check for busy loops in logs
docker-compose logs --tail=100 handover-xapp | grep -i "loop\|spinning"
```

**Solutions:**

1. **Limit CPU usage:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
    reservations:
      cpus: '1'
```

2. **Optimize application:**
- Check for infinite loops
- Implement proper sleep intervals
- Use batch processing instead of continuous loops

### Issue: High memory usage

**Symptoms:**
- "Out of memory" errors
- Container killed suddenly
- Swap usage increasing

**Diagnosis:**
```bash
# Check memory usage
docker stats --no-stream | grep handover-xapp

# Monitor memory over time
watch 'docker stats --no-stream'

# Check memory limits
docker inspect ntn-handover-xapp | grep -i memory
```

**Solutions:**

1. **Set memory limits:**
```yaml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

2. **Optimize memory usage:**
- Use memory profilers
- Check for memory leaks
- Implement proper cleanup

3. **Reduce Python memory overhead:**
```dockerfile
# Use slim base image (already done)
# Compile Python with less memory overhead
# Use PyPy instead of CPython if compatible
```

## Data and Storage Issues

### Issue: Data not persisting

**Symptoms:**
- Redis data lost after restart
- Prometheus data reset
- Configuration changes not saved

**Diagnosis:**
```bash
# Check volume mounts
docker inspect ntn-redis | grep -A 5 "Mounts"

# Verify volumes exist
docker volume ls | grep ntn

# Check volume data
docker run --rm -v ntn_redis_data:/data -it alpine ls -la /data
```

**Solutions:**

1. **Enable persistence:**
```yaml
redis:
  volumes:
    - redis_data:/data

volumes:
  redis_data:
    driver: local
```

2. **Manual backup:**
```bash
# Backup Redis
docker-compose exec redis redis-cli BGSAVE

# Copy backup file
docker cp ntn-redis:/data/dump.rdb ./redis-backup.rdb
```

### Issue: Disk space filling up

**Symptoms:**
- Disk full errors
- Services failing to write logs
- Build failures due to space

**Diagnosis:**
```bash
# Check disk usage
df -h

# Docker system usage
docker system df

# Find large containers
docker ps -as --sort=size

# Find large images
docker images --sort=size
```

**Solutions:**

1. **Clean up logs:**
```bash
# Truncate container logs
docker exec -it <container> sh -c 'echo "" > /var/log/app.log'

# Or use log rotation (already configured)
# Verify in docker-compose.yml:
# logging:
#   options:
#     max-size: "10m"
#     max-file: "3"
```

2. **Remove unused resources:**
```bash
# Remove dangling images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Remove stopped containers
docker container prune -f

# Full cleanup
docker system prune -a
```

3. **Increase disk space:**
```bash
# Add more disk to VM or physical machine
# Or use external volumes
# See documentation on persistent storage options
```

## Logging and Debugging

### Issue: Can't see logs

**Symptoms:**
- Logs are empty
- Logs are truncated
- Can't find error messages

**Solutions:**

1. **View complete logs:**
```bash
# All logs
docker-compose logs

# Specific service
docker-compose logs handover-xapp

# With timestamps
docker-compose logs -t

# Follow live logs
docker-compose logs -f

# Last N lines
docker-compose logs --tail=1000

# Since specific time
docker-compose logs --since 2024-01-01 --until 2024-01-02
```

2. **Enable debug logging:**
```yaml
environment:
  - LOG_LEVEL=DEBUG

# In application:
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. **Redirect logs to file:**
```bash
docker-compose logs > logs.txt
docker-compose logs -f handover-xapp | tee logs.txt
```

### Issue: Application won't start due to missing imports

**Symptoms:**
- "ModuleNotFoundError" in logs
- "ImportError" exceptions

**Solutions:**

1. **Verify imports are available:**
```bash
# Check if module is installed
docker-compose exec handover-xapp python -c "import module_name"

# List installed packages
docker-compose exec handover-xapp pip list

# Show installed versions
docker-compose exec handover-xapp pip show module_name
```

2. **Install missing packages:**
```bash
# One-time installation
docker-compose exec handover-xapp pip install module_name

# Permanent: update Dockerfile
# RUN pip install module_name
# Then rebuild: docker-compose build --no-cache
```

### Issue: Debugging hanging processes

**Symptoms:**
- Container running but not responding
- Logs show no activity
- CPU usage at 0%

**Solutions:**

1. **Attach to running container:**
```bash
# Get container ID
docker-compose ps

# Attach to container
docker attach ntn-handover-xapp

# Ctrl+C to detach (doesn't kill container)
```

2. **Execute debugging commands:**
```bash
# Get process list
docker-compose exec handover-xapp ps aux

# Check for stuck processes
docker-compose exec handover-xapp ps aux | grep python

# Kill specific process
docker-compose exec handover-xapp kill -9 <PID>
```

3. **Use debugger:**
```bash
# Start Python debugger
docker-compose exec -it handover-xapp python -m pdb script.py

# Or use ipdb for better experience
docker-compose exec -it handover-xapp python -m ipdb script.py
```

## Network Issues

### Issue: Container can't reach external network

**Symptoms:**
- "Network unreachable"
- Can't download packages
- DNS resolution fails

**Diagnosis:**
```bash
# Test connectivity from container
docker-compose exec handover-xapp curl -I https://pypi.org

# Check DNS
docker-compose exec handover-xapp nslookup pypi.org

# Check routing
docker-compose exec handover-xapp ip route

# Check network interfaces
docker-compose exec handover-xapp ip addr
```

**Solutions:**

1. **Fix DNS:**
```bash
# Check docker DNS settings
cat /etc/docker/daemon.json

# Add custom DNS
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}

# Restart Docker
sudo systemctl restart docker
```

2. **Check firewall:**
```bash
# Disable firewall (for testing)
sudo systemctl stop ufw

# Or allow Docker traffic
sudo ufw allow from 172.17.0.0/16
```

3. **Use bridge network:**
```bash
# Already configured in docker-compose.yml
networks:
  ntn-network:
    driver: bridge
```

## Getting Help

If you can't resolve an issue:

1. **Collect debugging information:**
```bash
# Docker version
docker --version

# Docker compose version
docker-compose --version

# System info
uname -a
free -h
df -h

# Service status
docker-compose ps

# Logs
docker-compose logs > debug_logs.txt

# Docker events (run in another terminal)
docker events
```

2. **Create a minimal reproducible example**
3. **Check known issues** in project documentation
4. **Search Docker documentation**
5. **Post issue with debugging information above**

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "docker: command not found" | Docker not installed | Install Docker |
| "permission denied" | User not in docker group | `sudo usermod -aG docker $USER` |
| "Connection refused" | Service not running | `docker-compose up -d` |
| "Port already in use" | Port in use by another process | `lsof -i :port` and kill process |
| "No space left on device" | Disk full | `docker system prune -a` |
| "Out of memory" | Container memory limit exceeded | Increase memory limit |
| "ModuleNotFoundError" | Python module not installed | Add to requirements.txt |
| "Name or service not known" | DNS resolution failed | Check network connectivity |

## Performance Optimization Tips

1. Use `.dockerignore` to reduce build context (already configured)
2. Use multi-stage builds (already configured)
3. Cache pip packages in Docker volume
4. Use slim base images (already using python:3.12-slim)
5. Minimize layers in Dockerfile
6. Use BuildKit for faster builds (`DOCKER_BUILDKIT=1`)
7. Pin specific dependency versions
8. Regular cleanup of dangling images and containers
