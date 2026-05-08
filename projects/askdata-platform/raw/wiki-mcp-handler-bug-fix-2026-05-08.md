# Wiki MCP Handler Bug 修复记录 — 2026-05-08

## 背景
Wiki 知识库的 MCP Handler 层（`core/mcp/handlers/wiki_handlers.py`）存在多个运行时 bug，自 Phase A-D 开发以来一直未被发现，因为 helper 方法签名与实际调用不匹配。

## 修复的 Bug

### 1. `WikiPageHelper.get_by_id` 不存在 — 4处调用崩溃

**症状**: 调用 `WikiCompareHelper.compare()`, `WikiComposeService.compose()`, `WikiSlideService.export()`, `get_page_citations()` 时抛出 `AttributeError: type object 'WikiPageHelper' has no attribute 'get_by_id'`

**根因**: `WikiPageHelper` 只有 `get(db, page_id) -> Optional[WikiPage]`，但调用者用 `(page, error) = await WikiPageHelper.get_by_id(db, id)` 元组解包方式调用。

**修复**:
- `core/modules/knowledge/wiki_helper.py:759-765` — `WikiCompareHelper.compare()`
- `core/modules/knowledge/wiki_flow_service.py:511-513` — `WikiComposeService.compose()`
- `core/modules/knowledge/wiki_flow_service.py:596-598` — `WikiSlideService.export()`
- `core/modules/knowledge/views/wiki_views.py:944-946` — `get_page_citations()`

全部改为 `page = await WikiPageHelper.get(db, page_id)` + `if not page:` 判断。

### 2. MCP Handler 参数传递错误

**`handle_wiki_search`**: `WikiPageHelper.search(db, req)` 传 pydantic 对象给期望 `str` 的参数。修复为 `WikiPageHelper.search(db, query=req.query, folder_id=req.folder_id, limit=req.limit)`。

**`handle_wiki_create_folder`**: `WikiFolderHelper.create(db, create_req)` 传 pydantic 对象给期望 `str` 的参数。修复为逐个参数传入。

### 3. MCP Handler 绕过 Helper 方法

**`handle_wiki_create_page`**: 直接操作 ORM 对象创建页面，跳过 `WikiPageHelper.create()` 的日志记录。修复后调用 helper 方法，自动生成标准化 frontmatter（包含 `created`, `last_updated`, `source_count`, `tags`）。

**`handle_wiki_update_page`**: 直接操作 ORM 对象更新，跳过 `WikiPageHelper.update()` 的版本快照和 `change_summary` 支持。修复后调用 helper 方法。

### 4. `handle_wiki_add_raw_source` 返回值处理错误

`WikiRawSourceHelper.add()` 返回 `Tuple[Optional[WikiRawSource], Optional[str]]`，handler 直接赋值并调用 `.to_dict()`，有错误时 `None.to_dict()` 会崩溃。修复为元组解包 + 错误判断，并传递 `source_metadata` 参数。

### 5. `wiki_flow_service.py` 缩进错误

`WikiSlideService._basic_format` 方法体（lines 735-749）因缩进错误被嵌套在 `WikiAutoIndexService.generate()` 内部，永远无法执行。修复后正确放置在 `WikiSlideService` 类中，并移除死代码。

## 新增功能（对标 Memex）

- **RAW 源不可变性**: `WikiRawSourceHelper.add()` 增加同 page 下 filename 重复检测
- **页面去重**: `WikiPageHelper.create()` 增加同 folder 下标题重复检测
- **统计增强**: `wiki_stats` 返回 type 分布、wikilink 数量、raw source 数量
- **日志增强**: `wiki_recent_log` 返回 `date` 字段
- **使用说明更新**: `wiki_get_instructions` 对齐 Memex 页面类型体系
- **引用集成**: `wiki_get_page` 返回 citation refs 和 wikilinks
- **全局 RAW 列表 API**: 新增 `GET /api/wiki/raw-sources` 端点

## 前端修复

- **WIKI_INGEST 路由守卫**: `routeAccess.ts` ACL 判断中增加 WIKI_INGEST 路径
- **Wiki 路由映射**: `appRouteMaps.ts` 增加 wiki 页面类型和路由映射
- **documentCount**: `utils.ts` 从 `wiki_page_count` 字段读取，不再硬编码 0
- **全局 RAW 源 API**: 前端 `web/src/apis/wiki/index.ts` 新增 `getRawSources()`

## 涉及文件
| 文件 | 改动 |
|------|------|
| `core/mcp/handlers/wiki_handlers.py` | 重写全部 handler 函数 |
| `core/modules/knowledge/wiki_helper.py` | 修复 compare，新增 RAW 不可变性、页面去重、get_all |
| `core/modules/knowledge/wiki_flow_service.py` | 修复 2 处 get_by_id，修复 _basic_format 缩进 |
| `core/modules/knowledge/views/wiki_views.py` | 修复 get_page_citations，新增全局 RAW 列表端点 |
| `web/src/app/routes/routeAccess.ts` | 添加 WIKI_INGEST ACL |
| `web/src/app/routes/appRouteMaps.ts` | 添加 wiki 路由映射 |
| `web/src/apis/knowledge-base/utils.ts` | 修复 documentCount |
| `web/src/apis/wiki/index.ts` | 添加 getRawSources API |
