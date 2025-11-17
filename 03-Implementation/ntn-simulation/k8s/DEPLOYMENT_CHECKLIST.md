# NTN-O-RAN Deployment Checklist

Pre-deployment checklist to ensure production readiness.

## Pre-Deployment

### Infrastructure

- [ ] Kubernetes cluster provisioned (1.24+)
  - [ ] Minimum 8 CPUs available
  - [ ] Minimum 16GB RAM available
  - [ ] Minimum 100GB storage available
- [ ] kubectl configured and tested
- [ ] Helm 3.8+ installed (if using Helm)
- [ ] Storage provisioner configured
- [ ] Ingress controller installed (nginx recommended)
- [ ] cert-manager installed (if using TLS)
- [ ] metrics-server installed (for HPA)

### Configuration

- [ ] Namespace created (`kubectl create namespace ntn-oran`)
- [ ] Secrets configured
  - [ ] Redis password (if enabled)
  - [ ] Weather API key
  - [ ] Grafana admin password
  - [ ] Database credentials (if applicable)
  - [ ] TLS certificates (if using HTTPS)
- [ ] ConfigMaps reviewed and customized
  - [ ] Log level appropriate (INFO for production)
  - [ ] Resource limits suitable for workload
  - [ ] Target metrics set (latency, throughput)
- [ ] Docker images built and pushed to registry
  - [ ] e2-termination:latest
  - [ ] handover-xapp:latest
  - [ ] power-xapp:latest
  - [ ] weather-service:latest (if applicable)
  - [ ] orbit-service:latest

### Security

- [ ] RBAC roles and bindings configured
- [ ] Service accounts created
- [ ] Network policies defined (if required)
- [ ] Security contexts set on pods
- [ ] Secrets encrypted at rest (cluster feature)
- [ ] Image pull secrets configured (if private registry)
- [ ] TLS enabled for external endpoints

### Monitoring

- [ ] Prometheus deployment configured
- [ ] Grafana deployment configured
- [ ] Grafana datasources configured
- [ ] Dashboards imported
  - [ ] NTN-O-RAN Overview
  - [ ] E2 Interface Metrics
  - [ ] Satellite Tracking
  - [ ] xApp Performance
- [ ] Alert rules configured
- [ ] Alert notification channels set up (Slack, email, etc.)

### Logging

- [ ] Elasticsearch deployment configured
- [ ] Logstash deployment configured
- [ ] Kibana deployment configured
- [ ] Filebeat DaemonSet configured
- [ ] Log retention policy set
- [ ] Index patterns created in Kibana

## Deployment

### Initial Deployment

- [ ] Deploy namespace
  ```bash
  kubectl apply -f k8s/namespace.yaml
  ```

- [ ] Deploy ConfigMaps
  ```bash
  kubectl apply -f k8s/configmap.yaml
  ```

- [ ] Deploy Secrets
  ```bash
  kubectl apply -f k8s/secrets.yaml
  ```

- [ ] Deploy Redis
  ```bash
  kubectl apply -f k8s/deployments/redis-deployment.yaml
  kubectl apply -f k8s/services/redis-service.yaml
  ```

- [ ] Wait for Redis to be ready
  ```bash
  kubectl wait --for=condition=ready pod -l app=redis -n ntn-oran --timeout=5m
  ```

- [ ] Deploy core services
  ```bash
  kubectl apply -f k8s/deployments/
  kubectl apply -f k8s/services/
  ```

- [ ] Deploy monitoring stack
  ```bash
  kubectl apply -f k8s/monitoring/prometheus/
  kubectl apply -f k8s/monitoring/grafana/
  ```

- [ ] Deploy logging stack (optional)
  ```bash
  kubectl apply -f k8s/logging/
  ```

- [ ] Deploy Ingress
  ```bash
  kubectl apply -f k8s/ingress.yaml
  ```

- [ ] Deploy HPA and PDB
  ```bash
  kubectl apply -f k8s/hpa.yaml
  kubectl apply -f k8s/pdb.yaml
  ```

### Verification

- [ ] All pods running
  ```bash
  kubectl get pods -n ntn-oran
  # Ensure all pods are Running
  ```

- [ ] All services have endpoints
  ```bash
  kubectl get endpoints -n ntn-oran
  ```

- [ ] Health checks passing
  ```bash
  # E2 Termination
  kubectl exec -it deployment/e2-termination -n ntn-oran -- curl localhost:8082/health

  # Handover xApp
  kubectl exec -it deployment/handover-xapp -n ntn-oran -- curl localhost:8080/health

  # Power xApp
  kubectl exec -it deployment/power-xapp -n ntn-oran -- curl localhost:8081/health
  ```

- [ ] Prometheus scraping metrics
  ```bash
  kubectl port-forward -n ntn-oran svc/prometheus-service 9090:9090
  # Open http://localhost:9090/targets
  # Verify all targets are UP
  ```

- [ ] Grafana accessible
  ```bash
  kubectl port-forward -n ntn-oran svc/grafana-service 3000:3000
  # Open http://localhost:3000
  # Login and verify dashboards
  ```

