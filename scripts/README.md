# Deployment and Automation Scripts

This directory contains automation scripts for deployment, testing, and monitoring of the SDR-O-RAN Platform.

## Deployment Scripts

### Windows Deployment
- **DEPLOY-NOW.ps1** - PowerShell script for automated deployment on Windows/WSL2
  - Checks WSL, Docker, and GPU prerequisites
  - Copies project to WSL environment
  - Initiates automated deployment

### Linux Deployment
- **auto-deploy.sh** - Comprehensive automated deployment script
  - Sets up complete environment
  - Configures all services
  - Runs validation tests

- **quick-start.sh** - Quick start script for rapid deployment
  - Minimal configuration
  - Fast startup
  - Development-friendly

## Management Scripts

- **stop-all.sh** - Stops all running services
  - Docker containers
  - Background processes
  - Cleanup operations

- **monitor.sh** - Monitoring dashboard launcher
  - Service health checks
  - Resource monitoring
  - Log aggregation

## Testing Scripts

- **test-all.sh** - Complete test suite runner
  - Unit tests
  - Integration tests
  - System tests
  - Validation checks

## Kubernetes Scripts

- **setup-k8s-namespaces.sh** - Kubernetes namespace setup
  - Creates required namespaces
  - Sets resource quotas
  - Configures RBAC

## Usage Examples

### Windows Quick Start
```powershell
.\scripts\DEPLOY-NOW.ps1
```

### Linux Quick Start
```bash
./scripts/quick-start.sh
```

### Full Deployment
```bash
./scripts/auto-deploy.sh
```

### Run Tests
```bash
./scripts/test-all.sh
```

### Stop All Services
```bash
./scripts/stop-all.sh
```

### Monitor Services
```bash
./scripts/monitor.sh
```

## Prerequisites

- **Windows**: PowerShell 5.1+, WSL2, Docker Desktop
- **Linux**: Bash 4.0+, Docker, Docker Compose
- **Kubernetes**: kubectl, helm (for K8s scripts)

For detailed deployment instructions, see [../docs/deployment/](../docs/deployment/)
