---
title: "LLM 调用统一收敛至 ScopeConfig → LLMConfig"
type: analysis
created: 2026-05-09
last_updated: 2026-05-09
source_count: 1
confidence: medium
status: active
tags:
  - llm
  - configuration
  - refactoring
  - unification
  - scope-config
  - central-config
sources:
  - llm-统一调用收敛至-central-config
---

# LLM 调用统一收敛至 ScopeConfig → LLMConfig

## 背景

项目中存在 4 个独立 LLM 配置系统，导致 LLM 调用没有集中走 `ScopeConfig` 入口 [^src-llm-统一调用收敛至-central-config]。

### 4 个独立配置系统

1. **`configs/llms_config.LLMConfig`**（中央配置）— 读取 `LLM_PARAMS_CONFIG` JSON env var，通过 `LLMParamsUtils` 解析 provider/base_url/api_key
2. **`utils/llms/llm.py`**（独立配置）— 读取 `conf.yaml` + `{TYPE}_MODEL__{KEY}` env var 覆盖，10 个 dashboard collab 调用点全走此路径 [^src-llm-统一调用收敛至-central-config]
3. **Report Agent 4 份 `LLMConfig` dataclass**（独立配置）— 各自读取本地 `llm_config.yaml` + env var，仅用于 internal/私有化部署模式 [^src-llm-统一调用收敛至-central-config]
4. **`utils/get_peers_utils.py`**（裸调用）— 直接 `openai.OpenAI(api_key=..., base_url=...).chat.completions.create()`，参数由调用方传入 [^src-llm-统一调用收敛至-central-config]

### 3 个断掉的调用者

- `core/claw/llm_client.py` 调用 `LLMConfig.get_llm()` — 方法不存在 [^src-llm-统一调用收敛至-central-config]
- `core/mcp/handlers/data_analysis_handlers.py` 调用 `get_llm("analysis")` — "analysis" 不是有效 LLMType [^src-llm-统一调用收敛至-central-config]
- `core/mcp/handlers/config_handlers.py` 调用 `get_default_model()` / `get_model_name()` — 方法不存在 [^src-llm-统一调用收敛至-central-config]

## 修复内容

### Phase 1：修复中央 API

- `utils/llm_params_utils.get_llm_params()` 不再静默降级到 `gpt-3.5-turbo`/`sk-default-key`，改为返回 `(None, None, None)` + warning [^src-llm-统一调用收敛至-central-config]
- 新增 `_apply_env_overrides()` — 支持 `{MODEL_NAME}__base_url` / `{MODEL_NAME}__api_key` 覆盖 [^src-llm-统一调用收敛至-central-config]
- 新增 `_apply_type_env_overrides()` — 兼容旧版 `BASIC_MODEL__api_key` 类型级 env var [^src-llm-统一调用收敛至-central-config]
- `LLMConfig` 新增 `get_llm()`、`get_default_model()`、`get_model_name()`、`get_configured_llm_models()` 方法 [^src-llm-统一调用收敛至-central-config]

### Phase 2：迁移 `utils/llms/llm.py` 及调用者

- `utils/llms/llm.py` 内部改为委托到 `configs.llms_config.LLMConfig`，保持函数签名和缓存行为不变 [^src-llm-统一调用收敛至-central-config]
- 迁移 10 个 dashboard collab 调用点、2 个 API config 端点、1 个测试 mock [^src-llm-统一调用收敛至-central-config]

### Phase 3：整合 Report Agent LLMConfig

- 新建 `resources/agents/report_agents/_shared_config.py` 共享 `ReportLLMConfig` 基类 [^src-llm-统一调用收敛至-central-config]
- 4 个 `config.py` 改为 `class LLMConfig(ReportLLMConfig): _CONFIG_DIR = ...`，消除 dataclass 重复 [^src-llm-统一调用收敛至-central-config]

### Phase 4：修复 `get_peers_utils.py`

- 当参数未传入时自动从 `LLMParamsUtils` 获取，保持向后兼容 [^src-llm-统一调用收敛至-central-config]

### Phase 5：修复断掉的调用者

- `data_analysis_handlers.py`: `get_llm("analysis")` → `get_llm_by_type("basic")` [^src-llm-统一调用收敛至-central-config]
- 其他断掉的方法调用由 Phase 1 新增方法自动修复 [^src-llm-统一调用收敛至-central-config]

## 关键决策

1. **不删除 `utils/llms/llm.py`** — 改为委托到中央配置，保持 API 兼容（10+ 调用点） [^src-llm-统一调用收敛至-central-config]
2. **env var 覆盖纳入中央配置** — 采纳 `utils/llms/llm.py` 的 env var 模式 [^src-llm-统一调用收敛至-central-config]
3. **ReportLLMConfig 采用继承** — 4 个 agent 各自定义 `_CONFIG_DIR`，类方法自动继承 [^src-llm-统一调用收敛至-central-config]
