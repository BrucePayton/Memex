---
title: "Beneish M-Score 财务造假检测"
type: concept
created: 2026-04-30
last_updated: 2026-04-30
source_count: 1
confidence: medium
status: active
tags:
  - 财务分析
  - Beneish-M-Score
  - 财务造假检测
sources:
  - target-company-financial-report
---

Beneish M-Score是一种财务造假检测模型，通过分析8个财务比率来评估企业财务操纵的可能性[^src-target-company-financial-report]。

## 阈值

- **M-Score > -1.78**：疑似财务造假
- **M-Score < -1.78**：非财务造假

## 案例：目标公司（恒大集团）

| 年份 | M-Score | 结论 |
|------|---------|------|
| 2020 | 2.04 | **疑似造假** |
| 2021 | -2.05 | 非造假 |
| 2022 | -1.91 | 非造假 |

2020年的疑似造假信号主要涉及应收账款增长、营收增长异常等指标。2021年随着会计准则调整和市场变化，M-Score回归正常区间[^src-target-company-financial-report]。

## 关联文档

- [[目标公司-财务分析报告]] - M-Score分析原始报告
- [[恒大集团]] - 财务数据概览
- [[目标公司-财务数据模板]] - 数据模板

[^src-target-company-financial-report]: [[目标公司-财务分析报告]]

