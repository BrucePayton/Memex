---
title: "Wiki MCP Handler Bug 修复与 Memex 对标"
type: analysis
created: 2026-05-08
last_updated: 2026-05-08
source_count: 1
confidence: medium
status: active
tags:
  - wiki
  - backend
  - frontend
  - mcp
  - bug-fix
  - memex-benchmark
  - 2026-05
sources:
  - wiki-mcp-handler-bug-fix-2026-05-08
---

# Wiki MCP Handler Bug 修复与 Memex 对标

## 问题概述

Wiki 知识库的 MCP Handler 层（`core/mcp/handlers/wiki_handlers.py`）自 Phase A-D 开发完成以来积累了多个运行时 bug，包括：方法名不存在、参数类型不匹配、跳过 helper 方法导致日志/版本快照缺失、RAW 源不可变性未实现等。[^src-wiki-mcp-handler-bug-fix-2026-05-08]

## Bug 分类

### Runtime Errors（导致服务崩溃）
1. **`WikiPageHelper.get_by_id` 不存在** — 4 处调用点（compare, compose, export, citations）均抛出 `AttributeError` [^src-wiki-mcp-handler-bug-fix-2026-05-08]
2. **`_basic_format` 缩进错误** — 方法体被嵌套在错误的类中，LLM 失败时降级方案永远不执行 [^src-wiki-mcp-handler-bug-fix-2026-05-08]

### 参数传递错误（静默失败）
1. **`handle_wiki_search`** — 将 pydantic `WikiSearchRequest` 对象作为 `str` 传入 helper，搜索变为匹配对象的 `__str__()` 表示 [^src-wiki-mcp-handler-bug-fix-2026-05-08]
2. **`handle_wiki_create_folder`** — 将 pydantic `WikiFolderCreate` 对象作为 `name: str` 传入 [^src-wiki-mcp-handler-bug-fix-2026-05-08]

### 功能绕过（静默失效）
1. **`handle_wiki_create_page`** — 直接操作 ORM 跳过 `WikiPageHelper.create()` 的日志记录 [^src-wiki-mcp-handler-bug-fix-2026-05-08]
2. **`handle_wiki_update_page`** — 直接操作 ORM 跳过版本快照和 `change_summary` [^src-wiki-mcp-handler-bug-fix-2026-05-08]
3. **`handle_wiki_add_raw_source`** — 返回值元组未解包，`source_metadata` 参数被丢弃 [^src-wiki-mcp-handler-bug-fix-2026-05-08]

## 修复方案

### 统一原则
- 所有 MCP handler **必须调用 helper 方法**，不得直接操作 ORM 对象
- helper 方法统一返回 `(result, error)` 元组，handler 层负责解包
- frontmatter 自动生成标准化字段：`created`, `last_updated`, `source_count`, `tags`

### RAW 不可变性保护
参考 Memex 的 `add_raw_source` 不可变设计，在 `WikiRawSourceHelper.add()` 中增加同 `(page_id, filename)` 重复检测，返回 `(None, "Raw source '...' already exists")` 阻止覆盖。[^src-wiki-mcp-handler-bug-fix-2026-05-08]

### 页面去重
参考 Memex 的 `create_page` dedup 设计（`{slug}-2`, `{slug}-3`），本项目由于使用 `folder_id + title` 作为逻辑标识，采用同文件夹下标题不可重复的策略。[^src-wiki-mcp-handler-bug-fix-2026-05-08]

## 统计接口增强（对标 Memex stats）

Memex 的 `stats` 工具返回 `total_pages`, `raw_sources`, `type_counts`, `total_links`。本项目的 `wiki_stats` 原来只返回 `total_pages` 和 `total_folders`，现已增强为返回完整统计。[^src-wiki-mcp-handler-bug-fix-2026-05-08]

## 前端修复

- **WIKI_INGEST 路由守卫** — `routeAccess.ts` ACL 判断中增加 `/wiki/ingest` 路径 [^src-wiki-mcp-handler-bug-fix-2026-05-08]
- **documentCount** — `utils.ts` 从后端 `wiki_page_count` 字段读取，修复硬编码 0 [^src-wiki-mcp-handler-bug-fix-2026-05-08]

## 经验教训

1. **Helper 方法签名变更时必须检查所有调用点** — `get_by_id` 被调用了 4 次但方法从未存在过
2. **MCP handler 不应直接操作 ORM** — 绕过 helper 会导致日志、版本快照、不可变性检查等横切功能全部失效
3. **元组返回值必须统一处理** — helper 方法返回 `(result, error)` 时 handler 层必须解包并判断 error
4. **Python 缩进错误可能导致方法永远不执行** — `_basic_format` 的缩进错误使降级方案完全失效

