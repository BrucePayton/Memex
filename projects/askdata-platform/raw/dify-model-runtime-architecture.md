# Dify Model Runtime Architecture

> 参考来源: `/Users/aiassistant/Projects/OpenSourceProjects/Dify/dify/api/core/model_runtime/`
> 记录于 2026-05-04，用于 AskData Platform LLM Provider 体系建设参考

## 整体架构

Dify 的 Model Runtime 是一套插件化的模型供应商体系，核心目录结构：

```
model_runtime/
├── callbacks/           # 回调处理
├── model_providers/     # 供应商注册与工厂
│   ├── __base/          # 基类体系
│   ├── __init__.py
│   ├── _position.yaml   # 44 个供应商的排序配置
│   └── model_provider_factory.py  # 工厂类
├── entities/            # 实体定义（ProviderEntity, AIModelEntity 等）
├── errors/              # 异常定义
├── schema_validators/   # 凭据校验器
└── utils/               # 工具函数
```

## Provider 注册与发现

- `_position.yaml` 定义了 44 个供应商的有序列表（openai, deepseek, anthropic...）
- `ModelProviderFactory` 读取 `_position.yaml` 构建排序映射
- 运行时通过 `get_plugin_model_providers()` 从插件守护进程获取 `PluginModelProviderEntity` 列表
- 每个 entity 携带 `declaration` 字段（类型 `ProviderEntity`）

## 基类体系

`AIModel`（Pydantic BaseModel）是根基类，包含：
- `tenant_id`, `plugin_id`, `provider_name`, `model_type`
- 错误映射与转换 (`_invoke_error_mapping`)
- 价格计算 (`get_price`)
- Schema 解析 (`get_model_schema`)

### 具体模型类型子类

| 子类 | model_type | 用途 |
|------|-----------|------|
| `LargeLanguageModel` | LLM | 文本生成/对话 |
| `TextEmbeddingModel` | TEXT_EMBEDDING | 文本嵌入 |
| `RerankModel` | RERANK | 重排序 |
| `Speech2TextModel` | SPEECH2TEXT | 语音识别 |
| `ModerationModel` | MODERATION | 内容审核 |
| `TTSModel` | TTS | 文本转语音 |

所有子类通过 `ModelProviderFactory.get_model_type_instance()` 按 `ModelType` 实例化。

## 凭据管理

凭据分两层：
1. **Provider 凭据** (`ProviderCredentialSchema`) — 全局 API key、base URL
2. **Model 凭据** (`ModelCredentialSchema`) — 每个模型的独立凭据覆盖

每个 `CredentialFormSchema` 包含：`variable`, `label`, `type` (TEXT_INPUT / SECRET_INPUT / SELECT / RADIO / SWITCH), `required`, `default`, `options`, `placeholder`, `max_length`, `show_on` 条件。

校验器链：`CommonValidator` → `ProviderCredentialSchemaValidator` / `ModelCredentialSchemaValidator` → 插件守护进程 `validate_*_credentials()`

## 调用模式

```
[Plugin Daemon] <--gRPC--> [PluginModelClient]
      |                          |
      | fetch_model_providers()  | invoke_llm(), validate_credentials()
      v                          v
[ModelProviderFactory] -----> [AIModel subclasses]
      |                          |
      | 读取 _position.yaml      | 委托给插件守护进程
      | 缓存 schemas             |
      v                          v
[ProviderEntity]           [LargeLanguageModel, TextEmbeddingModel, ...]
```

## 关键实体

- **`ProviderEntity`** — 完整供应商描述：`provider` 名称、i18n label/description、图标、`supported_model_types`、`configurate_methods`、`models`（AIModelEntity 列表）、`provider_credential_schema`、`model_credential_schema`
- **`AIModelEntity`**（extends `ProviderModel`）— 具体模型：`model` 名称、`label`、`model_type`、`features`、`fetch_from`、`model_properties`、`parameter_rules`、`pricing`
- **`PriceConfig`** — `input` 单价、`output` 单价、`unit`、`currency`

## 对 AskData Platform 的参考价值

Dify 这套架构的核心设计理念：
1. **Provider 即插件** — 每个供应商独立实现，通过注册机制加入系统
2. **凭据与逻辑分离** — 凭据声明式定义，不硬编码在 Provider 实现中
3. **多层模型类型** — 不只有 LLM，还有 embedding、rerank、TTS 等
4. **工厂驱动** — 按类型动态实例化，调用方无需关心具体 Provider

AskData 当前方案（`LLMParamsUtils` + `LiteLLMFunctions`）本质是单层代理，缺乏这些抽象。
