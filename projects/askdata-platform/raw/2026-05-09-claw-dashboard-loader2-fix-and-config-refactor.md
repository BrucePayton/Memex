# Claw Code 控制面板 Loader2 报错修复与配置体系重构

**日期**: 2026-05-09
**分支**: backup/dev_bruce_askdata
**提交**: 189ae2fd

## 问题描述

访问 Claw Code 管理面板时页面白屏，报错 "Loader2 is not defined"。

## 根因分析

### 直接原因
`ClawDashboardPage.tsx` 第 3 行 `lucide-react` 导入遗漏了 `Loader2`，但第 547、552 行使用了 `<Loader2>` 组件。React.lazy 加载该组件时立即抛出运行时异常。

### 深层问题
配置面板（Config tab）要求手动填 `ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_MODEL` 保存到 `.claw.json`，与项目现有 LLM 调用体系完全脱节。当参数为空时测试连接直接报错。

## 解决方案

### 1. 修复 Loader2 导入
`ClawDashboardPage.tsx` line 3 补充 `Loader2`。

### 2. 配置面板与项目 LLM 系统打通

**修改前**: 手动填 ANTHROPIC_* 参数 → 保存到 `.claw.json` → 手动拼 httpx 测试连接

**修改后**: 下拉选择 LLM 类型（basic/reasoning/vision）→ 保存到 `.claw.json` → 使用 `LLMConfig.create_chatopenai()` 测试连接

### 修改文件清单

| 文件 | 变更 |
|---|---|
| `web/src/features/claw/pages/ClawDashboardPage.tsx` | Loader2 导入 + 配置面板 UI 改造 |
| `core/modules/claw/helper.py` | `get_config`/`save_config`/`test_connection` 适配统一 LLM，新增 `get_available_models` |
| `core/modules/claw/views/claw_views.py` | `save_config` 接收 `llm_type`，新增 `GET /api/claw/config/models` |
| `core/modules/claw/request_model.py` | `ClawConfigUpdateRequest` 改为 `llm_type`，新增 `ClawLlmModelsResponse` |
| `web/src/apis/claw/claw.api.ts` | `saveConfig` 参数适配，新增 `getAvailableModels()` |
| `web/src/apis/claw/types.ts` | `ClawConfig` 增加 `llm_type` 字段 |

### 关键经验

1. **React.lazy 下遗漏组件导入会导致整页白屏**，而非单组件降级。Loader2 来自 lucide-react，需确保所有使用的图标都已导入。
2. **Docker 部署场景下，后端服务之间应使用内部服务名而非 localhost 通信**。此问题在之前的 dsc_views.py 修复中已处理过。
3. **Claw 配置不应独立维护 ANTHROPIC_* 参数**，应复用项目的 `configs/llms_config.py` + `utils/llm_params_utils.py` 统一体系。
4. **LLMConfig.get_configured_llm_models()** 可获取项目已配置的模型列表（按类型分组），可供其他模块复用。
