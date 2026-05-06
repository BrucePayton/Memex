---
title: "Keycloak 系统令牌获取失败 - Username or password is incorrect"
type: analysis
created: 2026-05-07
last_updated: 2026-05-07
source_count: 0
confidence: medium
status: active
tags:
  - keycloak
  - authentication
  - configuration
  - debug
---

## 故障概述

应用在访问需要页面权限控制的页面时，频繁出现错误日志：
```
Error getting system access token: Username or password is incorrect
resolve_roles_for_page_acl: admin realm role fetch skipped
```

虽然有降级处理不会导致页面崩溃，但会产生大量日志噪音，且无法从 Keycloak Admin API 获取用户的 realm 角色和组派生角色。

## 触发路径

1. 用户登录并访问需要权限控制的页面
2. `resolve_roles_for_page_acl()` 被调用以解析用户的页面 ACL 角色
3. 该方法尝试通过 `get_system_access_token()` 获取系统访问令牌
4. 令牌获取失败，触发警告日志
5. 系统回退到仅使用用户属性中的角色

## Root Cause

### 配置不匹配

在 `deployments/deployment_local/.env` 中存在配置不一致：

```env
# Keycloak 容器管理员密码（正确）
KC_ADMIN_PASSWORD=Aiwud3ujfe

# 系统访问令牌使用的密码（错误）
KEYCLOAK_SYSTEM_PASSWORD=admin123
```

系统使用 `KEYCLOAK_SYSTEM_PASSWORD` 作为凭据向 Keycloak 请求系统访问令牌，但该密码与实际的 Keycloak admin 用户密码不匹配。

### 技术细节

`get_system_access_token()` 方法：
- 读取 `KEYCLOAK_SYSTEM_USERNAME` 和 `KEYCLOAK_SYSTEM_PASSWORD` 环境变量
- 使用资源所有者密码模式（Resource Owner Password Credentials）向 Keycloak 请求令牌
- Keycloak 验证凭据失败，返回 "Username or password is incorrect"

`resolve_roles_for_page_acl()` 方法：
- 每次需要解析用户角色时都会调用 `get_system_access_token()`
- 虽然有 try-except 捕获异常并继续降级处理，但每次失败都会记录 ERROR 日志
- 没有失败冷却机制，导致短时间内大量重复的失败请求

## 修复方案

### 方案 1：配置修正（立即执行）

修改 `deployments/deployment_local/.env` 第 224 行：

```env
# 修改前
KEYCLOAK_SYSTEM_PASSWORD=admin123

# 修改后
KEYCLOAK_SYSTEM_PASSWORD=Aiwud3ujfe
```

然后重启后端容器使配置生效：
```bash
docker restart askdata_platform_backend
```

### 方案 2：代码优化（减少日志噪音）

修改 `utils/keycloak_utils.py`：

#### 1. 添加失败缓存机制

```python
# 在文件顶部添加
_system_token_failure_cache: Optional[float] = None
_system_token_failure_cooldown: float = 300.0  # 5分钟冷却时间
```

#### 2. 优化 `get_system_access_token()` 方法

- 添加冷却时间检查，避免短时间内重复尝试
- 将日志级别从 ERROR 降级为 WARNING（因为已有降级处理）
- 失败时记录时间戳，进入冷却期

#### 3. 优化 `resolve_roles_for_page_acl()` 方法

- 在冷却期内自动跳过 Admin API 尝试
- 添加调试日志说明冷却状态
- 减少不必要的异常捕获和警告日志

## 涉及文件

- `deployments/deployment_local/.env:224` — 修正 `KEYCLOAK_SYSTEM_PASSWORD`
- `utils/keycloak_utils.py` — 添加失败缓存和日志优化

## 经验教训

1. **配置一致性检查**：相关的配置项（如 `KC_ADMIN_PASSWORD` 和 `KEYCLOAK_SYSTEM_PASSWORD`）应该保持同步，或在文档中明确说明关系。

2. **环境变量模板维护**：`.env.template` 中应该注释说明这些配置项的关系，避免后续维护时出错。

3. **降级策略与日志级别**：当有完善的降级处理时，失败日志应使用 WARNING 级别而不是 ERROR，避免误导运维人员。

4. **失败冷却机制**：对于外部依赖的请求，应该添加失败冷却机制，避免短时间内大量重复失败请求造成日志洪水和资源浪费。

5. **配置验证**：应用启动时可以增加关键配置项的验证逻辑，提前发现配置不匹配问题。

## 相关文档

- `deployments/deployment_local/keycloak/TOKEN_SETTINGS.md` — Keycloak 配置说明

