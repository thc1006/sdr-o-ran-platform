# 快速启动指南 Quick Start Guides

本目录包含不同部署场景的快速启动指南，帮助用户在最短时间内运行SDR-O-RAN平台。

---

## 📁 可用指南 Available Guides

### 1. Docker快速启动 (推荐新手)
**文件**: [QUICK-START-DOCKER.md](QUICK-START-DOCKER.md)
**部署时间**: 5-10分钟
**难度**: ⭐ 简单
**适用场景**: 本地开发、测试、演示

**特点**:
- ✅ 一键自动化部署
- ✅ GPU加速支持（可选）
- ✅ 适合Windows (WSL2) / Linux / macOS
- ✅ 最小资源需求：16GB RAM, 4核CPU

**部署内容**:
```
Docker容器：
├── LEO NTN Simulator (GPU加速)
├── SDR Gateway (REST API + gRPC)
├── DRL Trainer (GPU加速)
└── FlexRIC (Near-RT RIC)
```

**快速命令**:
```bash
cd ~/dev/sdr-o-ran-platform
bash scripts/auto-deploy.sh
```

**访问服务**:
- SDR API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- TensorBoard: http://localhost:6006
- gRPC: localhost:50051

---

### 2. Kubernetes快速启动 (推荐生产环境)
**文件**: [QUICK-START-KUBERNETES.md](QUICK-START-KUBERNETES.md)
**部署时间**: 10-15分钟
**难度**: ⭐⭐⭐ 中等
**适用场景**: 生产部署、高可用、自动扩展

**特点**:
- ✅ 生产级高可用部署
- ✅ 自动扩展和故障恢复
- ✅ Prometheus + Grafana监控
- ✅ 负载均衡和服务发现

**部署内容**:
```
Kubernetes组件：
├── Redis集群 (3副本, 10Gi/节点)
├── Prometheus + Grafana监控
├── E2 Interface (3副本)
├── xApps (QoS + Handover, 2副本各)
├── gRPC Server (3副本 + LoadBalancer)
└── 网络策略和RBAC
```

**快速命令**:
```bash
cd 04-Deployment/kubernetes
./deploy-all.sh
```

**验证部署**:
```bash
kubectl get pods -n sdr-oran
kubectl get svc -n sdr-oran
```

---

## 🎯 选择合适的指南

### 我应该选择哪个？

| 需求 | Docker指南 | Kubernetes指南 |
|------|-----------|---------------|
| 快速测试/演示 | ✅ **推荐** | ⚠️ 过度 |
| 本地开发 | ✅ **推荐** | ⚠️ 过度 |
| 学习O-RAN | ✅ **推荐** | ✅ 可选 |
| 生产部署 | ⚠️ 不推荐 | ✅ **推荐** |
| 高可用需求 | ❌ 不支持 | ✅ **推荐** |
| 自动扩展 | ❌ 不支持 | ✅ **推荐** |
| GPU加速 | ✅ 支持 | ⭐ 复杂配置 |
| 简单性 | ⭐ 最简单 | ⭐⭐⭐ 中等 |

**建议流程**:
1. **初学者/开发者**: 先用Docker指南快速上手
2. **理解架构后**: 可选择性尝试Kubernetes指南
3. **生产部署**: 使用Kubernetes指南并参考完整部署文档

---

## 📋 前置要求对比

### Docker部署

**必需**:
- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM
- 4核CPU

**可选（用于GPU加速）**:
- NVIDIA GPU (如RTX 2060+)
- NVIDIA Docker runtime
- CUDA 12.0+

**操作系统**:
- ✅ Linux (Ubuntu 20.04+)
- ✅ Windows 10/11 (WSL2)
- ✅ macOS (Docker Desktop)

---

### Kubernetes部署

**必需**:
- Kubernetes集群 (v1.27+)
- kubectl (v1.27+)
- 3个节点，每个：
  - 32GB RAM
  - 8核CPU
  - 1TB SSD

**可选（用于完整功能）**:
- LoadBalancer服务（云环境）
- Persistent Volume支持
- GPU节点（用于DRL训练）

**操作系统**:
- ✅ Linux (推荐 Ubuntu 22.04 Server)
- ✅ 云平台 (AWS EKS, GCP GKE, Azure AKS)

---

## ⚡ 快速对比表

