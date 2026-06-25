---
title: "平台配置模块完整实现记录 - LLM配置、Provider管理、Domain配置、前端集成"
type: analysis
created: 2026-05-07
last_updated: 2026-05-07
source_count: 0
confidence: medium
status: active
tags:
  - platform-config
  - llm-config
  - provider
  - domain
  - implementation
  - askdata-platform
  - 2026-05
---

---
title: "平台配置模块完整实现记录 - LLM配置、Provider管理、Domain配置、前端集成"
type: "analysis"
tags: ["platform-config", "llm-config", "provider", "domain", "implementation", "askdata-platform", "2026-05"]
created: "2026-05-07"
last_updated: "2026-05-07"
confidence: "high"
status: "active"
---

# 平台配置模块完整实现记录

## 背景

2026-05-07，根据 git 历史提交记录和 wiki 知识库文档，发现 AskData Platform 的平台配置模块存在功能缺失。虽然数据库表结构已通过 commit `e699673f` 创建，但后端 API、前端界面和初始化脚本均不完整。

### 发现的问题

1. **后端 API 缺失**
   - Provider 管理 API（`provider_views.py`）
   - Domain 配置 API（`domain_config_views.py`）
   - LLM 配置历史版本显示问题

2. **前端界面缺失**
   - Domain 配置页面
   - Provider API 协议选择功能

3. **初始化脚本**
   - Domain 初始化脚本缺失

---

## 实现范围

本次实现完整补充了平台配置模块的所有功能，包括：

| 模块 | 状态 |
|------|------|
| LLM 配置管理 | ✅ 增强 |
| Provider 管理 | ✅ 新建 |
| Domain 配置 | ✅ 新建 |
| 平台配置入口 | ✅ 启用 |
| 初始化脚本 | ✅ 补充 |

---

## 后端实现详情

### 1. LLM 配置模块增强

#### 修复内容

**文件**: `core/modules/config/views/llm_config_views.py`

**问题**: LLM 配置历史版本显示为 0，缺少正确的关联查询

**修复**:
```python
# 添加缺失的导入
from sqlalchemy import select
from core.models.db.db_initial_models import LLMModuleConfig

# 在 get_config_history 中正确关联查询
for record in records:
    version = None  # 改为可选，避免硬编码 0
    if record.config_id:
        try:
            config_query = select(LLMModuleConfig).where(LLMModuleConfig.id == record.config_id)
            config_result = await db.execute(config_query)
            config_record = config_result.scalar_one_or_none()
            if config_record:
                version = config_record.version
        except Exception as e:
            LogUtils.warning(f"Failed to get config version for history record {record.id}: {e}")
```

#### 请求模型更新

**文件**: `core/modules/config/request_model.py`

添加了对 `api_protocol` 字段和 `version` 字段的支持

### 2. LLM 配置管理器

**新建文件**: `core/helpers/llm_config_manager.py`

提供配置验证功能，特别是对 Claw 配置中的 `domain_models` 进行验证：

```python
class LlmConfigManager:
    @classmethod
    async def validate_config(cls, module: str, config: Dict[str, Any], db: Optional[Database] = None):
        if module == "claw_code":
            domain_models = config.get("domain_models", {})
            if domain_models and db:
                for domain_code in domain_models.keys():
                    query = select(DomainConfig).where(DomainConfig.code == domain_code)
                    result = await db.execute(query)
                    if not result.scalar_one_or_none():
                        return False, f"Domain code '{domain_code}' does not exist"
        return True, None
```

### 3. Provider 管理模块

**新建文件**: `core/modules/config/views/provider_views.py`

#### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/config/providers/types` | GET | 获取支持的 Provider 类型列表 |
| `/api/config/providers` | GET | 获取所有 Provider 列表 |
| `/api/config/providers/{id}` | GET | 获取单个 Provider |
| `/api/config/providers` | POST | 创建 Provider |
| `/api/config/providers/{id}` | PUT | 更新 Provider |
| `/api/config/providers/{id}` | DELETE | 删除 Provider |

#### Provider 类型注册表

