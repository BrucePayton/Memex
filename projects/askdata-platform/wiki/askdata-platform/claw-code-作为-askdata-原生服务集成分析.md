# Claw-Code 作为 AskData 原生服务集成分析

## 一、用户设想

把 claw-code 作为 AskData 平台的 **原生开发服务** 接入，后续完善功能或新增功能时，通过 claw-code 直接完成代码变更，并自动管理 git 操作（分支、提交、PR、合并等）。

**核心诉求**：claw-code 不只是代码修复工具，而是整个项目的 "开发运维 Agent" —— 从需求到代码到部署的全自动化。

## 二、Claw-Code 当前能力边界

### 已具备的能力

| 能力 | 说明 | 对 AskData 的价值 |
|------|------|------------------|
| **CLI Agent Runtime** | 交互式 REPL / one-shot prompt，自动工具执行循环 | 作为 AskData 的开发 Agent 入口 |
| **Worker 生命周期** | 多 Worker 状态机（Spawning → Ready → Running → Finished/Failed） | 管理多个并发开发任务 |
| **TaskPacket** | 结构化任务委派（目标/范围/验收标准/升级策略） | 把需求转化为可执行的开发任务 |
| **GitContext** | 读取 git 状态（diff、branch、status） | 了解当前代码变更 |
| **RecoveryRecipes** | 7 种故障恢复策略 | 自动从常见开发失败中恢复 |
| **MCP 集成** | 6 种传输方式（Stdio/SSE/HTTP/WebSocket/SDK/ManagedProxy） | 可扩展 AskData 专用工具 |
| **Session 持久化** | JSONL 格式、workspace 指纹、原子写入 | 跨会话保持开发上下文 |
| **Hooks 系统** | PreToolUse/PostToolUse 生命周期钩子 | 可插拔的代码质量检查 |
| **PolicyEngine** | 规则引擎（条件→动作），支持优先级和链式动作 | 声明式管理开发流程策略 |
| **LaneEvents** | 丰富的事件分类体系 | 追踪开发任务状态变化 |
| **BranchLock** | 多 Lane 并发时的分支冲突检测 | 防止并行开发冲突 |

### 关键缺口

| 缺口 | 影响 | 是否需要补充 |
|------|------|-------------|
| **不是后台服务** | Claw-Code 是 CLI 工具（REPL/one-shot），不是持久运行的 daemon | 需要封装一层调度服务 |
| **Git 操作只读** | GitContext 仅读取 git 状态，commit/push/PR 通过 LLM 的 bash 调用完成，非内置 | 需要通过 agent prompt + tools 实现 |
| **无 CI/CD 编排** | 只有标准 GitHub Actions，无部署流水线编排 | 需要外部 CI 或自建 |
| **自主运行需上游** | WorkerRegistry 和 LaneEvents 需要 `clawhip`（事件路由器）和 `oh-my-openagent`（多 Agent 协调器） | 需要接入或自建 |
| **恢复限制** | 所有恢复配方 max_attempts=1，一次失败后升级给人 | 适合开发场景 |

### 结论

Claw-Code **不是** 开箱即用的后台服务，但它的 Worker/Task/Policy 架构为构建 "开发运维 Agent" 提供了完整的底层能力。需要：

1. **封装一层调度服务** 让它能够接受外部请求并持久运行
2. **配置 AskData 项目的 CLAUDE.md** 让它理解 AskData 的代码结构和工作流
3. **补充 git 操作工具链** 通过 Agent prompt + bash 或自定义 MCP 工具实现

## 三、集成方案设计（参考 Memex 已验证模式）

> **Memex 模式参考**：Memex 项目（`/Users/aiassistant/Projects/OpenSourceProjects/MEMEX/Memex`）已实现完整的 CLI 集成方案，包含 MCP Server + CLI Subprocess + Vendor Wrapper 三重对接模式。Memex 的 `memex-claw-vendor.sh` 已原生支持 claw-code。详见 [[Memex CLI 对接模式分析与 AskData 借鉴]]。

### 方案 A: 项目级 CLAUDE.md + Claw-Code 手动驱动

**最小可行方案**。在 AskData 项目根目录放置 CLAUDE.md，通过 claw-code CLI 手动触发开发任务。

```
# 在 AskData 项目根目录
free-style-report/
├── CLAUDE.md          # 项目级 Agent 指令（架构、工作流、验证命令）
├── .claw/             # Claw-Code 会话持久化
│   ├── session.jsonl  # 对话历史
│   └── worker-state/  # Worker 状态
└── .claw.json         # Claw-Code 项目配置
```

**工作流**：
```bash
# 1. 进入 AskData 项目目录
cd free-style-report

# 2. 使用 Memex vendor wrapper 启动 claw-code
claw "为 AskData 添加数据源同步功能"

# 3. Claw-Code 自动：
#    - 读取 CLAUDE.md 了解项目结构
#    - 规划实现步骤 → 编写代码 → 运行测试 → 提交
```

**优点**：
- 零额外开发，开箱即用
- CLAUDE.md 可以详细描述 AskData 的架构、编码规范、测试命令

**缺点**：
- 每次需要手动启动 CLI
- 无并发任务管理、无持久化任务队列

### 方案 B: Memex 三重模式集成（推荐起步）

**核心思路**：直接复用 Memex 的已验证集成模式，最小化自建开发。

