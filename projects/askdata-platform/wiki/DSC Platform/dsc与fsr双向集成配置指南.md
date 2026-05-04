---
title: "DSC与FSR双向集成配置指南"
type: configuration-guide
created: 2026-05-03
last_updated: 2026-05-03
source_count: 0
confidence: medium
status: active
tags:
  - DSC
  - FSR
  - Webhook
  - 双向集成
  - 配置指南
  - 部署
---

# DSC与FSR双向集成配置指南

## 1. 功能概述
DSC（数据供应链）与FSR（Free Style Report）双向集成支持两个核心能力：
1. FSR侧的链路快照/模板可以推送到DSC进行可视化编辑和执行
2. DSC侧设计发布的流程可以主动推送到FSR作为领域模板，支持模板拼接和复用

本文档详细说明双向集成的配置方法、场景示例和最佳实践。

---

## 2. 核心配置项说明

### 2.1 共享密钥配置（两端必须一致）
webhook secret 是DSC和FSR之间通信的共享密钥，用于验证请求来源的合法性，防止未授权访问。

#### 生成方式：
```bash
# 生成32位强随机密钥（推荐）
openssl rand -hex 16

# Python生成方式
python -c "import secrets; print(secrets.token_hex(16))"
```

#### 配置要求：
- 两端配置的密钥必须完全一致
- 密钥长度建议不少于16位，包含字母、数字组合
- 生产环境请勿使用简单密码，定期（3-6个月）轮换密钥
- 禁止将密钥提交到代码仓库或打印到日志中

---

### 2.2 FSR端配置项
在FSR的`.env`文件中配置：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `DSC_WEBHOOK_SECRET` | 与DSC端一致的共享密钥，用于验证DSC推送请求的签名 | `dsc_fsr_shared_secret_2024` |
| `DSC_WEBHOOK_IP_WHITELIST` | 允许访问webhook的IP列表，逗号分隔，支持CIDR格式，留空则不限制IP | `172.16.0.0/12,192.168.1.100` |

---

### 2.3 DSC端配置项
在DSC的`.env`文件中配置：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `FSR_WEBHOOK_ENABLED` | 是否启用向FSR推送流程的功能 | `true` |
| `FSR_WEBHOOK_URL` | FSR的服务地址，不需要加路径后缀，系统会自动拼接`/api/chain-template/webhook/dsc-push` | `http://askdata-backend:5555` |
| `FSR_WEBHOOK_SECRET` | 与FSR端一致的共享密钥 | `dsc_fsr_shared_secret_2024` |
| `FSR_WEBHOOK_MAX_RETRIES` | 推送失败的最大重试次数，默认3次 | `3` |
| `FSR_WEBHOOK_RETRY_BACKOFF_MS` | 重试间隔的基础时间，单位毫秒，采用指数退避策略，默认1000ms | `1000` |
| `ASKDATA_PLATFORM_BASE_URL` | DSC调用FSR业务API的基地址，用于流程解析、知识库查询等场景 | `http://askdata-backend:5555` |

---

### 2.4 ASKDATA_PLATFORM_BASE_URL与FSR_WEBHOOK_URL的区别
两个配置完全独立，不会冲突，设计上用于不同场景：

| 维度 | ASKDATA_PLATFORM_BASE_URL | FSR_WEBHOOK_URL |
|------|---------------------------|-----------------|
| 用途 | DSC主动调用FSR的业务API | DSC推送流程发布事件到FSR |
| 使用场景 | 流程解析、知识库查询、数据处理等 | 仅用于流程发布同步到FSR模板库 |
| 调用方向 | DSC → FSR 业务请求 | DSC → FSR 事件通知 |
| 是否可配置为相同地址 | ✅ 90%场景下可以配置为相同，不会有任何问题 | ✅ 简单部署直接复用即可 |

---

## 3. 不同部署场景配置示例

### 3.1 本地deployment_local同Docker网络部署（最常用）
DSC和FSR都在同一个docker-compose网络中，使用容器名作为地址：

