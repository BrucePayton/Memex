---
title: "Claw Code快捷启动"
type: "technique"
created: "2026-04-30"
last_updated: "2026-05-02"
source_count: 0
confidence: medium
status: active
tags:
  - claw-code
  - provider-routing
---
# Claw Code快捷启动

> 使用 Provider 区分方式组织 Claw Code快捷启动配置，同一 Qwen 模型通过不同 provider 路由。

## 项目路径

- **项目根目录**: `/Users/aiassistant/Projects/OpenSourceProjects/CLAWCODE/claw-code/`
- **Rust 二进制**: `rust/target/debug/claw`
- **Shell**: zsh

## 架构设计

采用 **env 文件 + shell alias** 模式，通过 Provider（而非模型）区分路由：

```
~/.claw-anthropic-env    → Anthropic-compatible proxy → Qwen
~/.claw-dashscope-env    → DashScope native → Qwen
~/.claw/settings.json    → User-defined model aliases
~/.bash_aliases          → Shell aliases
```

## Provider 路由规则

### Anthropic-compatible proxy

通过 `~/.claw-anthropic-env` 配置：
- **ANTHROPIC_BASE_URL**: `https://coding.dashscope.aliyuncs.com/apps/anthropic`
- **ANTHROPIC_AUTH_TOKEN**: Anthropic 兼容代理 token（`sk-sp-...` 格式）
- 通过 Anthropic 协议代理路由到 DashScope
- 模型由 `--model` 参数指定（如 `anthropic/qwen-plus`）

### DashScope native

通过 `~/.claw-dashscope-env` 配置：
- **DASHSCOPE_API_KEY**: DashScope 原生 API Key（`sk-...` 格式）
- DashScope base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`（claw 内置自动路由）
- 模型由 `--model` 参数指定（如 `qwen/qwen3.6-plus`）

### 环境变量注意事项

- `ANTHROPIC_API_KEY` 和 `ANTHROPIC_AUTH_TOKEN` **不可互换**
- Anthropic-compatible proxy 必须使用 `ANTHROPIC_AUTH_TOKEN`
- DashScope native 使用 `DASHSCOPE_API_KEY`

## 认证环境变量说明

| 变量 | 用途 | 格式 |
|------|------|------|
| `ANTHROPIC_AUTH_TOKEN` | Anthropic-compatible 代理认证 | `sk-sp-...` |
| `ANTHROPIC_BASE_URL` | Anthropic 代理端点 | URL |
| `DASHSCOPE_API_KEY` | DashScope 原生认证 | `sk-...` |

## Alias 配置清单

### `claw-anthropic-qwen`

- **Provider**: Anthropic-compatible proxy (硅基流动/DashScope)
- **模型**: `anthropic/qwen-plus`
- **env**: `~/.claw-anthropic-env`
- **认证**: `ANTHROPIC_AUTH_TOKEN`

### `claw-dashscope-qwen`

- **Provider**: DashScope native
- **模型**: `qwen/qwen3.6-plus`
- **env**: `~/.claw-dashscope-env`
- **认证**: `DASHSCOPE_API_KEY`

## Model Aliases (`~/.claw/settings.json`)

```json
{
  "aliases": {
    "q": "anthropic/qwen-plus",
    "qm": "qwen/qwen-max",
    "qwq": "qwen/qwq-max",
    "g": "grok",
    "gm": "grok-mini",
    "gpt": "openai/gpt-4.1",
    "gptmini": "openai/gpt-4.1-mini"
  }
}
```

## 扩展指南

### OpenRouter 模板

1. 创建 `~/.claw-openrouter-env`，填入 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`
2. 取消注释 `~/.bash_aliases` 中的 `claw-openrouter-qwen` alias
3. 根据需要修改 `--model` 参数

### xAI 模板

1. 创建 `~/.claw-xai-env`，填入 xAI 的 API Key 和 Base URL
2. 添加对应 shell alias

### Ollama 模板

1. 创建 `~/.claw-ollama-env`，填入 Ollama 的本地地址
2. 添加对应 shell alias，指定本地模型名

## 验证

```bash
source ~/.bash_aliases

# 测试 Anthropic-compatible proxy 路由
claw-anthropic-qwen      # anthropic/qwen-plus — 通过 Anthropic-compatible proxy

# 测试 DashScope native 路由
claw-dashscope-qwen      # qwen/qwen3.6-plus — 通过 DashScope native
```

## 相关页面

- [[OpenClaw工具链]] — OpenClaw 工具链配置
- [[AI模型提供商概览]] — AI 模型提供商列表
