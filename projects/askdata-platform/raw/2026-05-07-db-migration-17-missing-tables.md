# 数据库迁移补全 17 张缺失表 — 排查与修复记录

## 问题描述
部署过程显示仅创建 48 张表（含 alembic_version 和 4 个 LangGraph checkpoint 表），但 ORM 定义了 60 个数据库 artifact（58 个模型类 + 2 个关联表）。43 个业务表已存在，17 个表缺失。

## 缺失表清单
| 表名 | 模型类 | 所属模块 |
|------|--------|---------|
| t_domain_config | DomainConfig | Claw-Core |
| t_platform_registration | PlatformRegistration | Claw-Core |
| t_mcp_domain | MCPDomain | MCP |
| t_mcp_server | MCPServer | MCP |
| t_mcp_server_domain_binding | MCPServerDomainBinding | MCP |
| t_claw_code_session | ClawCodeSession | Claw-Core |
| t_claw_lane_event | ClawLaneEvent | Claw-Core |
| t_llm_module_config | LLMModuleConfig | LLM Config |
| t_llm_config_history | LLMConfigHistory | LLM Config |
| t_llm_provider | LlmProvider | LLM Config |
| t_wiki_folder | WikiFolder | Wiki |
| t_wiki_page | WikiPage | Wiki |
| t_wiki_raw_source | WikiRawSource | Wiki |
| t_wiki_log | WikiLog | Wiki |
| t_wiki_page_version | WikiPageVersion | Wiki |
| t_wiki_attachment | WikiAttachment | Wiki |
| t_knowledge_wiki_binding | KnowledgeWikiBinding | Wiki |

## 根因
当前部署走 LEGACY 路径（`RESET_ALL_LEGACY_MIGRATE=1`），复用已有 revision `80b9742e0f30_reset_all_migrate.py`。该 revision 创建于 2026-04-28，只包含前 43 张表。Claw-Code 集成的新模型（MCP、Wiki、LLM 配置）是在该 revision 之后添加到 ORM 的，但未生成新的迁移 revision。upgrade head 为 no-op，17 张新表从未被创建。

## 解决方案
按项目 ADR 政策：`修改 ORM → alembic revision --autogenerate → 审阅 → 提交`。

## 执行步骤

### 1. 验证当前状态
```bash
export PGSQL_DB_HOST="127.0.0.1"
export PGSQL_DB_PORT="5432"
export PGSQL_DB_USERNAME="postgres"
export PGSQL_DB_PASSWORD="<password>"
export STANDARD_DB_URL="postgresql://${PGSQL_DB_USERNAME}:${PGSQL_DB_PASSWORD}@${PGSQL_DB_HOST}:${PGSQL_DB_PORT}/postgres"

# alembic_version 应在 80b9742e0f30
psql "${STANDARD_DB_URL}" -c "SELECT version_num FROM public.alembic_version;"

# 业务表应为 43
psql "${STANDARD_DB_URL}" -t -c "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tablename NOT IN ('alembic_version','checkpoint_blobs','checkpoint_migrations','checkpoint_writes','checkpoints');"
```

### 2. 生成新 revision
```bash
cd /Users/aiassistant/Projects/MyProjects/free-style-report/storage/data_migration/alembic_data_migration
export DATABASE_URL="postgresql+asyncpg://${PGSQL_DB_USERNAME}:${PGSQL_DB_PASSWORD}@${PGSQL_DB_HOST}:${PGSQL_DB_PORT}/postgres"
export PYTHONPATH="/Users/aiassistant/Projects/MyProjects/free-style-report"

cp alembic_env_bak.py alembic/env.py
alembic revision --autogenerate -m "add_missing_17_claw_wiki_llm_tables"
```

### 3. 审阅 checklist
- [x] 17 个 `op.create_table()` 语句正确，表间 FK 依赖排序正确
- [x] 无多余 ALTER TABLE / DROP TABLE 操作
- [x] 排除 LangGraph checkpoint 表的 DROP（运行时管理，不由 Alembic 管理）
- [x] 保留 ADD COLUMN 操作（t_chain_template, t_datasource, t_external_resource_registration, t_knowledge, t_tag, t_workspace 的 ORM 后续变更）
- [x] 排除已有 FK 约束的无意义重建
- [x] JSONB 列使用 `postgresql.JSONB(astext_type=sa.Text())`，由于是 CREATE TABLE，无需 USING 子句
- [x] UniqueConstraint 命名正确（uq_mcp_server_domain, uq_llm_module_version, uq_kb_wiki_binding）
- [x] ClawLaneEvent.session_id FK 正确引用 t_claw_code_session.session_id（非 PK id）
- [x] downgrade() 包含 17 张表的 `op.drop_table()`，顺序与 upgrade 相反
- [x] 无重复建表

### 4. 应用与验证
```bash
alembic upgrade head
# 验证新 head
alembic current  # → 0a2119b5be45

# 验证 60 张业务表
psql "${STANDARD_DB_URL}" -t -c "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tablename NOT IN ('alembic_version','checkpoint_blobs','checkpoint_migrations','checkpoint_writes','checkpoints');"
# → 60

# 验证 17 张新表都存在
psql "${STANDARD_DB_URL}" -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('t_domain_config','t_platform_registration','t_mcp_domain','t_mcp_server','t_mcp_server_domain_binding','t_claw_code_session','t_claw_lane_event','t_llm_module_config','t_llm_config_history','t_llm_provider','t_wiki_folder','t_wiki_page','t_wiki_raw_source','t_wiki_log','t_wiki_page_version','t_wiki_attachment','t_knowledge_wiki_binding') ORDER BY tablename;"
# → 17 行
```

### 5. 提交
```bash
git add storage/data_migration/alembic_data_migration/alembic/versions/0a2119b5be45_add_missing_17_claw_wiki_llm_tables.py
git commit -m "migration: add 17 missing tables for Claw-Code integration"
```

## 关键文件
- 新 revision: `storage/data_migration/alembic_data_migration/alembic/versions/0a2119b5be45_add_missing_17_claw_wiki_llm_tables.py`
- 原始 revision: `storage/data_migration/alembic_data_migration/alembic/versions/80b9742e0f30_reset_all_migrate.py`
- ORM 定义: `core/models/db/db_initial_models.py`
- Alembic 环境: `storage/data_migration/alembic_data_migration/alembic_env_bak.py`

## 注意事项
- 绿场部署（ASKDATA_DB_INIT_MODE=greenfield）会自动 regenerated 包含全部 60 张表的 base revision，不需此修复
- 生产环境只能用 LEGACY 路径，依赖增量 revision
- LangGraph checkpoint 表由运行时创建和管理，Alembic 不应干预
