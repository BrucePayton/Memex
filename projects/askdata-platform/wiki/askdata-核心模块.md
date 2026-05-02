---
title: "AskData 核心模块"
type: concept
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - modules
  - 核心模块
---

# AskData 核心模块

## 1. AskData 问数分析模块

`core/modules/askdata/` — 自然语言到数据分析的核心模块。

### 主要子模块

- **intent_center** — 意图识别中心，解析用户问题意图
- **preflight_embedding** — 知识库预嵌入处理
- **data_collection** — 数据采集编排
- **analysis** — 分析逻辑编排
- **clarification** — 多轮澄清模块
- **hitl_gates** — 人工确认门控

### 工作流程

```
用户问题 → 意图识别 → 域路由
  ├─ 数据分析: SQL 生成 → 执行 → 结果展示
  ├─ 数据收集: 多源采集 → 格式化
  └─ 深度分析: 计划生成 → Agent 执行 → 报告生成
```

## 2. 数据源模块 (Datasource)

`core/modules/datasource/` — 多数据源连接与管理。

### 支持的数据源

- **PostgreSQL** — 主数据库
- **MySQL** — 通过 aiomysql 异步连接
- **Redis** — 缓存与会话
- **Apache Spark** — 大数据处理
- **TuGraph** — 图数据库

### 核心能力

- ETL 流程管理
- 数据同步调度
- 连接池管理
- Schema 自动发现

## 3. 知识库模块 (Knowledge)

`core/modules/knowledge/` — 文档知识库与 RAG。

- 文档上传与预处理
- 向量化嵌入 (Embedding)
- Chroma/pgvector 向量存储
- RAG 检索增强
- 知识库挂载管理

## 4. 报告模块 (Report)

`core/modules/report/` — 报告生成与管理。

### 报告阶段

```
Stage 1: 数据收集 → Stage 2: 分析 → Stage 3: 内容生成 → Stage 4: 终稿
```

### 支持的格式

- Markdown 文本
- HTML 渲染
- PDF (FPDF2)
- Word (python-docx)
- PPT (python-pptx)

## 5. Dashboard 看板模块

`core/modules/dashboard/` — AI 驱动的数据看板生成。

### 生成组件

- **KPI 卡片** — 关键指标
- **图表** — Plotly/Dash 可视化
- **表格** — 数据表格
- **布局** — 自动排版

### 安全机制

- 静态代码验证 (AST 检查)
- Pre-flight 预加载测试
- HTTP 探针可用性检测

## 6. 用户与权限模块

`core/modules/user/` — 用户管理与认证。

- Keycloak OIDC 认证
- JWT Token 管理
- RBAC 权限控制
- 会话管理 (Redis)
- 审计日志
- 密码策略

## 7. 工作区模块 (Workspace)

`core/modules/workspace/` — 多租户工作空间管理。

## 8. 执行引擎模块 (Executor)

`core/executor/` — 统一工作流执行框架。

- **ComboExecutor**: 多步骤组合执行
- **LayerManager**: 层级任务调度
- **StateAdapter**: 状态转换适配

## 9. 工具池 (Tools Pool)

`resources/tools/` — 可复用工具集合。

- **data tools**: 数据采集、搜索、内容提取
- **analysis tools**: SQL 执行、数据分析
- **collab tools**: 协作原子操作
- **MCP tools**: Model Context Protocol 集成
