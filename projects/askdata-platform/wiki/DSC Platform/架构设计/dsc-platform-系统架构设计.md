---
title: "DSC Platform 系统架构设计"
type: architecture
created: 2026-05-03
last_updated: 2026-05-03
source_count: 1
confidence: medium
status: active
tags:
  - architecture
  - system-design
  - modules
sources:
  - 项目代码结构分析
---

# DSC Platform 系统架构设计

## 整体架构
DSC Platform采用分层、模块化的架构设计，确保系统的可扩展性、可维护性和高可用性。整体架构分为以下几个层次：

```
┌─────────────────────────────────────────────────────────┐
│                     接入层 (Access Layer)               │
│  RESTful API / WebSocket / 管理后台 / 第三方集成        │
├─────────────────────────────────────────────────────────┤
│                  业务逻辑层 (Business Layer)            │
│  知识库管理 / 数据库管理 / 向量管理 / 流程编排 / 应用市场 │
├─────────────────────────────────────────────────────────┤
│                  服务支撑层 (Service Layer)             │
│  任务调度 / 消息队列 / 缓存服务 / 权限认证 / 日志监控    │
├─────────────────────────────────────────────────────────┤
│                  数据访问层 (Data Access Layer)         │
│  ORM框架 / 数据库连接池 / 向量数据库客户端 / 文件存储    │
├─────────────────────────────────────────────────────────┤
│                  基础设施层 (Infrastructure Layer)      │
│  计算资源 / 存储资源 / 网络资源 / 容器编排 / 云服务      │
└─────────────────────────────────────────────────────────┘
```

## 核心模块架构

### 1. agent_flow - 智能体流程编排框架
智能体流程编排是DSC Platform的核心引擎，提供了可视化的流程设计和执行能力。

```
agent_flow/
├── agent_flow_base/          # 流程引擎基础框架
│   ├── agent_flow_base.py        # 基础流程类
│   ├── agent_flow_base_abc.py    # 抽象基类定义
│   ├── agent_flow_base_implemetation.py  # 核心实现
│   ├── agent_flow_base_nodes_component.py # 节点组件基类
│   ├── agent_flow_base_register.py     # 组件注册器
│   ├── agent_flow_base_resource.py    # 资源管理
│   └── agent_flow_base_task.py        # 任务管理
├── agent_flow_nodes/          # 内置节点实现
│   ├── agent_flow_nodes_agent_components.py  # AI智能体节点
│   ├── agent_flow_nodes_components.py         # 通用处理节点
│   ├── agent_flow_nodes_dependency.py         # 依赖注入节点
│   └── agent_flow_nodes_wrapper_components.py # 包装器节点
├── agent_flow_config/         # 配置管理
│   ├── agent_flow_category_config.py  # 分类配置
│   └── agent_flow_model_config.py     # 模型配置
├── agent_flow_runner.py       # 流程执行器
├── agent_flow_job_manager.py  # 作业管理器
├── agent_flow_lifecycle.py    # 生命周期管理
├── agent_flow_node.py         # 节点基类定义
├── agent_flow_node_enum.py    # 节点类型枚举
└── agent_flow_utils/          # 工具函数库
```

#### 核心能力
- **可视化流程设计**：通过拖拽方式设计复杂的数据处理流程
- **组件化开发**：支持自定义节点组件，扩展处理能力
- **并行/串行执行**：支持复杂的流程控制逻辑
- **版本控制**：流程定义的版本管理和回滚
- **状态监控**：实时监控流程执行状态和进度

### 2. knowledge_mgt - 知识库管理模块
知识库管理模块负责各类非结构化数据的接入、解析、存储和检索。

