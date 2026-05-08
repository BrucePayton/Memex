---
title: "Wiki 知识库功能完整集成"
type: analysis
created: 2026-05-09
last_updated: 2026-05-09
source_count: 1
confidence: medium
status: active
tags:
  - wiki
  - frontend
  - backend
  - feature-implementation
  - knowledge-base
  - 2026-05
sources:
  - src-wiki-知识库功能完整集成-实现记录
---

## 概述

将 Wiki 知识库完整集成到 Free-Style-Report 平台，实现与向量知识库并列的 KB 管理体系。共 5 个阶段，覆盖 KB 详情 Tab 重构、绑定自动创建文件夹、Wiki 管理页增强（新增 4 个 Tab）、预处理步骤推 Wiki 开关、工作空间推 Wiki 集成。[^src-wiki-知识库功能完整集成-实现记录]

## 架构

Wiki 与向量知识库通过 `t_knowledge_wiki_binding` 桥接表关联，绑定时可自动创建 `kb-{resource_uuid[:8]}` 名称的 Wiki 文件夹。解绑时 Wiki 页面保留，仅停止自动同步。[^src-wiki-知识库功能完整集成-实现记录]

## 实现阶段

| 阶段 | 内容 | 关键组件 |
|------|------|----------|
| 1 | KB 详情 Tab 重构 | `KnowledgeDetailTabs` — 向量 vs Wiki 两个 Tab，workspaceId 从 binding API 获取 |
| 2 | 绑定自动创建文件夹 | `wiki_helper.bind(create_folder=True)`，新增 `wiki_folder_id` 列，DB 迁移 |
| 3 | Wiki 管理页增强 | 4 个新 Tab：RAW Sources / Compare / Stale Review / Compose，KB 上下文自动定位 |
| 4 | 预处理推 Wiki | `DocumentPreprocessStep` 新增 Switch 开关，自动检测绑定状态，推送 RAW 源 |
| 5 | 工作空间推 Wiki | Q&A/分析结果增加"沉淀到 Wiki"按钮，通过 `WikiIntegrationDialog` 扩展 |

## TS 类型修复

- `wiki/index.ts`：28 处 `apiClient` 调用缺少泛型参数，严格模式下 `T` 默认为 `unknown`，显式添加 `<Type>` 解决
- `KnowledgeManagement.tsx`：`NodeJS.Timeout` 不存在于浏览器环境，改为 `ReturnType<typeof setTimeout>`；`import('./DataContext')` 动态导入无法解析，改为直接类型引用

## DB 迁移

新增 `t_knowledge_wiki_binding.wiki_folder_id` 列，关联 `t_wiki_folder.id`。迁移文件 `add_wiki_folder_id_to_binding.py` 依赖基础 revision `e377ba4672cc`，通过 `make db-migrate` 执行。

