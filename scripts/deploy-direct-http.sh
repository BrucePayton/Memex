#!/usr/bin/env bash
# ── Memex MCP — Direct HTTP mode (no nginx proxy) ────────────────────
# Usage:
#   bash scripts/deploy-direct-http.sh              # local
#   bash scripts/deploy-direct-http.sh user@server   # remote (via SSH)
#
# What it does:
#   1. Sets MEMEX_MCP_TRANSPORT=http in .env
#   2. Exposes port 8081 on the host in docker-compose.yml
#   3. Rebuilds and restarts memex-mcp
#   4. MCP is accessible at http://<host>:8081/
#
# Use for internal networks where you can open port 8081.
# Simpler than nginx proxy but requires firewall changes.
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} $1"; }
ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
err()  { echo -e "${RED}  ❌ $1${NC}" >&2; }

# ── Args ──
REMOTE="${1:-}"
MCP_PORT=8081

# Helper: run command locally or via SSH
run() {
    if [ -n "$REMOTE" ]; then
        ssh "$REMOTE" "$@"
    else
        eval "$@"
    fi
}

# Determine project root
if [ -n "$REMOTE" ]; then
    DEPLOY_DIR=$(run "cd ~ && ls -d Memex memex 2>/dev/null | head -1" || echo "")
    if [ -z "$DEPLOY_DIR" ]; then
        err "Cannot find Memex directory on remote."
        exit 1
    fi
    PROJECT_ROOT="$HOME/$DEPLOY_DIR"
    cd_cmd="cd $PROJECT_ROOT &&"
else
    if [ ! -f "docker-compose.yml" ]; then
        for d in ~/Memex ~/memex .; do
            if [ -f "$d/docker-compose.yml" ]; then
                cd "$d"
                break
            fi
        done
        if [ ! -f "docker-compose.yml" ]; then
            err "docker-compose.yml not found. Run from Memex root."
            exit 1
        fi
    fi
    PROJECT_ROOT="$(pwd)"
    cd_cmd="cd $PROJECT_ROOT &&"
fi

HOST="${REMOTE:-localhost}"
MCP_URL="http://${HOST%%@*}:${MCP_PORT}/"

# ── Step 1: Configure .env ──
log "Step 1/4 — Configuring MCP direct HTTP mode in .env"
run "${cd_cmd} if grep -q 'MEMEX_MCP_TRANSPORT' .env 2>/dev/null; then
    sed -i '' 's/MEMEX_MCP_TRANSPORT=.*/MEMEX_MCP_TRANSPORT=http/' .env 2>/dev/null ||
    sed -i 's/MEMEX_MCP_TRANSPORT=.*/MEMEX_MCP_TRANSPORT=http/' .env
else
    echo 'MEMEX_MCP_TRANSPORT=http' >> .env
fi"
ok "MEMEX_MCP_TRANSPORT=http set in .env"

# ── Step 2: Expose port 8081 ──
log "Step 2/4 — Exposing port ${MCP_PORT} in docker-compose.yml"
# Check if port is already exposed
if run "${cd_cmd} grep -q 'ports:' docker-compose.yml 2>/dev/null && \
    ${cd_cmd} grep -q '${MCP_PORT}' docker-compose.yml 2>/dev/null"; then
    ok "Port ${MCP_PORT} already exposed"
else
    # Add ports section to memex-mcp if not present
    run "${cd_cmd} if ! grep -q 'ports:' docker-compose.yml; then
        sed -i '' '/memex-mcp:/,/healthcheck:/{/expose:/i\\
    ports:\\
      - \"${MCP_PORT}:${MCP_PORT}\"\\

        }' docker-compose.yml 2>/dev/null || \
        sed -i '/memex-mcp:/,/healthcheck:/{/expose:/i\\
    ports:\\
      - \"${MCP_PORT}:${MCP_PORT}\"\\

        }' docker-compose.yml 2>/dev/null
        echo '  ⚠️  Port exposure added to docker-compose.yml — review if needed'
    fi"
fi

# ── Step 3: Build & Restart ──
log "Step 3/4 — Building and restarting memex-mcp"
run "${cd_cmd} docker compose build memex-mcp && docker compose up -d memex-mcp"
log "Waiting for memex-mcp to start..."
sleep 5
MCP_STATUS=$(run "${cd_cmd} docker inspect -f '{{.State.Status}}' memex-mcp 2>/dev/null || echo 'unknown'")
if [ "$MCP_STATUS" = "running" ]; then
    ok "memex-mcp is running"
else
    warn "memex-mcp status: $MCP_STATUS"
    run "${cd_cmd} docker logs memex-mcp --tail 5" 2>/dev/null || true
fi

# ── Step 4: Verify ──
log "Step 4/4 — Verifying MCP HTTP endpoint"
if [ -n "$REMOTE" ]; then
    HTTP_CODE=$(ssh "$REMOTE" "curl -s -o /dev/null -w '%{http_code}' http://localhost:${MCP_PORT}/ 2>/dev/null" || echo "000")
else
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:${MCP_PORT}/ 2>/dev/null || echo "000")
fi
if [ "$HTTP_CODE" != "000" ] && [ "$HTTP_CODE" -lt 500 ]; then
    ok "MCP HTTP endpoint responding at $MCP_URL (HTTP $HTTP_CODE)"
else
    warn "HTTP check returned $HTTP_CODE — verify port ${MCP_PORT} is open"
fi

# ── Summary ──
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Direct HTTP MCP deployment complete${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  MCP URL:  $MCP_URL"
echo "  Mode:     Direct HTTP (port ${MCP_PORT})"
echo "  Note:     Ensure port ${MCP_PORT} is open in firewall"
echo ""
if [ -n "$REMOTE" ]; then
    echo "  Firewall (on remote server):"
    echo "    # Ubuntu/UFW:"
    echo "    ssh $REMOTE 'sudo ufw allow ${MCP_PORT}/tcp'"
    echo "    # CentOS/firewalld:"
    echo "    ssh $REMOTE 'sudo firewall-cmd --add-port=${MCP_PORT}/tcp --permanent && sudo firewall-cmd --reload'"
    echo ""
fi
echo "  Connect with Claude Code:"
echo "    claude mcp add memex -- npx @anthropic-ai/mcp-remote --url $MCP_URL"
echo ""
echo "  Connect with Claude Desktop (edit claude_desktop_config.json):"
echo '    {'
echo '      "mcpServers": {'
echo '        "memex": {'
echo '          "command": "npx",'
echo '          "args": ["@anthropic-ai/mcp-remote", "--url", "'"$MCP_URL"'"]'
echo '        }'
echo '      }'
echo '    }'
echo ""
echo "  Revert to stdio mode:"
echo "    sed -i '' 's/MEMEX_MCP_TRANSPORT=http/MEMEX_MCP_TRANSPORT=stdio/' .env && ./deploy.sh restart"
echo ""