```
knowledge_mgt/
├── knowledge_api/            # API接口层
│   ├── api_views.py               # 路由定义
│   ├── api_helper.py              # 业务逻辑封装
│   └── api_models.py              # 请求/响应模型
├── knowledge_process/        # 文档处理层
│   ├── knowledge_processor.py     # 处理引擎
│   ├── parsers/                   # 各类文档解析器
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── pptx_parser.py
│   │   ├── excel_parser.py
│   │   ├── image_parser.py
│   │   └── text_parser.py
│   ├── extractors/               # 内容提取器
│   │   ├── text_extractor.py
│   │   ├── table_extractor.py
│   │   ├── image_extractor.py
│   │   └── metadata_extractor.py
│   └── processors/               # 内容处理器
│       ├── cleaner.py
│       ├── splitter.py
│       └── enricher.py
├── knowledge_storage/       # 存储管理层
│   ├── knowledge_repository.py    # 知识库仓库
│   ├── document_store.py          # 文档存储
│   └── version_control.py         # 版本管理
└── knowledge_search/        # 检索引擎层
    ├── search_engine.py           # 全文检索
    ├── semantic_search.py         # 语义检索
    └── hybrid_search.py           # 混合检索
```

#### 核心能力
- **多格式支持**：支持PDF、Word、Excel、PPT、图片、文本等20+种文档格式
- **智能解析**：集成OCR、布局分析、内容理解等AI能力
- **自动分段**：智能文本分段，优化向量检索效果
- **元数据管理**：自动提取和管理文档元数据
- **版本追踪**：完整的文档版本历史和变更记录

### 3. db_mgt - 数据库管理模块
数据库管理模块提供结构化数据的接入、查询和管理能力。

```
db_mgt/
├── database_api/           # API接口层
│   ├── api_views.py            # 路由定义
│   ├── api_helper.py           # 业务逻辑封装
│   └── api_models.py           # 请求/响应模型
├── database_core/          # 核心功能层
│   ├── connection_manager.py   # 连接管理
│   ├── sql_parser.py           # SQL解析和校验
│   ├── query_executor.py       # 查询执行器
│   └── result_processor.py     # 结果处理
├── database_support/       # 数据源支持
│   ├── mysql_support.py        # MySQL支持
│   ├── postgresql_support.py   # PostgreSQL支持
│   ├── oracle_support.py       # Oracle支持
│   ├── sqlserver_support.py    # SQL Server支持
│   └── clickhouse_support.py   # ClickHouse支持
└── database_security/     # 安全管理层
    ├── access_control.py       # 访问控制
    ├── sql_audit.py            # SQL审计
    └── data_masking.py         # 数据脱敏
```

#### 核心能力
- **多数据源支持**：支持主流关系型数据库和大数据引擎
- **连接池管理**：高效的数据库连接复用和管理
- **智能SQL生成**：支持自然语言转SQL能力
- **查询优化**：自动分析和优化慢查询
- **安全审计**：完整的SQL执行审计和数据脱敏

### 4. vectors_mgt - 向量管理模块
向量管理模块负责向量的生成、存储和检索，为语义检索提供支持。

```
vectors_mgt/
├── vectors_api/            # API接口层
│   ├── api_views.py            # 路由定义
│   └── api_models.py           # 请求/响应模型
├── vectors_core/           # 核心功能层
│   ├── embedding_generator.py  # 向量生成器
│   ├── vector_store.py         # 向量存储
│   ├── vector_search.py        # 向量检索
│   └── vector_index.py         # 索引管理
├── vectors_models/         # 模型支持
│   ├── openai_embedding.py     # OpenAI嵌入模型
│   ├── baichuan_embedding.py   # 百川嵌入模型
│   ├── qianwen_embedding.py    # 千问嵌入模型
│   └── local_embedding.py      # 本地嵌入模型
└── vectors_store/          # 向量数据库支持
    ├── chroma_store.py         # ChromaDB支持
    ├── weaviate_store.py       # Weaviate支持
    ├── milvus_store.py         # Milvus支持
    └── pgvector_store.py       # PGVector支持
```

#### 核心能力
- **多模型支持**：兼容主流商用和开源嵌入模型
- **批量处理**：支持大规模向量的批量生成和导入
- **高效检索**：支持百亿级向量的毫秒级检索
- **混合检索**：支持关键词和语义的混合检索
- **动态索引**：支持索引的动态更新和维护

