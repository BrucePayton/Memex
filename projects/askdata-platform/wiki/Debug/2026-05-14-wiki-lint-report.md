---
title: "2026-05-14 Wiki Lint 审计报告"
type: analysis
created: 2026-05-14
last_updated: 2026-05-14
source_count: 0
confidence: high
status: active
tags:
  - wiki
  - lint
  - audit
  - maintenance
---

# Wiki Lint 审计报告 — 2026-05-14

## Critical (must fix)

- [ ] **dsc-platform-项目概述.md** — 完全缺少 frontmatter（无 `---` 分隔符），缺失 title/type/created/last_updated/source_count/confidence/status。需补充标准 frontmatter 块。
- [ ] **askdata-核心模块.md** — 完全缺少 frontmatter（无 `---` 分隔符），缺失所有元数据字段。需补充标准 frontmatter 块。
- [ ] **Domain-Config功能规范.md** — frontmatter 格式错误：使用 `[Frontmatter]` 而非标准 `---` 分隔符；type 值为 `"architecture"` 不在允许的枚举值中（应为 concept/technique/entity/source-summary/analysis）；sources 字段使用自由文本而非有效 source slug；created/last_updated 日期为 2025-05-04（未来日期，应为 2026）。需重写 frontmatter 为合规格式。
- [ ] **askdata-platform/askdata-组织概念分析与-projects-概念适配.slides.md** — frontmatter 为 Marp 专属格式（marp/theme/paginate/class），缺少标准 wiki frontmatter 字段（title/type/created/last_updated/source_count/confidence/status）。需补充标准字段或移至非 wiki 目录。
- [ ] **外部资源管理功能设计与实现.md** — frontmatter 使用非标准字段 `updated:` 替代 `last_updated:`，使用 `sources: []` 替代 `source_count:`。需修正字段名。
- [ ] **askdata的当前项目总览.md** — 同上，使用 `updated:` 替代 `last_updated:`，使用 `sources: []` 替代 `source_count:`。需修正字段名。
- [ ] **历史会话加载性能优化.md** (根目录) — frontmatter 中声明 `source_count: 1` 且 `sources: [src-askdata-chat-optimization]`，但正文中无任何 `[^src-*]` 引用脚注。需在正文中添加对应 inline citations 或修正 source_count 为 0。此外该文件与 `askdata-platform/性能优化/历史会话加载性能优化.md` 内容重复，应合并或删除。
- [ ] **历史会话编排阶段骨扇屏完全不渲染修复.md** — type 为 `source-summary`，confidence 为 `high`，但 `source_count: 0` 且无 inline citations。source-summary 类型必须有至少一个 source 引用。需补充 source 或将 type 改为 `analysis`。

## Warning (should fix)

### Citation 覆盖率不足（source_count: 0 但有事实性主张）

- [ ] **free-style-report-项目总览.md** — `source_count: 0`，全文无 citations。包含大量架构/功能描述（"平台由 AskData 框架、Free-Style-Report 模块、外部资源管理等组成"），需补充至少 2 个来源以支撑 generalization。
- [ ] **askdata-架构设计.md** — `source_count: 0`，全文无 citations。描述 LangGraph 工作流、节点设计、SSE 推送等具体架构决策，需补充来源。
- [ ] **askdata-platform/wiki-知识库绑定-404-故障复盘.md** — `source_count: 0`，详细描述 bug 根因、修复方案、涉及文件行号。需补充对应 raw source。
- [ ] **askdata-platform/Debug/平台多问题修复与功能增强路由通知模板外部资源claw.md** — `source_count: 0`，详述多个 bug 修复过程。需补充来源。
- [ ] **askdata-platform/acr-amd64-镜像迁移与统一版本标记经验总结.md** — `source_count: 0`，包含具体部署经验和命令。需补充来源。
- [ ] **askdata-platform/wiki-知识库功能完整集成.md** — `source_count: 0`（根据前文检查），详细描述 5 阶段集成过程。需补充对应 raw source。
- [ ] **askdata-platform/llm-调用统一入口重构-scopeconfig-llmconfig.md** — `source_count: 0`，描述具体代码重构细节。需补充来源。
- [ ] **askdata-platform/领域模板管理.md** — `source_count: 0`，描述领域模板功能。需补充来源。
- [ ] **askdata-platform/Debug/wiki-mcp-handler-bug-修复与-memex-对标.md** — `source_count: 0`，描述 bug 修复。需补充来源。
- [ ] **askdata-platform/Debug/wiki-知识库-memex-对标优化-phase-1-4-实现记录.md** — `source_count: 0`，描述 4 阶段优化实现。需补充来源。
- [ ] **外部资源管理功能实现进度与现状分析.md** — `source_count: 0`，功能分析类页面应有来源支撑。
- [ ] **askdata-platform/claw-code-与-fsr-集成现状-对照-wiki-分析的偏差分析.md** — `source_count: 0`，分析类页面无来源。
- [ ] **内容层报告生成功能问题分析.md** — `source_count: 0`，问题分析类页面无来源。
- [ ] **askdata-platform/claw-code-作为-askdata-原生服务集成分析.md** — `source_count: 0`，分析类页面无来源。
- [ ] **askdata-platform/claw-code-作为-askdata-驾驭框架可行性分析.md** — `source_count: 0`，分析类页面无来源。
- [ ] **askdata-platform/memex-cli-对接模式分析与-askdata-借鉴.md** — `source_count: 0`，分析类页面无来源。
- [ ] **askdata-platform/askdata-开发工作流现状分析.md** — `source_count: 0`，分析类页面无来源。

