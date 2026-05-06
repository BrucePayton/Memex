---
title: "Wiki 页面跳转崩溃 - Cannot read properties of undefined (reading 'find')"
type: analysis
created: 2026-05-06
last_updated: 2026-05-06
source_count: 0
confidence: medium
status: active
tags:
  - wiki
  - frontend
  - crash
  - typescript
---

## 故障概述

用户在知识库管理页面选择知识库后，进入 "Wiki 知识库" Tab，点击 "查看 Wiki" 按钮时页面崩溃，显示 "页面加载失败" 和错误信息 `Cannot read properties of undefined (reading 'find')`。

## 触发路径

1. `/knowledge` → 选择知识库 → detail 视图
2. 点击 "Wiki 知识库" Tab → `KnowledgeWikiTab` 组件渲染
3. 点击 "查看 Wiki" 按钮 → `navigate(ROUTES.WIKI, { state: { knowledgeBaseId } })`
4. 路由跳转到 `/wiki` → `WikiManagementPage` 渲染 → **崩溃**

## Root Cause

`WikiManagementPage` 渲染了 `<WikiPageCompare>` 组件但未传入必需的 `availablePages` prop：

```tsx
// WikiManagementPage.tsx:756 — 缺少 availablePages
<WikiPageCompare open={compareOpen} onOpenChange={setCompareOpen} />
```

而 `WikiPageCompare` 内部直接对该 prop 调用 `.find()`：

```tsx
// WikiPageCompare.tsx:50-51
const pageA = availablePages.find(p => p.id === Number(pageAId));
const pageB = availablePages.find(p => p.id === Number(pageBId));
```

`availablePages` 为 `undefined` → `undefined.find()` 抛出 `TypeError`。

该错误被 `ProtectedRoute` 中的 `DataProviderErrorBoundary` 捕获，展示 "页面加载失败" 错误 UI。

## 修复方案

### 文件 1: `web/src/features/wiki/pages/WikiManagementPage.tsx`

补传 `availablePages` prop，从组件内已加载的 `pages` state 提取：

```tsx
<WikiPageCompare
  open={compareOpen}
  onOpenChange={setCompareOpen}
  availablePages={pages.map(p => ({ id: p.id, title: p.title }))}
/>
```

### 文件 2: `web/src/features/wiki/components/WikiPageCompare.tsx`

添加默认值 `[]` 做防御，防止其他调用方同样遗漏：

```tsx
export default function WikiPageCompare({ open, onOpenChange, availablePages = [] }: WikiPageCompareProps) {
```

## 涉及文件

- `web/src/features/wiki/pages/WikiManagementPage.tsx:756` — 补传 prop
- `web/src/features/wiki/components/WikiPageCompare.tsx:18` — 默认值防御

## 经验教训

1. **TypeScript 接口强制要求但运行时无法保证**：`WikiPageCompareProps.availablePages` 声明为 `{ id: number; title: string }[]`（非可选），但父组件调用时遗漏导致运行时崩溃。应优先使用默认值或运行时校验。
2. **Dialog 组件也会执行顶层代码**：即使 dialog 的 `open` 为 `false`，组件内的顶层 `.find()` 调用仍会在每次渲染时执行，因此不能依赖 dialog 的状态来保护数据访问。
3. **防御性编程**：对可能来自父组件的数组 props 始终提供默认值 `= []`，避免 `.find()`、`.map()`、`.filter()` 等调用崩溃。

