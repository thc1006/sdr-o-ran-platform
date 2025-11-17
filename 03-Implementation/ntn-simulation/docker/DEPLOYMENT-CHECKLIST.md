# NTN Docker Deployment Checklist

Step-by-step checklist for deploying NTN xApps to production.

## Pre-Deployment Phase

### Environment Preparation
- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] At least 20GB free disk space available
- [ ] At least 8GB RAM available
- [ ] At least 4 CPU cores available
- [ ] Internet connectivity verified
- [ ] Firewall rules allow Docker networking
- [ ] NTP configured for time synchronization
- [ ] Log rotation configured at host level

### Repository Setup
- [ ] Code cloned to target system
- [ ] Correct branch checked out
- [ ] All submodules initialized (if any)
- [ ] Directory structure verified
- [ ] File permissions correct
- [ ] No sensitive data in code

### Configuration
- [ ] `.env` file created from `.env.example`
- [ ] Environment variables reviewed
- [ ] Port mappings appropriate for environment
- [ ] Resource limits set appropriately
- [ ] Logging configuration reviewed
- [ ] Network configuration reviewed

### Backup and Rollback
- [ ] Backup strategy defined
- [ ] Rollback procedure documented
- [ ] Previous version images archived (if upgrade)
- [ ] Data backup location identified
- [ ] Restore procedure tested

## Build Phase

### Image Building
- [ ] Run `./build.sh` or `make build`
- [ ] All images build successfully
  - [ ] E2 Termination image built
  - [ ] Handover xApp image built
  - [ ] Power Control xApp image built
- [ ] No build errors or warnings
- [ ] Image sizes reasonable (< 1GB each)
- [ ] Images tagged correctly
- [ ] Base images are latest security patches

### Image Validation
- [ ] Inspect images for correctness
  - [ ] `docker inspect ntn/e2-termination:latest`
  - [ ] `docker inspect ntn/handover-xapp:latest`
  - [ ] `docker inspect ntn/power-xapp:latest`
- [ ] Verify non-root users
- [ ] Verify correct entry points
- [ ] Verify exposed ports

### Registry (if applicable)
- [ ] Docker registry credentials configured
- [ ] `./build.sh --push --registry <url>` succeeds
- [ ] Images verifiable in registry
- [ ] Image signatures verified (if using signing)

## Pre-Deployment Testing

### Unit/Component Testing
- [ ] Run component tests locally
- [ ] Mock dependencies working
- [ ] Error handling verified
- [ ] Edge cases tested

### Integration Testing
- [ ] Services can communicate
- [ ] Redis connectivity verified
- [ ] E2 Termination port accessible
- [ ] Metric endpoints accessible
- [ ] Health checks pass

### Load Testing
- [ ] Performance under load acceptable
- [ ] No memory leaks detected
- [ ] Response times acceptable
- [ ] CPU usage within limits

### Security Testing
- [ ] Images scanned for vulnerabilities (if using tools)
- [ ] Non-root execution verified
- [ ] Secrets not hardcoded
- [ ] Network isolation verified
- [ ] Read-only filesystems tested (if configured)

## Deployment Phase

### Pre-Deployment Notification
- [ ] Team notified of deployment window
- [ ] Change request submitted (if required)
- [ ] Approval received
- [ ] Stakeholders informed

### Service Startup
- [ ] `docker-compose down` (clean slate)
- [ ] `docker-compose up -d` executed
- [ ] All containers started
  - [ ] E2 Termination container started
  - [ ] Handover xApp container started
  - [ ] Power Control xApp container started
  - [ ] Redis container started
  - [ ] Prometheus container started
- [ ] Startup logs reviewed for errors
- [ ] Services reach healthy state within 15 seconds

### Connectivity Verification
- [ ] E2 port 36421 accessible: `nc -zv localhost 36421`
- [ ] Handover port 8080 accessible: `curl http://localhost:8080/health`
- [ ] Power port 8081 accessible: `curl http://localhost:8081/health`
- [ ] E2 Termination port 8082 accessible: `curl http://localhost:8082/health`
- [ ] Redis accessible: `redis-cli -h localhost ping`
- [ ] Prometheus accessible: `curl http://localhost:9090`
- [ ] DNS resolution working between containers
- [ ] Cross-container communication working

### Service Health Verification
- [ ] `docker-compose ps` shows all healthy
- [ ] Health endpoints return 200 OK
- [ ] No error messages in logs
- [ ] Services responding to requests
- [ ] Metrics being generated

### Data Integrity
- [ ] Redis data accessible
- [ ] Prometheus collecting metrics
- [ ] Logs being written to volumes
- [ ] No data corruption detected

## Post-Deployment Validation

### Functional Testing
- [ ] Health checks passing
- [ ] Metrics accessible
- [ ] API endpoints responding
- [ ] Handover logic functioning (if testable)
- [ ] Power control functioning (if testable)

### Performance Validation
- [ ] `docker stats` shows reasonable resource usage
- [ ] Memory usage stable
- [ ] CPU usage reasonable
- [ ] Disk usage within limits
- [ ] Network throughput acceptable

### Monitoring Setup
- [ ] Prometheus targets all healthy
- [ ] Metrics scraping working
- [ ] Dashboards displaying data
- [ ] Alerting configured (if applicable)
- [ ] Log shipping working (if configured)

### Documentation
- [ ] Deployment completed in runbook
- [ ] Issues encountered documented
- [ ] Resolutions documented
- [ ] Lessons learned captured

