---
title: "Wiki 知识库 Memex 对标优化 - Phase 1-4 实现记录"
type: analysis
created: 2026-05-07
last_updated: 2026-05-07
source_count: 0
confidence: medium
status: active
tags:
  - wiki
  - frontend
  - backend
  - phase-complete
  - refactoring
  - debug
---

## 背景

Wiki 知识库对标 Memex 功能存在 9 个已发现的现象级问题，涉及 RAW 文件展示、路由守卫遗漏、LLM 集成、页面数据不一致等多个方面。本记录涵盖 Phase 1-4 的修复实现。

> 现象 5（LLM 功能全部失败）单独排期，不在此记录中。

---

## Phase 1: 关键 Bug 修复

### 1.1 RAW 文件展示

**问题**：`WikiRawViewer` 调用 `GET /api/wiki/raw-sources` 但后端只有 POST 端点，缺少全局 GET 端点，导致 404。

**修复**：
- **后端**：`WikiRawSourceHelper` 新增 `get_all()` 方法（`wiki_helper.py:438`），`wiki_views.py` 新增 `GET /api/wiki/raw-sources` 全局端点
- **前端**：`apis/wiki/index.ts` 新增 `getWikiRawSources()` API，`WikiManagementPage.tsx` 加载 `rawSources` 并传给 `WikiSidebar`

**涉及文件**：
- `core/modules/knowledge/wiki_helper.py:438-446`
- `core/modules/knowledge/views/wiki_views.py:462-475`
- `web/src/apis/wiki/index.ts` — `getWikiRawSources()`
- `web/src/features/wiki/pages/WikiManagementPage.tsx` — rawSources state → sidebar

### 1.2 收录路由守卫

**问题**：点击"收录"按钮后导航到首页而不是收录页。`routeAccess.ts` 的 `isPathAllowedByAcl` 和 `appRouteMaps.ts` 未包含 `WIKI_INGEST` 路径。

**修复**：
- `routeAccess.ts:140` — 在 `isPathAllowedByAcl` 中添加 `WIKI_INGEST` 判断
- `appRouteMaps.ts` — 添加 `[ROUTES.WIKI_INGEST, 'wiki']` 映射

### 1.3 返回导航保持选中状态

**问题**：从 Wiki 页面点击返回箭头（`navigate(-1)`）回到知识库管理后，之前选中的知识库未被保留选中状态。

**修复**：
- `WikiLayout.tsx` — `onBack` prop 已存在，`WikiManagementPage.tsx` 传入 `onBack={() => navigate(ROUTES.KNOWLEDGE, { state: { selectedKbId } })}`
- `KnowledgeManagement.tsx` — 新增 `useEffect` 监听 `location.state.selectedKbId`，在知识库列表加载后自动定位并展开该知识库详情

**涉及文件**：
- `web/src/features/wiki/pages/WikiManagementPage.tsx` — onBack prop
- `web/src/features/knowledge/pages/KnowledgeManagement.tsx` — auto-selection useEffect

### 1.4 页面列表与图谱一致

**问题**：图谱加载全部页面，但页面列表只显示当前选中文件夹的页面，导致图谱中可见的页面在列表中找不到。

**修复**：
- **后端**：`WikiPageHelper` 新增 `get_all_pages()` 方法，`wiki_views.py` 新增 `GET /api/wiki/pages` 端点
- **前端**：`apis/wiki/index.ts` 新增 `getAllPages()` API，`WikiSidebar` 和 browse 视图各添加"所有页面"入口
- **行为变更**：当 `selectedFolderId` 为 `null` 时，`loadFolderPages` 调用 `getAllPages()` 而非清空列表

**涉及文件**：
- `core/modules/knowledge/wiki_helper.py:298-310`
- `core/modules/knowledge/views/wiki_views.py:276-286`
- `web/src/apis/wiki/index.ts` — `getAllPages()`
- `web/src/features/wiki/pages/WikiManagementPage.tsx` — all-pages entry + load logic
- `web/src/features/wiki/components/WikiSidebar.tsx` — "所有页面" entry

---

## Phase 2: 数据准确性

### 2.1 文档数量修正

**问题**：`convertBackendToKnowledgeBase()` 中 `documentCount` 硬编码为 `0`，知识库详情始终显示"0 个文档"。

