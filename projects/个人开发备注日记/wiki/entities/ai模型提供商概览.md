---
title: "AI模型提供商概览"
type: entity
created: 2026-04-30
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags: []
---

# AI模型提供商概览

> 本页面汇总所有可用的 AI 模型提供商及其配置要点

## 提供商列表

### OpenAI
- **模型**: GPT-4o, GPT-4o-mini, o3-mini
- **API Base**: https://api.openai.com/v1
- **认证**: Bearer Token
- **用途**: 通用对话、代码生成、结构化输出

### Anthropic
- **模型**: Claude Sonnet 4 (20250514)
- **API Base**: https://api.anthropic.com
- **认证**: Bearer Token
- **用途**: 复杂推理、代码审查、长上下文

### Google
- **模型**: Gemini 2.5 Pro
- **API Base**: https://generativelanguage.googleapis.com
- **认证**: API Key
- **用途**: 多模态、长上下文分析

### DeepSeek
- **模型**: DeepSeek Chat, DeepSeek Reasoner
- **API Base**: https://api.deepseek.com
- **认证**: Bearer Token
- **用途**: 高性价比对话、推理任务

### 硅基流动 (SiliconFlow)
- **模型**: Qwen3-235B-A22B, GLM-4-Plus, Hunyuan-56B-A32B
- **API Base**: https://api.siliconflow.cn/v1
- **认证**: Bearer Token
- **用途**: 大模型推理、中文优化

### 智谱 AI (Zhipu)
- **模型**: GLM-4-Plus, GLM-4-FlashX
- **API Base**: https://open.bigmodel.cn
- **认证**: API Key
- **用途**: 中文NLP、代码生成

### 腾讯混元 (Hunyuan)
- **模型**: hunyuan-56b-a32b
- **API Base**: https://api.hunyuan.tencent.com/v1
- **认证**: Bearer Token
- **用途**: 中文对话、企业级应用

## 选型建议

- 通用对话 → Claude Sonnet 4 (推理能力强)
- 代码生成 → GPT-4o (代码质量高)
- 中文NLP → GLM-4-Plus (中文优化好)
- 高性价比 → DeepSeek Chat (成本低)
- 多模态 → Gemini 2.5 Pro (多模态能力强)
- 大模型推理 → Qwen3-235B (参数量大)

## 配置要点

- 所有提供商均使用 REST API
- 大部分支持 OpenAI 兼容格式
- 注意 rate limiting 和 quota
- 生产环境建议配置 fallback 机制

