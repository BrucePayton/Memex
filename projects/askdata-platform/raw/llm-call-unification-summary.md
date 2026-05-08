# LLM 调用统一入口重构：集中走 ScopeConfig → LLMConfig

## 背景

Free-Style-Report / AskData 平台项目中，LLM 调用存在多个独立的配置系统和直接的 API 调用，
没有集中通过 `configs/llms_config.py` 完成统一调用。

## 独立配置系统

| 系统 | 配置来源 | 使用者 |
|------|----------|--------|
| `configs/llms_config.LLMConfig` (主要) | `LLM_PARAMS_CONFIG` JSON env var | Graph helpers, agents |
| `utils/llms/llm.py` (独立) | `conf.yaml` + env vars (`BASIC_MODEL__api_key`) | Dashboard collab (10 call sites) |
| Report agent `LLMConfig` dataclass x4 (重复) | 本地 `llm_config.yaml` + env var | 4 个 report agent factories |
| `utils/get_peers_utils.py` (裸调用) | Caller-passed raw strings | 金融分析工具 |

## 发现的问题

1. `utils/llm_params_utils.py` 当 `LLM_PARAMS_CONFIG` 未设置时，静默降级返回 `gpt-3.5-turbo`/`sk-default-key`
2. `LLMConfig` 缺少 4 个方法导致调用者崩溃：
   - `get_llm()` — `LLMClient` 调用
   - `get_default_model()` — `config_handlers.py` 调用
   - `get_model_name()` — `config_handlers.py` 调用
   - `get_configured_llm_models()` — API endpoint 调用
3. `data_analysis_handlers.py` 传入 `"analysis"` 不是有效的 `LLMType`
4. 4 个 report agent `config.py` 各维护一份完全相同的 `LLMConfig` dataclass

## 修复方案 (5 个 Phase)

### Phase 1: 修复中央 API
- 移除 `get_llm_params()` 的静默降级，改为 `(None, None, None)` + warning
- 补齐 `LLMConfig` 缺失方法
- 向 `LLMParamsUtils` 添加 env var 覆盖支持（`{MODEL_NAME}__api_key`, `{MODEL_NAME}__base_url`）

### Phase 2: 迁移 `utils/llms/llm.py` 调用者
- `utils/llms/llm.py` 代理到中央配置 `LLMConfig()`
- 10 个 dashboard collab 调用点 + 2 个 API 端点 + test mocks 全部迁移

### Phase 3: 整合 report agent LLMConfig
- 创建 `_shared_config.py` 共享 `ReportLLMConfig` 基类
- 4 个 `config.py` 继承共享基类，各自指定 `_CONFIG_DIR`

### Phase 4: 修复裸 API 调用
- `get_peers_utils.py` 添加 `LLMParamsUtils` fallback

### Phase 5: 修复断掉的调用者
- `data_analysis_handlers.py`: `get_llm("analysis")` → `get_llm_by_type("basic")`
- `claw/llm_client.py`、`config_handlers.py` 由 Phase 1 自动修复

## 关键文件变更

- `utils/llm_params_utils.py` — 静默降级修复 + env var 覆盖
- `configs/llms_config.py` — 补齐 4 个方法 + 统一入口
- `utils/llms/llm.py` — 代理重构
- `core/helpers/askdata_flow/dashboard_collab_*.py` (4 files) — 迁移调用
- `graphs/sub_graphs/graphs_components/dashboard_collab_components.py` — 迁移调用
- `core/server/routers/config_router.py`, `core/server/app.py` — 迁移 API 端点
- `core/mcp/handlers/data_analysis_handlers.py` — 修复参数
- `core/mcp/handlers/config_handlers.py` — 自动修复
- `core/claw/llm_client.py` — 自动修复
- `utils/get_peers_utils.py` — 添加 fallback
- `resources/agents/report_agents/_shared_config.py` (new) — 共享基类
- `resources/agents/report_agents/*/config.py` (4 files) — 继承共享基类
- `tests/askdata/test_dashboard_collab_llm_augmentation.py` — 更新 mock

## 推荐调用模式

```python
# 统一入口 (推荐)
from configs.scope_config import ScopeConfig
llm = ScopeConfig("analysis").llm_config.get_llm_by_type("basic")

# 简短入口 (无 scope 上下文时)
from configs.llms_config import LLMConfig
llm = LLMConfig().get_llm_by_type("basic")
```

## 环境变量覆盖

支持模型级覆盖：`{MODEL_NAME}__base_url`, `{MODEL_NAME}__api_key`
兼容旧式类型级覆盖：`BASIC_MODEL__base_url`, `BASIC_MODEL__api_key`
