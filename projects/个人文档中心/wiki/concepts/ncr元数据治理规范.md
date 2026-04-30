---
title: "NCR元数据治理规范"
type: entity
created: 2026-04-30
last_updated: 2026-04-30
source_count: 2
confidence: medium
status: active
tags:
  - 元数据
  - NCR
  - 治理规范
  - AR-AP
sources:
  - ncr-architecture-evaluation
  - ncr-metaspec-report
---

NCR（Node-Component-Relationship）是元数据治理规范框架，将传统七层元模型收敛为四类节点[^src-ncr-architecture-evaluation]。

## 核心架构

### 四类节点

| 节点类型 | 实例数 | 职责 |
|----------|--------|------|
| Concept（概念节点） | 3 | 术语消歧，定义业务概念 |
| Entity（实体节点） | 5 | 数据结构定义，含字段、类型、主键及合规规则 |
| Activity（活动节点） | 2 | 流程步骤定义，含SLA约束 |
| Metric（指标节点） | 4 | KPI定义，含数据血缘和根因下钻 |

### 九种组件类型

语义组件、结构组件、规则组件、血缘组件、流程绑定、SLA组件、呈现组件、上下文组件、治理组件

### AR/AP域实现

在AR/AP（应收账款/应付账款）域中覆盖：
- **P2P（采购到付款）**：9步，约13工作日
- **O2C（订单到收款）**：8步

## 能力成熟度

六层能力模型完成4层（67%）：

| 层级 | 状态 |
|------|------|
| 基础问答 | ✅ 完成 |
| 合规检查 | ✅ 完成 |
| 流程追溯 | ✅ 完成 |
| 根因下钻 | ✅ 完成 |
| 智能问答 | 🔄 进行中 |
| 全量治理 | 📋 规划中 |

## 语义关系图谱

| 关系类型 | 数量 | 语义 |
|----------|------|------|
| FLOWS_INTO | 4 | 实体→实体流转 |
| DERIVES_FROM | 4 | 指标→实体溯源 |
| MEASURES | 2 | 指标→活动度量 |
| CONFUSED_WITH | 1 | 概念→概念消歧 |

图谱密度0.79，血缘链路闭环良好，但概念层语义消歧能力较弱[^src-ncr-metaspec-report]。

## 关联文档

- [[ncr-架构评估报告]] - 架构评估主报告
- [[ncr-metaspec-report-2026-03-05]] - AI生成的英文分析

[^src-ncr-architecture-evaluation]: [[ncr-架构评估报告]]
[^src-ncr-metaspec-report]: [[ncr-metaspec-report-2026-03-05]]

