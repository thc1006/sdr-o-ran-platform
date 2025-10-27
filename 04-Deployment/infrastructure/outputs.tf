# SDR-O-RAN Platform - Output Values
# Terraform 1.5+ with 2025 best practices

# Cluster Information
output "cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.main.id
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.main.endpoint
  sensitive   = true
}

output "cluster_version" {
  description = "Kubernetes version of the cluster"
  value       = aws_eks_cluster.main.version
}

output "cluster_platform_version" {
  description = "Platform version for the cluster"
  value       = aws_eks_cluster.main.platform_version
}

output "cluster_status" {
  description = "Status of the EKS cluster"
  value       = aws_eks_cluster.main.status
}

# Certificate Authority
output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

# OIDC Provider
output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

output "oidc_provider_arn" {
  description = "ARN of the OIDC Provider for EKS"
  value       = aws_iam_openid_connect_provider.eks.arn
}

# Network Information
output "vpc_id" {
  description = "VPC ID where the cluster is deployed"
  value       = aws_vpc.sdr_oran.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.sdr_oran.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "List of public Elastic IPs created for NAT Gateways"
  value       = aws_eip.nat[*].public_ip
}

# Security Groups
output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_security_group.eks_cluster.id
}

output "node_security_group_id" {
  description = "Security group ID attached to the EKS nodes"
  value       = aws_security_group.eks_nodes.id
}

# Node Group Information
output "node_group_id" {
  description = "EKS node group ID"
  value       = aws_eks_node_group.main.id
}

output "node_group_arn" {
  description = "Amazon Resource Name (ARN) of the EKS Node Group"
  value       = aws_eks_node_group.main.arn
}

output "node_group_status" {
  description = "Status of the EKS node group"
  value       = aws_eks_node_group.main.status
}

output "node_group_resources" {
  description = "Resources associated with the node group"
  value       = aws_eks_node_group.main.resources
}

# IAM Roles
output "cluster_iam_role_arn" {
  description = "IAM role ARN of the EKS cluster"
  value       = aws_iam_role.eks_cluster.arn
}

output "node_iam_role_arn" {
  description = "IAM role ARN of the EKS nodes"
  value       = aws_iam_role.eks_nodes.arn
}

output "vpc_cni_iam_role_arn" {
  description = "IAM role ARN for VPC CNI"
  value       = aws_iam_role.vpc_cni.arn
}

output "ebs_csi_iam_role_arn" {
  description = "IAM role ARN for EBS CSI driver"
  value       = aws_iam_role.ebs_csi.arn
}

output "cluster_autoscaler_iam_role_arn" {
  description = "IAM role ARN for Cluster Autoscaler"
  value       = aws_iam_role.cluster_autoscaler.arn
}

output "aws_load_balancer_controller_iam_role_arn" {
  description = "IAM role ARN for AWS Load Balancer Controller"
  value       = aws_iam_role.aws_load_balancer_controller.arn
}

# KMS Keys
output "kms_key_id" {
  description = "KMS key ID for EKS encryption"
  value       = aws_kms_key.eks.key_id
}

output "kms_key_arn" {
  description = "KMS key ARN for EKS encryption"
  value       = aws_kms_key.eks.arn
}

# CloudWatch Log Groups
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for EKS cluster logs"
  value       = aws_cloudwatch_log_group.eks_cluster.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for EKS cluster logs"
  value       = aws_cloudwatch_log_group.eks_cluster.arn
}

# Storage Class
output "redis_storage_class_name" {
  description = "Name of the storage class for Redis SDL"
  value       = kubernetes_storage_class.redis_sdl.metadata[0].name
}

# kubectl Configuration Command
output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

# EKS Add-ons
output "vpc_cni_addon_version" {
  description = "Version of VPC CNI add-on"
  value       = aws_eks_addon.vpc_cni.addon_version
}

output "coredns_addon_version" {
  description = "Version of CoreDNS add-on"
  value       = aws_eks_addon.coredns.addon_version
}

output "kube_proxy_addon_version" {
  description = "Version of kube-proxy add-on"
  value       = aws_eks_addon.kube_proxy.addon_version
}

output "ebs_csi_addon_version" {
  description = "Version of EBS CSI driver add-on"
  value       = aws_eks_addon.ebs_csi.addon_version
}