**修复**：
- `KnowledgeBaseBackend` 接口新增 `wiki_page_count` 字段，`KnowledgeBase` 接口新增 `wikiPageCount` 字段
- `convertBackendToKnowledgeBase()` 改为从 `backend.wiki_page_count` 读取，替代硬编码 0
- 详情视图标签从"文档数量"改为"Wiki 页面"，显示真实的 wiki 页面数

**涉及文件**：
- `web/src/apis/knowledge-base/types.ts` — wiki_page_count 字段
- `web/src/components/types.ts` — wikiPageCount 字段
- `web/src/apis/knowledge-base/utils.ts` — 映射 wiki_page_count
- `web/src/features/knowledge/pages/KnowledgeManagement.tsx` — 显示 wikiPageCount

### 2.2 Wiki 统计信息集成

**问题**：`getWikiStats()` API 已定义（`apis/wiki/index.ts:469`）但从未被调用；`WikiSidebar` 的 `stats` prop 从未传入。

**修复**：
- `WikiManagementPage.tsx` 导入 `getWikiStats`，新增 `stats` state，`loadWikiStats()` 加载函数，`useEffect` 在挂载时调用
- `WikiSidebar` 收到 `stats` 数据后显示页面数、来源数、链接数、文件数统计条

---

## Phase 3: UI/UX 改进

### 3.1 工具栏折叠优化

**问题**：`WikiToolbar` 所有子功能全部展开，工具栏过长且杂乱。

**修复**：
- 新增 `expanded` state（`Set<CategoryKey>`），每个分类默认收起
- 分类标题可点击展开/收起子功能，选中子功能后自动收起
- 当前激活的 view 会在收起状态下在分类标题旁显示标签

**涉及文件**：
- `web/src/features/wiki/components/WikiToolbar.tsx` — 完全重写

### 3.2 健康状态常驻指示器

**问题**：健康度状态隐藏在子功能"复习"中，没有独立可见的指示。

**修复**：
- 工具栏右侧常驻显示健康度指示器（圆点 + 分数），颜色随分数变化（>=80 绿，>=50 黄，<50 红）
- 点击指示器跳转到健康详情视图

---

## Phase 4: LLM 集成

### 4.1 LLM 连通性检测

**问题**：健康检查缺少 LLM 状态。

**修复**：
- `WikiHealthHelper.check()` 新增第 8 项检查：尝试创建 LLM 客户端（`reasoning` 模型）并发送最小测试请求
- 连接成功 → 标记 OK；返回空响应 → 扣 10 分；连接失败 → 扣 15 分并记录错误详情

**涉及文件**：
- `core/modules/knowledge/wiki_helper.py:962-975` — LLM 健康检查

> 注意：Phase 4.2（Claw-Code 集成）和 4.3（平台配置支持）已在之前的基础建设中完成 — `PlatformConfigPage` 已有 LLM Config / Provider Management / Claw Control 三个 Tab；`core/claw/` 模块已完整实现。

---

## 根因分类总结

| # | 现象 | 根因归类 | 修复定位 |
|---|------|---------|---------|
| 1 | RAW 文件不显示 | 后端 API 缺失 + 前端未传 prop | 后端 + 前端 |
| 2 | 工具栏子功能全部展开 | 缺少折叠/展开状态管理 | 前端纯 UI |
| 3 | 点击收录跳到首页 | 路由 ACL 遗漏 + 路由映射遗漏 | 前端路由 |
| 4 | 无 LLM 状态 | 健康检查未覆盖 | 后端 |
| 6 | 返回未保持选中状态 | navigate(-1) 丢失上下文 | 前端路由状态 |
| 7 | 文档数量不匹配 | 硬编码 0 | 前端数据映射 |
| 8 | 页面列表与图谱不一致 | 无全局页面加载路径 | 后端 + 前端 |
| 9 | 图谱有页面但列表没有 | 同上 | 同上 |

## 实施顺序与依赖关系

```
Phase 1 (关键 Bug) → Phase 2 (数据) → Phase 3 (UI/UX) → Phase 4 (LLM)
```

各阶段互不阻塞，可独立上线。Phase 1 为必修复项，Phase 2-4 为体验增强。LLM 链路排查（现象 5）和 Git 集成（现象 8 → Phase 5）待后续单独排期。

