---
title: "AskData 组织概念分析与 Projects 概念适配"
type: analysis
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - workspace
  - projects
  - architecture
  - 分析
---

# AskData 组织概念分析与 Projects 概念适配

## 一、AskData 现有组织模型

### 核心实体关系

```
User / Team / Org (组织层，Keycloak 集成)
  │
  └─→ WorkSpace (问数空间) ← 顶层容器
        │
        ├─→ Resource Mount (资源挂载)
        │     ├─ knowledge_base (知识库)
        │     ├─ database (数据源)
        │     └─ agent_app (Agent 应用)
        │
        ├─→ Production Artifacts (生产成果)
        │     ├─ SQL snippets
        │     ├─ Dashboards
        │     ├─ Reports
        │     └─ Chain Snapshots (链路快照)
        │
        ├─→ Chain Templates (领域模板)
        │     └─ 预建的领域分析模板 (DSC YAML)
        │
        ├─→ Chat Sessions (会话历史)
        │
        └─→ Applications (应用，遗留概念，子级)
```

### WorkSpace 的核心属性

| 属性 | 说明 | 对应 Memex |
|------|------|-----------|
| `name, desc, owner` | 名称、描述、所有者 | Project slug/title |
| `visibility` | public/team/org 三级可见性 | 无 (Memex 无多租户) |
| `linked_team_uuids` | 团队级访问控制 | 无 |
| `org_scope_unified_group_id` | 组织级访问控制 | 无 |
| `askdata_analysis_read_apps` | 分析能力配置 | 类似 template |
| `tags` | 标签 (JSONB) | 类似 folder 分类 |

### 问数空间的能力范围

从 `session_outcome_goals` 可看出一个 WorkSpace 提供的能力：

| 能力 | 说明 |
|------|------|
| `knowledge_qa` | 知识库问答 |
| `data_qa` | 数据问答 |
| `data_analysis` | 数据分析 |
| `dashboard` | 看板生成 |
| `report` | 报告生成 |

### 链路工作台 (ChainSnapshot / ChainTemplate)

| 概念 | 说明 |
|------|------|
| `ChainSnapshot` | 捕获一次问答会话的执行链路为 DSC YAML，可发布、可重放 |
| `ChainTemplate` | 预建的领域分析模板，支持关键词匹配和触发 |
| `ProductionArtifact` | Workspace 级共享资产，支持版本化 (lineage_root_id + version_seq) |

### 外部资源管理

| 资源类型 | 注册方式 | 挂载方式 |
|----------|---------|---------|
| knowledge_base | DSC/Dify 外部服务注册 | `t_workspace_resource_mount` |
| database | `t_datasource` | `t_workspace_resource_mount` |
| agent_app | 外部 Agent 注册 | `t_workspace_resource_mount` |
| external_agent | `t_external_resource_registration` | 挂载到 Workspace |
| mcp_server | `t_external_resource_registration` | 挂载到 Workspace |
| dsc_workflow | `t_external_resource_registration` | 挂载到 Workspace |

## 二、Projects 概念引入的冲突分析

### 冲突 1: 概念重叠

| Memex Project | AskData WorkSpace | 重叠度 |
|---------------|-------------------|--------|
| slug (唯一标识) | workspace uuid | 100% |
| title + description | name + desc | 100% |
| wiki/ 页面目录 | 问答会话 + 生产成果 | 60% |
| raw/ 不可变源 | 知识库文档 | 80% |
| CLAUDE.md | askdata_analysis_read_apps | 40% |
| 项目级 LLM model 配置 | 无对应 (全局配置) | 可扩充 |

**结论**：WorkSpace 已经承担了 Project 的角色。引入 "Project" 概念会与 WorkSpace 完全重叠。

### 冲突 2: 命名歧义

AskData 代码中已经存在 `Application` 实体，在 API 中被引用为 "project"：
```python
# WorkSpaceHelper.get_project_by_workspace()  # 查询 Application 作为 "project"
```

如果再引入 "Project"，系统中将出现三层命名歧义：
```
Project (新概念)
  └─ Application (旧概念，也叫 project)
      └─ WorkSpace (问数空间)
```

### 冲突 3: 多租户维度

Memex 的 Project 是单租户的（每个项目独立存放），而 AskData 的 WorkSpace 有三级可见性：

| 可见性 | 说明 | Memex 无对应 |
|--------|------|-------------|
| public | 所有人可访问 | 无 |
| team | 团队成员可访问 | 无 |
| org | 组织成员可访问 | 无 |

引入 "Project" 会破坏现有的多租户模型。

## 三、正确理解：概念映射而非概念引入

### 不应引入，而应映射

