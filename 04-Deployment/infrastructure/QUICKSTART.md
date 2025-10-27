# SDR-O-RAN Infrastructure - Quick Start Guide

Get your SDR-O-RAN platform running on AWS EKS in 30 minutes.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS account with admin access
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Terraform 1.5+ installed
- [ ] kubectl installed
- [ ] helm installed
- [ ] 30 minutes of time

## Quick Start (5 Steps)

### Step 1: Configure AWS Credentials (2 minutes)

```bash
# Configure AWS CLI
aws configure

# Verify access
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-name"
}
```

### Step 2: Clone and Configure (3 minutes)

```bash
# Navigate to infrastructure directory
cd 04-Deployment/infrastructure/

# Create your configuration from example
cp terraform.tfvars.example terraform.tfvars

# Edit with your details (use your favorite editor)
nano terraform.tfvars

# Minimum required changes:
# 1. Set your email: owner_email = "your-email@company.com"
# 2. Set allowed IPs: allowed_cidr_blocks = ["YOUR_IP/32"]
# 3. (Optional) Change cluster_name if desired
```

### Step 3: Create Backend Storage (3 minutes)

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket sdr-oran-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket sdr-oran-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name sdr-oran-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Wait for table to be active
aws dynamodb wait table-exists --table-name sdr-oran-terraform-locks
```

### Step 4: Deploy Infrastructure (20 minutes)

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy (takes ~20 minutes)
terraform apply

# Type 'yes' when prompted
```

What happens during deployment:
- **Minutes 0-5**: VPC, subnets, security groups created
- **Minutes 5-15**: EKS control plane provisioned
- **Minutes 15-20**: Worker nodes join cluster
- **Minutes 20-22**: EKS add-ons installed

### Step 5: Verify Deployment (2 minutes)

```bash
# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name sdr-oran-prod

# Check cluster
kubectl get nodes

# Should show 3 nodes:
# NAME                         STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal   Ready    <none>   5m    v1.33.0
# ip-10-0-2-101.ec2.internal   Ready    <none>   5m    v1.33.0
# ip-10-0-3-102.ec2.internal   Ready    <none>   5m    v1.33.0

# Check system pods
kubectl get pods -n kube-system

# All pods should be Running
```

## Post-Deployment Setup

### Install Essential Components

```bash
# Get IAM role ARN for ALB controller
ALB_ROLE=$(terraform output -raw aws_load_balancer_controller_iam_role_arn)

# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=sdr-oran-prod \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$ALB_ROLE

# Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify installations
kubectl get deployment -n kube-system aws-load-balancer-controller
kubectl get deployment -n kube-system metrics-server
```

### Deploy SDR-O-RAN Components

```bash
# Navigate to Kubernetes manifests
cd ../kubernetes/

# Create namespaces
kubectl apply -f namespaces.yaml

# Deploy Redis SDL
kubectl apply -f redis/

# Deploy E2Term
kubectl apply -f e2term/

# Deploy RIC Platform
kubectl apply -f ricplt/

# Verify deployments
kubectl get pods -n ricplt
kubectl get svc -n ricplt
```

## Validation Tests

### Test 1: Cluster Health

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods -A
```

All pods should be in `Running` or `Completed` state.

### Test 2: Storage

```bash
# Check storage class
kubectl get storageclass

# Should show redis-sdl-storage with gp3
```

### Test 3: Networking

```bash
# Test DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default

# Should resolve to cluster IP
```

### Test 4: Resource Usage

```bash
kubectl top nodes
kubectl top pods -A
```

Nodes should show reasonable CPU/memory usage (<50% on fresh cluster).

## Common Issues and Solutions

### Issue: "Error: creating EKS Cluster: InvalidParameterException"

**Solution**: Check AWS region and ensure you have sufficient EC2 limits.

```bash
# Check service limits
aws service-quotas list-service-quotas \
  --service-code eks \
  --query 'Quotas[?QuotaName==`Clusters per account`]'
```

### Issue: Nodes not joining cluster

**Solution**: Check security groups and IAM roles.

```bash
# View node bootstrap logs
aws logs tail /aws/eks/sdr-oran-prod/user-data --follow

