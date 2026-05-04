#!/usr/bin/env bash
# Memex helper: load ~/.claw-*-env then exec Claw Code CLI.
# The dashboard subprocess does not see shell aliases — install symlinks via
# scripts/install-memex-cli-wrappers.sh and set claude_cli_binary to e.g.
# memex-claw-anthropic (with install dir on Extra PATH) or an absolute path.
#
# Symlink names drive which env file is sourced:
#   memex-claw-anthropic   -> ~/.claw-anthropic-env
#   memex-claw-dashscope   -> ~/.claw-dashscope-env
#   memex-claw-openrouter  -> ~/.claw-openrouter-env
#   memex-claw-xai         -> ~/.claw-xai-env
#   memex-claw-ollama      -> ~/.claw-ollama-env
#
# Optional env:
#   MEMEX_CLAW_BIN              Absolute path to claw if not on PATH
#   MEMEX_VENDOR_SKIP_PERMISSIONS Set to 0 to omit --dangerously-skip-permissions
set -euo pipefail

invoke_name="$(basename "$0")"

pick_env_for_name() {
  case "$invoke_name" in
    *anthropic*) echo "${HOME}/.claw-anthropic-env" ;;
    *dashscope*) echo "${HOME}/.claw-dashscope-env" ;;
    *openrouter*) echo "${HOME}/.claw-openrouter-env" ;;
    *xai*) echo "${HOME}/.claw-xai-env" ;;
    *ollama*) echo "${HOME}/.claw-ollama-env" ;;
    *vendor*) echo "" ;;
    *) echo "" ;;
  esac
}

env_file="$(pick_env_for_name)"
if [[ -z "$env_file" ]]; then
  echo "memex-claw-vendor: invoke via symlink memex-claw-{anthropic,dashscope,openrouter,xai,ollama} (see scripts/install-memex-cli-wrappers.sh). Got: $invoke_name" >&2
  exit 2
fi

if [[ ! -f "$env_file" ]]; then
  echo "memex-claw-vendor: missing $env_file (create it or fix symlink name)." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

claw_bin="${MEMEX_CLAW_BIN:-}"
if [[ -z "$claw_bin" ]]; then
  claw_bin="$(command -v claw || true)"
fi
if [[ -z "$claw_bin" ]] || [[ ! -x "$claw_bin" ]]; then
  echo "memex-claw-vendor: 'claw' executable not found. Install claw-code or set MEMEX_CLAW_BIN to its absolute path." >&2
  exit 1
fi

skip_flags=(--dangerously-skip-permissions)
if [[ "${MEMEX_VENDOR_SKIP_PERMISSIONS:-1}" == "0" ]]; then
  skip_flags=()
fi

exec "$claw_bin" "${skip_flags[@]}" "$@"
