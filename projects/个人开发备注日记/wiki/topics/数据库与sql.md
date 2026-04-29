---
title: "数据库与SQL"
type: topic
created: 2026-04-30
last_updated: 2026-04-30
source_count: 0
confidence: medium
status: active
tags: []
---

# 03 Database Sql

*8 notes grouped from Apple Notes*

---

## DB-GPT GraphRag 源码修改

# DB-GPT GraphRag 源码修改

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p10 -->

<div><h1>DB-GPT GraphRag 源码修改</h1></div>
<div><br></div>
<div>1.packages/dbgpt-ext/src/dbgpt_ext/storage/graph_store/tugraph_store.py</div>
<div><br></div>
<div>222-231</div>
<div><br></div>
<div>2.准备好Tu Graph配置json</div>
<div><br></div>
<div><br></div>
<div>{</div>
<div>    &quotdirectory&quot : &quot/var/lib/lgraph/data&quot,</div>
<div>    &quothost&quot : &quot0.0.0.0&quot,</div>
<div>    &quotport&quot : 7070,</div>
<div>    &quotrpc_port&quot : 9090,</div>
<div>    &quotenable_plugin&quot: true,</div>
<div>    &quotenable_rpc&quot : true,</div>
<div>    &quotbolt_port&quot: 7687,</div>
<div>    &quotenable_ha&quot : false,</div>
<div>    &quotverbose&quot : 1,</div>
<div>    &quotlog_dir&quot : &quot/var/log/lgraph_log&quot,</div>
<div>    &quotdisable_auth&quot : false,</div>
<div>    &quotssl_auth&quot : false,</div>
<div>    &quotserver_key&quot : &quot/usr/local/etc/lgraph/server-key.pem&quot,</div>
<div>    &quotserver_cert&quot : &quot/usr/local/etc/lgraph/server-cert.pem&quot,</div>
<div>    &quotweb&quot : &quot/usr/local/share/lgraph/browser-resource&quot</div>
<div>}</div>
<div><br></div>
<div>从宿主机上挂在该json</div>
<div>docker run -d \</div>
<div>    -p 7070:7070 -p 7687:7687 -p 9090:9090 \</div>
<div>    -v /Users/aiassistant/Projects/OpenSourceProjects/DBGPT/DB-GPT/docker/tugraph_config/lgraph.json:/usr/local/etc/lgraph.json \</div>
<div>    --name tugraph_demo \</div>
<div>    tugraph/tugraph-runtime-centos7:latest \</div>
<div>    lgraph_server -d run</div>
<div><br></div>
<div>docker run -d -p 7070:7070  -p 7687:7687 -p 9090:9090 -v /Users/aiassistant/Projects/OpenSourceProjects/DBGPT/DB-GPT/docker/tugraph_config/lgraph.json:/usr/local/etc/lgraph.json  --name tugraph_demo tugraph/tugraph-runtime-centos7:latest lgraph_server -d run</div>
<div><br></div>
<div><br></div>
<div>3.milvus的服务版本与package版本是要严格一致的</div>
<div><br></div>
<div>4.配置好milvus.yaml 并挂在到对应的docker或cluster中</div>
<div><br></div>
<div>5./Users/aiassistant/Projects/OpenSourceProjects/DBGPT/DB-GPT/packages/dbgpt-ext/src/dbgpt_ext/storage/vector_store/milvus_store.py</div>
<div><br></div>
<div>230～232行</div>
<div>        self.port = milvus_vector_config.get(&quotport&quot) or os.getenv(</div>
<div>            &quotMILVUS_PORT&quot, &quot19530&quot</div>
<div>        )</div>
<div><br></div>
<div><br></div>
<div>293～295<font face=".PingFangUITextSC-Regular">行</font></div>
<div>self._milvus_client = MilvusClient(</div>
<div>            uri=url, token=f&quot{self.username}:{self.password}&quot, db_name=&quotdefault&quot</div>
<div>        )</div>
<div><br></div>
<div><br></div>
<div>383~385行</div>
<div>        self.index_params[&quotparams&quot]=self.index_params_map.get(</div>
<div>            self.index_params.get(&quotindex_type&quot, &quotHNSW&quot), {}</div>
<div>        ).get(&quotparams&quot, {})</div>
<div><br></div>
<div>…需要对底层对象及对应的方法进行替换</div>

