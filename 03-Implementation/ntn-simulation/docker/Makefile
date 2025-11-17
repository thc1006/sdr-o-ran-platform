.PHONY: help build build-verbose build-nocache test start stop restart down clean logs ps shell health stats build-push

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_REGISTRY ?=
DOCKER_REPO_PREFIX := ntn
IMAGE_E2 := $(DOCKER_REPO_PREFIX)/e2-termination
IMAGE_HANDOVER := $(DOCKER_REPO_PREFIX)/handover-xapp
IMAGE_POWER := $(DOCKER_REPO_PREFIX)/power-xapp
IMAGE_TAG := 1.0.0
IMAGE_TAG_LATEST := latest

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "$(BLUE)NTN Docker Compose Makefile$(NC)"
	@echo ""
	@echo "$(BLUE)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Environment variables:$(NC)"
	@echo "  DOCKER_REGISTRY - Docker registry URL (optional)"
	@echo ""

# Build targets
build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@./build.sh
	@echo "$(GREEN)Build complete!$(NC)"

build-verbose: ## Build with verbose output
	@echo "$(BLUE)Building Docker images (verbose)...$(NC)"
	@./build.sh --verbose
	@echo "$(GREEN)Build complete!$(NC)"

build-nocache: ## Build without using cache
	@echo "$(BLUE)Building Docker images (no cache)...$(NC)"
	@./build.sh --no-cache
	@echo "$(GREEN)Build complete!$(NC)"

build-e2: ## Build only E2 Termination image
	@echo "$(BLUE)Building E2 Termination image...$(NC)"
	docker build -f Dockerfile.e2-termination -t $(IMAGE_E2):$(IMAGE_TAG) -t $(IMAGE_E2):$(IMAGE_TAG_LATEST) ..
	@echo "$(GREEN)E2 Termination image built!$(NC)"

build-handover: ## Build only Handover xApp image
	@echo "$(BLUE)Building Handover xApp image...$(NC)"
	docker build -f Dockerfile.handover-xapp -t $(IMAGE_HANDOVER):$(IMAGE_TAG) -t $(IMAGE_HANDOVER):$(IMAGE_TAG_LATEST) ..
	@echo "$(GREEN)Handover xApp image built!$(NC)"

build-power: ## Build only Power Control xApp image
	@echo "$(BLUE)Building Power Control xApp image...$(NC)"
	docker build -f Dockerfile.power-xapp -t $(IMAGE_POWER):$(IMAGE_TAG) -t $(IMAGE_POWER):$(IMAGE_TAG_LATEST) ..
	@echo "$(GREEN)Power Control xApp image built!$(NC)"

build-push: build ## Build and push images to registry
ifdef DOCKER_REGISTRY
	@echo "$(BLUE)Pushing images to $(DOCKER_REGISTRY)...$(NC)"
	@./build.sh --push --registry $(DOCKER_REGISTRY)
else
	@echo "$(RED)Error: DOCKER_REGISTRY not set$(NC)"
	@echo "Usage: make build-push DOCKER_REGISTRY=myregistry.com"
	@exit 1
endif

# Service management
start: ## Start all services in background
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Waiting for services to be healthy...$(NC)"
	@sleep 5
	@docker-compose ps

stop: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose stop
	@echo "$(GREEN)Services stopped!$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Services restarted!$(NC)"

down: ## Stop and remove containers
	@echo "$(BLUE)Stopping and removing containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)Containers removed!$(NC)"

clean: ## Remove containers, volumes, and images (WARNING: destructive!)
	@echo "$(RED)WARNING: This will remove containers, volumes, and images!$(NC)"
	@read -p "Are you sure? (y/N) " confirm && [ $$confirm = y ] || exit 1
	@echo "$(BLUE)Cleaning up...$(NC)"
	docker-compose down -v
	docker rmi $(IMAGE_E2) $(IMAGE_HANDOVER) $(IMAGE_POWER) 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Logging and status
logs: ## View all logs (use SERVICE=name for specific service)
	docker-compose logs -f $(SERVICE)

ps: ## Show running containers
	docker-compose ps

shell: ## Open shell in container (use SERVICE=name, default: handover-xapp)
	docker-compose exec $(SERVICE) bash

# Monitoring
health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)Health endpoints:$(NC)"
	@for port in 8080 8081 8082; do \
		echo -n "Port $$port: "; \
		curl -s -f "http://localhost:$$port/health" > /dev/null && echo "$(GREEN)OK$(NC)" || echo "$(RED)FAIL$(NC)"; \
	done

stats: ## Show container resource usage
	@echo "$(BLUE)Container resource usage:$(NC)"
	docker stats --no-stream

# Testing
test: ## Run comprehensive tests
	@echo "$(BLUE)Running tests...$(NC)"
	@./test.sh

# Image management
images: ## List all NTN images
	@echo "$(BLUE)NTN Docker Images:$(NC)"
	docker images | grep ntn/ || echo "No NTN images found"

prune: ## Remove unused Docker resources
	@echo "$(BLUE)Pruning Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)Prune complete!$(NC)"

# Development
dev-build: ## Build for development
	@echo "$(BLUE)Building development images...$(NC)"
	docker-compose -f docker-compose.yml build

dev-up: dev-build start ## Build and start for development

dev-shell: ## Open interactive shell for development
	docker-compose exec handover-xapp bash

dev-logs: ## Show live logs for debugging
	docker-compose logs -f

# Utilities
validate: ## Validate docker-compose configuration
	@echo "$(BLUE)Validating docker-compose configuration...$(NC)"
	docker-compose config > /dev/null && echo "$(GREEN)Configuration is valid!$(NC)" || echo "$(RED)Configuration error!$(NC)"

version: ## Show versions
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@echo "NTN Image Tag: $(IMAGE_TAG)"

pull-base: ## Pull base images
	@echo "$(BLUE)Pulling base images...$(NC)"
	docker pull python:3.12-slim
	docker pull redis:7-alpine
	docker pull prom/prometheus:latest
	@echo "$(GREEN)Base images updated!$(NC)"

# All in one targets
full-rebuild: clean build ## Clean and rebuild everything
	@echo "$(GREEN)Full rebuild complete!$(NC)"

init: pull-base build start test ## Initialize complete stack
	@echo "$(GREEN)Initialization complete!$(NC)"
	@echo "Services are running at:"
	@echo "  - E2 Termination: http://localhost:8082"
	@echo "  - Handover xApp: http://localhost:8080"
	@echo "  - Power Control xApp: http://localhost:8081"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Redis: localhost:6379"
