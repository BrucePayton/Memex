---
title: "Docker部署"
type: topic
created: 2026-04-30
last_updated: 2026-04-30
source_count: 0
confidence: medium
status: active
tags: []
---

# 02 Docker Deployment

*8 notes grouped from Apple Notes*

---

## 1768  docker rm -f askdata-nginx

# 1768  docker rm -f askdata-nginx

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p57 -->

<div> 1768  docker rm -f askdata-nginx</div>
<div> 1769  docker run -d   --name askdata-nginx   -p 8080:8080   -v /var/projects/AskdataWeb/askdata_web/dist:/usr/share/nginx/html:ro   -v /var/projects/AskdataWeb/askdata_web/nginx.conf:/etc/nginx/conf.d/default.conf:ro   --restart always   nginx:latest</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div><br></div>
<div>docker rm -f openclaw-nginx</div>
<div>docker run -d \</div>
<div>  --name openclaw-nginx \</div>
<div>  -p 3080:80 \</div>
<div>  -v /var/projects/OpenClawCollection/pajf-clawhub/dist:/usr/share/nginx/html:ro \</div>
<div>  -v /var/projects/OpenClawCollection/pajf-clawhub/nginx.conf:/etc/nginx/nginx.conf:ro \</div>
<div>  --restart always \</div>
<div>  nginx:latest</div>
<div><br></div>
<div><br></div>
<div>docker run -d --name mysql-server -p 3306:3306 -v /var/lib/mysql_data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=123456 mysql:latest</div>
<div><br></div>
<div>docker run -d \</div>
<div>  --name openclaw-nginx \</div>
<div>  -p 3080:80 \</div>
<div>  -v /Users/aiassistant/Projects/MyProjects/OpenClawCaseCollection/dist:/usr/share/nginx/html:ro \</div>
<div>  -v /Users/aiassistant/Projects/MyProjects/OpenClawCaseCollection/nginx.conf:/etc/nginx/nginx.conf:ro \</div>
<div>  --restart always \</div>
<div>  nginx:latest</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div>Open claw token YOUR_GITHUB_PAT</div>
<div><br></div>
<div>git remote set-url origin https://<b>BrucePayton</b>:YOUR_GITHUB_PAT@github.com/BrucePayton/pajf-clawhub.git<br></div>
<div><br></div>
<div><br></div>
<div>docker pull mongo@sha256:e0df0dfdeb4824f6586a7d9ee9048de516846ff528396b7ec89be2d2dc6f7efb</div>

---

## 1  登录阿里云 Container Registry

# 1. 登录阿里云 Container Registry

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p47 -->

