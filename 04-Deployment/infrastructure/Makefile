# SDR-O-RAN Platform - Infrastructure Makefile
# Convenient commands for Terraform operations

.PHONY: help init plan apply destroy validate fmt clean console output cost

# Default target
.DEFAULT_GOAL := help

# Variables
CLUSTER_NAME ?= sdr-oran-prod
AWS_REGION ?= us-east-1
TF_PLAN_FILE := tfplan

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "SDR-O-RAN Infrastructure Management"
	@echo "===================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Initialization

init: ## Initialize Terraform (download providers, modules)
	@echo "$(GREEN)Initializing Terraform...$(NC)"
	terraform init -upgrade

init-backend: ## Initialize with S3 backend
	@echo "$(GREEN)Creating S3 backend...$(NC)"
	@bash scripts/create-backend.sh $(CLUSTER_NAME) $(AWS_REGION)
	@echo "$(GREEN)Initializing Terraform with backend...$(NC)"
	terraform init -backend-config="bucket=$(CLUSTER_NAME)-terraform-state" \
	               -backend-config="region=$(AWS_REGION)"

##@ Planning

plan: validate ## Create and show Terraform execution plan
	@echo "$(GREEN)Creating Terraform plan...$(NC)"
	terraform plan -out=$(TF_PLAN_FILE)

plan-json: plan ## Create plan and export as JSON
	@echo "$(GREEN)Exporting plan to JSON...$(NC)"
	terraform show -json $(TF_PLAN_FILE) | jq > plan.json
	@echo "$(GREEN)Plan exported to plan.json$(NC)"

plan-destroy: ## Create plan for infrastructure destruction
	@echo "$(YELLOW)Creating destruction plan...$(NC)"
	terraform plan -destroy -out=$(TF_PLAN_FILE)-destroy

##@ Deployment

apply: ## Apply Terraform changes (requires confirmation)
	@echo "$(GREEN)Applying Terraform changes...$(NC)"
	terraform apply

apply-auto: plan ## Apply Terraform changes automatically (no confirmation)
	@echo "$(GREEN)Auto-applying Terraform changes...$(NC)"
	terraform apply $(TF_PLAN_FILE)

##@ Destruction

destroy: ## Destroy all Terraform-managed infrastructure (requires confirmation)
	@echo "$(RED)WARNING: This will destroy all infrastructure!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		terraform destroy; \
	else \
		echo "$(YELLOW)Destruction cancelled.$(NC)"; \
	fi

destroy-auto: ## Destroy infrastructure without confirmation (DANGEROUS!)
	@echo "$(RED)Auto-destroying infrastructure...$(NC)"
	terraform destroy -auto-approve

##@ Validation and Formatting

validate: fmt ## Validate Terraform configuration
	@echo "$(GREEN)Validating Terraform configuration...$(NC)"
	terraform validate

fmt: ## Format Terraform files
	@echo "$(GREEN)Formatting Terraform files...$(NC)"
	terraform fmt -recursive

lint: ## Lint Terraform files with tflint
	@echo "$(GREEN)Linting Terraform files...$(NC)"
	@command -v tflint >/dev/null 2>&1 || { echo "$(YELLOW)tflint not installed. Run: brew install tflint$(NC)"; exit 1; }
	tflint --init
	tflint

##@ Information

output: ## Show all Terraform outputs
	@terraform output

output-json: ## Show outputs in JSON format
	@terraform output -json

show: ## Show current state
	@terraform show

console: ## Open Terraform console for interactive queries
	@terraform console

graph: ## Generate dependency graph
	@terraform graph | dot -Tpng > graph.png
	@echo "$(GREEN)Graph generated as graph.png$(NC)"

##@ State Management

state-list: ## List all resources in state
	@terraform state list

state-show: ## Show details of a specific resource
	@read -p "Enter resource address: " resource; \
	terraform state show $$resource

state-pull: ## Pull and display remote state
	@terraform state pull

refresh: ## Refresh state to match real resources
	@echo "$(GREEN)Refreshing state...$(NC)"
	terraform refresh

##@ Kubernetes

kubeconfig: ## Update kubectl config for EKS cluster
	@echo "$(GREEN)Updating kubeconfig...$(NC)"
	aws eks update-kubeconfig --region $(AWS_REGION) --name $(CLUSTER_NAME)

