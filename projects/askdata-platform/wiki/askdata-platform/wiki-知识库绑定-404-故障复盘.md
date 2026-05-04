---
title: "Wiki 知识库绑定 404 故障复盘"
type: analysis
created: 2026-05-04
last_updated: 2026-05-04
source_count: 0
confidence: medium
status: active
tags:
  - postmortem
  - bug-fix
  - api-routing
  - frontend
  - askdata-platform
---

# Wiki 知识库绑定 404 故障复盘

## 现象

在知识库详情页选择"Wiki 知识库"卡片，点击"绑定到 Wiki"按钮，请求 `POST /api/wp/api/wiki/bindings` 和 `GET /api/wp/api/wiki/bindings/knowledge-base/1` 均返回 404。

## 根因分析

共发现 **3 个问题**，叠加导致 404：

### 1. 前端 `getApiBasePath()` 返回路径含 `/api` 前缀（根本原因）

**文件**: `web/src/apis/wiki/index.ts`

```typescript
// 错误 — 包含了 /api 前缀
function getApiBasePath(): string {
  return '/api/wiki';
}
```

前端 API 客户端通过 `resolveApiEndpointPath()` 将 endpoint 转为最终 URL：

```
endpoint = '/api/wiki/bindings'
→ resolveApiEndpointPath → 检查 DIRECT_UNDER_API_PREFIXES
→ '/api/wiki/bindings' 不匹配 '/wiki'（多了 /api/）
→ 回退到 /wp 前缀规则
→ 返回 '/wp/api/wiki/bindings'
→ URL = /api + /wp/api/wiki/bindings = /api/wp/api/wiki/bindings → 404
```

**约定**: 所有其他模块（`/kb`、`/askdata`、`/wp`）的 `getApiBasePath()` 都只返回路径段，**不包含** `/api` 前缀。Wiki 模块违反了此约定。

### 2. 后端 `wiki_router` 未在 `manage.py` 中注册

**文件**: `manage.py` (`mount_routers()`)

`wiki_router` 仅在 `core/server/app.py`（遗留入口）中注册，生产入口 `manage.py` 的 `mount_routers()` 中缺少该路由器的导入和注册。即使前端 URL 正确，后端也不会响应。

### 3. GET 绑定接口前后端契约不匹配

**前端**: `KnowledgeWikiTab.tsx` 调用 `GET /api/wiki/bindings?knowledge_base_id=1&workspace_id=0`（query 参数，期望数组响应）

**后端**: `wiki_views.py` 只有 `GET /api/wiki/bindings/knowledge-base/{knowledge_base_id}`（路径参数，返回单个对象或 null）

## 修复方案

| # | 文件 | 改动 |
|---|------|------|
| 1 | `web/src/apis/wiki/index.ts` | `getApiBasePath()` 返回 `/wiki` 而非 `/api/wiki` |
| 2 | `web/src/features/wiki/components/KnowledgeWikiTab.tsx` | 本地 `getBindings()` 的硬编码路径从 `/api/wiki/bindings/knowledge-base/${kbId}` 改为 `/wiki/bindings/knowledge-base/${kbId}` |
| 3 | `web/src/shared/api/client.ts` | `DIRECT_UNDER_API_PREFIXES` 添加 `/wiki`（配合 Fix 1 生效） |
| 4 | `manage.py` | `mount_routers()` 中导入并注册 `wiki_router` |

## 经验教训

### 1. API 路径前缀约定

- `getApiBasePath()` 只返回路径段（如 `/wiki`、`/kb`），**绝不**包含 `/api`
- `resolveApiEndpointPath()` 的 `DIRECT_UNDER_API_PREFIXES` 列表与 `manage.py` 中 `mount_routers()` 的 prefix 保持一致
- 新增后端模块时，两端需同步：后端加路由注册，前端加直连前缀

### 2. 注册路由的一致性

所有路由器都应在 `manage.py` 的 `mount_routers()` 中注册（生产入口），而非仅在 `core/server/app.py`（遗留入口）中。

### 3. API 契约对齐

前端调用后端 API 时，端点和参数格式需与后端定义严格一致（路径参数 vs query 参数、响应格式等）。

## 相关文件

- `web/src/apis/wiki/index.ts`
- `web/src/features/wiki/components/KnowledgeWikiTab.tsx`
- `web/src/shared/api/client.ts`
- `manage.py`
- `core/modules/knowledge/views/wiki_views.py`