<div><b>1. 登录阿里云 Container Registry</b></div>
<div>$ docker login --username=马就到了-vnlxvf crpi-ofpooywmr74yngd2.cn-shanghai.personal.cr.aliyuncs.com</div>
<div><br></div>
<div>密码：@ZPL91823zpl</div>
<div>用于登录的用户名为阿里云账号全名，密码为开通服务时设置的密码。</div>
<div>您可以在访问凭证页面修改凭证密码。</div>
<div>注意：使用 RAM 用户（子账号）登录镜像仓库时，不支持企业别名带有英文半角句号（.）。</div>
<div><b>2. 从Registry中拉取镜像</b></div>
<div>$ docker pull crpi-ofpooywmr74yngd2.cn-shanghai.personal.cr.aliyuncs.com/askdata_platform/askdata:[镜像版本号]</div>
<div><b>3. 将镜像推送到Registry</b></div>
<div>$ docker login --username=马就到了-vnlxvf crpi-ofpooywmr74yngd2.cn-shanghai.personal.cr.aliyuncs.com</div>
<div>$ docker tag [ImageId] crpi-ofpooywmr74yngd2.cn-shanghai.personal.cr.aliyuncs.com/askdata_platform/askdata:[镜像版本号]</div>
<div>$ docker push crpi-ofpooywmr74yngd2.cn-shanghai.personal.cr.aliyuncs.com/askdata_platform/askdata:[镜像版本号]</div>
<div>请根据实际镜像信息替换示例中的[ImageId]和[镜像版本号]参数。</div>
<div><b>4. 选择合适的镜像仓库地址</b></div>
<div>从ECS推送镜像时，可以选择使用镜像仓库内网地址。推送速度将得到提升并且将不会损耗您的公网流量。</div>
<div>如果您使用的机器位于VPC网络，请使用 crpi-ofpooywmr74yngd2-vpc.cn-shanghai.personal.cr.aliyuncs.com 作为Registry的域名登录。</div>
<div><b>5. 示例</b></div>
<div>使用&quotdocker tag&quot命令重命名镜像，并将它通过专有网络地址推送至Registry。</div>
<div>$ docker images</div>
<div>REPOSITORY                                                         TAG                 IMAGE ID            CREATED             VIRTUAL SIZE</div>
<div>registry.aliyuncs.com/acs/agent                                    0.7-dfb6816         37bb9c63c8b2        7 days ago          37.89 MB</div>
<div>$ docker tag 37bb9c63c8b2 crpi-ofpooywmr74yngd2-vpc.cn-shanghai.personal.cr.aliyuncs.com/acs/agent:0.7-dfb6816</div>
<div>使用 &quotdocker push&quot 命令将该镜像推送至远程。</div>
<div>$ docker push crpi-ofpooywmr74yngd2-vpc.cn-shanghai.personal.cr.aliyuncs.com/acs/agent:0.7-dfb6816</div>
<div><br></div>
<div># VPC网络尝试</div>
<div>docker login --username=马就到了-vnlxvf crpi-ofpooywmr74yngd2-vpc.cn-shanghai.personal.cr.aliyuncs.com</div>
<div><br></div>
<div># Amd64镜像</div>
<div>docker tag aa3 crpi-ofpooywmr74yngd2.cn-shanghai.personal.cr.aliyuncs.com/askdata_platform/askdata:pgsql-amd64-v0.1</div>
<div>docker push crpi-ofpooywmr74yngd2.cn-shanghai.personal.cr.aliyuncs.com/askdata_platform/askdata:pgsql-amd64-v0.1</div>

---

## DOCKER CONFIG   DOCKER CONFIG - HOME  docker 

# DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p46 -->

<div>DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}</div>

---

## FSR部署

# FSR部署

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p144 -->

