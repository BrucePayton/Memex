# Wiki 知识库功能完整集成 — 实现总结

## 背景
Free-Style-Report 平台已有向量知识库（Vector KB）管理功能，Wiki 知识库作为并列架构的能力尚未完全集成到 KB 详情页的 Tab 体系、预处理流程和工作空间中。后端已有 70+ Wiki API 端点（CRUD、搜索、知识图谱、同步等），前端已有 WikiManagementPage 和 KnowledgeWikiTab 组件，但缺少 Tab 整合、绑定自动创建文件夹、预处理推 RAW、工作空间推送等关键集成。

## 架构决策
- Wiki 与向量知识库是**并列关系**，通过 `t_knowledge_wiki_binding` 桥接表关联
- 每个知识库（KB）可绑定一个 Wiki 工作空间，绑定后自动创建对应 Wiki 文件夹
- 解绑时 Wiki 页面保留，仅停止自动同步
- 绑定关系存储在 `t_knowledge_wiki_binding`，新增 `wiki_folder_id` 列指向 `t_wiki_folder`

## 分阶段实现

### 阶段 1: KB 详情页 Tab 重构
- 新建 `KnowledgeDetailTabs.tsx`：shadcn Tabs 组件，包含"向量知识库"和"Wiki知识库"两个 Tab
- 修改 `KnowledgeManagement.tsx`：右侧详情区替换为 Tab 组件
- workspaceId 从 `getKnowledgeBaseBinding()` 获取

### 阶段 2: Wiki 绑定增强
- 后端 `wiki_helper.py`：bind() 支持 `create_folder` 参数，自动创建 `kb-{resource_uuid[:8]}` 文件夹
- `db_initial_models.py`：KnowledgeWikiBinding 新增 `wiki_folder_id` 列
- DB 迁移脚本 `add_wiki_folder_id_to_binding.py`
- 解绑文案明确提示"已有 Wiki 页面将保留"

### 阶段 3: Wiki 管理页面增强
- 新增 `WikiRawSourcesTab` — RAW 源列表（搜索 + type 过滤）
- 新增 `WikiCompareTab` — 两页面对比（相似度、字数、diff）
- 新增 `WikiStaleReviewTab` — 过时页面审查（天数阈值 + 标记已审查）
- 新增 `WikiComposeTab` — 多选页面 + LLM 生成合成内容
- `WikiManagementPage`：从 location.state 读取 KB 上下文，自动选中绑定文件夹

### 阶段 4: 预处理步骤推 Wiki 开关
- `DocumentPreprocessStep.tsx`：新增 Switch 开关"同步到 Wiki 知识库"
- 开关自动检测绑定状态，未绑定时禁用并提示
- 开启后遍历预处理内容，创建 Wiki 页面 + 推送 RAW 源

### 阶段 5: 工作空间推 Wiki 集成
- `QueryAnalysisChat.tsx`：消息底部新增"沉淀到 Wiki"按钮
- `getWorkspaceBindings` API 封装
- WikiIntegrationDialog 扩展支持 chat/analysis sourceType

## 关键文件清单

| 文件 | 操作 |
|------|------|
| `web/src/features/knowledge/components/KnowledgeDetailTabs.tsx` | 新建 |
| `web/src/features/knowledge/pages/KnowledgeManagement.tsx` | 修改 |
| `web/src/apis/wiki/index.ts` | 修改（类型参数修复 + API 增强） |
| `core/models/db/db_initial_models.py` | 修改（wiki_folder_id 列） |
| `core/modules/knowledge/wiki_helper.py` | 修改（自动创建文件夹） |
| `core/modules/knowledge/wiki_request_model.py` | 修改（create_folder 字段） |
| `core/modules/knowledge/views/wiki_views.py` | 修改（绑定端点 + 工作空间查询） |
| `web/src/features/wiki/components/KnowledgeWikiTab.tsx` | 修改 |
| `web/src/features/wiki/pages/WikiManagementPage.tsx` | 修改 |
| `web/src/features/wiki/components/WikiRawSourcesTab.tsx` | 新建 |
| `web/src/features/wiki/components/WikiCompareTab.tsx` | 新建 |
| `web/src/features/wiki/components/WikiComposeTab.tsx` | 新建 |
| `web/src/features/wiki/components/WikiStaleReviewTab.tsx` | 新建 |
| `web/src/components/DocumentPreprocessStep.tsx` | 修改 |
| `web/src/features/query-space/pages/QueryAnalysisChat.tsx` | 修改 |
| `storage/data_migration/alembic_data_migration/alembic/versions/add_wiki_folder_id_to_binding.py` | 新建 |

## 修复的 TypeScript 错误
- `wiki/index.ts`：28 处 apiClient 调用缺少泛型类型参数 → 显式添加 `<Type>`
- `KnowledgeManagement.tsx`：`NodeJS.Timeout` 不存在于浏览器环境 → `ReturnType<typeof setTimeout>`；动态 `import('./DataContext')` 无法解析 → 改为直接导入 `KnowledgeBaseTag` 类型
