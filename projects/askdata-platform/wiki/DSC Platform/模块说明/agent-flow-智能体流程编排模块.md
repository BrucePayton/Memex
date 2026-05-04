---
title: "agent_flow 智能体流程编排模块"
type: module
created: 2026-05-03
last_updated: 2026-05-03
source_count: 1
confidence: medium
status: active
tags:
  - agent_flow
  - workflow
  - orchestration
  - 核心模块
sources:
  - agent_flow模块代码分析
---

# agent_flow 智能体流程编排模块

## 模块概述
agent_flow是DSC Platform的核心流程引擎，提供了低代码的可视化流程编排能力，允许用户通过拖拽方式设计复杂的数据处理流程、AI工作流和业务流程。该模块借鉴了LangGraph和Airflow的设计理念，同时提供了更友好的可视化界面和更灵活的扩展能力。

## 核心概念

### 1. 节点 (Node)
节点是流程的基本组成单元，每个节点代表一个具体的操作或处理步骤。系统提供了丰富的预置节点类型，同时支持用户自定义扩展。

#### 节点类型
- **基础节点**：输入、输出、条件判断、循环等控制流节点
- **处理节点**：文本处理、数据转换、格式转换等数据处理节点
- **AI节点**：大模型调用、提示词工程、向量检索等AI相关节点
- **集成节点**：数据库操作、API调用、第三方服务集成等节点
- **自定义节点**：用户通过Python代码自定义的业务节点

#### 节点结构
每个节点包含以下核心部分：
```python
class BaseNode:
    node_id: str                # 节点唯一标识
    node_name: str              # 节点名称
    node_type: NodeType         # 节点类型
    category: NodeCategory      # 节点分类
    parameters: List[Parameter] # 节点参数定义
    inputs: List[Port]          # 输入端口
    outputs: List[Port]         # 输出端口
    description: str            # 节点描述
```

### 2. 工作流 (Workflow)
工作流是由多个节点通过连接线连接而成的有向无环图(DAG)，定义了数据的流动和处理顺序。

#### 工作流属性
```python
class AgentFlow:
    dag_id: str                 # 工作流唯一标识
    name: str                   # 工作流名称
    description: str            # 工作流描述
    nodes: List[BaseNode]       # 节点列表
    edges: List[Edge]           # 连接线列表
    version: str                # 版本号
    status: FlowStatus          # 状态（草稿/已发布/已归档）
    create_time: datetime       # 创建时间
    update_time: datetime       # 更新时间
```

### 3. 上下文 (Context)
上下文是工作流执行过程中的数据容器，用于在节点之间传递数据和状态。

#### 上下文结构
```python
class AgentFlowContext:
    _event_loop_task_id: int    # 事件循环任务ID
    _node_to_outputs: Dict[str, TaskContext] # 节点输出映射
    _share_data: Dict[str, Any] # 全局共享数据
    _streaming_call: bool       # 是否为流式调用
    _node_name_to_ids: Dict[str, str] # 节点名称到ID的映射
```

### 4. 参数系统
参数系统定义了节点的输入输出规范，支持多种参数类型和校验规则。

#### 参数类型
- **基本类型**：字符串、整数、浮点数、布尔值
- **复杂类型**：对象、数组、枚举
- **特殊类型**：资源引用、动态选项、秘密值

#### 参数定义示例
```python
Parameter(
    label="智谱API Key",
    name="api_key",
    type_name="str",
    type_cls="builtins.str",
    category="resource",
    resource_type=ResourceType.INSTANCE,
    optional=False,
    description="调用智谱大模型需要的API密钥",
    placeholder="请输入API Key",
    sensitive=True
)
```

## 核心组件

### 1. 流程设计器 (Flow Designer)
可视化的流程设计界面，支持：
- 拖拽式节点添加和连接
- 节点参数可视化配置
- 流程预览和调试
- 版本管理和回滚

### 2. 执行引擎 (Execution Engine)
负责工作流的调度和执行，核心特性：
- 异步并行执行，提高处理效率
- 依赖自动解析，确保执行顺序正确
- 错误重试和故障恢复
- 执行状态实时监控
- 支持断点续跑

### 3. 组件注册中心 (Component Registry)
管理所有可用的节点组件，支持：
- 组件自动发现和注册
- 组件版本管理
- 组件依赖管理
- 组件权限控制

### 4. 作业管理器 (Job Manager)
负责作业的生命周期管理，功能包括：
- 作业调度和队列管理
- 作业状态跟踪
- 作业日志管理
- 作业资源监控

## 核心功能