kubectl-test: kubeconfig ## Test kubectl connection
	@echo "$(GREEN)Testing kubectl connection...$(NC)"
	kubectl get nodes
	kubectl get pods -A

install-components: kubeconfig ## Install essential Kubernetes components
	@echo "$(GREEN)Installing AWS Load Balancer Controller...$(NC)"
	@bash scripts/install-alb-controller.sh $(CLUSTER_NAME)
	@echo "$(GREEN)Installing Cluster Autoscaler...$(NC)"
	@bash scripts/install-cluster-autoscaler.sh $(CLUSTER_NAME)
	@echo "$(GREEN)Installing Metrics Server...$(NC)"
	kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

##@ Cost Management

cost: ## Estimate infrastructure costs (requires infracost)
	@echo "$(GREEN)Calculating infrastructure costs...$(NC)"
	@command -v infracost >/dev/null 2>&1 || { echo "$(YELLOW)infracost not installed. Visit: https://www.infracost.io/docs/$(NC)"; exit 1; }
	infracost breakdown --path .

cost-diff: ## Show cost difference from last plan
	@command -v infracost >/dev/null 2>&1 || { echo "$(YELLOW)infracost not installed$(NC)"; exit 1; }
	infracost diff --path .

##@ Security

security-scan: ## Run security scan with checkov
	@echo "$(GREEN)Running security scan...$(NC)"
	@command -v checkov >/dev/null 2>&1 || { echo "$(YELLOW)checkov not installed. Run: pip install checkov$(NC)"; exit 1; }
	checkov -d .

trivy-scan: ## Scan for security issues with Trivy
	@echo "$(GREEN)Running Trivy scan...$(NC)"
	@command -v trivy >/dev/null 2>&1 || { echo "$(YELLOW)trivy not installed. Visit: https://aquasecurity.github.io/trivy/$(NC)"; exit 1; }
	trivy config .

tfsec: ## Security scan with tfsec
	@echo "$(GREEN)Running tfsec scan...$(NC)"
	@command -v tfsec >/dev/null 2>&1 || { echo "$(YELLOW)tfsec not installed. Run: brew install tfsec$(NC)"; exit 1; }
	tfsec .

##@ Documentation

docs: ## Generate documentation from Terraform files
	@echo "$(GREEN)Generating documentation...$(NC)"
	@command -v terraform-docs >/dev/null 2>&1 || { echo "$(YELLOW)terraform-docs not installed. Run: brew install terraform-docs$(NC)"; exit 1; }
	terraform-docs markdown table . > TERRAFORM.md
	@echo "$(GREEN)Documentation generated as TERRAFORM.md$(NC)"

##@ Maintenance

clean: ## Remove temporary files and caches
	@echo "$(GREEN)Cleaning temporary files...$(NC)"
	rm -f $(TF_PLAN_FILE) $(TF_PLAN_FILE)-destroy
	rm -f plan.json
	rm -f graph.png
	rm -f .terraform.lock.hcl
	rm -rf .terraform/
	@echo "$(GREEN)Clean complete$(NC)"

upgrade-providers: ## Upgrade provider versions
	@echo "$(GREEN)Upgrading providers...$(NC)"
	terraform init -upgrade

lock: ## Create or update provider lock file
	@echo "$(GREEN)Creating provider lock file...$(NC)"
	terraform providers lock \
	  -platform=darwin_amd64 \
	  -platform=darwin_arm64 \
	  -platform=linux_amd64 \
	  -platform=linux_arm64 \
	  -platform=windows_amd64

##@ CI/CD

ci-validate: ## Run CI validation checks
	@echo "$(GREEN)Running CI validation...$(NC)"
	terraform fmt -check -recursive
	terraform init -backend=false
	terraform validate

ci-plan: ## Create plan for CI/CD
	@echo "$(GREEN)Creating plan for CI/CD...$(NC)"
	terraform plan -input=false -no-color -out=$(TF_PLAN_FILE)

ci-apply: ## Apply plan in CI/CD
	@echo "$(GREEN)Applying plan in CI/CD...$(NC)"
	terraform apply -input=false -no-color $(TF_PLAN_FILE)

##@ Monitoring