# Check node status
kubectl describe node <node-name>
```

### Issue: Terraform state locked

**Solution**: Force unlock (use with caution).

```bash
# Get lock ID from error message
terraform force-unlock <LOCK_ID>
```

### Issue: Out of IP addresses

**Solution**: Use larger VPC CIDR or reduce availability zones.

```bash
# Edit terraform.tfvars
vpc_cidr = "10.0.0.0/8"  # Provides ~16M IPs
```

## Quick Commands Reference

### Terraform Commands

```bash
terraform init          # Initialize
terraform plan          # Preview changes
terraform apply         # Deploy
terraform destroy       # Tear down
terraform output        # Show outputs
terraform fmt           # Format files
terraform validate      # Validate config
```

### kubectl Commands

```bash
kubectl get nodes                    # List nodes
kubectl get pods -A                  # List all pods
kubectl get svc -n ricplt           # List services
kubectl describe pod <name>         # Pod details
kubectl logs <pod-name>             # Pod logs
kubectl top nodes                   # Resource usage
kubectl delete pod <name>           # Delete pod
```

### AWS CLI Commands

```bash
# EKS cluster info
aws eks describe-cluster --name sdr-oran-prod

# List node groups
aws eks list-nodegroups --cluster-name sdr-oran-prod

# View CloudWatch logs
aws logs tail /aws/eks/sdr-oran-prod/cluster --follow
```

## Monitoring Your Cluster

### CloudWatch Logs

```bash
# View cluster control plane logs
aws logs tail /aws/eks/sdr-oran-prod/cluster --follow

# View node logs
aws logs tail /aws/eks/sdr-oran-prod/system --follow
```

### AWS Console

Access these URLs (replace region if different):

- **EKS Console**: https://console.aws.amazon.com/eks/home?region=us-east-1#/clusters/sdr-oran-prod
- **EC2 Instances**: https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances
- **CloudWatch**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1

### Kubernetes Dashboard (Optional)

```bash
# Install dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Create admin user
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kube-system
EOF

# Get token
kubectl -n kube-system create token admin-user

# Start proxy
kubectl proxy

# Access at: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

## Cost Monitoring

### View Current Costs

```bash
# Estimate monthly cost (requires infracost)
infracost breakdown --path .

# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://cost-filter.json
```

### Cost Optimization Tips

1. **Use Reserved Instances**: Save 40-60% on compute
2. **Enable Cluster Autoscaler**: Scale down during off-hours
3. **Use gp3 volumes**: 20% cheaper than gp2
4. **Monitor unused resources**: Delete unused load balancers, IPs
5. **Use Spot instances for dev**: 70-90% savings

## Cleanup

When you're done testing, clean up to avoid charges:

```bash
# Delete Kubernetes resources first
kubectl delete namespace ricplt
kubectl delete namespace monitoring

# Destroy infrastructure
cd 04-Deployment/infrastructure/
terraform destroy

# Type 'yes' when prompted

# Clean up backend (optional)
aws s3 rm s3://sdr-oran-terraform-state --recursive
aws s3api delete-bucket --bucket sdr-oran-terraform-state
aws dynamodb delete-table --table-name sdr-oran-terraform-locks
```

## Getting Help

### Documentation
- [Full README](README.md) - Complete documentation
- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)

### Troubleshooting
1. Check Terraform errors: Look at detailed error messages
2. Check AWS Console: Verify resources in AWS Console
3. Check logs: CloudWatch Logs for cluster and node logs
4. Check kubectl: Use `kubectl describe` and `kubectl logs`

### Support Channels
- GitHub Issues: Report bugs and feature requests
- Slack: Join #sdr-oran channel
- Email: support@sdr-oran.example.com

## Next Steps

After successful deployment:

1. **Configure Monitoring**: Set up Prometheus and Grafana
2. **Enable Auto-scaling**: Configure HPA for workloads
3. **Set up Backups**: Configure Velero for disaster recovery
4. **Security Hardening**: Implement network policies and RBAC
5. **Performance Tuning**: Optimize for 5G RAN workloads
6. **CI/CD Integration**: Connect to your CI/CD pipeline

## Estimated Timeline

- **First-time setup**: 30 minutes
- **Subsequent deployments**: 15 minutes
- **Full production setup**: 2-3 hours
- **Learning and customization**: 1-2 days

## Success Criteria

Your deployment is successful when:

- ✅ 3 nodes show as Ready
- ✅ All system pods are Running
- ✅ Storage class is created
- ✅ kubectl commands work
- ✅ Load balancer controller is deployed
- ✅ SDR-O-RAN pods are running

## Additional Resources

- [Architecture Diagram](ARCHITECTURE.md)
- [Cost Breakdown](README.md#cost-estimation)
- [Security Best Practices](README.md#security-best-practices)
- [Performance Tuning](README.md#performance-optimization)

---

**Questions?** Open an issue or contact the team.

**Last Updated**: 2025-10-27