```env
# FSR端配置
DSC_WEBHOOK_SECRET=dsc_fsr_shared_secret_2024
DSC_WEBHOOK_IP_WHITELIST=172.16.0.0/12  # 允许Docker内部网段访问

# DSC端配置
FSR_WEBHOOK_ENABLED=true
FSR_WEBHOOK_URL=http://askdata-backend:5555
FSR_WEBHOOK_SECRET=dsc_fsr_shared_secret_2024
ASKDATA_PLATFORM_BASE_URL=http://askdata-backend:5555
```

✅ 优点：配置简单，不需要关心IP变化
✅ 适用场景：本地开发、测试环境、单主机部署

---

### 3.2 生产环境同VPC部署
DSC和FSR部署在同一内网VPC中：

```env
# FSR端配置
DSC_WEBHOOK_SECRET=your-production-secret-2024abc
DSC_WEBHOOK_IP_WHITELIST=10.0.1.10,10.0.1.11  # DSC服务的内网IP

# DSC端配置
FSR_WEBHOOK_ENABLED=true
FSR_WEBHOOK_URL=http://fsr-internal:5555  # FSR的内网服务地址
FSR_WEBHOOK_SECRET=your-production-secret-2024abc
ASKDATA_PLATFORM_BASE_URL=http://fsr-internal:5555
```

✅ 优点：安全性高，走内网速度快
✅ 适用场景：生产环境同机房部署

---

### 3.3 跨机房/云服务部署（内外网分离）
DSC和FSR部署在不同机房或云服务商，API调用走内网，webhook回调走公网：

```env
# DSC端配置
ASKDATA_PLATFORM_BASE_URL=http://fsr-internal.corp.com  # 内网API地址
FSR_WEBHOOK_URL=https://fsr-public.example.com  # 公网Webhook地址
```

✅ 优点：适配复杂网络架构，兼顾性能和可用性
✅ 适用场景：跨地域部署、混合云部署

---

## 4. 安全最佳实践
1. **密钥安全**：
   - 生产环境使用独立的强密钥，不要与其他系统共用
   - 密钥定期轮换，轮换时两端同步更新
   - 密钥通过配置中心或加密方式存储，不要明文硬编码

2. **IP白名单**：
   - 生产环境必须配置IP白名单，限制只有DSC的出口IP可以访问webhook接口
   - Docker部署可以配置Docker内网网段，不要全放开

3. **网络安全**：
   - 生产环境建议使用HTTPS协议通信
   - 不要将webhook接口暴露到公网无防护环境

---

## 5. 故障排查

### 5.1 推送失败报错"签名验证失败"
- 检查两端`DSC_WEBHOOK_SECRET`和`FSR_WEBHOOK_SECRET`配置是否完全一致
- 检查密钥是否有多余的空格或特殊字符
- 检查DSC版本是否支持签名功能（v1.8.0+）

### 5.2 推送失败报错"IP不在白名单中"
- 查看FSR日志中被拒绝的IP地址：`WARNING: DSC Webhook: Rejected request from non-whitelisted IP: x.x.x.x`
- 将该IP添加到FSR的`DSC_WEBHOOK_IP_WHITELIST`配置中
- Docker环境建议配置Docker内网网段`172.16.0.0/12`

### 5.3 推送失败报错"连接超时"
- 检查FSR服务是否正常运行
- 检查DSC到FSR的网络连通性：`curl telnet FSR地址:端口`
- 检查防火墙/安全组是否允许DSC访问FSR的5555端口

### 5.4 推送成功但FSR看不到模板
- 检查DSC流程是否正确发布（dry_run=false）
- 检查FSR模板库中`dsc_flow_id`是否和DSC的flow_id一致
- 查看FSR日志是否有数据写入错误

---

## 6. 配置验证方法
1. 配置完成后重启DSC和FSR服务
2. 在DSC中创建一个测试流程并发布
3. 查看FSR的领域模板库是否自动生成了对应的模板
4. 验证模板可以正常打开和编辑
5. 尝试将模板推回DSC，验证双向推送正常
