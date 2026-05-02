---
title: "Memex CLI 对接模式分析与 AskData 借鉴"
type: analysis
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - memex
  - cli-integration
  - mcp
  - 分析
---

# Memex CLI 对接模式分析与 AskData 借鉴

## 一、Memex 的三重 CLI 对接模式

Memex 已经实现了一套完整的 CLI 工具集成方案，包含三个层次：

### 模式 1: MCP Server（工具暴露层）

MCP Server 是 Memex 的核心对接方式，通过 `mcp-server/memex_mcp.py` 暴露 14 个工具给任何 MCP 客户端（Claude Code、Claude Desktop 等）。

```
┌──────────────┐     stdio      ┌─────────────────┐
│  Claude Code │◄──────────────►│  memex_mcp.py   │
│  (CLI Agent) │   MCP Protocol │  (14 Tools)     │
└──────────────┘                └─────────────────┘
```

**注册方式**：
```bash
claude mcp add --scope user memex \
  -- "$PWD/mcp-server/.venv/bin/python" "$PWD/mcp-server/memex_mcp.py"
```

**14 个工具分工**：

| 只读工具（7 个） | 写入工具（5 个） | 管理工具（2 个） |
|------------------|------------------|------------------|
| `list_projects` | `add_raw_source` | `get_instructions` |
| `stats` | `create_page` | `folder_tree` |
| `list_pages` | `update_page` | `list_raw_sources` |
| `read_page` | `create_folder` | |
| `search` | `git_commit` | |
| `recent_log` | | |

**关键设计决策**：
- MCP Server 是 **独立的 Python 进程**，不依赖 dashboard 服务
- Transport 使用 **stdio**（而非 SSE），意味着可以直接通过 `claude mcp add` 注册
- 每个工具接受可选的 `project` 参数，空值回退到 active project
- `add_raw_source` 是 **append-only** 的（raw 目录不可变）
- `git_commit` 自动 stage 特定路径，使用带前缀的 commit message

### 模式 2: CLI Subprocess（任务执行层）

Dashboard 服务（Python HTTP Server）通过 subprocess 调用 Claude Code CLI 执行自动化任务。

```python
# dashboard/server.py
cmd = [
    exe, "-p",                        # pipe mode（非交互式）
    "--allowedTools", "Edit,Write,Read,Glob,Grep",  # 权限限制
    "--model", model,                 # 可选模型选择
    "--output-format", "text",        # 文本输出
    prompt                            # 任务描述
]
subprocess.run(cmd, cwd=project.root, env=_cli_subprocess_env(), timeout=600)
```

**关键模式**：
- `cwd=project.root` — 每个 CLI 调用 **限定在项目目录内**，Agent 只能操作自己项目的文件
- `--allowedTools` — 精确控制 Agent 可使用的文件操作权限
- 超时保护 — 默认 600s，通过 `CLAUDE_TIMEOUT` 环境变量可配置
- 环境变量注入 — 通过 `_cli_subprocess_env()` 传递 API key 等凭证

### 模式 3: Vendor Wrapper（多 LLM 供应商适配层）

为支持不同 LLM 提供商，Memex 实现了 vendor wrapper 脚本模式。

```
scripts/memex-claw-vendor.sh  ──安装──►  ~/bin/memex-claw-anthropic
                                          ~/bin/memex-claw-dashscope
                                          ~/bin/memex-claw-qwen
```

**工作原理**：
```bash
#!/bin/bash
# memex-claw-vendor.sh 核心逻辑
source "${VENDOR_ENV_FILE}"   # 加载 API key 等环境变量
exec claw "$@"                # 代理到实际的 claw 二进制
```

**解决的核心问题**：
- Dashboard subprocess 无法看到 shell alias
- 不同 LLM 需要不同的 API key 配置
- 通过 wrapper 隔离环境变量，每个 vendor 独立配置

## 二、多项目隔离机制

Memex 的项目隔离设计非常精巧，值得 AskData 直接借鉴：

### 项目注册表

```json
// projects.json
{
  "version": 1,
  "active": "askdata-platform",  // 当前活动项目
  "projects": [
    {
      "slug": "askdata-platform",
      "title": "AskData Platform",
      "description": "...",
      "model": "default",
      "template": "llm-research"
    }
  ]
}
```

### 项目目录结构

```
projects/<slug>/
├── CLAUDE.md            # 项目级 schema（从模板复制，可自定义）
├── .settings.json       # 项目级模型配置
├── wiki/                # LLM 维护的 wiki 页面
│   ├── index.md         # 内容目录
│   ├── log.md           # 活动时间日志
│   └── <folders>/       # 按 topic/concept/entity 等分类
├── raw/                 # 不可变源文档（append-only）
├── ingest-reports/      # 每次 ingests 的 WHY 报告
├── reflect-reports/     # 定期元分析报告
└── plans/               # 项目任务队列
```

