---
title: "Wiki Dashboard 对齐 — Canvas 知识图谱渲染与 Phase 3 视图实现"
type: analysis
created: 2026-05-09
last_updated: 2026-05-09
source_count: 1
confidence: medium
status: active
tags:
  - wiki-dashboard
  - knowledge-graph
  - canvas-rendering
  - memex-alignment
  - phase-complete
  - frontend
  - 2026-05
sources:
  - src-2026-05-09-wiki-dashboard-memex-graph-phase4-and-phase3-views
---

## 概述

完成 Wiki Dashboard 与 Memex 对齐的剩余核心工作：Canvas 2D 知识图谱重写、Phase 3 视图实现、孤儿代码清理、knowledgeBaseId 状态透传。至此，对标计划中除 i18n（可选）外的所有 Phase 均已完成。[^src-0]

## Canvas 知识图谱重写

**文件**: `web/src/features/wiki/components/KnowledgeGraph.tsx` — 从 SVG + React state 驱动全面重写为 Canvas 2D + requestAnimationFrame。[^src-0]

### 渲染架构

- **物理引擎**: 保留 d3-forceSimulation（forceLink, forceManyBody, forceCenter, forceCollide），alphaDecay 0.025
- **画布**: HTML Canvas 2D，`devicePixelRatio` 适配高清屏，CSS 尺寸自动跟随容器 ResizeObserver
- **渲染循环**: `requestAnimationFrame` 驱动，每帧从 `positionsRef` 读取节点位置重绘，不触发 React re-render
- **数据流**: d3 tick → 写入 Map ref → rAF 读取绘制 → 零 React 状态更新开销

### Memex TC 颜色系统（精确匹配）

| 类型 | 色值 | 色名 |
|------|------|------|
| source | `#3fb950` | 绿 |
| entity | `#58a6ff` | 蓝 |
| concept / technique | `#bc8cff` | 紫 |
| comparison | `#d29922` | 黄 |
| analysis | `#39d2c0` | 青 |
| overview | `#8b949e` | 灰 |
| missing | `#f85149` | 红虚线边框 |
| page / tag / folder | 兼容后端现有类型 | — |

### 交互

- **节点拖拽**: 设置 `simulation.node.fx/fy` → reheat（alphaTarget 0.3）→ 松手释放 `fx/fy = null`
- **悬停高亮**: 外发光光晕（alpha 0.12）+ 标签放大 13px + 更亮填充
- **Canvas 平移**: 背景拖拽记录偏移量，重绘时 `ctx.translate`
- **滚轮缩放**: `deltaY * 0.002` 调整 scale，范围 [0.2, 4]，`ctx.scale` 应用
- **点击导航**: 区分 click（pointer up 时移动 < 5px）与 drag，page 节点触发 `wiki:navigate` 事件
- **图例**: 右下角半透明覆盖层，8 种节点类型色点 + 标签

### GraphView 包装

`views/GraphView.tsx` — 调用 `getKnowledgeGraph(knowledgeBaseId)`，加载态 spinner、错误提示、空数据兜底、节点点击页面导航。[^src-0]

## Phase 3 新视图（带后端 API 支持）

| 视图 | API | 关键特性 |
|------|-----|---------|
| LintView | `lintWiki()` | 多维检查结果表，pass/warn/fail 三态图标，Auto-fix |
| ReflectView | `reflectWiki()` | 元分析摘要 + 建议列表 + 统计网格 |
| ProvenanceView | `getWikiProvenance()` / `fixWikiProvenance(pageId)` | 引用覆盖率进度条，逐页修复按钮 |
| SearchView | `searchWiki()` | 全文搜索输入框 + 结果列表 + 点击导航 |
| SettingsView | `getWikiExternalStatus()` | 外部服务状态显示 + LLM/Claw Code 执行模式切换 |[^src-0]

## 状态管理透传

`useDashboardState` 新增 `knowledgeBaseId` 状态 + `wiki:kb-context` 事件监听，数据流：WikiManagementPage → CustomEvent → useDashboardState → WikiDashboardLayout → DashboardViews → GraphView 消费。[^src-0]

## WikiManagementPage 清理

文件中残留约 719 行孤儿代码（旧 mock 数据、useEffect、CRUD 处理器、400+ 行 Tabs JSX、未使用导入）。使用 Write 工具完全重写为 22 行薄壳组件。[^src-0]

## 提交记录

`0a7b5268` — feat(wiki): Memex 风格 Dashboard 布局与知识图谱 Canvas 渲染（18 files, +1425/−0）[^src-0]

[^src-0]: projects/askdata-platform/raw/2026-05-09-wiki-dashboard-memex-graph-phase4-and-phase3-views.md

