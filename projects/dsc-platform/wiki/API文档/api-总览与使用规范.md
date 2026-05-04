---
title: "API 总览与使用规范"
type: api
created: 2026-05-03
last_updated: 2026-05-03
source_count: 2
confidence: medium
status: active
tags:
  - API
  - 接口规范
  - 开发指南
sources:
  - api_main.py
  - 项目接口分析
---

# API 总览与使用规范

## 概述
DSC Platform提供完整的RESTful API接口，涵盖知识库管理、向量检索、流程编排、数据库操作等所有功能。API设计遵循REST原则，使用标准HTTP状态码，支持JSON格式的请求和响应，便于各种编程语言和框架集成。

## 基础信息

### 服务地址
- **本地开发**：`http://localhost:5630`
- **测试环境**：`https://api-test.dsc-platform.com`
- **生产环境**：`https://api.dsc-platform.com`

### 版本控制
API采用URL路径版本控制，当前最新版本为v1：
```
https://api.dsc-platform.com/api/v1/...
```

### 通信协议
所有API请求均使用HTTPS协议，确保数据传输安全。

## 认证与授权

### API Key认证
大部分API需要通过API Key进行认证，将API Key放在请求头中：
```http
Authorization: Bearer YOUR_API_KEY
```

### 认证流程
1. 在平台控制台创建API Key，设置对应的权限范围
2. 在API请求的Header中携带API Key
3. 服务端验证API Key的有效性和权限
4. 验证通过后处理请求，否则返回401错误

### 权限范围
| 权限范围 | 描述 |
|---------|------|
| `knowledge:read` | 知识库读取权限 |
| `knowledge:write` | 知识库写入权限 |
| `vectors:read` | 向量检索权限 |
| `vectors:write` | 向量管理权限 |
| `flow:read` | 流程读取权限 |
| `flow:write` | 流程编辑和执行权限 |
| `database:read` | 数据库查询权限 |
| `database:write` | 数据库管理权限 |
| `admin` | 管理员权限，包含所有权限 |

## 请求规范

### 请求方法
| 方法 | 用途 | 幂等性 |
|------|------|--------|
| `GET` | 查询资源 | 是 |
| `POST` | 创建资源或执行操作 | 否 |
| `PUT` | 更新资源（全量） | 是 |
| `PATCH` | 更新资源（部分） | 是 |
| `DELETE` | 删除资源 | 是 |

### 请求头
| 头字段 | 说明 | 示例 |
|--------|------|------|
| `Content-Type` | 请求体类型，必须为 `application/json` | `Content-Type: application/json` |
| `Authorization` | 认证信息 | `Authorization: Bearer sk_xxxxxxxxxxxxxxxx` |
| `X-Request-ID` | 请求唯一标识，用于问题排查，推荐添加 | `X-Request-ID: req_1234567890abcdef` |
| `X-Tenant-ID` | 租户ID，多租户场景下需要 | `X-Tenant-ID: tenant_123` |

### 请求参数
- **路径参数**：用于标识资源ID，如 `/api/knowledge/documents/{doc_id}`
- **查询参数**：用于过滤、分页、排序等，放在URL的?后面
- **请求体**：用于传递创建或更新资源的详细信息，JSON格式

### 分页请求
所有列表类接口都支持分页，使用以下查询参数：
| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `page` | int | 页码，从1开始 | 1 |
| `page_size` | int | 每页数量，最大不超过100 | 20 |
| `sort_by` | string | 排序字段 | `create_time` |
| `sort_order` | string | 排序方向，`asc`或`desc` | `desc` |

分页响应示例：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

## 响应规范

### 统一响应格式
所有API响应都采用统一的JSON格式：
```json
{
  "code": 0,              // 状态码，0表示成功，非0表示失败
  "message": "success",   // 响应消息，成功时为"success"，失败时为错误描述
  "data": {},             // 响应数据，成功时返回，失败时可能为null
  "request_id": "req_1234567890abcdef"  // 请求ID，用于排查问题
}
```

