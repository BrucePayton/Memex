#!/usr/bin/env bash
# Install memex-claude-vendor.sh into ~/bin (or DEST) and create symlinks
# memex-claude-qwen, memex-claude-deepseek, memex-claude-kimi → memex-claude-vendor.
#
# Usage:
#   ./scripts/install-memex-cli-wrappers.sh
#   ./scripts/install-memex-cli-wrappers.sh /usr/local/bin
#
# Then in Memex → AI & CLI settings:
#   - Set claude_cli_binary to memex-claude-qwen (or deepseek/kimi), and
#   - Add the install directory to "Extra PATH" if the dashboard cannot find them,
#     OR use the absolute path shown below for claude_cli_binary.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/memex-claude-vendor.sh"
DEST_DIR="${1:-$HOME/bin}"

if [[ ! -f "$SRC" ]]; then
  echo "Cannot find $SRC" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
install -m 0755 "$SRC" "$DEST_DIR/memex-claude-vendor"

for nick in qwen deepseek kimi; do
  ln -sf "memex-claude-vendor" "$DEST_DIR/memex-claude-${nick}"
done

REAL_DEST="$(cd "$DEST_DIR" && pwd)"
echo "Installed:"
echo "  $REAL_DEST/memex-claude-vendor"
echo "  $REAL_DEST/memex-claude-qwen → memex-claude-vendor"
echo "  $REAL_DEST/memex-claude-deepseek → memex-claude-vendor"
echo "  $REAL_DEST/memex-claude-kimi → memex-claude-vendor"
echo ""
echo "Memex settings:"
echo "  • claude_cli_binary: memex-claude-qwen   (or memex-claude-deepseek / memex-claude-kimi)"
echo "  • Extra PATH (one dir per line), if needed:"
echo "      $REAL_DEST"
echo "  • Or use an absolute binary path, e.g."
echo "      $REAL_DEST/memex-claude-qwen"
echo ""
echo "Smoke test:"
echo "  $REAL_DEST/memex-claude-qwen --version"