---

## DBGPT部署

# DBGPT部署

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p22 -->

<div><h1>DBGPT部署</h1></div>
<div><br></div>
<div>  bash docker/base/build_image.sh</div>
<div><br></div>
<div>docker run -d --ipc host -p 5670:5670 --name dbgpt  eosphorosai/dbgpt:latest dbgpt start webserver --config /app/configs/dbgpt-proxy-tongyi.toml</div>
<div><br></div>
<div><br></div>
<div>挂载大模型</div>
<div>docker run -d \</div>
<div>  --ipc host \</div>
<div>  -p 5670:5670 \</div>
<div>  -v ./models/:/app/models/ \</div>
<div>  --name dbgpt \</div>
<div>  eosphorosai/dbgpt-llama-cpp:latest \</div>
<div>  dbgpt start webserver --config /app/configs/dbgpt-local-llama-cpp-server.toml</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div><br></div>
<div>本地化部署llama cpp模型启动dbgpt</div>
<div><br></div>
<div>后端</div>
<div><br></div>
<div>uv run python packages/dbgpt-app/src/dbgpt_app/dbgpt_server.py --config configs/dbgpt-proxy-tongyi.toml</div>
<div>uv run dbgpt start webserver --config configs/dbgpt-proxy-tongyi.toml</div>
<div><br></div>
<div><br></div>
<div>uv run python packages/dbgpt-app/src/dbgpt_app/dbgpt_server.py --config configs/dbgpt-local-llama-cpp.toml</div>
<div><br></div>
<div>uv run dbgpt start webserver --config configs/dbgpt-local-llama-cpp.toml</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div>尝试运用本地模型</div>
<div>bash docker/base/build_image_amd64.sh --install-mode llama-cpp</div>

---

## Mysql修改密码权限

# Mysql修改密码权限

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p26 -->

<div><h1>Mysql修改密码权限</h1></div>
<div><br></div>
<div>-- 先刷新权限</div>
<div>FLUSH PRIVILEGES;</div>
<div><br></div>
<div>-- 然后修改密码</div>
<div>ALTER USER 'root'@'localhost' IDENTIFIED BY  ‘#ZPL91823zpl';</div>

---

## PGSQL

# PGSQL

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p13 -->

<div><h1>PGSQL</h1></div>
<div><br></div>
<div>超级管理员</div>
<div>psql -U aiassistant -d postgres -W</div>
<div><br></div>
<div>操作用户</div>
<div>psql -U pgsql_admin -d askdata -W</div>
<div><br></div>
<div>授予用户的数据库权限</div>
<div>GRANT ALL PRIVILEGES ON DATABASE askdata TO pgsql_admin;</div>
<div><br></div>
<div>授予用户的schema权限</div>
<div>postgres=# GRANT ALL PRIVILEGES ON SCHEMA public TO pgsql_admin;</div>
<div>GRANT</div>
<div>postgres=# GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pgsql_admin;</div>
<div>GRANT</div>
<div>postgres=# GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pgsql_admin;</div>
<div>GRANT</div>
<div>postgres=# GRANT CREATE ON SCHEMA public TO pgsql_admin;</div>
<div><br></div>
<div><br></div>
<div>创建临时数据库</div>
<div>CREATE DATABASE temp_data_db </div>
<div>WITH </div>
<div>    TEMPLATE = template0</div>
<div>    ENCODING = 'UTF8'</div>
<div>    LC_COLLATE = 'C'</div>
<div>    LC_CTYPE = 'C'</div>
<div>    CONNECTION LIMIT = -1;</div>
<div><br></div>
<div>-- 设置数据库参数优化临时数据操作</div>
<div>ALTER DATABASE temp_data_db SET temp_buffers = '256MB';</div>
<div>ALTER DATABASE temp_data_db SET work_mem = '64MB';</div>
<div>ALTER DATABASE temp_data_db SET maintenance_work_mem = '256MB';</div>
<div><br></div>
<div>ALTER DATABASE temp_data_db SET autovacuum_naptime = ‘10s';</div>
<div>ALTER DATABASE temp_data_db SET autovacuum_vacuum_scale_factor = 0.1;</div>
<div>ALTER DATABASE temp_data_db SET autovacuum_analyze_scale_factor = 0.05;</div>

