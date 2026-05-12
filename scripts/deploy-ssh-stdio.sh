#!/usr/bin/env bash
# ── Memex MCP — SSH stdio tunnel deployment ──────────────────────────
# Usage:
#   bash scripts/deploy-ssh-stdio.sh user@your-server.com
#   bash scripts/deploy-ssh-stdio.sh user@your-server.com /path/to/memex   # explicit repo path
#
# What it does:
#   1. Verifies SSH connectivity to remote host
#   2. Confirms memex-mcp container is running on remote
#   3. Registers MCP with Claude Code via SSH stdio tunnel
#   4. Verifies the registration
#
# No ports need to be opened on the server — everything goes through SSH.
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
if [ -z "$REMOTE" ]; then
    echo "Usage: $0 user@server.com [repo_path]"
    echo ""
    echo "Registers Memex MCP on a remote server with Claude Code via SSH stdio tunnel."
    echo ""
    echo "Examples:"
    echo "  $0 root@192.168.1.100"
    echo "  $0 deploy@memex.example.com /opt/memex"
    exit 1
fi

REPO_PATH="${2:-/home/appuser/Memex}"  # default path on remote

# ── Step 1: Verify SSH ──
log "Step 1/4 — Verifying SSH connectivity to ${REMOTE}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE" "echo ok" >/dev/null 2>&1; then
    err "SSH connection failed. Check your SSH key setup:"
    echo "  ssh-keygen -t ed25519"
    echo "  ssh-copy-id $REMOTE"
    exit 1
fi
ok "SSH connection OK"

# ── Step 2: Verify remote MCP container ──
log "Step 2/4 — Checking memex-mcp container on remote"
CONTAINER_STATUS=$(ssh "$REMOTE" "docker inspect -f '{{.State.Status}}' memex-mcp 2>/dev/null || echo 'not_found'")

if [ "$CONTAINER_STATUS" = "not_found" ]; then
    err "memex-mcp container not found on remote."
    echo ""
    echo "First deploy Memex to the remote server, then re-run this script."
    echo ""
    echo "Quick deploy on remote:"
    echo "  ssh $REMOTE 'cd $REPO_PATH && ./deploy.sh deploy'"
    exit 1
fi

if [ "$CONTAINER_STATUS" != "running" ]; then
    warn "memex-mcp container exists but is '$CONTAINER_STATUS'. Attempting to start..."
    ssh "$REMOTE" "docker start memex-mcp 2>/dev/null || docker compose -f $REPO_PATH/docker-compose.yml up -d memex-mcp" || {
        err "Failed to start memex-mcp. Deploy Memex first."
        exit 1
    }
    sleep 3
fi
ok "memex-mcp is running on remote"

# ── Step 3: Check if already registered ──
log "Step 3/4 — Checking existing Claude Code MCP registration"
EXISTING=$(claude mcp list 2>/dev/null | grep memex || true)
if [ -n "$EXISTING" ]; then
    warn "memex MCP is already registered in Claude Code:"
    echo "  $EXISTING"
    echo ""
    read -rp "Remove existing registration and re-register? [y/N] " confirm
    if [[ "$confirm" =~ ^[Yy] ]]; then
        claude mcp remove memex 2>/dev/null || true
        ok "Removed existing registration"
    else
        echo "Exiting. Current registration remains."
        exit 0
    fi
fi

# ── Step 4: Register ──
log "Step 4/4 — Registering MCP with Claude Code via SSH tunnel"

CMD="python3 $REPO_PATH/mcp-server/memex_mcp.py"
FULL_CMD="ssh $REMOTE \"docker exec -i memex-mcp $CMD\""

claude mcp add memex -- "$FULL_CMD"

ok "MCP registered as 'memex' in Claude Code"

# ── Summary ──
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  SSH stdio tunnel MCP deployment complete${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Remote:  $REMOTE"
echo "  Server:  $REPO_PATH"
echo "  Mode:    SSH stdio tunnel (no open ports needed)"
echo ""
echo "  Next: Open Claude Code and run:"
echo "    claude"
echo ""
echo "  Then ask: \"List my Memex projects.\""
echo ""
echo "  To remove later:"
echo "    claude mcp remove memex"
echo ""
