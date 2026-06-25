# AskData Platform — Activity Log

## [2026-05-07] feat | 平台配置模块完整实现

**作者**: Claude Opus

**变更内容**:

### 后端 API
- 新建 `core/helpers/llm_config_manager.py` - LLM 配置验证管理器
- 新建 `core/modules/config/views/provider_views.py` - Provider 管理 API
- 新建 `core/modules/config/views/domain_config_views.py` - Domain 配置 API
- 修改 `core/modules/config/views/llm_config_views.py` - 修复历史版本显示
- 修改 `core/models/db/db_initial_models.py` - LlmProvider 添加 api_protocol 字段
- 修改 `core/server/app.py` - 注册配置模块路由

### 前端界面
- 新建 `web/src/features/domain-config/pages/DomainConfigPage.tsx` - Domain 配置页面
- 修改 `web/src/features/llm-config/pages/LlmConfigPage.tsx` - 添加 API 协议选择
- 修改 `web/src/features/platform-config/pages/PlatformConfigPage.tsx` - 启用 Domain 配置
- 修改 `web/src/app/routes/index.tsx` - 添加 Domain 配置路由

### 初始化脚本
- 新建 `deployments/deployment_local/init-scripts/05-init-domains.sql` - Domain 初始化脚本
- 确认 `03-init-tags.sql` 已有完整标签初始化

**关联文档**:
- [平台配置模块完整实现记录 - LLM配置、Provider管理、Domain配置、前端集成](./askdata-platform/平台配置模块完整实现记录-llm配置provider管理domain配置前端集成.md)
- [平台配置管理多问题修复 - LLM配置、Provider管理、Claw配置、Tag初始化](./askdata-platform/平台配置管理多问题修复-llm配置provider管理claw配置tag初始化.md)

---

## [2026-05-04] init | 行业标准
Project created.
