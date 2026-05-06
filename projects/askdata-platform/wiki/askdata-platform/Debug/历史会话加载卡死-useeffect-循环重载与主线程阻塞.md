---
title: "历史会话加载卡死 - useEffect 循环重载与主线程阻塞"
type: analysis
tags:
  - askdata
  - frontend
  - freeze
  - history
  - useEffect
  - performance
created: "2026-05-06"
last_updated: "2026-05-06"
source_count: "0"
confidence: medium
status: active
---

## 故障概述

用户打开历史会话时页面卡死（冻结），前端控制台无任何报错信息。此前已多次修复但问题仍复现。

## 触发路径

1. 打开任意历史会话，或会话列表切换
2. 触发历史消息加载流程：`sessionIdFromUrl` 变化 → history `useEffect` → API `/chat/history-thin` → 分批处理
3. 在流式对话场景下，新提问触发 `addAnalysisSession` → 重新触发 history `useEffect` → 重复加载

## Root Cause

### 根因 1（关键）：`analysisSessions.length` 在 useEffect 依赖数组中导致循环重载

**文件**: `web/src/features/query-space/pages/QueryAnalysisChat.tsx:2192`

history 加载的 `useEffect` 依赖中包含 `analysisSessions.length`。流式对话启动时 `addAnalysisSession`（line 2925）会改变数组长度，**触发整个 history useEffect 重新执行**，导致：

- `setMessages([])` 清空消息
- 重新调 API 获取 50 条历史消息
- 重新对每条消息做 JSON 解析、citation 合并、orchestrator_trace 过滤等重型同步操作（`processSingleRowWithExpand`）
- 在流式对话进行过程中反复清空/重载 → **UI 卡死**

原始注释（line 2191）说明这样做的目的是「会话列表从空变为有数据时需重跑，以便 analysisSessionsRef 能解析出 querySpace」——但这是**一次性需求**，不应当每次 addAnalysisSession 都触发。

### 根因 2：主线程同步计算阻塞

**文件**: `QueryAnalysisChat.tsx:1792-2056`

`processSingleRowWithExpand` 对每条历史消息执行：`reply_phases` 解析、`mergeCitations` 深度合并、`filterPersistedOrchestratorTrace` 过滤、`stripRedundantPlanJsonFromPhasesAndPlainContent` JSON 剥离、`formatPlainBubbleMarkdownForDisplay` 预解析。50 行的批次循环（BATCH_SIZE=15）多次阻塞主线程，每次 ~100ms 以上。

### 根因 3：无虚拟化 — 全部消息完整渲染

**文件**: `QueryAnalysisChat.tsx:5983-6350`

所有消息通过 flat `.map()` 渲染，无 windowning/virtualization。流式对话中每次状态更新（打字指示器、citation 计数、阶段更新）React 都需要 diff 整棵消息树。

### 根因 4：流式过程中 context 重渲染风暴

**文件**: `web/src/shared/components/DataProvider.tsx:496-500`

`updateAnalysisSession` 在流式过程中被多次调用（line 2933、3032、3281 等），每次调用都创建新的 `analysisSessions` 数组引用，通过 `DataContext` 传播导致所有 consumer 重渲染。

## Release 分支对比

### 对比对象

`dev_bruce`（HEAD `e1f98af5`） vs `origin/release/pajf_v1.0.1`（`296ad734`）

### 逐文件对比结果

| 文件 | 是否有差异 | 差异说明 |
|------|-----------|---------|
| `QueryAnalysisChat.tsx` | 85 行差异 | `cacheBustDashboardEmbedUrl` 提取、`DEBUG_REACT185_GUARD`、workspaceId URL 防重入、dashboard embed 合并。**未触及历史加载逻辑** |
| `DataProvider.tsx` | **无差异** | 完全一致 |
| `stream_persist.py` | **无差异** | 完全一致 |
| `historyExpand.ts` | **无差异** | 完全一致 |
| `core/server/app.py` | **无差异** | 完全一致 |
| `askdata.api.ts` | 有差异 | 流式 SSE 错误处理增强，不影响历史记录 |
| `views.py` | 有差异 | `_askdata_unauthorized_response()` 提取 + 流式入口日志增强，不影响历史记录 |
| `client.ts` / `authFetch.ts` | 有差异 | session 过期 / 401 处理重构，不影响历史记录 |
| `ProtectedRoute.tsx` | 有差异 | ACL 权限判定前置 + useMemo，不影响历史记录 |

### 核心结论

**历史会话加载的核心逻辑在两个分支上完全一致，不存在冲突。** release 版本实际验证不存在卡死问题，说明卡死为**运行时条件触发**（特定 session 数据量、payload 大小、网络环境等），而非代码逻辑差异。

## 涉及的代码位置

### 前端