## Production Hardening

### Backup Configuration
- [ ] Backup script created
- [ ] Backup schedule set (cron job)
- [ ] First backup completed successfully
- [ ] Restore procedure tested
- [ ] Backup retention policy configured

### Monitoring and Alerting
- [ ] Prometheus retention configured
- [ ] Alert rules configured (if applicable)
- [ ] Notification channels configured
- [ ] Alert testing completed
- [ ] On-call rotation documented

### Log Management
- [ ] Central log aggregation configured (if applicable)
- [ ] Log rotation configured
- [ ] Log retention policy set
- [ ] Log search capability verified
- [ ] Log analysis tools configured (if applicable)

### Security Hardening
- [ ] Firewall rules reviewed
- [ ] Network policies configured
- [ ] Access controls verified
- [ ] Secrets management in place
- [ ] Audit logging enabled (if required)

### Documentation
- [ ] Runbooks created
- [ ] Troubleshooting guide reviewed
- [ ] Emergency procedures documented
- [ ] Escalation procedures defined
- [ ] Contact information updated

## Operational Validation

### Daily Operations
- [ ] Services monitored daily
- [ ] No critical errors in logs
- [ ] All health checks passing
- [ ] Resource usage acceptable
- [ ] Backups completing successfully

### Weekly Review
- [ ] Performance metrics reviewed
- [ ] Capacity planning verified
- [ ] Operational issues documented
- [ ] Lessons learned documented
- [ ] Changes logged

### Monthly Review
- [ ] Security updates reviewed
- [ ] Dependency updates evaluated
- [ ] Upgrade path planned
- [ ] Disaster recovery tested
- [ ] Capacity planning updated

## Issue Management

### If Issues Found
- [ ] Issue severity assessed
- [ ] Rollback decision made
- [ ] If rolling back:
  - [ ] `docker-compose down`
  - [ ] Previous version images pulled
  - [ ] `docker-compose up -d`
  - [ ] Verification completed
- [ ] Root cause analysis scheduled
- [ ] Fix planned
- [ ] Resolution tested in staging
- [ ] Re-deployment scheduled

### If No Issues Found
- [ ] Deployment marked successful
- [ ] Sign-off obtained
- [ ] Documentation updated
- [ ] Metrics baseline established
- [ ] Team notified of success

## Post-Deployment Review

### Immediate (Day 1)
- [ ] All systems stable
- [ ] No errors in logs
- [ ] Performance as expected
- [ ] Team feedback collected
- [ ] Any issues logged

### Short-term (Week 1)
- [ ] Continued stability verified
- [ ] Performance metrics analyzed
- [ ] Optimization opportunities identified
- [ ] User feedback collected
- [ ] Lessons learned documented

### Medium-term (Month 1)
- [ ] Capacity assessment completed
- [ ] Upgrade/scaling plan refined
- [ ] Cost analysis completed
- [ ] Reliability metrics calculated
- [ ] Team training completed

## Sign-off

### Deployment Sign-off
- [ ] Deployer name: _______________
- [ ] Date: _______________
- [ ] Time: _______________
- [ ] Status: SUCCESS / ROLLBACK / PARTIAL

### Verification Sign-off
- [ ] Verifier name: _______________
- [ ] Date: _______________
- [ ] All checks passed: YES / NO
- [ ] Issues found: NONE / DOCUMENTED

### Management Sign-off
- [ ] Approval by: _______________
- [ ] Date: _______________
- [ ] Notes: _______________

## Appendix: Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| On-Call Engineer | | | |
| Team Lead | | | |
| Infrastructure | | | |
| Security | | | |
| Management | | | |

## Appendix: Important Commands

```bash
# Pre-deployment cleanup
docker-compose down -v

# Build images
./build.sh

# Start services
docker-compose up -d

# Verify services
docker-compose ps
./test.sh

# View logs
docker-compose logs -f

# Emergency rollback
docker-compose down
git checkout <previous-version>
./build.sh
docker-compose up -d

# Backup before upgrade
docker-compose exec redis redis-cli BGSAVE
docker cp ntn-redis:/data/dump.rdb backup-$(date +%Y%m%d).rdb

# Stop all services
docker-compose stop

# Remove all containers
docker-compose down

# Clean up volumes
docker volume prune -f
```

## Appendix: Expected Service Startup Times

| Service | Expected Time | Max Wait |
|---------|---------------|----------|
| Redis | 2-3s | 10s |
| Prometheus | 3-5s | 15s |
| E2 Termination | 5-10s | 20s |
| Handover xApp | 10-15s | 30s |
| Power Control xApp | 10-15s | 30s |

**Total Stack Startup**: 30-50 seconds

## Appendix: Resource Requirements

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| E2 Termination | 2 cores | 2GB | 100MB |
| Handover xApp | 2 cores | 2GB | 100MB |
| Power xApp | 2 cores | 2GB | 100MB |
| Redis | 1 core | 1GB | 1GB |
| Prometheus | 1 core | 1GB | 10GB |
| **Total** | **8 cores** | **8GB** | **11.2GB** |

## Appendix: Port Usage

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| E2 Termination | 36421 | TCP | E2 Interface |
| E2 Termination | 8082 | HTTP | Management |
| Handover xApp | 8080 | HTTP | API/Metrics |
| Power xApp | 8081 | HTTP | API/Metrics |
| Redis | 6379 | TCP | Cache |
| Prometheus | 9090 | HTTP | Metrics/UI |