<div><h1>FSR</h1><h1>部署</h1><h1><br></h1></div>
<div>cd deployments/deployment_local</div>
<div><br></div>
<div>cp .env.template .env</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div># 重启平台系统容器<br></div>
<div>./deploy-local.sh up -d --force-recreate postgres data-migration askdata_backend</div>
<div><br></div>
<div># 重构镜像<br></div>
<div>./deploy-local.sh up -d --build --force-recreate --remove-orphans</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div># langfuse-web fix</div>
<div>cd deployments/deployment_local</div>
<div>docker compose -f docker-compose.base.yaml -f docker-compose.langfuse.yaml up -d langfuse-web</div>
<div>docker inspect --format='{{.State.Health.Status}}' langfuse-web</div>
<div><br></div>
<div><br></div>
<div># 初始化<br></div>
<ol>
<li><b>改密后「</b><b>password authentication failed for user keycloak</b><b>」</b><br>若 .env 里 KEYCLOAK_DB_* 和<b>已初始化过的</b>库里密码不一致，必须先 <b>./deploy-local.sh reset-keycloak-db</b>，再 <b>./deploy-local.sh up -d</b>；只 up 不会改库内密码。<br></li>
</ol>
<div><br></div>
<div><br></div>
<div><h2>如果你现在本机容器已起，我建议马上执行这三条完成实库回归：</h2><h2><br></h2></div>
<div>cd deployments/deployment_local</div>
<div>./scripts/run-keycloak-data-migrations.sh</div>
<div>./scripts/verify-keycloak-data-migration.sh</div>
<div>./scripts/run-keycloak-data-migration-acceptance.sh</div>
<div><br></div>
<div><br></div>
<div><b><h2>何时用哪个命令</h2></b><b><h2><br></h2></b></div>
<ul>
<li><b>只改</b><b> .env</b>：./deploy-local.sh recreate</li>
<li><b>改前端代码</b><b> / Dockerfile / nginx </b><b>路由配置</b>：./deploy-local.sh rebuild ...</li>
<li><b>全栈统一强制更新</b>（最省心但重）：./deploy-local.sh rebuild</li>
</ul>
<div><br></div>
<div>除 Langfuse（http://127.0.0.1:3000/）外，当前其他前端入口是：<br></div>
<ul>
<li>Askdata 主前端：http://127.0.0.1/</li>
<li>DSC 前端：http://127.0.0.1/dsc-admin/</li>
<li>DSC 兼容跳转：http://127.0.0.1/dsc/（会重定向到 /dsc-admin/）<br></li>
<li>Dify Web：http://127.0.0.1/dify/</li>
<li>Dashboard 前端：http://127.0.0.1/dash/</li>
<li>Report 前端：http://127.0.0.1/report/</li>
</ul>
<div>如果你希望我再给你一版 localhost 域名形式（http://localhost/...）我也可以直接列出来。<br></div>
<div><br></div>
<div>已用 <b>bash -n deploy-local.sh</b> 做过语法检查。<br></div>
<div><b>你本地若仍见</b><b> 410</b>：在 deployment_local 执行 <b>./deploy-local.sh reload-edge</b>，或 <b>docker compose … restart edge-nginx</b>，再访问 <b>http://localhost/dify/</b>（端口与 .env 中 <b>EDGE_HTTP_PORT</b> 一致）<br></div>
<div><br></div>
<div><br></div>

---

##   1  启动服务器 可选 tmux new 会自动启动 

# # 1. 启动服务器（可选，tmux new 会自动启动）

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p51 -->

<div># 1. 启动服务器（可选，tmux new 会自动启动）</div>
<div>tmux start-server</div>
<div><br></div>
<div># 2. 创建会话（会自动保存）</div>
<div>tmux new -d -s mysession  # -d 不附加，直接后台运行</div>
<div><br></div>
<div># 3. 验证</div>
<div>tmux ls</div>
<div># 应该看到：mysession: 1 windows (created ...)</div>
<div><br></div>
<div># 4. 连接</div>
<div>tmux attach -t mysession</div>

---

## docker pull --platform linux amd64 mysql 8 4

# docker pull --platform linux/amd64 mysql:8.4

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p117 -->

<div>docker pull --platform linux/amd64 mysql:8.4</div>

---

## docker容器分割与合并

# docker容器分割与合并

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p23 -->

<div><h1>docker容器分割与合并</h1></div>
<div><br></div>
<div># 将tar包拆分为每个1GB的部分</div>
<div>split -b 1G image.tar &quotimage.tar.part.&quot</div>
<div><br></div>
<div># 或者指定不同的后缀</div>
<div>split -b 512M image.tar &quotimage_part_&quot</div>
<div><br></div>
<div># 查看生成的文件</div>
<div>ls -lh image.tar.part.*</div>
<div><br></div>
<div> # 合并</div>
<div>cat dbgpt.tar.part.* &gt dbgpt_merged.tar</div>

---

## tee  etc systemd system docker service d mirror conf   - EOF 

# tee /etc/systemd/system/docker.service.d/mirror.conf <<-'EOF'

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p147 -->

<div>tee /etc/systemd/system/docker.service.d/mirror.conf &lt&lt-'EOF'</div>
<div>[Service]</div>
<div>ExecStart=</div>
<div>ExecStart=/usr/bin/docker daemon -H fd:// --registry-mirror=&ltyour accelerate address&gt</div>
<div>EOF</div>

---


