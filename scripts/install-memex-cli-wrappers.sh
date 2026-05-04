#!/usr/bin/env bash
# Install memex-claude-vendor.sh and/or memex-claw-vendor.sh into DEST (default ~/bin)
# and create symlinks:
#   memex-claude-{qwen,deepseek,kimi} → memex-claude-vendor
#   memex-claw-{anthropic,dashscope,openrouter,xai,ollama} → memex-claw-vendor
#
# Usage:
#   ./scripts/install-memex-cli-wrappers.sh                          # install all (claude + claw)
#   ./scripts/install-memex-cli-wrappers.sh --target claude           # claude only
#   ./scripts/install-memex-cli-wrappers.sh --target claw             # claw only
#   ./scripts/install-memex-cli-wrappers.sh /usr/local/bin            # custom path (backward compatible)
#   ./scripts/install-memex-cli-wrappers.sh --target claw /usr/local/bin
#
# Then in Memex → AI & CLI settings:
#   - Set claude_cli_binary to memex-claude-qwen (or memex-claw-anthropic, etc.), and
#   - Add the install directory to "Extra PATH" if the dashboard cannot find them,
#     OR use the absolute path shown below.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
DEST_DIR="$HOME/bin"
TARGET="all"  # all | claude | claw

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      shift
      if [[ $# -eq 0 ]]; then echo "Error: --target requires a value (claude|claw)" >&2; exit 1; fi
      TARGET="$1"
      shift
      ;;
    *)
      # Positional arg = destination directory (backward compatible)
      DEST_DIR="$1"
      shift
      ;;
  esac
done

if [[ "$TARGET" != "all" && "$TARGET" != "claude" && "$TARGET" != "claw" ]]; then
  echo "Error: --target must be 'all', 'claude', or 'claw'. Got: $TARGET" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

INSTALLED_CLAUDE=0
INSTALLED_CLAW=0

install_claude() {
  local SRC="$SCRIPT_DIR/memex-claude-vendor.sh"
  if [[ ! -f "$SRC" ]]; then
    echo "Warning: $SRC not found, skipping Claude wrappers." >&2
    return
  fi

  install -m 0755 "$SRC" "$DEST_DIR/memex-claude-vendor"
  for nick in qwen deepseek kimi; do
    ln -sf "memex-claude-vendor" "$DEST_DIR/memex-claude-${nick}"
  done
  INSTALLED_CLAUDE=1
}

install_claw() {
  local SRC="$SCRIPT_DIR/memex-claw-vendor.sh"
  if [[ ! -f "$SRC" ]]; then
    echo "Warning: $SRC not found, skipping Claw wrappers." >&2
    return
  fi

  install -m 0755 "$SRC" "$DEST_DIR/memex-claw-vendor"
  for nick in anthropic dashscope openrouter xai ollama; do
    ln -sf "memex-claw-vendor" "$DEST_DIR/memex-claw-${nick}"
  done
  INSTALLED_CLAW=1
}

case "$TARGET" in
  all)
    install_claude
    install_claw
    ;;
  claude)
    install_claude
    ;;
  claw)
    install_claw
    ;;
esac

REAL_DEST="$(cd "$DEST_DIR" && pwd)"
echo "Installed into: $REAL_DEST"
echo ""

if [[ "$INSTALLED_CLAUDE" == "1" ]]; then
  echo "Claude wrappers:"
  echo "  $REAL_DEST/memex-claude-vendor"
  for nick in qwen deepseek kimi; do
    echo "  $REAL_DEST/memex-claude-${nick} → memex-claude-vendor"
  done
  echo ""
fi

if [[ "$INSTALLED_CLAW" == "1" ]]; then
  echo "Claw wrappers:"
  echo "  $REAL_DEST/memex-claw-vendor"
  for nick in anthropic dashscope openrouter xai ollama; do
    echo "  $REAL_DEST/memex-claw-${nick} → memex-claw-vendor"
  done
  echo ""
fi

echo "Memex settings:"
if [[ "$INSTALLED_CLAUDE" == "1" ]]; then
  echo "  • claude_cli_binary: memex-claude-qwen   (or memex-claude-deepseek / memex-claude-kimi)"
fi
if [[ "$INSTALLED_CLAW" == "1" ]]; then
  echo "  • cli_type: claw, then claude_cli_binary: memex-claw-anthropic (or dashscope / openrouter / xai / ollama)"
fi
echo "  • Extra PATH (one dir per line), if needed:"
echo "      $REAL_DEST"
echo "  • Or use an absolute binary path, e.g."
if [[ "$INSTALLED_CLAUDE" == "1" ]]; then
  echo "      $REAL_DEST/memex-claude-qwen"
fi
if [[ "$INSTALLED_CLAW" == "1" ]]; then
  echo "      $REAL_DEST/memex-claw-anthropic"
fi
echo ""
echo "Smoke test:"
if [[ "$INSTALLED_CLAUDE" == "1" ]]; then
  echo "  $REAL_DEST/memex-claude-qwen --version"
fi
if [[ "$INSTALLED_CLAW" == "1" ]]; then
  echo "  $REAL_DEST/memex-claw-anthropic --version"
fi
