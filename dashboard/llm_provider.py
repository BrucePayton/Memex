"""Unified LLM provider for Memex.

Single source of truth for:
- Model registry and validation
- Settings loading (file + env var fallback + AI profile overlay)
- CLI subprocess configuration and execution
- HTTP API (OpenAI-compatible) configuration and execution
- Unified dispatch: run()

Used by dashboard/server.py, wiki_ops.py, and transitively by MCP server.
"""

from __future__ import annotations

import json
import os
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

# ─── locate repo ─────────────────────────────────────────────────────────────

_PROVIDER_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = _PROVIDER_ROOT.parent

# ─── constants ───────────────────────────────────────────────────────────────

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

AVAILABLE_MODELS = [
    {"id": "claude-opus-4-7", "label": "Opus 4.7"},
    {"id": "claude-sonnet-4-6", "label": "Sonnet 4.6"},
    {"id": "claude-haiku-4-5", "label": "Haiku 4.5"},
    {"id": "default", "label": "Default"},
]

_ALLOWED_MODEL_IDS = frozenset(m["id"] for m in AVAILABLE_MODELS)

SETTINGS_FILE = PROJECT_ROOT / ".dashboard-settings.json"

_DEFAULT_SETTINGS = {
    "model": "default",
    "cli_type": "claude",
    "claude_cli_binary": "claude",
    "claude_cli_extra_args": [],
    "cli_path_extra": "",
    "ai_provider": "cli",
    "openai_base_url": "",
    "openai_api_key": "",
    "openai_model": "",
    "http_temperature": 0.2,
    "http_max_tokens": 0,
    "use_graphify_enhancement": False,
    "ai_profiles": {},
    "active_ai_profile": "",
}

# ─── settings ────────────────────────────────────────────────────────────────


def load_settings(overrides: dict | None = None) -> dict:
    """Load .dashboard-settings.json, apply profile overlay, env fallback, overrides.

    Env vars (MEMEX_*) override file values.  *overrides* dict wins over all.
    """
    merged = dict(_DEFAULT_SETTINGS)

    if SETTINGS_FILE.exists():
        try:
            user = json.loads(SETTINGS_FILE.read_text("utf-8"))
            merged.update(user)
        except Exception:
            pass

    # Apply active AI profile overlay (mirrors server.py:_apply_active_profile)
    _apply_profile_overlay(merged)

    # Environment variable fallback (MEMEX_* prefix)
    _env_fallback(merged, "MEMEX_AI_PROVIDER", "ai_provider")
    _env_fallback(merged, "MEMEX_OPENAI_BASE_URL", "openai_base_url")
    _env_fallback(merged, "MEMEX_OPENAI_API_KEY", "openai_api_key")
    _env_fallback(merged, "MEMEX_OPENAI_MODEL", "openai_model")
    _env_fallback(merged, "MEMEX_CLI_TYPE", "cli_type")
    _env_fallback(merged, "MEMEX_CLI_BINARY", "claude_cli_binary")

    if overrides:
        merged.update({k: v for k, v in overrides.items() if v is not None})

    return merged


def _apply_profile_overlay(s: dict) -> None:
    name = (s.get("active_ai_profile") or "").strip()
    if not name:
        return
    prof = (s.get("ai_profiles") or {}).get(name)
    if not isinstance(prof, dict):
        return
    for k in (
        "ai_provider", "openai_base_url", "openai_api_key", "openai_model",
        "cli_type", "claude_cli_binary", "claude_cli_extra_args", "cli_path_extra",
        "http_temperature", "http_max_tokens",
    ):
        if k in prof and prof[k] is not None:
            s[k] = prof[k]


def _env_fallback(s: dict, env_key: str, setting_key: str) -> None:
    val = os.environ.get(env_key, "").strip()
    if val and not s.get(setting_key):
        s[setting_key] = val


# ─── helpers ─────────────────────────────────────────────────────────────────


def http_ready(settings: dict) -> bool:
    """True when OpenAI-compatible HTTP API is fully configured."""
    if settings.get("ai_provider") != "openai_compatible":
        return False
    return bool(
        (settings.get("openai_base_url") or "").strip()
        and (settings.get("openai_api_key") or "").strip()
        and (settings.get("openai_model") or "").strip()
    )


def get_model_validator() -> Callable[[str], bool]:
    return lambda m: m in _ALLOWED_MODEL_IDS


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
            r = cand.resolve(strict=False)
            if r.is_dir():
                out.append(str(r))
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
    ev = _effective_path_env_value(settings)
    if ev != os.environ.get("PATH", ""):
        env["PATH"] = ev
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
    path_arg = _effective_path_env_value(settings)
    resolved = shutil.which(name, path=path_arg)
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


