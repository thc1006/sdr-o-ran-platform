# SDR-O-RAN Platform - Deployment Checklist

## Stage 1 Completion Checklist

### Dependencies
- [x] Virtual environment created
- [x] All pip packages installed
- [x] Dependencies verified

### Security (TLS)
- [ ] Certificates generated (CA, server, client)
- [ ] Server updated with TLS support
- [ ] Client updated with TLS support
- [ ] TLS connection tested

### Testing
- [x] gRPC connection test created
- [x] Infrastructure tests created
- [ ] Test coverage >= 40%
- [ ] All tests passing

### Integration
- [x] gRPC services implemented
- [x] Health check script created
- [x] Docker compose validated

### Documentation
- [x] Integration test guide created
- [x] Deployment checklist completed
- [ ] Known issues documented

## Deployment Steps

### 1. Pre-deployment Checks

Run health check to verify system readiness:
```bash
cd /home/gnb/thc1006/sdr-o-ran-platform
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

Expected output:
- Virtual environment exists
- All core dependencies installed
- gRPC stubs generated
- Ports available (50051, 8000, 5555, etc.)

### 2. Run Integration Tests

Execute the full integration test suite:
```bash
chmod +x scripts/run_integration_tests.sh
./scripts/run_integration_tests.sh
```

Expected results:
- gRPC stubs test PASSED
- Infrastructure tests PASSED
- All imports successful

### 3. Deploy Services

Deploy the platform using Docker Compose:
```bash
docker-compose up -d
```

This will start:
- **leo-simulator** (port 5555) - LEO NTN Simulator with GPU
- **sdr-gateway** (ports 8000, 50051) - FastAPI + gRPC gateway
- **drl-trainer** (port 6006) - DRL Trainer with GPU
- **flexric** (ports 36421, 36422) - FlexRIC nearRT-RIC
- **mcp-gateway** (port 3000) - Model Context Protocol Gateway

### 4. Verify Deployment

Check service status:
```bash
docker-compose ps
```

Expected: All services should be "Up" and healthy.

Check service logs:
```bash
docker-compose logs -f
```

Look for:
- No errors in startup
- Services listening on expected ports
- Health checks passing

### 5. Test Running Services

Test gRPC server connection:
```bash
cd 03-Implementation/integration/sdr-oran-connector
source /home/gnb/thc1006/sdr-o-ran-platform/venv/bin/activate
python3 test_grpc_connection.py
```

Test FastAPI health endpoint:
```bash
curl http://localhost:8000/healthz
```

Expected: `{"status":"healthy"}`

### 6. Monitor Services

Monitor all services:
```bash
./scripts/monitor.sh
```

Or monitor specific service:
```bash
docker-compose logs -f sdr-gateway
```

### 7. Rollback (if needed)

If deployment fails or issues are detected:
```bash
docker-compose down
```

Review logs:
```bash
docker-compose logs > deployment-failure.log
```

Fix issues and redeploy.

## Service Architecture

### Network Configuration
- Network: oran-network (bridge)
- Subnet: 172.20.0.0/16

### Service Dependencies
```
leo-simulator (standalone)
    |
    v
sdr-gateway (depends on leo-simulator)
    |
    +-- FastAPI on port 8000
    +-- gRPC on port 50051
    +-- Connects to ZMQ on tcp://leo-simulator:5555

drl-trainer (standalone, GPU required)
flexric (standalone)
mcp-gateway (standalone)
```

### Port Mapping Summary
- 5555: LEO Simulator (ZMQ)
- 8000: SDR Gateway (FastAPI)
- 50051: SDR Gateway (gRPC)
- 6006: DRL Trainer (TensorBoard)
- 36421, 36422: FlexRIC (E2 interface)
- 3000: MCP Gateway

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :50051

# Kill the process if needed
kill -9 <PID>
```

#### 2. GPU Not Available
```bash
# Check NVIDIA drivers
nvidia-smi

# Verify Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### 3. gRPC Stubs Missing
```bash
cd 03-Implementation/integration/sdr-oran-connector
./generate_grpc_stubs.sh
```

#### 4. Virtual Environment Issues
```bash
# Recreate virtual environment
cd /home/gnb/thc1006/sdr-o-ran-platform
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Performance Monitoring

### Resource Usage
```bash
# Monitor container resources
docker stats

# Monitor GPU usage
watch -n 1 nvidia-smi
```

### Network Traffic
```bash
# Monitor network connections
docker network inspect oran-network

# Check service connectivity
docker exec sdr-gateway ping leo-simulator
```

## Next Steps After Deployment

1. **Performance Testing**: Run load tests on gRPC and FastAPI endpoints
2. **Security Audit**: Implement TLS for production
3. **Monitoring Setup**: Configure Prometheus/Grafana for metrics
4. **Backup Strategy**: Set up automated backups for models and logs
5. **CI/CD Pipeline**: Automate testing and deployment
6. **Documentation**: Update API documentation and user guides

## References

- Docker Compose file: `/home/gnb/thc1006/sdr-o-ran-platform/docker-compose.yml`
- Health check script: `/home/gnb/thc1006/sdr-o-ran-platform/scripts/health_check.sh`
- Integration tests: `/home/gnb/thc1006/sdr-o-ran-platform/scripts/run_integration_tests.sh`
- gRPC connector: `/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/integration/sdr-oran-connector/`