### HTTP状态码
| 状态码 | 含义 | 说明 |
|--------|------|------|
| `200 OK` | 请求成功 | 正常响应 |
| `201 Created` | 创建成功 | POST请求创建资源成功 |
| `202 Accepted` | 已接受 | 请求已接受，正在异步处理 |
| `204 No Content` | 无内容 | 请求成功但没有返回内容 |
| `400 Bad Request` | 请求错误 | 参数错误、格式错误等 |
| `401 Unauthorized` | 未认证 | 认证信息缺失或无效 |
| `403 Forbidden` | 无权限 | 认证成功但没有访问权限 |
| `404 Not Found` | 资源不存在 | 请求的资源不存在 |
| `405 Method Not Allowed` | 方法不允许 | 请求方法不支持 |
| `409 Conflict` | 资源冲突 | 资源已存在或版本冲突 |
| `429 Too Many Requests` | 请求过多 | 触发限流 |
| `500 Internal Server Error` | 服务器错误 | 服务端内部错误 |
| `502 Bad Gateway` | 网关错误 | 网关或代理错误 |
| `503 Service Unavailable` | 服务不可用 | 服务暂时不可用 |
| `504 Gateway Timeout` | 网关超时 | 请求处理超时 |

### 业务错误码
| 错误码 | 含义 | 说明 |
|--------|------|------|
| `0` | 成功 | 请求处理成功 |
| `10000` | 参数错误 | 请求参数校验失败 |
| `10001` | 缺少必填参数 | 缺少必要的请求参数 |
| `10002` | 参数格式错误 | 参数格式不符合要求 |
| `10003` | 参数值超出范围 | 参数值不在允许的范围内 |
| `20000` | 认证错误 | 认证失败 |
| `20001` | API Key无效 | API Key不存在或已过期 |
| `20002` | 权限不足 | 没有访问该资源的权限 |
| `20003` | IP地址受限 | 请求IP不在白名单中 |
| `30000` | 资源不存在 | 请求的资源不存在 |
| `30001` | 资源已存在 | 创建的资源已存在 |
| `30002` | 资源被占用 | 资源正在被使用，无法删除或修改 |
| `40000` | 操作失败 | 业务操作失败 |
| `40001` | 文件上传失败 | 文件上传过程中出现错误 |
| `40002` | 文件格式不支持 | 不支持的文件格式 |
| `40003` | 文件大小超出限制 | 文件大小超过最大限制 |
| `40100` | 知识库操作失败 | 知识库相关操作失败 |
| `40200` | 向量操作失败 | 向量相关操作失败 |
| `40300` | 流程操作失败 | 流程相关操作失败 |
| `40400` | 数据库操作失败 | 数据库相关操作失败 |
| `50000` | 服务端错误 | 服务端内部错误 |
| `50001` | 服务暂不可用 | 服务暂时不可用，请稍后重试 |
| `50002` | 操作超时 | 请求处理超时 |
| `50003` | 第三方服务错误 | 调用第三方服务失败 |

### 错误响应示例
```json
{
  "code": 10001,
  "message": "缺少必填参数: document_id",
  "data": null,
  "request_id": "req_1234567890abcdef"
}
```

## API模块总览

### 1. 知识库管理API (`/api/knowledge`)
提供知识库和文档的全生命周期管理能力。
- 知识库的创建、查询、更新、删除
- 文档的上传、下载、重新处理
- 文档解析、OCR、元数据提取
- 文档列表查询、检索

### 2. 向量管理API (`/api/vectors`)
提供向量数据集管理和检索能力。
- 向量数据集管理
- 文档向量化处理
- 向量检索（向量检索、混合检索、关键词检索）
- 检索结果重排序

### 3. 流程编排API (`/api/flow`)
提供工作流的定义、执行和管理能力。
- 流程的CRUD和版本管理
- 流程的执行和状态查询
- 流程执行日志查询
- 流程模板管理

### 4. 流程应用市场API (`/api/flow-apps`)
提供预定义流程应用的调用和管理能力。
- 应用模板查询
- 应用执行
- 应用执行结果查询
- 自定义应用开发

### 5. 数据库管理API (`/api/database`)
提供数据库连接管理和查询能力。
- 数据库连接配置管理
- 数据库查询执行
- 查询历史和保存
- SQL解析和优化建议

### 6. 系统管理API (`/api/admin`)
提供系统级别的管理能力。
- 用户和权限管理
- 系统配置管理
- 监控和统计
- 日志查询

## 异步任务处理规范

### 异步任务流程
对于耗时较长的操作，API采用异步处理模式：
1. 客户端发起请求，服务端立即返回202 Accepted状态
2. 响应中包含task_id，用于后续查询任务状态
3. 服务端后台异步处理任务
4. 客户端通过任务查询接口轮询任务状态
5. 任务完成后，可以获取任务结果

