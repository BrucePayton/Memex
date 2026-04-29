#!/usr/bin/env bash
# Memex helper: load ~/.claude-*-env then exec Claude Code CLI.
# The dashboard subprocess does not see shell aliases — install symlinks via
# scripts/install-memex-cli-wrappers.sh and set claude_cli_binary to e.g.
# memex-claude-qwen (with install dir on Extra PATH) or an absolute path.
#
# Symlink names drive which env file is sourced:
#   memex-claude-qwen      -> ~/.claude-qwen-env
#   memex-claude-deepseek  -> ~/.claude-deepseek-env
#   memex-claude-kimi      -> ~/.claude-kimi-env
#
# Optional env:
#   MEMEX_CLAUDE_BIN              Absolute path to claude if not on PATH
#   MEMEX_VENDOR_SKIP_PERMISSIONS Set to 0 to omit --dangerously-skip-permissions
set -euo pipefail

invoke_name="$(basename "$0")"

pick_env_for_name() {
  case "$invoke_name" in
    *qwen*) echo "${HOME}/.claude-qwen-env" ;;
    *deepseek*) echo "${HOME}/.claude-deepseek-env" ;;
    *kimi*) echo "${HOME}/.claude-kimi-env" ;;
    *vendor*) echo "" ;;
    *) echo "" ;;
  esac
}

env_file="$(pick_env_for_name)"
if [[ -z "$env_file" ]]; then
  echo "memex-claude-vendor: invoke via symlink memex-claude-{qwen,deepseek,kimi} (see scripts/install-memex-cli-wrappers.sh). Got: $invoke_name" >&2
  exit 2
fi

if [[ ! -f "$env_file" ]]; then
  echo "memex-claude-vendor: missing $env_file (create it or fix symlink name)." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

claude_bin="${MEMEX_CLAUDE_BIN:-}"
if [[ -z "$claude_bin" ]]; then
  claude_bin="$(command -v claude || true)"
fi
if [[ -z "$claude_bin" ]] || [[ ! -x "$claude_bin" ]]; then
  echo "memex-claude-vendor: 'claude' executable not found. Install @anthropic-ai/claude-code or set MEMEX_CLAUDE_BIN to its absolute path." >&2
  exit 1
fi

skip_flags=(--dangerously-skip-permissions)
if [[ "${MEMEX_VENDOR_SKIP_PERMISSIONS:-1}" == "0" ]]; then
  skip_flags=()
fi

exec "$claude_bin" "${skip_flags[@]}" "$@"