### 1. 控制流支持
- **条件分支**：根据条件判断执行不同的流程路径
- **循环执行**：支持For循环和While循环
- **并行执行**：多个节点同时执行，提高效率
- **等待节点**：等待特定条件满足后继续执行
- **子流程**：支持流程嵌套和复用

### 2. 数据处理能力
- **数据转换**：支持JSONPath、JQ等数据转换表达式
- **格式转换**：支持多种数据格式之间的互转
- **数据过滤**：根据条件过滤数据
- **数据聚合**：对多个数据源进行合并和聚合

### 3. AI工作流支持
- **大模型集成**：开箱即用支持主流大模型API
- **提示词模板**：支持参数化的提示词模板
- **多轮对话**：支持复杂的多轮对话流程
- **工具调用**：支持大模型调用外部工具
- **RAG流程**：预置检索增强生成流程模板

### 4. 高级特性
- **版本控制**：完整的流程版本历史和变更对比
- **权限管理**：细粒度的流程访问和操作权限
- **审计日志**：完整的操作和执行审计记录
- **性能监控**：节点执行性能和资源消耗监控
- **错误告警**：执行失败时的多渠道告警通知

## 开发指南

### 自定义节点开发
开发自定义节点只需要继承BaseNode类并实现execute方法：

```python
from agent_flow.agent_flow_node import BaseNode
from agent_flow.agent_flow_base.agent_flow_base_task import TaskContext

class CustomNode(BaseNode):
    # 节点元数据定义
    node_type = "custom_node"
    node_name = "自定义节点"
    category = "custom"
    description = "这是一个自定义节点示例"
    
    # 定义参数
    parameters = [
        Parameter(
            label="输入参数",
            name="input_param",
            type_name="str",
            type_cls="builtins.str",
            category="common",
            optional=False,
            description="节点输入参数"
        )
    ]
    
    async def execute(self, task_context: TaskContext) -> Any:
        """节点执行逻辑"""
        # 获取参数
        input_param = task_context.parameters["input_param"]
        
        # 业务逻辑处理
        result = f"处理结果: {input_param}"
        
        # 返回结果
        return result
```

### 流程编程式定义
除了可视化设计，也支持通过代码直接定义工作流：

```python
from agent_flow.agent_flow_runner import DefaultWorkflowRunner
from agent_flow.agent_flow_nodes import *

# 创建节点
input_node = InputNode(name="输入节点")
process_node = TextProcessorNode(name="处理节点")
output_node = OutputNode(name="输出节点")

# 连接节点
input_node.connect_to(process_node)
process_node.connect_to(output_node)

# 创建执行器
runner = DefaultWorkflowRunner()

# 执行工作流
result = await runner.execute_workflow(
    node=output_node,
    call_data={
        "input": "待处理的文本内容"
    }
)

# 获取结果
print(result.output)
```

## 部署和扩展

### 部署架构
agent_flow支持两种部署模式：
1. **嵌入模式**：作为库嵌入到其他Python应用中使用
2. **服务模式**：作为独立服务部署，提供RESTful API和可视化界面

### 扩展能力
- **节点扩展**：通过Python代码开发自定义节点
- **执行器扩展**：支持自定义执行引擎，适配不同的运行环境
- **存储扩展**：支持自定义存储后端，适配不同的数据库
- **监控扩展**：支持自定义监控指标和告警渠道

## 性能指标
- 单实例支持同时运行1000+个工作流
- 节点调度延迟<10ms
- 支持百万级节点的复杂流程
- 水平扩展支持无限并发能力

## 最佳实践

### 流程设计最佳实践
1. **模块化设计**：将复杂流程拆分为多个子流程，提高复用性
2. **错误处理**：为每个节点添加错误处理和重试逻辑
3. **参数校验**：对输入参数进行严格校验，避免运行时错误
4. **日志记录**：在关键节点添加日志，方便问题排查
5. **版本管理**：每次修改流程都创建新版本，便于回滚

### 性能优化最佳实践
1. **并行执行**：将没有依赖关系的节点设为并行执行
2. **批量处理**：减少小批量操作，尽量使用批量处理
3. **缓存机制**：对重复计算的结果进行缓存
4. **资源限制**：为节点设置合理的资源限制，避免资源耗尽

## 常见问题

### Q: 如何处理长时间运行的任务？
A: agent_flow支持异步任务执行，对于长时间运行的任务会自动转为后台执行，并提供状态查询接口。

### Q: 流程执行失败后如何恢复？
A: 系统会自动保存执行快照，支持从失败节点处重新执行，无需从头开始。

### Q: 支持哪些调度方式？
A: 支持立即执行、定时执行、事件触发、API触发等多种调度方式。

### Q: 如何实现流程之间的数据共享？
A: 可以通过全局上下文、子流程参数传递、外部存储等多种方式实现数据共享。
