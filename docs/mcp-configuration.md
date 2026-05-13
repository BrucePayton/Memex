# Memex MCP 服务配置文档

## 概述

Memex MCP 服务器提供 **60 个工具**和 **3 个资源**，覆盖项目管理、Wiki 读写、知识图谱操作、跨项目宇宙查询、Wiki 智能维护和定时任务。

---

## 启动方式

### 1. Stdio 模式（本地 Claude CLI 集成）

Claude Code 通过 stdio 直接调用，无需网络端口。

```bash
claude mcp add memex -- python3 mcp-server/memex_mcp.py
```

### 2. HTTP 模式（远程/容器部署）

启动 Streamable HTTP 服务，支持 SSE 流式响应。

```bash
MEMEX_MCP_TRANSPORT=http MEMEX_MCP_PORT=8081 python3 mcp-server/memex_mcp.py
```

**环境变量：**

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MEMEX_MCP_TRANSPORT` | `stdio` | `stdio` 或 `http` |
| `MEMEX_MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MEMEX_MCP_PORT` | `8081` | 监听端口 |
| `MEMEX_DASHBOARD_URL` | `http://localhost:8000` | Dashboard API 地址（图谱工具依赖） |
| `MEMEX_ACTIVE_PROJECT` | 空 | 默认激活的项目 slug |

**HTTP 端点：**

| 路径 | 方法 | 说明 |
|------|------|------|
| `/mcp` | POST | MCP JSON-RPC 端点（SSE 流式响应） |

**客户端请求要求：**

```
Content-Type: application/json
Accept: application/json, text/event-stream
```

---

## 客户端配置

所有 HTTP 客户端统一连接地址：**`http://your-domain:80/mcp`**（或 HTTPS `https://your-domain:443/mcp`）。

### 1. Claude Code（CLI）

```bash
# 添加 HTTP MCP 服务器
claude mcp add memex http://localhost:80/mcp

# 添加 Stdio 模式（本地开发）
claude mcp add memex -- python3 /path/to/mcp-server/memex_mcp.py

# 查看/移除
claude mcp list
claude mcp remove memex
```

