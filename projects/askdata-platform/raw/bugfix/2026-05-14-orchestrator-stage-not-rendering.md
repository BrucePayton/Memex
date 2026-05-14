# 修复：历史会话编排阶段（骨扇屏）完全不渲染

日期：2026-05-14
分支：backup/dev_bruce_askdata

## 问题描述

打开历史会话时，API 成功返回了真实的历史消息数据，但编排阶段（orchestrator-stage）的内容完全不显示，只有一个空白气泡留存，没有任何可点击的阶段标题。

## 根因分析

### 数据流

1. API 返回 `row.payload.orchestrator_trace` 包含阶段事件数组
2. `processSingleRowWithExpand` 中 `pushStageRow` 将每个阶段转为 `type: 'orchestrator-stage'` 的 Message
3. `setMessages(withSeqs)` 存入消息列表
4. `useStageTreeMemo(displayMessages)` 构建 `childStageIds`、`stageGroupByTurn` 等
5. 渲染时遍历 `displayMessages`，检查是否在 `childStageIds` 中

### Bug 定位

**文件**: `web/src/features/query-space/hooks/useStageTreeMemo.ts`（第 32-38 行）

```ts
const pid = m.stageEvent?.parent_stage_id;
if (pid) {
  const parentKey = `${tk}::${pid}`;
  const siblings = stageChildrenMap.get(parentKey) || [];
  siblings.push(m);
  stageChildrenMap.set(parentKey, siblings);
  childStageIds.add(key);  // BUG: 无论父节点是否存在都加入
}
```

渲染处（QueryAnalysisChat.tsx 第 6217-6224 行）：
```tsx
if (
  message.type === 'orchestrator-stage' &&
  message.stageEvent?.stage_id &&
  childStageIds.has(...)
) {
  return null;  // 所有子阶段被跳过
}
```

**问题**：后端 `combo_executor.py` 发送的阶段事件大量使用 `parent_stage_id="supper_short"`，但父阶段 `stage_id="supper_short"` 本身从未被发送或持久化。因此所有子阶段在 `childStageIds` 中，渲染时被 `return null` 全部跳过。

### 对比正确逻辑

同文件中 `buildStageForest` 函数（第 666 行）正确处理了这种情况：
```ts
if (pid && byId.has(`${tk}::${pid}`)) {  // 检查父节点是否存在
  byId.get(`${tk}::${pid}`)!.children.push(node);
} else {
  roots.push(node);  // 父节点不存在时提升为根节点
}
```

## 修复方案

**修改文件**: `web/src/features/query-space/hooks/useStageTreeMemo.ts`

```diff
  const pid = m.stageEvent?.parent_stage_id;
- if (pid) {
+ if (pid && stageMessagesById.has(`${tk}::${pid}`)) {
```

添加父阶段存在性检查，使孤儿子阶段不被加入 `childStageIds`，从而作为根节点参与渲染。

## 部署方式

通过 deployment_local 的 compose 方案单独重建前端容器：
```bash
cd deployments/deployment_local
docker compose -p askdata-local --env-file .env \
  -f docker-compose.base.yaml -f docker-compose.data.yaml \
  -f docker-compose.redis.yaml -f docker-compose.keycloak.yaml \
  -f docker-compose.langfuse.yaml -f docker-compose.app.yaml \
  build askdata_frontend
docker compose -p askdata-local --env-file .env \
  -f docker-compose.base.yaml -f docker-compose.data.yaml \
  -f docker-compose.redis.yaml -f docker-compose.keycloak.yaml \
  -f docker-compose.langfuse.yaml -f docker-compose.app.yaml \
  up -d askdata_frontend
```

## 教训

1. 父子关系映射必须验证父节点是否存在，不能仅凭字段存在就归类为子节点
2. `buildStageForest` 已有正确实现模式，`useStageTreeMemo` 应保持一致
3. 流式响应和历史加载使用不同的阶段构建逻辑，需要统一验证