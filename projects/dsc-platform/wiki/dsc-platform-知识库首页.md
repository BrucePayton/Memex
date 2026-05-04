---
title: "DSC Platform 知识库首页"
type: overview
created: 2026-05-03
last_updated: 2026-05-03
source_count: 0
confidence: medium
status: active
tags:
  - 首页
  - 导航
  - 概述
---

# DSC Platform 知识库

欢迎使用DSC Platform（Data Supply Chain Platform）知识库。DSC Platform是一个专为生成式AI应用打造的全链路数据平台，提供数据接入、文档处理、知识库管理、向量检索、流程编排等核心能力，帮助企业快速搭建AI应用。

## 📚 文档导航

### 快速入门
- [项目概述](./dsc-platform-项目概述.md) - 了解平台的核心功能、技术栈和应用场景
- [部署指南](./部署文档/部署指南.md) - 快速部署平台到本地或生产环境
- [API 总览与使用规范](./API文档/api-总览与使用规范.md) - 了解API的使用方式和规范

### 核心模块
- [agent_flow 智能体流程编排模块](./模块说明/agent-flow-智能体流程编排模块.md) - 低代码流程编排引擎，支持复杂工作流和AI Agent开发
- [knowledge_mgt 知识库管理模块](./模块说明/knowledge-mgt-知识库管理模块.md) - 多格式文档处理、知识库全生命周期管理
- [vectors_mgt 向量管理模块](./模块说明/vectors-mgt-向量管理模块.md) - 向量嵌入、存储、检索全链路能力
- [db_mgt 数据库管理模块]() - 多数据源接入、SQL查询和分析能力（待完善）
- [flow_mgt 流程管理模块]() - 工作流定义、执行和应用市场（待完善）

### 开发相关
- [开发指南](./开发指南/开发指南.md) - 二次开发、功能扩展的详细指南
- [API 参考文档]() - 所有API接口的详细说明（待完善）
- [SDK 使用文档]() - 多语言SDK的使用说明（待完善）

### 运维相关
- [部署指南](./部署文档/部署指南.md) - 多种部署方式的详细说明
- [监控与运维指南]() - 系统监控、运维和故障排查（待完善）
- [性能优化指南]() - 性能调优最佳实践（待完善）
- [安全规范]() - 安全配置和最佳实践（待完善）

### 其他
- [常见问题FAQ](./常见问题/常见问题FAQ.md) - 常见问题解答
- [版本更新日志]() - 各版本的更新内容说明（待完善）
- [贡献指南]() - 参与项目贡献的指南（待完善）

## 🚀 核心特性

### 1. 多源数据接入
- 支持PDF、Word、Excel、PPT、图片、文本等20+种文档格式
- 支持关系型数据库、NoSQL数据库、API等多数据源接入
- 支持批量导入、实时同步、Webhook等多种接入方式

### 2. 智能文档处理
- 集成PaddleOCR，支持中英文和表格识别
- 智能文档解析，自动提取元数据、结构、内容
- 多种分块策略，支持语义分块、结构化分块
- 支持自定义解析规则和处理流程

### 3. 高性能向量检索
- 支持Weaviate、Milvus、Chroma等主流向量数据库
- 集成OpenAI、千问、智谱、BGE等多种嵌入模型
- 支持向量检索、全文检索、混合检索多种检索方式
- 支持检索结果重排序、上下文扩展等高级特性
- 支持千亿级向量毫秒级检索

### 4. 低代码流程编排
- 可视化流程设计器，拖拽式操作
- 丰富的内置节点库，覆盖常见数据处理和AI能力
- 支持自定义节点扩展，满足个性化需求
- 支持流程版本管理、调试、监控
- 内置流程模板市场，快速搭建常见业务流程

### 5. 企业级特性
- 多租户隔离，支持组织和权限管理
- 完善的安全审计和操作日志
- 高可用分布式架构，支持水平扩展
- 完整的监控和告警体系
- 支持私有化部署和云原生部署

## 🛠️ 技术栈

| 技术/组件 | 用途 | 版本要求 |
|----------|------|----------|
| Python 3.11 | 开发语言 | 3.11+ |
| FastAPI | Web框架 | 0.100+ |
| Pydantic | 数据验证 | 2.0+ |
| SQLAlchemy | ORM框架 | 2.0+ |
| PostgreSQL/MySQL | 关系型数据库 | PostgreSQL 13+ / MySQL 8.0+ |
| Redis | 缓存和消息队列 | 6.0+ |
| Weaviate/Milvus | 向量数据库 | Weaviate 1.23+ / Milvus 2.3+ |
| Celery | 异步任务队列 | 5.3+ |
| PaddleOCR | OCR识别 | 2.7+ |
| LangChain | LLM应用框架 | 0.1.0+ |
| Docker/Kubernetes | 容器化部署 | Docker 20+ / Kubernetes 1.24+ |

## 📋 版本信息

- **当前稳定版本**：v1.0.0
- **发布日期**：2024-01-01
- **更新日志**：[查看版本更新历史]()

## 🤝 社区与支持

### 文档反馈
如果发现文档有错误或有改进建议，可以提交Issue或PR。

### 问题反馈
- GitHub Issues：[提交问题](https://github.com/your-org/dsc-platform/issues)
- 邮件支持：support@dsc-platform.com
- 社区Discord：[加入讨论](https://discord.gg/dsc-platform)

### 贡献代码
欢迎参与项目贡献，具体可以查看[贡献指南]()。

## 🔗 相关链接

- [官方网站](https://dsc-platform.com)
- [GitHub 仓库](https://github.com/your-org/dsc-platform)
- [API 文档](https://api.dsc-platform.com/docs)
- [演示环境](https://demo.dsc-platform.com)

---

> 最后更新：2024年01月01日
