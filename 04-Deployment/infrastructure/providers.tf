# SDR-O-RAN Platform - Provider Configurations
# Terraform 1.5+ with 2025 best practices

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SDR-O-RAN"
      ManagedBy   = "Terraform"
      Environment = var.environment
      Owner       = var.owner_email
      CostCenter  = var.cost_center
      Compliance  = "GDPR,HIPAA"
    }
  }

  # Security best practices
  skip_metadata_api_check     = false
  skip_region_validation      = false
  skip_credentials_validation = false
}

# Kubernetes Provider Configuration
provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      aws_eks_cluster.main.name,
      "--region",
      var.aws_region
    ]
  }
}

# Helm Provider Configuration
provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = [
        "eks",
        "get-token",
        "--cluster-name",
        aws_eks_cluster.main.name,
        "--region",
        var.aws_region
      ]
    }
  }
}

# TLS Provider for OIDC
provider "tls" {}
