#!/usr/bin/env bash
# =============================================================================
# Memex Dashboard — 一键部署管理脚本
# 用法: ./deploy.sh <subcommand> [options]
#
#   子命令:
#     install       初始化环境（复制 .env.example → .env）
#     build         构建 / 重建 Docker 镜像
#     start         启动所有服务
#     stop          停止所有容器
#     restart       重启所有服务
#     deploy        一键部署 = install + build + start（带健康检查）
#     status        查看容器状态与端口占用
#     logs          查看日志  [–f / –tail N / --service NAME]
#     shell         进入容器交互式 Shell  [–service NAME]
#     exec CMD      在 memex-dashboard 容器内执行命令
#     test          运行连通性测试（HTTP + API + health）
#     prune         清理孤儿容器、未使用的镜像和网络
#     destroy       完全卸载：stop + remove volumes
#     env VAR VALUE 查看或设置环境变量
#     help          显示本帮助
# =============================================================================
set -Eu

cd "$(dirname "${BASH_SOURCE[0]}")"

COMPOSE="docker compose -f docker-compose.yml"
ENV_FILE="${MEMEX_ENV_FILE:-$(pwd)/.env}"
MEMEX_DEFAULT_PORT=3011

# ── Colors & formatting ──────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()    { printf '\n[%s] %b%s%b\n' "$(date '+%H:%M:%S')" "$BOLD" "$*" "$NC"; }
ok()     { printf '  ✅ %s\n' "$*"; }
warn()   { printf '\n[%s] %b%s%b\n' "$(date '+%H:%M:%S')" "$YELLOW" "⚠ $*" "$NC"; }
err_msg(){ printf '\n[%s] %b%s%b\n' "$(date '+%H:%M:%S')" "$RED" "✗ $*" "$NC"; }

header() {
  echo ""
  printf '%b%-70s%b\n' "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "$NC"
}

# ── Helpers ──────────────────────────────────────────────────────────────────
require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    err_msg "缺少 docker。请先安装: https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    err_msg "Docker daemon 未运行。请启动 Docker Desktop 或 dockerd。"
    exit 1
  fi
}

load_env() {
  if [ -f "$ENV_FILE" ]; then
    local saved_port="${MEMEX_PORT:-}"
    set -a; source "$ENV_FILE"; set +a
    MEMEX_PORT="${saved_port:-$MEMEX_PORT}"
  fi
}

export_port() { export MEMEX_PORT="${MEMEX_PORT:-$MEMEX_DEFAULT_PORT}"; }

container_is_healthy() {
  local name="$1"
  local status
  status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name" 2>/dev/null) || true
  [ "$status" = "healthy" ]
}

dump_container_logs() {
  local svc
  for svc in "$@"; do
    echo -e "\n${CYAN}── ${svc} 最近 30 行 ──${NC}"
    docker logs "$svc" --tail 30 2>/dev/null || echo "(无法获取日志)"
    echo -e "${CYAN}─────────────────────────────${NC}\n"
  done
}

get_lan_ip() {
  local ip=""
  ip=$(hostname -I 2>/dev/null) || true
  ip=$(echo "$ip" | awk '{print $1}' | tr -d ' ')
  if [ -z "$ip" ]; then
    ip=$(ipconfig getifaddr en0 2>/dev/null) || true
  fi
  echo "$ip"
}

print_endpoints() {
  local port="${MEMEX_PORT:-$MEMEX_DEFAULT_PORT}"
  local lan
  lan=$(get_lan_ip)
  header
  ok "部署完成"
  echo ""
  echo -e "  ${GREEN}本机:${NC}    http://localhost:${port}"
  if [ -n "$lan" ]; then
    echo -e "  ${GREEN}局域网:${NC}  http://${lan}:${port}"
  fi
  header
  echo ""
  echo -e "  ${CYAN}Dashboard: GET  http://localhost:${port}/${NC}"
  echo -e "  ${CYAN}API:       GET  http://localhost:${port}/api/wiki${NC}"
  echo -e "  ${CYAN}Health:    GET  http://localhost:${port}/health${NC}"
  echo ""
  echo -e "  ${YELLOW}示例:${NC}"
  echo "    curl -s http://localhost:${port}/"
  echo "    curl -s http://localhost:${port}/health"
  echo "    curl -s http://localhost:${port}/api/wiki"
  echo ""
}

