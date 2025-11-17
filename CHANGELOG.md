# 变更日志 Changelog

本项目的所有重要变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [3.3.0] - 2025-11-17 - Stage 3: O-RAN整合完成

### 新增 Added
- **E2 Interface完整实现**
  - E2AP协议消息（基于ETSI TS 104 039 V4.0.0）
  - RIC订阅管理
  - RIC指示消息处理
  - RIC控制请求处理
  - E2SM-KPM服务模型
  - 健康监控功能
  - 测试覆盖率：79.47%

- **xApp开发框架**
  - 抽象基类支持xApp开发
  - Async/await异步操作支持
  - E2指示处理接口
  - SDL (Shared Data Layer) 状态管理
  - 生命周期管理 (start, stop, health checks)
  - 配置管理系统
  - 测试覆盖率：95%+

- **示例xApp实现**
  - QoS优化器xApp (174行)
    - UE吞吐量监控（阈值：10.0 Mbps）
    - QoS参数自动调整
    - SDL状态持久化
  - 切换管理器xApp (189行)
    - RSRP监控（阈值：-110 dBm）
    - 小区负载监控（阈值：80%）
    - 智能切换决策逻辑

- **端到端整合测试**
  - 完整SDR→gRPC→DRL→E2→xApp数据流
  - 6个整合测试全部通过
  - 性能验证：66,434 setups/sec

### 改进 Improved
- 整体测试覆盖率达到**82%**
- E2接口性能超越目标**6643%**
- 延迟<0.01ms（超越目标10,000倍）
- 100%测试通过率

### 文档 Documentation
- E2接口架构文档 (19 KB)
- xApp框架设计文档 (15 KB)
- xApp开发指南 (15 KB)
- E2SM-KPM整合指南 (12 KB)

**详细报告**: [docs/reports/stages/STAGE-3-COMPLETION-REPORT.md](docs/reports/stages/STAGE-3-COMPLETION-REPORT.md)

---

## [3.2.0] - 2025-11-17 - Stage 2: mTLS + 监控 + CI/CD

### 新增 Added
- **mTLS双向认证**
  - 客户端证书验证
  - 双向TLS握手
  - 证书链完整验证
  - 零信任架构实施

- **监控和可观测性**
  - Prometheus指标收集
    - 7个关键指标
    - 自动scrape端点
  - Grafana仪表盘
    - 8个可视化面板
    - 实时性能监控
    - 历史数据分析
  - 健康检查端点
  - Liveness/Readiness探针

- **CI/CD自动化**
  - GitHub Actions工作流
    - 代码质量检查（Black, isort, Pylint）
    - 安全扫描（Bandit）
    - 基础设施验证（Terraform）
    - 单元测试执行
    - Docker镜像构建
    - 容器安全扫描（Trivy）
  - 总pipeline时长：~3分钟

- **API Gateway增强测试**
  - 81.29%测试覆盖率
  - 38个测试用例（新增10个）
  - OAuth2/JWT认证测试
  - 站点管理CRUD测试
  - LEO NTN整合测试

- **DRL Trainer增强测试**
  - 50.32%测试覆盖率
  - 26个测试用例（新增7个）
  - RIC环境测试
  - 奖励计算验证
  - Redis SDL整合测试

### 改进 Improved
- 整体测试覆盖率：50% → **67%** (+17%)
- 总测试数：70 → **87** (+17)
- 安全性：TLS → **mTLS** (企业级)
- 可观测性：0% → **80%**
- 自动化：0% → **75%**

### 修复 Fixed
- passlib后端依赖问题
- FastAPI/Starlette版本冲突
- TestClient初始化问题
- RICState规范化测试断言
- Gymnasium vs gym导入兼容性

### 文档 Documentation
- Prometheus监控指南 (8 KB)
- Grafana仪表盘配置 (10 KB)
- CI/CD pipeline文档 (7 KB)
- 监控部署报告 (16 KB)

**详细报告**:
- [docs/reports/stages/STAGE-2-COMPLETION-REPORT.md](docs/reports/stages/STAGE-2-COMPLETION-REPORT.md)
- [docs/reports/agents/AGENT2-FINAL-REPORT.md](docs/reports/agents/AGENT2-FINAL-REPORT.md)
- [docs/reports/agents/AGENT-4-COMPLETION-SUMMARY.md](docs/reports/agents/AGENT-4-COMPLETION-SUMMARY.md)

---

## [3.1.0] - 2025-11-17 - Stage 1: TLS加密 + 测试增强

### 新增 Added
- **TLS加密完整实施**
  - SSL/TLS证书生成（RSA 4096-bit）
    - CA证书和私钥
    - 服务器证书和私钥
    - 客户端证书和私钥
  - gRPC服务器TLS支持
  - gRPC客户端TLS支持
  - TLS连接测试套件（2/2通过）
  - 非加密连接正确拒绝

- **测试基础设施**
  - pytest配置（pytest.ini）
  - 全局fixtures（tests/conftest.py）
  - 覆盖率配置（.coveragerc）
  - 自定义测试标记（unit, integration, grpc, drl, api, slow）