### 5. flow_mgt - 流程管理模块
流程管理模块提供业务流程的设计、执行和监控能力。

```
flow_mgt/
├── flow_api/               # API接口层
│   ├── api_views.py            # 路由定义
│   └── api_models.py           # 请求/响应模型
├── flow_app_market/        # 应用市场
│   ├── app_store.py           # 应用商店
│   ├── app_template.py        # 应用模板
│   └── app_runtime.py         # 应用运行时
├── flow_core/              # 核心功能层
│   ├── flow_designer.py        # 流程设计器
│   ├── flow_executor.py        # 流程执行器
│   ├── flow_monitor.py         # 流程监控
│   └── flow_scheduler.py       # 流程调度
└── flow_integration/       # 集成层
    ├── third_party_api.py      # 第三方API集成
    ├── webhook_support.py      # Webhook支持
    └── event_bus.py            # 事件总线
```

#### 核心能力
- **低代码设计**：可视化的流程设计界面
- **丰富的组件库**：提供各类预置组件，快速搭建流程
- **定时调度**：支持定时触发和事件触发
- **运行监控**：实时监控流程执行状态和性能
- **应用市场**：预置各类行业解决方案模板

## 技术架构特点
### 1. 异步高性能设计
- 基于FastAPI和Uvicorn的异步架构，支持高并发访问
- 异步IO处理，大幅提升IO密集型任务的吞吐量
- 连接池和缓存机制，减少重复计算和IO操作

### 2. 插件化扩展架构
- 所有功能模块采用插件化设计，支持热插拔
- 标准化的组件接口，方便自定义扩展
- 自动发现和注册机制，无需手动配置

### 3. 云原生架构
- 容器化部署，支持Kubernetes编排
- 微服务化设计，各个模块可以独立部署和扩展
- 可观测性设计，集成日志、监控、链路追踪

### 4. 安全可靠设计
- 完善的身份认证和权限控制体系
- 数据加密传输和存储
- 多租户隔离设计
- 灾备和高可用支持

## 部署架构
### 单机部署
适合开发测试和小规模使用场景：
```
┌─────────────────────────────────────────────────────────┐
│                     DSC Platform                        │
│  API服务 + 任务调度 + 所有业务模块                       │
├─────────────────────────────────────────────────────────┤
│                     本地存储                             │
│  SQLite + 文件系统 + 本地向量数据库                      │
└─────────────────────────────────────────────────────────┘
```

### 集群部署
适合生产环境和大规模使用场景：
```
┌─────────────────────────────────────────────────────────┐
│                     负载均衡层                           │
│  Nginx / ALB / 云负载均衡                                │
├─────────────────────────────────────────────────────────┤
│                     服务层                               │
│  API服务集群 × N + 任务调度集群 × N + 业务模块集群 × N   │
├─────────────────────────────────────────────────────────┤
│                     中间件层                             │
│  Redis集群 + Kafka集群 + Elasticsearch集群              │
├─────────────────────────────────────────────────────────┤
│                     存储层                               │
│  MySQL集群 + MongoDB集群 + 向量数据库集群 + 对象存储    │
└─────────────────────────────────────────────────────────┘
```

## 数据流设计
### 文档处理数据流
```
文档上传 → 格式识别 → 内容解析 → 文本提取 → 智能分段 → 
向量生成 → 元数据提取 → 索引构建 → 存储入库 → 检索可用
```

### 查询请求数据流
```
用户查询 → 查询理解 → 意图识别 → 路由分发 → 并行检索 → 
结果融合 → 排序优化 → 内容生成 → 结果返回
```

### 流程执行数据流
```
流程触发 → 上下文初始化 → 节点执行 → 状态更新 → 事件传递 → 
依赖检查 → 后续节点执行 → 结果汇总 → 流程结束 → 通知用户
```