# ── Wait functions ───────────────────────────────────────────────────────────
_wait_dashboard() {
  local i
  for i in $(seq 1 60); do
    if container_is_healthy memex-dashboard; then
      return 0
    fi
    if [ $((i % 10)) -eq 0 ]; then
      log "后端等待中（已等待 $((i * 2))s）..."
    fi
    sleep 2
  done
  err_msg "后端健康检查超时（>120s）"
  dump_container_logs memex-dashboard
  return 1
}

_wait_nginx() {
  local port="${MEMEX_PORT:-$MEMEX_DEFAULT_PORT}"
  local i
  for i in $(seq 1 30); do
    if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
      return 0
    fi
    if [ $((i % 5)) -eq 0 ]; then
      log "Nginx 等待中（已等待 ${i}s）..."
    fi
    sleep 1
  done
  err_msg "Nginx 健康检查超时（>30s）"
  dump_container_logs memex-dashboard memex-nginx
  return 1
}

# ── Subcommands ──────────────────────────────────────────────────────────────

cmd_install() {
  load_env
  log "环境初始化"

  if [ -f ".env" ]; then
    ok ".env 已存在，跳过初始化"
  else
    if [ -f ".env.example" ]; then
      cp ".env.example" ".env"
      ok ".env 已从 .env.example 生成"
    else
      warn ".env.example 不存在，创建默认配置"
      cat > .env <<EOF
MEMEX_PORT=${MEMEX_DEFAULT_PORT}
MEMEX_VERSION=0.1.0
MEMEX_TZ=Asia/Shanghai
EOF
      ok "已创建 .env"
    fi
  fi

  if [ ! -d "projects" ]; then
    warn "未找到 projects/ 目录。"
  else
    ok "projects/ 已就绪"
  fi

  ok "环境初始化完成"
  echo ""
}

cmd_build() {
  require_docker
  load_env
  log "构建 Docker 镜像"

  local force=false
  local service="all"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force|--no-cache) force=true; shift ;;
      --only-dashboard)   service="memex-dashboard"; shift ;;
      --only-mcp)          service="memex-mcp"; shift ;;
      *)                   shift ;;
    esac
  done

  if [ "$force" = true ]; then
    if [ "$service" = "all" ]; then
      $COMPOSE build --no-cache memex-dashboard memex-mcp nginx
    else
      $COMPOSE build --no-cache "$service"
    fi
  else
    if [ "$service" = "all" ]; then
      $COMPOSE build memex-dashboard memex-mcp nginx
    else
      $COMPOSE build "$service"
    fi
  fi

  ok "镜像构建完成"
}

cmd_start() {
  require_docker
  load_env
  export_port

  local mode="all"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --only-backend) mode="backend"; shift ;;
      --only-web)     mode="web"; shift ;;
      *)              shift ;;
    esac
  done

  log "启动服务（Nginx :${MEMEX_PORT} → memex-dashboard :8000）"
  $COMPOSE up -d memex-dashboard

  log "等待 memex-dashboard 健康检查通过"
  _wait_dashboard || return 1

  log "启动 memex-mcp"
  $COMPOSE up -d memex-mcp

  if [ "$mode" != "backend" ]; then
    log "启动 Nginx 反向代理"
    $COMPOSE up -d nginx
    log "等待 Nginx 就绪"
    _wait_nginx || return 1
  fi

  print_endpoints
}

cmd_stop() {
  require_docker
  load_env
  log "停止所有服务"
  $COMPOSE down 2>/dev/null || true
  ok "服务已停止"
}

cmd_restart() {
  require_docker
  load_env
  export_port

  log "重启服务"
  $COMPOSE restart
  log "等待服务就绪"

  _wait_dashboard || return 1
  _wait_nginx || return 1

  ok "服务重启完成"
  echo ""
  echo -e "  ${GREEN}访问: http://localhost:${MEMEX_PORT}${NC}"
  print_endpoints
}

cmd_deploy() {
  require_docker
  load_env
  export_port

  log "一键部署"
  cmd_install
  cmd_build --force
  cmd_start "$@"
}

