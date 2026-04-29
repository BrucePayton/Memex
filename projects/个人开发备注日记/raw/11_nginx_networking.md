# 11 Nginx Networking

*1 notes grouped from Apple Notes*

---

## 基于路径的Nginx的反向代理设计

# 基于路径的Nginx的反向代理设计

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p24 -->

<div><h1>基于路径的Nginx的反向代理设计</h1></div>
<div><font face=".PingFangUITextSC-Regular"><br></font></div>
<div><font face=".PingFangUITextSC-Regular"># 查看80端口占用</font></div>
<div>lsof -i :80<font face=".PingFangUITextSC-Regular"><br></font></div>
<div><font face=".PingFangUITextSC-Regular"><br></font></div>
<div><font face=".PingFangUITextSC-Regular"><br></font></div>
<div><font face=".PingFangUITextSC-Regular">我来详细解释如何设计这种基于路径区分的</font>Nginx反向代理配置。</div>
<div><br></div>
<div>## 1. 完整的Nginx配置示例</div>
<div><br></div>
<div>```nginx</div>
<div>http {</div>
<div>    upstream service1_backend {</div>
<div>        server localhost:3001;</div>
<div>        # 如果是多实例可以这样配置</div>
<div>        # server service1:3000;  # Docker服务名</div>
<div>    }</div>
<div><br></div>
<div>    upstream service2_backend {</div>
<div>        server localhost:3002;</div>
<div>    }</div>
<div><br></div>
<div>    upstream service3_backend {</div>
<div>        server localhost:3003;</div>
<div>    }</div>
<div><br></div>
<div>    # ... 其他服务</div>
<div><br></div>
<div>    server {</div>
<div>        listen 80;</div>
<div>        server_name your-domain.com;</div>
<div>        </div>
<div>        # 通用代理配置</div>
<div>        proxy_set_header Host $host;</div>
<div>        proxy_set_header X-Real-IP $remote_addr;</div>
<div>        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;</div>
<div>        proxy_set_header X-Forwarded-Proto $scheme;</div>
<div><br></div>
<div>        # 服务1 - 管理后台</div>
<div>        location /service1/ {</div>
<div>            proxy_pass http://service1_backend/;</div>
<div>            # 如果需要路径重写</div>
<div>            rewrite ^/service1/(.*)$ /$1 break;</div>
<div>        }</div>
<div><br></div>
<div>        # 服务2 - API服务</div>
<div>        location /service2/ {</div>
<div>            proxy_pass http://service2_backend/;</div>
<div>            rewrite ^/service2/(.*)$ /$1 break;</div>
<div>            </div>
<div>            # API特殊配置</div>
<div>            proxy_connect_timeout 30s;</div>
<div>            proxy_send_timeout 30s;</div>
<div>            proxy_read_timeout 30s;</div>
<div>        }</div>
<div><br></div>
<div>        # 服务3 - 静态文件服务</div>
<div>        location /service3/ {</div>
<div>            proxy_pass http://service3_backend/;</div>
<div>            rewrite ^/service3/(.*)$ /$1 break;</div>
<div>            </div>
<div>            # 静态文件缓存配置</div>
<div>            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {</div>
<div>                expires 1y;</div>
<div>                add_header Cache-Control &quotpublic, immutable&quot;</div>
<div>            }</div>
<div>        }</div>
<div><br></div>
<div>        # 默认路由（可选）</div>
<div>        location / {</div>
<div>            # 可以指向默认服务或返回404</div>
<div>            return 404 &quotNot Found&quot;</div>
<div>            # 或者重定向到某个服务</div>
<div>            # return 302 /service1/;</div>
<div>        }</div>
<div><br></div>
<div>        # 健康检查端点</div>
<div>        location /health {</div>
<div>            access_log off;</div>
<div>            return 200 &quothealthy\n&quot;</div>
<div>            add_header Content-Type text/plain;</div>
<div>        }</div>
<div>    }</div>
<div>}</div>
<div>```</div>
<div><br></div>
<div>## 2. Docker Compose配置</div>
<div><br></div>
<div>```yaml</div>
<div>version: '3.8'</div>
<div><br></div>
<div>services:</div>
<div>  nginx:</div>
<div>    image: nginx:alpine</div>
<div>    ports:</div>
<div>      - &quot80:80&quot</div>
<div>    volumes:</div>
<div>      - ./nginx.conf:/etc/nginx/nginx.conf</div>
<div>      - ./logs:/var/log/nginx</div>
<div>    depends_on:</div>
<div>      - service1</div>
<div>      - service2</div>
<div>      - service3</div>
<div>    networks:</div>
<div>      - app-network</div>
<div><br></div>
<div>  service1:</div>
<div>    image: your-app1:latest</div>
<div>    ports:</div>
<div>      - &quot3001:3000&quot</div>
<div>    environment:</div>
<div>      - PORT=3000</div>
<div>      - BASE_URL=/service1</div>
<div>    networks:</div>
<div>      - app-network</div>
<div>    healthcheck:</div>
<div>      test: [&quotCMD&quot, &quotcurl&quot, &quot-f&quot, &quothttp://localhost:3000/health&quot]</div>
<div>      interval: 30s</div>
<div>      timeout: 10s</div>
<div>      retries: 3</div>
<div><br></div>
<div>  service2:</div>
<div>    image: your-app2:latest</div>
<div>    ports:</div>
<div>      - &quot3002:3000&quot</div>
<div>    environment:</div>
<div>      - PORT=3000</div>
<div>      - BASE_URL=/service2</div>
<div>    networks:</div>
<div>      - app-network</div>
<div><br></div>
<div>  service3:</div>
<div>    image: your-app3:latest</div>
<div>    ports:</div>
<div>      - &quot3003:3000&quot</div>
<div>    environment:</div>
<div>      - PORT=3000</div>
<div>      - BASE_URL=/service3</div>
<div>    networks:</div>
<div>      - app-network</div>
<div><br></div>
<div>networks:</div>
<div>  app-network:</div>
<div>    driver: bridge</div>
<div>```</div>
<div><br></div>
<div>## 3. 前端应用配置调整</div>
<div><br></div>
<div>### React应用（vite.config.js）</div>
<div>```javascript</div>
<div>export default {</div>
<div>  base: '/service1/',  // 设置基础路径</div>
<div>  server: {</div>
<div>    proxy: {</div>
<div>      '/api': 'http://localhost:3001'</div>
<div>    }</div>
<div>  }</div>
<div>}</div>
<div>```</div>
<div><br></div>
<div>### Vue应用（vue.config.js）</div>
<div>```javascript</div>
<div>module.exports = {</div>
<div>  publicPath: process.env.NODE_ENV === 'production' </div>
<div>    ? '/service1/'</div>
<div>    : '/',</div>
<div>  devServer: {</div>
<div>    proxy: {</div>
<div>      '/api': {</div>
<div>        target: 'http://localhost:3001',</div>
<div>        changeOrigin: true</div>
<div>      }</div>
<div>    }</div>
<div>  }</div>
<div>}</div>
<div>```</div>
<div><br></div>
<div>## 4. 路径设计最佳实践</div>
<div><br></div>
<div>### 清晰的路径命名</div>
<div>```nginx</div>
<div># 好的命名</div>
<div>location /admin/ {}      # 管理后台</div>
<div>location /api/ {}        # API接口</div>
<div>location /auth/ {}       # 认证服务</div>
<div>location /storage/ {}    # 文件存储</div>
<div>location /analytics/ {}  # 数据分析</div>
<div>location /payment/ {}    # 支付服务</div>
<div><br></div>
<div># 避免的命名</div>
<div>location /s1/ {}         # 不明确</div>
<div>location /app1/ {}       # 不够具体</div>
<div>```</div>
<div><br></div>
<div>### 版本化管理（如果需要）</div>
<div>```nginx</div>
<div># API版本化</div>
<div>location /api/v1/ {</div>
<div>    proxy_pass http://api_v1_backend/;</div>
<div>}</div>
<div><br></div>
<div>location /api/v2/ {</div>
<div>    proxy_pass http://api_v2_backend/;</div>
<div>}</div>
<div>```</div>
<div><br></div>
<div>## 5. 高级配置选项</div>
<div><br></div>
<div>### 负载均衡</div>
<div>```nginx</div>
<div>upstream service1_backend {</div>
<div>    server service1:3000 weight=3;  # 权重</div>
<div>    server service1_replica:3000 weight=1;</div>
<div>    </div>
<div>    # 负载均衡策略</div>
<div>    least_conn;  # 最少连接</div>
<div>    # ip_hash;   # IP哈希</div>
<div>}</div>
<div>```</div>
<div><br></div>
<div>### 限流配置</div>
<div>```nginx</div>
<div>location /api/ {</div>
<div>    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;</div>
<div>    </div>
<div>    limit_req zone=api burst=20 nodelay;</div>
<div>    proxy_pass http://service2_backend/;</div>
<div>}</div>
<div>```</div>
<div><br></div>
<div>### 缓存配置</div>
<div>```nginx</div>
<div>location /static/ {</div>
<div>    proxy_pass http://service3_backend/;</div>
<div>    </div>
<div>    proxy_cache static_cache;</div>
<div>    proxy_cache_valid 200 302 1h;</div>
<div>    proxy_cache_valid 404 1m;</div>
<div>    </div>
<div>    add_header X-Cache-Status $upstream_cache_status;</div>
<div>}</div>
<div>```</div>
<div><br></div>
<div>## 6. 环境变量管理</div>
<div><br></div>
<div><font face=".PingFangUITextSC-Regular">创建环境配置文件：</font><br></div>
<div>```bash</div>
<div># .env</div>
<div>NGINX_PORT=80</div>
<div>SERVICE1_PORT=3001</div>
<div>SERVICE2_PORT=3002</div>
<div>SERVICE1_BASE_PATH=/admin</div>
<div>SERVICE2_BASE_PATH=/api</div>
<div>```</div>
<div><br></div>
<div><font face=".PingFangUITextSC-Regular">在</font>Docker Compose中使用：</div>
<div>```yaml</div>
<div>environment:</div>
<div>  - BASE_URL=${SERVICE1_BASE_PATH}</div>
<div>  - PORT=3000</div>
<div>```</div>
<div><br></div>
<div><font face=".PingFangUITextSC-Regular">这样的设计可以让你：</font><br></div>
<div>- 清晰地通过路径区分不同服务</div>
<div>- 灵活地调整路由规则</div>
<div>- 便于扩展和维护</div>
<div>- 支持健康检查和监控</div>
<div><br></div>
<div><br></div>
<div># 测试主页</div>
<div>curl http://localhost:8080/</div>

---

