# SDR-O-RAN Platform - Infrastructure as Code (Terraform)

Comprehensive Terraform configuration for deploying the SDR-O-RAN platform on AWS EKS with Kubernetes 1.33.

## Architecture Overview

This infrastructure deploys a production-ready Kubernetes cluster optimized for 5G RAN workloads with the following characteristics:

- **Kubernetes Version**: 1.33 (latest as of 2025)
- **Cloud Provider**: AWS (EKS)
- **Compute**: 3x m5.2xlarge instances (8 vCPU, 32GB RAM each)
- **Storage**: gp3 EBS volumes with high IOPS for Redis SDL
- **Networking**: VPC with public/private subnets across 3 availability zones
- **High Availability**: Multi-AZ deployment with auto-scaling

## Cost Estimation

### Monthly Breakdown
| Component | Specification | Monthly Cost |
|-----------|---------------|--------------|
| EKS Cluster | Control plane | $73.00 |
| EC2 Instances | 3x m5.2xlarge | $615.60 |
| EBS Storage | 300GB gp3 (3x100GB) | $24.00 |
| Data Transfer | 500GB/month | $45.00 |
| Load Balancers | 1x NLB | $16.20 |
| NAT Gateways | 3x NAT Gateway | $97.20 |
| **Total Monthly** | | **~$871.00** |

### 3-Year Total Cost of Ownership (TCO)
| Item | Cost |
|------|------|
| Infrastructure (36 months) | $31,356 |
| Storage (3 years) | $8,640 |
| Data Transfer | $16,200 |
| Support & Monitoring | $10,800 |
| Backup & DR | $8,640 |
| Reserved Instances Savings | -$15,678 |
| **Total 3-Year TCO** | **$100,300** |

> **Note**: Costs can be reduced by 40-50% using Reserved Instances or Savings Plans for 3-year commitments.

## Prerequisites

### Required Software
- **Terraform**: v1.5.0 or higher
- **AWS CLI**: v2.15.0 or higher
- **kubectl**: v1.33.0 or higher
- **Helm**: v3.14.0 or higher

### AWS Requirements
- Active AWS account with appropriate permissions
- AWS credentials configured (`aws configure`)
- IAM permissions for:
  - VPC, EC2, EKS resources
  - IAM role creation
  - KMS key management
  - CloudWatch Logs

### Install Required Tools

#### Terraform (2025 version)
```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Windows
choco install terraform

# Verify installation
terraform version
```

#### AWS CLI
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Configure AWS credentials
aws configure
```

#### kubectl
```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Windows
choco install kubernetes-cli

# Verify installation
kubectl version --client
```

#### Helm
```bash
# macOS
brew install helm

# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Windows
choco install kubernetes-helm

# Verify installation
helm version
```

## Directory Structure

```
infrastructure/
├── main.tf                          # Main infrastructure configuration
├── providers.tf                     # Provider configurations
├── variables.tf                     # Input variables
├── outputs.tf                       # Output values
├── user-data.sh                     # EC2 user data script
├── terraform.tfvars                 # Variable values (create this)
├── policies/
│   └── alb-controller-policy.json   # ALB controller IAM policy
└── README.md                        # This file
```

## Deployment Guide

### Step 1: Clone and Prepare

```bash
# Navigate to infrastructure directory
cd 04-Deployment/infrastructure/

# Create terraform.tfvars file
cat > terraform.tfvars <<EOF
# Cluster Configuration
cluster_name        = "sdr-oran-prod"
environment         = "production"
aws_region          = "us-east-1"
kubernetes_version  = "1.33"

# Network Configuration
vpc_cidr                = "10.0.0.0/16"
availability_zones_count = 3
allowed_cidr_blocks     = ["0.0.0.0/0"]  # Restrict this in production

# Node Configuration
node_instance_type   = "m5.2xlarge"
node_desired_count   = 3
node_min_count       = 3
node_max_count       = 10
node_disk_size       = 100
node_capacity_type   = "ON_DEMAND"

# Storage Configuration
redis_storage_size   = 50
redis_storage_iops   = 16000

# Tagging
owner_email          = "admin@yourcompany.com"
cost_center          = "telecom-ran"

# Feature Flags
enable_cluster_autoscaler = true
enable_metrics_server     = true
enable_prometheus         = true
enable_grafana            = true
EOF
```

### Step 2: Initialize Terraform

```bash
# Initialize Terraform (downloads providers)
terraform init

# Expected output:
# Terraform has been successfully initialized!
```

### Step 3: Create S3 Backend (Optional but Recommended)

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket sdr-oran-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket sdr-oran-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket sdr-oran-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name sdr-oran-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Step 4: Plan Infrastructure

```bash
# Review planned changes
terraform plan -out=tfplan

# Save plan to file for review
terraform show -json tfplan | jq > plan.json

# Expected output: ~150 resources to be created
```

### Step 5: Deploy Infrastructure

```bash
# Apply infrastructure changes
terraform apply tfplan

