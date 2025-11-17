# NTN Docker Directory Index

Quick navigation guide for all Docker-related files and documentation.

## Directory Structure

```
docker/
├── Dockerfile.e2-termination          # E2 Termination service container
├── Dockerfile.handover-xapp           # Handover optimization xApp container
├── Dockerfile.power-xapp              # Power control optimization xApp container
├── docker-compose.yml                 # Complete stack orchestration
├── prometheus.yml                     # Prometheus monitoring config
├── .dockerignore                      # Build context optimization
├── .env.example                       # Environment variables template
├── requirements-docker.txt            # Python dependencies for Docker
├── build.sh                           # Build automation script
├── test.sh                            # Testing framework
├── run.sh                             # Service management shortcuts
├── Makefile                           # Alternative build system
├── INDEX.md                           # This file
├── DELIVERABLES.md                    # Deliverables summary
├── README.md                          # Main user guide
├── QUICK-REFERENCE.md                 # Command reference
├── DEPLOYMENT-GUIDE.md                # Step-by-step deployment
├── DEPLOYMENT-CHECKLIST.md            # Pre-flight checklist
├── ARCHITECTURE.md                    # System architecture
├── TESTING-GUIDE.md                   # Testing procedures
└── TROUBLESHOOTING.md                 # Problem solving guide
```

## File Quick Links

### Configuration Files

| File | Purpose | Size |
|------|---------|------|
| `docker-compose.yml` | Stack definition | 4KB |
| `prometheus.yml` | Metrics config | 2KB |
| `.dockerignore` | Build optimization | <1KB |
| `.env.example` | Environment template | 1KB |

### Application Containers

| File | Service | Port(s) | User |
|------|---------|---------|------|
| `Dockerfile.e2-termination` | E2 Interface | 36421, 8082 | e2term |
| `Dockerfile.handover-xapp` | Handover Optimization | 8080 | xapp |
| `Dockerfile.power-xapp` | Power Control | 8081 | xapp |

### Build & Automation

| File | Purpose | Type |
|------|---------|------|
| `build.sh` | Image building | Bash script |
| `test.sh` | Testing framework | Bash script |
| `run.sh` | Service management | Bash script |
| `Makefile` | Alternative build system | Makefile |

### Documentation

| File | Focus | Length |
|------|-------|--------|
| `README.md` | Getting started | 500+ lines |
| `QUICK-REFERENCE.md` | Fast command reference | 300+ lines |
| `DEPLOYMENT-GUIDE.md` | Step-by-step deployment | 600+ lines |
| `DEPLOYMENT-CHECKLIST.md` | Pre-flight checks | 400+ lines |
| `ARCHITECTURE.md` | System design | 600+ lines |
| `TESTING-GUIDE.md` | Quality assurance | 400+ lines |
| `TROUBLESHOOTING.md` | Problem solving | 400+ lines |
| `DELIVERABLES.md` | Inventory & summary | 300+ lines |

## Getting Started

### 1. First Time Setup

```bash
cd docker
cp .env.example .env    # Create environment config
./build.sh              # Build all images (first time)
docker-compose up -d    # Start services
./test.sh               # Verify deployment
```

**Time required**: 10-30 minutes (depending on system/network)

### 2. Daily Operations

```bash
./run.sh start          # Start services
./run.sh logs -f        # Watch logs
./run.sh health         # Check health
./run.sh stop           # Stop services
```

**See**: `QUICK-REFERENCE.md` for more commands

### 3. Deployment

```bash
# Read deployment guide
cat DEPLOYMENT-GUIDE.md

# Use checklist
cat DEPLOYMENT-CHECKLIST.md

# Deploy
./build.sh
docker-compose up -d
./test.sh
```

**See**: `DEPLOYMENT-GUIDE.md` for complete procedures

### 4. Troubleshooting

**Having issues?**

1. Check logs: `docker-compose logs`
2. Check health: `./run.sh health`
3. Run tests: `./test.sh`
4. Consult: `TROUBLESHOOTING.md`

**See**: `TROUBLESHOOTING.md` for detailed solutions

## Documentation Guide

### For Different Audiences

**System Operators**
1. Start with `README.md` for overview
2. Use `QUICK-REFERENCE.md` for daily commands
3. Consult `TROUBLESHOOTING.md` for issues
4. Reference `DEPLOYMENT-CHECKLIST.md` for procedures

**DevOps/Cloud Engineers**
1. Read `ARCHITECTURE.md` for system design
2. Review `DEPLOYMENT-GUIDE.md` for deployment
3. Understand `DEPLOYMENT-CHECKLIST.md` for validation
4. Check `TESTING-GUIDE.md` for CI/CD integration

**Developers**
1. Start with `README.md`
2. Use `QUICK-REFERENCE.md` for local development
3. Check `ARCHITECTURE.md` for design details
4. Run `./test.sh` to verify changes

**Security/Compliance Teams**
1. Review `ARCHITECTURE.md` (security section)
2. Check `DEPLOYMENT-GUIDE.md` (security hardening)
3. Verify `DEPLOYMENT-CHECKLIST.md` (security checks)
4. Audit `TROUBLESHOOTING.md` (security considerations)

## Command Quick Reference

### Build

```bash
./build.sh                              # Build all images
./build.sh --no-cache                   # Force rebuild
./build.sh --verbose                    # Detailed output
make build                              # Using Makefile
docker-compose build                    # Using docker-compose
```

### Start/Stop

```bash
./run.sh start                          # Start all services
docker-compose up -d                    # Start in background
./run.sh stop                           # Stop services
docker-compose stop                     # Alternative
./run.sh restart                        # Restart services
```

### Monitoring

```bash
./run.sh health                         # Check all health
docker-compose ps                       # Service status
docker stats                            # Resource usage
./run.sh logs                           # View logs
docker-compose logs -f handover-xapp    # Follow specific service
```