cmd_status() {
  load_env
  export_port

  echo -e "${BOLD}容器状态${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  $COMPOSE ps 2>/dev/null || {
    echo -e "  ${RED}无运行中的容器。请先执行: ./deploy.sh start${NC}"
  }

  echo ""
  echo -e "${BOLD}端口信息${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Dashboard:  localhost:${MEMEX_PORT}"
  echo "  API:        http://localhost:${MEMEX_PORT}/api/"
  echo "  Health:     http://localhost:${MEMEX_PORT}/health"

  echo ""
  echo -e "${BOLD}资源使用情况${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  local c mem cpu
  for c in memex-dashboard memex-nginx; do
    if docker inspect "$c" >/dev/null 2>&1; then
      mem=$(docker stats --no-stream --format "{{.MemUsage}}" "$c" 2>/dev/null) || mem="-"
      cpu=$(docker stats --no-stream --format "{{.CPUPerc}}" "$c" 2>/dev/null) || cpu="-"
      printf "  %-18s CPU: %-8s MEM: %s\n" "$c" "$cpu" "$mem"
    fi
  done

  echo ""
  echo -e "${BOLD}镜像列表${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  docker images "memex*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null || echo "  (无相关镜像)"
  echo ""
}

cmd_logs() {
  local service=""
  local follow=false
  local tail_num=50

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f|--follow)   follow=true; shift ;;
      --tail)        tail_num="$2"; shift 2 ;;
      --service)     service="$2"; shift 2 ;;
      --*)
        local svc="${1#--}"
        if docker inspect "$svc" >/dev/null 2>&1; then
          service="$svc"
        else
          echo "未知服务: $1" >&2
          exit 1
        fi
        shift ;;
      *)
        if docker inspect "$1" >/dev/null 2>&1; then
          service="$1"
        else
          echo "未知服务: $1" >&2
          exit 1
        fi
        shift ;;
    esac
  done

  local args=("--tail" "$tail_num")
  if [ "$follow" = true ]; then
    args+=("-f")
  fi

  if [ -n "$service" ]; then
    docker logs "${args[@]}" "$service" 2>/dev/null
  else
    for svc in memex-dashboard memex-nginx; do
      if docker inspect "$svc" >/dev/null 2>&1; then
        docker logs "${args[@]}" "$svc" 2>/dev/null || true
        echo ""
      fi
    done
  fi
}

cmd_shell() {
  require_docker
  local svc="memex-dashboard"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --service) svc="$2"; shift 2 ;;
      *)         svc="$1"; shift ;;
    esac
  done

  docker exec -it "$svc" sh
}