# Deployment time: ~20-25 minutes
# - VPC and networking: ~5 minutes
# - EKS cluster: ~10 minutes
# - Node group: ~8 minutes
# - Add-ons: ~2 minutes
```

### Step 6: Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name sdr-oran-prod

# Verify cluster access
kubectl get nodes

# Expected output:
# NAME                         STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal   Ready    <none>   5m    v1.33.0
# ip-10-0-2-101.ec2.internal   Ready    <none>   5m    v1.33.0
# ip-10-0-3-102.ec2.internal   Ready    <none>   5m    v1.33.0

# Check all pods
kubectl get pods -A
```

### Step 7: Install Essential Components

#### AWS Load Balancer Controller

```bash
# Add EKS Helm repository
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Get IAM role ARN from Terraform outputs
ALB_ROLE_ARN=$(terraform output -raw aws_load_balancer_controller_iam_role_arn)

# Install AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=sdr-oran-prod \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$ALB_ROLE_ARN \
  --set region=us-east-1 \
  --set vpcId=$(terraform output -raw vpc_id)

# Verify installation
kubectl get deployment -n kube-system aws-load-balancer-controller
```

#### Cluster Autoscaler

```bash
# Get IAM role ARN
CA_ROLE_ARN=$(terraform output -raw cluster_autoscaler_iam_role_arn)

# Download manifest
wget https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Apply with modifications
cat cluster-autoscaler-autodiscover.yaml | \
  sed "s/<YOUR CLUSTER NAME>/sdr-oran-prod/g" | \
  kubectl apply -f -

# Annotate service account
kubectl annotate serviceaccount cluster-autoscaler \
  -n kube-system \
  eks.amazonaws.com/role-arn=$CA_ROLE_ARN

# Patch deployment for latest version
kubectl patch deployment cluster-autoscaler \
  -n kube-system \
  -p '{"spec":{"template":{"metadata":{"annotations":{"cluster-autoscaler.kubernetes.io/safe-to-evict": "false"}}}}}'

kubectl set image deployment cluster-autoscaler \
  -n kube-system \
  cluster-autoscaler=registry.k8s.io/autoscaling/cluster-autoscaler:v1.33.0

# Verify
kubectl logs -f deployment/cluster-autoscaler -n kube-system
```

#### Metrics Server (for HPA)

```bash
# Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify installation
kubectl get deployment metrics-server -n kube-system

# Test metrics
kubectl top nodes
kubectl top pods -A
```

#### EBS CSI Driver Test

```bash
# Verify EBS CSI driver
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver

# Test storage class
kubectl get storageclass

# Expected output includes:
# NAME               PROVISIONER             RECLAIMPOLICY
# redis-sdl-storage  ebs.csi.aws.com         Retain
```

### Step 8: Deploy SDR-O-RAN Components

```bash
# Navigate to Kubernetes manifests
cd ../kubernetes/

# Deploy O-RAN components
kubectl apply -f namespaces.yaml
kubectl apply -f redis/
kubectl apply -f e2term/
kubectl apply -f ricplt/
kubectl apply -f services/

# Verify deployments
kubectl get pods -n ricplt
kubectl get svc -n ricplt

# Check Redis SDL with high-performance storage
kubectl get pvc -n ricplt
```

## Post-Deployment Verification

### Cluster Health Check

```bash
# Check cluster status
kubectl cluster-info

# Check node status
kubectl get nodes -o wide

# Check system pods
kubectl get pods -n kube-system

# Check resource usage
kubectl top nodes
kubectl top pods -A

# Check events
kubectl get events -A --sort-by='.lastTimestamp' | head -20
```

### Network Verification

```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default

# Test connectivity between pods
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://e2term-service.ricplt.svc.cluster.local:38000/health
```

### Security Verification

```bash
# Check Pod Security Standards
kubectl get psa -A

# Verify encryption
aws kms describe-key --key-id $(terraform output -raw kms_key_id)

# Check RBAC
kubectl get clusterrolebindings | grep -E "system:|eks:"
```

## Monitoring and Observability

### CloudWatch Logs

```bash
# View cluster logs
aws logs tail /aws/eks/sdr-oran-prod/cluster --follow

# View node logs
aws logs tail /aws/eks/sdr-oran-prod/system --follow
```

### Prometheus Metrics (if enabled)

```bash
# Port-forward Prometheus
kubectl port-forward -n monitoring svc/prometheus-server 9090:80

# Access at http://localhost:9090
```

### Grafana Dashboards (if enabled)

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80

# Access at http://localhost:3000
# Default credentials: admin/admin
```

## Scaling Operations

### Manual Scaling

```bash
# Scale node group
aws eks update-nodegroup-config \
  --cluster-name sdr-oran-prod \
  --nodegroup-name sdr-oran-prod-node-group \
  --scaling-config minSize=3,maxSize=15,desiredSize=5