# Cost Estimation
output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD (EKS + EC2 instances only)"
  value       = "Approximately $800-900/month for 3x m5.2xlarge nodes"
}

output "estimated_3year_tco" {
  description = "Estimated 3-year Total Cost of Ownership in USD"
  value       = "$100,300 (includes EKS, compute, storage, data transfer)"
}

# Connection Information
output "connection_details" {
  description = "Detailed connection information for the cluster"
  value = {
    cluster_name     = aws_eks_cluster.main.name
    cluster_endpoint = aws_eks_cluster.main.endpoint
    region           = var.aws_region
    kubectl_config   = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
    verify_access    = "kubectl get nodes"
  }
  sensitive = true
}

# Cluster Resource Summary
output "cluster_resources" {
  description = "Summary of cluster resources"
  value = {
    vpc_id                = aws_vpc.sdr_oran.id
    vpc_cidr              = aws_vpc.sdr_oran.cidr_block
    public_subnets        = length(aws_subnet.public)
    private_subnets       = length(aws_subnet.private)
    nat_gateways          = length(aws_nat_gateway.main)
    availability_zones    = var.availability_zones_count
    node_instance_type    = var.node_instance_type
    node_desired_count    = var.node_desired_count
    node_min_count        = var.node_min_count
    node_max_count        = var.node_max_count
    kubernetes_version    = aws_eks_cluster.main.version
  }
}

# Monitoring Endpoints
output "monitoring_endpoints" {
  description = "Monitoring and observability endpoints"
  value = {
    cloudwatch_logs = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${aws_cloudwatch_log_group.eks_cluster.name}"
    eks_console     = "https://console.aws.amazon.com/eks/home?region=${var.aws_region}#/clusters/${aws_eks_cluster.main.name}"
    ec2_instances   = "https://console.aws.amazon.com/ec2/v2/home?region=${var.aws_region}#Instances:tag:eks:cluster-name=${aws_eks_cluster.main.name}"
  }
}

# Security Configuration
output "security_configuration" {
  description = "Security configuration details"
  value = {
    encryption_enabled        = true
    secrets_encryption        = true
    kms_key_id               = aws_kms_key.eks.key_id
    cluster_security_group   = aws_security_group.eks_cluster.id
    node_security_group      = aws_security_group.eks_nodes.id
    endpoint_private_access  = aws_eks_cluster.main.vpc_config[0].endpoint_private_access
    endpoint_public_access   = aws_eks_cluster.main.vpc_config[0].endpoint_public_access
    enabled_cluster_log_types = aws_eks_cluster.main.enabled_cluster_log_types
  }
}

# Next Steps
output "next_steps" {
  description = "Recommended next steps after cluster creation"
  value = <<-EOT
    1. Configure kubectl:
       aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}

    2. Verify cluster access:
       kubectl get nodes
       kubectl get pods -A

    3. Install AWS Load Balancer Controller:
       helm repo add eks https://aws.github.io/eks-charts
       helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
         -n kube-system \
         --set clusterName=${aws_eks_cluster.main.name} \
         --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=${aws_iam_role.aws_load_balancer_controller.arn}

    4. Install Cluster Autoscaler:
       kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml
       kubectl annotate serviceaccount cluster-autoscaler \
         -n kube-system \
         eks.amazonaws.com/role-arn=${aws_iam_role.cluster_autoscaler.arn}

    5. Deploy SDR-O-RAN components:
       kubectl apply -f ../kubernetes/

    6. Monitor cluster health:
       kubectl get nodes
       kubectl top nodes
       kubectl get events -A --sort-by='.lastTimestamp'

    7. Access CloudWatch Logs:
       https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${aws_cloudwatch_log_group.eks_cluster.name}
  EOT
}

# Helm Values for SDR-O-RAN
output "helm_values_sdr_oran" {
  description = "Helm values for SDR-O-RAN deployment"
  value = {
    storageClass = kubernetes_storage_class.redis_sdl.metadata[0].name
    nodeSelector = {
      "kubernetes.io/arch" = "amd64"
    }
    redis = {
      persistence = {
        enabled      = true
        storageClass = kubernetes_storage_class.redis_sdl.metadata[0].name
        size         = "${var.redis_storage_size}Gi"
      }
    }
  }
}

# Tags Applied
output "applied_tags" {
  description = "Common tags applied to all resources"
  value       = var.common_tags
}