```
┌──────────────────────────────────────────────────────────────┐
│                    AskData Worker Manager                     │
│  ┌──────────────┐  ┌──────────────────────┐  ┌────────────┐  │
│  │ Task Queue   │─►│ CLI Subprocess       │─►│ Vendor     │  │
│  │ (Redis)      │  │ (claw -p, cwd=...)   │  │ Wrapper    │  │
│  │              │  │ --allowedTools ...   │  │ (已有)     │  │
│  └──────────────┘  └──────────────────────┘  └────────────┘  │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │ AskData MCP Server (mcp SDK, stdio)                     │       │
│  │ - get_project_structure, run_tests, create_branch       │       │
│  │ - execute_workflow, get_agent_context                   │       │
│  │ 注册: claude mcp add --scope user askdata -- python ... │       │
│  └─────────────────────────────────────────────────────────┘       │
└──────────────────────┬───────────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│          AskData 项目 (free-style-report/)                      │
│  ├── CLAUDE.md (项目级 Agent 指令)                              │
│  ├── .claw/ (会话持久化)                                        │
│  └── .claw.json (项目配置)                                      │
└────────────────────────────────────────────────────────────────┘
```

**与方案 C 的区别**：直接复用 Memex 已有的 vendor wrapper（`memex-claw-anthropic` 等），无需自建 LLM 供应商适配层。

**开发量**：1-2 周（vs 方案 C 的 2-3 周）

```python
# 伪代码 — 复用 Memex 模式
async def run_claw_task(task: dict, project_path: str):
    cmd = [
        "memex-claw-anthropic",  # Memex 已有 vendor wrapper
        "-p",                     # pipe mode
        "--dangerously-skip-permissions",
        task["prompt"],
    ]
    result = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=project_path,         # 限定在项目目录（Memex 模式）
        env=vendor_env,           # wrapper 自带 API key
    )
    return await result.communicate()
```

**核心组件**：

#### 1. CLAUDE.md（项目上下文）

```markdown
# Free-Style-Report 开发指南

## 项目架构
- 后端: FastAPI + LangGraph (Python 3.12)
- 前端: React + TypeScript + Vite
- 数据库: PostgreSQL + Redis
- 工作流: LangGraph StateGraph

## 关键目录
- `graphs/builder.py` - Orchestrator 状态图
- `core/modules/` - 业务模块
- `resources/agents/` - Agent 定义
- `web/src/` - 前端代码

## 验证命令
```bash
make test-askdata
make db-migrate
cd deployments/deployment_local && ./deploy-local.sh up
```
```

#### 2. 事件流

```
Task Created → Worker Spawned → Code Changes → Test Run
  → (fail) Recovery → (pass) Commit → PR → Policy Check → Merge
```

**优点**：
- 复用 Memex 已有的 vendor wrapper，支持多 LLM 无需自建
- MCP Server 标准接口，任何 MCP 客户端都能对接
- 轻量实现，1-2 周可交付
- 可与 AskData 的 SSE 流集成，实时反馈

**缺点**：
- 依赖 Memex 的 vendor wrapper 脚本（需安装）
- Git 操作仍依赖 LLM 的 bash 调用

### 方案 C: Claw-Code + Clawhip 事件驱动（长期目标）

**核心思路**：利用 claw-code 生态的 `clawhip`（事件路由器）实现持久化的事件驱动开发服务。

```
┌────────────────────────────────────────────────────┐
│                   AskData Web 前端                  │
└──────────────────┬─────────────────────────────────┘
                   │ Task Queue / Dispatcher
┌──────────────────▼─────────────────────────────────┐
│              Clawhip (Event Router)                 │
└──┬───────────┬───────────┬──────────┬──────────────┘
   │           │           │          │
┌──▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Worker│  │Worker │  │Worker │  │Worker │
│  #1  │  │  #2   │  │  #3   │  │  #4   │
└──────┘  └───────┘  └───────┘  └───────┘
```

**优点**：
- 持久化运行，自动接收和处理任务
- 支持多 Worker 并发，完整事件追踪
- PolicyEngine 自动管理合并流程

**缺点**：
- 需要部署和配置 clawhip（上游项目）
- 需要维护 Task Queue/Dispatcher 服务

## 四、关键风险与缓解

| 风险 | 描述 | 缓解措施 |
|------|------|----------|
| **LLM 生成的 git 操作不稳定** | 通过 bash 调用 git，可能生成错误命令 | Worker Manager 层增加 git 操作沙箱验证 |
| **代码质量不可控** | Agent 生成的代码可能不符合规范 | CLAUDE.md 明确编码规范 + lint/type-check 验收 |
| **并发冲突** | 多个 Worker 同时修改同一文件 | 启用 BranchLock + worktree 隔离 |
| **测试不充分** | Agent 可能跳过测试 | 验收标准强制包含测试 |
| **恢复有限** | max_attempts=1，一次失败后需要人工介入 | 适合开发场景 |

## 五、推荐方案演进路径

```
Phase 0 (1 周)       Phase 1 (1-2 周)       Phase 2 (2-3 周)
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ CLAUDE.md    │───►│ Memex 三重模式   │───►│ 增强 + Clawhip   │
│ Vendor 安装  │    │ CLI Subprocess   │    │ 路由规则化       │
│ MCP 确认     │    │ AskData MCP      │    │ PolicyEngine     │
└──────────────┘    └──────────────────┘    └──────────────────┘
  验证基础          自动化开发流程            成熟事件驱动
```

**不做**：替换 LangGraph Orchestrator
- Claw-Code 作为 **开发服务**，不是 **运行时服务**
- AskData 的用户分析流程仍然走 LangGraph
- Claw-Code 只负责 AskData 本身的代码开发和维护
