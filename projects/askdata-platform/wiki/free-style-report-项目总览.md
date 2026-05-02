---
title: "Free-Style-Report 项目总览"
type: concept
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - 项目总览
  - architecture
---

# Free-Style-Report (AskData Platform) 项目总览

`Free-Style-Report`（亦称 **AskData Platform**）是一个基于生成式 AI 的数据分析与报告生成平台。它通过动态构建 **数据链、分析链和生成链**，实现按需、自适应的深度报告生成。

## 核心定位

- **智能问数分析平台**：用户用自然语言提问，系统自动理解意图、查询数据、分析结果并生成报告
- **动态数据链**：自动采集、处理和链接多数据源数据
- **智能分析链**：AI 驱动的分析推理，支持多层级推理
- **生成式报告链**：LLM 自动生成结构化报告，支持自定义格式化

## 关键特性

| 特性 | 描述 |
|------|------|
| 问数分析 (AskData) | 自然语言到 SQL，自动数据查询与分析 |
| 智能报告生成 | 从数据自动生成分层报告（收入分析、商业分析等） |
| Dashboard 可视化 | AI 生成的交互式数据看板（KPI、图表、表格） |
| 知识库管理 | 文档上传、向量化、RAG 检索增强 |
| 多数据源支持 | PostgreSQL、MySQL、Redis 等，支持 ETL |
| 多轮澄清 | 自动识别模糊问题，主动追问澄清 |
| MCP 工具集成 | 支持 Model Context Protocol 工具扩展 |
| 工作流编排 | 基于 LangGraph 的多阶段状态机工作流 |

## 项目结构概览

```
free-style-report/
├── apps/              # 应用入口 (orchestrator_app)
├── assets/            # 模板资源 (agent/prompt/graph/task templates)
├── configs/           # 配置管理 (llm/db/auth/dashboard 等)
├── core/              # 核心模块
│   ├── executor/      # 执行引擎 (combo/unified executor)
│   ├── helpers/       # 辅助工具 (graph/db/prompt helpers)
│   ├── middlewares/   # 中间件 (auth/exception/logging)
│   ├── models/        # 数据模型
│   ├── modules/       # 业务模块 (askdata/datasource/knowledge/user...)
│   └── server/        # FastAPI 服务 (routers/API endpoints)
├── graphs/            # LangGraph 工作流定义
│   ├── nodes/         # 节点实现 (analysis/data/content/askdata)
│   └── sub_graphs/    # 子图 (analysis/basic/collab)
├── resources/         # 资源管理
│   ├── agents/        # Agent 定义 (report/creator/middle agents)
│   └── tools/         # 工具池 (data/analysis/collation)
├── web/               # React 前端 (Vite + TypeScript)
├── deployments/       # Docker Compose 部署配置
├── storage/           # 存储 (PostgreSQL + Redis)
├── utils/             # 通用工具
└── tests/             # 测试
```

## 主要应用场景

- **商业智能**：自动市场/竞品分析
- **财务分析**：实时财务报表与洞察
- **数据查询**：自然语言问数，自动 SQL 生成
- **报告生成**：按数据自动生成分析报告
- **知识管理**：文档知识库 + RAG 检索