```python
PROVIDER_TYPE_REGISTRY = {
    "tongyi": {
        "display_name": "通义千问（DashScope）",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_protocol": "openai",
        "description": "阿里云通义千问系列模型",
    },
    "anthropic": {
        "display_name": "Anthropic Claude",
        "default_base_url": "https://api.anthropic.com",
        "default_protocol": "anthropic",
        "description": "Anthropic Claude 系列模型",
    },
    "openai": {
        "display_name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "default_protocol": "openai",
        "description": "OpenAI GPT 系列模型",
    },
    "ollama": {
        "display_name": "Ollama",
        "default_base_url": "http://localhost:11434/v1",
        "default_protocol": "openai",
        "description": "本地 Ollama 模型",
    },
    "openai_api_compatible": {
        "display_name": "OpenAI API 兼容",
        "default_base_url": None,
        "default_protocol": "openai",
        "description": "兼容 OpenAI API 的服务",
    },
}
```

#### 数据库模型更新

**文件**: `core/models/db/db_initial_models.py`

为 `LlmProvider` 模型添加了 `api_protocol` 字段：

```python
api_protocol = Column(String(32), nullable=False, default="openai",
                     comment="API 协议: openai | anthropic")
```

### 4. Domain 配置模块

**新建文件**: `core/modules/config/views/domain_config_views.py`

#### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/config/domains` | GET | 获取所有 Domain 列表 |
| `/api/config/domains/tree` | GET | 获取 Domain 树形结构 |
| `/api/config/domains/{id}` | GET | 获取单个 Domain |
| `/api/config/domains/code/{code}` | GET | 通过 code 获取 Domain |
| `/api/config/domains` | POST | 创建 Domain |
| `/api/config/domains/{id}` | PUT | 更新 Domain |
| `/api/config/domains/{id}` | DELETE | 删除 Domain |

#### Domain 层级结构

支持两层结构：
- Level 1: 行业域、职能域
- Level 2: 具体行业、具体职能

### 5. 路由注册

**文件**: `core/server/app.py`

添加配置模块路由注册：

```python
# Config routers
from core.modules.config.views import (
    domain_config_router,
    llm_config_router,
    provider_router,
)

# Register config routers
app.include_router(llm_config_router)
app.include_router(provider_router)
app.include_router(domain_config_router)
```

同时更新了 `DIRECT_UNDER_API_PREFIXES` 配置以支持 `/config` 路径。

---

## 前端实现详情

### 1. API 客户端

**文件**: `web/src/apis/config/`

新增了：
- `provider.api.ts` - Provider 管理 API 客户端
- `domain.api.ts` - Domain 配置 API 客户端
- 更新了 `llm-config.api.ts` 和 `types.ts`

### 2. Domain 配置页面

**新建文件**: `web/src/features/domain-config/pages/DomainConfigPage.tsx`

功能特性：
- Domain 列表显示
- 按类型筛选（行业/职能）
- 创建新 Domain
- 删除 Domain（有子级校验）
- 编辑 Domain

### 3. LLM 配置页面增强

**文件**: `web/src/features/llm-config/pages/LlmConfigPage.tsx`

新增功能：
- Provider 类型选择时自动填充默认 API 协议
- API 协议下拉框（OpenAI/Anthropic）
- 历史记录中显示版本号

### 4. 平台配置页面更新

**文件**: `web/src/features/platform-config/pages/PlatformConfigPage.tsx`

启用了 Domain 配置链接（移除了 disabled 状态）

### 5. 路由集成

**文件**: `web/src/app/routes/index.tsx`

添加了 Domain 配置页面路由：

```typescript
const DomainConfigPage = lazy(() => import('@/features/domain-config/pages/DomainConfigPage'))

// 在路由配置中添加：
<Route path={ROUTES.DOMAIN_CONFIG} element={
  <Suspense fallback={<LoadingFallback />}>
    <DomainConfigPage />
  </Suspense>
} />
```

---

## 数据初始化

### 1. Tag 初始化脚本

**现有文件**: `deployments/deployment_local/init-scripts/03-init-tags.sql`

已包含完整的标签初始化，包括：
- 五大财务循环
- 查询类型
- 知识资产类型
- 成员公司（寿险、产险、银行、租赁等）

### 2. Domain 初始化脚本

**新建文件**: `deployments/deployment_local/init-scripts/05-init-domains.sql`

包含：
- Level 1 根节点：行业域、职能域
- Level 2 行业域：金融业、保险业、银行业、证券业、基金业、信托业、房地产业、制造业、零售业、医疗健康
- Level 2 职能域：人力资源、财务管理、信息技术、运营管理、市场营销、法务合规、行政管理

所有 INSERT 使用幂等性设计（`WHERE NOT EXISTS`）

---

## 修改文件清单

### 后端文件

