# SDR-O-RAN Platform - Input Variables
# Terraform 1.5+ with 2025 best practices

# General Configuration
variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "sdr-oran-cluster"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.cluster_name))
    error_message = "Cluster name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be a valid region format (e.g., us-east-1)."
  }
}

# Kubernetes Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.33"

  validation {
    condition     = can(regex("^1\\.(3[0-9])$", var.kubernetes_version))
    error_message = "Kubernetes version must be 1.30 or higher."
  }
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 3

  validation {
    condition     = var.availability_zones_count >= 2 && var.availability_zones_count <= 6
    error_message = "Availability zones count must be between 2 and 6."
  }
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the cluster API"
  type        = list(string)
  default     = ["0.0.0.0/0"]

  validation {
    condition     = alltrue([for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))])
    error_message = "All CIDR blocks must be valid IPv4 CIDR blocks."
  }
}

# Node Group Configuration
variable "node_instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "m5.2xlarge"

  validation {
    condition     = can(regex("^[a-z][0-9][a-z]?\\.[a-z0-9]+$", var.node_instance_type))
    error_message = "Instance type must be a valid EC2 instance type."
  }
}

variable "node_desired_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3

  validation {
    condition     = var.node_desired_count >= 1 && var.node_desired_count <= 100
    error_message = "Desired node count must be between 1 and 100."
  }
}

variable "node_min_count" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 3

  validation {
    condition     = var.node_min_count >= 1 && var.node_min_count <= 100
    error_message = "Minimum node count must be between 1 and 100."
  }
}

variable "node_max_count" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10

  validation {
    condition     = var.node_max_count >= 1 && var.node_max_count <= 100
    error_message = "Maximum node count must be between 1 and 100."
  }
}

variable "node_disk_size" {
  description = "Disk size in GB for worker nodes"
  type        = number
  default     = 100

  validation {
    condition     = var.node_disk_size >= 20 && var.node_disk_size <= 16384
    error_message = "Node disk size must be between 20 GB and 16,384 GB."
  }
}

variable "node_capacity_type" {
  description = "Type of capacity for node group (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "Capacity type must be ON_DEMAND or SPOT."
  }
}

# EKS Add-on Versions
variable "vpc_cni_version" {
  description = "Version of VPC CNI add-on"
  type        = string
  default     = "v1.18.0-eksbuild.1"
}

variable "coredns_version" {
  description = "Version of CoreDNS add-on"
  type        = string
  default     = "v1.11.1-eksbuild.4"
}

variable "kube_proxy_version" {
  description = "Version of kube-proxy add-on"
  type        = string
  default     = "v1.33.0-eksbuild.1"
}

variable "ebs_csi_version" {
  description = "Version of EBS CSI driver add-on"
  type        = string
  default     = "v1.28.0-eksbuild.1"
}

# Logging Configuration
variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period."
  }
}

# Tagging Configuration
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "SDR-O-RAN"
    ManagedBy   = "Terraform"
    Repository  = "github.com/sdr-oran/infrastructure"
    Application = "5G-RAN"
    Technology  = "O-RAN"
  }
}

variable "owner_email" {
  description = "Email address of the resource owner"
  type        = string
  default     = "admin@sdr-oran.example.com"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.owner_email))
    error_message = "Owner email must be a valid email address."
  }
}

variable "cost_center" {
  description = "Cost center for billing purposes"
  type        = string
  default     = "telecom-ran"
}

# Auto-scaling Configuration
variable "enable_cluster_autoscaler" {
  description = "Enable Cluster Autoscaler"
  type        = bool
  default     = true
}

variable "enable_metrics_server" {
  description = "Enable Metrics Server for HPA"
  type        = bool
  default     = true
}

# High Availability Configuration
variable "enable_multi_az" {
  description = "Enable multi-AZ deployment for high availability"
  type        = bool
  default     = true
}

# Security Configuration
variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest for EBS volumes"
  type        = bool
  default     = true
}

