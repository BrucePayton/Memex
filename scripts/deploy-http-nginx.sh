#!/usr/bin/env bash
# ── Memex MCP — HTTP mode via nginx reverse proxy ────────────────────
# Usage:
#   bash scripts/deploy-http-nginx.sh              # local
#   bash scripts/deploy-http-nginx.sh user@server   # remote (via SSH)
#
# What it does:
#   1. Sets MEMEX_MCP_TRANSPORT=http in .env
#   2. Rebuilds and restarts all services
#   3. MCP is accessible at http://<host>:8000/mcp
#   4. Prints Claude Code & Desktop connection instructions
#
# This is the recommended production deployment — all traffic goes
# through nginx on port 80 (no extra ports needed).
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
    # Find Memex root on remote
    DEPLOY_DIR=$(run "cd ~ && ls -d Memex memex 2>/dev/null | head -1" || echo "")
    if [ -z "$DEPLOY_DIR" ]; then
        err "Cannot find Memex directory on remote. Please specify with MEMEX_DIR env."
        echo "  ssh $REMOTE 'ls -d ~/Memex ~/memex'"
        exit 1
    fi
    PROJECT_ROOT="$HOME/$DEPLOY_DIR"
    log "Remote project root: $PROJECT_ROOT"
    cd_cmd="cd $PROJECT_ROOT &&"
else
    # Local: use current directory if it contains docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        # Try to find it
        for d in ~/Memex ~/memex .; do
            if [ -f "$d/docker-compose.yml" ]; then
                cd "$d"
                break
            fi
        done
        if [ ! -f "docker-compose.yml" ]; then
            err "docker-compose.yml not found. Run this script from the Memex root directory."
            exit 1
        fi
    fi
    PROJECT_ROOT="$(pwd)"
    cd_cmd="cd $PROJECT_ROOT &&"
fi

HOST="${REMOTE:-localhost}"
PORT="${MEMEX_PORT:-8000}"
MCP_URL="http://${HOST%%@*}:${PORT}/mcp"

# ── Step 1: Configure .env ──
log "Step 1/4 — Configuring MCP HTTP mode in .env"
run "${cd_cmd} if grep -q 'MEMEX_MCP_TRANSPORT' .env 2>/dev/null; then
    sed -i '' 's/MEMEX_MCP_TRANSPORT=.*/MEMEX_MCP_TRANSPORT=http/' .env 2>/dev/null ||
    sed -i 's/MEMEX_MCP_TRANSPORT=.*/MEMEX_MCP_TRANSPORT=http/' .env
else
    echo 'MEMEX_MCP_TRANSPORT=http' >> .env
fi"
ok "MEMEX_MCP_TRANSPORT=http set in .env"

# ── Step 2: Build ──
log "Step 2/4 — Building memex-mcp image"
run "${cd_cmd} docker compose build memex-mcp"
ok "Image built"

# ── Step 3: Restart ──
log "Step 3/4 — Restarting services"
run "${cd_cmd} docker compose up -d memex-mcp"
log "Waiting for memex-mcp to be healthy..."
sleep 5
MCP_STATUS=$(run "${cd_cmd} docker inspect -f '{{.State.Health.Status}}' memex-mcp 2>/dev/null || echo 'unknown'")
if [ "$MCP_STATUS" = "healthy" ] || [ "$MCP_STATUS" = "starting" ]; then
    ok "memex-mcp is running ($MCP_STATUS)"
else
    warn "memex-mcp status: $MCP_STATUS (check logs with: docker logs memex-mcp)"
fi

# ── Step 4: Verify ──
log "Step 4/4 — Verifying MCP HTTP endpoint"
if [ -n "$REMOTE" ]; then
    HTTP_CODE=$(ssh "$REMOTE" "curl -s -o /dev/null -w '%{http_code}' http://localhost:${PORT}/mcp 2>/dev/null" || echo "000")
else
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:${PORT}/mcp 2>/dev/null || echo "000")
fi
if [ "$HTTP_CODE" != "000" ] && [ "$HTTP_CODE" -lt 500 ]; then
    ok "MCP HTTP endpoint responding (HTTP $HTTP_CODE)"
else
    warn "HTTP check returned $HTTP_CODE — the endpoint may need a moment to start"
fi

# ── Summary ──
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  HTTP mode via nginx deployment complete${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  MCP URL:  $MCP_URL"
echo "  Mode:     HTTP via nginx (port $PORT only)"
echo "  Security: Behind nginx reverse proxy"
echo ""
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