def _model_args_for(project, settings: dict) -> list[str]:
    """Return --model flag if a non-default model is configured."""
    # Per-project model (non-legacy projects store .model attribute)
    if project is not None and not getattr(project, "is_legacy", True):
        m = getattr(project, "model", None)
        if m and m != "default":
            return ["--model", m]
        return []
    # Global settings model
    model = settings.get("model", "default")
    if not model or model == "default":
        return []
    if model not in _ALLOWED_MODEL_IDS:
        return []
    return ["--model", model]


def _timeout_hint() -> str:
    return f"CLI timed out. Increase CLAUDE_TIMEOUT (currently {os.environ.get('CLAUDE_TIMEOUT', '600')}s)."


# ─── HTTP API ────────────────────────────────────────────────────────────────


def run_http(
    messages: list[dict],
    settings: dict | None = None,
    system: str | None = None,
    timeout: int = 120,
) -> tuple[bool, str, str]:
    """OpenAI-compatible POST /chat/completions (stdlib only). → (ok, text, err)."""
    if settings is None:
        settings = load_settings()
    if not http_ready(settings):
        return (False, "", "OpenAI-compatible provider not fully configured (base URL, API key, model).")

    base = (settings.get("openai_base_url") or "").strip().rstrip("/")
    key = (settings.get("openai_api_key") or "").strip()
    model = (settings.get("openai_model") or "").strip()
    url = base + "/chat/completions"

    msg_list = []
    if system:
        msg_list.append({"role": "system", "content": system})
    msg_list.extend(messages)

    try:
        temp = float(settings.get("http_temperature", 0.2))
    except (TypeError, ValueError):
        temp = 0.2
    temp = max(0.0, min(2.0, temp))

    try:
        max_tok = int(settings.get("http_max_tokens") or 0)
    except (TypeError, ValueError):
        max_tok = 0

    payload: dict = {"model": model, "messages": msg_list, "temperature": temp}
    if max_tok > 0:
        payload["max_tokens"] = max_tok

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + key)

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        choice = (body.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        text = msg.get("content") or ""
        return (True, text[:32000], "")
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            detail = str(e)
        return (False, "", f"HTTP {e.code}: {detail}")
    except Exception as e:
        return (False, "", str(e)[:500])


# ─── CLI subprocess ──────────────────────────────────────────────────────────


def run_cli(
    prompt: str,
    settings: dict | None = None,
    project=None,
    timeout: int | None = None,
    cwd: str | None = None,
) -> tuple[bool, str, str]:
    """Run Claude/Claw CLI subprocess (tools enabled). → (ok, output, error)."""
    if settings is None:
        settings = load_settings()

    claudetools = os.environ.get("CLAUDE_TOOLS", "Edit,Write,Read,Glob,Grep")
    t = timeout or int(os.environ.get("CLAUDE_TIMEOUT", "600"))
    target_cwd = str(cwd or (project.root if project else PROJECT_ROOT))
    exe = get_cli_executable(settings)

    cmd = (
        [exe, "-p", "--allowedTools", claudetools]
        + _model_args_for(project, settings)
        + _parse_claude_extra_args(settings)
        + ["--output-format", "text", prompt]
    )

    try:
        r = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=t,
            cwd=target_cwd,
            env=_cli_subprocess_env(settings),
        )
        err = r.stderr[:500] if r.returncode != 0 else ""
        return (r.returncode == 0, r.stdout[:8000], err)
    except subprocess.TimeoutExpired:
        return (False, "", _timeout_hint())
    except FileNotFoundError:
        bin_name = settings.get("claude_cli_binary", "claude")
        return (False, "", f"CLI not found: {bin_name}. Adjust claude_cli_binary or cli_path_extra (shell aliases are not visible); use an absolute path or a wrapper script.")


# ─── unified dispatch ────────────────────────────────────────────────────────


def run(
    prompt: str,
    settings: dict | None = None,
    project=None,
    timeout: int | None = None,
    cwd: str | None = None,
    force_cli: bool = True,
) -> tuple[bool, str, str]:
    """Run AI prompt: HTTP when configured and force_cli=False, else CLI.

    Tool-based flows (Ingest, Lint, ...) must keep force_cli=True (default).
    """
    if settings is None:
        settings = load_settings()

    if not force_cli and http_ready(settings):
        return run_http(
            [{"role": "user", "content": prompt}],
            settings=settings,
            timeout=timeout or 120,
        )
    return run_cli(prompt, settings=settings, project=project, timeout=timeout, cwd=cwd)
