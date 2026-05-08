---
title: "Wiki Dashboard 功能完善（12 视图补齐与执行模式配置）"
type: analysis
created: 2026-05-09
last_updated: 2026-05-09
source_count: 1
confidence: medium
status: active
tags:
  - wiki-dashboard
  - frontend
  - memex-style
  - view-completion
  - execution-mode
  - 2026-05
sources:
  - src-2026-05-09-platform-feature-completion-and-wiki-dashboard-enhancement
---

## 概述

Wiki Dashboard 是 Memex 风格的 Wiki 知识库全屏管理界面，此前仅 7 个视图有真实实现，其余为 "coming soon" 占位符。本次补齐全部 12 个视图并新增执行模式配置。

[^src-0]: 原始变更记录参考 raw source

## 架构

- 路由 `/wiki` → `WikiManagementPage`（薄壳）→ `WikiDashboardLayout`
- 布局：Header（状态栏）→ Body（可拖拽侧栏 + Main（工具栏 + 内容区））
- `DashboardViews` 是 `ViewType` 的 switch 路由，渲染对应组件
- 所有视图统一使用 `ViewPanel` 容器：`max-w-[820px] mx-auto px-11 py-9`

## 新增视图清单（12 个）

### BrowseView
- 双模式：Folder 模式（调用 `getFolderPages()` 展示页面列表）和 Page 模式（调用 `getPage()` 展示内容）
- 状态覆盖：未选文件夹（装饰图标）、加载中（spinner）、空文件夹、加载失败（重试按钮）、数据展示

### HealthView
- 自动加载 `getWikiHealth()`，显示健康评分（绿 ≥0.8 / 橙 ≥0.5 / 红 <0.5）
- 逐项指标展示（pass/warn/fail 图标），手动刷新

### RawView
- 直接复用 `WikiRawSourcesTab` 组件，~20 行代码
- 自带加载/筛选/错误处理

### HistoryView / LogsView
- 调用 `getWikiLogs(200)` 展示完整操作日志
- HistoryView 支持实体类型筛选（all/page/folder/raw_source）
- 日志条目：时间戳 + 操作类型（颜色编码 Badge）+ 实体名 + 类型

### QueryView
- 内联问答界面，适配自 `WikiQueryDialog`
- 输入框 + 提交按钮，答案展示 + 引用来源卡片
- 使用新封装 `wikiQuery()`

### ReviewView / CompareView
- 分别复用 `WikiStaleReviewTab` 和 `WikiCompareTab`
- ~20 行包装代码

### WriteView
- 轻量内联编辑器：标题、文件夹选择、标签、`WikiMarkdownEditor`
- 调用 `createPage()`，成功后导航至 `/wiki`

### IngestView
- 紧凑导入表单：源文本、源名、文件夹、标签、自动拆分开关
- 预览（`wikiIngestPreview`）和执行（`wikiIngest`）分离

### SchemaView
- 静态参考页，无 API 调用
- Frontmatter 字段参考、页面类型说明、引用格式、文件夹结构

### GuideView
- 静态使用指南，无 API 调用
- 侧栏/工具栏/内容创建/快捷键分段说明，颜色编码区分

## 执行模式配置

- 替换 SettingsView 中的 "Configuration coming soon" 占位
- 分段按钮切换 **LLM** / **Claw Code** 模式
- 偏好存储在 `localStorage`（key: `wiki-execution-mode`，默认 `llm`）
- 附带快速跳转按钮：`/llm-config` 和 `/claw`

## 新增前端 API 封装

在 `web/src/apis/wiki/index.ts` 追加：
- `wikiQuery()` → `POST /api/wiki/query`
- `wikiIngest()` → `POST /api/wiki/ingest`
- `wikiIngestPreview()` → `POST /api/wiki/ingest/preview`
- `wikiStaleReview()` → `POST /api/wiki/stale-review`
- `wikiComparePages()` → `POST /api/wiki/pages/compare`

## 已复用组件

| 组件 | 视图 | 路径 |
|------|------|------|
| WikiRawSourcesTab | RawView | `wiki/components/WikiRawSourcesTab.tsx` |
| WikiStaleReviewTab | ReviewView | `wiki/components/WikiStaleReviewTab.tsx` |
| WikiCompareTab | CompareView | `wiki/components/WikiCompareTab.tsx` |
| WikiMarkdownEditor | WriteView | `wiki/components/WikiMarkdownEditor.tsx` |
| ViewPanel | 全部视图 | `wiki-dashboard/views/ViewPanel.tsx` |

## 完整提交

`c9e477bb` — feat: Wiki Dashboard 功能完善——补齐 12 个视图与执行模式配置（16 files, +1310/−34）

[^src-0]: projects/askdata-platform/raw/2026-05-09-platform-feature-completion-and-wiki-dashboard-enhancement.md

