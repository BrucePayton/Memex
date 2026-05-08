---
title: "LLM 调用统一入口重构 — ScopeConfig → LLMConfig"
type: technique
created: 2026-05-09
last_updated: 2026-05-09
source_count: 1
confidence: medium
status: active
tags:
  - llm-config
  - refactoring
  - architecture
  - unified-config
  - 2026-05
  - askdata-platform
sources:
  - src-llm-call-unification-summary
---

## 背景

项目中存在 4 个独立的 LLM 配置系统和多处直接调用 LLM 的代码，没有集中走 `ScopeConfig` → `configs/llms_config.py` 的统一入口[^src-llm-call-unification-summary]。

## 独立配置系统

| 系统 | 配置来源 | 调用者数量 |
|------|----------|-----------|
| `configs.llms_config.LLMConfig`（主要） | `LLM_PARAMS_CONFIG` JSON env var | 正常使用 |
| `utils/llms/llm.py`（独立） | `conf.yaml` + env var 覆盖 | 10 个调用点（dashboard collab） |
| Report agent `LLMConfig` x4（重复） | 本地 `llm_config.yaml` | 4 个 agent factories |
| `utils/get_peers_utils.py`（裸调用） | 调用者传入参数 | 1 处 |

## 发现的问题

1. **静默降级** — `LLMParamsUtils.get_llm_params()` 在配置缺失时返回 `gpt-3.5-turbo`/`sk-default-key`，掩盖配置错误
2. **缺失方法** — `LLMConfig` 缺少 `get_llm()`、`get_default_model()`、`get_model_name()`、`get_configured_llm_models()`，导致 `LLMClient`、`config_handlers.py` 等调用者崩溃
3. **无效参数** — `data_analysis_handlers.py` 传入 `"analysis"`，不是有效的 `LLMType`
4. **代码重复** — 4 个 report agent `config.py` 各维护一份完全相同的 `LLMConfig` dataclass

## 修复方案（5 Phase）

### Phase 1: 修复中央 API
- 移除 `get_llm_params()` 的静默降级配置，改为返回 `(None, None, None)` + warning log
- 补齐 `LLMConfig` 缺失方法
- 向 `LLMParamsUtils` 添加 env var 覆盖支持（`{MODEL_NAME}__api_key`、`{MODEL_NAME}__base_url`），同时保留旧式类型级覆盖兼容

### Phase 2: 迁移 `utils/llms/llm.py` 及调用者
- 该模块的 `get_llm_by_type()` 和 `get_configured_llm_models()` 内部委托到 `LLMConfig()`
- 10 个 dashboard collab 调用点全部切换到 `LLMConfig().get_llm_by_type("basic")`
- 2 个 API 端点（`config_router.py`、`app.py`）切换到 `LLMConfig.get_configured_llm_models()`
- 测试 mock 目标同步更新

### Phase 3: 整合 report agent LLMConfig
- 创建 `_shared_config.py` 共享 `ReportLLMConfig` 基类
- 4 个 `config.py` 的 `LLMConfig` 改为继承共享基类，各自通过 `_CONFIG_DIR` 指定配置文件路径
- agent_factory.py 代码无需改动，继承的类方法自动使用子类的 `_CONFIG_DIR`

### Phase 4: 修复裸 API 调用
- `get_peers_utils.py` 在无显式凭证时自动通过 `LLMParamsUtils` 获取参数

### Phase 5: 修复断掉的调用者
- `data_analysis_handlers.py`: `get_llm("analysis")` → `get_llm_by_type("basic")`
- `claw/llm_client.py`、`config_handlers.py` 由 Phase 1 自动修复

## 推荐调用模式

```python
# 统一入口（推荐）
from configs.scope_config import ScopeConfig
llm = ScopeConfig("analysis").llm_config.get_llm_by_type("basic")

# 简短入口（无 scope 上下文时）
from configs.llms_config import LLMConfig
llm = LLMConfig().get_llm_by_type("basic")
```

## 环境变量覆盖

支持模型级覆盖（新标准）：
- `QWEN_FLASH__base_url`
- `QWEN_FLASH__api_key`

兼容旧式类型级覆盖：
- `BASIC_MODEL__base_url`
- `BASIC_MODEL__api_key`

## 涉及文件

共修改 16 个文件，新建 1 个文件：

- `utils/llm_params_utils.py` — 静默降级修复 + env var 覆盖
- `configs/llms_config.py` — 补齐方法 + 统一入口
- `utils/llms/llm.py` — 代理到中央配置
- `core/helpers/askdata_flow/dashboard_collab_pipeline.py`、`dashboard_collab_llm.py`、`dashboard_theme_llm_select.py` — 迁移调用
- `graphs/sub_graphs/graphs_components/dashboard_collab_components.py` — 迁移调用
- `core/server/routers/config_router.py`、`core/server/app.py` — 迁移 API 端点
- `core/mcp/handlers/data_analysis_handlers.py` — 修复参数
- `core/claw/llm_client.py` — 自动修复（方法补齐）
- `core/mcp/handlers/config_handlers.py` — 自动修复（方法补齐）
- `utils/get_peers_utils.py` — 添加 LLMConfig fallback
- `resources/agents/report_agents/_shared_config.py` — 新建文件，共享基类
- `resources/agents/report_agents/*/config.py`（4 files）— 继承共享基类
- `tests/askdata/test_dashboard_collab_llm_augmentation.py` — 更新 mock