dashboard: ## Open AWS console dashboards
	@echo "$(GREEN)Opening AWS console...$(NC)"
	@open "https://console.aws.amazon.com/eks/home?region=$(AWS_REGION)#/clusters/$(CLUSTER_NAME)" 2>/dev/null || \
	 xdg-open "https://console.aws.amazon.com/eks/home?region=$(AWS_REGION)#/clusters/$(CLUSTER_NAME)" 2>/dev/null || \
	 echo "$(YELLOW)Please open: https://console.aws.amazon.com/eks/home?region=$(AWS_REGION)#/clusters/$(CLUSTER_NAME)$(NC)"

logs: kubeconfig ## Show cluster logs
	@echo "$(GREEN)Fetching cluster logs...$(NC)"
	kubectl logs -n kube-system -l app=kube-apiserver --tail=100

events: kubeconfig ## Show cluster events
	@echo "$(GREEN)Fetching cluster events...$(NC)"
	kubectl get events -A --sort-by='.lastTimestamp' | head -50

top: kubeconfig ## Show resource usage
	@echo "$(GREEN)Showing resource usage...$(NC)"
	kubectl top nodes
	@echo ""
	kubectl top pods -A

##@ Backup and Recovery

backup-state: ## Backup Terraform state
	@echo "$(GREEN)Backing up Terraform state...$(NC)"
	@mkdir -p backups
	terraform state pull > backups/terraform-state-$(shell date +%Y%m%d-%H%M%S).json
	@echo "$(GREEN)State backed up to backups/$(NC)"

restore-state: ## Restore Terraform state from backup
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -1 backups/terraform-state-*.json 2>/dev/null || echo "No backups found"
	@read -p "Enter backup filename: " backup; \
	if [ -f "backups/$$backup" ]; then \
		terraform state push "backups/$$backup"; \
		echo "$(GREEN)State restored from $$backup$(NC)"; \
	else \
		echo "$(RED)Backup file not found$(NC)"; \
	fi

##@ Development

dev-apply: ## Quick apply for development (skip validations)
	@echo "$(YELLOW)Quick development apply...$(NC)"
	terraform apply -auto-approve

dev-destroy: ## Quick destroy for development
	@echo "$(YELLOW)Quick development destroy...$(NC)"
	terraform destroy -auto-approve

dev-refresh: ## Refresh development environment
	@echo "$(YELLOW)Refreshing development environment...$(NC)"
	terraform apply -refresh-only -auto-approve

##@ Advanced

taint: ## Mark a resource for recreation
	@read -p "Enter resource address to taint: " resource; \
	terraform taint $$resource

untaint: ## Remove taint from a resource
	@read -p "Enter resource address to untaint: " resource; \
	terraform untaint $$resource

import: ## Import existing resource into state
	@read -p "Enter resource address: " addr; \
	read -p "Enter resource ID: " id; \
	terraform import $$addr $$id

workspace-list: ## List Terraform workspaces
	@terraform workspace list

workspace-new: ## Create new workspace
	@read -p "Enter workspace name: " name; \
	terraform workspace new $$name

workspace-select: ## Select workspace
	@read -p "Enter workspace name: " name; \
	terraform workspace select $$name

##@ Utilities

version: ## Show Terraform version
	@terraform version

providers: ## Show provider requirements
	@terraform providers

check-tools: ## Check if required tools are installed
	@echo "$(GREEN)Checking required tools...$(NC)"
	@command -v terraform >/dev/null 2>&1 && echo "✓ terraform" || echo "✗ terraform (required)"
	@command -v aws >/dev/null 2>&1 && echo "✓ aws-cli" || echo "✗ aws-cli (required)"
	@command -v kubectl >/dev/null 2>&1 && echo "✓ kubectl" || echo "✗ kubectl (required)"
	@command -v helm >/dev/null 2>&1 && echo "✓ helm" || echo "✗ helm (required)"
	@command -v jq >/dev/null 2>&1 && echo "✓ jq" || echo "✗ jq (optional)"
	@command -v tflint >/dev/null 2>&1 && echo "✓ tflint" || echo "✗ tflint (optional)"
	@command -v checkov >/dev/null 2>&1 && echo "✓ checkov" || echo "✗ checkov (optional)"
	@command -v infracost >/dev/null 2>&1 && echo "✓ infracost" || echo "✗ infracost (optional)"

install-tools: ## Install recommended tools (macOS)
	@echo "$(GREEN)Installing recommended tools (macOS)...$(NC)"
	brew install terraform aws-cli kubectl helm jq tflint tfsec
	pip3 install checkov
	@echo "$(GREEN)Tools installed. Run 'make check-tools' to verify.$(NC)"
