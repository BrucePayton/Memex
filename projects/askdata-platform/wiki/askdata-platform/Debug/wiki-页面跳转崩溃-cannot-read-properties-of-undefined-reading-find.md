---
title: Wiki 页面跳转崩溃 - missing availablePages prop
type: analysis
tags: ["wiki", "frontend", "crash", "typescript"]
---

## 故障概述

用户在知识库管理页面选择知识库后，进入 "Wiki 知识库" Tab，点击 "查看 Wiki" 按钮时页面崩溃，显示 "页面加载失败"。

先后出现两个错误：
1. `Cannot read properties of undefined (reading 'find')` — **WikiPageCompare**
2. `Cannot read properties of undefined (reading 'length')` — **WikiComposeDialog**

## 触发路径

1. `/knowledge` → 选择知识库 → detail 视图
2. 点击 "Wiki 知识库" Tab → `KnowledgeWikiTab` 组件渲染
3. 点击 "查看 Wiki" 按钮 → `navigate(ROUTES.WIKI, { state: { knowledgeBaseId } })`
4. 路由跳转到 `/wiki` → `WikiManagementPage` 渲染 → **崩溃**

## Root Cause

`WikiManagementPage` 在渲染 dialog 组件时，其中两个组件缺少必需的 `availablePages` prop，而组件内部直接在该 prop 上调用数组方法（`.find()` / `.length`），导致 `TypeError`。

### Bug 1: WikiPageCompare（.find）

```tsx
// WikiManagementPage.tsx — 缺失 availablePages
<WikiPageCompare open={compareOpen} onOpenChange={setCompareOpen} />

// WikiPageCompare.tsx — 直接调用 .find()
const pageA = availablePages.find(p => p.id === Number(pageAId));
```

### Bug 2: WikiComposeDialog（.length）

```tsx
// WikiManagementPage.tsx — 同样是缺失 availablePages
<WikiComposeDialog open={composeOpen} onOpenChange={setComposeOpen} />

// WikiComposeDialog.tsx — 直接调用 .length
{availablePages.length === 0 ? ( ... ) : ( ... )}
```

两个 dialog 组件在渲染时即使 `open=false`，React 仍会执行组件函数体，因此对 `undefined` 的 prop 的数组方法调用在挂载瞬间就崩溃。

错误被 `ProtectedRoute` 中的 `DataProviderErrorBoundary` 捕获，展示 "页面加载失败" 错误 UI。第一个错误修复后，刷新页面再次导航会暴露第二个错误。

## 修复方案

### `WikiManagementPage.tsx:755-756`

补传 `availablePages` 给两个 dialog，从已加载的 `pages` state 提取：

```tsx
<WikiComposeDialog
  open={composeOpen}
  onOpenChange={setComposeOpen}
  availablePages={pages.map(p => ({ id: p.id, title: p.title }))}
/>
<WikiPageCompare
  open={compareOpen}
  onOpenChange={setCompareOpen}
  availablePages={pages.map(p => ({ id: p.id, title: p.title }))}
/>
```

### `WikiPageCompare.tsx:18 + WikiComposeDialog.tsx:20`

添加默认值 `[]` 做防御：

```tsx
// 两个组件相同模式
export default function WikiPageCompare({ open, onOpenChange, availablePages = [] }: WikiPageCompareProps) {
export default function WikiComposeDialog({ open, onOpenChange, availablePages = [] }: WikiComposeDialogProps) {
```

## 涉及文件

- `web/src/features/wiki/pages/WikiManagementPage.tsx:755-756` — 补传 availablePages
- `web/src/features/wiki/components/WikiPageCompare.tsx:18` — 默认值 `[]`
- `web/src/features/wiki/components/WikiComposeDialog.tsx:20` — 默认值 `[]`

## 经验教训

1. **同一条枪连续走火两次**：`WikiPageCompare` 和 `WikiComposeDialog` 都是同一个反模式——`availablePages` prop 必填但未传入。说明类似问题应举一反三，检查所有 dialog 组件。
2. **Dialog 组件也会执行顶层代码**：即使 `open=false`，组件函数体内的顶层 `.find()` / `.length` 调用仍会在每次渲染时执行，不能依赖 dialog 的开关状态做保护。
3. **防御性编程**：对来自父组件的数组 props 始终提供默认值 `= []`，这是最低成本的防崩溃手段。
4. **检修清单**：`WikiManagementPage` 中所有无条件渲染的子组件（`WikiQueryDialog`、`WikiComposeDialog`、`WikiPageCompare`、`WikiWriteDialog`）都应检查其 props 接口，确保不缺少必填项。
