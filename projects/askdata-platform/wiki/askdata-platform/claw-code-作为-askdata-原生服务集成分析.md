---
title: "Claw-Code 作为 AskData 原生服务集成分析"
type: analysis
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - claw-code
  - integration
  - dev-service
  - 分析
---

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

## 三、集成方案设计

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

# 2. 启动 claw-code（自动检测 CLAUDE.md）
claw "为 AskData 添加数据源同步功能，参考现有 datasource module 的模式"

# 3. Claw-Code 自动：
#    - 读取 CLAUDE.md 了解项目结构
#    - 规划实现步骤
#    - 读取现有代码
#    - 编写新代码
#    - 运行测试（make test-askdata）
#    - 提交代码（git commit）
#    - 创建分支和 PR

# 4. 后续补充
claw "修复刚才提交中的测试失败"
claw "为新的数据源功能添加 API 端点"
```

**优点**：
- 零额外开发，开箱即用
- CLAUDE.md 可以详细描述 AskData 的架构、编码规范、测试命令
- 适合功能探索和快速原型

**缺点**：
- 每次需要手动启动 CLI
- 无并发任务管理（单 Worker）
- 无持久化的任务队列
- Git 操作依赖 LLM 生成的 bash 命令，质量不稳定

### 方案 B: Claw-Code + Clawhip 事件驱动（推荐）

**核心思路**：利用 claw-code 生态的 `clawhip`（事件路由器）实现持久化的事件驱动开发服务。

```
┌────────────────────────────────────────────────────┐
│                   AskData Web 前端                  │
│              (功能需求/问题报告入口)                   │
└──────────────────┬─────────────────────────────────┘
                   │ HTTP API
┌──────────────────▼─────────────────────────────────┐
│               Task Queue / Dispatcher               │
│         (自定义: 接收需求 → 生成 TaskPacket)         │
└──────────────────┬─────────────────────────────────┘
                   │ TaskPacket
┌──────────────────▼─────────────────────────────────┐
│              Clawhip (Event Router)                 │
│   - 接收任务请求                                    │
│   - 调度 Claw-Code Worker                           │
│   - 监控 Worker 状态                                │
│   - 事件广播（SSE/WebSocket）                       │
└──┬───────────┬───────────┬──────────┬──────────────┘
   │           │           │          │
┌──▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Worker│  │Worker │  │Worker │  │Worker │
│  #1  │  │  #2   │  │  #3   │  │  #4   │
│feat-A│  │feat-B │  │fix-C  │  │test-D │
└──┬───┘  └───┬───┘  └───┬───┘  └───┬───┘
   │           │           │          │
   └───────────┴───────────┴──────────┘
               │
┌──────────────▼─────────────────────────────────────┐
│              Git Operations Layer                   │
│  - 自动分支创建                                     │
│  - 代码提交                                         │
│  - PR 创建                                         │
│  - 合并 (经 PolicyEngine 规则检查)                   │
└────────────────────────────────────────────────────┘
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
# 测试
make test-askdata
python -m pytest tests/ -v

# 数据库迁移
make db-migrate
make db-migrate-autogenerate

# 本地部署
cd deployments/deployment_local && ./deploy-local.sh up
```

## 编码规范
- 使用 Poetry 管理依赖
- 节点必须纯函数（无副作用）
- 新增模块必须配套测试
```

#### 2. TaskPacket（任务委派）

```json
{
  "objective": "为 datasource 模块添加 MongoDB 支持",
  "scope": "Module",
  "repo": "free-style-report",
  "worktree": true,
  "branch_policy": "create",
  "acceptance_tests": [
    "make test-askdata 通过",
    "新模块导入测试通过",
    "数据库连接测试通过"
  ],
  "commit_policy": "atomic",
  "reporting_contract": "clawhip",
  "escalation_policy": "on_failure_alert"
}
```

#### 3. 事件流

```
Task Created → Worker Spawned → Worker Ready → Code Changes → Test Run
  → Test Pass/Fail → (if fail) Recovery → Commit → PR Created → Policy Check
  → (if pass) Merge → Task Completed
```

**优点**：
- 持久化运行，自动接收和处理任务
- 支持多 Worker 并发
- 完整的事件追踪和状态广播
- PolicyEngine 自动管理合并流程
- 自动 git 分支管理和 PR

**缺点**：
- 需要部署和配置 clawhip（上游项目）
- 需要维护 Task Queue/Dispatcher 服务
- Git 操作仍依赖 LLM 的 bash 调用，需要 prompt 工程保证质量

### 方案 C: 自建轻量调度层（推荐起步）

**核心思路**：不依赖 clawhip，自建一个轻量 Python 调度服务，直接调用 claw-code CLI。

```
┌──────────────────────────────┐
│  REST API / Webhook          │
│  (接收开发任务)               │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│  Task Queue (Redis)          │
│  - 任务持久化                 │
│  - 状态追踪                   │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│  Worker Manager (Python)      │
│  - 管理 claw-code 进程        │
│  - 任务分配                   │
│  - 超时/重试                  │
│  - 结果收集                   │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│  Claw-Code Workers            │
│  (subprocess 调用)            │
│  - 加载 CLAUDE.md            │
│  - 执行开发任务               │
│  - 运行验证                   │
│  - Git 操作                   │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│  AskData 项目                 │
│  (git + 代码 + 测试)          │
└──────────────────────────────┘
```

```python
# 伪代码
class ClawCodeWorker:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.process = None

    async def run_task(self, task: TaskPacket) -> TaskResult:
        """启动 claw-code 执行开发任务"""
        cmd = ["claw", "--task", task.objective, "--worktree", task.scope]
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # 监控进程状态、输出、超时
        return await self._monitor_and_collect()

    async def _monitor_and_collect(self) -> TaskResult:
        """监控执行，收集结果（代码变更、git diff、测试结果）"""
        ...
```

**优点**：
- 不依赖外部上游项目（clawhip/oh-my-openagent）
- 轻量实现，2-3 周可交付
- 完全控制调度逻辑和失败处理
- 可与 AskData 的 SSE 流集成，实时反馈

**缺点**：
- 自建调度器需要维护
- 缺少 clawhip 的成熟事件系统（可后续迁移）

## 四、关键风险与缓解

| 风险 | 描述 | 缓解措施 |
|------|------|----------|
| **LLM 生成的 git 操作不稳定** | Claw-Code 通过 bash 调用 git，可能生成错误的命令 | 在 Worker Manager 层增加 git 操作沙箱验证 |
| **代码质量不可控** | Agent 生成的代码可能不符合规范 | CLAUDE.md 明确编码规范 + 集成 lint/type-check 作为验收步骤 |
| **并发冲突** | 多个 Worker 同时修改同一文件 | 启用 BranchLock + worktree 隔离 |
| **测试不充分** | Agent 可能跳过测试或测试不完整 | 验收标准强制包含测试，通过 make test-askdata 验证 |
| **恢复有限** | max_attempts=1，一次失败后需要人工介入 | 适合开发场景，复杂失败让人工判断 |

## 五、推荐方案

**起步**：方案 C（自建轻量调度层）+ CLAUDE.md 配置
- 2-3 周交付
- 验证核心流程
- 积累使用经验

**演进**：从方案 C 迁移到方案 B（clawhip）
- 当调度需求复杂时
- 需要更成熟的事件系统时
- 上游 clawhip 稳定后

**不做**：替换 LangGraph Orchestrator（这是另一个话题）
- Claw-Code 作为 **开发服务**，不是 **运行时服务**
- AskData 的用户分析流程仍然走 LangGraph
- Claw-Code 只负责 AskData 本身的代码开发和维护