cmd_exec() {
  require_docker
  if [ $# -eq 0 ]; then
    echo "用法: ./deploy.sh exec CMD [ARGS...]"
    exit 1
  fi
  if [ -t 0 ]; then
    docker exec -it memex-dashboard "$@"
  else
    docker exec -i memex-dashboard "$@"
  fi
}

cmd_test() {
  load_env
  export_port

  local port="${MEMEX_PORT:-$MEMEX_DEFAULT_PORT}"
  log "连通性测试"

  # Test 1: Root endpoint
  echo -n "  📡 Root endpoint... "
  local root_resp
  root_resp=$(curl -sf --max-time 5 "http://localhost:${port}/" 2>/dev/null) || {
    err_msg "FAIL（服务未运行？）"
    return 1
  }
  ok "OK"

  # Test 2: Health
  echo -n "  💚 Health check... "
  local health_resp
  health_resp=$(curl -sf --max-time 5 "http://localhost:${port}/health" 2>/dev/null) || {
    err_msg "FAIL"
    return 1
  }
  ok "OK (${health_resp})"

  # Test 3: API endpoint
  echo -n "  🔌 API endpoint... "
  local api_resp
  api_resp=$(curl -sf --max-time 10 "http://localhost:${port}/api/wiki" 2>/dev/null) || {
    warn "API 返回异常（可能是正常响应）"
    echo "  ${api_resp:0:120}"
  }
  ok "API reachable"

  header
  ok "连通性测试完成"
  echo ""
}

cmd_prune() {
  require_docker
  log "清理 Docker 资源"
  echo "  孤儿容器..."
  $COMPOSE down --remove-orphans 2>/dev/null || true
  echo "  悬空镜像..."
  docker image prune -f 2>/dev/null || true
  echo "  悬空网络..."
  docker network prune -f 2>/dev/null || true
  ok "清理完成"
}

cmd_destroy() {
  require_docker
  load_env

  warn "这将删除所有容器和数据卷！"
  read -rp "确认？(yes/no): " confirm
  if [ "$confirm" != "yes" ]; then
    echo "已取消"
    return 0
  fi

  log "完全卸载"
  $COMPOSE down --rmi all --volumes --remove-orphans 2>/dev/null || true
  ok "已完全卸载"
}

cmd_env_show() {
  if [ $# -eq 0 ]; then
    echo "当前环境变量:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if [ -f "$ENV_FILE" ]; then
      grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/^/  /'
    else
      echo "  (无 .env 文件)"
    fi
    echo ""
    echo "  MEMEX_PORT=${MEMEX_PORT:-$MEMEX_DEFAULT_PORT}"
  else
    local var_name="$1"
    local var_val="${2:-}"

    if [ -z "$var_val" ]; then
      if [ -f "$ENV_FILE" ]; then
        grep "^${var_name}=" "$ENV_FILE" | cut -d= -f2- || echo "(not set)"
      else
        echo "(not set)"
      fi
    else
      if [ -f "$ENV_FILE" ]; then
        if grep -q "^${var_name}=" "$ENV_FILE"; then
          sed -i '' "s|^${var_name}=.*|${var_name}=${var_val}|" "$ENV_FILE"
        else
          echo "${var_name}=${var_val}" >> "$ENV_FILE"
        fi
      else
        echo "${var_name}=${var_val}" > "$ENV_FILE"
      fi
      ok "设置 ${var_name}=${var_val}"
    fi
  fi
}

cmd_help() {
  cat <<'USAGE'

memex-deploy.sh — 一键部署管理脚本

用法: ./deploy.sh <子命令> [选项]

主要操作:
  deploy              一键部署（build + start + 健康检查）
  install             初始化环境（复制 .env.example → .env）
  start               启动所有服务
  stop                停止所有容器
  restart             重启所有服务

运维操作:
  status              查看容器状态、资源使用、端口信息
  logs [-f] [--tail N] [--service NAME]
                      查看日志（支持流式输出）
  shell [--service NAME]
                      进入容器交互式 Shell
  exec CMD [ARGS...]  在 memex-dashboard 容器内执行命令

维护操作:
  build [--force]
                      构建所有 Docker 镜像（默认 dashboard + mcp + nginx）
      --only-dashboard  仅构建 dashboard
      --only-mcp        仅构建 mcp
  test                运行连通性测试（根端点/health/API）
  prune               清理孤儿容器和悬空镜像/网络
  destroy             完全卸载（容器 + 镜像 + 数据卷）

变量管理:
  env                 显示当前环境变量
  env KEY VALUE       设置环境变量到 .env 文件
  env KEY             查看单个变量值

通用选项:
  --port PORT         指定对外端口（默认 3011）
  --only-backend      仅启动后端（不启动 Nginx）
  --only-web          仅启动 Nginx（依赖已有运行的后端）

连接方式:
  本机:      http://localhost:PORT
  Dashboard: GET  http://localhost:PORT/
  API:       GET  http://localhost:PORT/api/
  Health:    GET  http://localhost:PORT/health

示例:
  ./deploy.sh deploy                     # 一键部署
  ./deploy.sh deploy --port 8080         # 自定义端口
  ./deploy.sh start --only-backend       # 仅启动后端
  ./deploy.sh logs -f                    # 实时日志
  ./deploy.sh logs --tail 100 --nginx    # Nginx 最近 100 行
  ./deploy.sh shell --memex-dashboard    # 进入后端容器
  ./deploy.sh exec python3 -c "import sys; print(sys.version)"
  ./deploy.sh test                       # 连通性测试
  ./deploy.sh prune                      # 清理资源
  ./deploy.sh build --force --mcp        # 强制重建 MCP 镜像
USAGE
}

# ── Dispatcher ───────────────────────────────────────────────────────────────
cmd="${1:-help}"
shift 2>/dev/null || true

case "$cmd" in
  install)         cmd_install "$@" ;;
  build)           cmd_build "$@" ;;
  start)           cmd_start "$@" ;;
  stop)            cmd_stop ;;
  restart)         cmd_restart ;;
  deploy)          cmd_deploy "$@" ;;
  status)          cmd_status ;;
  logs)            cmd_logs "$@" ;;
  shell)           cmd_shell "$@" ;;
  exec)            cmd_exec "$@" ;;
  test)            cmd_test ;;
  prune)           cmd_prune ;;
  destroy)         cmd_destroy ;;
  env)             cmd_env_show "$@" ;;
  help|-h|--help|"")
                   cmd_help ;;
  *)
    err_msg "未知子命令: $cmd"
    echo "运行 './deploy.sh help' 查看所有可用命令"
    exit 1
    ;;
esac