- **gRPC模块测试**
  - 40个测试用例创建
    - 23个单元测试
    - 17个整合测试
  - 100%测试通过率
  - 执行时间：0.32秒

### 改进 Improved
- 测试覆盖率：15% → **44.37%** (+29.37%)
  - sdr_grpc_server.py: **64.39%**
  - ric_state.py: **77.42%**
  - oran_grpc_client.py: **44.07%**
- 安全性：未加密 → **TLS 1.2/1.3**
- 证书强度：无 → **RSA 4096-bit + SHA-256**

### 文档 Documentation
- TLS实施报告 (13 KB)
- TLS快速启动指南 (7.8 KB)
- 证书信息文档
- 测试覆盖率报告 (13 KB)
- 测试指南 (9 KB)

**详细报告**: [docs/reports/stages/STAGE-1-COMPLETION-REPORT.md](docs/reports/stages/STAGE-1-COMPLETION-REPORT.md)

---

## [3.0.0] - 2025-11-17 - Stage 0: 紧急修复

### 修复 Fixed
1. **gRPC Protobuf stubs导入修复**
   - 修正import路径
   - 更新stub生成脚本
   - 验证所有gRPC服务可导入

2. **gRPC测试字段名称修正**
   - 修正Protobuf消息字段命名
   - 更新测试用例以匹配实际schema
   - 确保测试与实现一致

3. **DRL Trainer multiprocessing pickle错误修复**
   - 修正不可pickle的类引用
   - 重构代码以支持多进程
   - 验证DRL训练pipeline可运行

4. **Redis SDL连接问题解决**
   - 配置Redis主机和端口
   - 添加连接重试逻辑
   - 实施健康检查

5. **TLS/mTLS实施指南建立**
   - 创建完整的TLS设置文档
   - mTLS配置步骤
   - 证书生成和管理指南

6. **依赖套件安装指南建立**
   - 核心依赖清单
   - 安装步骤文档
   - 依赖版本兼容性说明

### 改进 Improved
- 项目完成度：70% → **75%**
- 所有阻塞性bug已解决
- 开发环境完全可用

### 文档 Documentation
- 依赖安装指南 (9.5 KB)
- 部署检查清单 (5.1 KB)
- Stage 0修复总结 (14 KB)

**详细报告**: [docs/reports/stages/STAGE-0-FIX-SUMMARY.md](docs/reports/stages/STAGE-0-FIX-SUMMARY.md)

---

## [2.0.0] - 2025-10-26 - 初始研发版本

### 新增 Added
- **MBSE模型**
  - SysML系统架构模型
  - 组件关系图
  - 接口规范

- **SDR平台基础**
  - FastAPI REST服务器 (685行)
  - gRPC双向流式传输 (1,157行)
  - VITA 49.2 VRT协议支持
  - USRP X310硬件抽象层

- **O-RAN整合基础**
  - O-RAN gNB实现 (1,147行)
  - Near-RT RIC架构 (891行)
  - E2, F1, A1, O1接口框架

- **AI/ML Pipeline**
  - DRL训练器 (649行)
    - PPO算法支持
    - SAC算法支持
  - Gymnasium自定义RIC环境
  - Redis SDL状态管理

- **后量子密码学**
  - ML-KEM-1024 (NIST标准)
  - ML-DSA-87签名
  - 混合加密方案（PQC + X25519）

- **编排和部署**
  - Kubernetes清单 (743行)
  - Docker Compose配置
  - Terraform IaC (AWS EKS)

### 文档 Documentation
- 技术白皮书 (95+ markdown文件)
- 架构分析文档
- 系统需求规范
- 接口规范文档

**代码统计**: 6,337行生产Python代码

---

## [0.1.0] - 2023-09 - 研究起始

### 新增 Added
- 初始研究和概念验证
- RunSpace竞赛提交材料
- 文献综述和需求分析

---

## 链接 Links

- [最终项目报告](docs/reports/final/FINAL-PROJECT-COMPLETION-REPORT.md)
- [最终项目状态](docs/reports/final/FINAL-PROJECT-STATUS.md)
- [综合测试覆盖率报告](docs/reports/technical/TEST-COVERAGE-COMPREHENSIVE-REPORT.md)
- [NTN学术价值评估](docs/research/NTN-ACADEMIC-VALUE-ASSESSMENT.md)
- [NTN研究后续步骤](docs/research/NTN-RESEARCH-NEXT-STEPS.md)

---

## 版本说明 Version Notes

### 版本编号规则
- **主版本号 (Major)**: 重大架构变更或不兼容的API变更
- **次版本号 (Minor)**: 新功能添加，向后兼容
- **修订号 (Patch)**: Bug修复和小改进

### 标签说明
- `Added`: 新功能
- `Changed`: 现有功能的变更
- `Deprecated`: 即将移除的功能
- `Removed`: 已移除的功能
- `Fixed`: Bug修复
- `Security`: 安全性修复
- `Documentation`: 文档更新
- `Performance`: 性能改进

---

**维护者**: Hsiu-Chi Tsai (thc1006@ieee.org)
**最后更新**: 2025-11-17
