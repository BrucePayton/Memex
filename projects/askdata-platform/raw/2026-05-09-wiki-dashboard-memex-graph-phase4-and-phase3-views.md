# Wiki Dashboard Memex 对齐 — Phase 4 Canvas 知识图谱 + Phase 3 视图实现

## 会话摘要

本次会话完成了 Wiki Dashboard 与 Memex 对齐计划的剩余核心工作：

### 修复：WikiManagementPage.tsx 孤儿代码清理

- 该文件在前期重构后残留约 719 行孤儿代码（旧的 mock 数据、useEffect 处理器、CRUD 处理器、400+ 行的 Tabs JSX）
- 使用 Write 工具完全重写为 22 行干净组件：仅保留 `useLocation` 知识库上下文传递 + `<WikiDashboardLayout />` 渲染
- 删除所有旧导入（shadcn UI 组件、旧 API、旧子组件）

### Phase 4: 知识图谱 Canvas 2D 渲染重写

**文件**: `web/src/features/wiki/components/KnowledgeGraph.tsx`

从 SVG + React state 驱动 → Canvas 2D + requestAnimationFrame：

- **渲染引擎**: HTML Canvas 2D，`devicePixelRatio` 高清适配，CSS 尺寸自动跟随容器
- **物理引擎**: 保留 d3-forceSimulation（forceLink + forceManyBody + forceCenter + forceCollide），alphaDecay 0.025
- **颜色系统**: Memex TC 色值精确匹配：
  - source: `#3fb950` 绿
  - entity: `#58a6ff` 蓝
  - concept/technique: `#bc8cff` 紫
  - comparison: `#d29922` 黄
  - analysis: `#39d2c0` 青
  - overview/missing: `#8b949e` 灰 / `#f85149` 红虚线边框
  - page/tag/folder: 兼容后端现有 type
- **交互**:
  - 节点拖拽 → 设置 fx/fy → reheat simulation，松手释放
  - 悬停高亮 → 更亮填充 + 放大标签 + 外发光光晕
  - Canvas 背景拖拽平移 + 滚轮缩放（scale 范围 0.2-4x）
  - 点击检测：区分 click（移动 < 5px）与 drag，click 触发 `onNodeClick`
- **图例**: 右下角半透明覆盖层，列出所有 8 种 Memex 节点类型及其色点
- **边界状态**: 空数据时渲染 "No graph data available" 居中提示

**GraphView.tsx**: 新包装组件，调用 `getKnowledgeGraph(knowledgeBaseId)` API，页面节点点击通过 `wiki:navigate` 事件导航

### Phase 3: 新视图实现（带后端 API 支持）

| 视图 | 文件 | API | 功能 |
|------|------|-----|------|
| LintView | `views/LintView.tsx` | `lintWiki()` | 多维检查，pass/warn/fail 图表，Auto-fix 按钮 |
| ReflectView | `views/ReflectView.tsx` | `reflectWiki()` | 元分析摘要 + 建议列表 + 统计网格 |
| ProvenanceView | `views/ProvenanceView.tsx` | `getWikiProvenance()` + `fixWikiProvenance()` | 引用覆盖率进度条，逐页修复按钮 |
| SearchView | `views/SearchView.tsx` | `searchWiki()` | 全文搜索输入，搜索结果列表，点击导航 |
| SettingsView | `views/SettingsView.tsx` | `getWikiExternalStatus()` | 外部服务状态（Claude CLI 等），执行模式切换 |

### 状态管理：knowledgeBaseId 透传

- `useDashboardState` 新增 `knowledgeBaseId` state + `wiki:kb-context` 事件监听
- `DashboardState` 类型新增 `knowledgeBaseId?: number`
- 数据流: WikiManagementPage dispatch event → useDashboardState → WikiDashboardLayout → DashboardViews → GraphView

### 提交

`0a7b5268` — feat(wiki): Memex 风格 Dashboard 布局与知识图谱 Canvas 渲染（18 files, +1425/−0）