### 项目切换

| 入口 | 方式 |
|------|------|
| Dashboard | `POST /api/projects/switch` 更新 `projects.json` 的 active 字段 |
| MCP | 工具参数 `project="slug"` |
| Legacy | 无 `projects.json` 时，root `wiki/` + `raw/` 作为 fallback |

### 项目创建

```
POST /api/projects/create → create_project() → 创建目录 → 复制模板 CLAUDE.md
→ 初始化 wiki/index.md + wiki/log.md
```

## 三、对 AskData + Claw-Code 集成的直接借鉴

### 借鉴 1: MCP Server 作为标准对接接口

Memex 的 `memex_mcp.py` 已经证明，用 Python + `mcp` SDK 暴露工具给 Claude Code 是可行且稳定的模式。

**对 AskData 的适用性**：

可以创建一个 `askdata-mcp` 服务，暴露 AskData 专用的操作工具：

```python
# askdata_mcp.py（参考 memex_mcp.py 模式）
from mcp.server import Server
from mcp.types import Tool

@mcp.tool()
async def get_project_structure() -> str:
    """返回 AskData 项目当前目录结构"""

@mcp.tool()
async def run_tests(module: str = None) -> str:
    """运行指定模块的测试"""

@mcp.tool()
async def create_branch(name: str) -> str:
    """创建 git 分支"""

@mcp.tool()
async def get_agent_context(scope: str) -> str:
    """获取指定 Agent 的上下文（prompt + tools + state）"""

@mcp.tool()
async def execute_workflow(workflow: str, params: dict) -> dict:
    """执行 AskData 工作流并返回结果"""
```

**关键价值**：
- 任何 MCP 客户端（claw-code、claude-code）都能直接调用 AskData 的操作
- 不需要修改 claw-code 本身，只需注册一个新的 MCP Server
- 与 Memex 完全一致的模式，已有验证

### 借鉴 2: CLI Subprocess + Project Scope 模式

Memex 的 `claude -p --allowedTools ... cwd=project.root` 模式可以直接应用到 claw-code：

```python
# 伪代码 — Worker Manager 模式
async def run_claw_task(task: dict, project_path: str):
    cmd = [
        "claw",           # 或 memex-claw-anthropic（vendor wrapper）
        "-p",             # pipe mode
        "--dangerously-skip-permissions",  # 跳过信任确认
        task["prompt"],
    ]
    result = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=project_path,      # 限定在项目目录
        env=vendor_env,        # 注入 LLM API key
        stdout=asyncio.subprocess.PIPE,
    )
    return await result.communicate()
```

**与 Memex 的对应**：

| Memex 做法 | AskData 适配 |
|------------|-------------|
| `cwd=project.root` | `cwd=free_style_report/` |
| `--allowedTools Edit,Write,Read,Glob,Grep` | 相同模式，限制文件操作 |
| `_cli_subprocess_env()` | Vendor wrapper 注入 API key |
| `CLAUDE_TIMEOUT=600` | 可配置超时 |

### 借鉴 3: Vendor Wrapper 模式

Memex 的 `memex-claw-vendor.sh` **已经支持 claw-code**！

```bash
# Memex 已有的 vendor wrapper 支持
~/bin/memex-claw-anthropic    → 使用 Anthropic API
~/bin/memex-claw-dashscope    → 使用 DashScope API
~/bin/memex-claw-qwen         → 使用 Qwen API
```

**对 AskData 的意义**：
- **不需要自己实现 wrapper** — Memex 已有现成的 `memex-claw-vendor.sh`
- 可以在 AskData 的调度服务中直接使用 `memex-claw-anthropic` 作为 CLI 二进制
- 支持多 LLM 供应商自动适配

### 借鉴 4: 项目注册 + 项目隔离

Memex 的 `projects.json` + `Project` dataclass 模式可以用于管理多个 AskData 的部署实例：

```json
// 类似 projects.json 的 AskData 注册表
{
  "version": 1,
  "active": "free-style-report",
  "projects": [
    {
      "slug": "free-style-report",
      "title": "AskData Platform",
      "path": "/path/to/free-style-report",
      "cli_binary": "memex-claw-anthropic",
      "allowed_tools": "Edit,Write,Read,Glob,Grep,Bash,Agent",
      "test_command": "make test-askdata"
    }
  ]
}
```

