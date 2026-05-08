# Changelog

| Date | Source | Summary |
|------|--------|---------|
| 2026-05-09 | 重构/架构 | **LLM 调用统一入口重构 — ScopeConfig → LLMConfig**：修复 `LLMParamsUtils` 静默降级，补齐 `LLMConfig` 缺失方法，迁移 `utils/llms/llm.py` 的 10 个 dashboard collab 调用点到 `LLMConfig()`，合并 4 份 report agent `LLMConfig` dataclass 为共享基类，修复 3 个断掉的调用者，添加 env var 覆盖支持 [^src-llm-call-unification-summary] |
| 2026-05-09 | 功能开发 | **Wiki 知识库功能完整集成（5 阶段）**：KB 详情 Tab 重构（向量/Wiki 切换）、绑定自动创建 Wiki 文件夹、新增 4 个管理 Tab（RAW Sources/Compare/Stale Review/Compose）、预处理步骤推 Wiki 开关、工作空间 Q&A/分析结果沉淀到 Wiki。新增迁移 `add_wiki_folder_id_to_binding`，修复 wiki/index.ts 泛型类型参数缺失 |
| 2026-05-09 | 前端开发 | **Wiki Dashboard 功能完善**：补齐 12 个待实现视图（Browse/Health/Raw/History/Logs/Query/Review/Compare/Write/Ingest/Schema/Guide），新增 LLM/Claw Code 执行模式切换（localStorage 持久化），新增 5 个 API 封装 |
| 2026-05-09 | 综合修复 | **平台多问题修复**：Wiki 404 路由修复、领域配置/Provider 路由挂载、通知中心事件驱动启用（快照/数据源/Wiki 同步/启动）、领域模板静态→动态聚合重构、外部资源管理 Tab 重构、Claw Code 配置面板 |
| 2026-05-08 | 前端部署修复 | 前端 Docker 打包失败修复：孤儿 `</Suspense>` 和 `} />` 标签破坏 JSX 解析树 |
| 2026-05-08 | 外部资源管理 | 外部资源管理功能补全：平台注册管理 API、适配器源码、前端平台管理页面与路由 |
| 2026-05-08 | 前端调试 | React const 暂时性死区导致 Cannot access before initialization 错误排查 |
| 2026-05-08 | 开发修复 | 平台配置模块迁移侧边栏系统管理及权限修复 |
| 2026-05-07 | 数据库迁移 | 补全 17 张缺失数据库表（DomainConfig/MCP/Wiki/LLM Config 等） |
| 2026-05-07 | 前端开发 | MainSide 通知中心功能恢复 |
| 2026-05-07 | 前端开发 | 平台配置前端功能缺失识别与实现 |
| 2026-05-07 | 部署修复 | nginx 配置重复指令问题彻底解决 |
| 2026-05-07 | 开发修复 | Wiki Memex 对标优化 Phase 1-4 完成 |
| 2026-05-05 | 开发规划 | 成果物文本自适应与导出能力建设规划 |
| 2026-05-04 | 代码库扫描 | 内容层报告生成功能问题分析 |
| 2026-05-04 | 代码库扫描 | Claw Code 实现审计与分析 |
