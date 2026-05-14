---
title: "修复记录：历史会话首次点击骨扇屏折叠不展开"
type: source-summary
tags:
  - bugfix
  - askdata
  - frontend
created: 2026-05-14
last_updated: 2026-05-14
source_count: 0
confidence: high
status: active
---

# 修复记录：历史会话首次点击骨扇屏折叠不展开

## 来源

原始记录：`raw/bugfix/2026-05-14-bone-fan-screen-collapsed-on-first-click.md`

## 概要

2026-05-14 在 `backup/dev_bruce_askdata` 分支上修复的 bug，紧接前序的 [[历史会话编排阶段骨扇屏完全不渲染修复]] 之后。

第一次点击历史会话时，编排阶段仅显示可点击标题（骨扇屏状态），内容需要手动点击才能看到。根因是三重折叠状态的默认值均为 `false`：

1. 阶段卡片 `collapsedState[msg.id] = false` → `stageCardOpen[id]=false` → 内容隐藏
2. 阶段组 `groupCollapsedState[msg.turnBotId] = false` → 组折叠
3. 渲染 fallback `stageCardOpen[message.id] ?? false` → undefined 也导致折叠

此外，切换会话时未重置 `stageCardOpen` 和 `stageGroupOpen`，导致跨会话折叠状态污染。

修复方案：将 `false` 改为 `true`（默认展开），并在 session switch 时重置两个折叠状态对象。

关键教训：变量名 `collapsedState` 的语义与 `setStageCardOpen`（open state）相反——true 在 collapsedState 中表示折叠，但作为 open state 的 value 时表示展开。`??` 空值合并的 fallback 值必须与业务意图一致。

## 涉及文件

- `web/src/features/query-space/pages/QueryAnalysisChat.tsx`（第 2108、2118、1715-1724、5878、5980 行）
