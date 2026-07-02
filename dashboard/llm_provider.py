"""Unified agent CLI runner for Memex."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

_PROVIDER_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = _PROVIDER_ROOT.parent

CLI_TYPES = {
    "claude": {
        "label": "Claude Code",
        "default_binary": "claude",
        "wrapper_prefix": "memex-claude-",
        "env_file_prefix": "~/.claude-",
    },
    "claw": {
        "label": "Claw Code",
        "default_binary": "claw",
        "wrapper_prefix": "memex-claw-",
        "env_file_prefix": "~/.claw-",
    },
    "claude-ark": {
        "label": "Claude Code (Ark Proxy)",
        "default_binary": "claude-ark",
        "wrapper_prefix": "memex-claude-ark-",
        "env_file_prefix": "~/.claude-ark-",
    },
    "claw-anthropic-ark": {
        "label": "Claw Code (Anthropic Ark Proxy)",
        "default_binary": "claw-anthropic-ark",
        "wrapper_prefix": "memex-claw-anthropic-ark-",
        "env_file_prefix": "~/.claw-anthropic-ark-",
    },
}

SETTINGS_FILE = PROJECT_ROOT / ".dashboard-settings.json"

_DEFAULT_SETTINGS = {
    "cli_type": "claude",
    "claude_cli_binary": "claude",
    "claude_cli_extra_args": [],
    "cli_path_extra": "",
    "use_graphify_enhancement": False,
}


def load_settings(overrides: dict | None = None) -> dict:
    """Load .dashboard-settings.json, apply env fallback, overrides."""
    merged = dict(_DEFAULT_SETTINGS)

    if SETTINGS_FILE.exists():
        try:
            user = json.loads(SETTINGS_FILE.read_text("utf-8"))
            if isinstance(user, dict):
                merged.update(user)
        except Exception:
            pass

    _env_fallback(merged, "MEMEX_CLI_TYPE", "cli_type")
    _env_fallback(merged, "MEMEX_CLI_BINARY", "claude_cli_binary")

    if overrides:
        merged.update({k: v for k, v in overrides.items() if v is not None})

    return merged


def _env_fallback(s: dict, env_key: str, setting_key: str) -> None:
    val = os.environ.get(env_key, "").strip()
    if val and not s.get(setting_key):
        s[setting_key] = val


def _parse_cli_path_extra_dirs(settings: dict) -> list[str]:
    raw = settings.get("cli_path_extra") or ""
    if not isinstance(raw, str) or not raw.strip():
        return []
    tokens = []
    for line in raw.replace("\r", "\n").split("\n"):
        for seg in line.split(os.pathsep):
            seg = seg.strip()
            if seg:
                tokens.append(seg)
    out = []
    for p in tokens:
        try:
            cand = Path(p).expanduser()
            if ".." in cand.parts:
                continue
            resolved = cand.resolve(strict=False)
            if resolved.is_dir():
                out.append(str(resolved))
        except Exception:
            continue
    return out


def _effective_path_env_value(settings: dict) -> str:
    extra = _parse_cli_path_extra_dirs(settings)
    base = os.environ.get("PATH", "")
    if not extra:
        return base
    return os.pathsep.join(extra) + (os.pathsep + base if base else "")


def _cli_subprocess_env(settings: dict) -> dict[str, str]:
    env = os.environ.copy()
    effective_path = _effective_path_env_value(settings)
    if effective_path != os.environ.get("PATH", ""):
        env["PATH"] = effective_path
    return env


def get_cli_executable(settings: dict) -> str:
    cli_type = settings.get("cli_type") or "claude"
    cli_info = CLI_TYPES.get(cli_type, CLI_TYPES["claude"])
    default_bin = cli_info.get("default_binary", "claude")
    name = os.path.expanduser(
        (settings.get("claude_cli_binary") or default_bin).strip() or default_bin
    )
    if os.path.isabs(name):
        p = Path(name)
        if p.is_file():
            return str(p.resolve())
    resolved = shutil.which(name, path=_effective_path_env_value(settings))
    if resolved:
        return resolved
    return name


def _parse_claude_extra_args(settings: dict) -> list[str]:
    raw = settings.get("claude_cli_extra_args")
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []
    out = []
    for x in raw[:20]:
        if isinstance(x, str) and x.startswith("--") and len(x) < 200:
            out.append(x)
    return out


def _timeout_hint() -> str:
    return f"CLI timed out. Increase CLAUDE_TIMEOUT (currently {os.environ.get('CLAUDE_TIMEOUT', '600')}s)."


def run_cli(
    prompt: str,
    settings: dict | None = None,
    project=None,
    timeout: int | None = None,
    cwd: str | None = None,
) -> tuple[bool, str, str]:
    """Run Claude/Claw CLI subprocess (tools enabled)."""
    if settings is None:
        settings = load_settings()

    claudetools = os.environ.get("CLAUDE_TOOLS", "Edit,Write,Read,Glob,Grep")
    run_timeout = timeout or int(os.environ.get("CLAUDE_TIMEOUT", "600"))
    target_cwd = str(cwd or (project.root if project else PROJECT_ROOT))
    exe = get_cli_executable(settings)

    cmd = (
        [exe, "-p", "--allowedTools", claudetools]
        + _parse_claude_extra_args(settings)
        + ["--output-format", "text", prompt]
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=run_timeout,
            cwd=target_cwd,
            env=_cli_subprocess_env(settings),
        )
        err = result.stderr[:500] if result.returncode != 0 else ""
        return (result.returncode == 0, result.stdout[:8000], err)
    except subprocess.TimeoutExpired:
        return (False, "", _timeout_hint())
    except FileNotFoundError:
        bin_name = settings.get("claude_cli_binary", "claude")
        return (
            False,
            "",
            f"CLI not found: {bin_name}. Adjust claude_cli_binary or cli_path_extra "
            "(shell aliases are not visible); use an absolute path or a wrapper script.",
        )


def run(
    prompt: str,
    settings: dict | None = None,
    project=None,
    timeout: int | None = None,
    cwd: str | None = None,
) -> tuple[bool, str, str]:
    """Run agent prompt via CLI."""
    return run_cli(prompt, settings=settings, project=project, timeout=timeout, cwd=cwd)