| Memex 概念 | AskData 对应 | 说明 |
|------------|-------------|------|
| **Project** | **WorkSpace** | 问数空间 = 项目容器 |
| **slug** | **workspace uuid** | 唯一标识 |
| **wiki/** | **Chat Sessions + Production Artifacts** | 内容产出 |
| **raw/** | **Knowledge Base Documents** | 不可变源文档 |
| **CLAUDE.md** | **askdata_analysis_read_apps 配置** | 项目级指令 |
| **templates/** | **Chain Templates** | 领域模板 |
| **ingest-reports/** | **Chain Snapshots** | 执行链路记录 |
| **projects.json** | **WorkSpace CRUD API** | 注册表 |

### Memex 模式在 AskData 的适配

| Memex 做法 | AskData 适配方案 |
|-----------|-----------------|
| 创建 Project | 创建 WorkSpace (已有 API) |
| 切换 Project | 切换 WorkSpace (已有 API) |
| `cwd=project.root` | `workspace_id` 参数限定上下文 |
| Project 级 CLAUDE.md | WorkSpace 级资源挂载配置 |
| `raw/` 不可变源 | Knowledge Base 文档 (已不可变) |
| Project 级 model 配置 | WorkSpace 级 LLM 配置扩展 |
| `wiki/log.md` | 会话历史 + Chain Snapshots |

## 四、Claw-Code 集成：基于 WorkSpace 而非 Projects

### 核心思路

Claw-Code 集成到 AskData **不需要引入 Projects 概念**，而是：

1. **开发层**：AskData 本身是一个 git repo，Claw-Code 直接操作代码
2. **运行时层**：Claw-Code 通过 WorkSpace API 管理开发任务

### 三层隔离模型

```
┌──────────────────────────────────────────────────────────┐
│                  开发层 (Development)                      │
│  ┌──────────────────────────────────────────────────┐    │
│  │  AskData Codebase (free-style-report/)           │    │
│  │  ├── CLAUDE.md                                   │    │
│  │  ├── .claw/                                      │    │
│  │  └── 所有 AskData 源码                            │    │
│  └──────────────────────────────────────────────────┘    │
│         │ 操作代码                                        │
│  ┌──────▼──────┐                                        │
│  │ Claw-Code   │                                        │
│  │ Worker(s)   │                                        │
│  └─────────────┘                                        │
└──────────────────────────────────────────────────────────┘
         │ 通过 API 管理
┌──────────────────────────────────────────────────────────┐
│                  运行时层 (Runtime)                        │
│  ┌──────────────────────────────────────────────────┐    │
│  │  WorkSpace A (财务部)                             │    │
│  │  ├── knowledge_base: 财务报表KB                   │    │
│  │  ├── database: 财务数据库                         │    │
│  │  ├── agent_app: 收入分析Agent                     │    │
│  │  ├── chain_templates: 财务分析模板                │    │
│  │  └── sessions: 问答历史                           │    │
│  └──────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │  WorkSpace B (市场部)                             │    │
│  │  ├── knowledge_base: 市场报告KB                   │    │
│  │  ├── database: 市场数据库                         │    │
│  │  └── ...                                         │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
         │ 链路成果化
┌──────────────────────────────────────────────────────────┐
│                  成果层 (Artifacts)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ChainSnapshot│  │ChainTemplate│  │Production   │      │
│  │(执行链路)    │  │(领域模板)    │  │Artifact     │      │
│  │             │  │             │  │(SQL/报表等)  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└──────────────────────────────────────────────────────────┘
```

### 为什么不需要 Projects

| 假设的 Project 用途 | AskData 已有替代 | 说明 |
|--------------------|----------------|------|
| 代码隔离 | git repo 本身 | AskData 是单 repo |
| 数据隔离 | WorkSpace | 问数空间天然提供多租户隔离 |
| 资源隔离 | Resource Mount | 每个 WS 挂载自己的 KB/DB/Agent |
| 模板隔离 | Chain Templates | 领域模板绑定 Workspace |
| 会话隔离 | Chat Sessions | 按 Workspace 隔离 |
| Agent 上下文 | CLAUDE.md + workspace config | Agent 加载项目级 schema |

## 五、Claw-Code 与 AskData 功能模块的协调关系

### 协调矩阵

| AskData 模块 | Claw-Code 如何协调 | 方式 |
|-------------|-------------------|------|
| **问数空间 (资源域)** | 通过 WorkSpace CRUD API 管理 Workspace 的创建、配置、资源挂载 | REST API 调用 |
| **链路工作台 (链路成果化)** | 通过 ChainSnapshot API 捕获和回放执行链路；通过 ChainTemplate API 管理模板 | REST API 调用 |
| **外部资源管理** | 通过 ResourceMount API 注册外部资源并挂载到 Workspace | REST API 调用 |
| **知识库** | 通过 Knowledge API 上传文档、管理 embedding | REST API 调用 |
| **数据源** | 通过 Datasource API 注册数据库连接 | REST API 调用 |

### 协调模式

Claw-Code **不管理 AskData 的用户数据**，而是：

1. **修改 AskData 的代码**（开发层，git repo）
2. **通过 API 测试 AskData 的功能**（运行时层，调用 WorkSpace API 验证）
3. **产出 AskData 的配置**（如 ChainTemplate YAML，写入 repo 作为种子数据）

## 六、结论与建议

### 核心结论

1. **不引入 "Projects" 概念** — AskData 的 WorkSpace (问数空间) 已完全覆盖 Project 的功能
2. **概念映射而非引入** — Memex 的每个概念都能在 AskData 找到对应实体
3. **三层隔离自然成立** — 开发层（代码）/ 运行时层（Workspace）/ 成果层（Artifacts）
4. **Claw-Code 集成无概念冲突** — Claw-Code 操作代码层，通过 API 与运行时层交互

### 推荐的集成架构

```
AskData 项目 (git repo)
├── CLAUDE.md              ← Claw-Code 的项目上下文
├── .claw/                 ← Claw-Code 会话持久化
├── 所有源码...             ← Claw-Code 可修改的范围
│
└── 运行时 (通过 API)       ← Claw-Code 通过 API 交互
    ├── WorkSpace API      ← 管理问数空间
    ├── ResourceMount API  ← 管理外部资源挂载
    ├── ChainTemplate API  ← 管理链路模板
    └── Knowledge/DB API   ← 管理数据源和知识库
```

Claw-Code 的角色是 **AskData 代码的开发者**，不是 AskData 运行时数据的操作者。这种分层使得所有概念协调自然、无冲突。
