---
title: "React const 暂时性死区导致 Cannot access before initialization 错误排查"
type: analysis
created: 2026-05-08
last_updated: 2026-05-08
source_count: 0
confidence: medium
status: active
tags:
  - react
  - frontend
  - temporal-dead-zone
  - const
  - usecallback
  - javascript
  - hoisting
---

## 问题概述

2026-05-08 在知识库管理页面添加 Wiki 入口按钮时，点击知识库模块后页面崩溃，报错：

```
页面加载失败
Cannot access 'm' before initialization
```

错误提示为路由懒加载失败，实际是 JavaScript 运行时异常。

---

## Root Cause 分析

### 根因：const 暂时性死区（Temporal Dead Zone）

**文件**: `web/src/features/knowledge/pages/KnowledgeManagement.tsx`

在 React 函数组件中，错误地将使用了 `selectedKnowledgeBase` 变量的 `useCallback` 定义在 `selectedKnowledgeBase` 的 `useState` 声明**之前**：

```typescript
// ❌ 错误代码：handleGoToWiki 在 selectedKnowledgeBase 声明之前使用
function KnowledgeManagement() {
  const { addKnowledgeBase, updateKnowledgeBase } = useData();
  const navigate = useNavigate();

  // handleGoToWiki 引用了 selectedKnowledgeBase，但后者还未声明
  const handleGoToWiki = useCallback(async () => {
    if (!selectedKnowledgeBase) return;     // 引用 selectedKnowledgeBase
    // ...
  }, [selectedKnowledgeBase, navigate]);    // 依赖数组也引用 selectedKnowledgeBase

  // selectedKnowledgeBase 在 handleGoToWiki 之后才声明
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);
  // ...
}
```

### 为什么会导致报错

在 JavaScript 中，`const` 和 `let` 声明的变量会被提升（hoisted），但在声明之前处于**暂时性死区（Temporal Dead Zone, TDZ）**。在 TDZ 中访问这些变量会抛出 `ReferenceError`：

```
ReferenceError: Cannot access 'm' before initialization
```

其中 `m` 是生产环境代码压缩后（minified）的变量名，对应开发环境中的 `selectedKnowledgeBase`。

### 运行机制详解

1. `useCallback(handler, deps)` 调用时，依赖数组 `[selectedKnowledgeBase, navigate]` **立即求值**
2. 此时 `selectedKnowledgeBase` 尚未执行 `useState` 初始化，处于 TDZ
3. JavaScript 引擎抛出 `ReferenceError`，导致模块初始化失败
4. 由于组件是路由懒加载，错误表现为"路由懒加载失败"

---

## 修复方案

### 修复：将 useCallback 定义移到所有 useState 声明之后

**文件**: `web/src/features/knowledge/pages/KnowledgeManagement.tsx`

```typescript
function KnowledgeManagement() {
  const { addKnowledgeBase, updateKnowledgeBase } = useData();
  const navigate = useNavigate();

  // ✅ 先声明所有状态变量
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [pageMode, setPageMode] = useState<PageMode>('list');
  const [tagFilter, setTagFilter] = useState<string>('all-tags');
  // ... 其他 useState/useRef

  // ✅ 在所有状态声明之后，再定义使用这些状态的 useCallback
  const handleGoToWiki = useCallback(async () => {
    if (!selectedKnowledgeBase) return;
    // ...
  }, [selectedKnowledgeBase, navigate]);

  // ...
}
```

---

## 影响范围

- **文件**: `web/src/features/knowledge/pages/KnowledgeManagement.tsx`
- **影响**: 知识库管理整个模块无法加载，页面崩溃
- **严重程度**: 高 — 阻塞整个功能模块的正常使用

---

## 经验总结

### 1. React 函数组件中的变量声明顺序

在 React 函数组件中，`const`/`let` 变量严格遵循**声明顺序**：

| 声明位置 | 可访问性 |
|---------|---------|
| `useState`/`useRef` 等 Hook 调用 | 必须在组件顶层，按固定顺序执行 |
| 使用 Hook 返回值的变量（如 `useCallback`） | **必须在**对应的 Hook 声明之后 |

**黄金法则**：将所有 `useState` 和 `useRef` 声明放在所有 `useCallback`/自定义函数之前。

### 2. 暂时性死区（TDZ）的识别

`const`/`let` 的 TDZ 特性：
- 变量在作用域内被"hoisted"但不可访问，直到声明被执行
- 在声明前访问会抛出 `ReferenceError: Cannot access 'X' before initialization`
- 生产环境（minified）错误信息中变量名会被压缩（如 `m`），增加了排查难度

### 3. 懒加载错误的排查方向

当遇到"路由懒加载失败"类错误时，排查方向：
1. ✅ **优先检查模块内部语法错误和运行时错误**（本文案例）
2. ❌ 不要立即怀疑网络或构建配置
3. 在 `Suspense` 的 `fallback` 之上，真正的错误来自组件模块内部的执行异常

### 4. 预防措施

- 在 React 函数组件中保持一致的声明顺序：`useState` → `useRef` → `useEffect` → `useCallback`/自定义函数
- 新添加的变量定义应插入到同类型声明的末尾，而非随意插入
- 团队可通过 ESLint 规则 `no-use-before-define`（配置为检查 `const`/`let`）来静态预防

---

## 关联文档

- [历史会话加载卡死 — useEffect 循环重载与主线程阻塞](./历史会话加载卡死-useeffect-循环重载与主线程阻塞.md) — 另一个 React 前端调试案例

