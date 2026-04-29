---
title: "Docker部署模式"
type: technique
created: 2026-04-30
last_updated: 2026-04-30
source_count: 0
confidence: medium
status: active
tags: []
---

# Docker部署模式

> 从 Apple Notes 中提取的 Docker 部署实践

## 1. Nginx 静态站点部署

标准模式：反向代理 + 静态文件挂载

```bash
docker run -d --name <name> -p <host-port>:80 \
  -v <local-dist>:/usr/share/nginx/html:ro \
  -v <nginx.conf>:/etc/nginx/conf.d/default.conf:ro \
  --restart always nginx:latest
```

实例：
- askdata-nginx: 8080→80 (AskdataWeb)
- openclaw-nginx: 3080→80 (OpenClawCollection)

## 2. 数据库部署

### MySQL
```bash
docker run -d --name mysql-server -p 3306:3306 \
  -v /var/lib/mysql_data:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=xxx mysql:latest

# ARM 机器拉取 AMD64 镜像
docker pull --platform linux/amd64 mysql:8.4
```

### MongoDB
```bash
docker pull mongo@sha256:<digest>
```

## 3. 阿里云 Container Registry

### 登录
```bash
docker login --username=<account> crpi-<region>.personal.cr.aliyuncs.com
```

### 推送镜像
```bash
docker tag <image-id> crpi-<region>.personal.cr.aliyuncs.com/<repo>:<tag>
docker push crpi-<region>.personal.cr.aliyuncs.com/<repo>:<tag>
```

### VPC 内网推送
```bash
docker login --username=<account> crpi-<region>-vpc.cn-shanghai.personal.cr.aliyuncs.com
```

## 4. FSR (Askdata) 部署

```bash
cd deployments/deployment_local
cp .env.template .env

# 重启服务
./deploy-local.sh up -d --force-recreate postgres data-migration askdata_backend

# 全量重建
./deploy-local.sh up -d --build --force-recreate --remove-orphans
```

访问入口：
- Askdata: http://127.0.0.1/
- DSC: http://127.0.0.1/dsc-admin/
- Dify: http://127.0.0.1/dify/
- Dashboard: http://127.0.0.1/dash/
- Report: http://127.0.0.1/report/
- Langfuse: http://127.0.0.1:3000/

## 5. Docker 镜像分割与合并

```bash
# 分割 (每1GB)
split -b 1G image.tar "image.tar.part."

# 合并
cat image.tar.part.* > merged.tar
```

## 6. Docker 镜像加速

```bash
tee /etc/systemd/system/docker.service.d/mirror.conf <<-'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/docker daemon -H fd:// --registry-mirror=<address>
EOF
```

## 7. Tmux 会话管理

```bash
tmux new -d -s mysession
tmux ls
tmux attach -t mysession
```

## 相关页面

- [[数据库操作速查]] — 数据库查询
- [[Git工作流速查]] — 版本控制