### 异步任务相关接口
```http
# 查询任务状态
GET /api/tasks/{task_id}

# 取消任务
POST /api/tasks/{task_id}/cancel

# 获取任务结果（完成后）
GET /api/tasks/{task_id}/result
```

### 任务状态
| 状态 | 描述 |
|------|------|
| `pending` | 任务等待中 |
| `running` | 任务正在执行 |
| `completed` | 任务执行成功 |
| `failed` | 任务执行失败 |
| `cancelled` | 任务已取消 |

### 异步任务响应示例
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_1234567890abcdef",
    "status": "running",
    "progress": 65,
    "message": "正在处理文档...",
    "create_time": "2024-01-01T12:00:00Z",
    "update_time": "2024-01-01T12:00:10Z"
  },
  "request_id": "req_1234567890abcdef"
}
```

## SDK与集成

### 官方SDK
平台提供多语言的官方SDK，简化集成过程：
- **Python SDK**：`pip install dsc-platform`
- **JavaScript/TypeScript SDK**：`npm install @dsc-platform/sdk`
- **Java SDK**：Maven依赖
- **Go SDK**：Go module

### Python SDK使用示例
```python
from dsc_platform import DscPlatformClient

# 初始化客户端
client = DscPlatformClient(
    api_key="sk_xxxxxxxxxxxxxxxx",
    base_url="https://api.dsc-platform.com"
)

# 上传文档
result = client.knowledge.upload_document(
    dataset_id="my_dataset",
    file_path="document.pdf",
    metadata={"category": "tech"}
)

# 检索
search_result = client.vectors.search(
    dataset_id="my_dataset",
    query="如何使用API？",
    limit=5
)

# 执行流程
flow_result = client.flow.execute_flow(
    flow_id="flow_123",
    inputs={"query": "帮我生成报告"}
)
```

## 限流策略

### 限流规则
API采用令牌桶算法进行限流，不同级别的用户有不同的限流配额：
- **免费版**：100次/分钟，1000次/天
- **专业版**：1000次/分钟，10000次/天
- **企业版**：自定义配额，可联系商务调整

### 限流响应头
限流相关信息会在响应头中返回：
| 头字段 | 说明 |
|--------|------|
| `X-RateLimit-Limit` | 时间窗口内的最大请求数 |
| `X-RateLimit-Remaining` | 时间窗口内剩余的请求数 |
| `X-RateLimit-Reset` | 限流重置时间，Unix时间戳 |

### 触发限流后的处理
当触发限流时，会返回429 Too Many Requests状态码，建议客户端：
1. 实现指数退避重试策略
2. 合理控制请求频率，避免并发过高
3. 对于批量操作，使用批量接口而不是多次调用单条接口

## 最佳实践

### 1. 错误处理
- 对所有API调用都进行错误捕获和处理
- 针对不同的错误码采取不同的处理策略
- 记录详细的错误信息和request_id，方便排查问题

### 2. 性能优化
- 对于批量操作，使用批量接口减少请求次数
- 合理使用缓存，减少重复请求
- 异步操作使用任务查询接口，避免频繁轮询
- 合理设置超时时间，避免长时间等待

### 3. 安全建议
- API Key要妥善保管，不要硬编码到代码中
- 定期轮换API Key
- 配置IP白名单，限制API Key的使用范围
- 按照最小权限原则为API Key分配权限

### 4. 兼容性考虑
- 关注API版本变更，及时适配新版本
- 避免依赖未文档化的接口和字段
- 响应中的额外字段要能兼容处理，不要严格校验字段存在性

## 常见问题

### Q: API请求超时时间是多少？
A: 同步接口的超时时间是30秒，超过30秒的操作会转为异步任务处理。

### Q: 支持的最大请求体大小是多少？
A: 普通请求最大支持10MB，文件上传接口最大支持100MB。

### Q: 如何获取API Key？
A: 登录平台控制台，进入"API管理"页面，可以创建和管理API Key。

### Q: API支持跨域请求吗？
A: 支持，服务端已经配置了CORS头，可以直接在浏览器端调用。

### Q: 有没有API调用次数限制？
A: 不同的套餐有不同的限制，具体可以查看控制台的配额信息，超过限制会返回429错误。
