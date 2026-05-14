# Memex MCP 服务 — 服务器部署与接入指南

## 概述

本文档指导如何将 Memex MCP 服务部署到远程服务器，并从本地客户端（Claude Code、Claude Desktop、Cursor 等）接入使用。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    远程服务器                              │
│                                                         │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────┐ │
│  │  Nginx   │    │   Dashboard   │    │   MCP Server │ │
│  │  :80/:443│───▶│   :8000       │    │   :8081      │ │
│  │          │    │               │    │              │ │
│  │ /api/*   │    └───────────────┘    └──────┬───────┘ │
│  │ /mcp     │────────────────────────────────┘         │
│  │ /        │                                          │
│  └──────────┘                                          │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ HTTPS /mcp
                         │
              ┌──────────┴──────────┐
              │    本地客户端         │
              │  Claude Code / IDE   │
              └─────────────────────┘
```

所有外部请求统一通过 Nginx（端口 80 或 443），MCP 服务通过 `/mcp` 路径暴露。

---

## 前提条件

| 项目 | 要求 |
|------|------|
| 操作系统 | Linux (Ubuntu 22.04+ / Debian 12+ / AlmaLinux 9+) |
| Docker | Docker Engine 24.0+ 或 Docker Desktop |
| Docker Compose | v2.20+ |
| 域名 | 用于 HTTPS 访问（推荐） |
| SSL 证书 | Let's Encrypt 或自有证书（可选但推荐） |
| 防火墙 | 开放 80 (HTTP) 和 443 (HTTPS) 端口 |

---

## 1. 服务器端部署

### 1.1 克隆项目

```bash
git clone https://github.com/your-org/memex.git
cd memex
```

### 1.2 配置 .env

复制示例配置并修改：

```bash
cp .env.example .env
```

```bash
# .env — 服务器端配置
MEMEX_VERSION=0.1.0

# 对外端口（80 = HTTP, 推荐配合 Nginx + HTTPS 使用 443）
MEMEX_PORT=80

# 数据持久化目录
MEMEX_WIKI_DIR=./wiki
MEMEX_RAW_DIR=./raw
MEMEX_PROJECTS_DIR=./projects
MEMEX_GIT_DIR=.git
MEMEX_DATA_DIR=./data
MEMEX_SSL_DIR=./ssl

# 默认激活项目（留空使用 projects.json 中的 active 设置）
MEMEX_ACTIVE_PROJECT=

# Git 自动提交
MEMEX_GIT_AUTO_COMMIT=true

# 时区
MEMEX_TZ=Asia/Shanghai
```

### 1.3 启用 HTTPS（推荐）

获取 SSL 证书后，修改 `nginx/nginx.conf`，取消 HTTPS server 块的注释并填入证书路径：

```nginx
server {
    listen       443 ssl http2;
    server_name  your-domain.com;
    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Health check
    location /health {
        access_log off;
        add_header Content-Type application/json;
        return 200 '{"status":"ok"}';
    }

    # API proxy → dashboard
    location /api/ {
        proxy_pass http://memex-dashboard;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection "";
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # MCP Server (Streamable HTTP + SSE)
    location /mcp {
        proxy_pass http://memex-mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Static files
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Root → dashboard
    location / {
        proxy_pass http://memex-dashboard;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

同时将证书挂载到 `docker-compose.yml`：

```yaml
nginx:
  volumes:
    - ./ssl:/etc/nginx/ssl:ro
```

### 1.4 启动服务

```bash
docker compose up -d --build
```

### 1.5 验证部署

```bash
# 检查容器状态
docker compose ps

# 测试 Dashboard
curl -s http://your-domain.com/ -o /dev/null -w "HTTP %{http_code}\n"

# 测试 MCP 端点（应返回 400 或 405，说明服务在运行）
curl -s http://your-domain.com/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

### 1.6 防火墙配置

```bash
# UFW (Ubuntu)
ufw allow 80/tcp
ufw allow 443/tcp

# firewalld (CentOS/RHEL)
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

---

## 2. 客户端接入

部署完成后，MCP 服务的统一接入地址为：

| 协议 | 地址 |
|------|------|
| HTTP | `http://your-domain.com/mcp` |
| HTTPS | `https://your-domain.com/mcp` |

### 2.1 Claude Code（CLI）

```bash
# HTTPS 模式（推荐）
claude mcp add memex https://your-domain.com/mcp

# HTTP 模式（仅本地测试）
claude mcp add memex http://your-domain.com/mcp

# 验证
claude mcp list
```

添加后，Claude Code 启动时会自动连接并加载所有 60+ 个 MCP 工具。

### 2.2 Claude Desktop

编辑配置文件：

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "memex": {
      "url": "https://your-domain.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### 2.3 Cursor

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "memex": {
      "url": "https://your-domain.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

或在 Settings → MCP Servers 中添加。

### 2.4 Windsurf (Codium)

编辑 Windsurf MCP 配置：

```json
{
  "mcpServers": {
    "memex": {
      "url": "https://your-domain.com/mcp"
    }
  }
}
```

### 2.5 Python 客户端（MCP SDK）

```python
from mcp import ClientSession, StreamableHttpTransport
import asyncio

async def main():
    async with ClientSession(
        "https://your-domain.com/mcp",
        transport=StreamableHttpTransport()
    ) as session:
        await session.initialize()

        # 列出所有工具
        tools = await session.list_tools()
        for tool in tools.tools:
            print(f"  {tool.name}: {tool.description}")

        # 调用工具示例
        result = await session.call_tool("list_projects", arguments={})
        print(result.content)

asyncio.run(main())
```

### 2.6 Node.js 客户端

```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const client = new Client({
  name: "memex-test",
  version: "0.1.0",
}, { capabilities: {} });

const transport = new StreamableHTTPClientTransport(
  new URL("https://your-domain.com/mcp")
);

await client.connect(transport);

const { tools } = await client.listTools();
console.log(tools.map(t => t.name));

const result = await client.callTool({
  name: "list_projects",
  arguments: {},
});
console.log(result);

await client.close();
```

---

## 3. 安全加固

### 3.1 基本认证（Basic Auth）

在 `nginx/nginx.conf` 中为 `/mcp` 添加认证：

```nginx
location /mcp {
    auth_basic "MCP Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://memex-mcp;
    # ... 其他 proxy 配置保持不变 ...
}
```

生成密码文件：

```bash
# 安装 htpasswd 工具
apt install apache2-utils -y

# 创建用户
htpasswd -c /path/to/ssl/.htpasswd memex-user

# 在 docker-compose.yml 中挂载
nginx:
  volumes:
    - ./ssl/.htpasswd:/etc/nginx/.htpasswd:ro
```

客户端连接时需要携带认证信息：

```bash
# Claude Code — 需要手动在 URL 中携带（或通过代理层处理）
# 推荐在 Nginx 层配置 Bearer Token 认证
```

### 3.2 Bearer Token 认证（推荐）

```nginx
location /mcp {
    # 要求请求头包含 Authorization: Bearer <token>
    if ($http_authorization !~* "^Bearer your-secret-token-here$") {
        return 401;
    }
    proxy_pass http://memex-mcp;
    # ... 其他 proxy 配置 ...
}
```

客户端请求示例：

```bash
curl -s https://your-domain.com/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-token-here" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### 3.3 IP 白名单

```nginx
location /mcp {
    allow 192.168.1.0/24;    # 内部网络
    allow 10.0.0.0/8;        # 公司网络
    deny all;
    proxy_pass http://memex-mcp;
    # ...
}
```

### 3.4 Rate Limiting

```nginx
# http 块中定义限流规则
limit_req_zone $binary_remote_addr zone=mcp_rate:10m rate=30r/m;

server {
    location /mcp {
        limit_req zone=mcp_rate burst=5 nodelay;
        proxy_pass http://memex-mcp;
        # ...
    }
}
```

---

## 4. 故障排查

### 4.1 容器状态检查

```bash
# 查看所有容器状态
docker compose ps

# 查看容器日志
docker logs memex-dashboard --tail 50
docker logs memex-mcp --tail 50
docker logs memex-nginx --tail 50
```

### 4.2 MCP 端点无响应

```bash
# 1. 确认 MCP 容器运行
docker compose ps memex-mcp

# 2. 测试直连（容器内）
docker exec memex-mcp python3 -c "
import urllib.request
r = urllib.request.urlopen('http://localhost:8081/mcp', timeout=5)
print('MCP OK')
"

# 3. 测试 Nginx 代理
curl -v https://your-domain.com/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

### 4.3 502 Bad Gateway

```bash
# Nginx 找不到 upstream 服务
# 检查 Dashboard 和 MCP 是否健康
docker compose ps

# 重启 Nginx（刷新 DNS）
docker compose restart nginx

# 检查 Nginx 日志
docker logs memex-nginx --tail 20
```

### 4.4 SSL 证书问题

```bash
# 验证证书
openssl s_client -connect your-domain.com:443 -servername your-domain.com </dev/null 2>/dev/null | openssl x509 -noout -dates

# 检查 Nginx 配置语法
docker exec memex-nginx nginx -t
```

### 4.5 网络连通性

```bash
# 从 Nginx 容器测试到 Dashboard 的连通性
docker exec memex-nginx wget -q -O- http://memex-dashboard:8000/api/schedules

# 从 Nginx 容器测试到 MCP 的连通性
docker exec memex-nginx wget -q -O- --post-data='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' http://memex-mcp:8081/mcp
```

---

## 5. 维护操作

### 5.1 更新版本

```bash
git pull
docker compose up -d --build
```

### 5.2 备份数据

```bash
# 备份所有持久化数据
tar czf memex-backup-$(date +%Y%m%d).tar.gz \
  wiki/ raw/ projects/ .git/ .dashboard-settings.json .memex/ projects.json data/
```

### 5.3 查看日志

```bash
# 实时日志
docker compose logs -f

# 仅 MCP 日志
docker compose logs -f memex-mcp
```

### 5.4 停止服务

```bash
docker compose down
```

---

## 6. 可用工具清单

Memex MCP 服务提供 **60 个工具**和 **3 个资源**，详见 [mcp-configuration.md](mcp-configuration.md)。

快速查看可用工具（连接成功后）：

```
/ MCP tools
→ list_projects, get_instructions, list_pages, read_page, search, ...
```