### 借鉴 5: CLAUDE.md Schema 模式

Memex 每个项目都有自己的 `CLAUDE.md`（从模板复制），这是 AskData 最需要的。

```markdown
# Free-Style-Report CLAUDE.md（AskData 项目专用）

## 项目架构
- 后端: FastAPI + LangGraph (Python 3.12, Poetry)
- 前端: React + TypeScript + Vite + TailwindCSS
- 数据库: PostgreSQL + Redis
- 工作流: LangGraph StateGraph（graphs/builder.py）

## 编码规范
- 节点必须是纯函数（无副作用）
- 使用 Poetry 管理依赖
- 新增模块必须配套测试
- Orchestrator 节点必须通过路由规则测试

## 验证命令
- 测试: make test-askdata
- 迁移: make db-migrate-autogenerate
- 部署: cd deployments/deployment_local && ./deploy-local.sh up

## 重要文件
- 入口: main.py, core/server/app.py
- Orchestrator: graphs/builder.py
- 配置: configs/basic_config.py
```

## 四、AskData + Claw-Code 集成：Memex 模式方案

基于 Memex 的已验证模式，重新审视 AskData 集成方案：

```
┌────────────────────────────────────────────────────────────┐
│                    AskData Web 前端                         │
│              (功能需求/问题报告入口)                           │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼─────────────────────────────────────┐
│          AskData Worker Manager (Python)                    │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │ Task Queue      │  │ CLI Subprocess Manager          │  │
│  │ (Redis)         │─►│ - subprocess.run("claw", ...)   │  │
│  │                 │  │ - cwd=free_style_report/        │  │
│  │                 │  │ - vendor wrapper for API keys   │  │
│  └─────────────────┘  └─────────────────┬───────────────┘  │
│                                          │                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ AskData MCP Server (Python, mcp SDK, stdio)          │  │
│  │ - get_project_structure                              │  │
│  │ - run_tests, create_branch, git_commit               │  │
│  │ - execute_workflow, get_agent_context                │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                             │ 注册方式:                     │
│                             │ claude mcp add --scope user   │
│                             │ askdata -- python askdata_mcp │  │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │ Memex Vendor Wrapper (已存在)                         │  │
│  │ - memex-claw-anthropic                               │  │
│  │ - memex-claw-dashscope                               │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│          AskData 项目 (free-style-report/)                  │
│  ├── CLAUDE.md (项目级 Agent 指令)                          │
│  ├── .claw/ (会话持久化)                                    │
│  └── .claw.json (项目配置)                                  │
└────────────────────────────────────────────────────────────┘
```

**关键优势**：
1. **MCP Server** — AskData 暴露操作给任何 MCP 客户端
2. **CLI Subprocess** — Worker Manager 调用 claw-code 执行任务（与 Memex 相同模式）
3. **Vendor Wrapper** — 复用 Memex 已有的 `memex-claw-vendor.sh`，支持多 LLM
4. **CLAUDE.md** — AskData 项目级 schema，让 Agent 理解代码结构

## 五、Memex 模式 vs 之前方案对比

| 维度 | 之前方案 C（自建调度） | Memex 模式（改进版） |
|------|----------------------|---------------------|
| **CLI 调用** | 直接 `claw ...` | 通过 vendor wrapper `memex-claw-*` |
| **多 LLM** | 需自建 | Memex 已有 wrapper，零开发 |
| **工具暴露** | 无 | MCP Server（14 工具标准模式） |
| **项目隔离** | 手动管理 cwd | Project Registry + cwd 限定 |
| **项目切换** | 不支持 | 通过 registry 切换 |
| **权限控制** | 需自建 | `--allowedTools` 原生支持 |
| **开发量** | 2-3 周 | 1-2 周（大量复用） |

## 六、推荐实施路径

**Phase 0: 准备（1 周）** — 先做 Memex 已验证的基础设施
1. 在 AskData 项目根目录创建 `CLAUDE.md`
2. 安装 Memex vendor wrappers: `./scripts/install-memex-cli-wrappers.sh`
3. 注册 Memex MCP Server（已有）确认工作流

**Phase 1: 轻量 CLI 对接（1-2 周）** — 复用 Memex 模式
1. 创建 AskData Worker Manager（Python asyncio subprocess）
2. 使用 vendor wrapper 调用 claw-code
3. 实现 Task Queue（Redis）
4. 集成 AskData MCP Server

**Phase 2: 增强（2-3 周）** — 超出 Memex 模式的部分
1. AskData MCP Server 开发（项目结构、测试、工作流等工具）
2. PolicyEngine 路由规则化
3. 集成 AskData SSE 流实时反馈
