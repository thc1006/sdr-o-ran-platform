# 🚀 START HERE - Automated Deployment Guide

## ⚡ Quick Start (5 Minutes)

Your SDR-O-RAN platform is **ready for automated deployment**!

### Option 1: One-Command Full Deployment ⭐ **RECOMMENDED**

```bash
# In WSL terminal:
cd ~/dev/sdr-o-ran-platform
bash scripts/auto-deploy.sh
```

This will automatically:
- ✅ Set up WSL environment
- ✅ Build all 4 Docker containers
- ✅ Deploy complete stack
- ✅ Run end-to-end tests
- ✅ Generate deployment report

**Duration**: 30-45 minutes (mostly automated build time)

---

### Option 2: Manual Step-by-Step

If you prefer to control each step:

#### Step 1: Copy Project to WSL

```powershell
# In PowerShell:
wsl
```

```bash
# In WSL:
mkdir -p ~/dev
cp -r /mnt/c/Users/ict/OneDrive/桌面/dev/sdr-o-ran-platform ~/dev/
cd ~/dev/sdr-o-ran-platform
```

#### Step 2: Build Containers

```bash
docker-compose build
```

#### Step 3: Start Services

```bash
docker-compose up -d
```

#### Step 4: Test Everything

```bash
bash scripts/test-all.sh
```

---

## 📊 Access Your Platform

Once deployed, access these services:

| Service | URL | Description |
|---------|-----|-------------|
| **SDR API** | http://localhost:8000 | Main REST API |
| **Swagger UI** | http://localhost:8000/docs | Interactive API docs |
| **Metrics** | http://localhost:8000/metrics | Prometheus metrics |
| **TensorBoard** | http://localhost:6006 | DRL training visualization |
| **gRPC** | localhost:50051 | IQ streaming service |

---

## 🎯 What Gets Deployed

### Container 1: LEO NTN Simulator (GPU)
- 🛰️ Simulates LEO satellite at 600km altitude
- 📡 Generates IQ samples with Doppler & fading
- 🎮 Uses RTX 2060 GPU for acceleration
- 📤 Streams via ZMQ on port 5555

### Container 2: SDR Gateway
- 📡 FastAPI server on port 8000
- 🔗 gRPC server on port 50051
- 📊 Prometheus metrics
- 🔒 OAuth2 authentication ready

### Container 3: DRL Trainer (GPU)
- 🤖 PPO algorithm training
- 🎮 GPU-accelerated (RTX 2060)
- 📈 TensorBoard on port 6006
- 💾 Model checkpoints saved

### Container 4: FlexRIC RIC
- 🌐 Near-RT RIC with E2 interface
- 🔧 Assertion fix applied
- 📡 E2 ports: 36421, 36422
- 🧠 Ready for xApp integration

---

## 🛠️ Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f leo-simulator
docker-compose logs -f sdr-gateway
docker-compose logs -f drl-trainer
docker-compose logs -f flexric
```

### Monitor Resources
```bash
# Real-time dashboard
bash scripts/monitor.sh

# Quick status
docker-compose ps

# GPU usage
nvidia-smi
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart one
docker-compose restart sdr-gateway
```

### Stop Everything
```bash
bash scripts/stop-all.sh
# or
docker-compose down
```

---

## 🐛 Troubleshooting

### GPU Not Detected

```bash
# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# If fails, restart Docker Desktop and enable GPU support
```

### Container Won't Start

```bash
# Check logs
docker-compose logs [container-name]

# Rebuild specific container
docker-compose build [container-name]
docker-compose up -d [container-name]
```

### Port Already in Use

```bash
# Check what's using port
netstat -ano | findstr :8000

# Stop conflicting service or change port in docker-compose.yml
```

---

## 📈 Expected Resource Usage

| Container | CPU | RAM | GPU VRAM | Notes |
|-----------|-----|-----|----------|-------|
| LEO Simulator | 20-40% | 2-3GB | 1-2GB | GPU accelerated |
| SDR Gateway | 5-10% | 500MB | - | REST + gRPC |
| DRL Trainer | 30-50% | 1-2GB | 2-3GB | Training active |
| FlexRIC | 5-10% | 300MB | - | Lightweight |
| **Total** | **60-110%** | **4-6GB** | **3-5GB** | Peak usage |

With RTX 2060 (6GB VRAM), you have sufficient resources!

---

## 📝 Files Created

All necessary files have been created:

```
sdr-o-ran-platform/
├── docker-compose.yml              ✅ Main orchestration
├── 03-Implementation/
│   ├── simulation/
│   │   └── Dockerfile.leo-simulator    ✅ LEO NTN container
│   ├── sdr-platform/
│   │   └── Dockerfile.sdr-gateway      ✅ SDR services
│   └── ai-ml-pipeline/
│       └── Dockerfile.drl-trainer      ✅ DRL training
├── 04-Deployment/docker/
│   └── Dockerfile.flexric              ✅ FlexRIC RIC
├── scripts/
│   ├── auto-deploy.sh              ✅ Full automation
│   ├── quick-start.sh              ✅ Quick start
│   ├── stop-all.sh                 ✅ Stop services
│   ├── test-all.sh                 ✅ Test suite
│   └── monitor.sh                  ✅ Monitoring
├── DEPLOYMENT-WSL2-GPU.md          ✅ Detailed guide
└── START-HERE.md                   ✅ This file
```

---

## 🎓 Next Steps After Deployment

1. **Verify Deployment**
   ```bash
   bash scripts/test-all.sh
   ```

2. **Monitor Training**
   - Open http://localhost:6006 (TensorBoard)
   - Watch loss curves and rewards

3. **Test APIs**
   - Open http://localhost:8000/docs
   - Try out endpoints

4. **Collect Data**
   - Let system run for hours/days
   - Gather metrics for research

5. **Write Papers**
   - Use collected data
   - Generate plots and analysis

---

## ⏰ Deployment Timeline

- **Automated deployment**: 30-45 min (build time)
- **Manual deployment**: 1-2 hours (if you follow steps)
- **First results**: Available immediately after deployment
- **Training convergence**: 2-24 hours (depending on timesteps)

---

## 😴 Sleep Mode Deployment

Since you're going to sleep, the **auto-deploy.sh** script will:

1. ✅ Run completely unattended
2. ✅ Generate detailed logs
3. ✅ Create deployment report
4. ✅ Keep containers running
5. ✅ Monitor in background

When you wake up:
- Check `DEPLOYMENT-REPORT-*.md` for results
- Check `/tmp/sdr-oran-deployment-*.log` for details
- Open http://localhost:8000 to access API
- Open http://localhost:6006 to see training progress

---

## 🚀 Ready to Deploy!

**Execute this now**:

```bash
wsl
cd ~/dev/sdr-o-ran-platform
bash scripts/auto-deploy.sh
```

Then go to sleep! 😴

The script will complete everything and your platform will be running when you wake up! 🌅

---

**Good night! Sweet dreams of satellites and neural networks! 🛰️🤖💤**