### Testing

```bash
./test.sh                               # Run full test suite
make test                               # Using Makefile
docker-compose exec handover-xapp bash  # Interactive shell
```

### Cleanup

```bash
./run.sh clean                          # Full cleanup (destructive!)
docker-compose down -v                  # Remove containers & volumes
docker system prune -a                  # Remove all unused resources
```

**See**: `QUICK-REFERENCE.md` for complete list

## Port Usage

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| Handover xApp | 8080 | HTTP | http://localhost:8080 |
| Power Control xApp | 8081 | HTTP | http://localhost:8081 |
| E2 Termination HTTP | 8082 | HTTP | http://localhost:8082 |
| E2 Termination Protocol | 36421 | TCP | localhost:36421 |
| Redis | 6379 | TCP | localhost:6379 |
| Prometheus | 9090 | HTTP | http://localhost:9090 |

## Service Details

### E2 Termination (`Dockerfile.e2-termination`)
- **Ports**: 36421 (E2), 8082 (HTTP)
- **User**: e2term (non-root)
- **Entry Point**: `python -m e2_ntn_extension.ntn_e2_bridge`
- **Health Check**: TCP port 36421
- **Memory**: 2GB limit, 1GB reservation

### Handover xApp (`Dockerfile.handover-xapp`)
- **Port**: 8080 (HTTP)
- **User**: xapp (non-root)
- **Entry Point**: `python -m xapps.ntn_handover_xapp`
- **Health Check**: HTTP GET /health
- **Memory**: 2GB limit, 1GB reservation

### Power Control xApp (`Dockerfile.power-xapp`)
- **Port**: 8081 (HTTP)
- **User**: xapp (non-root)
- **Entry Point**: `python -m xapps.ntn_power_control_xapp`
- **Health Check**: HTTP GET /health
- **Memory**: 2GB limit, 1GB reservation

### Supporting Services

**Redis** (docker image: redis:7-alpine)
- **Port**: 6379
- **Volume**: redis_data
- **Purpose**: State management, caching

**Prometheus** (docker image: prom/prometheus:latest)
- **Port**: 9090
- **Volume**: prometheus_data
- **Purpose**: Metrics collection, monitoring

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|-----------|
| Startup time | <30s | <60s |
| Health check | <2s | <5s |
| API response | <100ms | <500ms |
| Memory per service | <300MB | <500MB |
| CPU usage at rest | <0.5% | <5% |
| Disk per service | <100MB | <500MB |

## Troubleshooting Quick Links

**Service won't start?**
→ `TROUBLESHOOTING.md` → "Service Startup Issues"

**Can't connect to services?**
→ `TROUBLESHOOTING.md` → "Connectivity Issues"

**Performance problems?**
→ `TROUBLESHOOTING.md` → "Performance Issues"

**Disk space issues?**
→ `TROUBLESHOOTING.md` → "Data and Storage Issues"

**Build failures?**
→ `TROUBLESHOOTING.md` → "Build Issues"

## File Sizes

```
Dockerfiles:
  - Dockerfile.e2-termination:    2KB
  - Dockerfile.handover-xapp:      1.7KB
  - Dockerfile.power-xapp:         1.7KB

Configuration:
  - docker-compose.yml:            4KB
  - prometheus.yml:                2KB
  - .dockerignore:                 <1KB
  - .env.example:                  1KB

Scripts:
  - build.sh:                      4.6KB
  - test.sh:                       6.5KB
  - run.sh:                        3.6KB
  - Makefile:                      8KB

Documentation:
  - README.md:                     ~20KB
  - DEPLOYMENT-GUIDE.md:           ~24KB
  - TROUBLESHOOTING.md:            ~16KB
  - ARCHITECTURE.md:               ~24KB
  - QUICK-REFERENCE.md:            ~12KB
  - TESTING-GUIDE.md:              ~16KB
  - DEPLOYMENT-CHECKLIST.md:       ~16KB
  - DELIVERABLES.md:               ~12KB
  - INDEX.md:                      ~8KB (this file)
```

## Contact and Support

### For Questions About

**Docker Setup**: See `README.md`
**Deployment**: See `DEPLOYMENT-GUIDE.md`
**Troubleshooting**: See `TROUBLESHOOTING.md`
**Architecture**: See `ARCHITECTURE.md`
**Commands**: See `QUICK-REFERENCE.md`
**Testing**: See `TESTING-GUIDE.md`
**Checklist**: See `DEPLOYMENT-CHECKLIST.md`

### Before Deploying to Production

- [ ] Read `DEPLOYMENT-GUIDE.md`
- [ ] Complete `DEPLOYMENT-CHECKLIST.md`
- [ ] Review `ARCHITECTURE.md`
- [ ] Run `./test.sh` successfully
- [ ] Review logs for any errors
- [ ] Verify all health checks passing
- [ ] Document any modifications

## Next Steps

1. **First Time?**
   - Read `README.md` (10 min)
   - Run `./build.sh` (15-30 min)
   - Run `./test.sh` (2 min)
   - Explore with `./run.sh` commands

2. **Ready to Deploy?**
   - Review `DEPLOYMENT-GUIDE.md` (30 min)
   - Complete `DEPLOYMENT-CHECKLIST.md` (15 min)
   - Execute deployment procedures
   - Monitor with `./run.sh logs`

3. **Troubleshooting Needed?**
   - Check `TROUBLESHOOTING.md`
   - Run `./run.sh health`
   - Run `./test.sh`
   - Review `docker-compose logs`

## File Modification Timeline

Created: 2025-11-17

All files are production-ready and documented.

---

**Last Updated**: 2025-11-17
**Status**: Complete
**Ready for**: Development & Production
