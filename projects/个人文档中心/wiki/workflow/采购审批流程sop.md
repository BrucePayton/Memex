---
title: "采购审批流程SOP"
type: source-summary
created: 2026-04-30
last_updated: 2026-04-30
source_count: 1
confidence: medium
status: active
tags:
  - workflow
  - 业务流程
  - 采购
  - 审批
sources:
  - procurement-approval-sop
---

---
title: "采购审批流程SOP"
type: source-summary
tags:
  - workflow
  - 业务流程
  - 采购
  - 审批
created: 2026-04-29
last_updated: 2026-04-29
source_count: 1
confidence: high
status: active
---

# 采购审批流程SOP

[[source-procurement-approval-sop|采购审批流程SOP]] 版本 v1.0，由采购部管理，定义了包含财务初审与技术评审并行、金额超50万元需副总审批的条件分支的采购审批流程。[^src-procurement-approval-sop]

## 流程概述

该流程定义了从接收采购申请到合同生成归档的完整审批链路：

1. **接收采购申请**：使用采购申请单模板（Word）填写新采购申请的标准化表单，确保信息完整。[^src-procurement-approval-sop]
2. **并行评审启动**：通过并行分支（parallel-fork）同时启动财务初审和技术评审。[^src-procurement-approval-sop]
3. **财务初审**：需在3个工作日内完成，使用OA审批系统执行财务初审操作，支持审批流管理与SLA监控。[^src-procurement-approval-sop]
4. **技术评审**：与财务初审并行，截止时间同为3个工作日，使用OA系统执行技术评审操作，支持并行任务分发与时限控制。[^src-procurement-approval-sop]
5. **评审结果汇聚**：通过并行汇聚（parallel-join）汇合双评审结果，系统强制要求双评审均提交后方可进入下一节点。[^src-procurement-approval-sop]
6. **金额条件判断**：判断采购金额是否超过50万元，金额超过50万元需进入副总审批环节。[^src-procurement-approval-sop]
7. **副总审批**：针对金额超过50万元的采购，需在1个工作日内完成。[^src-procurement-approval-sop]
8. **生成合同**：审批通过后生成合同，使用合同模板（PDF），录入OA系统并同步至ERP系统建档管理，邮件通知审批状态。[^src-procurement-approval-sop]
9. **归档结束**：合同归档，流程终止。[^src-procurement-approval-sop]

## 涉及系统

- **OA系统**：财务初审、技术评审、合同录入、审批流管理
- **ERP系统**：接收合同创建请求，完成合同正式建档与管理

## 风险点

- **财务初审超时未完成**（高风险）：因无预警机制导致延误，需设置SLA倒计时提醒与自动催办功能。[^src-procurement-approval-sop]
- **技术评审进度不同步**（中风险）：缺乏进度同步机制导致评审结果汇合延迟，需建立并行任务统一进度看板。[^src-procurement-approval-sop]
- **副总审批责任不明确**（高风险）：存在审批空窗期风险，需指定主责人并配置自动待办提醒与超时上报机制。[^src-procurement-approval-sop]
- **评审结果汇聚校验缺失**（中风险）：可能遗漏任一评审意见，需系统强制要求双评审均提交。[^src-procurement-approval-sop]
- **合同生成触发条件不明确**（中风险）：审批通过后未及时生成合同，需设置自动触发合同生成的规则引擎。[^src-procurement-approval-sop]

[^src-procurement-approval-sop]: [[source-procurement-approval-sop]]

