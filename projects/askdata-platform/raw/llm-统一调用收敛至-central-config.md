# LLM 调用统一收敛至 ScopeConfig → LLMConfig

> Date: 2026-05-09
> Branch: backup/dev_bruce_askdata

## 问题范围

项目中存在 **4 个独立 LLM 配置系统** 和 **3 个断掉的调用者**：

| # | 问题 | 影响文件数 |
|---|------|-----------|
| 1 | `utils/llms/llm.py` 独立配置系统（conf.yaml + env var） | 1 模块 + 10 调用点 |
| 2 | Report agent 4 份重复 `LLMConfig` dataclass | 4 config.py + 4 agent_factory.py |
| 3 | `get_peers_utils.py` 裸 `openai.OpenAI()` 调用 | 1 文件 |
| 4 | `LLMParamsUtils.get_llm_params()` 静默降级到 `sk-default-key` | 1 文件 |
| 5 | `LLMClient`/handlers 调了不存在的方法 | 3 文件 |

## 修复方案与变更

### Phase 1：修复中央 API

**`utils/llm_params_utils.py`**：
- `get_llm_params()` 不再静默降级，改为返回 `(None, None, None)` + warning
- 新增 `_apply_env_overrides()` — 支持 `{MODEL_NAME}__base_url` / `{MODEL_NAME}__api_key` 覆盖
- 新增 `_apply_type_env_overrides()` — 兼容旧版 `BASIC_MODEL__api_key` 类型级 env var

**`configs/llms_config.py`**：
- 新增 `get_llm(llm_type)` — 代理 `get_llm_by_type`
- 新增 `get_default_model()` — 返回 `LLM_DETAIL_MAP["basic"]`
- 新增 `get_model_name(model_type)` — 按类型查模型名
- 新增 `get_configured_llm_models()` — API 端点使用，按类型分组

### Phase 2：迁移 `utils/llms/llm.py` 及所有调用者

**`utils/llms/llm.py`**：内部代理到 `configs.llms_config.LLMConfig`，保持同样的函数签名和缓存。

**迁移文件**：
- `core/helpers/askdata_flow/dashboard_collab_llm.py` — 5 处
- `core/helpers/askdata_flow/dashboard_collab_pipeline.py` — 1 处
- `core/helpers/askdata_flow/dashboard_theme_llm_select.py` — 1 处
- `graphs/sub_graphs/graphs_components/dashboard_collab_components.py` — 2 处
- `core/server/routers/config_router.py` — 1 处
- `core/server/app.py` — 1 处
- `tests/askdata/test_dashboard_collab_llm_augmentation.py` — mock target 更新

### Phase 3：整合 Report Agent LLMConfig（4 合 1）

**新建** `resources/agents/report_agents/_shared_config.py`：共享 `ReportLLMConfig` 基类 + `load_config_file()` 工具。

**4 个 config.py** 去掉本地 `LLMConfig` dataclass，改为 `class LLMConfig(ReportLLMConfig): _CONFIG_DIR = ...`。每个 agent_factory.py 无需改动（类方法 + 子类继承自动生效）。

### Phase 4：修复 `get_peers_utils.py` 裸 API 调用

当 `api_key`/`base_url`/`model_name` 均未传入时，从 `LLMParamsUtils` 自动获取。

### Phase 5：修复断掉的调用者

- `core/mcp/handlers/data_analysis_handlers.py`: `get_llm("analysis")` → `get_llm_by_type("basic")`
- `core/claw/llm_client.py` + `core/mcp/handlers/config_handlers.py`: 由 Phase 1 新增方法自动修复

## 关键决策

1. **不删除 `utils/llms/llm.py`** — 改为委托到中央配置，保持 API 兼容（10+ 调用点）
2. **env var 覆盖纳入中央配置** — 采纳 `utils/llms/llm.py` 的 env var 模式，支持 `{MODEL_NAME}__base_url` / `{MODEL_NAME}__api_key`
3. **ReportLLMConfig 采用继承而非组合** — 4 个 agent 各自定义 `_CONFIG_DIR`，类方法自动继承

## 验证

- 语法检查通过：10 个修改文件 0 FAILED
- 无遗留 `utils.llms.llm` import（除测试 mock 已更新）
- 无遗留 `.get_llm("analysis")` 调用