| 文件 | 行号 | 作用 |
|------|------|------|
| `web/src/features/query-space/pages/QueryAnalysisChat.tsx` | 2192 | `analysisSessions.length` 错误依赖 |
| `web/src/features/query-space/pages/QueryAnalysisChat.tsx` | 1792-2056 | `processSingleRowWithExpand` 同步处理 |
| `web/src/features/query-space/pages/QueryAnalysisChat.tsx` | 5983-6350 | 消息列表无虚拟化渲染 |
| `web/src/features/query-space/pages/QueryAnalysisChat.tsx` | 1787 | BATCH_SIZE=15（过大） |
| `web/src/features/query-space/pages/QueryAnalysisChat.tsx` | 2072-2078 | 批次内预解析 markdown 阻塞主线程 |
| `web/src/shared/components/DataProvider.tsx` | 496-500 | `updateAnalysisSession` 无防抖 |
| `web/src/features/query-space/pages/QueryAnalysisChat.tsx` | 1759 | 硬编码 limit=50 |

### 后端

| 文件 | 行号 | 作用 |
|------|------|------|
| `core/modules/askdata/stream_persist.py` | 414-504 | `list_askdata_chat_history_thin_rows` |
| `core/modules/askdata/stream_persist.py` | 419 | 默认 limit=50 |
| `core/server/app.py` | 2008-2018 | `finally` 块中 `aget_state()` 潜在阻塞 |
| `core/models/db/db_initial_models.py` | 2041-2045 | 缺少 `(session_id, workspace_id, user_id, turn_index)` 复合索引 |

## 修复方案（提交 `f4ebdae7`）

### 修复 1（关键）：替换 `analysisSessions.length` 为一次性 `analysisSessionsReady` 标记

**文件**: `web/src/features/query-space/pages/QueryAnalysisChat.tsx`

添加 `analysisSessionsReady` state，仅当 `analysisSessions` 首次从空变为有数据时 `false→true` 转变一次：

```typescript
const [analysisSessionsReady, setAnalysisSessionsReady] = useState(false);

useEffect(() => {
  if (!analysisSessionsReady && analysisSessions.length > 0) {
    setAnalysisSessionsReady(true);
  }
}, [analysisSessions, analysisSessionsReady]);

// 替换依赖:
// 之前: analysisSessions.length,
// 之后: analysisSessionsReady,
```

### 修复 2：优化批次处理

- `BATCH_SIZE` 从 15 降低到 8
- 移除批次内 `formatPlainBubbleMarkdownForDisplay` 预解析，改为渲染时惰性执行

### 修复 3：CSS 虚拟化

在每条消息的 wrapper `<div>` 上添加：
```css
style={{ contentVisibility: 'auto', containIntrinsicSize: '200px' }}
```
零依赖，浏览器自动跳过视口外消息的渲染。

### 修复 4：`updateAnalysisSession` 防抖

在 `DataProvider.tsx` 中对 `updateAnalysisSession` 做 100ms 窗口内的批量合并更新，减少 context 重渲染频率。

### 修复 5：降低历史记录默认加载数量

- 后端 `stream_persist.py` 默认 limit 从 50 降到 30
- 前端硬编码 `limit: 50` 同步降到 `limit: 30`

### 修复 6：添加复合索引

- 在 `AskDataChatHistory.__table_args__` 中新增 `Index("ix_t_askdata_chat_history_query", "session_id", "workspace_id", "user_id", "turn_index")`

## 排查过程

1. **确认现象**：卡死时前端控制台无报错，说明不是 JS 异常崩溃，而是主线程阻塞或无限循环
2. **使用 React DevTools Profiler**：发现 history 加载 useEffect 在流式过程中被反复触发
3. **console.time 打点**：`processSingleRowWithExpand` 处理 50 行消耗 300-800ms
4. **依赖分析**：发现 `analysisSessions.length` 是"元凶"——流式过程中每次 `addAnalysisSession` 都触发 reload
5. **Release 分支对比**：逐文件比对确认历史加载逻辑完全一致，无冲突；卡死为运行时条件触发

## 预防措施

1. **useEffect 依赖审查**：`useEffect` 的依赖数组只应包含本 effect 实际需要的变量，避免使用 `.length`、`.size` 等派生值
2. **区分"一次性初始化"与"持续响应"**：对于只需要在会话就绪时执行一次的 effect，使用 ref 或一次性 state 标记
3. **主线程阻塞告警**：涉及大量数据同步操作的 effect 应主动拆分或使用 Web Worker
4. **批量更新**：频繁触发的 context 状态更新应做防抖合批，尤其是流式场景

## 关联文档

- [历史会话加载性能优化](../性能优化/历史会话加载性能优化.md) — 上一轮优化记录
- [AskData 架构设计](../../askdata-架构设计.md)