---

## SELECT bu sub1  product line  product l1  area  avenue  date rq  pay 

# SELECT bu_sub1, product_line, product_l1, area, avenue, date_rq, pay…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p58 -->

<div>SELECT bu_sub1, product_line, product_l1, area, avenue, date_rq, pay, price_now, quantity, type1, um, unit FROM ods_jfcxexcel_shouru_dlt_m WHERE bu_sub1 = '不动产' AND STR_TO_DATE(date_rq, '%Y-%m-%d') &gt= '2025-10-01' AND STR_TO_DATE(date_rq, '%Y-%m-%d') &lt= '2025-10-31'</div>
<div><br></div>
<div><br></div>
<div>SELECT * FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq = \'10月\' AND product_l3 LIKE \'%不动产%\'</div>

---

## SELECT product line  SUM avenue   10000  AS income in 10 thousand yuan 

# SELECT product_line, SUM(avenue / 10000) AS income_in_10_thousand_yuan…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p122 -->

<div>SELECT product_line, SUM(avenue / 10000) AS income_in_10_thousand_yuan, (SUM(avenue / 10000) * 100.0 / (SELECT SUM(avenue / 10000) FROM ods_jfcxexcel_shouru_dlt_m WHERE STR_TO_DATE(date_rq, '%Y-%m-%d') &gt= '2025-01-01' AND STR_TO_DATE(date_rq, '%Y-%m-%d') &lt= '2025-12-31')) AS percentage FROM ods_jfcxexcel_shouru_dlt_m WHERE STR_TO_DATE(date_rq, '%Y-%m-%d') &gt= '2025-01-01' AND STR_TO_DATE(date_rq, '%Y-%m-%d') &lt= '2025-12-31' GROUP BY product_line ORDER BY income_in_10_thousand_yuan DESC</div>

---

## clawdbot onboard --install-daemon

# clawdbot onboard --install-daemon

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p61 -->

<div> clawdbot onboard --install-daemon </div>
<div><br></div>
<div>AIzaSyDgpRvt80hPIRtgdk8NXeluYSIF9e7kIAE</div>
<div><br></div>
<div>channel：</div>
<div><br></div>
<div>1.iMessage done</div>
<div><br></div>
<div>2.飞书：</div>
<div>app_id: YOUR_LARK_APP_ID</div>
<div>App secret: YOUR_LARK_APP_SECRET</div>
<div><br></div>
<div>3.Discord: token: YOUR_DISCORD_BOT_TOKEN</div>
<div>Client ID:YOUR_DISCORD_CLIENT_SECRET</div>
<div>Client Secret:YOUR_DISCORD_CLIENT_SECRET</div>
<div><br></div>
<div>Generated_URL: https://discord.com/oauth2/authorize?client_id=1476783079702925393&amppermissions=117824&ampresponse_type=code&ampredirect_uri=https%3A%2F%2Fdiscord.com%2Foauth2%2Fauthorize%3Fclient_id%3D1476783079702925393&ampintegration_type=0&ampscope=bot+applications.commands<br></div>

---

## 数据库初始化

# 数据库初始化

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p55 -->

<div><h1>数据库初始化</h1></div>
<div><br></div>
<div>./deploy.sh &quot$@&quot</div>
<div><br></div>
<div><br></div>
<div>docker exec askdata-postgres psql -U aiassistant -d askdata -c &quotTRUNCATE TABLE alembic_version;&quot</div>
<div>rm -rf storage/data_migration/alembic_data_migration/alembic</div>
<div>rm -rf deployments/postgresql/postgres-data</div>
<div>cd deployments/postgresql </div>
<div>docker compose down</div>
<div>docker compose up -d</div>
<div><br></div>

---


