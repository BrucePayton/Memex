---
title: "产险机构杂费付款审核SOP"
type: source-summary
created: 2026-04-30
last_updated: 2026-04-30
source_count: 1
confidence: medium
status: active
tags:
  - workflow
  - 业务流程
  - 保险
  - 付款审核
  - SOP
sources:
  - property-insurance-payment-sop
---

---
title: "产险机构杂费付款审核SOP"
type: source-summary
tags:
  - workflow
  - 业务流程
  - 保险
  - 付款审核
  - SOP
created: 2026-04-29
last_updated: 2026-04-29
source_count: 1
confidence: high
status: active
---

# 产险机构杂费付款审核SOP

[[source-property-insurance-payment-sop|产险机构杂费付款审核SOP]] 版本 V3，由新金科财务服务中心管理，定义了产险机构杂费付款审核流程，涵盖多种付款类型的并行处理，所有审核需在2小时内完成。[^src-property-insurance-payment-sop]

## 流程概述

该流程以OA审批（EOA）为统一入口，采用并行分发模式处理9种付款类型：

1. **接收待办签报**：所有流程以OA审批为统一入口。[^src-property-insurance-payment-sop]
2. **审核签报内容与附件一致性**：根据付款性质和签报、附件内容进行待办签报审核，核对信息一致性，SLA为2H以内。[^src-property-insurance-payment-sop]
3. **并行分发付款类型处理**：通过并行分支（parallel-fork）分发至以下9条支线：
   - **流水退款**：原卡原退或同主体退款，核对收付款人名称、账号、金额一致。[^src-property-insurance-payment-sop]
   - **退第三方**：需提供收款人身份证/营业执照、授权委托书、支付凭证，金额≥1万需咨询合规。[^src-property-insurance-payment-sop]
   - **共保保费支付**：需上传用印共保协议和保单号，2026年1月起需咨询赵旭老师。[^src-property-insurance-payment-sop]
   - **保证金支付**：需OA签报、招标公告/合同协议，核对账号、金额、收款人信息。[^src-property-insurance-payment-sop]
   - **安抚基金、生育基金**：2026年1月起取消咨询，需OA签报和收款人身份证。[^src-property-insurance-payment-sop]
   - **通知单退款**：需退款申请书和营业执照，车船税需上传入账截图。[^src-property-insurance-payment-sop]
   - **互联网二期**：含退保和手续费支付，2026年1月起蚂蚁手续费支付需咨询赵旭老师。[^src-property-insurance-payment-sop]
   - **理赔款**：大类参照流水退款规则处理。[^src-property-insurance-payment-sop]
   - **安责险费**：杭州地区需咨询丁宇，使用指定建行监管账户（5555账户）。[^src-property-insurance-payment-sop]
4. **月结截止资金支付**：统一回复并退回签报，待下月开账后重起。[^src-property-insurance-payment-sop]
5. **并行处理结果汇聚**：所有支线完成后进入汇合节点。[^src-property-insurance-payment-sop]

## 涉及系统

- **EOA系统**：所有审批流程的统一入口

## 风险点

- **签报与附件信息不一致**（高风险）：需增加双人复核机制和系统自动比对。[^src-property-insurance-payment-sop]
- **合规咨询遗漏**（高风险）：金额≥1万未咨询合规、共保支付未咨询赵旭老师等，需系统设置金额阈值提醒。[^src-property-insurance-payment-sop]
- **收款信息不一致**（中风险）：保证金支付场景中需补充来源证明。[^src-property-insurance-payment-sop]
- **系统关账后重起签报**（高风险）：月结截止时需系统自动识别关账状态并锁定操作。[^src-property-insurance-payment-sop]

[^src-property-insurance-payment-sop]: [[source-property-insurance-payment-sop]]

