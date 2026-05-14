# 修复：历史会话首次点击骨扇屏折叠不展开

日期：2026-05-14
分支：backup/dev_bruce_askdata
前序修复：useStageTreeMemo 父阶段存在性检查（解决完全不渲染问题）

## 问题描述

第一次点击历史会话时，编排阶段只显示可点击的标题（骨扇屏状态），内容不显示。需要手动点击展开才能看到阶段内容。

## 根因分析

### 三重折叠默认值均为 `false`

**问题 1：阶段卡片默认折叠**（QueryAnalysisChat.tsx 第 2108 行）
```ts
collapsedState[msg.id] = false;  // false → stageCardOpen[id]=false → Collapsible open=false → 内容隐藏
```

**问题 2：阶段组默认折叠**（第 2118 行）
```ts
groupCollapsedState[msg.turnBotId] = false;  // false → stageGroupOpen[turnBotId]=false → 组折叠
```

**问题 3：渲染 fallback 也是折叠**（第 5878、5980 行）
```ts
const isOpen = stageCardOpen[message.id] ?? false;  // undefined 或 false 都导致折叠
const isGroupOpen = stageGroupOpen[turnBotId] ?? isGroupRunning;  // 历史消息全是 done → false
```

三重折叠叠加 → 历史会话首次加载时，所有编排阶段内容完全不可见。

### 附加问题：切换会话时未重置折叠状态

第 1715-1724 行的 session switch 逻辑中，重置了 `messages`、`sessionCitations` 等，但没有重置 `stageCardOpen` 和 `stageGroupOpen`。如果用户从会话 A 直接切换到会话 B，会话 B 的历史加载会继承会话 A 的折叠状态 key。

## 修复方案

### 修改 1：阶段卡片默认展开（第 2108 行）
```diff
- collapsedState[msg.id] = false;
+ collapsedState[msg.id] = true;
```

### 修改 2：阶段组默认展开（第 2118 行）
```diff
- groupCollapsedState[msg.turnBotId] = false;
+ groupCollapsedState[msg.turnBotId] = true;
```

### 修改 3：切换会话时重置折叠状态（第 1715-1724 行）
```diff
       startTransition(() => {
         // ... existing resets ...
+        setStageCardOpen({});
+        setStageGroupOpen({});
       });
```

### 修改 4：更新注释
```diff
- // 将所有历史阶段消息默认设置为折叠状态
+ // 将所有历史阶段消息默认设置为展开状态
```

## 教训

1. 变量名 `collapsedState` 暗示 true=折叠，但传给 `setStageCardOpen`（open state）时语义反转：true=展开
2. `??` 空值合并的 fallback 值必须与业务意图一致，不能随意写 `false`
3. 状态切换时必须重置所有相关 UI 状态，避免跨会话污染