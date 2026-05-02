---
title: "Keycloak认证"
type: "concept"
created: "2026-04-30"
last_updated: "2026-05-02"
source_count: 0
confidence: medium
status: active
tags: []
---

# 12 Keycloak Auth

*1 notes grouped from Apple Notes*

---

## Keycloak

# Keycloak

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p17 -->

<div><b> Keycloak</b></div>
<div><br></div>
<div><br></div>
<div># 打包amd64架构基础</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div># 进入 Keycloak容器</div>
<div>docker exec -it upbeat_wilbur /bin/bash</div>
<div><br></div>
<div># 或者使用管理API清除缓存</div>
<div>kcadm.sh update realms/zp_test --body '{&quotcache&quot: {&quotclearUserCache&quot: true}}'</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div><br></div>
<div>./kcadm.sh config credentials \</div>
<div>  --server http://localhost:8080 \</div>
<div>  --realm zp_test \</div>
<div>  --user admin \</div>
<div>  --password admin123</div>

---

## 相关页面

- [[Docker部署]] — Keycloak 容器部署笔记
- [[Nginx网络]] — 反向代理配置
- [[API密钥与凭证]] — 认证凭据管理
- [[知识库索引]]