### 2. Claude Desktop

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "memex": {
      "url": "http://localhost:80/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### 3. Cursor

`.cursor/mcp.json` 或 Settings → MCP：

```json
{
  "mcpServers": {
    "memex": {
      "url": "http://localhost:80/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### 4. Windsurf (Codium)

```json
{
  "mcpServers": {
    "memex": {
      "url": "http://localhost:80/mcp"
    }
  }
}
```

### 5. Python 客户端（MCP SDK）

```python
from mcp import ClientSession, StreamableHttpTransport
import asyncio

async def main():
    async with ClientSession(
        "http://localhost:80/mcp",
        transport=StreamableHttpTransport()
    ) as session:
        await session.initialize()
        tools = await session.list_tools()
        for tool in tools.tools:
            print(f"  {tool.name}: {tool.description}")

asyncio.run(main())
```

### 6. curl（快速测试）

```bash
# 初始化
curl -s -N --max-time 3 http://localhost:80/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'

# 列出工具
curl -s -N --max-time 3 http://localhost:80/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# 调用工具
curl -s -N --max-time 5 http://localhost:80/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}'
```

---

## Docker 部署

### docker-compose.yml

```yaml
memex-mcp:
  build:
    context: .
    dockerfile: Dockerfile.mcp
  container_name: memex-mcp
  expose:
    - "8081"
  volumes:
    - ./wiki:/home/appuser/wiki:rw
    - ./raw:/home/appuser/raw:ro
    - ./projects:/home/appuser/projects:rw
    - ./.git:/home/appuser/.git:rw
    - ./.dashboard-settings.json:/home/appuser/.dashboard-settings.json:rw
    - ./.memex:/home/appuser/.memex:rw
  environment:
    - MEMEX_MCP_TRANSPORT=http
    - MEMEX_MCP_HOST=0.0.0.0
    - MEMEX_MCP_PORT=8081
    - MEMEX_ACTIVE_PROJECT=askdata-platform
    - TZ=Asia/Shanghai
  healthcheck:
    test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8081/')"]
    interval: 30s
    timeout: 10s
    retries: 3
  restart: unless-stopped
```

### Nginx 反向代理

```nginx
upstream memex-mcp {
    server memex-mcp:8081;
}

location /mcp {
    proxy_pass http://memex-mcp;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

---

## 工具分类

### 项目管理（8 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `list_projects` | 列出所有项目（含 legacy） | — |
| `get_instructions` | 获取 CLAUDE.md（Wiki 规范文档） | `project` |
| `list_template_names` | 列出可用项目模板 | — |
| `create_project` | 创建新项目 | `slug_hint`*, `title`*, `description`, `model`, `template` |
| `switch_project` | 切换当前激活项目 | `slug`* |
| `update_project_settings` | 更新项目设置 | `slug`*, `model`, `title`, `description` |
| `delete_project` | 删除项目（软删除到 .trash） | `slug`*, `confirm`* |
| `stats` | Wiki 统计（页面数、类型分布、源数量、链接数） | `project` |

### Wiki 读取（6 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `list_pages` | 列出 Wiki 页面（含 frontmatter 摘要） | `project`, `type_filter`, `folder`, `limit` |
| `read_page` | 读取页面内容（frontmatter + body + 链接） | `filename`*, `project` |
| `search` | TF-IDF 全文搜索（支持中韩英） | `query`*, `top_k`, `project` |
| `folder_tree` | 查看 Wiki 目录结构 | `project` |
| `recent_log` | 查看最近的 Wiki 日志条目 | `n`, `project` |
| `list_raw_sources` | 列出原始源文件（只读） | `project` |

### Wiki 写入（5 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `add_raw_source` | 添加不可变源文件到 raw/（append-only） | `filename`*, `content`*, `project` |
| `create_page` | 创建新 Wiki 页面（自动生成 frontmatter） | `title`*, `page_type`*, `content`, `folder`, `tags`, `sources` |
| `update_page` | 覆盖更新页面内容 | `filename`*, `content`*, `project` |
| `create_folder` | 创建 Wiki 文件夹 | `name`*, `parent`, `project` |
| `git_commit` | 提交 Wiki 变更到 git | `message`*, `project` |

### 知识图谱（13 个工具）

> 图谱工具通过 HTTP 异步调用 Dashboard API（`/api/graph/*`）实现。

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `graph_build` | 从 Wiki 页面构建知识图谱 | `project` |
| `graph_community` | 社区检测（连通分量） | `project` |
| `graph_god_nodes` | 获取最重要节点（最高度数） | `project`, `top_n` |
| `graph_stats` | 图谱统计信息 | `project` |
| `graph_shortest_path` | 两点间最短路径（BFS） | `source`*, `target`*, `project` |
| `graph_neighbors` | 获取节点的直接邻居 | `node_id`*, `project` |
| `graph_insights` | 图谱洞察（桥接页、孤立页、跨类型连接） | `project` |
| `graph_export` | 导出图谱（JSON 或 HTML 可视化） | `format`, `project` |
| `graph_composite` | 获取复合图谱数据（节点+边+社区+凝聚度） | `project` |
| `graph_rebuild` | 重建并持久化图谱 | `project` |
| `graph_name_community` | 为社区设置人类可读名称 | `community_id`*, `name`*, `project` |
| `graph_get_community` | 获取社区详情 | `community_id`*, `project` |
| `graph_insights` | 发现图谱中的有趣模式 | `project` |

### MCP 资源（3 个）

> MCP 资源是可订阅的只读数据端点，客户端可主动获取。

| 资源 URI | 功能 |
|----------|------|
| `memex://graph/stats` | 图谱统计摘要（纯文本） |
| `memex://graph/god-nodes` | Top 10 最重要节点（纯文本） |
| `memex://graph/insights` | 图谱洞察与建议（纯文本） |

### Wiki 智能操作（8 个工具）

> 这些工具触发 LLM 驱动的 Wiki 维护操作，通过 `wiki_ops.py` 实现。

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `wiki_ingest` | 完整 Ingest 流程（源文件 → Wiki 页面） | `title`*, `content`*, `folder`, `project` |
| `wiki_lint` | Wiki 审计（frontmatter/citation/orphan/freshness） | `project` |
| `wiki_lint_fix` | 自动修复审计问题 | `project` |
| `wiki_reflect` | 元分析：Wiki 模式识别与改进建议 | `window`, `project` |
| `wiki_compare` | 对比两个 Wiki 页面 | `page_a`*, `page_b`*, `save_as`, `project` |
| `wiki_write` | AI 写作助手（生成带引用的 Wiki 内容） | `topic`*, `length`, `style`, `project` |
| `wiki_validate_links` | 验证 Wiki 链接完整性与引用健康度 | `project` |
| `wiki_loop` | 执行 Wiki 维护循环（lint → lint_fix → reflect） | `steps`, `include_ingest`, `reflect_window`, `continue_on_error` |

### 跨项目知识宇宙（14 个工具）

> 跨项目操作，支持多个 Memex 项目的统一图谱和关联发现。

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `graph_universe` | 获取全项目统一图谱数据 | `project_filter`, `project` |
| `graph_universe_config` | 获取/更新宇宙配置 | `config`, `project` |
| `graph_join_universe` | 将项目加入知识宇宙 | `slug`*, `project` |
| `graph_leave_universe` | 从宇宙隐藏项目 | `slug`*, `project` |
| `graph_new_projects` | 检测新加入的项目 | `project` |
| `graph_project` | 获取单项目图谱 | `slug`*, `project` |
| `graph_bridges` | 获取跨项目虫洞（基于标题相似度/标签重叠） | `min_similarity`, `project` |
| `graph_search_universe` | 全宇宙搜索（标题/标签/类型匹配） | `query`*, `limit`, `project` |
| `graph_god_nodes_universe` | 全宇宙最重要节点 | `limit`, `project` |
| `graph_community_universe` | 全宇宙社区检测 | `project` |
| `graph_shortest_path_universe` | 跨项目最短路径（BFS） | `from_node`*, `to_node`*, `project` |
| `graph_insights_universe` | 全宇宙洞察（孤立页/跨项目连接/虫洞） | `project` |
| `graph_suggest_bridges` | 智能推荐潜在跨项目关联 | `limit`, `project` |
| `graph_add_bridge` | 手动创建跨项目关联 | `from_node`*, `to_node`*, `reason`, `project` |
| `graph_export_universe` | 导出完整宇宙数据（JSON） | `format`, `project` |

### 定时任务（6 个工具）

> 管理周期性 Wiki 维护任务，数据存储在 `.dashboard-settings.json` 中。

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `schedule_list` | 列出所有定时任务 | `project` |
| `schedule_create` | 创建定时任务 | `name`*, `cron`*, `steps`*, `enabled`, `project`, `include_ingest`, `reflect_window` |
| `schedule_delete` | 删除定时任务 | `schedule_id`* |
| `schedule_toggle` | 启用/禁用定时任务 | `schedule_id`*, `enabled`* |
| `schedule_run_now` | 立即执行定时任务 | `schedule_id`* |
| `schedule_get` | 获取定时任务详情 | `schedule_id`* |

---

## 架构说明

### 数据流

```
┌──────────────┐     stdio / HTTP      ┌──────────────────┐
│  MCP Client  │ ◄──────────────────► │  memex_mcp.py    │
│  (Claude等)  │                       │  (FastMCP server) │
└──────────────┘                       └────────┬─────────┘
                                                 │
                    ┌────────────────────────────┼──────────────────┐
                    │                            │                   │
              直接文件读写                   HTTP 调用           子进程调用
                    │                     (Dashboard API)       (wiki_ops)
                    │                            │                   │
            raw/ wiki/ .git             /api/graph/*           dashboard/
            .dashboard-settings.json     /api/graph/universe*   wiki_ops.py
            .memex/universe_config.json  /api/graph/rebuild*    (subprocess)
```

### 工具实现方式

| 类别 | 实现方式 | 依赖 |
|------|----------|------|
| 项目管理 | 直接调用 `project_registry.py` | 文件读写 |
| Wiki 读取 | 直接扫描 `wiki/` 目录 + 本地 TF-IDF | `project_registry`, `wiki_ops` |
| Wiki 写入 | 直接文件写入 + path traversal 防护 | `project_registry`, `wiki_ops` |
| 知识图谱 | 异步调用 Dashboard HTTP API (`/api/graph/*`) | `MEMEX_DASHBOARD_URL` |
| 跨项目宇宙 | 混合：本地计算 + Dashboard API 调用 | `project_registry`, Dashboard API |
| Wiki 智能操作 | 调用 `wiki_ops.py` 函数 | `wiki_ops` (触发 LLM CLI 子进程) |
| 定时任务 | 直接读写 `.dashboard-settings.json` | `wiki_ops.SETTINGS_FILE` |

### 关键设计约束

- **`raw/` 不可变**：`add_raw_source` 拒绝覆盖已存在的文件，防止源数据被意外修改
- **路径安全**：所有 wiki/raw 操作都经过 `_safe_wiki_path()` 防护，防止路径遍历攻击
- **项目隔离**：空 `project` 参数回退到当前激活项目或 legacy 单项目模式
- **图谱工具异步**：图谱工具通过 `_api_call()` 异步调用 Dashboard API，需要 Dashboard 服务运行中

---

## 快速验证

### 1. 测试 HTTP 模式启动

```bash
MEMEX_MCP_TRANSPORT=http MEMEX_MCP_PORT=8081 python3 mcp-server/memex_mcp.py
```

预期输出：
```
INFO:     Started server process [PID]
INFO:     Uvicorn running on http://0.0.0.0:8081
```

### 2. 测试工具列表

```bash
curl -s -N --max-time 3 http://127.0.0.1:8081/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

### 3. 测试工具调用

```bash
curl -s -N --max-time 5 http://127.0.0.1:8081/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}'
```

---

## 依赖

```
mcp>=1.2,<2
uvicorn>=0.30
```

> `mcp` 和 `uvicorn` 通过 `mcp-server/requirements.txt` 安装。Docker 构建时自动安装。