| 路径 | 类型 | 说明 |
|------|------|------|
| `core/modules/config/helper.py` | 修改 | 添加 validate_config 方法调用 |
| `core/modules/config/request_model.py` | 修改 | 添加 api_protocol、version、Domain 相关模型 |
| `core/modules/config/views/llm_config_views.py` | 修改 | 修复历史版本显示、添加 provider 兼容端点 |
| `core/modules/config/views/provider_views.py` | 新建 | Provider 管理 API |
| `core/modules/config/views/domain_config_views.py` | 新建 | Domain 配置 API |
| `core/modules/config/views/__init__.py` | 修改 | 导出所有路由 |
| `core/helpers/llm_config_manager.py` | 新建 | LLM 配置验证管理器 |
| `core/models/db/db_initial_models.py` | 修改 | LlmProvider 添加 api_protocol 字段 |
| `core/server/app.py` | 修改 | 注册配置模块路由 |

### 前端文件

| 路径 | 类型 | 说明 |
|------|------|------|
| `web/src/apis/config/types.ts` | 修改 | 添加 Domain、Provider 相关类型 |
| `web/src/apis/config/llm-config.api.ts` | 修改 | 更新 API 客户端 |
| `web/src/apis/config/provider.api.ts` | 新建 | Provider API 客户端 |
| `web/src/apis/config/domain.api.ts` | 新建 | Domain API 客户端 |
| `web/src/apis/config/index.ts` | 新建 | 统一导出 |
| `web/src/features/llm-config/pages/LlmConfigPage.tsx` | 修改 | 添加 API 协议选择、版本显示 |
| `web/src/features/platform-config/pages/PlatformConfigPage.tsx` | 修改 | 启用 Domain 配置 |
| `web/src/features/domain-config/pages/DomainConfigPage.tsx` | 新建 | Domain 配置页面 |
| `web/src/app/routes/index.tsx` | 修改 | 添加 Domain 配置路由 |

### 初始化脚本

| 路径 | 类型 | 说明 |
|------|------|------|
| `deployments/deployment_local/init-scripts/05-init-domains.sql` | 新建 | Domain 初始化脚本 |

---

## 架构遵循

本次实现严格遵循以下原则：

### 1. 向后兼容

- 所有新增字段均有默认值
- API 保持兼容性
- 现有配置无需迁移

### 2. 验证前置

- Provider 创建时验证协议类型
- Claw 配置保存前验证 domain_code 存在性
- Domain 删除前检查子级存在性

### 3. 幂等性设计

- 所有初始化脚本使用 `WHERE NOT EXISTS`
- 可重复执行，不会产生重复数据

### 4. 统一入口

- 所有 LLM 配置修改仍通过 `ScopeConfig` 生效
- 未绕过现有配置链路

---

## 使用指南

### Provider 管理

1. 访问 `/platform-config` → 点击 "LLM 配置"
2. 点击 "新建 Provider"
3. 选择 Provider 类型（如 "通义千问"）
4. 自动填充默认 API 协议和 Base URL
5. 填写其余信息并保存

### Domain 配置

1. 访问 `/platform-config` → 点击 "Domain 配置"
2. 查看现有 Domain 树形结构
3. 可新增、编辑、删除 Domain

### LLM 配置

1. 访问 `/platform-config` → 点击 "LLM 配置"
2. 为不同模块（analysis_room、claw_code、knowledge_base）创建配置版本
3. 激活需要的配置版本
4. 查看历史变更记录

---

## 测试验证清单

### 后端 API
- [x] Provider CRUD 正常工作
- [x] Domain CRUD 正常工作
- [x] LLM 配置历史版本正确显示
- [x] Domain 删除时检查子级
- [x] Claw 配置验证 domain_code 存在性

### 前端界面
- [x] 平台配置入口可访问
- [x] Provider 管理界面正常
- [x] Domain 配置界面正常
- [x] LLM 配置界面正常
- [x] 路由切换正常

### 数据初始化
- [x] `03-init-tags.sql` 执行成功
- [x] `05-init-domains.sql` 执行成功
- [x] 重复执行不产生重复数据

---

## 关联文档

- [平台配置管理多问题修复 - LLM配置、Provider管理、Claw配置、Tag初始化](./平台配置管理多问题修复-llm配置provider管理claw配置tag初始化.md) — 原始问题分析
- [Domain-Config功能规范](./Domain-Config功能规范.md) — Domain 配置功能规范
- [LLM Provider 多供应商体系规划](./llm-provider-多供应商体系-参考-dify-model-runtime-的建设规划.md) — Provider 体系长期规划
- [AskData 架构设计](./askdata-架构设计.md) — 总体架构

