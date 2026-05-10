# Analysis App 自动化生成 — Phase 4/5/6 开发记录

## 日期
2026-05-10

## 背景
Analysis App 自动化生成是 AskData 平台的核心功能之一，目标是从数据源元数据出发，自动生成完整的 Analysis App（含 Profile、代码、Prompt、热门问题、Git 提交）。整个流程分为 6 个 Phase，本次完成 Phase 4/5/6。

## Phase 4: Orchestrator Pipeline + API 端点 + Hot Questions

### 核心模块
- `core/modules/app_generator/orchestrator.py` — 10 阶段编排器
- `core/modules/app_generator/profile_generator.py` — Profile 生成
- `core/modules/app_generator/code_generator.py` — 代码生成
- `core/modules/app_generator/prompt_generator.py` — Prompt 生成
- `core/modules/app_generator/hot_question_generator.py` — 热门问题生成
- `core/modules/app_generator/langfuse_sync.py` — Langfuse 同步
- `core/modules/app_generator/registry_patcher.py` — Registry 注册
- `core/modules/app_generator/git_manager.py` — Git 提交
- `core/modules/app_generator/schemas.py` — Pydantic 数据模型
- `core/modules/app_generator/views.py` — FastAPI 路由

### 10 阶段 Pipeline
1. connection_test — 测试数据源连接
2. metadata_extract — 提取 Schema
3. ncr_convert — 转换为 NCR 规范
4. profile_gen — 生成 Analysis App Profile
5. code_gen — 生成代码文件
6. prompt_gen — 生成 Prompts
7. langfuse_sync — 同步到 Langfuse
8. hot_question_gen — 生成热门问题
9. registry_patch — 注册到 Analysis App Registry
10. git_commit — Git 提交产物

### 数据库模型
- `AppGenerationTask` — 任务主表 (t_app_generation_task)
- `AppGenerationStage` — 阶段子表 (t_app_generation_stage)
- `HotQuestion` — 热门问题表 (t_hot_question)

### API 端点
- POST /api/app-generator/tasks — 创建任务
- GET /api/app-generator/tasks — 任务列表
- GET /api/app-generator/tasks/{id} — 任务详情
- GET /api/app-generator/apps — 已生成 App 列表
- GET /api/app-generator/hot-questions — 热门问题
- POST /api/app-generator/hot-questions/generate — 生成热门问题

## Phase 5: MCP 工具暴露 + Hot Questions DB 持久化 + 前端面板

### MCP 工具 (6 个)
文件: `core/mcp/handlers/app_generator_handlers.py`
- metadata_extract — 提取数据源 Schema
- metadata_analyze — 分析元数据生成 Profile
- generate_app_preview — 预览生成代码
- generate_app — 正式生成 App
- sync_to_langfuse — 同步 Prompts
- list_generated_apps — 列出已生成 Apps

注册到 `core/mcp/stdio_server.py` 的 app_generator 域。

### 前端热门问题面板
- `web/src/features/query-space/components/HotQuestionsPanel.tsx` — 紫色卡片面板
- `web/src/features/query-space/pages/QueryAnalysisChat.tsx` — 集成到问数对话流

## Phase 6: 端到端验证 + 前端 Wizard

### 测试
- `tests/test_phase5.py` — 19 个测试
- `tests/test_phase6_e2e.py` — 28 个测试
- 全量回归: 139 个测试全部通过

### 前端 Wizard
- `web/src/features/app-generator/pages/AppGeneratorPage.tsx` — 5 步向导页面
  1. 选择数据源
  2. 配置领域
  3. 预览确认
  4. 生成中 (10 阶段进度条)
  5. 完成 (展示结果和热门问题)

### API Client 扩展
- `web/src/apis/app-generation/api.ts` — 新增 createAppGenerationTask, listAppTasks, getAppTaskDetail, listGeneratedApps

### 路由注册
- `web/src/shared/constants/index.ts` — 新增 ROUTES.APP_GENERATOR
- `web/src/app/routes/index.tsx` — 注册 /app-generator 路由
- `web/src/features/platform-config/pages/PlatformConfigPage.tsx` — 新增 "App 生成" 入口

## Git 提交记录
8 个 commit:
1. feat(askdata): AskData 流程优化与图谱增强 (24 文件)
2. feat(config): LLM 配置体系增强 (7 文件)
3. feat(app-generator): Analysis App 自动化生成 (45 文件) ← Phase 4/5/6 核心
4. feat(knowledge): 知识库与 Wiki 流程优化 (4 文件)
5. feat(user): 通知类型扩展 (8 文件)
6. fix(utils): Prose/Podcast 图谱节点优化 (10 文件)
7. feat(migration): 数据迁移重置、部署脚本及测试补充 (17 文件)
8. chore(migration): 删除旧的 alembic 重置迁移脚本 (1 文件)

## 技术要点
1. Orchestrator 使用 async/await + SQLAlchemy AsyncSession
2. 10 阶段按顺序执行，任一阶段失败则标记 failed 并停止
3. MCP 工具通过 ToolRegistry 注册到 app_generator 域
4. 前端 Wizard 使用 2 秒轮询获取任务进度
5. 热门问题生成器基于 Profile 的维度/度量字段自动生成
