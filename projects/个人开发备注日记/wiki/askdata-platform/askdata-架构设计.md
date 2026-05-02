---
title: "AskData 架构设计"
type: concept
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - architecture
  - langgraph
  - 工作流
---

# AskData 架构设计

## 整体架构

AskData Platform 采用 **分层架构 + Agent 编排** 的设计模式，核心围绕 LangGraph 状态图构建多阶段工作流。[^src-02-structure]

```
┌─────────────────────────────────────────────────────┐
│                   Web Frontend (React)               │
│  Vite + TypeScript + TailwindCSS + Dash Components   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Gateway (Port 8000)             │
│  CORS → Auth Middleware → Route Handlers             │
│  ├── /api/chat (SSE streaming)                       │
│  ├── /api/askdata/* (问数分析)                       │
│  ├── /api/dashboard/* (看板管理)                     │
│  ├── /api/knowledge/* (知识库)                       │
│  ├── /api/datasource/* (数据源)                      │
│  └── /api/report/* (报告)                            │
└──┬─────────┬──────────┬──────────┬──────────┬───────┘
   │         │          │          │          │
┌──▼──┐  ┌───▼───┐  ┌──▼───┐  ┌──▼───┐  ┌───▼───┐
│Lang │  │Postge │  │Redis │  │Key-  │  │Ext    │
│Graph│  │sqlDB  │  │Cache │  │cloak │  │Svcs   │
│Orch │  │       │  │      │  │Auth  │  │DSC/Dif│
│estr │  │       │  │      │  │      │  │y/Sbx  │
└─────┘  └───────┘  └──────┘  └──────┘  └───────┘
```

## LangGraph 工作流引擎

核心图定义在 `graphs/builder.py`，采用 **StateGraph** 模式：[^src-03-builder]

### 主工作流节点

```
START → session_bootstrap
       ├─→ intent_agent (意图识别)
       │   └─→ orchestrator_domain_routing (域路由)
       │       ├─→ askdata_decision_shell (决策壳)
       │       │   └─→ 多轮澄清/重路由
       │       └─→ askdata_orchestrator_branch (编排分支)
       │           ├─→ askdata_policy_end (直接结束)
       │           ├─→ supper_dispatch (短路径调度)
       │           ├─→ askdata_artifact_preflight (预检)
       │           └─→ askdata_routing_hitl (人工确认)
       └─→ askdata_sql_artifact_replay (SQL 结果回放)
```

### 长路径 (Deep Path)

```
askdata_artifact_preflight → route_after_artifact_preflight
  ├─→ background_investigator (背景调研)
  │   └─→ planner (规划器)
  │       └─→ orchestrator_delegate_managers (委派管理器)
  │           └─→ create_manager_agent (创建代理 Agent)
  │               └─→ human_feedback (人工反馈)
  │                   └─→ askdata_implicit_replan_gate (隐式重规划)
  │                       └─→ 循环回 planner 或 exit
  └─→ planner
```

### 关键节点说明

| 节点 | 职责 |
|------|------|
| `session_bootstrap` | 会话初始化，识别问数意图 vs 普通对话 |
| `intent_agent` | 意图识别与分类 |
| `orchestrator_domain_routing` | 域路由（数据分析/数据收集/内容生成） |
| `askdata_decision_shell` | 决策壳，含模糊澄清、多轮追问 |
| `supper_dispatch` | 短路径快速调度（简单 QA 直接返回） |
| `askdata_artifact_preflight` | 预检节点，决定是否需要深度分析 |
| `background_investigation_node` | 背景信息调研 |
| `planner_node` | 数据收集+分析计划生成 |
| `create_manager_agent_node` | 创建领域专用 Agent（Collection/Format） |
| `askdata_session_wrapup` | 会话收尾，保存状态到 checkpoint |

## 执行引擎

`core/executor/` 提供统一执行框架：[^src-04-executor]

- **BaseExecutor** - 基础执行器抽象
- **ComboExecutor** - 组合执行器，支持多步骤编排
- **UnifiedExecutor** - 统一执行接口
- **LayerManager** - 层级管理器
- **StateAdapter** - 状态适配器

## Agent 分层架构

```
Orchestrator (编排层)
  ├─→ Creator Manager (创建管理层)
  │     ├─→ Collection Agent (数据采集 Agent)
  │     └─→ Format Agent (数据格式化 Agent)
  ├─→ Middle Agent (中间层)
  │     └─→ SQL Agent (SQL 生成与执行)
  └─→ Report Agent (报告层)
        ├─→ Basic Report Agent
        ├─→ Advanced Report Agent
        └─→ Final Report Agent
```

## 部署架构

Docker Compose 多服务部署：[^src-05-deploy]

- **app** - FastAPI 后端 + Web 前端
- **PostgreSQL** - 主数据库
- **Redis** - 缓存与会话存储
- **Keycloak** - 身份认证
- **Langfuse** - LLM 可观测性
- **Nginx** - 反向代理
- **Dashboard Server** - Dash 应用宿主 (port 8088)
- **Report App Server** - 报告预览 (port 9980)

[^src-02-structure]: [project_structure.txt](https://github.com/BrucePayton/free-style-report/project_structure.txt)
[^src-03-builder]: `graphs/builder.py`
[^src-04-executor]: `core/executor/`
[^src-05-deploy]: `deployments/deployment_local/`
