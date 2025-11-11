# Deployment Documentation

This directory contains all deployment-related documentation for the SDR-O-RAN Platform.

## Quick Start
- [README-DEPLOYMENT.md](./README-DEPLOYMENT.md) - Deployment overview and quick reference

## Deployment Guides
- [DEPLOYMENT-GUIDE.md](./DEPLOYMENT-GUIDE.md) - Comprehensive deployment guide
- [DEPLOYMENT-WSL2-GPU.md](./DEPLOYMENT-WSL2-GPU.md) - WSL2 with GPU acceleration deployment guide
- [GPU-MACHINE-COMPLETE-SETUP-SCRIPT.md](./GPU-MACHINE-COMPLETE-SETUP-SCRIPT.md) - Complete GPU machine setup script
- [GPU-MACHINE-LEO-SIMULATOR-SETUP.md](./GPU-MACHINE-LEO-SIMULATOR-SETUP.md) - LEO simulator GPU setup

## Deployment Status & Reports
- [DEPLOYMENT-SUMMARY.md](./DEPLOYMENT-SUMMARY.md) - Deployment summary and overview
- [DEPLOYMENT-SUCCESS-REPORT.md](./DEPLOYMENT-SUCCESS-REPORT.md) - Successful deployment report
- [DEPLOYMENT-IN-PROGRESS.md](./DEPLOYMENT-IN-PROGRESS.md) - Current deployment progress tracker
- [NIGHT-DEPLOYMENT-STATUS.md](./NIGHT-DEPLOYMENT-STATUS.md) - Night deployment status updates

## Testing & Validation
- [DEPLOYMENT-TEST-REPORT.md](./DEPLOYMENT-TEST-REPORT.md) - Deployment test results
- [REAL-DEPLOYMENT-TEST-PLAN.md](./REAL-DEPLOYMENT-TEST-PLAN.md) - Real deployment test plan
- [REAL-DEPLOYMENT-TEST-REPORT.md](./REAL-DEPLOYMENT-TEST-REPORT.md) - Real deployment test report

## Deployment Architecture

The platform supports multiple deployment scenarios:
1. **Local Development** - Docker Compose on local machine
2. **WSL2 + GPU** - Windows Subsystem for Linux with GPU acceleration
3. **Cloud Deployment** - AWS EKS with Terraform (see [../../04-Deployment/](../../04-Deployment/))
4. **Kubernetes** - Production-ready Kubernetes deployment

For technical reports and analysis, see [../reports/](../reports/)
