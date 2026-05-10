---
title: "Analysis App 自动化生成"
type: concept
created: 2026-05-10
last_updated: 2026-05-10
source_count: 1
confidence: medium
status: active
tags:
  - app-generator
  - pipeline
  - mcp
  - automation
sources:
  - 2026-05-10-analysis-app-自动化生成-phase456开发记录
---

# Analysis App 自动化生成

Analysis App 自动化生成是 AskData 平台的核心功能，目标是从挂载的数据源出发，**零代码生成**完整的 Analysis App。通过元数据提取→NCR 转换→Profile 生成→代码生成→Prompt 生成→Langfuse 同步→热门问题→Registry 注册→Git 提交 10 个阶段的自动化流水线实现。

## 架构总览

```
数据源 → 元数据提取 → NCR 转换 → Profile 生成
                                      ↓
                            代码生成 → Git 提交
                            Prompt 生成 → Langfuse 同步
                            热门问题生成 → DB 持久化
                            Registry 注册 → App 可用
```

## 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| Orchestrator | `core/modules/app_generator/orchestrator.py` | 10 阶段流水线编排 |
| Profile Generator | `profile_generator.py` | 从 NCR 生成维度/度量/实体 Profile |
| Code Generator | `code_generator.py` | 根据 Profile 生成 React/TypeScript 代码 |
| Prompt Generator | `prompt_generator.py` | 生成 LLM 对话 Prompt |
| HotQuestionGenerator | `hot_question_generator.py` | 基于 Profile 生成热门问题 |
| LangfuseSyncer | `langfuse_sync.py` | 同步 Prompts 到 Langfuse |
| RegistryPatcher | `registry_patcher.py` | 注册到 Analysis App Registry |
| GitManager | `git_manager.py` | Git 提交所有产物 |
| Schemas | `schemas.py` | Pydantic 数据模型定义 |
| Views | `views.py` | FastAPI REST API 端点 |

## 10 阶段 Pipeline

1. **connection_test** — 测试数据源连接
2. **metadata_extract** — 提取完整 Schema
3. **ncr_convert** — 转换为 NCR（Neural Concept Representation）规范
4. **profile_gen** — 生成 Analysis App Profile（维度、度量、实体、概念）
5. **code_gen** — 生成 React/TypeScript 代码文件
6. **prompt_gen** — 生成 LLM 对话 Prompts
7. **langfuse_sync** — 同步 Prompts 到 Langfuse 平台
8. **hot_question_gen** — 生成热门问题并持久化到 DB
9. **registry_patch** — 注册到 Analysis App Registry
10. **git_commit** — Git 提交所有产物

任一阶段失败则标记为 failed 并终止流水线。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/app-generator/tasks` | 创建生成任务 |
| GET | `/api/app-generator/tasks` | 任务列表 |
| GET | `/api/app-generator/tasks/{id}` | 任务详情 |
| GET | `/api/app-generator/apps` | 已生成 App 目录 |
| GET | `/api/app-generator/hot-questions` | 热门问题列表 |
| POST | `/api/app-generator/hot-questions/generate` | 手动生成热门问题 |

## MCP 工具 (6 个)

通过 `core/mcp/handlers/app_generator_handlers.py` 暴露，注册到 MCP stdio_server 的 `app_generator` 域：

| 工具 | 说明 |
|------|------|
| metadata_extract | 从数据源提取 Schema |
| metadata_analyze | 分析元数据生成 Profile |
| generate_app_preview | 预览将生成的代码 |
| generate_app | 正式生成 App 全流程 |
| sync_to_langfuse | 同步 Prompts 到 Langfuse |
| list_generated_apps | 列出所有已生成 Apps |

## 前端 Wizard

`web/src/features/app-generator/pages/AppGeneratorPage.tsx` — 5 步向导：

1. **选择数据源** — 下拉选择已挂载数据库
2. **配置领域** — 输入 App 名称、domain、function
3. **预览确认** — 展示配置和 10 阶段预览
4. **生成中** — 2 秒轮询展示进度条和各阶段状态
5. **完成** — 展示结果、热门问题、已生成 App 列表

入口：`PlatformConfigPage` → "App 生成"卡片 → `/app-generator` 路由。

## 数据库模型

| 表 | ORM 模型 | 说明 |
|----|---------|------|
| `t_app_generation_task` | `AppGenerationTask` | 任务主表 |
| `t_app_generation_stage` | `AppGenerationStage` | 阶段子表（关联 task_id） |
| `t_hot_question` | `HotQuestion` | 热门问题（关联 datasource_id） |

## 测试覆盖

- `tests/test_phase5.py` — 19 个测试（MCP 工具 + Hot Questions）
- `tests/test_phase6_e2e.py` — 28 个测试（Pipeline + API + MCP + 前端）
- 全量回归 139 个测试全部通过

[^src-2026-05-10-analysis-app-自动化生成-phase456开发记录]: projects/askdata-platform/raw/2026-05-10-analysis-app-自动化生成-phase456开发记录.md