- [ ] Logs flowing to Elasticsearch
  ```bash
  kubectl port-forward -n ntn-oran svc/kibana 5601:5601
  # Open http://localhost:5601
  # Verify logs are visible
  ```

## Post-Deployment

### Functional Testing

- [ ] E2 interface connectivity test
- [ ] Message flow test (Indication, Control, Subscription)
- [ ] Handover xApp functionality test
- [ ] Power xApp functionality test
- [ ] Weather service integration test (if applicable)
- [ ] Orbit service satellite tracking test

### Performance Testing

- [ ] Latency measurement
  - [ ] Target: <5.5ms average
  - [ ] Acceptable: <10ms
- [ ] Throughput measurement
  - [ ] Target: >600 msg/s
  - [ ] Acceptable: >400 msg/s
- [ ] Error rate check
  - [ ] Target: <1%
  - [ ] Acceptable: <5%
- [ ] Resource usage baseline
  - [ ] CPU usage per pod
  - [ ] Memory usage per pod
  - [ ] Disk I/O

### Scaling Tests

- [ ] HPA triggers correctly
  ```bash
  # Generate load and verify scaling
  kubectl get hpa -n ntn-oran -w
  ```
- [ ] Pod Disruption Budget prevents outages
  ```bash
  kubectl drain <node> --ignore-daemonsets
  # Verify minimum pods remain available
  ```
- [ ] Replica scaling manual test
  ```bash
  kubectl scale deployment/e2-termination --replicas=5 -n ntn-oran
  ```

### High Availability

- [ ] Test pod failure recovery
  ```bash
  kubectl delete pod <pod-name> -n ntn-oran
  # Verify pod restarts automatically
  ```
- [ ] Test node failure (if multi-node)
  ```bash
  kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
  # Verify pods migrate to other nodes
  ```
- [ ] Test rolling update
  ```bash
  kubectl set image deployment/e2-termination e2-termination=ntn/e2-termination:v2 -n ntn-oran
  # Verify zero downtime
  ```

### Security Validation

- [ ] Network policies effective (if configured)
- [ ] RBAC permissions correct
- [ ] Secrets not exposed in logs
- [ ] TLS certificates valid
- [ ] Image vulnerabilities scanned
  ```bash
  docker scan ntn/e2-termination:latest
  ```

## Documentation

- [ ] Deployment documentation updated
- [ ] Architecture diagram current
- [ ] Runbook created for common operations
- [ ] Disaster recovery plan documented
- [ ] Contact information for escalation
- [ ] Monitoring dashboard URLs documented
- [ ] Access credentials documented (in secure location)

## Backup & Recovery

- [ ] Persistent volume backup strategy defined
- [ ] Configuration backup automated
  ```bash
  kubectl get configmap -n ntn-oran -o yaml > backup/configmaps.yaml
  kubectl get secret -n ntn-oran -o yaml > backup/secrets.yaml
  ```
- [ ] Disaster recovery procedure tested
- [ ] RTO (Recovery Time Objective) defined
- [ ] RPO (Recovery Point Objective) defined

## Operational Readiness

- [ ] Monitoring alerts configured and tested
- [ ] On-call rotation established
- [ ] Incident response plan in place
- [ ] Communication channels set up (Slack, PagerDuty, etc.)
- [ ] Training completed for operations team
- [ ] Change management process defined
- [ ] Rollback procedure documented and tested

## Sign-Off

- [ ] Development team approval
- [ ] DevOps team approval
- [ ] Security team approval
- [ ] Management approval

## Post-Production

### First 24 Hours

- [ ] Monitor dashboards continuously
- [ ] Check logs for errors
- [ ] Verify alert rules triggering correctly
- [ ] Monitor resource usage trends
- [ ] Check for any unexpected restarts

### First Week

- [ ] Review performance metrics vs baselines
- [ ] Tune resource requests/limits if needed
- [ ] Optimize HPA settings
- [ ] Review and tune alerts (reduce false positives)
- [ ] Document any issues and resolutions
- [ ] Collect feedback from users

### First Month

- [ ] Performance trend analysis
- [ ] Capacity planning review
- [ ] Cost optimization
- [ ] Security audit
- [ ] Disaster recovery drill
- [ ] Documentation updates

## Rollback Plan

If deployment fails:

1. Rollback using Helm:
   ```bash
   helm rollback ntn-oran -n ntn-oran
   ```

2. Or rollback manually:
   ```bash
   kubectl rollout undo deployment/<deployment-name> -n ntn-oran
   ```

3. Restore from backup if needed:
   ```bash
   kubectl apply -f backup/
   ```

4. Notify stakeholders
5. Conduct post-mortem
6. Document lessons learned

## Support Contacts

- **Development Team**: dev@ntn-oran.local
- **DevOps Team**: devops@ntn-oran.local
- **On-Call**: oncall@ntn-oran.local
- **Escalation**: escalation@ntn-oran.local

## References

- [Deployment README](./README.md)
- [Monitoring Guide](./MONITORING_GUIDE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Scaling Guide](./SCALING_GUIDE.md)
