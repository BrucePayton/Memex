---
title: "AskData Orchestrator 优化规划"
type: analysis
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - orchestration
  - optimization
  - 规划
---

# AskData Orchestrator 优化规划

## 优化目标

1. 消除 God-Node，路由决策规则化
2. 支持真正的动态并发执行
3. 节点间显式数据契约
4. 声明式故障恢复
5. 提升可测试性和可观测性

## 分阶段实施计划

---

### Phase 1: 路由决策规则化（2-3 周）

**目标**：消除 `orchestrator_domain_routing_node` 单体决策逻辑

#### 1.1 实现 Python PolicyEngine

参考 Claw-Code `policy_engine.rs`，用 Python 实现轻量规则引擎：

```python
class PolicyEngine:
    """声明式规则引擎，替代 if/else 瀑布"""
    
    rules: list[PolicyRule]  # 按优先级排序
    
    def evaluate(self, state: State) -> PolicyAction:
        """按优先级匹配规则，返回第一个匹配的动作"""
        for rule in self.rules:
            if rule.condition.match(state):
                return rule.action.execute(state)
```

**规则示例**：
```python
rules = [
    PolicyRule(
        name="fast_sql_replay",
        condition=And(HasSqlArtifact(), ExactQuestionMatch()),
        action=BranchTo("askdata_sql_artifact_replay")
    ),
    PolicyRule(
        name="supper_short_path",
        condition=And(HasSupperAgent(), PlannerGateMet(), Not(NeedsReport())),
        action=BranchTo("supper_dispatch")
    ),
    PolicyRule(
        name="needs_clarification",
        condition=Or(FuzzyQuestion(), AmbiguousDomain()),
        action=BranchTo("askdata_decision_shell")
    ),
    PolicyRule(
        name="deep_analysis_path",
        condition=And(PlannerGateMet(), NeedsReportOrDashboard()),
        action=BranchTo("askdata_artifact_preflight")
    ),
]
```

#### 1.2 路由规则外部化

将路由规则从代码中抽离到 YAML 配置：

```yaml
# assets/orchestrator/routing_rules.yaml
rules:
  - name: fast_sql_replay
    when:
      has_sql_artifact: true
      exact_question_match: true
    then: askdata_sql_artifact_replay
    
  - name: supper_qa
    when:
      intent: data_qa
      has_supper_agent: true
      planner_gate: met
    then: supper_dispatch
    
  - name: need_clarification
    when:
      question_breadth: wide
      time_context: missing
    then: askdata_decision_shell
```

#### 1.3 测试验证

- 为每条路由规则编写单元测试
- 覆盖所有 intent × resource 组合
- 确保与原行为一致（回归测试）

**产出**：
- `core/executor/policy_engine.py` — PolicyEngine 实现
- `assets/orchestrator/routing_rules.yaml` — 路由规则配置
- `tests/orchestrator/test_policy_engine.py` — 规则测试

---

### Phase 2: 数据契约化（2 周）

**目标**：消除 ~90 字段的全局 State 共享

#### 2.1 定义 TaskPacket

参考 Claw-Code `task_packet.rs`：

```python
@dataclass
class TaskPacket:
    """节点间传递的显式数据契约"""
    task_id: str
    objective: str                    # 目标描述
    scope: TaskScope                  # 作用域
    preconditions: dict               # 前置条件
    inputs: dict                      # 输入数据引用
    expected_outputs: list[str]       # 期望输出字段
    acceptance_criteria: list[str]    # 验收标准
    timeout_seconds: int | None       # 超时
    fallback: str | None              # 失败时降级策略
```

#### 2.2 State 分区

将当前 90 字段的 State 按 ownership 分区：

```python
@dataclass
class IntentContext:         # 意图层私有
    intent: IntentPayload
    domain: DomainRouting
    clarification_rounds: int

@dataclass
class PlanningContext:       # 规划层私有
    plan: Plan | None
    has_background_context: bool

@dataclass
class ExecutionContext:      # 执行层私有
    stages: list[StageResult]
    artifacts: dict

@dataclass
class State:                 # 全局 State 仅保留路由用字段
    messages: list
    intent_ctx: IntentContext
    planning_ctx: PlanningContext
    execution_ctx: ExecutionContext
```

#### 2.3 节点间通过 TaskPacket 传递数据

```python
# 当前模式
def create_manager_agent_node(state: State) -> State:
    plan = state.plan  # 从全局 state 读取
    ...

# 新模式
def create_manager_agent_node(packet: TaskPacket) -> TaskPacket:
    plan = packet.inputs["plan"]  # 从显式契约读取
    packet.outputs["execution_result"] = result
    return packet
```

**产出**：
- `core/models/task_packet.py` — TaskPacket 定义
- 重构 3-5 个核心节点使用新契约

---

### Phase 3: 并发执行框架（3-4 周）

**目标**：替代线性串行，支持动态并发

#### 3.1 引入 Lane 概念

每个独立分支作为 Lane 并发执行：