# Scale deployment
kubectl scale deployment e2term -n ricplt --replicas=5
```

### Auto-scaling with HPA

```bash
# Create HPA for E2Term
kubectl autoscale deployment e2term -n ricplt \
  --cpu-percent=70 \
  --min=3 \
  --max=10

# Check HPA status
kubectl get hpa -n ricplt
```

## Backup and Disaster Recovery

### Velero Setup (Optional)

```bash
# Install Velero for backup
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm install velero vmware-tanzu/velero \
  --namespace velero \
  --create-namespace \
  --set configuration.backupStorageLocation[0].bucket=sdr-oran-backups \
  --set configuration.backupStorageLocation[0].provider=aws \
  --set configuration.volumeSnapshotLocation[0].provider=aws

# Create backup
velero backup create sdr-oran-backup --include-namespaces ricplt

# List backups
velero backup get
```

## Upgrading

### Kubernetes Version Upgrade

```bash
# Update variable in terraform.tfvars
kubernetes_version = "1.34"

# Plan upgrade
terraform plan

# Apply upgrade (cluster updates first, then nodes)
terraform apply

# Verify upgrade
kubectl version
```

### Node Group Updates

```bash
# Update instance type in terraform.tfvars
node_instance_type = "m5.4xlarge"

# Apply changes (creates new nodes before destroying old ones)
terraform apply
```

## Troubleshooting

### Common Issues

#### Issue: Nodes not joining cluster

```bash
# Check node logs
aws logs tail /aws/eks/sdr-oran-prod/user-data --follow

# Check IAM role
aws iam get-role --role-name $(terraform output -raw node_iam_role_arn | cut -d'/' -f2)

# Verify security groups
kubectl describe node <node-name>
```

#### Issue: Pod stuck in Pending

```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check node resources
kubectl top nodes

# Check storage class
kubectl get storageclass
kubectl describe storageclass redis-sdl-storage
```

#### Issue: Load balancer not created

```bash
# Check ALB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Verify IAM role
kubectl describe serviceaccount aws-load-balancer-controller -n kube-system

# Check ingress events
kubectl describe ingress <ingress-name> -n <namespace>
```

### Debugging Commands

```bash
# Get all resources in namespace
kubectl get all -n ricplt

# Check resource quotas
kubectl describe resourcequota -n ricplt

# Check network policies
kubectl get networkpolicies -A

# Check persistent volumes
kubectl get pv,pvc -A

# Check service endpoints
kubectl get endpoints -A

# SSH to node (via Session Manager)
aws ssm start-session --target <instance-id>
```

## Cleanup

### Destroy Infrastructure

```bash
# Delete Kubernetes resources first
kubectl delete namespace ricplt
kubectl delete namespace monitoring

# Destroy Terraform infrastructure
terraform destroy

# Confirm by typing 'yes'
```

### Clean up S3 backend

```bash
# Empty S3 bucket
aws s3 rm s3://sdr-oran-terraform-state --recursive

# Delete bucket
aws s3api delete-bucket --bucket sdr-oran-terraform-state

# Delete DynamoDB table
aws dynamodb delete-table --table-name sdr-oran-terraform-locks
```

## Security Best Practices

1. **Network Security**
   - Restrict `allowed_cidr_blocks` to known IPs
   - Use private subnets for worker nodes
   - Enable VPC Flow Logs for audit

2. **Access Control**
   - Use IAM roles for service accounts (IRSA)
   - Implement Pod Security Standards
   - Enable audit logging

3. **Encryption**
   - Enable encryption at rest for EBS volumes
   - Use KMS for secrets encryption
   - Enable encryption in transit (TLS)

4. **Monitoring**
   - Enable CloudWatch Container Insights
   - Set up alerts for critical metrics
   - Regular security scanning

5. **Compliance**
   - Regular vulnerability scanning
   - Implement network policies
   - Use private container registries

## Performance Optimization

### For 5G RAN Workloads

1. **Network Performance**
   - Enable enhanced networking
   - Use SR-IOV for data plane
   - Configure huge pages for DPDK

2. **CPU Performance**
   - Pin critical pods to specific CPUs
   - Use CPU manager policy
   - Enable CPU isolation

3. **Storage Performance**
   - Use gp3 with high IOPS
   - Enable EBS optimization
   - Use local NVMe for cache

## Support and Resources

### Documentation
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [O-RAN Alliance](https://www.o-ran.org/)

### Community
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Slack](https://kubernetes.slack.com/)
- [O-RAN SC Community](https://wiki.o-ran-sc.org/)

## License

Copyright (c) 2025 SDR-O-RAN Project
Licensed under Apache 2.0

## Contributors

- Infrastructure Team
- DevOps Team
- RAN Engineering Team

---

**Last Updated**: 2025-10-27
**Terraform Version**: 1.7.0
**Kubernetes Version**: 1.33
**Status**: Production Ready
