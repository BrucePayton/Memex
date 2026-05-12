# Memex MCP 服务配置文档

## 概述

Memex MCP 服务器提供 58 个工具，覆盖 wiki 管理、知识图谱操作、跨项目宇宙查询和定时维护任务。

---

## 启动方式

### 1. Stdio 模式（本地 Claude CLI 集成）

Claude Code 通过 stdio 直接调用，无需网络端口。

```bash
# claude mcp add memex -- python3 mcp-server/memex_mcp.py
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

### Wiki 管理（13 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `get_instructions` | 获取 wiki 架构规范（frontmatter/citation/contradiction） | `project` |
| `list_pages` | 列出 wiki 页面 | `project`, `type_filter`, `folder`, `limit` |
| `read_page` | 读取 wiki 页面内容 | `filename`*, `project` |
| `search` | TF-IDF 全文搜索 | `query`*, `top_k`, `project` |
| `folder_tree` | 查看 wiki 目录结构 | `project` |
| `recent_log` | 查看最近的 wiki 日志 | `n`, `project` |
| `list_raw_sources` | 列出原始源文件 | `project` |
| `add_raw_source` | 添加不可变源文件 | `filename`*, `content`*, `project` |
| `create_page` | 创建新 wiki 页面 | `title`*, `page_type`, `content`, `folder` |
| `update_page` | 更新 wiki 页面 | `filename`*, `content`*, `project` |
| `create_folder` | 创建 wiki 文件夹 | `name`*, `parent`, `project` |
| `git_commit` | 提交 wiki 变更到 git | `message`*, `project` |
| `list_template_names` | 列出项目模板 | - |

### 知识图谱（13 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `graph_build` | 构建项目图谱 | `project` |
| `graph_community` | 社区检测 | `project` |
| `graph_god_nodes` | 获取最重要节点（最高度） | `project`, `top_n` |
| `graph_stats` | 图谱统计信息 | `project` |
| `graph_shortest_path` | 两点间最短路径 | `source`*, `target`*, `project` |
| `graph_neighbors` | 获取节点的邻居 | `node_id`*, `project` |
| `graph_insights` | 图谱洞察（桥接页、孤立页） | `project` |
| `graph_export` | 导出图谱 | `format`, `project` |
| `graph_composite` | 获取复合图谱数据 | `project` |
| `graph_rebuild` | 重建图谱 | `project` |
| `graph_name_community` | 命名社区 | `community_id`*, `name`*, `project` |
| `graph_get_community` | 获取社区详情 | `community_id`*, `project` |
| `graph_neighbors` | 获取邻居节点 | `node_id`*, `project` |

### Wiki 智能操作（9 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `wiki_ingest` | 导入源文件到 wiki | `title`*, `content`*, `folder`, `project` |
| `wiki_lint` | 运行 wiki 审计 | `project` |
| `wiki_lint_fix` | 自动修复审计问题 | `project` |
| `wiki_reflect` | 元分析 wiki 模式和改进建议 | `window`, `project` |
| `wiki_compare` | 对比两个 wiki 页面 | `page_a`*, `page_b`*, `save_as`, `project` |
| `wiki_write` | 生成 wiki 页面内容 | `topic`*, `length`, `style`, `project` |
| `wiki_validate_links` | 验证 wiki 链接完整性 | `project` |
| `wiki_loop` | 执行 wiki 维护循环 | `steps`, `include_ingest`, `project` |
| `create_project` | 创建新项目 | `slug_hint`*, `title`*, `description`, `model` |

### 跨项目宇宙（14 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `graph_universe` | 获取全项目统一图谱 | `project_filter`, `project` |
| `graph_universe_config` | 获取/更新宇宙配置 | `config`, `project` |
| `graph_join_universe` | 将项目加入宇宙 | `slug`*, `project` |
| `graph_leave_universe` | 从宇宙隐藏项目 | `slug`*, `project` |
| `graph_new_projects` | 检测新项目 | `project` |
| `graph_project` | 获取单项目图谱 | `slug`*, `project` |
| `graph_bridges` | 获取跨项目虫洞 | `min_similarity`, `project` |
| `graph_search_universe` | 全宇宙搜索 | `query`*, `limit`, `project` |
| `graph_god_nodes_universe` | 全宇宙最重要节点 | `limit`, `project` |
| `graph_community_universe` | 全宇宙社区检测 | `project` |
| `graph_shortest_path_universe` | 跨项目最短路径 | `from_node`*, `to_node`*, `project` |
| `graph_insights_universe` | 全宇宙洞察 | `project` |
| `graph_suggest_bridges` | 智能推荐虫洞 | `limit`, `project` |
| `graph_add_bridge` | 人工创建跨项目关联 | `from_node`*, `to_node`*, `reason`, `project` |
| `graph_export_universe` | 导出完整宇宙 | `format`, `project` |

### 定时任务（6 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `schedule_list` | 列出所有定时任务 | `project` |
| `schedule_create` | 创建定时任务 | `name`*, `cron`*, `steps`* |
| `schedule_delete` | 删除定时任务 | `schedule_id`* |
| `schedule_toggle` | 启用/禁用定时任务 | `schedule_id`*, `enabled`* |
| `schedule_run_now` | 立即执行定时任务 | `schedule_id`* |
| `schedule_get` | 获取定时任务详情 | `schedule_id`* |

### 其他（3 个工具）

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `list_projects` | 列出所有项目 | - |
| `switch_project` | 切换当前项目 | `slug`* |
| `update_project_settings` | 更新项目设置 | `slug`*, `model`, `title`, `description` |
| `delete_project` | 删除项目 | `slug`*, `confirm` |
| `stats` | 获取 wiki 统计 | `project` |

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

### 2. 测试 initialize 请求

```bash
curl -s -N --max-time 3 http://127.0.0.1:8081/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"initialize",
    "params":{
      "protocolVersion":"2025-03-26",
      "capabilities":{},
      "clientInfo":{"name":"test","version":"0.1"}
    }
  }'
```

预期返回 SSE 事件流：
```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-03-26",...}}
```

### 3. 测试工具列表

```bash
curl -s -N --max-time 3 http://127.0.0.1:8081/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/list"
  }'
```

### 4. 测试工具调用

```bash
curl -s -N --max-time 5 http://127.0.0.1:8081/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "id":3,
    "method":"tools/call",
    "params":{
      "name":"list_projects",
      "arguments":{}
    }
  }'
```

---

## 依赖

```
mcp>=1.2,<2
uvicorn>=0.30
```
