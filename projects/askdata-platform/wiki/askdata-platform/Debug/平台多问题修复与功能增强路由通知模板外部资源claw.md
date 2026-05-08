---
title: "平台多问题修复与功能增强（路由/通知/模板/外部资源/Claw）"
type: analysis
created: 2026-05-09
last_updated: 2026-05-09
source_count: 1
confidence: medium
status: active
tags:
  - bug-fix
  - routing
  - notification-center
  - domain-template
  - external-resources
  - claw-code
  - 2026-05
sources:
  - src-2026-05-09-platform-feature-completion-and-wiki-dashboard-enhancement
---

## 概述

本次修复和增强覆盖 7 个已知问题，按严重程度从 P0（阻塞级 404）到 P3（UI 优化）依次修复，并启用通知中心。

[^src-0]: 原始变更记录参考 raw source

---

## P0: 路由 404 修复（Wiki + 领域配置 + Provider）

### Wiki 知识库绑定 404
- **根因**：前端 `resolveApiEndpointPath()` 中的 `DIRECT_UNDER_API_PREFIXES` 缺少 `/wiki`，导致请求被错误路由到 `/api/wp/wiki/...`
- **修复**：在 `web/src/shared/api/client.ts` 的数组中追加 `'/wiki'`

### 领域配置 & Provider 路由未挂载
- **根因**：`domain_config_views.router` 和 `provider_views.router` 在 `core/modules/config/views/` 下已完整实现，但 `manage.py` 的 `mount_routers()` 从未导入和挂载它们。所有 `/api/config/domains/*` 和 `/api/config/providers/*` 返回 404
- **修复**：在 `manage.py` 中添加导入和 `(domain_config_router, None, None)` / `(provider_router, None, None)` 挂载

---

## P1: 通知中心真正启用

此前通知中心 API 和前端组件已就位，但系统从未产生任何通知。本次在 4 个关键业务节点接入：

1. **链路快照创建** — 创建成功后发送 `task` 类型通知，附带快照名称和跳转链接
2. **数据源状态变更** — 启用/禁用时发送 `system` 通知
3. **Wiki 知识库同步** — 同步完成后发送结果通知（成功含新建/更新页数，失败含错误信息）
4. **服务启动** — 为 admin 用户创建欢迎通知

所有通知创建都包裹在 try/catch 中，不影响主流程。

---

## P2: 领域模板重构（静态→动态聚合）

- 移除 `core/modules/chain_template/builtin_templates.py` 中 4 个硬编码模板
- 移除 `manage.py` 中的 `seed_builtin_templates()` 启动初始化
- 新增 `POST /api/chain-template/aggregate-from-snapshots` 聚合端点
- 前端移除内置模板卡片，新增"从快照聚合"按钮和对话框

---

## P3: 外部资源管理 Tab 布局重构

- 从卡片式布局完全重构为 Tabs 布局
- "外部资源" Tab：统一表格展示所有 kind，支持按 kind 过滤、搜索、CRUD
- "平台管理" Tab：PlatformRegistration CRUD + 资源发现

---

## Claw Code 配置面板

- 平台配置页新增 Claw Code 入口卡片（`<Terminal />` 图标，emerald 色）
- Claw Dashboard 新增"配置"Tab：ANTHROPIC_BASE_URL / AUTH_TOKEN / MODEL 表单字段
- 后端：`POST /api/claw/config`（保存到 `.claw.json`）和 `POST /api/claw/test-connection`（HTTP POST 到 `/chat/completions`）
- 返回按钮改为智能导航：`history.length > 2 ? navigate(-1) : navigate(ROUTES.HOME)`

## 提交历史

| Commit | 内容 |
|--------|------|
| `db211183` | 路由修复 + 领域模板重构 |
| `ca6a740d` | 通知中心启用 + Wiki 增强 |
| `239ef7de` | 外部资源 Tab 重构 |
| `eae5a353` | Claw Code 配置面板 |

[^src-0]: projects/askdata-platform/raw/2026-05-09-platform-feature-completion-and-wiki-dashboard-enhancement.md