| 特性 | Docker | Kubernetes |
|------|--------|-----------|
| **部署时间** | 5-10分钟 | 10-15分钟 |
| **资源需求** | 低 (16GB RAM) | 高 (96GB+ 总计) |
| **复杂度** | 简单 | 中等 |
| **扩展性** | 单机 | 多节点 |
| **高可用** | ❌ | ✅ |
| **监控** | 基础 | 完整 (Prometheus + Grafana) |
| **适合场景** | 开发/测试 | 生产 |
| **成本** | 极低 | 中高 |

---

## 🚀 部署后的下一步

### 1. 验证部署
**Docker**:
```bash
# 检查容器状态
docker-compose ps

# 测试API
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

**Kubernetes**:
```bash
# 检查Pod状态
kubectl get pods -n sdr-oran

# 获取服务端点
kubectl get svc -n sdr-oran

# 查看Grafana
kubectl port-forward -n sdr-oran svc/grafana-service 3000:3000
```

---

### 2. 运行测试
```bash
# 运行所有测试
./scripts/test-all.sh

# 运行特定测试
pytest tests/unit/ -v
pytest tests/integration/ -v
```

---

### 3. 访问监控
**Docker**:
- TensorBoard: http://localhost:6006

**Kubernetes**:
- Prometheus: http://<PROMETHEUS_IP>:9090
- Grafana: http://<GRAFANA_IP>:3000
  - 用户名: admin
  - 密码: admin12345

---

### 4. 查看日志
**Docker**:
```bash
docker-compose logs -f sdr-gateway
docker-compose logs -f leo-simulator
docker-compose logs -f drl-trainer
```

**Kubernetes**:
```bash
kubectl logs -f deployment/e2-interface -n sdr-oran
kubectl logs -f deployment/xapp-qos-optimizer -n sdr-oran
kubectl logs -f deployment/sdr-grpc-server -n sdr-oran
```

---

## 📚 深入学习资源

### 完整文档
- [完整部署指南](../deployment/DEPLOYMENT-GUIDE.md) - 详细的部署说明
- [WSL2 GPU设置](../deployment/DEPLOYMENT-WSL2-GPU.md) - Windows GPU支持
- [部署检查清单](../deployment/CHECKLIST.md) - 部署验证清单

### 技术文档
- [架构文档](../architecture/) - 系统架构设计
- [API文档](../../03-Implementation/sdr-platform/api-gateway/) - REST API规范
- [E2接口文档](../../03-Implementation/ric-platform/e2-interface/) - O-RAN E2接口

### 测试和验证
- [测试指南](../testing/TESTING-GUIDE.md) - 如何运行测试
- [测试覆盖率报告](../reports/technical/TEST-COVERAGE-COMPREHENSIVE-REPORT.md)

---

## 🔧 常见问题 FAQ

### Docker部署

**Q: GPU加速不工作？**
A: 确保安装了NVIDIA Docker runtime并配置了GPU支持。参考WSL2 GPU设置文档。

**Q: 端口冲突？**
A: 修改`docker-compose.yml`中的端口映射。默认端口：8000 (API), 50051 (gRPC), 6006 (TensorBoard)。

**Q: 容器启动失败？**
A: 检查日志：`docker-compose logs <service-name>`

---

### Kubernetes部署

**Q: Pod处于Pending状态？**
A: 检查资源是否足够：`kubectl describe pod <pod-name> -n sdr-oran`

**Q: 无法访问服务？**
A: 确保LoadBalancer或NodePort正确配置：`kubectl get svc -n sdr-oran`

**Q: Persistent Volume问题？**
A: 检查StorageClass是否可用：`kubectl get sc`

---

## 🔗 相关链接

- [项目主README](../../README.md)
- [变更日志](../../CHANGELOG.md)
- [最终项目报告](../reports/final/FINAL-PROJECT-COMPLETION-REPORT.md)
- [依赖安装指南](../deployment/DEPENDENCY-GUIDE.md)

---

## 📞 获取帮助

### 文档资源
1. 首先查阅本目录的快速启动指南
2. 参考完整的部署指南
3. 查看已知问题列表：[docs/testing/KNOWN-ISSUES.md](../testing/KNOWN-ISSUES.md)

### 社区支持
- GitHub Issues: [项目Issues页面]
- Email: thc1006@ieee.org

---

**最后更新**: 2025-11-17
**维护者**: Hsiu-Chi Tsai (thc1006@ieee.org)
**项目版本**: 3.3.0
