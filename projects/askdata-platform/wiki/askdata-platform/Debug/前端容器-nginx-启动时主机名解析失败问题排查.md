---
title: "前端容器 nginx 启动时主机名解析失败问题排查"
type: analysis
created: 2026-05-07
last_updated: 2026-05-07
source_count: 0
confidence: medium
status: active
tags:
  - nginx
  - docker
  - deployment
  - debug
  - askdata-frontend
---

---
title: 前端容器 nginx 启动时主机名解析失败问题排查
date: 2026-05-07
tags: [nginx, docker, deployment, debug, askdata-frontend]
category: Debug
status: resolved
---

## 问题描述

部署时出现 `askdata_platform_frontend` 容器 unhealthy 导致依赖失败的问题，错误日志显示：

```
nginx: [emerg] host not found in upstream "askdata_backend" in /etc/nginx/conf.d/default.conf:35
```

## 根因分析

### 问题根因

前端容器的 nginx 配置中使用了硬编码的 proxy_pass：

```nginx
location /api/ {
    proxy_pass http://askdata_backend:5555/api/;
    ...
}
```

**关键问题**：
- nginx 在配置加载阶段（启动时）就会尝试解析主机名 `askdata_backend`
- 此时 `askdata_backend` 容器可能还没启动或还没在 Docker DNS 中注册
- 导致 nginx 启动失败

### 部署时序问题

1. Docker Compose 按依赖顺序启动容器
2. `askdata_frontend` 可能在 `askdata_backend` 完全就绪前启动
3. nginx 立即尝试解析 upstream 主机名
4. 解析失败 → nginx 启动失败 → 容器 unhealthy

## 解决方案

### 修改 nginx 配置

在 `web/nginx.default.conf` 中进行两处关键修改：

#### 1. 添加 Docker DNS 解析器

```nginx
server {
    listen 80;
    server_name _;
    client_max_body_size 100M;
    
    # 使用 Docker 内置的 DNS 解析器
    resolver 127.0.0.11 valid=10s ipv6=off;
    ...
}
```

#### 2. 使用变量形式的 proxy_pass

```nginx
location /api/ {
    # 使用变量形式，nginx 会在请求时才解析主机名
    set $upstream_api http://askdata_backend:5555;
    proxy_pass $upstream_api/api/;
    
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    proxy_buffering off;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

### 技术原理

- **变量延迟解析**：当 proxy_pass 使用变量时，nginx 不会在配置加载时解析主机名，而是在实际处理请求时才解析
- **Docker DNS**：`127.0.0.11` 是 Docker 内置的 DNS 服务器，负责解析容器名
- **valid=10s**：DNS 解析结果缓存 10 秒，避免频繁解析
- **ipv6=off**：禁用 IPv6 解析，减少潜在问题

## 验证结果

修改并重新部署后：

✅ 所有容器健康运行
✅ 前端容器不再因主机名解析失败而 unhealthy
✅ 堆栈完整部署成功
✅ API 代理功能正常

容器状态验证：
```
askdata_platform_backend    Up (healthy)
askdata_platform_frontend   Up (healthy)
askdata-edge-nginx          Up (healthy)
langfuse-web                Up (healthy)
...
```

## 相关知识

### nginx upstream 解析时机

| 配置方式 | 解析时机 | 适用场景 |
|---------|---------|---------|
| `proxy_pass http://service:port;` | 配置加载时（启动时） | 服务地址固定，启动时一定可用 |
| `proxy_pass $variable;` | 请求处理时 | 动态服务，启动时可能不可用 |

### Docker Compose 健康检查依赖

为避免类似问题，可在 docker-compose 中配置：

```yaml
services:
  askdata_frontend:
    depends_on:
      askdata_backend:
        condition: service_healthy
```

这样可以确保前端在后端完全健康后才启动。

## 参考资料

- [[nginx-配置重复指令导致启动失败问题排查]]
- [[历史会话加载卡死-useeffect-循环重载与主线程阻塞]]