### Tags 为空数组

- [ ] **askdata-platform/领域模板管理.md** — `tags: []`，应添加相关标签。
- [ ] **askdata-platform/acr-amd64-镜像迁移与统一版本标记经验总结.md** — `tags: []`，应添加相关标签。
- [ ] **askdata-platform/Debug/nginx配置重复指令导致启动失败问题排查.md** — `tags: []`，应添加相关标签。
- [ ] **askdata-platform/Debug/后端启动失败pydantic-field-未导入-yaml-未导入导致-nameerror-修复.md** — `tags: []`，应添加相关标签。

### source_count 与实际引用不一致

- [ ] **askdata-platform/wiki-知识库功能完整集成.md** — frontmatter 中 `source_count` 需与实际 `[^src-*]` 脚注数量核对一致。
- [ ] **平台配置管理多问题修复-llm配置provider管理claw配置tag初始化.md** — `source_count: 0` 但正文引用了具体文件路径和代码（如 `core/modules/config/views/llm_config_views.py:203-212`），应补充来源或添加 `(待提交)` 标注。

## Info (nice to have)

### 重复/相似页面

- [ ] **历史会话加载性能优化.md** (根目录) vs **askdata-platform/性能优化/历史会话加载性能优化.md** — 两份独立文档描述同一主题，index.md 只链接了后者。建议合并到 askdata-platform/ 子目录下并删除根目录版本。
- [ ] **askdata-platform/llm-调用统一入口重构-scopeconfig-llmconfig.md** vs **askdata-platform/llm-调用统一收敛至-scopeconfig-llmconfig.md** — 标题相似，疑似同一主题的两个版本。index.md 只链接了后者（作为"LLM 调用统一收敛"）。建议合并。
- [ ] **askdata-platform/askdata-组织概念分析与-projects-概念适配.md** vs **askdata-platform/askdata-组织概念分析与-projects-概念适配.slides.md** — slides 版本为 Marp 演示文稿，与主文档内容重叠。考虑将 slides 移至 `raw/assets/` 或单独目录。

### 孤立页面（orphan — 无入站 wikilink）

以下页面在 index.md 中无入口，或未被其他页面引用：

- [ ] **askdata-platform/askdata-组织概念分析与-projects-概念适配.slides.md** — Marp 幻灯片，不在 index.md 中。
- [ ] **DSC Platform 子目录下多个页面** — `DSC Platform/` 目录下 10 个页面（系统架构设计、agent-flow、knowledge-mgt、vectors-mgt、API 总览、部署指南、开发指南、知识库首页、FAQ、双向集成配置指南）均在 index.md 中只有 `dsc-platform-项目概述.md` 一个入口，子页面缺乏从根目录的直接引用。建议在 index.md 中为 DSC Platform 添加子目录索引。
- [ ] **askdata-platform/Wiki Dashboard/wiki-dashboard-对齐-canvas-知识图谱渲染与-phase-3-视图实现.md** — 未在 index.md 中注册。
- [ ] **平台配置管理多问题修复-llm配置provider管理claw配置tag初始化.md** — 未在 index.md 中注册。
- [ ] **Debug/前端构建失败-jsx-孤儿闭合标签导致esbuild解析错误.md** — 未在 index.md 中注册。
- [ ] **askdata-platform/Debug/前端构建失败-notificationbell-html实体编码问题排查.md** — 未在 index.md 中注册。
- [ ] **askdata-platform/llm-调用统一入口重构-scopeconfig-llmconfig.md** — 未在 index.md 中注册（与另一版本重复）。

### TODO 占位链接

- [ ] **历史会话加载性能优化.md** (根目录) 第 177-179 行 — 包含 `[[todo]]` 占位链接（"Askdata Platform 架构概述"、"前端性能优化指南"、"流式对话实现原理"），应替换为实际页面引用或移除。

### 无 confidence/status 字段

- 多个页面缺少 `confidence` 和 `status` 字段，虽然 CLAUDE.md 未标记为必填，但建议补齐以保持一致性。
