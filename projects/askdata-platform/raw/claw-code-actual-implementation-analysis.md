# Claw Code 在 FSR 中的实际落地分析

> 基于代码库 `core/claw/` 的实际扫描结果，记录于 2026-05-04

## 实现概览

`core/claw/` 下共 13 个 Python 源文件，1,757 行代码。分为三个层级：

### 第一层：生产活跃（Active）
| 文件 | 行数 | 状态 |
|------|------|------|
| `engine.py` | 221 | 任务执行引擎，按 domain 路由，发射事件，触发恢复 |
| `llm_client.py` | 154 | LLM 客户端，含热更新，已被 project-wide 使用 |
| `worker_registry.py` | 160 | 基于 Redis 的 Worker 注册与发现 |
| `worker_manager.py` | 125 | 异步任务队列、提交/消费循环 |
| `recovery.py` | 113 | 7 种恢复策略 |
| `events.py` | 129 | LaneEvent 持久化与查询 |
| `hooks.py` | 61 | PRE/POST 任务钩子系统 |
| `metrics.py` | 225 | 指标收集（任务/LLM/Worker 维度） |
| `worker.py` | 35 | FastAPI ASGI 入口（claw-worker 容器） |
| `models.py` | 174 | TaskPacket、LaneEvent、Checkpoint 等数据模型 |

### 第二层：已实现但无运行时消费者（Orphaned）
| 文件 | 行数 | 原因 |
|------|------|------|
| `policy_engine.py` | 122 | Rule/Priority 引擎完整，但未注册任何规则，无调用方 |
| `branch_lock.py` | 74 | Redis 分布式锁，但没有任何文件 import |
| `alerts.py` | 164 | AlertManager 存在，但只在 API 按需返回，无主动评估循环 |

### 第三层：构想/骨架（Aspirational）
- `page_group_defaults.py` 中 Claw 前端入口已注释掉
- `mcp_domain_manager.py` 中 2 处 TODO 注释（MCP 客户端集成未实现）
- `claw-mcp-server` 容器定义存在，但 MCP ↔ Claw 集成路径是空的

## API 端点

`claw_router` 注册在 `/api/claw/` 下，共 11 个端点：
- `POST /sessions`、`GET /sessions/{id}`
- `POST /tasks`、`GET /tasks/{id}`、`GET /sessions/{id}/tasks`
- `GET /events/{session_id}`
- `GET /workers`
- `GET /health`、`GET /metrics`、`GET /alerts`

另：LLM 配置端点 `GET/POST /api/config/llm/claw`。

## 部署

- `docker-compose.claw.yaml` 定义 `claw-worker` + `claw-mcp-server` 两个容器
- Nginx 路由 `/api/claw/mcp/` → `claw-mcp-server:8000`
- `deploy-local.sh` 支持 `claw` 子命令
- `CLAUDE_ENABLED=true` 时启用

## 关键发现：llm_client 已超越 Claw 边界

`global_llm_client` 不仅在 `engine.py` 中使用，还被：
- `domain_config_manager.py` — 用于标签生成
- `scope_config.py` — 作为 `chat()`/`chat_stream()` 的统一 LLM 入口

这意味着 `ClawLLMClient` 已事实上成为项目的**全局 LLM 网关**。
