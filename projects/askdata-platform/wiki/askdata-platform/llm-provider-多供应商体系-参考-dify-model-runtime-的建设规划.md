---
title: "LLM Provider 多供应商体系 — 参考 Dify Model Runtime 的建设规划"
type: planning
created: 2026-05-04
last_updated: 2026-05-04
source_count: 1
confidence: medium
status: active
tags:
  - llm-provider
  - dify-reference
  - architecture
  - planned
  - todo
sources:
  - src-dify-model-runtime-architecture
---

## 概述

当前 AskData (Free-Style-Report) 的 LLM 调用体系基于 `LLMParamsUtils` + `LiteLLMFunctions`，本质是单层代理。为实现多供应商、多对接方法的 LLM 调用生态，需参考 Dify Model Runtime 架构进行建设。

## 现状与差距

| 维度 | 当前方案 | 目标（参考 Dify） |
|------|---------|-----------------|
| 供应商支持 | 3 个（tongyi/ollama/openai_api_compatible），全部走 LiteLLM | 插件化 Provider 注册，每个独立实现 |
| 凭据管理 | 单组环境变量，全系统共享 | 声明式 CredentialSchema，支持多租户 |
| 模型类型 | 仅 LLM | LLM + Embedding + Rerank + TTS + Moderation |
| 模型路由 | 按名称精确匹配，无回退 | 预定义 model list + 可自定义 |
| Provider 抽象 | 无 | BaseProvider → LargeLanguageModel 等 |
| 热更新 | 仅 Claw 模块 domain_models | 完整 DB 驱动配置热更新 |

## 参考来源

Dify Model Runtime 完整架构分析见 [Dify Model Runtime Architecture](../../raw/dify-model-runtime-architecture.md)。

## 待办规划

### Phase 1: Provider 抽象层
- [ ] 定义 `BaseProvider` 基类（provider_name、model_type、validate_credentials、get_model_instance）
- [ ] 实现 `OpenAICompatibleProvider`（覆盖当前 tongyi / openai_api_compatible）
- [ ] 实现 `OllamaProvider`
- [ ] 建立 `ProviderRegistry` 注册机制

### Phase 2: ModelRouter
- [ ] 实现按 (model_type, domain_code) → provider + model 的路由
- [ ] 支持多配置源（env 优先 → DB 回退）
- [ ] 兼容现有 `LLM_DETAIL_MAP` 回退行为

### Phase 3: CredentialStore
- [ ] 定义 `BaseCredentialSource` 接口
- [ ] 实现 `EnvCredentialSource`（读取 LLM_PARAMS_CONFIG）
- [ ] 实现 `DBCredentialSource`（新建凭据表，支持多租户）
- [ ] 凭据热更新

### Phase 4: ScopeConfig 集成
- [ ] `ScopeConfig.get_llm()` 通过 ModelRouter 获取 Provider 实例
- [ ] `ScopeConfig.chat()` 委托给 domain-aware 的 Provider 调用
- [ ] 保留向后兼容，逐步迁移现有 `LLMConfig()` 直调

### Phase 5: Admin 管理界面
- [ ] Provider 注册与配置页面
- [ ] 凭据管理 UI
- [ ] 模型路由规则配置
- [ ] 调用监控与用量统计