variable "enable_secrets_encryption" {
  description = "Enable encryption for Kubernetes secrets"
  type        = bool
  default     = true
}

variable "enable_pod_security_policy" {
  description = "Enable Pod Security Policy"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}

variable "enable_prometheus" {
  description = "Enable Prometheus for monitoring"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana for visualization"
  type        = bool
  default     = true
}

# Backup Configuration
variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention days must be between 1 and 365."
  }
}

# Redis SDL Storage Configuration
variable "redis_storage_size" {
  description = "Storage size in GB for Redis SDL"
  type        = number
  default     = 50

  validation {
    condition     = var.redis_storage_size >= 10 && var.redis_storage_size <= 1000
    error_message = "Redis storage size must be between 10 GB and 1000 GB."
  }
}

variable "redis_storage_iops" {
  description = "IOPS for Redis SDL storage"
  type        = number
  default     = 16000

  validation {
    condition     = var.redis_storage_iops >= 3000 && var.redis_storage_iops <= 16000
    error_message = "Redis storage IOPS must be between 3000 and 16000."
  }
}

# Performance Configuration
variable "enable_enhanced_networking" {
  description = "Enable enhanced networking for EC2 instances"
  type        = bool
  default     = true
}

variable "enable_ebs_optimization" {
  description = "Enable EBS optimization for EC2 instances"
  type        = bool
  default     = true
}

# Cost Optimization Configuration
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_max_price" {
  description = "Maximum price for spot instances (empty for on-demand price)"
  type        = string
  default     = ""
}

# Disaster Recovery Configuration
variable "enable_cross_region_backup" {
  description = "Enable cross-region backup for disaster recovery"
  type        = bool
  default     = false
}

variable "backup_region" {
  description = "AWS region for backup replication"
  type        = string
  default     = "us-west-2"
}

# Compliance Configuration
variable "enable_compliance_scanning" {
  description = "Enable compliance scanning (CIS, PCI-DSS)"
  type        = bool
  default     = true
}

variable "enable_audit_logging" {
  description = "Enable audit logging for compliance"
  type        = bool
  default     = true
}

# Network Policy Configuration
variable "enable_network_policy" {
  description = "Enable network policies for pod-to-pod communication"
  type        = bool
  default     = true
}

variable "network_policy_provider" {
  description = "Network policy provider (calico, cilium)"
  type        = string
  default     = "calico"

  validation {
    condition     = contains(["calico", "cilium"], var.network_policy_provider)
    error_message = "Network policy provider must be calico or cilium."
  }
}

# Load Balancer Configuration
variable "enable_nlb" {
  description = "Enable Network Load Balancer"
  type        = bool
  default     = true
}

variable "enable_alb" {
  description = "Enable Application Load Balancer"
  type        = bool
  default     = true
}

variable "load_balancer_type" {
  description = "Type of load balancer (network, application)"
  type        = string
  default     = "network"

  validation {
    condition     = contains(["network", "application"], var.load_balancer_type)
    error_message = "Load balancer type must be network or application."
  }
}

# DNS Configuration
variable "enable_external_dns" {
  description = "Enable ExternalDNS for automatic DNS management"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for external DNS"
  type        = string
  default     = "sdr-oran.example.com"
}

# Certificate Configuration
variable "enable_cert_manager" {
  description = "Enable cert-manager for automatic certificate management"
  type        = bool
  default     = true
}

variable "cert_manager_email" {
  description = "Email for Let's Encrypt certificate notifications"
  type        = string
  default     = "admin@sdr-oran.example.com"
}

# Service Mesh Configuration
variable "enable_service_mesh" {
  description = "Enable service mesh (Istio)"
  type        = bool
  default     = false
}

variable "service_mesh_provider" {
  description = "Service mesh provider (istio, linkerd)"
  type        = string
  default     = "istio"

  validation {
    condition     = contains(["istio", "linkerd"], var.service_mesh_provider)
    error_message = "Service mesh provider must be istio or linkerd."
  }
}
