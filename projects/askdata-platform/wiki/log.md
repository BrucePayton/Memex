# Changelog

| Date | Source | Summary |
|------|--------|---------|
| 2026-05-09 | 前端开发 | **Wiki Dashboard Canvas 知识图谱 + Phase 3 视图补齐**：KnowledgeGraph 从 SVG 重写为 Canvas 2D（Memex TC 色值、d3-force 物理引擎、rAF 渲染、拖拽/平移/缩放/悬停、虚线边框 missing 节点、图例），新增 LintView/ReflectView/ProvenanceView/SearchView/SettingsView 5 个实装视图，knowledgeBaseId 状态透传，清理 WikiManagementPage 孤儿代码 |
| 2026-05-09 | 前端开发 | **Wiki Dashboard 功能完善**：补齐 12 个待实现视图（Browse/Health/Raw/History/Logs/Query/Review/Compare/Write/Ingest/Schema/Guide），新增 LLM/Claw Code 执行模式切换（localStorage 持久化），新增 5 个 API 封装 [^src-2026-05-09-platform-feature-completion] |
| 2026-05-09 | 综合修复 | **平台多问题修复**：Wiki 404 路由修复、领域配置/Provider 路由挂载、通知中心事件驱动启用（快照/数据源/Wiki 同步/启动）、领域模板静态→动态聚合重构、外部资源管理 Tab 重构、Claw Code 配置面板 |
| 2026-05-08 | 前端部署修复 | 前端 Docker 打包失败修复：`web/src/app/routes/index.tsx` 存在孤儿 `</Suspense>` 和 `} />` 标签（第 153-154 行），破坏 JSX 解析树，删除后构建恢复正常 |
| 2026-05-08 | 外部资源管理 | 外部资源管理功能补全：实现平台注册管理 API（GET/POST/PATCH/DELETE /wp/platforms + POST /wp/platforms/{id}/discover），补全平台适配器源代码（Dify/DSC/SkillHub 适配器），新增前端平台管理页面与路由，统一资源类型定义（新增 skill/workflow 类型） |
| 2026-05-08 | 前端调试 | React const 暂时性死区导致 Cannot access before initialization 错误排查：`useCallback` 引用 `useState` 变量但定义在其之前，触发了 const 的 temporal dead zone，导致知识库模块路由懒加载失败 |
| 2026-05-08 | 开发修复 | 平台配置模块迁移侧边栏系统管理及权限修复：后端 page_group_defaults.py 新增 PlatformConfig/LlmConfig/Claw/DomainConfig 页面组定义（parent_menu=system_management）；前端移除侧边栏隐藏逻辑、补充路由权限完整性、首页移除平台配置卡片 |
| 2026-05-07 | 数据库迁移 | 补全 17 张缺失数据库表：通过 `alembic revision --autogenerate` 生成新 revision `0a2119b5be45`，创建 DomainConfig、MCP、Wiki、LLM Config 等 17 张缺失表（Claw-Code 集成模块），同时补全已有表的 ADD COLUMN 变更。审阅中排除了 LangGraph checkpoint 表 DROP 和 FK 约束重建等多余操作 |
| 2026-05-07 | 前端开发 | MainSide通知中心功能恢复：代码回归后重建完整通知功能，包括API客户端扩展、NotificationBell组件创建、MainSidebar集成，支持未读计数、标记已读、删除、分页加载、30秒轮询等 |
| 2026-05-07 | 前端开发 | 平台配置前端功能缺失识别与实现：完成 LLM 配置、Claw Code、平台配置入口的完整前端实现，包括 API 封装、页面组件、路由与权限配置 |
| 2026-05-07 | 部署修复 | nginx配置重复指令问题彻底解决：移除include模式，每个location显式配置所有proxy指令，避免proxy_buffering/proxy_read_timeout等重复错误 |
| 2026-05-07 | 开发修复 | Wiki Memex 对标优化 Phase 1-4 完成：RAW 文件展示、路由守卫、返回导航、页面列表一致性、文档数量、Wiki 统计、工具栏折叠、健康指示器、LLM 连通性检测 |
| 2026-05-05 | 开发规划 | 成果物文本自适应与导出能力建设规划：Pretext 文本自适应工具链 Phase 1-2 完成，规划 Phase 2.5（气泡布局优化）/ Phase 3.1（Canvas 报告渲染器）/ Phase 3.2（后端 PDF CJK）/ Phase 3.3（看板截图导出） |
| 2026-05-04 | 代码库扫描 | 内容层报告生成功能问题分析：发现核心实现完整但API路由未注册的关键问题 |
| 2026-05-04 | 代码库扫描 | Claw Code 实现审计：实际实现 vs wiki 分析的偏差分析。发现实现方向从 Rust CLI 集成偏移为 Python 原生内嵌，PolicyEngine/BranchLock 已实现但孤立 |