```python
class Lane:
    """独立执行分支"""
    lane_id: str
    objective: str
    steps: list[TaskPacket]
    status: LaneStatus
    events: list[LaneEvent]
    
class LaneManager:
    """Lane 管理器"""
    lanes: dict[str, Lane]
    
    async def spawn(self, objective: str, steps: list[TaskPacket]) -> str:
        """创建新 Lane"""
    
    async def wait_any(self, lane_ids: list[str]) -> LaneEvent:
        """等待任意 Lane 完成"""
    
    async def wait_all(self, lane_ids: list[str]) -> dict[str, LaneResult]:
        """等待所有 Lane 完成"""
```

#### 3.2 动态 Lane 发现

在 preflight 阶段分析任务依赖，自动识别可并发的 Lane：

```python
def discover_concurrent_lanes(plan: Plan) -> list[Lane]:
    """分析计划依赖图，发现无依赖的子任务组"""
    dep_graph = build_dependency_graph(plan.tasks)
    independent_groups = find_independent_groups(dep_graph)
    return [Lane(id=f"lane-{i}", tasks=group) for i, group in enumerate(independent_groups)]
```

#### 3.3 Lane 事件总线

```python
class LaneEventType(StrEnum):
    LANES_SPAWNED = "lanes_spawned"
    LANE_STARTED = "lane_started"
    LANE_BLOCKED = "lane_blocked"
    LANE_COMPLETED = "lane_completed"
    LANE_FAILED = "lane_failed"

class EventBus:
    """事件总线，支持 SSE 推送"""
    subscribers: list[EventSubscriber]
    
    async def publish(self, event: LaneEvent):
        for sub in self.subscribers:
            await sub.on_event(event)
```

**产出**：
- `core/executor/lane_manager.py` — Lane 管理器
- `core/executor/event_bus.py` — 事件总线
- 重构 `CrossLayerComboExecutor` 使用 Lane 模型

---

### Phase 4: 故障恢复（2 周）

**目标**：声明式故障恢复策略

#### 4.1 RecoveryRecipe 定义

```python
@dataclass
class RecoveryRecipe:
    """故障恢复配方"""
    name: str
    triggers: list[str]               # 触发条件（错误码/异常类型）
    max_attempts: int
    strategy: RecoveryStrategy         # Retry/Alternative/CircuitBreaker
    cooldown_seconds: int
    escalation: EscalationPolicy | None # 升级策略
```

#### 4.2 集成到 Stage 执行

```python
# 每个 Stage 关联恢复配方
STAGE_RECOVERY = {
    "data_collection": RecoveryRecipe(
        name="retry_with_fallback",
        triggers=["timeout", "connection_error"],
        max_attempts=3,
        strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
    ),
    "sql_generation": RecoveryRecipe(
        name="switch_agent",
        triggers=["llm_error"],
        max_attempts=1,
        strategy=RecoveryStrategy.ALTERNATIVE_AGENT,
    ),
}
```

---

### Phase 5: 可测试性与可观测性（2 周）

**目标**：全链路可追踪、可回放

#### 5.1 执行追踪

```python
@dataclass
class ExecutionTrace:
    trace_id: str
    user_query: str
    steps: list[StepTrace]
    decisions: list[DecisionRecord]
    timing: TimingSummary
    
@dataclass
class StepTrace:
    step_name: str
    input_snapshot: dict    # 输入快照
    output_snapshot: dict   # 输出快照
    duration_ms: int
    status: str
```

#### 5.2 决策审计

```python
@dataclass
class DecisionRecord:
    node: str
    rule_matched: str
    alternatives_considered: list[str]
    rationale: str
    timestamp: datetime
```

#### 5.3 回放机制

基于 ExecutionTrace 回放完整执行过程，用于调试和回归测试。

---

## 实施优先级矩阵

| Phase | 工作量 | 影响度 | 风险 | 优先级 |
|-------|--------|--------|------|--------|
| Phase 1: 路由规则化 | 2-3 周 | 高 | 低 | P0 — 最先做 |
| Phase 2: 数据契约化 | 2 周 | 高 | 中 | P1 |
| Phase 4: 故障恢复 | 2 周 | 中 | 低 | P2 |
| Phase 3: 并发执行 | 3-4 周 | 高 | 高 | P3 |
| Phase 5: 可观测性 | 2 周 | 中 | 低 | P4 |

## 不做的部分

- **不替换 LangGraph** — 继续作为状态图运行时
- **不引入 Rust** — 所有增强在 Python 层实现
- **不改变用户接口** — 保持现有 Web 前端和 SSE 流
- **不替换 Keycloak/PostgreSQL** — 基础设施不变

## 预期收益

1. **路由决策**：从 310+ 行单体函数 → 可独立测试的声明式规则
2. **状态管理**：从 90 字段全局共享 → 分区 + 显式契约
3. **执行效率**：从完全串行 → 动态并发，预计缩短 30-50% 分析时间
4. **可靠性**：从 "继续执行" → 声明式恢复策略，减少失败场景
5. **可维护性**：从 "不敢改" → 每个组件可独立测试和演进

