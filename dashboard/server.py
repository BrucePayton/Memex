#!/usr/bin/env python3
"""
LLM Wiki Dashboard Server
- Dashboard HTML serving
- Claude CLI / Obsidian connection status check
- Ingest, Query, Lint, folder/page CRUD API
- No dependencies (Python 3.10+ stdlib only)
"""

import json, os, re, select, shutil, ssl, subprocess, sys, time, threading, urllib.error, urllib.parse, urllib.request

# Shared models and utilities (single source of truth)
from dashboard.models import (
    make_slug, parse_fm, extract_links, extract_citations,
    WikiPage, GraphNode, GraphEdge, SearchResult,
    FRONTMATTER_RE, WIKILINK_RE, LOG_ENTRY_RE, is_system_page,
    SYSTEM_PAGES, resolve_wikilink_target,
)
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from dashboard.provenance import build_provenance_graph
from dashboard.index_strategy import get_strategy, get_index_instruction, rebuild_index
import dashboard.project_registry as project_registry
from dashboard.project_registry import REGISTRY_FILE
import dashboard.wiki_ops as wiki_ops
import dashboard.llm_provider as llm_provider
from dashboard.scheduler import _load_schedules as _sched_load, _save_schedules as _save_sched_files

PORT = int(os.environ.get("PORT", "8090"))
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
RAW_DIR = PROJECT_ROOT / "raw"

# Configurable via env var. Default 600s (10 min) — Ingest can take long when generating 10+ pages.
CLAUDE_TIMEOUT = int(os.environ.get("CLAUDE_TIMEOUT", "600"))
CLAUDE_TOOLS = os.environ.get("CLAUDE_TOOLS", "Edit,Write,Read,Glob,Grep")
# Short diagnostic timeout
CLAUDE_QUICK_TIMEOUT = int(os.environ.get("CLAUDE_QUICK_TIMEOUT", "30"))
# Stream heartbeat interval (seconds)
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "10"))

# --- Runtime settings (model etc.) ---

SETTINGS_FILE = PROJECT_ROOT / ".dashboard-settings.json"

# OpenAI-compatible vendor presets (align with KnowledgeBuildAnalysis SetupPage AI_PRESETS)
HTTP_PRESETS = [
    {"id": "openai", "name": "OpenAI", "endpoint": "https://api.openai.com/v1", "model": "gpt-4o"},
    {"id": "gemini", "name": "Gemini (OpenAI compat)", "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai", "model": "gemini-1.5-pro"},
    {"id": "qwen", "name": "Qwen (DashScope)", "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-max"},
    {"id": "deepseek", "name": "DeepSeek", "endpoint": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    {"id": "custom", "name": "Custom", "endpoint": "", "model": ""},
]


def _save_settings(s):
    """Atomically write settings to avoid corruption from concurrent writers."""
    import tempfile
    data = json.dumps(s, ensure_ascii=False, indent=2)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False,
        dir=SETTINGS_FILE.parent, prefix=".dashboard-settings.",
    )
    try:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, str(SETTINGS_FILE))
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise


SETTINGS = llm_provider.load_settings()

# Register model validator
project_registry.set_model_validator(llm_provider.get_model_validator())

# Backward-compat aliases for dashboard UI code
CLI_TYPES = llm_provider.CLI_TYPES
AVAILABLE_MODELS = llm_provider.AVAILABLE_MODELS


def _settings_for_response():
    """Strip secrets for JSON responses."""
    s = dict(SETTINGS)
    if s.get("openai_api_key"):
        s["openai_api_key_set"] = True
        s["openai_api_key"] = ""
    else:
        s["openai_api_key_set"] = False
    return s


def _cli_display_short() -> str:
    """Short label for configured CLI binary (basename or token)."""
    raw = os.path.expanduser((SETTINGS.get("claude_cli_binary") or "claude").strip() or "claude")
    try:
        return Path(raw.replace("\\", "/")).name
    except Exception:
        return raw[:48]


def _http_vendor_label() -> str:
    """Preset vendor name or truncated model id — no secrets."""
    if SETTINGS.get("ai_provider") != "openai_compatible":
        return ""
    model = (SETTINGS.get("openai_model") or "").strip()
    base = (SETTINGS.get("openai_base_url") or "").strip().rstrip("/")
    if not model:
        return ""
    matches = []
    for p in HTTP_PRESETS:
        if (p.get("id") or "") == "custom":
            continue
        pm = (p.get("model") or "").strip()
        if pm != model:
            continue
        ep = (p.get("endpoint") or "").strip().rstrip("/")
        matches.append((str(p.get("name") or pm), ep))
    if not matches:
        return model[:48]
    if len(matches) == 1:
        return matches[0][0]
    if base:
        for name, ep in matches:
            if ep and (base == ep or base.startswith(ep) or ep in base):
                return name
    return matches[0][0]


def _build_llm_ui() -> dict:
    """Provider identity for dashboard buttons and toolbar chip (no secrets)."""
    http_ready = llm_provider.http_ready(SETTINGS)
    ap = SETTINGS.get("ai_provider") or "cli"
    cli_short = _cli_display_short()
    http_short = ""
    if ap == "openai_compatible":
        http_short = _http_vendor_label()
        if not http_short:
            om = (SETTINGS.get("openai_model") or "").strip()
            http_short = om[:48] if om else ""

    if ap == "openai_compatible" and http_ready:
        mode = "mixed"
    else:
        mode = "cli_only"

    qb = "http" if http_ready else "cli"
    action_backend = {
        "ingest": "cli",
        "lint": "cli",
        "lint_fix": "cli",
        "reflect": "cli",
        "write": "cli",
        "compare": "cli",
        "review_refresh": "cli",
        "slides": "cli",
        "fix_citations": "cli",
        "suggest_sources": "cli",
        "query_save": "cli",
        "query": qb,
        "assistant": qb,
    }
    cli_type = SETTINGS.get("cli_type") or "claude"
    cli_type_info = CLI_TYPES.get(cli_type, CLI_TYPES["claude"])
    return {
        "cli_short": cli_short,
        "http_short": http_short,
        "mode": mode,
        "http_ready": http_ready,
        "action_backend": action_backend,
        "cli_type": cli_type,
        "cli_type_label": cli_type_info.get("label", cli_type),
    }


# Backward-compat: lambda wrapping http_ready with SETTINGS
_openai_http_ready = lambda: llm_provider.http_ready(SETTINGS)


# Backward-compat aliases for CLI helpers used by run_claude_tracked / run_claude_streaming
get_cli_executable = llm_provider.get_cli_executable


_QUERY_RAG_TOP_K = 8
_QUERY_INDEX_EXCERPT_MAX = 6000
_CJK_HAN_RE = re.compile(r"[\u4e00-\u9fff]")


def _query_contains_cjk_han(text: str) -> bool:
    return bool(_CJK_HAN_RE.search(text or ""))


def _query_response_language_line(question: str, lang_ui: str | None) -> str:
    """Single English instruction line for response language: Han in question forces Chinese."""
    if _query_contains_cjk_han(question):
        return "Respond in Simplified Chinese."
    lg = (lang_ui or "").strip().lower()
    if lg == "zh":
        return "Respond in Simplified Chinese."
    if lg == "ko":
        return "Respond in Korean."
    return "Respond in English."


def _wiki_rel_for_project(proj, wiki_file_rel: str) -> str:
    """PROJECT_ROOT-relative path for a file under this project's wiki_dir."""
    wf = wiki_file_rel.replace("\\", "/").strip().lstrip("/")
    try:
        return str((proj.wiki_dir / wf).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        slug = getattr(proj, "slug", "") or ""
        if slug:
            return f"projects/{slug}/wiki/{wf}"
        return f"wiki/{wf}"


# ─── Backward-compat: llm_provider-based replacements for old run_claude/openai_chat_completion ───

def run_claude(prompt, timeout=None, cwd=None, project=None, force_cli=True):
    """Run AI prompt via unified llm_provider."""
    return llm_provider.run(prompt, settings=SETTINGS, project=project, timeout=timeout, cwd=cwd, force_cli=force_cli)


def openai_chat_completion(messages, system=None, timeout=120):
    """OpenAI-compatible chat via llm_provider."""
    return llm_provider.run_http(messages, settings=SETTINGS, system=system, timeout=timeout)


# Helpers for run_claude_tracked / run_claude_streaming (still CLI-only, stream-json)
def _cli_subprocess_env():
    return llm_provider._cli_subprocess_env(SETTINGS)


def _parse_claude_extra_args():
    return llm_provider._parse_claude_extra_args(SETTINGS)


def _model_args_for(project=None):
    return llm_provider._model_args_for(project, SETTINGS)


RAW_ABS = os.path.abspath(str(RAW_DIR))


def _resolve_project_body(body):
    """Extract project slug from POST body -> Project. Unknown slug raises KeyError."""
    slug = (body.get("project") or "").strip() or None
    return project_registry.get_project(slug)


# --- slug generation (unicode support) ---

# make_slug, parse_fm, extract_links, FRONTMATTER_RE, WIKILINK_RE now imported from dashboard.models


# --- raw/ protection ---

def assert_writable(path):
    """Block writes to raw/ directory. Legacy raw + all projects/<slug>/raw/ are immutable."""
    if project_registry.is_protected_raw(path):
        raise PermissionError(f"raw/ is immutable: {path}")


def assert_raw_create_only(path):
    """Only allow new file creation inside any raw/ (no modification/overwrite of existing files)."""
    if not project_registry.is_protected_raw(path):
        return  # outside raw/, skip
    if os.path.exists(str(path)):
        raise PermissionError(f"raw/ file already exists (immutable): {path}")


def dedupe_raw_path(raw_path: Path) -> Path:
    """If same filename exists in raw/, auto-rename with -2, -3, etc."""
    if not raw_path.exists():
        return raw_path
    stem = raw_path.stem
    suffix = raw_path.suffix
    parent = raw_path.parent
    n = 2
    while True:
        candidate = parent / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _snapshot_raw():
    """raw/ file hash snapshot (for change detection)"""
    snap = {}
    for f in RAW_DIR.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            snap[str(f.relative_to(PROJECT_ROOT))] = f.stat().st_mtime
    return snap


_raw_snapshot_at_start = _snapshot_raw()


def check_raw_integrity():
    """raw/ change detection -> return list of changed files"""
    current = _snapshot_raw()
    modified = []
    for path, mtime in _raw_snapshot_at_start.items():
        if path in current and current[path] != mtime:
            modified.append(path)
    deleted = [p for p in _raw_snapshot_at_start if p not in current]
    return {"modified": modified, "deleted": deleted, "ok": not modified and not deleted}


# ─── GitManager ───

class GitManager:
    def __init__(self):
        self.root = str(PROJECT_ROOT)
        # init if not a git repo
        if not (PROJECT_ROOT / ".git").is_dir():
            self._run("init")
            self._run("add", "-A")
            self._run("commit", "-m", "init: wiki bootstrap")

    def _run(self, *args):
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, cwd=self.root,
        )
        return r

    def _stage_all(self, project=None):
        """Stage project-scoped changes (if legacy, root wiki/raw/ingest-reports)."""
        if project and not project.is_legacy:
            base = str(project.root.relative_to(PROJECT_ROOT))
            for sub in ("wiki", "raw", "ingest-reports", "reflect-reports", ".settings.json", "query-log.jsonl", "CLAUDE.md"):
                p = project.root / sub
                if p.exists():
                    self._run("add", f"{base}/{sub}")
            # include registry changes too
            if REGISTRY_FILE.exists():
                self._run("add", "projects.json")
        else:
            self._run("add", "wiki/", "raw/")
            if (PROJECT_ROOT / "ingest-reports").is_dir():
                self._run("add", "ingest-reports/")

    def _slug_prefix(self, project):
        if project and not project.is_legacy:
            return f"({project.slug})"
        return ""

    def commit_ingest(self, source_name, project=None):
        """Commit after ingest. Returns commit hash."""
        self._stage_all(project)
        status = self._run("diff", "--cached", "--name-only")
        files = [f for f in status.stdout.strip().split("\n") if f]
        if not files:
            return {"hash": None, "files": []}
        msg = f"ingest{self._slug_prefix(project)}: {source_name}"
        self._run("commit", "-m", msg)
        log = self._run("log", "-1", "--format=%H")
        return {"hash": log.stdout.strip(), "files": files}

    def commit_query_save(self, question, project=None):
        self._stage_all(project)
        msg = f"query{self._slug_prefix(project)}: {question[:80]}"
        self._run("commit", "-m", msg)
        log = self._run("log", "-1", "--format=%H")
        return log.stdout.strip()

    def commit_lint_fix(self, project=None):
        self._stage_all(project)
        msg = f"lint{self._slug_prefix(project)}: auto-fix"
        self._run("commit", "-m", msg)
        log = self._run("log", "-1", "--format=%H")
        return log.stdout.strip()

    def commit_generic(self, message, project=None):
        """For arbitrary operations — no auto project prefix in message, caller decides."""
        self._stage_all(project)
        self._run("commit", "-m", message)
        log = self._run("log", "-1", "--format=%H")
        return log.stdout.strip()

    def list_ingests(self, limit=50):
        """ingest: extract commits only -> [{hash, source, date, files_changed}]"""
        log = self._run(
            "log", f"--max-count={limit}", "--format=%H|%s|%aI",
            "--grep=^ingest:", "--extended-regexp",
        )
        results = []
        for line in log.stdout.strip().split("\n"):
            if not line or "|" not in line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            h, subject, date = parts
            # changed files count
            stat = self._run("diff-tree", "--no-commit-id", "--name-only", "-r", h)
            files = [f for f in stat.stdout.strip().split("\n") if f]
            source = subject.replace("ingest: ", "", 1)
            results.append({
                "hash": h,
                "hash_short": h[:8],
                "source": source,
                "date": date[:19].replace("T", " "),
                "files_changed": len(files),
                "files": files,
            })
        return results

    def revert_ingest(self, commit_hash):
        """Revert only that commit (git revert --no-edit)"""
        # safety: verify it is an ingest commit
        log = self._run("log", "-1", "--format=%s", commit_hash)
        subject = log.stdout.strip()
        if not subject.startswith("ingest:"):
            return {"ok": False, "error": f"Not an ingest commit: {subject}"}
        r = self._run("revert", "--no-edit", commit_hash)
        if r.returncode != 0:
            # on conflict
            self._run("revert", "--abort")
            return {"ok": False, "error": f"Revert conflict: {r.stderr[:300]}"}
        new_log = self._run("log", "-1", "--format=%H|%s")
        parts = new_log.stdout.strip().split("|", 1)
        return {"ok": True, "revert_hash": parts[0], "message": parts[1] if len(parts) > 1 else ""}


git_mgr = GitManager()

# ─── helpers (parse_fm, extract_links, make_slug, LOG_ENTRY_RE now imported from dashboard.models) ───


def _timeout_hint():
    """Detailed hints to show user on timeout"""
    return (
        f"Claude CLI timeout ({CLAUDE_TIMEOUT}s). Possible causes + solutions:\n"
        f"  1. Claude CLI not authenticated -> run 'claude' in terminal to verify login\n"
        f"  2. Model too heavy -> switch to Sonnet/Haiku in header model dropdown\n"
        f"  3. Task itself is large -> restart server with env CLAUDE_TIMEOUT=1200\n"
        f"  4. Quick check via /api/claude/diagnose"
    )


def run_claude_tracked(prompt, cwd=None, project=None):
    """Trace Claude CLI stream-json events (Query only — HTTP queries use _do_query_openai_rag).

    → (ok, answer, error, files_read, token_usage)"""
    target_cwd = str(cwd or (project.root if project else PROJECT_ROOT))
    exe = llm_provider.get_cli_executable(SETTINGS)
    cmd = (
        [exe, "-p", "--allowedTools", CLAUDE_TOOLS]
        + _model_args_for(project)
        + _parse_claude_extra_args()
        + ["--output-format", "stream-json", "--verbose", prompt]
    )
    try:
        r = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
            cwd=target_cwd,
            env=_cli_subprocess_env(),
        )
    except subprocess.TimeoutExpired:
        return (False, "", _timeout_hint(), [], {})
    except FileNotFoundError:
        bin_name = SETTINGS.get("claude_cli_binary", "claude")
        return (False, "", f"CLI not found: {bin_name}. Use absolute path or cli_path_extra.", [], {})

    files_read = []
    answer = ""
    token_usage = {}

    for line in r.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Read tool result -> extract filePath
        if evt.get("type") == "user":
            msg = evt.get("message", {})
            tur = evt.get("tool_use_result")
            if tur and isinstance(tur, dict):
                fp = tur.get("file", {}).get("filePath", "")
                if fp:
                    # convert to project-relative path
                    try:
                        rel = str(Path(fp).relative_to(PROJECT_ROOT))
                    except ValueError:
                        rel = fp
                    if rel not in files_read:
                        files_read.append(rel)
            # also search in content array (tool_result)
            content = msg.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        # this was already handled above
                        pass

        # result event -> answer + usage
        if evt.get("type") == "result":
            answer = evt.get("result", "")
            token_usage = {
                "input_tokens": evt.get("usage", {}).get("input_tokens", 0),
                "output_tokens": evt.get("usage", {}).get("output_tokens", 0),
                "cost_usd": evt.get("total_cost_usd", 0),
            }

    ok = r.returncode == 0
    return (ok, answer[:4000], r.stderr[:500] if not ok else "", files_read, token_usage)


# ─── SSE Streaming Engine ───

def _normalize_path(fp, proj=None):
    """Convert absolute file path to project-relative string."""
    if not fp:
        return fp
    try:
        return str(Path(fp).relative_to(PROJECT_ROOT))
    except ValueError:
        pass
    if proj:
        for base in [proj.root, proj.wiki_dir]:
            try:
                return str(Path(fp).relative_to(base))
            except ValueError:
                continue
    return fp


def parse_stream_event(evt, elapsed=0):
    """Normalize a raw stream-json event from Claude CLI to our SSE event format."""
    evt_type = evt.get("type", "")

    if evt_type == "start":
        subtype = evt.get("subtype", "")
        return {"type": "progress", "phase": "starting", "message": f"Starting {subtype}…", "elapsed": elapsed}

    if evt_type == "result":
        return {"type": "done", "ok": True, "output": evt.get("result", ""), "elapsed": elapsed}

    if evt_type == "error":
        return {"type": "error", "message": evt.get("message", "Unknown error"), "elapsed": elapsed}

    # Handle assistant thinking/delta messages to show content
    if evt_type in ("assistant", "delta"):
        msg = evt.get("message", {})
        # Check for text content
        content = msg.get("content", [])
        text_content = ""
        if isinstance(content, str):
            text_content = content
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if text:
                        text_content += text
        # Also check for top-level text
        if not text_content and msg.get("content") and isinstance(msg.get("content"), str):
            text_content = msg.get("content")
        if text_content and len(text_content.strip()) > 0:
            # Show first 400 chars of thinking/content
            return {"type": "assistant_content", "content": text_content[:400], "elapsed": elapsed}

    # tool_use from assistant/delta: nested in message.content[] array
    if evt_type in ("assistant", "delta", "content_block_start", "content_block_delta", "content_block_stop"):
        msg = evt.get("message", {})
        content = msg.get("content", [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")
                    tool_input = item.get("input", {})
                    if tool_name == "Read":
                        fp = tool_input.get("file_path", "")
                        return {"type": "tool_use", "tool": "Read", "file": _normalize_path(fp), "elapsed": elapsed}
                    if tool_name == "Write":
                        fp = tool_input.get("file_path", "")
                        write_content = tool_input.get("content", "")
                        preview = ""
                        if write_content:
                            if len(write_content) > 200:
                                preview = write_content[:200] + "..."
                            else:
                                preview = write_content
                        return {"type": "tool_use", "tool": "Write", "file": _normalize_path(fp), "content_preview": preview, "elapsed": elapsed}
                    if tool_name == "Edit":
                        fp = tool_input.get("file_path", "")
                        old_str = tool_input.get("old_string", "")
                        new_str = tool_input.get("new_string", "")
                        preview = ""
                        if old_str and len(old_str) < 150:
                            preview = f"Replacing: {old_str[:100]}"
                        elif new_str and len(new_str) < 150:
                            preview = f"With: {new_str[:100]}"
                        return {"type": "tool_use", "tool": "Edit", "file": _normalize_path(fp), "content_preview": preview, "elapsed": elapsed}
                    if tool_name == "Grep":
                        pattern = tool_input.get("pattern", "")
                        path = tool_input.get("path", "")
                        return {"type": "tool_use", "tool": "Grep", "pattern": pattern, "path": _normalize_path(path) if path else "", "elapsed": elapsed}
                    if tool_name == "Glob":
                        pattern = tool_input.get("pattern", "")
                        return {"type": "tool_use", "tool": "Glob", "pattern": pattern, "elapsed": elapsed}
                    return {"type": "tool_use", "tool": tool_name, "input": {k: str(v)[:200] for k, v in tool_input.items()}, "elapsed": elapsed}

    # tool_use from assistant (top-level key, alternate format)
    tool_use = evt.get("tool_use")
    if tool_use and isinstance(tool_use, dict):
        tool_name = tool_use.get("name", "")
        tool_input = tool_use.get("input", {})
        if tool_name == "Read":
            fp = tool_input.get("file_path", "")
            return {"type": "tool_use", "tool": "Read", "file": _normalize_path(fp), "elapsed": elapsed}
        if tool_name == "Write":
            fp = tool_input.get("file_path", "")
            write_content = tool_input.get("content", "")
            preview = ""
            if write_content:
                if len(write_content) > 200:
                    preview = write_content[:200] + "..."
                else:
                    preview = write_content
            return {"type": "tool_use", "tool": "Write", "file": _normalize_path(fp), "content_preview": preview, "elapsed": elapsed}
        if tool_name == "Edit":
            fp = tool_input.get("file_path", "")
            old_str = tool_input.get("old_string", "")
            new_str = tool_input.get("new_string", "")
            preview = ""
            if old_str and len(old_str) < 150:
                preview = f"Replacing: {old_str[:100]}"
            elif new_str and len(new_str) < 150:
                preview = f"With: {new_str[:100]}"
            return {"type": "tool_use", "tool": "Edit", "file": _normalize_path(fp), "content_preview": preview, "elapsed": elapsed}
        if tool_name == "Grep":
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", "")
            return {"type": "tool_use", "tool": "Grep", "pattern": pattern, "path": _normalize_path(path) if path else "", "elapsed": elapsed}
        if tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            return {"type": "tool_use", "tool": "Glob", "pattern": pattern, "elapsed": elapsed}
        return {"type": "tool_use", "tool": tool_name, "input": {k: str(v)[:200] for k, v in tool_input.items()}, "elapsed": elapsed}

    # tool_result (user message with tool_result) - enhanced with better content preview
    tur = evt.get("tool_use_result")
    if tur and isinstance(tur, dict):
        is_err = tur.get("is_error", False)
        content = tur.get("content", "")
        fp = ""
        if isinstance(tur.get("file"), dict):
            fp = tur["file"].get("filePath", "")
        # Generate better preview
        preview = ""
        if content:
            content_str = str(content)
            if len(content_str) > 500:
                # Show first 250 and last 250 chars
                preview = content_str[:250] + "\n...\n" + content_str[-250:]
            else:
                preview = content_str
        return {"type": "tool_result", "tool": tur.get("toolName", ""), "file": _normalize_path(fp), "status": "error" if is_err else "ok", "preview": preview, "elapsed": elapsed}

    # Generic passthrough — display unknown event types on frontend
    return {"type": "tool_use", "tool": f"[{evt_type or 'unknown'}]", "file": "", "elapsed": elapsed}


def run_claude_streaming(prompt, timeout=None, cwd=None, project=None):
    """Stream Claude CLI events via Popen (yield dicts). → done or error at end.

    Uses --output-format stream-json for structured output.
    Supports early termination via GeneratorExit → proc.terminate().
    """
    t = timeout or CLAUDE_TIMEOUT
    target_cwd = str(cwd or (project.root if project else PROJECT_ROOT))
    exe = llm_provider.get_cli_executable(SETTINGS)
    cmd = (
        [exe, "-p", "--allowedTools", CLAUDE_TOOLS]
        + _model_args_for(project)
        + _parse_claude_extra_args()
        + ["--output-format", "stream-json", "--verbose", prompt]
    )
    proc = None
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=target_cwd, env=_cli_subprocess_env(),
        )
        start = time.monotonic()
        heartbeat_interval = HEARTBEAT_INTERVAL
        last_activity_type = "starting"
        try:
            while True:
                readable, _, _ = select.select([proc.stdout], [], [], heartbeat_interval)
                if readable:
                    line = proc.stdout.readline()
                    if not line:  # EOF
                        break
                    if not line.strip():
                        continue
                    elapsed = time.monotonic() - start
                    try:
                        evt = json.loads(line)
                        # Track activity type for better heartbeat messages
                        evt_type = evt.get("type", "")
                        if evt_type == "tool_use" or evt_type == "assistant":
                            last_activity_type = evt_type
                        yield parse_stream_event(evt, elapsed=round(elapsed, 1))
                    except (json.JSONDecodeError, ValueError) as e:
                        # Log JSON parse errors for debugging but continue processing
                        # Don't yield to avoid polluting SSE stream
                        print(f"[stream debug] JSON parse error: {e} — line: {line[:200]}", file=sys.stderr)
                        continue
                else:
                    # Timeout — emit heartbeat to keep frontend alive
                    elapsed = time.monotonic() - start
                    # More descriptive heartbeat based on recent activity
                    if last_activity_type == "tool_use":
                        msg = f"Working with tools... ({int(elapsed)}s)"
                    elif last_activity_type == "assistant":
                        msg = f"Thinking... ({int(elapsed)}s)"
                    else:
                        msg = f"Processing... ({int(elapsed)}s)"
                    yield {"type": "heartbeat", "elapsed": round(elapsed, 1), "message": msg}
        except GeneratorExit:
            raise
        proc.wait(timeout=5)
        final_elapsed = time.monotonic() - start
        if proc.returncode != 0:
            yield {"type": "error", "message": f"CLI exited with code {proc.returncode}", "elapsed": round(final_elapsed, 1)}
        yield {"type": "done", "ok": proc.returncode == 0, "elapsed": round(final_elapsed, 1)}
    except GeneratorExit:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception as e:
        if proc and proc.poll() is None:
            proc.terminate()
        yield {"type": "error", "message": f"{type(e).__name__}: {e}", "elapsed": 0}


# ─── SSE Helpers for Handler ───

def _sse_data(event_dict):
    """Serialize event dict to SSE wire format: 'data: {...}\\n\\n'"""
    return "data: " + json.dumps(event_dict, ensure_ascii=False) + "\n\n"


def _handle_stream(handler, events):
    """Consume event generator, write SSE wire format, handle disconnect."""
    try:
        handler._sse_start()
        for evt in events:
            try:
                handler._sse_send(evt)
            except (BrokenPipeError, ConnectionResetError):
                return  # client disconnected — generator handles cleanup
        handler._sse_end()
    except (BrokenPipeError, ConnectionResetError):
        pass
    except Exception as e:
        import traceback
        try:
            handler._sse_send({"type": "error", "message": f"{type(e).__name__}: {e}", "elapsed": 0})
            handler._sse_end()
        except Exception:
            print(f"[ERROR] SSE stream: {traceback.format_exc()[:800]}")


# ─── Streaming Operation Wrappers ───

def _op_prompt_for(operation, **kw):
    """Map operation name + kwargs to the same prompt the blocking version uses."""
    if operation == "lint":
        proj = project_registry.get_project(kw.get("project_slug"))
        today = datetime.now().strftime("%Y-%m-%d")
        from index_strategy import get_index_instruction
        idx_inst = get_index_instruction(proj.wiki_dir)
        return f"""{idx_inst}

⚡ PERFORMANCE: Use parallel tool calls — read multiple wiki pages in a single turn rather than sequentially.

Read the "Lint checklist" section in CLAUDE.md and audit the entire wiki.

Run **all** checks:

### Structure
- Pages missing frontmatter or invalid type
- status: superseded without superseded_by
- status: disputed without ## Disputed
- superseded_by targets missing pages

### Citations
- Factual claims missing [^src-*]
- Per-page citation coverage
- [^src-*] referenced but undefined at bottom
- Referenced source-summary pages missing from wiki/
- source_count mismatches actual citations

### Links
- Orphan pages (no inbound [[wikilink]])
- Mentioned concepts without pages
- Related pages missing cross-links

### Freshness (today: {today})
- active pages with last_updated older than 30 days
- source_count 1 but broad generalizations
- confidence high but source_count < 2

Report format:
## Lint Report — {today}
### Critical (must fix)
- [ ] page.md — issue + suggested fix
### Warning (should fix)
- [ ] page.md — issue + suggested fix
### Info (nice to have)
- [ ] page.md — issue + suggested fix"""

    if operation == "lint_fix":
        return """You just ran the CLAUDE.md Lint checklist. Fix every issue found now:

- Fix missing/invalid frontmatter
- Add [^src-*] to uncited claims when a source exists
- Align source_count with actual citations
- Bump last_updated to today where appropriate
- Add inbound [[wikilink]] to orphan pages; add missing cross-links
- Create stub pages for mentioned concepts without pages (min. one citation)
- Fix status / superseded_by inconsistencies
- Add ## Disputed where status demands it
- Refresh wiki/index.md, wiki/log.md, wiki/overview.md as needed

Summarize fixes by Critical / Warning / Info."""

    if operation == "reflect":
        from project_registry import get_project as get_proj
        from index_strategy import get_index_instruction
        proj = get_proj(kw.get("project_slug"))
        reflect_dir = proj.reflect_reports
        reflect_dir.mkdir(parents=True, exist_ok=True)
        window = kw.get("window", "last-10-ingests")

        # Reuse _collect_reflect_context from above
        ctx = _collect_reflect_context(window, project=proj)
        reports_summary = "\n\n".join(
            f"### {r['name']}\n{r['content']}" for r in ctx["reports"]
        ) or "(no ingest reports)"
        low_ratio = "\n".join(
            f"- Q: {q['question'][:80]}  (wiki_ratio: {q['wiki_ratio']})"
            for q in ctx["low_ratio_queries"]
        ) or "(none)"
        today = datetime.now().strftime("%Y-%m-%d")
        report_path = f"reflect-reports/{today}.md"

        return f"""Analyze the following data:

## Recent wiki log (excerpt)
{ctx['log_text'][-1500:]}

## Ingest reports
{reports_summary[:3000]}

## Low wiki_ratio queries
{low_ratio}

Produce:

1. **SUGGESTED_PAGES**: Entities/concepts that appear often but lack dedicated wiki pages.
2. **SUGGESTED_SCHEMA**: If repeated ingest judgment patterns emerge, propose rules to add to CLAUDE.md.
3. **SUGGESTED_SOURCES**: From low-ratio queries, suggest search terms / sources.
4. **CONTRADICTION_REVIEW**: If conflicting source behaviors appear often, propose improvements.

Save the result to {report_path}."""

    if operation == "review_refresh":
        proj = project_registry.get_project(kw.get("project_slug"))
        filename = kw.get("filename", "")
        today = datetime.now().strftime("%Y-%m-%d")
        return f"""Read wiki/{filename} and:
1. Check Sources in wiki/index.md for material that could add new perspective to this page
2. If yes, merge that material with proper [^src-*] citations and refresh the page
3. Set last_updated to {today}
4. Summarize what you added

If nothing new applies, reply "No new updates; refreshed last_updated only." and only bump last_updated."""

    if operation == "fix_citations":
        page = kw.get("page", "")
        return f"""Read wiki/{page}.
Find factual claims whose sentences lack inline citations [^src-*].
Add appropriate [^src-source-slug] citations where a matching source exists.

Rules:
- Place citations at sentence ends; definitions at bottom: [^src-slug]: [[source-slug]]
- Only use sources listed under Sources in wiki/index.md
- Do not add a citation when no matching source exists
- Keep existing citations

Report what you changed."""

    if operation == "ingest":
        title = kw.get("title", "")
        content = kw.get("content", "")
        folder = kw.get("folder", "")
        slug = kw.get("slug", "")
        report_rel = kw.get("report_rel", "")
        proj = project_registry.get_project(kw.get("project_slug"))
        from index_strategy import get_index_instruction
        idx_inst = get_index_instruction(proj.wiki_dir)
        folder_inst = f" Place any new pages under wiki/{folder}/." if folder else ""
        return f"""{idx_inst}
IMPORTANT: Never modify or delete files under raw/ — raw/ is immutable. Only write under wiki/.
Ingest raw/{slug}.md — read this source and create/update wiki pages according to CLAUDE.md. Skip preamble and execute.{folder_inst}

When finished:
1. Summarize why you made these choices in 3–5 lines (start with REASONING:).
2. Create {report_rel} using this shape:
# Ingest Report: {title}
## Created
- wiki/path/file.md — WHY: one line
## Modified
- wiki/path/file.md — WHY: one line
## New cross-links
- [[a]] ↔ [[b]]"""

    if operation == "write":
        proj = project_registry.get_project(kw.get("project_slug"))
        topic = kw.get("topic", "")
        length = kw.get("length", "medium")
        style = kw.get("style", "blog")
        from index_strategy import get_index_instruction
        idx_inst = get_index_instruction(proj.wiki_dir)
        word_map = {"short": "~300 words", "medium": "~700 words", "long": "~1500 words"}
        style_map = {
            "blog": "Blog tone (friendly, clear)",
            "paper": "Academic tone (precise, rigorous)",
            "explainer": "Explainer tone (accessible to newcomers)",
        }
        return f"""{idx_inst}
Topic: {topic}
Length: {word_map.get(length, '~700 words')}
Style: {style_map.get(style, 'Blog tone')}

Use accumulated wiki pages as sources.

Requirements:
- Every factual claim needs [^src-source-slug] inline citations
- Reference related wiki pages with [[wikilink]]
- Footnote definitions at bottom: [^src-*]: [[source-*]]
- Introduction / body / conclusion
- Do not invent topics lacking supporting sources in the wiki

Output only the article (no meta commentary)."""

    if operation == "compare":
        proj = project_registry.get_project(kw.get("project_slug"))
        page_a = kw.get("page_a", "")
        page_b = kw.get("page_b", "")
        return f"""Read wiki/{page_a} and wiki/{page_b}, then compare them.

Structure:
## Common ground
## Differences
## Relationship / implications

Include [^src-*] citations for claims; draw on sources from both pages."""

    return f"[operation={operation}]"


def stream_lint(project_slug=None):
    proj = project_registry.get_project(project_slug)
    prompt = _op_prompt_for("lint", project_slug=project_slug)
    yield {"type": "progress", "phase": "starting", "message": "Starting lint…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt
    # Post-processing: run git commit if successful (after stream ends)
    try:
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"lint{git_mgr._slug_prefix(proj)}: lint audit")
    except Exception:
        pass


def stream_lint_fix(project_slug=None):
    proj = project_registry.get_project(project_slug)
    prompt = _op_prompt_for("lint_fix")
    yield {"type": "progress", "phase": "starting", "message": "Starting lint fix…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt
    try:
        git_mgr.commit_lint_fix(project=proj)
    except Exception:
        pass


def stream_reflect(window="last-10-ingests", project_slug=None):
    proj = project_registry.get_project(project_slug)
    prompt = _op_prompt_for("reflect", project_slug=project_slug, window=window)
    yield {"type": "progress", "phase": "starting", "message": "Starting reflect…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt
    try:
        git_mgr._stage_all(project=proj)
        today = datetime.now().strftime("%Y-%m-%d")
        git_mgr._run("commit", "-m", f"reflect{git_mgr._slug_prefix(proj)}: {today} ({window})")
    except Exception:
        pass


def stream_review_refresh(filename, project_slug=None):
    proj = project_registry.get_project(project_slug)
    prompt = _op_prompt_for("review_refresh", project_slug=project_slug, filename=filename)
    yield {"type": "progress", "phase": "starting", "message": f"Refreshing {filename}…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt
    try:
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"review{git_mgr._slug_prefix(proj)}: refresh {filename}")
    except Exception:
        pass


def stream_fix_citations(page_filename, project_slug=None):
    proj = project_registry.get_project(project_slug)
    filepath = proj.wiki_dir / page_filename
    if not filepath.exists():
        yield {"type": "error", "message": "Page not found", "elapsed": 0}
        return
    prompt = _op_prompt_for("fix_citations", project_slug=project_slug, page=page_filename)
    yield {"type": "progress", "phase": "starting", "message": f"Fixing citations in {page_filename}…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt
    try:
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"citation{git_mgr._slug_prefix(proj)}: fix {page_filename}")
    except Exception:
        pass


def stream_ingest(title, content, folder="", project_slug=None):
    proj = project_registry.get_project(project_slug)
    raw_dir = proj.raw_dir
    wiki_dir = proj.wiki_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    wiki_dir.mkdir(parents=True, exist_ok=True)

    slug = make_slug(title)
    raw_path = dedupe_raw_path(raw_dir / f"{slug}.md")
    raw_path.write_text(content, encoding="utf-8")
    slug = raw_path.stem

    ts = datetime.now().strftime("%Y-%m-%d-%H%M")
    report_rel = f"ingest-reports/{ts}-{slug}.md"
    (proj.ingest_reports).mkdir(parents=True, exist_ok=True)

    prompt = _op_prompt_for("ingest", project_slug=project_slug, title=title, content=content, folder=folder, slug=slug, report_rel=report_rel)
    yield {"type": "progress", "phase": "starting", "message": f"Ingesting {slug}…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt
    try:
        from index_strategy import rebuild_index
        rebuild_index(wiki_dir)
        c = git_mgr.commit_ingest(title, project=proj)
        yield {"type": "post_action", "action": "commit", "hash": c.get("hash", ""), "elapsed": 0}
    except Exception:
        pass


def stream_write(topic, length="medium", style="blog", project_slug=None):
    if not topic or not topic.strip():
        yield {"type": "error", "message": "Topic is required", "elapsed": 0}
        return
    proj = project_registry.get_project(project_slug)
    prompt = _op_prompt_for("write", project_slug=project_slug, topic=topic, length=length, style=style)
    yield {"type": "progress", "phase": "starting", "message": f"Writing: {topic}…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt


def stream_compare(page_a, page_b, save_as="", project_slug=None):
    if not page_a or not page_b:
        yield {"type": "error", "message": "Both pages required", "elapsed": 0}
        return
    proj = project_registry.get_project(project_slug)
    wiki_dir = proj.wiki_dir
    fa = wiki_dir / page_a
    fb = wiki_dir / page_b
    if not fa.exists() or not fb.exists():
        yield {"type": "error", "message": "Page not found", "elapsed": 0}
        return
    prompt = _op_prompt_for("compare", project_slug=project_slug, page_a=page_a, page_b=page_b)
    yield {"type": "progress", "phase": "starting", "message": f"Comparing {page_a} vs {page_b}…", "elapsed": 0}
    for evt in run_claude_streaming(prompt, project=proj):
        yield evt
    if save_as:
        try:
            target = wiki_dir / f"{make_slug(save_as)}.md"
            n = 2
            while target.exists():
                target = wiki_dir / f"{make_slug(save_as)}-{n}.md"
                n += 1
            today = datetime.now().strftime("%Y-%m-%d")
            fm = f"""---
title: "{save_as}"
type: comparison
created: {today}
last_updated: {today}
sources: []
tags:
  - comparison
---

# {save_as}

{save_as} comparison created via streaming."""
            target.write_text(fm, encoding="utf-8")
            git_mgr._stage_all(project=proj)
            git_mgr._run("commit", "-m", f"compare{git_mgr._slug_prefix(proj)}: {save_as}")
        except Exception:
            pass


def stream_loop(
    steps=None, include_ingest=False, reflect_window="last-10-ingests",
    project_slug=None, continue_on_error=False,
):
    """SSE streaming version of the wiki loop."""
    if steps is None:
        steps = ["lint", "lint_fix", "reflect"]

    step_generators = {
        "lint": lambda: stream_lint(project_slug=project_slug),
        "lint_fix": lambda: stream_lint_fix(project_slug=project_slug),
        "reflect": lambda: stream_reflect(window=reflect_window, project_slug=project_slug),
    }

    start = time.monotonic()
    yield {"type": "loop_start", "steps": steps, "elapsed": 0}

    # Step 0: ingest if requested
    if include_ingest:
        step_start = time.monotonic()
        yield {"type": "step_start", "step": "ingest", "label": "Ingest", "elapsed": round(time.monotonic() - start, 1)}
        new_sources = wiki_ops.detect_new_sources(project_slug)
        uncited = [s for s in new_sources if not s["cited"]]
        if uncited:
            for src in uncited:
                yield {"type": "step_progress", "step": "ingest", "phase": "starting", "message": f"Ingesting {src['slug']}…"}
                ingest_gen = stream_ingest(src["slug"], "", project_slug=project_slug)
                for evt in ingest_gen:
                    yield evt
        else:
            yield {"type": "step_done", "step": "ingest", "status": "skipped", "reason": "no_new_sources", "elapsed": round(time.monotonic() - step_start, 1)}

    # Main steps
    for step_name in steps:
        step_start = time.monotonic()
        gen_fn = step_generators.get(step_name)
        if not gen_fn:
            yield {"type": "step_done", "step": step_name, "status": "skipped",
                    "reason": f"unknown step: {step_name}", "elapsed": 0}
            continue

        yield {"type": "step_start", "step": step_name, "label": step_name.replace("_", " ").title(),
                "elapsed": round(time.monotonic() - start, 1)}
        for evt in gen_fn():
            evt["step"] = step_name
            yield evt

    yield {"type": "loop_done", "ok": True, "elapsed": round(time.monotonic() - start, 1)}


QUERY_LOG = PROJECT_ROOT / "query-log.jsonl"


def _log_query(question, files_read, wiki_ratio, answer_length, query_log=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question[:200],
        "files_read": files_read,
        "wiki_ratio": wiki_ratio,
        "answer_length": answer_length,
    }
    target = query_log or QUERY_LOG
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _get_query_stats(n=20, query_log=None):
    """Average wiki_ratio of last n queries"""
    target = query_log or QUERY_LOG
    if not target.exists():
        return {"avg_wiki_ratio": None, "count": 0}
    lines = target.read_text("utf-8").strip().split("\n")
    recent = []
    for line in reversed(lines):
        if not line:
            continue
        try:
            recent.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(recent) >= n:
            break
    if not recent:
        return {"avg_wiki_ratio": None, "count": 0}
    ratios = [e["wiki_ratio"] for e in recent if e.get("wiki_ratio") is not None]
    avg = sum(ratios) / len(ratios) if ratios else 0
    return {"avg_wiki_ratio": round(avg, 3), "count": len(recent)}


# ─── wiki data ───

def _normalize_ui_lang(code):
    if not code:
        return None
    c = str(code).strip().lower().replace("_", "-")
    if c.startswith("zh"):
        return "zh"
    if c in ("en", "ko"):
        return c
    return None


def _resolve_project(slug=None):
    """slug → Project.

    - slug is empty/None: fallback active -> legacy (project_registry.get_project default behavior)
    - slug has a specific value but not in registry: propagate KeyError (caller handles as 404)
    """
    return project_registry.get_project(slug or None)


def build_wiki_data(project_slug=None, ui_lang=None):
    """Build wiki data by delegating to the shared graph builder."""
    proj = _resolve_project(project_slug)
    from dashboard.graph.builder import build_wiki_data as _builder_build
    return _builder_build(
        proj.wiki_dir, proj.raw_dir,
        project_slug=proj.slug, ui_lang=ui_lang,
    )


def get_folder_tree(project_slug=None):
    proj = _resolve_project(project_slug)
    wiki_dir = proj.wiki_dir
    tree = {"project": proj.slug, "name": "wiki", "path": "", "children": [], "pages": []}
    if not wiki_dir.exists():
        return tree
    for f in sorted(wiki_dir.glob("*.md")):
        tree["pages"].append(f.name)
    for d in sorted(wiki_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            sub = {"name": d.name, "path": d.name, "children": [], "pages": []}
            for f in sorted(d.rglob("*.md")):
                sub["pages"].append(str(f.relative_to(wiki_dir)))
            for sd in sorted(d.iterdir()):
                if sd.is_dir() and not sd.name.startswith("."):
                    sub["children"].append({"name": sd.name, "path": str(sd.relative_to(wiki_dir)), "pages": [str(f.relative_to(wiki_dir)) for f in sorted(sd.rglob("*.md"))]})
            tree["children"].append(sub)
    return tree


def wiki_hash(project_slug=None):
    """Simple hash for wiki/ change detection — file count + total mtime"""
    proj = _resolve_project(project_slug)
    wiki_dir = proj.wiki_dir
    total = 0
    count = 0
    if wiki_dir.exists():
        for md in wiki_dir.rglob("*.md"):
            total += int(md.stat().st_mtime * 1000)
            count += 1
    return f"{count}:{total}"


# ─── graph analysis APIs (ported from graphify, stdlib-only) ────────────────

def _build_graph_data(proj):
    """Build {nodes, edges} from wiki pages. Returns (nodes, edges, node_map)."""
    data = build_wiki_data(proj.slug)
    nodes = []
    edges = []
    node_map = {}
    # Use already-resolved graph data (edges have basename resolution applied)
    for n in data["graph"]["nodes"]:
        fn = n["id"]
        # Find the full page dict to include all fields; stub nodes won't have one
        pg = next((p for p in data["pages"] if p["filename"] == fn), None)
        if pg:
            node_entry = dict(pg)
        else:
            # Stub/missing node — fill required fields with defaults
            stem = os.path.basename(fn).replace(".md", "").replace("-", " ").title()
            node_entry = {
                "filename": fn, "folder": "", "title": stem, "type": n.get("type", "missing"),
                "created": "", "updated": "", "tags": [], "sources": [],
                "links": [], "word_count": 0, "content": "",
            }
        nodes.append(node_entry)
        node_map[fn] = node_entry
    for e in data["graph"]["edges"]:
        edges.append({"from": e["from"], "to": e["to"]})
    return nodes, edges, node_map


def _build_nx_graph(proj):
    """Build a networkx.Graph from wiki pages and wikilinks.

    Returns (nx.Graph, node_map). Nodes have attrs: label, type, filename.
    Only includes non-system pages (index.md, log.md, overview.md excluded).
    """
    import networkx as nx

    nodes, edges, node_map = _build_graph_data(proj)
    sys_pages = SYSTEM_PAGES
    G = nx.Graph()
    for n in nodes:
        fn = n["filename"]
        if fn not in sys_pages:
            G.add_node(fn,
                       label=n["title"],
                       type=n.get("type", "unknown"),
                       word_count=n.get("word_count", 0),
                       tags=n.get("tags", []))
    for e in edges:
        src, tgt = e["from"], e["to"]
        if src in G and tgt in G:
            G.add_edge(src, tgt)
    return G, node_map


def _graph_build_api(proj):
    nodes, edges, node_map = _build_graph_data(proj)
    return {
        "project": proj.slug,
        "nodes": [{"id": n["filename"], "label": n["title"], "type": n["type"],
                   "word_count": n["word_count"], "tags": n.get("tags", [])} for n in nodes],
        "edges": edges,
    }


def _graph_stats_api(proj):
    nodes, edges, node_map = _build_graph_data(proj)
    sys_pages = SYSTEM_PAGES
    type_counts = {}
    for n in nodes:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
    degree = {n["filename"]: 0 for n in nodes if n["filename"] not in sys_pages}
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1
    n_real = len(degree)
    avg_degree = round(sum(degree.values()) / n_real, 2) if n_real > 0 else 0
    max_possible = n_real * (n_real - 1) / 2 if n_real > 1 else 1
    density = round(len(edges) / max_possible, 4) if max_possible > 0 else 0
    isolated = sum(1 for d in degree.values() if d == 0)
    return {
        "project": proj.slug, "node_count": len(nodes), "edge_count": len(edges),
        "real_nodes": n_real, "type_counts": type_counts, "isolated_pages": isolated,
        "avg_degree": avg_degree, "density": density,
    }


def _graph_god_nodes_api(proj, top_n=10):
    nodes, edges, node_map = _build_graph_data(proj)
    sys_pages = SYSTEM_PAGES
    degree = {n["filename"]: 0 for n in nodes if n["filename"] not in sys_pages}
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1
    sorted_nodes = sorted(degree.items(), key=lambda x: -x[1])
    result = []
    for nid, deg in sorted_nodes[:top_n]:
        n = node_map.get(nid)
        result.append({"id": nid, "label": n["title"] if n else nid,
                       "degree": deg, "type": n["type"] if n else "unknown"})
    return {"project": proj.slug, "god_nodes": result}


def _graph_step_path_api(proj, step_name=""):
    """Return the dependency chain for process steps in the wiki graph."""
    from dashboard.graph.paths import step_dependency_path
    result = step_dependency_path(proj.wiki_dir, step_name)
    result["project"] = proj.slug
    return result


def _graph_community_api_enhanced(proj):
    """Community detection using graphify's Leiden algorithm."""
    G, node_map = _build_nx_graph(proj)
    try:
        comms_raw = cluster(G)  # dict[int, list[str]]
    except Exception as exc:
        sys.stderr.write(f"[graphify cluster failed: {exc}] falling back to BFS\n")
        return _graph_community_api_bfs(proj)
    # Build same output format as BFS
    final_comms = sorted(comms_raw.values(), key=len, reverse=True)
    # Cohesion score (same formula as BFS)
    node_list = [n["filename"] for n in _build_graph_data(proj)[0]]
    _, edges_list, _ = _build_graph_data(proj)

    def cohesion_score(nodes_in_comp):
        nc = len(nodes_in_comp)
        if nc <= 1:
            return 1.0
        comp_set = set(nodes_in_comp)
        actual = sum(1 for e in edges_list if e["from"] in comp_set and e["to"] in comp_set)
        possible = nc * (nc - 1) / 2
        return round(actual / possible, 2) if possible > 0 else 0.0

    final_comms.sort(key=len, reverse=True)
    cohesion = {str(i): cohesion_score(c) for i, c in enumerate(final_comms)}
    return {
        "project": proj.slug,
        "communities": {str(i): c for i, c in enumerate(final_comms)},
        "cohesion": cohesion,
        "community_count": len(final_comms),
    }


def _graph_community_api_bfs(proj):
    """BFS connected components + greedy splitting (original built-in)."""
    from collections import deque
    nodes, edges, node_map = _build_graph_data(proj)
    node_ids = [n["filename"] for n in nodes]
    id_idx = {nid: i for i, nid in enumerate(node_ids)}
    n = len(node_ids)
    adj = [set() for _ in range(n)]
    for e in edges:
        if e["from"] in id_idx and e["to"] in id_idx:
            u, v = id_idx[e["from"]], id_idx[e["to"]]
            adj[u].add(v)
            adj[v].add(u)
    visited = [False] * n
    components = []
    for start in range(n):
        if visited[start]:
            continue
        comp = []
        queue = deque([start])
        visited[start] = True
        while queue:
            u = queue.popleft()
            comp.append(node_ids[u])
            for v in adj[u]:
                if not visited[v]:
                    visited[v] = True
                    queue.append(v)
        components.append(comp)

    def cohesion_score(nodes_in_comp):
        nc = len(nodes_in_comp)
        if nc <= 1:
            return 1.0
        comp_set = set(nodes_in_comp)
        actual = sum(1 for e in edges if e["from"] in comp_set and e["to"] in comp_set)
        possible = nc * (nc - 1) / 2
        return round(actual / possible, 2) if possible > 0 else 0.0

    # Split large communities (>10 nodes)
    final_components = []
    for comp in components:
        if len(comp) <= 10:
            final_components.append(comp)
        else:
            comp_set = set(comp)
            comp_idx = {nid: i for i, nid in enumerate(comp)}
            comp_adj = [set() for _ in range(len(comp))]
            for e in edges:
                if e["from"] in comp_idx and e["to"] in comp_idx:
                    u, v = comp_idx[e["from"]], comp_idx[e["to"]]
                    comp_adj[u].add(v)
                    comp_adj[v].add(u)
            degrees = sorted(range(len(comp)), key=lambda i: len(comp_adj[i]), reverse=True)
            seeds = degrees[:min(2, len(degrees))]
            clusters = [[] for _ in seeds]
            for i in range(len(comp)):
                if i in seeds:
                    continue
                best = max(range(len(seeds)), key=lambda si: len(comp_adj[i] & comp_adj[seeds[si]]), default=0)
                clusters[best].append(comp[i])
            for si, seed in enumerate(seeds):
                clusters[si].append(comp[seed])
            final_components.extend([c for c in clusters if c])

    final_components.sort(key=len, reverse=True)
    cohesion = {i: cohesion_score(c) for i, c in enumerate(final_components)}
    return {
        "project": proj.slug,
        "communities": {str(i): c for i, c in enumerate(final_components)},
        "cohesion": cohesion,
        "community_count": len(final_components),
    }


def _graph_community_api(proj):
    """Route to graphify-enhanced or built-in based on setting."""
    if SETTINGS.get("use_graphify_enhancement") and _GRAPHIFY_AVAILABLE:
        return _graph_community_api_enhanced(proj)
    return _graph_community_api_bfs(proj)


def _graph_shortest_path_api(proj, source, target):
    from collections import deque
    nodes, edges, node_map = _build_graph_data(proj)
    node_lookup = {}
    for n in nodes:
        node_lookup[n["filename"].lower()] = n["filename"]
        node_lookup[n["title"].lower()] = n["filename"]
    src_id = node_lookup.get(source.lower())
    tgt_id = node_lookup.get(target.lower())
    if not src_id:
        return {"ok": False, "error": f"source node not found: {source}"}
    if not tgt_id:
        return {"ok": False, "error": f"target node not found: {target}"}
    if src_id == tgt_id:
        return {"ok": True, "path": [src_id], "hops": 0, "edges": []}
    adj = {n["filename"]: [] for n in nodes}
    for e in edges:
        if e["from"] in adj and e["to"] in adj:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])
    visited = {src_id: None}
    queue = deque([src_id])
    while queue:
        u = queue.popleft()
        if u == tgt_id:
            break
        for v in adj[u]:
            if v not in visited:
                visited[v] = u
                queue.append(v)
    if tgt_id not in visited:
        return {"ok": False, "error": f"no path between '{source}' and '{target}'"}
    path = []
    cur = tgt_id
    while cur is not None:
        path.append(cur)
        cur = visited[cur]
    path.reverse()
    path_edges = [{"from": path[i], "to": path[i + 1]} for i in range(len(path) - 1)]
    return {"ok": True, "path": path, "hops": len(path) - 1, "edges": path_edges}


def _universe_shortest_path_api(source=None, target=None, source_id=None, target_id=None):
    """BFS shortest path on the full universe graph (cross-project).

    Supports both ID-based (source_id/target_id) and label-based (source/target) lookups.
    ID-based is preferred for exact matching across projects.
    """
    from collections import deque
    universe_data = _build_universe_graph()
    nodes = universe_data["nodes"]
    edges = universe_data["edges"]
    bridges = universe_data.get("bridges", [])

    # Build node lookup: prefixed ID → node
    node_lookup = {}
    for n in nodes:
        nid = n["id"]
        node_lookup[nid.lower()] = nid
        node_lookup[n["label"].lower()] = nid
        # Also match by filename without project prefix
        node_lookup[n.get("filename", "").lower()] = nid
        # Merged nodes: also match by original instance IDs
        if n.get("merged") and "instances" in n:
            for inst in n["instances"]:
                inst_id = f"{inst['project']}/{inst['filename']}"
                node_lookup[inst_id.lower()] = nid

    # ID-based lookup (preferred)
    if source_id and target_id:
        src_id = node_lookup.get(source_id.lower())
        tgt_id = node_lookup.get(target_id.lower())
        if not src_id:
            return {"ok": False, "error": f"source node not found: {source_id}"}
        if not tgt_id:
            return {"ok": False, "error": f"target node not found: {target_id}"}
    elif source and target:
        # Fallback: label-based lookup (legacy)
        src_id = node_lookup.get(source.lower())
        tgt_id = node_lookup.get(target.lower())
        if not src_id:
            return {"ok": False, "error": f"source node not found: {source}"}
        if not tgt_id:
            return {"ok": False, "error": f"target node not found: {target}"}
    else:
        return {"ok": False, "error": "missing source_id/target_id or source/target"}

    if src_id == tgt_id:
        return {"ok": True, "path": [src_id], "hops": 0, "edges": []}

    # Build adjacency list from project edges + bridge edges
    adj = {n["id"]: [] for n in nodes}
    for e in edges:
        s, t = e["source"], e["target"]
        if s in adj and t in adj:
            adj[s].append(t)
            adj[t].append(s)
    for b in bridges:
        s, t = b.get("from_node", ""), b.get("to_node", "")
        if s and t and s in adj and t in adj:
            adj[s].append(t)
            adj[t].append(s)

    # BFS — skip system/* nodes as intermediate hops to avoid artificial
    # connectivity through the global index/log hubs.
    visited = {src_id: None}
    queue = deque([src_id])
    while queue:
        u = queue.popleft()
        if u == tgt_id:
            break
        for v in adj[u]:
            if v not in visited and not v.startswith("system/"):
                visited[v] = u
                queue.append(v)

    if tgt_id not in visited:
        src_label = source_id or source or src_id
        tgt_label = target_id or target or tgt_id
        return {"ok": False, "error": f"no path between '{src_label}' and '{tgt_label}'"}

    path = []
    cur = tgt_id
    while cur is not None:
        path.append(cur)
        cur = visited[cur]
    path.reverse()

    path_edges = [{"source": path[i], "target": path[i + 1]} for i in range(len(path) - 1)]
    return {"ok": True, "path": path, "hops": len(path) - 1, "edges": path_edges}


def _read_page_content_snippet(proj, filename: str, max_chars: int = 800) -> dict | None:
    """Read a wiki page and return a content snippet."""
    fp = proj.wiki_dir / filename
    if not fp.exists():
        return None
    text = fp.read_text("utf-8")
    meta, body = parse_fm(text)
    return {
        "filename": filename,
        "title": meta.get("title", filename.replace(".md", "").replace("-", " ").title()),
        "type": meta.get("type", "unknown"),
        "tags": meta.get("tags", []),
        "status": meta.get("status", "active"),
        "confidence": meta.get("confidence", ""),
        "snippet": body[:max_chars].strip(),
        "word_count": len(body.split()),
    }


def _shortest_path_with_content_api(proj, source, target):
    """Project-level shortest path with page content."""
    path_result = _graph_shortest_path_api(proj, source, target)
    if not path_result.get("ok"):
        return path_result
    content = []
    for fn in path_result.get("path", []):
        snippet = _read_page_content_snippet(proj, fn)
        if snippet:
            content.append(snippet)
    path_result["content"] = content
    return path_result


def _universe_path_with_content_api(source_id=None, target_id=None, source=None, target=None):
    """Universe-level shortest path with page content."""
    path_result = _universe_shortest_path_api(
        source_id=source_id, target_id=target_id, source=source, target=target
    )
    if not path_result.get("ok"):
        return path_result
    content = []
    for nid in path_result.get("path", []):
        if nid.startswith("system/"):
            content.append({
                "id": nid,
                "title": nid.split("/")[1].title(),
                "type": "system",
                "snippet": "",
                "word_count": 0,
            })
            continue
        # Merged node: read content from all instances
        if nid.startswith("title:"):
            label = nid[6:]
            universe_data = _build_universe_graph()
            for n in universe_data["nodes"]:
                if n.get("merged") and n["label"] == label:
                    for inst in n.get("instances", []):
                        try:
                            proj = _resolve_project(inst["project"])
                            snippet = _read_page_content_snippet(proj, inst["filename"])
                            if snippet:
                                snippet["id"] = nid
                                snippet["project"] = inst["project"]
                                snippet["instance_filename"] = inst["filename"]
                                content.append(snippet)
                        except Exception:
                            pass
                    break
            continue
        parts = nid.split("/", 1)
        if len(parts) != 2:
            continue
        proj_slug, filename = parts
        try:
            proj = _resolve_project(proj_slug)
            snippet = _read_page_content_snippet(proj, filename)
            if snippet:
                snippet["id"] = nid
                snippet["project"] = proj_slug
                content.append(snippet)
        except Exception:
            pass
    path_result["content"] = content
    return path_result


def _graph_neighbors_api(proj, node_id):
    nodes, edges, node_map = _build_graph_data(proj)
    node_lookup = {}
    for n in nodes:
        node_lookup[n["filename"].lower()] = n["filename"]
        node_lookup[n["title"].lower()] = n["filename"]
    nid = node_lookup.get(node_id.lower())
    if not nid:
        return {"ok": False, "error": f"node not found: {node_id}"}
    neighbors = []
    seen = set()
    for e in edges:
        if e["from"] == nid and e["to"] not in seen:
            seen.add(e["to"])
            info = node_map.get(e["to"])
            neighbors.append({"id": e["to"], "label": info["title"] if info else e["to"],
                              "type": info["type"] if info else "unknown", "relation": "wikilink"})
        elif e["to"] == nid and e["from"] not in seen:
            seen.add(e["from"])
            info = node_map.get(e["from"])
            neighbors.append({"id": e["from"], "label": info["title"] if info else e["from"],
                              "type": info["type"] if info else "unknown", "relation": "wikilink"})
    info = node_map.get(nid)
    return {
        "ok": True, "project": proj.slug,
        "node": {"id": nid, "label": info["title"] if info else nid,
                 "type": info["type"] if info else "unknown"},
        "neighbors": neighbors, "neighbor_count": len(neighbors),
    }


def _graph_insights_api(proj):
    nodes, edges, node_map = _build_graph_data(proj)
    sys_pages = SYSTEM_PAGES
    degree = {n["filename"]: 0 for n in nodes}
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1
    cross_type = []
    for e in edges:
        src = node_map.get(e["from"])
        tgt = node_map.get(e["to"])
        if src and tgt and src["type"] != tgt["type"]:
            cross_type.append({"from": e["from"], "from_type": src["type"],
                               "to": e["to"], "to_type": tgt["type"]})
    isolated = []
    for nid, deg in degree.items():
        if deg <= 1 and nid not in sys_pages:
            info = node_map.get(nid)
            isolated.append({"id": nid, "label": info["title"] if info else nid,
                             "type": info["type"] if info else "unknown", "degree": deg})
    from collections import deque
    node_ids = [n["filename"] for n in nodes if n["filename"] not in sys_pages]
    adj = {nid: [] for nid in node_ids}
    for e in edges:
        if e["from"] in adj and e["to"] in adj:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])
    def count_components(exclude=None):
        remaining = [nid for nid in node_ids if nid != exclude]
        if not remaining:
            return 0
        vis = set()
        comps = 0
        for start in remaining:
            if start in vis:
                continue
            comps += 1
            q = deque([start])
            vis.add(start)
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v != exclude and v not in vis:
                        vis.add(v)
                        q.append(v)
        return comps
    base_comps = count_components()
    bridges = []
    for nid in node_ids:
        if degree.get(nid, 0) < 2:
            continue
        new_comps = count_components(exclude=nid)
        if new_comps > base_comps:
            info = node_map.get(nid)
            bridges.append({"id": nid, "label": info["title"] if info else nid,
                            "type": info["type"] if info else "unknown",
                            "degree": degree[nid], "components_if_removed": new_comps})
    bridges.sort(key=lambda x: -x["components_if_removed"])

    # Graphify-enhanced surprising connections
    sc_suggestions = []
    if SETTINGS.get("use_graphify_enhancement") and _GRAPHIFY_AVAILABLE:
        try:
            G, _ = _build_nx_graph(proj)
            comm_result = _graph_community_api(proj)
            comms = {int(k): v for k, v in comm_result.get("communities", {}).items()}
            sc_list = surprising_connections(G, communities=comms, top_n=5)
            for sc in sc_list:
                # graphify returns node LABELS (titles), not filenames
                src_label = sc.get("source", "?")
                tgt_label = sc.get("target", "?")
                score = sc.get("relation", "") or sc.get("confidence", "unknown")
                label = f"{src_label} ↔ {tgt_label} ({score})"
                sc_suggestions.append(label)
        except Exception as exc:
            sys.stderr.write(f"[surprising_connections failed: {exc}] skipping\n")

    suggestions = []
    for s in sc_suggestions:
        suggestions.append("[Enhanced] " + s)
    if isolated:
        suggestions.append(f"{len(isolated)} isolated page(s) found — consider adding more wikilinks")
    if bridges:
        suggestions.append(f"{len(bridges)} bridge page(s) detected — these connect separate graph regions")
    if cross_type:
        suggestions.append(f"{len(cross_type)} cross-type connection(s) found")
    return {
        "project": proj.slug,
        "cross_type": cross_type[:20],
        "bridges": bridges[:10],
        "isolated": isolated[:20],
        "suggestions": suggestions,
    }


def _graph_export_api(proj, fmt="json"):
    nodes, edges, node_map = _build_graph_data(proj)
    if fmt == "json":
        out = proj.root / "graph-export.json"
        out.write_text(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        return {"ok": True, "project": proj.slug, "path": str(out.relative_to(PROJECT_ROOT)), "format": "json"}
    if fmt == "html":
        nodes_json = json.dumps(nodes, ensure_ascii=False)
        edges_json = json.dumps(edges, ensure_ascii=False)
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Memex Graph</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,sans-serif;overflow:hidden}}
canvas{{width:100vw;height:100vh;cursor:grab}}
#legend{{position:fixed;bottom:12px;left:12px;background:#161b22ee;border:1px solid #30363d;border-radius:8px;padding:8px 12px;font-size:11px}}
#legend span{{display:inline-flex;align-items:center;gap:4px;margin-right:12px}}
#legend i{{width:8px;height:8px;border-radius:50%;display:inline-block}}
#info{{position:fixed;top:12px;left:12px;background:#161b22ee;border:1px solid #30363d;border-radius:8px;padding:6px 10px;font-size:11px;color:#8b949e}}
</style></head><body>
<div id="info">{len(nodes)} nodes · {len(edges)} edges · click a node to highlight</div>
<div id="legend"></div>
<canvas id="cv"></canvas>
<script>
var TC={{source:'#059669',entity:'#2563eb',concept:'#7c3aed',analysis:'#39d2c0',overview:'#8b949e',missing:'#f85149',unknown:'#8b949e','process-step':'#16a34a','process-card':'#15803d','metric-card':'#7c3aed','org-card':'#2563eb','rule-card':'#d97706'}};
var nodes={nodes_json},edges={edges_json};
var cv=document.getElementById('cv'),ctx=cv.getContext('2d');
function resize(){{cv.width=innerWidth*devicePixelRatio;cv.height=innerHeight*devicePixelRatio;ctx.scale(devicePixelRatio,devicePixelRatio);}}
resize();addEventListener('resize',resize);
var W=innerWidth,H=innerHeight;
var ns=nodes.map(function(n){{return {{...n,x:W/2+(Math.random()-.5)*400,y:H/2+(Math.random()-.5)*400,vx:0,vy:0,r:n.type==='overview'?16:10}};}});
var nm={{}};ns.forEach(function(n){{nm[n.id]=n;}});
var es=edges.filter(function(e){{return nm[e.from]&&nm[e.to];}}).map(function(e){{return {{s:nm[e.from],t:nm[e.to]}};}});
var hov=null,drag=null;
var types={{}};ns.forEach(function(n){{types[n.type]=true;}});
var lg=document.getElementById('legend');
Object.keys(types).forEach(function(tp){{lg.innerHTML+='<span><i style="background:'+(TC[tp]||'#8b949e')+'"></i>'+tp+'</span>';}});
// Progressive render: reveal nodes in layers with fade-in/scale animation
var RENDER_DELAY_MS=150,BATCH_SIZE=6,_t0=performance.now();
var _revealOrder=[];ns.forEach(function(n){{if(n.type==='process-step')_revealOrder.unshift(n);else _revealOrder.push(n);}});
var _nextIdx=0,_lastT=0;
for(var i in ns){{ns[i].alpha=0;ns[i].scale=0;ns[i].visible=false;}}
for(var j in es){{es[j].alpha=0;}}

function tick(now){{
  if(_nextIdx<_revealOrder.length&&now-_lastT>RENDER_DELAY_MS){{
    for(var b=0;b<BATCH_SIZE&&_nextIdx<_revealOrder.length;b++)_revealOrder[_nextIdx++].visible=true;
    _lastT=now;
  }}
  var cx=W/2,cy=H/2;
  for(var n of ns){{n.vx+=(cx-n.x)*.001;n.vy+=(cy-n.y)*.001;}}
  for(var i=0;i<ns.length;i++)for(var j=i+1;j<ns.length;j++){{
    var a=ns[i],b=ns[j],dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=1200/(d*d);
    a.vx-=dx/d*f;a.vy-=dy/d*f;b.vx+=dx/d*f;b.vy+=dy/d*f;
  }}
  for(var e of es){{
    var dx2=e.t.x-e.s.x,dy2=e.t.y-e.s.y,d2=Math.sqrt(dx2*dx2+dy2*dy2)||1,f2=(d2-140)*.004;
    e.s.vx+=dx2/d2*f2;e.s.vy+=dy2/d2*f2;e.t.vx-=dx2/d2*f2;e.t.vy-=dy2/d2*f2;
  }}
  for(var n of ns){{
    if(n===drag)continue;n.vx*=.82;n.vy*=.82;
    n.x+=n.vx;n.y+=n.vy;n.x=Math.max(n.r,Math.min(W-n.r,n.x));n.y=Math.max(n.r,Math.min(H-n.r,n.y));
    if(n.visible){{n.alpha=Math.min(1,n.alpha+.05);n.scale=Math.min(1,n.scale+.05);}}
  }}
  ctx.clearRect(0,0,W,H);
  for(var e of es){{
    if(!e.s.visible||!e.t.visible)continue;e.alpha=Math.min(1,e.alpha+.04);
    var hi=hov&&(e.s.id===hov.id||e.t.id===hov.id);
    ctx.globalAlpha=e.alpha;ctx.strokeStyle=hi?'#58a6ff66':'#30363d';ctx.lineWidth=hi?2:1;
    ctx.beginPath();ctx.moveTo(e.s.x,e.s.y);ctx.lineTo(e.t.x,e.t.y);ctx.stroke();
    ctx.globalAlpha=1;
  }}
  for(var n of ns){{
    if(!n.visible)continue;
    var c=TC[n.type]||'#8b949e',hi=hov&&hov.id===n.id,s=n.scale;
    ctx.save();ctx.translate(n.x,n.y);ctx.scale(s,s);
    ctx.beginPath();ctx.arc(0,0,n.r,0,Math.PI*2);
    ctx.fillStyle=hi?c:c+'88';ctx.fill();
    if(hi){{ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();}}
    ctx.restore();
    ctx.fillStyle=hi?'#e6edf3':'#8b949e';ctx.font=(hi?'12':'10')+'px sans-serif';ctx.textAlign='center';
    ctx.fillText(n.label,n.x,n.y+n.r+13);
  }}
  requestAnimationFrame(tick);
}}
function hit(mx,my){{for(var n of ns){{var dx=mx-n.x,dy=my-n.y;if(dx*dx+dy*dy<(n.r+8)**2)return n;}}return null;}}
cv.onmousemove=function(e){{var r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;if(drag){{drag.x=mx;drag.y=my;drag.vx=0;drag.vy=0;return;}}hov=hit(mx,my);cv.style.cursor=hov?'pointer':'default';}};
cv.onmousedown=function(e){{var r=cv.getBoundingClientRect();drag=hit(e.clientX-r.left,e.clientY-r.top);}};
cv.onmouseup=function(){{drag=null;}};
tick();
</script></body></html>"""
        out = proj.root / "graph-export.html"
        out.write_text(html, encoding="utf-8")
        return {"ok": True, "project": proj.slug, "path": str(out.relative_to(PROJECT_ROOT)), "format": "html"}
    return {"ok": False, "error": f"unsupported format: {fmt}"}


# ─── enhanced composite graph API (with persistence) ─────────────────────────

# Optional graphify integration (partial imports allowed)
_GRAPHIFY_AVAILABLE = False
try:
    from graphify.cluster import cluster
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
except ImportError:
    cluster = god_nodes = surprising_connections = suggest_questions = None
try:
    from graphify.export import generate_html as graphify_export_html
except ImportError:
    graphify_export_html = None
if cluster is not None:
    _GRAPHIFY_AVAILABLE = True

def _get_graph_dir(proj):
    """Get the .graph directory for a project, creating it if needed."""
    graph_dir = proj.root / ".graph"
    graph_dir.mkdir(exist_ok=True)
    return graph_dir

def _load_persisted_graph(proj):
    """Load persisted graph data if available, returns None otherwise."""
    graph_dir = _get_graph_dir(proj)
    graph_file = graph_dir / "graph.json"
    labels_file = graph_dir / "community_labels.json"

    if not graph_file.exists():
        return None

    try:
        data = json.loads(graph_file.read_text(encoding="utf-8"))
        if labels_file.exists():
            data["community_labels"] = json.loads(labels_file.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None

def _persist_graph(proj, graph_data):
    """Persist graph data to .graph directory."""
    graph_dir = _get_graph_dir(proj)

    # Save main graph
    graph_file = graph_dir / "graph.json"
    graph_file.write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save community labels separately if present
    if "community_labels" in graph_data:
        labels_file = graph_dir / "community_labels.json"
        labels_file.write_text(json.dumps(graph_data["community_labels"], ensure_ascii=False, indent=2), encoding="utf-8")

def _graph_composite_api(proj):
    """Get composite graph data (nodes + edges + communities + cohesion + labels)."""
    # First try to load persisted graph
    persisted = _load_persisted_graph(proj)
    if persisted:
        persisted["project"] = proj.slug
        persisted["persisted"] = True
        return persisted

    # Otherwise build from scratch
    nodes, edges, node_map = _build_graph_data(proj)
    community_result = _graph_community_api(proj)

    result = {
        "project": proj.slug,
        "persisted": False,
        "graphify_enhanced": _GRAPHIFY_AVAILABLE,
        "nodes": [{"id": n["filename"], "label": n["title"], "type": n["type"],
                   "word_count": n["word_count"], "tags": n.get("tags", [])} for n in nodes],
        "edges": edges,
        "communities": community_result["communities"],
        "cohesion": community_result["cohesion"],
        "community_count": community_result["community_count"],
        "community_labels": {},
    }

    return result

def _graph_rebuild_api(proj):
    """Rebuild and persist the graph."""
    nodes, edges, node_map = _build_graph_data(proj)
    community_result = _graph_community_api(proj)

    result = {
        "nodes": [{"id": n["filename"], "label": n["title"], "type": n["type"],
                   "word_count": n["word_count"], "tags": n.get("tags", [])} for n in nodes],
        "edges": edges,
        "communities": community_result["communities"],
        "cohesion": community_result["cohesion"],
        "community_count": community_result["community_count"],
        "community_labels": {},
    }

    # Persist the graph
    _persist_graph(proj, result)

    return {
        "ok": True,
        "project": proj.slug,
        "graphify_enhanced": _GRAPHIFY_AVAILABLE,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "community_count": community_result["community_count"],
    }

def _graph_name_community_api(proj, community_id, name):
    """Set a human-readable name for a community."""
    # Load current persisted graph or build new one
    data = _load_persisted_graph(proj)
    if not data:
        # Build and persist first
        _graph_rebuild_api(proj)
        data = _load_persisted_graph(proj)

    # Update the label
    if "community_labels" not in data:
        data["community_labels"] = {}
    data["community_labels"][community_id] = name

    # Persist
    _persist_graph(proj, data)

    return {
        "ok": True,
        "project": proj.slug,
        "community_id": community_id,
        "name": name,
    }

def _graph_get_community_api(proj, community_id):
    """Get detailed information about a specific community."""
    composite = _graph_composite_api(proj)

    communities = composite.get("communities", {})
    if community_id not in communities:
        return {"ok": False, "error": f"Community not found: {community_id}"}

    node_ids = communities[community_id]
    cohesion = composite.get("cohesion", {}).get(community_id, 0)
    label = composite.get("community_labels", {}).get(community_id, f"Community {community_id}")

    # Get full node info
    node_map = {n["id"]: n for n in composite.get("nodes", [])}
    nodes = [node_map.get(nid, {"id": nid, "label": nid}) for nid in node_ids]

    return {
        "ok": True,
        "project": proj.slug,
        "community_id": community_id,
        "name": label,
        "cohesion": cohesion,
        "node_count": len(nodes),
        "nodes": nodes,
    }


# ─── knowledge universe (cross-project) ───

_UNIVERSE_CONFIG_FILE = PROJECT_ROOT / ".memex" / "universe_config.json"


def _load_universe_config() -> dict:
    """Load universe configuration."""
    if _UNIVERSE_CONFIG_FILE.exists():
        try:
            return json.loads(_UNIVERSE_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "version": 1,
        "auto_join_new": False,
        "auto_join_import": True,
        "auto_join_sync": True,
        "default_view": "2d",
        "excluded_projects": [],
        "pending_confirmation": [],
        "known_projects": [],
        "galaxy_positions": {},
    }


def _save_universe_config(config: dict):
    """Save universe configuration."""
    _UNIVERSE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _UNIVERSE_CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _universe_project_nodes(proj):
    """Build graph data for a single project with project-prefixed IDs.

    Excludes system pages (index.md, log.md, overview.md) — these are
    consolidated into global hub nodes by _build_universe_graph().

    Detects cross-project wikilinks ([[project-slug/page]]) and preserves
    them as direct cross-project edges without local-project prefixing.
    """
    nodes, edges, node_map = _build_graph_data(proj)
    prefixed_nodes = []
    prefixed_edges = []
    sys_pages = SYSTEM_PAGES

    # Collect known project slugs for cross-project link detection
    known_slugs = {p.slug for p in project_registry.list_projects()}

    for n in nodes:
        if n["filename"] in sys_pages:
            continue
        nid = f"{proj.slug}/{n['filename']}"
        prefixed_nodes.append({
            "id": nid,
            "label": n.get("label", n["title"]),
            "type": n.get("type", "unknown"),
            "filename": n["filename"],
            "word_count": n.get("word_count", 0),
            "tags": n.get("tags", []),
            "project": proj.slug,
            "project_title": proj.title,
            "status": n.get("status", "active"),
            "confidence": n.get("confidence", ""),
        })

    for e in edges:
        src_id = f"{proj.slug}/{e['from']}"
        tgt_raw = e['to']

        # Check if target is a cross-project wikilink: [[other-project/page]]
        xp_link = None
        if '/' in tgt_raw:
            from dashboard.models import parse_cross_project_link
            xp_link = parse_cross_project_link(tgt_raw)
        if xp_link and xp_link["project_slug"] in known_slugs:
            tgt_path = xp_link["page_path"]
            if not tgt_path.endswith('.md'):
                tgt_path += '.md'
            tgt_id = f"{xp_link['project_slug']}/{tgt_path}"
            prefixed_edges.append({
                "source": src_id,
                "target": tgt_id,
                "type": "cross-project",
                "project": proj.slug,
            })
        else:
            tgt_id = f"{proj.slug}/{tgt_raw}"
            prefixed_edges.append({
                "source": src_id,
                "target": tgt_id,
                "type": "wikilink",
                "project": proj.slug,
            })

    return prefixed_nodes, prefixed_edges, node_map


def _detect_cross_project_bridges(all_nodes: list) -> list:
    """Detect cross-project connections based on title similarity and tag overlap."""
    import re as _re
    bridges = []
    from collections import defaultdict as _dd

    # Group by normalized title
    title_map = _dd(list)
    for n in all_nodes:
        key = _re.sub(r'[^a-z0-9]+', '', n["label"].lower())
        if len(key) > 4:
            title_map[key].append(n)

    for key, nodes in title_map.items():
        if len(nodes) < 2:
            continue
        projects = set(n["project"] for n in nodes)
        if len(projects) < 2:
            continue
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if nodes[i]["project"] != nodes[j]["project"]:
                    bridges.append({
                        "from_node": nodes[i]["id"],
                        "from_title": nodes[i]["label"],
                        "from_project": nodes[i]["project"],
                        "to_node": nodes[j]["id"],
                        "to_title": nodes[j]["label"],
                        "to_project": nodes[j]["project"],
                        "similarity": 0.85,
                        "reason": "标题相同或高度相似",
                        "_title_bridge": True,
                    })

    # Also check tag overlap
    tag_map = _dd(list)
    for n in all_nodes:
        for tag in n.get("tags", []):
            tag_map[tag.lower()].append(n)

    for tag, nodes in tag_map.items():
        if len(nodes) < 2:
            continue
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if nodes[i]["project"] != nodes[j]["project"]:
                    exists = any(
                        b["from_node"] == nodes[i]["id"] and b["to_node"] == nodes[j]["id"]
                        for b in bridges
                    )
                    if not exists:
                        bridges.append({
                            "from_node": nodes[i]["id"],
                            "from_title": nodes[i]["label"],
                            "from_project": nodes[i]["project"],
                            "to_node": nodes[j]["id"],
                            "to_title": nodes[j]["label"],
                            "to_project": nodes[j]["project"],
                            "similarity": 0.5,
                            "reason": f"共享标签: {tag}",
                        })

    return bridges


def _merge_instance_tags(group: list) -> list:
    """Merge tags from all instances, preserving order and deduplicating."""
    seen = set()
    merged = []
    for n in group:
        for t in n.get("tags", []):
            if t not in seen:
                seen.add(t)
                merged.append(t)
    return merged


def _best_instance_status(group: list) -> str:
    """Pick the best status from all instances (active > draft > archived)."""
    priority = {"active": 3, "draft": 2, "archived": 1}
    best = max(group, key=lambda n: priority.get(n.get("status", "draft"), 0))
    return best.get("status", "active")


def _best_instance_confidence(group: list) -> str:
    """Pick the first non-empty confidence from all instances."""
    for n in group:
        c = n.get("confidence", "")
        if c:
            return c
    return ""


def _consolidate_same_title_nodes(nodes: list, edges: list) -> tuple:
    """Group nodes by exact title (label) across projects.

    When multiple projects share the same frontmatter title, merge them
    into a single node with an ``instances`` array.  Edges are remapped
    so that any edge whose both endpoints are merged gets deduplicated
    at the merged-node level.
    """
    from collections import defaultdict as _dd

    # 1. Group by exact label
    label_map: dict[str, list] = _dd(list)
    for n in nodes:
        label_map[n["label"]].append(n)

    # Mapping: original_id -> merged_id (or None if not merged)
    id_to_merged: dict[str, str] = {}
    merged_nodes: list[dict] = []
    non_merged: list[dict] = []

    for label, group in label_map.items():
        projects = set(n["project"] for n in group)
        if len(projects) >= 2:
            # Multi-project → merge
            merged_id = f"title:{label}"
            merged_nodes.append({
                "id": merged_id,
                "label": label,
                "type": group[0].get("type", "unknown"),
                "merged": True,
                "instances": [
                    {
                        "project": n["project"],
                        "project_title": n.get("project_title", n["project"]),
                        "filename": n["filename"],
                        "type": n.get("type", "unknown"),
                        "status": n.get("status", "active"),
                        "confidence": n.get("confidence", ""),
                        "tags": n.get("tags", []),
                    }
                    for n in group
                ],
                "tags": _merge_instance_tags(group),
                "status": _best_instance_status(group),
                "confidence": _best_instance_confidence(group),
            })
            for n in group:
                id_to_merged[n["id"]] = merged_id
        else:
            non_merged.extend(group)

    # 2. Remap edges
    seen_pairs: set = set()
    remapped_edges: list[dict] = []
    for e in edges:
        src = id_to_merged.get(e["source"], e["source"])
        tgt = id_to_merged.get(e["target"], e["target"])
        if src == tgt:
            continue  # self-loop after merge → skip
        pair_key = "|||".join(sorted([src, tgt]))
        if pair_key in seen_pairs:
            continue  # deduplicate
        seen_pairs.add(pair_key)
        remapped_edges.append({
            "source": src,
            "target": tgt,
            "type": e.get("type", "wikilink"),
            "project": e.get("project", ""),
        })

    all_nodes = merged_nodes + non_merged
    return all_nodes, remapped_edges, id_to_merged


def _build_universe_graph(include_hidden: bool = False) -> dict:
    """构建全项目统一图谱。

    System pages (index.md, log.md) are consolidated into two global hub
    nodes (system/index, system/log) to avoid artificial hub effects
    that inflate project-internal distances.

    Cross-project nodes with the same frontmatter title are merged into
    a single node with an ``instances`` array listing each project's copy.
    """
    config = _load_universe_config()
    excluded = set(config.get("excluded_projects", []))

    all_nodes = []
    all_edges = []
    project_info = {}

    for proj in project_registry.list_projects():
        if not include_hidden and proj.slug in excluded:
            continue

        nodes, edges, node_map = _universe_project_nodes(proj)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

        project_info[proj.slug] = {
            "title": proj.title,
            "description": proj.description,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    # Detect bridges on original nodes (before title consolidation)
    pre_bridges = _detect_cross_project_bridges(all_nodes)

    # Consolidate same-title nodes across projects
    all_nodes, all_edges, _id_to_merged = _consolidate_same_title_nodes(
        all_nodes, all_edges
    )

    # Remap bridge node IDs through consolidation mapping.
    # Title bridges become self-loops (both ends map to same merged node) → drop.
    # Tag-only bridges that still connect different nodes → keep.
    bridges = []
    for b in pre_bridges:
        new_src = _id_to_merged.get(b["from_node"], b["from_node"])
        new_tgt = _id_to_merged.get(b["to_node"], b["to_node"])
        if new_src == new_tgt:
            continue  # self-loop after consolidation
        bridge = dict(b)
        bridge["from_node"] = new_src
        bridge["to_node"] = new_tgt
        bridges.append(bridge)

    # Add surviving bridge connections as INFERRED edges in the graph.
    # Without this, bridge connections exist only as metadata — merged nodes
    # that are linked by bridges but have no wikilinks appear as orphans (degree=0)
    # in the force layout.
    for b in bridges:
        all_edges.append({
            "source": b["from_node"],
            "target": b["to_node"],
            "type": "INFERRED",
            "project": "",
            "bridge": True,
        })

    # Explicit cross-project wikilinks ([[project-slug/page]]) already
    # created as type:"cross-project" edges in _universe_project_nodes.
    # Register them as bridges too so they render with dashed styling.
    for e in all_edges:
        if e.get("type") == "cross-project":
            bridges.append({
                "from_node": e["source"],
                "to_node": e["target"],
                "from_title": "",
                "from_project": e.get("project", ""),
                "to_title": "",
                "to_project": e["target"].split("/", 1)[0] if "/" in e["target"] else "",
                "similarity": 1.0,
                "reason": "显式跨项目 wikilink",
                "_explicit_cross_project": True,
            })

    # Build global hub nodes for index.md, log.md, and overview.md
    sys_hubs = {
        "system/index": {
            "id": "system/index", "label": "Index",
            "type": "system", "filename": "index.md",
            "word_count": 0, "tags": [],
            "project": "system", "project_title": "System",
            "status": "active", "confidence": "",
        },
        "system/log": {
            "id": "system/log", "label": "Log",
            "type": "system", "filename": "log.md",
            "word_count": 0, "tags": [],
            "project": "system", "project_title": "System",
            "status": "active", "confidence": "",
        },
        "system/overview": {
            "id": "system/overview", "label": "Overview",
            "type": "system", "filename": "overview.md",
            "word_count": 0, "tags": [],
            "project": "system", "project_title": "System",
            "status": "active", "confidence": "",
        },
    }
    all_node_ids = {n["id"] for n in all_nodes} | set(sys_hubs.keys())

    # Remap edges: project-level index.md/log.md/overview.md → system hubs, then
    # apply title-consolidation ID mapping.
    hub_map = {}
    for proj in project_registry.list_projects():
        if not include_hidden and proj.slug in excluded:
            continue
        for sp in SYSTEM_PAGES:
            hub_map[f"{proj.slug}/{sp}"] = f"system/{sp}"

    final_edges = []
    seen_pairs = set()
    for e in all_edges:
        src = e["source"]
        tgt = e["target"]
        # Step 1: redirect to system hubs
        if src in hub_map:
            src = hub_map[src]
        if tgt in hub_map:
            tgt = hub_map[tgt]
        # Step 2: apply title-consolidation ID mapping
        src = _id_to_merged.get(src, src)
        tgt = _id_to_merged.get(tgt, tgt)
        if src == tgt:
            continue  # self-loop
        pair_key = "|||".join(sorted([src, tgt]))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        if src in all_node_ids and tgt in all_node_ids:
            new_edge = dict(e)
            new_edge["source"] = src
            new_edge["target"] = tgt
            final_edges.append(new_edge)

    all_edges = final_edges
    all_nodes.extend(sys_hubs.values())

    merged_count = sum(1 for n in all_nodes if n.get("merged"))
    return {
        "universe": {
            "total_nodes": len(all_nodes),
            "total_edges": len(all_edges),
            "projects": project_info,
            "merged_nodes": merged_count,
        },
        "nodes": all_nodes,
        "edges": all_edges,
        "bridges": bridges,
    }


def _universe_dimension_aggregation(dimension: str = "") -> dict:
    """Aggregate nodes across all process-knowledge projects by dimension.

    Groups nodes by dimension type (org/rules/metrics/concepts) across all
    process-knowledge projects. Each group shows project-level subgroups.

    Args:
        dimension: filter to a specific dimension (org/rules/metrics/concepts).
                   Empty = return all dimensions.
    """
    all_dims = {"org", "rules", "metrics", "concepts"}
    target_dims = {dimension} if dimension in all_dims else all_dims

    result: dict[str, dict] = {d: {"projects": {}, "total_nodes": 0} for d in target_dims}

    for proj in project_registry.list_projects():
        if proj.template != "process-knowledge":
            continue
        dim_nodes: dict[str, list] = {d: [] for d in target_dims}
        wiki_dir = proj.root / "wiki"
        if not wiki_dir.is_dir():
            continue

        for md_file in sorted(wiki_dir.glob("**/*.md")):
            rel = str(md_file.relative_to(wiki_dir))
            try:
                text = md_file.read_text(encoding="utf-8")
                meta, _ = parse_fm(text)
                # Determine dimension from folder path
                folder = rel.split("/")[0] if "/" in rel else ""
                wp_type = meta.get("type", "unknown")
                # Classify: folder-based dimension OR card type mapping
                dim = None
                if folder in target_dims:
                    dim = folder
                elif wp_type == "metric-card":
                    dim = "metrics"
                elif wp_type == "org-card":
                    dim = "org"
                elif wp_type == "rule-card":
                    dim = "rules"
                elif wp_type == "process-card":
                    dim = "concepts"

                if dim and dim in target_dims:
                    dim_nodes[dim].append({
                        "id": rel,
                        "title": meta.get("title", md_file.stem),
                        "type": wp_type,
                        "folder": folder,
                    })
            except Exception:
                pass

        proj_slug = proj.slug
        for dim_name, nodes in dim_nodes.items():
            if nodes:
                result[dim_name]["projects"][proj_slug] = {
                    "title": proj.title,
                    "nodes": nodes,
                    "count": len(nodes),
                }
                result[dim_name]["total_nodes"] += len(nodes)

    return {"ok": True, "dimensions": result}


# ─── status ───

def _paths_match(a: str, b: str) -> bool:
    """Check if two paths are the same using multiple methods. Handles platform/symlink/case differences."""
    if not a or not b:
        return False
    # 1. direct string comparison
    if a == b:
        return True
    # 2. Path.resolve() comparison (symlink resolution)
    try:
        if Path(a).resolve() == Path(b).resolve():
            return True
    except Exception:
        pass
    # 3. normpath + normcase (Windows/macOS case-insensitive)
    try:
        if os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b)):
            return True
    except Exception:
        pass
    # 4. samefile (both paths same inode)
    try:
        if Path(a).samefile(Path(b)):
            return True
    except Exception:
        pass
    return False


def _read_obsidian_facts():
    """Read and return only facts from Obsidian. No judgment/labels.

    Returns:
        process_running: bool (pgrep Obsidian result)
        config_path: str | None (discovered Obsidian config file path)
        vault_registered: bool (this project is registered as a vault)
        vault_open: bool | None (open flag of registered vault. None if not registered)
        vault_last_ts: int | None (last access timestamp in ms)
        project_path: str (for debugging - current project absolute path)
        registered_vaults: list[str] (for debugging - all vault paths in obsidian.json)
    """
    facts = {
        "process_running": False,
        "config_path": None,
        "vault_registered": False,
        "vault_open": None,
        "vault_last_ts": None,
        "project_path": str(PROJECT_ROOT.resolve()),
        "registered_vaults": [],
    }

    # process — supports macOS/Linux(pgrep), Windows(tasklist)
    try:
        if sys.platform == "win32":
            r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Obsidian.exe"],
                               capture_output=True, text=True, timeout=5)
            facts["process_running"] = "Obsidian.exe" in r.stdout
        else:
            r = subprocess.run(["pgrep", "-x", "Obsidian"], capture_output=True, timeout=3)
            facts["process_running"] = r.returncode == 0
    except Exception:
        pass

    # find config — supports multiple OS paths
    home = Path.home()
    candidates = [
        home / "Library/Application Support/obsidian/obsidian.json",  # macOS
        home / ".config/obsidian/obsidian.json",                       # Linux
        home / ".var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json",  # Flatpak
        home / "AppData/Roaming/obsidian/obsidian.json",               # Windows
        home / "AppData/Roaming/Obsidian/obsidian.json",               # Windows (uppercase)
    ]
    for p in candidates:
        if p.exists():
            facts["config_path"] = str(p)
            try:
                cfg = json.loads(p.read_text("utf-8"))
                project_path = facts["project_path"]
                for vid, info in (cfg.get("vaults") or {}).items():
                    vpath = info.get("path", "")
                    if not vpath:
                        continue
                    facts["registered_vaults"].append(vpath)
                    if _paths_match(vpath, project_path):
                        facts["vault_registered"] = True
                        facts["vault_open"] = bool(info.get("open", False))
                        facts["vault_last_ts"] = info.get("ts")
            except Exception as e:
                facts["config_error"] = str(e)
            break
    return facts


def check_status():
    claude_ok, claude_ver = False, ""
    exe = llm_provider.get_cli_executable(SETTINGS)
    try:
        r = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=5,
            env=_cli_subprocess_env(),
        )
        if r.returncode == 0:
            claude_ok = True
            claude_ver = r.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return {
        "claude": {"connected": claude_ok, "version": claude_ver, "binary": SETTINGS.get("claude_cli_binary", "claude")},
        "ai_provider": SETTINGS.get("ai_provider", "cli"),
        "cli_type": SETTINGS.get("cli_type", "claude"),
        "openai_configured": _openai_http_ready(),
        "obsidian": _read_obsidian_facts(),
        "llm_ui": _build_llm_ui(),
    }


def diagnose_claude():
    """Quick Claude CLI check — installation, auth, model response time"""
    env_cli = _cli_subprocess_env()
    path_preview = env_cli.get("PATH", "")[:280]
    extra_dirs = llm_provider._parse_cli_path_extra_dirs(SETTINGS)

    result = {
        "cli_installed": False,
        "version": "",
        "auth_ok": None,
        "model": SETTINGS.get("model", "default"),
        "model_args": llm_provider._model_args_for(None, SETTINGS),
        "quick_test_seconds": None,
        "quick_test_ok": False,
        "quick_test_output": "",
        "error": "",
        "config_timeout": CLAUDE_TIMEOUT,
        "advice": [],
        "resolved_executable": "",
        "effective_path_preview": path_preview,
        "cli_path_extra_count": len(extra_dirs),
        "cli_type": SETTINGS.get("cli_type", "claude"),
    }

    exe = llm_provider.get_cli_executable(SETTINGS)
    result["cli_binary"] = SETTINGS.get("claude_cli_binary", "claude")
    result["resolved_executable"] = exe

    # 1. version check
    try:
        r = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=10,
            env=env_cli,
        )
        if r.returncode == 0:
            result["cli_installed"] = True
            result["version"] = r.stdout.strip().split("\n")[0]
        else:
            result["error"] = r.stderr[:200] or "CLI --version failed"
    except FileNotFoundError:
        result["error"] = f"CLI not found ({result['cli_binary']}). npm install -g @anthropic-ai/claude-code or set claude_cli_binary."
        result["advice"].append("Install Claude CLI or set claude_cli_binary to an absolute path.")
        result["advice"].append(
            "Shell aliases (e.g. claude-qwen) are invisible to the server — use scripts/memex-claude-vendor.sh "
            "(install via scripts/install-memex-cli-wrappers.sh), an absolute path, or cli_path_extra."
        )
        cb = (result.get("cli_binary") or "").strip()
        if cb and os.path.sep not in cb:
            result["advice"].append(
                "If the name only resolves after sourcing dotfiles, run `command -v <name>` or `type <name>` "
                "in a shell without aliases and paste the resolved filesystem path into claude_cli_binary."
            )
        return result
    except subprocess.TimeoutExpired:
        result["error"] = "CLI --version timeout"
        return result

    if not result["cli_installed"]:
        return result

    # 2. measure response time with short prompt (verify auth + model access)
    try:
        t0 = time.time()
        exe = llm_provider.get_cli_executable(SETTINGS)
        r = subprocess.run(
            [exe, "-p"] + llm_provider._model_args_for(None, SETTINGS) + _parse_claude_extra_args() + ["--output-format", "text", "Reply with the single word OK."],
            capture_output=True, text=True, timeout=CLAUDE_QUICK_TIMEOUT,
            cwd=str(PROJECT_ROOT),
            env=_cli_subprocess_env(),
        )
        elapsed = time.time() - t0
        result["quick_test_seconds"] = round(elapsed, 1)
        result["quick_test_ok"] = r.returncode == 0
        result["quick_test_output"] = (r.stdout or r.stderr).strip()[:200]
        result["auth_ok"] = r.returncode == 0
        if r.returncode != 0:
            err = (r.stderr or "").lower()
            if "auth" in err or "login" in err or "unauthorized" in err:
                result["advice"].append("Claude CLI auth required. Run 'claude' in terminal to login.")
            else:
                result["advice"].append(f"Claude response failed: {(r.stderr or '')[:200]}")
        if elapsed > 15:
            result["advice"].append(f"Response is slow ({elapsed:.1f}s). Consider switching to Sonnet/Haiku.")
    except subprocess.TimeoutExpired:
        result["auth_ok"] = False
        result["error"] = f"Quick diagnostic also timed out ({CLAUDE_QUICK_TIMEOUT}s)"
        result["advice"].append("Claude CLI not responding. Run 'claude' in terminal to check auth/network.")

    # 3. recommendation for heavy models
    if SETTINGS.get("model") == "claude-opus-4-7":
        result["advice"].append("Opus 4.7 is the slowest. For large tasks like Ingest, Sonnet 4.6 recommended.")

    return result


# ─── LLM Wiki vault scaffolding ───
# Applied idempotently when registering an Obsidian vault. Never overrides existing
# user files or settings — only fills in missing pieces so the vault is recognised
# by Obsidian as a Memex/LLM-Wiki workspace out of the box.

LLM_WIKI_APP_JSON_DEFAULTS = {
    "attachmentFolderPath": "raw/assets",
    "newFileLocation": "folder",
    "newFileFolderPath": "wiki",
    "useMarkdownLinks": False,
    "strictLineBreaks": True,
    "readableLineLength": True,
}


def _llm_wiki_index_template(today: str) -> str:
    return (
        "---\n"
        "title: Index\n"
        "type: overview\n"
        f"created: {today}\n"
        f"last_updated: {today}\n"
        "tags:\n"
        "  - meta\n"
        "---\n"
        "\n"
        "# Wiki Index\n"
        "\n"
        "All wiki pages, organized by type. Updated on every ingest.\n"
        "\n"
        "## Overview\n"
        "- [[overview]] — wiki scope and current state\n"
        "\n"
        "## Sources\n_(none yet)_\n\n"
        "## Entities\n_(none yet)_\n\n"
        "## Concepts\n_(none yet)_\n\n"
        "## Techniques\n_(none yet)_\n\n"
        "## Analyses\n_(none yet)_\n"
    )


def _llm_wiki_log_template(today: str) -> str:
    return (
        "---\n"
        "title: Log\n"
        "type: overview\n"
        f"created: {today}\n"
        f"last_updated: {today}\n"
        "tags:\n"
        "  - meta\n"
        "---\n"
        "\n"
        "# Wiki Log\n"
        "\n"
        "Chronological record of all wiki activity.\n"
        "\n"
        f"## [{today}] init | Vault initialized\n"
        "Schema scaffolding created by the Memex dashboard.\n"
    )


def _llm_wiki_overview_template(today: str) -> str:
    return (
        "---\n"
        "title: Overview\n"
        "type: overview\n"
        f"created: {today}\n"
        f"last_updated: {today}\n"
        "sources: []\n"
        "tags:\n"
        "  - meta\n"
        "---\n"
        "\n"
        "# Wiki Overview\n"
        "\n"
        "## Current state\n"
        "\n"
        "- **Sources**: 0\n"
        "- **Entity pages**: 0\n"
        "- **Concept pages**: 0\n"
        "- **Technique pages**: 0\n"
        "- **Total wiki pages**: 0\n"
        "\n"
        "_The vault is empty. Add a source to get started._\n"
        "\n"
        "## Getting started\n"
        "\n"
        "1. Drop a document into `raw/` (or use the dashboard Ingest view).\n"
        "2. Claude creates a source summary, extracts entities and concepts, wires up cross-references.\n"
        "3. Watch pages appear in Obsidian and the dashboard in real time.\n"
    )


def _ensure_vault_scaffolding(vault_root: Path) -> dict:
    """Provision LLM Wiki schema + Obsidian app.json defaults inside the vault.

    Idempotent. Existing files and existing keys in app.json are preserved;
    only missing pieces are added. Returns a structured report of changes.
    """
    vault_root = Path(vault_root)
    created: list[str] = []
    updated: list[str] = []

    # 1. Directory skeleton (raw/ is immutable for content, but the dirs themselves are scaffolding)
    for sub in ("raw", "raw/assets", "wiki", "ingest-reports"):
        d = vault_root / sub
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(sub + "/")

    # 2. Wiki scaffolding files (only when missing)
    today = datetime.now().strftime("%Y-%m-%d")
    scaffolds = (
        ("wiki/index.md", _llm_wiki_index_template(today)),
        ("wiki/log.md", _llm_wiki_log_template(today)),
        ("wiki/overview.md", _llm_wiki_overview_template(today)),
    )
    for fname, content in scaffolds:
        p = vault_root / fname
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            created.append(fname)

    # 3. CLAUDE.md (only when missing; copy from templates/CLAUDE.md if shipped with the vault)
    claude_md = vault_root / "CLAUDE.md"
    if not claude_md.exists():
        tmpl = vault_root / "templates" / "CLAUDE.md"
        if tmpl.is_file():
            try:
                claude_md.write_text(tmpl.read_text("utf-8"), encoding="utf-8")
                created.append("CLAUDE.md")
            except Exception:
                pass

    # 4. .obsidian/app.json defaults — merge, never override existing keys
    obs_dir = vault_root / ".obsidian"
    obs_dir.mkdir(parents=True, exist_ok=True)
    app_json = obs_dir / "app.json"
    existing: dict = {}
    if app_json.exists():
        try:
            parsed = json.loads(app_json.read_text("utf-8"))
            if isinstance(parsed, dict):
                existing = parsed
        except Exception:
            existing = {}
    merged = dict(existing)
    keys_added: list[str] = []
    for k, v in LLM_WIKI_APP_JSON_DEFAULTS.items():
        if k not in merged:
            merged[k] = v
            keys_added.append(k)
    if not app_json.exists():
        app_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        created.append(".obsidian/app.json")
    elif keys_added:
        app_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        updated.append(".obsidian/app.json (added: " + ", ".join(keys_added) + ")")

    return {"created": created, "updated": updated}


def register_obsidian_vault():
    """Register current project folder as a vault in Obsidian config.

    Adds this project entry to the vaults dict in obsidian.json.
    If already registered, only sets the open flag to true.
    Obsidian may be running, so overwrite config carefully.
    Also idempotently enhances the vault with LLM Wiki schema and Obsidian defaults.
    """
    facts = _read_obsidian_facts()
    project_path = facts["project_path"]

    # determine config path (create if missing)
    home = Path.home()
    candidates = [
        home / "Library/Application Support/obsidian/obsidian.json",
        home / ".config/obsidian/obsidian.json",
        home / ".var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json",
        home / "AppData/Roaming/obsidian/obsidian.json",
        home / "AppData/Roaming/Obsidian/obsidian.json",
    ]
    config_path = facts.get("config_path")
    if config_path:
        config_path = Path(config_path)
    else:
        # first existing one. if none, create at OS default path
        config_path = next((p for p in candidates if p.parent.exists()), None)
        if not config_path:
            # try creating directory at macOS default
            default = candidates[0] if sys.platform == "darwin" else (
                candidates[3] if sys.platform == "win32" else candidates[1]
            )
            default.parent.mkdir(parents=True, exist_ok=True)
            config_path = default

    # read existing config
    cfg = {"vaults": {}}
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text("utf-8")) or {"vaults": {}}
        except Exception as e:
            return {"ok": False, "error": f"config parse error: {e}"}

    if "vaults" not in cfg or not isinstance(cfg["vaults"], dict):
        cfg["vaults"] = {}

    # check if already registered
    existing_id = None
    for vid, info in cfg["vaults"].items():
        if _paths_match(info.get("path", ""), project_path):
            existing_id = vid
            break

    import secrets
    if existing_id:
        # just toggle open flag on
        cfg["vaults"][existing_id]["open"] = True
        cfg["vaults"][existing_id]["ts"] = int(time.time() * 1000)
        action = "already_registered"
    else:
        # new registration
        vault_id = secrets.token_hex(8)  # 16-char hex
        cfg["vaults"][vault_id] = {
            "path": project_path,
            "ts": int(time.time() * 1000),
            "open": True,
        }
        action = "registered"

    try:
        config_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        return {"ok": False, "error": f"config write error: {e}"}

    # LLM Wiki auto-setup — vault scaffolding (idempotent, non-destructive)
    try:
        scaffolding = _ensure_vault_scaffolding(Path(project_path))
    except Exception as e:
        scaffolding = {"created": [], "updated": [], "error": f"{type(e).__name__}: {e}"}

    return {
        "ok": True,
        "action": action,
        "config_path": str(config_path),
        "project_path": project_path,
        "scaffolding": scaffolding,
        "restart_hint": "Restart (or launch) Obsidian to see the vault in the list.",
    }


# ─── operations ───

def _snapshot_wiki(wiki_dir=None):
    """Snapshot all wiki/ file contents as dict"""
    d = wiki_dir or WIKI_DIR
    snap = {}
    if not d.exists():
        return snap
    for md in d.rglob("*.md"):
        try:
            rel = str(md.relative_to(PROJECT_ROOT))
        except ValueError:
            rel = str(md)
        try:
            snap[rel] = md.read_text("utf-8")
        except Exception:
            pass
    return snap


def _diff_snapshots(before, after):
    """Compare before/after snapshots -> created_pages, modified_pages"""
    import difflib
    created, modified = [], []
    for path, content in after.items():
        if path not in before:
            # new file — preview first 10 lines
            lines = content.strip().split("\n")
            preview = "\n".join(lines[:12])
            created.append({"path": path, "preview_text": preview})
        elif before[path] != content:
            # modified file — unified diff
            diff = difflib.unified_diff(
                before[path].splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=f"a/{path}", tofile=f"b/{path}", lineterm="",
            )
            modified.append({"path": path, "diff_unified": "\n".join(diff)})
    return created, modified


def do_ingest(title, content, folder="", project_slug=None):
    proj = project_registry.get_project(project_slug)
    raw_dir = proj.raw_dir
    wiki_dir = proj.wiki_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    wiki_dir.mkdir(parents=True, exist_ok=True)

    slug = make_slug(title)
    raw_path = dedupe_raw_path(raw_dir / f"{slug}.md")
    raw_path.write_text(content, encoding="utf-8")
    slug = raw_path.stem

    snap_before = _snapshot_wiki(wiki_dir)

    ts = datetime.now().strftime("%Y-%m-%d-%H%M")
    report_rel = f"ingest-reports/{ts}-{slug}.md"
    (proj.ingest_reports).mkdir(parents=True, exist_ok=True)
    folder_inst = f" Place any new pages under wiki/{folder}/." if folder else ""
    idx_inst = get_index_instruction(wiki_dir)

    prompt = f"""{idx_inst}
IMPORTANT: Never modify or delete files under raw/ — raw/ is immutable. Only write under wiki/.
Ingest raw/{slug}.md — read this source and create/update wiki pages according to CLAUDE.md. Skip preamble and execute.{folder_inst}

When finished:
1. Summarize why you made these choices in 3–5 lines (start with REASONING:).
2. Create {report_rel} using this shape:
# Ingest Report: {title}
## Created
- wiki/path/file.md — WHY: one line
## Modified
- wiki/path/file.md — WHY: one line
## New cross-links
- [[a]] ↔ [[b]]"""

    ok, out, err = run_claude(prompt, project=proj)

    if ok:
        rebuild_index(wiki_dir)

    snap_after = _snapshot_wiki(wiki_dir)
    created, modified = _diff_snapshots(snap_before, snap_after)

    reasoning = ""
    if "REASONING:" in out:
        reasoning = out.split("REASONING:")[-1].strip()

    commit_hash = None
    if ok:
        c = git_mgr.commit_ingest(title, project=proj)
        commit_hash = c.get("hash")

    raw_rel = str(raw_path.relative_to(PROJECT_ROOT))
    return {
        "ok": ok,
        "project": proj.slug,
        "raw_file": raw_rel,
        "claude_output": out,
        "error": err,
        "commit_hash": commit_hash,
        "created_pages": created,
        "modified_pages": modified,
        "reasoning": reasoning,
        "report_path": str((proj.root / report_rel).relative_to(PROJECT_ROOT)),
    }


def _do_query_openai_rag(proj, question: str, lang_line: str):
    """OpenAI-compatible query: inject TF-IDF wiki snippets + index excerpt; English system prompt."""
    scored = _tfidf_wiki_search(proj, question, top_k=_QUERY_RAG_TOP_K)
    files_order: list[str] = []
    seen: set[str] = set()

    def _add(p: str) -> None:
        if p not in seen:
            seen.add(p)
            files_order.append(p)

    index_ex = ""
    index_p = proj.wiki_dir / "index.md"
    if index_p.is_file():
        raw = index_p.read_text("utf-8")
        _, body = parse_fm(raw)
        index_ex = (body or "")[:_QUERY_INDEX_EXCERPT_MAX]
        _add(_wiki_rel_for_project(proj, "index.md"))

    excerpt_parts = []
    for row in scored:
        rel = row["filename"]
        _add(_wiki_rel_for_project(proj, rel))
        excerpt_parts.append(f"### {rel} (score={row['score']})\n{row.get('snippet', '')}")

    excerpts_block = "\n\n".join(excerpt_parts) if excerpt_parts else "(No TF-IDF matches — rely on index excerpt only if present.)"

    system = (
        "You answer using ONLY the wiki index excerpt and retrieved wiki excerpts below. "
        "Do not invent facts beyond them. "
        "Cite relevant wiki pages using [[wikilink]] syntax.\n"
        + lang_line
    )
    user_content = (
        "## Wiki index excerpt (truncated)\n"
        + (index_ex if index_ex else "(wiki/index.md missing or empty)") + "\n\n"
        "## Retrieved wiki excerpts\n"
        + excerpts_block
        + "\n\n## Question\n"
        + question
    )

    ok, ans, err = openai_chat_completion(
        [{"role": "user", "content": user_content}],
        system=system,
        timeout=CLAUDE_TIMEOUT,
    )
    return ok, ans[:4000], err, files_order, {}


def do_query(question, project_slug=None, lang=None):
    proj = project_registry.get_project(project_slug)
    q = (question or "").strip()
    if not q:
        return {
            "ok": False,
            "project": proj.slug,
            "answer": "",
            "error": "Empty question",
            "files_read": [],
            "wiki_files": 0,
            "raw_files": 0,
            "wiki_ratio": 0.0,
            "token_usage": {},
        }

    lang_line = _query_response_language_line(q, lang)
    idx_inst = get_index_instruction(proj.wiki_dir)
    prompt = f"""Answer using this project's wiki. {idx_inst}
Find and read relevant wiki pages, then synthesize an answer.
Cite relevant wiki pages with [[wikilink]] syntax.

Language: {lang_line}

Question:
{q}"""

    if _openai_http_ready():
        ok, answer, err, files_read, token_usage = _do_query_openai_rag(proj, q, lang_line)
    else:
        ok, answer, err, files_read, token_usage = run_claude_tracked(prompt, project=proj)

    # paths may be project-relative or root-relative, cover both
    def _is_wiki(f):
        return f.startswith("wiki/") or "/wiki/" in f
    def _is_raw(f):
        return f.startswith("raw/") or "/raw/" in f

    wiki_files = [f for f in files_read if _is_wiki(f)]
    raw_files = [f for f in files_read if _is_raw(f)]
    total = len(files_read)
    wiki_ratio = len(wiki_files) / total if total > 0 else 0.0

    _log_query(q, files_read, round(wiki_ratio, 3), len(answer), query_log=proj.query_log)

    return {
        "ok": ok, "project": proj.slug, "answer": answer, "error": err,
        "files_read": files_read,
        "wiki_files": len(wiki_files),
        "raw_files": len(raw_files),
        "wiki_ratio": round(wiki_ratio, 3),
        "token_usage": token_usage,
    }


def do_query_save(title, content, project_slug=None):
    """Save Query answer as analysis page in wiki"""
    if not title or not title.strip():
        return {"ok": False, "error": "Title is required"}
    proj = project_registry.get_project(project_slug)
    wiki_dir = proj.wiki_dir
    wiki_dir.mkdir(parents=True, exist_ok=True)
    slug = make_slug(title)
    filepath = wiki_dir / f"{slug}.md"
    n = 2
    while filepath.exists():
        filepath = wiki_dir / f"{slug}-{n}.md"
        n += 1
    slug = filepath.stem
    today = datetime.now().strftime("%Y-%m-%d")
    md = f"""---
title: "{title}"
type: analysis
created: {today}
updated: {today}
sources: []
tags:
  - query-result
---

{content}
"""
    filepath.write_text(md, encoding="utf-8")
    prompt = (
        f"You just created wiki/{slug}.md. Add it to the Analyses section of wiki/index.md, append a query entry to wiki/log.md, "
        "and refresh statistics in wiki/overview.md."
    )
    run_claude(prompt, project=proj)
    git_mgr.commit_query_save(title, project=proj)
    return {"ok": True, "project": proj.slug, "filename": f"{slug}.md"}


def do_fix_citations(page_filename, project_slug=None):
    """Have Claude fix citations for a specific page"""
    proj = project_registry.get_project(project_slug)
    filepath = proj.wiki_dir / page_filename
    if not filepath.exists():
        return {"ok": False, "error": "Page not found"}
    prompt = f"""Read wiki/{page_filename}.
Find factual claims whose sentences lack inline citations [^src-*].
Add appropriate [^src-source-slug] citations where a matching source exists.

Rules:
- Place citations at sentence ends; definitions at bottom: [^src-slug]: [[source-slug]]
- Only use sources listed under Sources in wiki/index.md
- Do not add a citation when no matching source exists
- Keep existing citations

Report what you changed."""
    ok, out, err = run_claude(prompt, project=proj)
    if ok:
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"citation{git_mgr._slug_prefix(proj)}: fix {page_filename}")
    return {"ok": ok, "project": proj.slug, "output": out, "error": err}


REFLECT_DIR = PROJECT_ROOT / "reflect-reports"
REFLECT_DIR.mkdir(exist_ok=True)


def _collect_reflect_context(window, project=None):
    """Collect log entries + ingest-reports text based on window"""
    wiki_dir = project.wiki_dir if project else WIKI_DIR
    ingest_dir = project.ingest_reports if project else (PROJECT_ROOT / "ingest-reports")
    qlog_file = project.query_log if project else QUERY_LOG

    log_file = wiki_dir / "log.md"
    log_text = log_file.read_text("utf-8") if log_file.exists() else ""

    reports = []
    if ingest_dir.is_dir():
        for f in sorted(ingest_dir.glob("*.md"), reverse=True):
            reports.append({"name": f.name, "content": f.read_text("utf-8")[:2000]})

    low_ratio_queries = []
    if qlog_file.exists():
        for line in qlog_file.read_text("utf-8").strip().split("\n"):
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("wiki_ratio", 1.0) < 0.5:
                    low_ratio_queries.append(entry)
            except json.JSONDecodeError:
                pass

    # limit scope by window
    if window == "last-10-ingests":
        reports = reports[:10]
    elif window == "last-week":
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()[:10]
        reports = [r for r in reports if r["name"][:10] >= cutoff]

    return {
        "log_text": log_text[-3000:],  # last 3000 chars
        "reports": reports[:20],
        "low_ratio_queries": low_ratio_queries[:10],
    }


def do_reflect(window="last-10-ingests", project_slug=None):
    proj = project_registry.get_project(project_slug)
    reflect_dir = proj.reflect_reports
    reflect_dir.mkdir(parents=True, exist_ok=True)
    ctx = _collect_reflect_context(window, project=proj)

    reports_summary = "\n\n".join(
        f"### {r['name']}\n{r['content']}" for r in ctx["reports"]
    ) or "(no ingest reports)"

    low_ratio = "\n".join(
        f"- Q: {q['question'][:80]}  (wiki_ratio: {q['wiki_ratio']})"
        for q in ctx["low_ratio_queries"]
    ) or "(none)"

    today = datetime.now().strftime("%Y-%m-%d")
    report_path = f"reflect-reports/{today}.md"

    prompt = f"""Analyze the following data:

## Recent wiki log (excerpt)
{ctx['log_text'][-1500:]}

## Ingest reports
{reports_summary[:3000]}

## Low wiki_ratio queries
{low_ratio}

Produce:

1. **SUGGESTED_PAGES**: Entities/concepts that appear often but lack dedicated wiki pages — list each with one line why it matters.

2. **SUGGESTED_SCHEMA**: If repeated ingest judgment patterns emerge, propose rules to add to CLAUDE.md (diff-style OK).

3. **SUGGESTED_SOURCES**: From low-ratio queries, suggest search terms / sources that would strengthen those topics.

4. **CONTRADICTION_REVIEW**: If conflicting source behaviors appear often, propose contradiction-policy improvements.

Save the result to {report_path}. Use this outline:
# Reflect Report — {today}
## Suggested Pages
- page-name — why
## Suggested Schema Updates
(diff or prose)
## Suggested Sources
- "term" — why
## Contradiction Review
(findings or \"none\")

Include parse markers before sections: SUGGESTED_PAGES:, SUGGESTED_SCHEMA:, SUGGESTED_SOURCES:, CONTRADICTION_REVIEW:"""

    ok, out, err = run_claude(prompt, project=proj)
    if ok:
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"reflect{git_mgr._slug_prefix(proj)}: {today} ({window})")

    sections = {"suggested_pages": "", "suggested_schema": "", "suggested_sources": "", "contradiction_review": ""}
    report_file = proj.root / report_path
    report_text = report_file.read_text("utf-8") if report_file.exists() else out
    # handle both ## SUGGESTED_PAGES: and ## Suggested Pages formats
    section_patterns = [
        (r"##\s*(?:SUGGESTED_PAGES:?\s*)?Suggested Pages\b", "suggested_pages"),
        (r"##\s*(?:SUGGESTED_SCHEMA:?\s*)?Suggested Schema", "suggested_schema"),
        (r"##\s*(?:SUGGESTED_SOURCES:?\s*)?Suggested Sources", "suggested_sources"),
        (r"##\s*(?:CONTRADICTION_REVIEW:?\s*)?Contradiction Review", "contradiction_review"),
    ]
    import re as _re
    positions = []
    for pattern, key in section_patterns:
        m = _re.search(pattern, report_text, _re.IGNORECASE)
        if m:
            positions.append((m.end(), key))
    positions.sort(key=lambda x: x[0])
    for i, (start, key) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(report_text)
        # find next ## heading from end
        next_heading = _re.search(r"\n##\s", report_text[start:end])
        if next_heading:
            end = start + next_heading.start()
        sections[key] = report_text[start:end].strip().lstrip("#").strip()

    return {
        "ok": ok, "project": proj.slug, "error": err,
        "raw_output": out,
        "report_path": str((proj.root / report_path).relative_to(PROJECT_ROOT)),
        "sections": sections,
    }


def get_last_reflect_date(project_slug=None):
    """Date of last reflect report"""
    proj = project_registry.get_project(project_slug)
    d = proj.reflect_reports
    if not d.is_dir():
        return None
    files = sorted(d.glob("*.md"), reverse=True)
    if not files:
        return None
    return files[0].stem


def do_lint(project_slug=None):
    proj = project_registry.get_project(project_slug)
    today = datetime.now().strftime("%Y-%m-%d")
    idx_inst = get_index_instruction(proj.wiki_dir)
    prompt = f"""{idx_inst}
Read the "Lint checklist" section in CLAUDE.md and audit the entire wiki.

Run **all** checks:

### Structure
- Pages missing frontmatter or invalid type
- status: superseded without superseded_by
- status: disputed without ## Disputed
- superseded_by targets missing pages

### Citations
- Factual claims missing [^src-*]
- Per-page citation coverage
- [^src-*] referenced but undefined at bottom
- Referenced source-summary pages missing from wiki/
- source_count mismatches actual citations

### Links
- Orphan pages (no inbound [[wikilink]])
- Mentioned concepts without pages
- Related pages missing cross-links

### Freshness (today: {today})
- active pages with last_updated older than 30 days
- source_count 1 but broad generalizations
- confidence high but source_count < 2

Report format:
## Lint Report — {today}
### Critical (must fix)
- [ ] page.md — issue + suggested fix
### Warning (should fix)
- [ ] page.md — issue + suggested fix
### Info (nice to have)
- [ ] page.md — issue + suggested fix"""
    ok, out, err = run_claude(prompt, project=proj)
    return {"ok": ok, "project": proj.slug, "report": out, "error": err}


def do_lint_fix(project_slug=None):
    proj = project_registry.get_project(project_slug)
    prompt = """You just ran the CLAUDE.md Lint checklist. Fix every issue found now:

- Fix missing/invalid frontmatter
- Add [^src-*] to uncited claims when a source exists
- Align source_count with actual citations
- Bump last_updated to today where appropriate
- Add inbound [[wikilink]] to orphan pages; add missing cross-links
- Create stub pages for mentioned concepts without pages (min. one citation)
- Fix status / superseded_by inconsistencies
- Add ## Disputed where status demands it
- Refresh wiki/index.md, wiki/log.md, wiki/overview.md as needed

Summarize fixes by Critical / Warning / Info."""
    ok, out, err = run_claude(prompt, project=proj)
    if ok:
        git_mgr.commit_lint_fix(project=proj)
    return {"ok": ok, "project": proj.slug, "result": out, "error": err}


# ─── Writing Companion ───

# ─── Link Validation & Repair ───

def _scan_wiki_pages(wiki_dir):
    """Scan all wiki .md files, return (filename, content) pairs."""
    pages = {}
    if not wiki_dir or not wiki_dir.exists():
        return pages
    for f in sorted(wiki_dir.rglob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            # Extract title from frontmatter
            title_match = re.search(r'^title:\s*["\']?(.+?)["\']?$', content, re.M)
            title = title_match.group(1).strip() if title_match else f.stem.replace('-', ' ').title()
            rel = f.relative_to(wiki_dir)
            pages[rel.as_posix()] = {"content": content, "title": title, "path": str(f)}
        except Exception:
            pass
    return pages


def validate_links_api(project_slug=None):
    """Scan all wiki pages for broken links, orphan references, missing citations."""
    proj = project_registry.get_project(project_slug)
    wiki_dir = proj.wiki_dir
    issues = {
        "broken_links": [],      # [[unknown-page]] that don't match any file
        "self_broken": [],       # Pages that link to themselves (usually intentional but flag)
        "orphan_references": [],  # Page content mentions [[page]] without corresponding file
        "missing_citations": [],  # Factual claims without [^src-*]
        "summary": {},
    }
    pages = _scan_wiki_pages(wiki_dir)
    known_filenames = set(pages.keys())
    # Build slug → filename mapping
    slug_map = {}
    for fn in known_filenames:
        slug_map[fn.replace("/", "-").lower()] = fn
        slug_map[fn.replace("/", "_").lower()] = fn
        slug_map[fn.lower().replace(".md", "")] = fn

    import re as _re
    citation_re = _re.compile(r'\[\^src-[a-zA-Z0-9_-]+\]')

    total_claims = 0
    cited_claims = 0
    for fn, info in pages.items():
        content = info["content"]
        # Check for wikilinks
        matches = WIKILINK_RE.findall(content)
        for target in matches:
            target_lower = target.strip().lower()
            # Normalize: remove spaces, hyphens for matching
            target_slug = target_lower.replace(" ", "-")
            matched = False
            # Check direct filename match
            if (target_slug + ".md") in known_filenames:
                matched = True
            # Check slug_map
            elif target_slug in slug_map:
                matched = True
            # Use shared resolution with basename lookup + title hint
            if not matched:
                resolved = resolve_wikilink_target(
                    target_slug, known_filenames, title_hint=info.get("title", ""))
                if resolved:
                    matched = True
            if not matched:
                issues["broken_links"].append({
                    "from_page": fn,
                    "target": target.strip(),
                    "hint": f"No matching page found. Consider creating [[{target.strip()}]] or removing the link."
                })
        # Check for factual claims missing citations
        # Simple heuristic: sentences with common claim patterns
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("---") or line.startswith("-"):
                continue
            # Check if line has potential claim indicators
            claim_indicators = ["is", "are", "was", "the", "this", "that"]
            has_claim_hint = any(ind in line.lower() for ind in claim_indicators)
            if has_claim_hint and len(line) > 30 and "[^" not in line and not line.startswith(">") and not line.startswith("*"):
                total_claims += 1
                if citation_re.search(line):
                    cited_claims += 1

    issues["missing_citations"] = [] if cited_claims / max(total_claims, 1) > 0.8 else [f"{total_claims - cited_claims}/{total_claims} potentially uncited claims detected"]

    summary = {
        "total_pages": len(pages),
        "broken_link_count": len(issues["broken_links"]),
        "citation_health": f"{cited_claims}/{total_claims}" if total_claims else "N/A",
        "critical": len(issues["broken_links"]) > 5,
    }
    issues["summary"] = summary
    return {"ok": True, "project": proj.slug, "issues": issues, "summary": summary}


def fix_links_batch_api(project_slug, auto_create=False, alias_map=None):
    """Batch fix broken links across wiki pages."""
    proj = project_registry.get_project(project_slug)
    wiki_dir = proj.wiki_dir
    alias_map = alias_map or {}

    pages = _scan_wiki_pages(wiki_dir)
    changes = []
    new_pages_created = []

    for fn, info in pages.items():
        content = info["content"]
        changed = False
        # Apply alias replacements
        for old_target, new_target in alias_map.items():
            old_link = f"[[{old_target}]]"
            new_link = f"[[{new_target}]]"
            if old_link in content:
                content = content.replace(old_link, new_link)
                changes.append({"type": "alias_replace", "from": fn, "old": old_target, "new": new_target})
                changed = True
        # Auto-create missing pages
        if auto_create:
            targets = WIKILINK_RE.findall(content)
            for target in targets:
                target_clean = target.strip()
                target_slug = target_clean.replace(" ", "-")
                candidate = (wiki_dir / (target_slug + ".md")).resolve()
                if not candidate.exists() and candidate.parent == wiki_dir.resolve():
                    # Create stub page
                    stub_content = f"""---
title: "{target_clean}"
type: concept
tags: []
created: 2026-05-11
last_updated: 2026-05-11
source_count: 0
confidence: low
status: active
---

> [!warning] Stub page
> This page was auto-created by link repair. Add proper content.
"""
                    try:
                        candidate.write_text(stub_content, encoding="utf-8")
                        new_pages_created.append(target_clean)
                        changes.append({"type": "auto_created", "page": target_clean})
                    except Exception as e:
                        changes.append({"type": "error", "page": target_clean, "error": str(e)})
        if changed:
            # Write back
            pages[fn]["content"] = content

    result = {"ok": True, "project": proj.slug, "changes": changes, "new_pages": new_pages_created}
    # Git commit if there were changes
    if changes:
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"fix-links: batch repair ({len(changes)} changes)")
        result["committed"] = True
    return result


def do_write(topic, length="medium", style="blog", project_slug=None):
    if not topic or not topic.strip():
        return {"ok": False, "error": "Topic is required"}
    proj = project_registry.get_project(project_slug)
    word_map = {"short": "~300 words", "medium": "~700 words", "long": "~1500 words"}
    style_map = {
        "blog": "Blog tone (friendly, clear)",
        "paper": "Academic tone (precise, rigorous)",
        "explainer": "Explainer tone (accessible to newcomers)",
    }
    idx_inst = get_index_instruction(proj.wiki_dir)
    prompt = f"""{idx_inst}
Topic: {topic}
Length: {word_map.get(length, '~700 words')}
Style: {style_map.get(style, 'Blog tone')}

Use accumulated wiki pages as sources.

Requirements:
- Every factual claim needs [^src-source-slug] inline citations
- Reference related wiki pages with [[wikilink]]
- Footnote definitions at bottom: [^src-*]: [[source-*]]
- Introduction / body / conclusion
- Do not invent topics lacking supporting sources in the wiki

Output only the article (no meta commentary)."""
    ok, out, err = run_claude(prompt, project=proj)
    return {"ok": ok, "project": proj.slug, "draft": out, "error": err}


# ─── Page Comparison ───

def do_compare(page_a, page_b, save_as="", project_slug=None):
    if not page_a or not page_b:
        return {"ok": False, "error": "Both pages required"}
    proj = project_registry.get_project(project_slug)
    wiki_dir = proj.wiki_dir
    fa = wiki_dir / page_a
    fb = wiki_dir / page_b
    if not fa.exists() or not fb.exists():
        return {"ok": False, "error": "Page not found"}

    prompt = f"""Read wiki/{page_a} and wiki/{page_b}, then compare them.

Structure:
## Common ground
## Differences
## Relationship / implications

Include [^src-*] citations for claims; draw on sources from both pages."""

    ok, out, err = run_claude(prompt, project=proj)
    saved_file = None
    if ok and save_as:
        slug = make_slug(save_as)
        target = wiki_dir / f"{slug}.md"
        n = 2
        while target.exists():
            target = wiki_dir / f"{slug}-{n}.md"
            n += 1
        today = datetime.now().strftime("%Y-%m-%d")
        fm = f"""---
title: "{save_as}"
type: comparison
created: {today}
last_updated: {today}
sources: []
tags:
  - comparison
---

# {save_as}

{out}
"""
        target.write_text(fm, encoding="utf-8")
        saved_file = str(target.relative_to(wiki_dir))
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"compare{git_mgr._slug_prefix(proj)}: {save_as}")
    return {"ok": ok, "project": proj.slug, "analysis": out, "error": err, "saved": saved_file}


# ─── Spaced Review ───

def do_review_list(days=30, project_slug=None):
    proj = project_registry.get_project(project_slug)
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    stale = []
    wiki_dir = proj.wiki_dir
    if not wiki_dir.exists():
        return stale
    for md in wiki_dir.rglob("*.md"):
        text = md.read_text("utf-8")
        meta, _ = parse_fm(text)
        if meta.get("status", "active") != "active":
            continue
        if meta.get("type") in ("overview", "source-summary"):
            continue
        last_updated = meta.get("last_updated") or meta.get("updated")
        if not last_updated:
            continue
        try:
            lu = datetime.strptime(last_updated[:10], "%Y-%m-%d")
            if lu < cutoff:
                days_stale = (datetime.now() - lu).days
                stale.append({
                    "filename": str(md.relative_to(wiki_dir)),
                    "title": meta.get("title", md.stem),
                    "type": meta.get("type", ""),
                    "last_updated": last_updated[:10],
                    "days_stale": days_stale,
                })
        except ValueError:
            continue
    stale.sort(key=lambda x: -x["days_stale"])
    return stale


def do_review_refresh(filename, project_slug=None):
    proj = project_registry.get_project(project_slug)
    fp = proj.wiki_dir / filename
    if not fp.exists():
        return {"ok": False, "error": "Page not found"}
    prompt = f"""Read wiki/{filename} and:
1. Check Sources in wiki/index.md for material that could add new perspective to this page
2. If yes, merge that material with proper [^src-*] citations and refresh the page
3. Set last_updated to today
4. Summarize what you added

If nothing new applies, reply "No new updates; refreshed last_updated only." and only bump last_updated."""
    ok, out, err = run_claude(prompt, project=proj)
    if ok:
        git_mgr._stage_all(project=proj)
        git_mgr._run("commit", "-m", f"review{git_mgr._slug_prefix(proj)}: refresh {filename}")
    return {"ok": ok, "project": proj.slug, "result": out, "error": err}


# ─── Marp Slide Export ───

def do_slides(page_filename, project_slug=None):
    proj = project_registry.get_project(project_slug)
    fp = proj.wiki_dir / page_filename
    if not fp.exists():
        return {"ok": False, "error": "Page not found"}
    content = fp.read_text("utf-8")
    meta, body = parse_fm(content)
    title = meta.get("title", page_filename.replace(".md", ""))

    prompt = f"""Convert wiki/{page_filename} into a Marp slide deck.

Requirements:
- Include Marp frontmatter (marp: true, theme: default, paginate: true, class: invert)
- Title slide with subtitle
- One main idea per slide
- 3–5 bullets per slide when applicable
- Preserve syntax highlighting in code fences
- Separate slides with ---
- Keep citations ([^src-*]) in slide footers when present

Output only raw Marp markdown (no explanations)."""
    ok, out, err = run_claude(prompt, project=proj)
    return {"ok": ok, "project": proj.slug, "marp": out, "error": err, "title": title}


# ─── Smart Search (TF-IDF) ───

def _tokenize(text):
    return re.findall(r"[\w]+", text.lower())


def _tfidf_wiki_search(proj, query, top_k=10):
    """TF-IDF over wiki/*.md (stdlib). Returns list of {filename, score, snippet}."""
    import math

    wiki_dir = proj.wiki_dir
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    docs = {}
    if not wiki_dir.exists():
        return []
    for md in wiki_dir.rglob("*.md"):
        rel = str(md.relative_to(wiki_dir))
        text = md.read_text("utf-8")
        _, body = parse_fm(text)
        tokens = _tokenize(body)
        if tokens:
            docs[rel] = {"tokens": tokens, "body": body}

    if not docs:
        return []

    df = {}
    for doc in docs.values():
        for tok in set(doc["tokens"]):
            df[tok] = df.get(tok, 0) + 1
    N = len(docs)

    scored = []
    for rel, doc in docs.items():
        tf = {}
        for tok in doc["tokens"]:
            tf[tok] = tf.get(tok, 0) + 1
        score = 0.0
        for qt in q_tokens:
            if qt in tf and qt in df:
                idf = math.log((N + 1) / (df[qt] + 1)) + 1
                score += (tf[qt] / len(doc["tokens"])) * idf
        if score > 0:
            snippet = ""
            body_low = doc["body"].lower()
            for qt in q_tokens:
                idx = body_low.find(qt)
                if idx >= 0:
                    start = max(0, idx - 60)
                    end = min(len(doc["body"]), idx + 120)
                    snippet = (
                        ("..." if start > 0 else "")
                        + doc["body"][start:end]
                        + ("..." if end < len(doc["body"]) else "")
                    )
                    break
            scored.append({"filename": rel, "score": round(score, 4), "snippet": snippet})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]


def do_search(query, top_k=10, project_slug=None):
    """TF-IDF wiki search (stdlib only)."""
    proj = project_registry.get_project(project_slug)
    scored = _tfidf_wiki_search(proj, query, top_k)
    return {"ok": True, "project": proj.slug, "results": scored}


# ─── Related Sources Suggestion ───

def do_suggest_sources(project_slug=None):
    proj = project_registry.get_project(project_slug)
    prompt = """Read wiki/index.md and recent wiki/log.md to judge coverage gaps.

Propose 5–10 concrete search terms or paper titles worth ingesting next:

1. Entities/concepts mentioned often but lacking dedicated pages
2. Topics with thin source coverage
3. Natural extensions of recent ingests (e.g., after Transformer → BERT, GPT-3, …)

Output one suggestion per line, parse-friendly:
```
SUGGESTION: "term or title" | WHY: reason | EXPECTED_PAGES: wiki pages this would strengthen
```
Suggestions only — no preamble."""
    ok, out, err = run_claude(prompt, project=proj)
    suggestions = []
    if ok:
        for line in out.split("\n"):
            if line.strip().startswith("SUGGESTION:"):
                parts = line.split("|")
                if len(parts) >= 2:
                    sugg = parts[0].replace("SUGGESTION:", "").strip().strip('"')
                    why = parts[1].replace("WHY:", "").strip() if len(parts) > 1 else ""
                    expected = parts[2].replace("EXPECTED_PAGES:", "").strip() if len(parts) > 2 else ""
                    suggestions.append({"suggestion": sugg, "why": why, "expected_pages": expected})
    return {"ok": ok, "project": proj.slug, "suggestions": suggestions, "raw": out, "error": err}


# --- Dashboard Assistant Chatbot ---
# Answers questions about the dashboard itself. Not wiki content — features/usage.

ASSISTANT_CONTEXT_EN = """You are "Claude", a friendly AI assistant for **Memex** — an LLM-powered personal knowledge base that continuously builds, maintains, and updates enterprise-grade wikis.

ABOUT MEMEX (this IS a special wiki platform you help manage):
- Architecture: Obsidian vault with raw/ (immutable sources, 4-layer protection), wiki/ (LLM-maintained knowledge pages with YAML frontmatter), projects/ (multi-project support).
- Schema: CLAUDE.md defines everything — frontmatter rules (type/status/confidence/source_count), inline citations [^src-*], wikilinks [[page-name]], contradiction resolution policy.
- Wiki lifecycle: Ingest (add raw source → Claude creates/updates wiki pages) → Query (ask about wiki content) → Write (draft pages) → Compare (side-by-side) → Lint (citation health check) → Reflect (pattern analysis) → Review (quality assessment).
- Git integration: every Ingest = automatic git commit. All changes revertible via History.
- Graph view: wikilinks form a knowledge graph. BFS community detection finds topic clusters. Isolated pages have no links — adding wikilinks improves KB health.
- MCP server exposes wiki operations programmatically (list pages, search, create/update pages, validate/fix links).
- Optional Graphify integration: Leiden/Louvain clustering, god-nodes filtering, surprising connections, community naming, interactive HTML export.
- Dashboard languages: English, 中文.
- Claude CLI must be installed and configured. Model selector: Opus/Sonnet/Haiku/Default.

DASHBOARD FEATURES:
- Toolbar has 5 categories:
  * Work: Ingest, Query, Write, Compare
  * Analyze: Lint, Reflect, Review, Provenance
  * Browse: Search, Graph, History
  * Create: + Folder, + Page
  * More: CLAUDE.md, Guide
- Sidebar: drag right edge to resize (220-500px). Cmd/Ctrl+B to toggle. Click folder NAME (not arrow) for continuous folder view.
- Header: language toggle (English / 中文), model selector (Opus/Sonnet/Haiku/Default), Wiki Ratio gauge, index strategy badge.
- Status bar (bottom-left): raw facts only. Claude CLI (on/off) + Obsidian (process + vault_open).
- Per-page: Edit, Slides (Marp export), Delete.
- Every ingest = git commit. Revertable via History.
- Inline citations [^src-*] rendered as numbered badges.
- Adaptive indexing: flat (<50) → hierarchical (50-200) → indexed (>200).

WIKI ACTIONS FROM CHAT: Users can type natural language commands like "run lint", "run the wiki loop", "check for broken links", "run reflect", "any new sources?" — these are detected and executed directly without Claude CLI invocation. For conversational questions, answer normally.

If asked about dashboard usage, give direct instructions. Keep answers SHORT (2-4 sentences). For deep wiki content analysis, suggest the Query feature.
"""


ASSISTANT_CONTEXT_ZH = """你是 "Claude"，**Memex**（LLM 驱动的个人知识库平台）的友好助手。Memex 持续构建、维护、更新企业级知识库。

关于 Memex（这是你需要帮助管理的系统本身）：
- 架构：Obsidian vault — raw/（不可变源文件，四层保护），wiki/（LLM 维护的知识页面），projects/（多项目支持）。
- 模式：CLAUDE.md 定义一切 — frontmatter 规则（type/status/confidence/source_count）、内联引用 [^src-*]、wikilink [[page-name]]、矛盾解决策略。
- Wiki 循环：Ingest（添加 raw 源 → Claude 创建/更新 wiki 页面）→ Query（查询 wiki 内容）→ Write（起草页面）→ Compare（对比）→ Lint（引用健康度检查）→ Reflect（模式分析）→ Review（质量评估）。
- Git 集成：每次 Ingest = 自动 git commit。所有变更可通过 History 恢复。
- 图谱视图：wikilink 形成知识图谱。BFS 社区检测识别主题簇。孤立页面无链接 — 添加 wikilink 可提升知识库健康度。
- MCP Server 程序化暴露 wiki 操作（列出页面、搜索、创建/更新、链接验证/修复）。
- 可选 Graphify 集成：Leiden/Louvain 聚类、god-nodes 过滤、意外连接发现、社区命名、交互式 HTML 导出。
- 控制台语言：English, 中文。
- 需安装配置 Claude CLI。模型选择：Opus/Sonnet/Haiku/Default。

控制台要点：
- 工具栏 5 类：工作（收录、问答、写作、比较）；分析（检查、反思、复习、引证）；浏览（搜索、图谱、历史）；创建（+文件夹、+页面）；更多（CLAUDE.md、指南）。
- 侧栏：拖右缘 220–500px。Cmd/Ctrl+B 收起。在树中点击文件夹**名称**（非小箭头）进入连续阅读。
- 标题栏：语言切换（English / 中文）、模型、Wiki Ratio、索引导航。
- 左下状态栏：只显示事实。Claude CLI 与 Obsidian（进程 + vault 是否打开）。
- 单页：编辑、Slides（Marp 导出）、删除。
- 每次收录 = git 提交，可在历史中恢复。
- 内联引用 [^src-*] 渲染为数字角标。
- 索引策略：flat (<50) → hierarchical (50-200) → indexed (>200)。

聊天 Wiki 命令：用户可以说 "run lint"、"wiki loop"、"check broken links"、"reflect" 等自然语言直接执行 wiki 操作。普通问答正常回答。

回答要**短（2–4 句）**。涉及深层 wiki 内容分析时建议用 Query 功能。
"""

# Context for project-specific knowledge base Q&A
ASSISTANT_CONTEXT_KB_QA = """You are "Claude", a friendly AI assistant for the **{project_name}** knowledge base.
Your job is to answer questions about THIS KNOWLEDGE BASE using the wiki context provided below.

Rules:
- If the answer can be found in the wiki context, use it directly with inline citations [[page-name]].
- If the context doesn't contain enough information, say so honestly rather than making things up.
- Keep answers SHORT (2-4 sentences) and cite sources when possible.
- If asked about dashboard features (not wiki content), redirect to Query feature.

=== WIKI CONTEXT START ===
{WIKI_CONTEXT}
=== WIKI CONTEXT END ===
"""


# ─── Chat Action Dispatch (regex → LLM fallback → CLI execution) ─────────────

import re as _re
import json as _json

_CHAT_ACTION_DESCRIPTIONS = {
    "lint": "Check wiki citation health, formatting, orphaned pages, and overall quality. Triggered by 'lint', 'check health/quality', 'wiki 检查', etc.",
    "lint_fix": "Auto-repair wiki lint issues. Triggered by 'fix lint', 'auto repair wiki', '修复 lint', etc.",
    "reflect": "Analyze wiki patterns from recent ingests. Triggered by 'reflect', 'analyze patterns', '反思分析', etc.",
    "validate_links": "Check for broken/dead wiki links. Triggered by 'broken links', 'validate links', '检查链接', etc.",
    "detect_sources": "Scan for raw sources not yet cited. Triggered by 'new sources', 'uncited files', '未收录源文件', etc.",
    "loop": "Full wiki maintenance cycle (lint→fix→reflect). Triggered by 'wiki loop', 'maintenance', '执行循环', '循环', etc.",
    "schedule_help": "Set up periodic wiki tasks via cron. Triggered by 'schedule lint', 'daily wiki', '定时任务', etc.",
}

_CHAT_ACTION_EXAMPLES = [
    "run the wiki maintenance loop",
    "lint 一下",
    "帮我检查一下 wiki 的健康状况",
    "fix all formatting issues automatically",
    "看看有没有还没被引用的源文件",
    "run a reflect analysis on the last 5 ingests",
    "schedule a weekly link validation",
    
    "每天自动检查一次 wiki",
    "把所有缺失引用的源文件列出来",
]


def _llm_classify_chat_intent(question: str, timeout: int = 15) -> dict:
    """Use CLI-based LLM to classify user intent into a wiki action or conversational.

    Returns {action, params} where action is one of _CHAT_ACTION_DESCRIPTIONS
    keys or "conversational". Falls back to regex on failure.
    """
    fast = _regex_detect_chat_command(question)
    if fast.get("action", "conversational") != "conversational":
        return fast  # Regex already found it — no need for LLM

    # LLM classification for ambiguous cases (via CLI)
    action_list = "\n".join(f"- **{k}**: {v}" for k, v in _CHAT_ACTION_DESCRIPTIONS.items())
    examples = "\n".join(f"  • {e}" for e in _CHAT_ACTION_EXAMPLES)

    prompt = f"""You are an intent classifier for a Memex wiki chat.

AVAILABLE ACTIONS:
{action_list}

EXAMPLES:
{examples}

RULES:
- If the user is requesting a wiki operation, classify it as the matching action.
- If asking a general question, classify as "conversational".
- If ambiguous, lean toward "conversational".
- User may write in English, Korean, or Chinese.
- "schedule" means SET UP a recurring task, not run now.

Return ONLY JSON: {{"action": "<action_name>", "params": {{}}}}
For "loop": params may include {{"steps": ["lint","lint_fix","reflect"], "include_ingest": false}}
For "reflect": params may include {{"window": "last-N-ingests"}}

User message: "{question}"
JSON:"""

    ok, text, err = run_claude(prompt, timeout=timeout, cwd=str(PROJECT_ROOT), project=None, force_cli=False)
    if ok and text:
        try:
            ts = text.strip()
            if ts.startswith("{"):
                parsed = _json.loads(ts[:ts.rfind("}")+1])
                act = parsed.get("action", "").lower()
                if act in _CHAT_ACTION_DESCRIPTIONS:
                    return {"action": act, "params": parsed.get("params", {})}
                for k in _CHAT_ACTION_DESCRIPTIONS:
                    if k in act or act in k:
                        return {"action": k, "params": parsed.get("params", {})}
        except (_json.JSONDecodeError, KeyError, ValueError):
            pass

    return fast  # LLM failed — fall back to regex


def _regex_detect_chat_command(question: str) -> dict:
    """Regex-based intent detection for wiki action commands.

    Returns {action, params} or {"action": "conversational", "params": {}}.
    """
    q = question.lower().strip()

    # ── Schedule commands (checked early — "schedule a lint" ≠ run lint now) ──
    if _re.search(r"(schedule|cron|timer|periodic|every\s+\w+)", q):
        action_words = _re.search(r"(lint|loop|reflect|valid|check|ingest|maintenance|clean)", q)
        if action_words:
            return {"action": "schedule_help", "params": {"detected_action": action_words.group(1)}}

    # ── Loop ──
    loop_pats = [
        r"(run|start|execute|begin)\s*(the)?\s*(wiki\s*)?(loop|maintenance(\s*loop)?|maintenance\s*cycle)",
        r"(run|start|execute)\s*(a\s*)?(wiki\s*)?(maint(en|ain)|clean)(\s*(up|loop|cycle))?",
        r"do\s*(a\s*)?(wiki\s*)?(loop|maintenance|clean\s*up)",
        r"(wiki\s*)?(loop|maintenance(\s*loop|cycle)?)\b",
    ]
    for pat in loop_pats:
        if _re.search(pat, q):
            steps = []
            if _re.search(r"(lint|fix|repair)", q):
                if _re.search(r"(fix|repair)", q):
                    steps.extend(["lint", "lint_fix"])
                else:
                    steps.append("lint")
            if _re.search(r"(reflect|analy[sz]|pattern)", q):
                steps.append("reflect")
            if _re.search(r"(valid|link|broken|orphan)", q):
                steps.append("validate_links")
            if _re.search(r"(ingest|import|new.source|add.source)", q):
                return {"action": "loop", "params": {"steps": steps or ["lint", "lint_fix", "reflect"], "include_ingest": True}}
            return {"action": "loop", "params": {"steps": steps or ["lint", "lint_fix", "reflect"]}}

    # ── Lint Fix (before lint — more specific) ──
    if _re.search(r"(lint|check).*fix|fix.*(lint|citation|link|format|wiki)|auto.*(fix|repair).*wiki", q):
        return {"action": "lint_fix", "params": {}}

    # ── Validate Links ──
    if _re.search(r"valid.*link|check.*(broken|dead|orphan)|link.*(valid|check|broken)|find.*(broken|orphan|dead).*link", q):
        return {"action": "validate_links", "params": {}}

    # ── Lint ──
    if _re.search(r"(run\s*)?lint|check.*(wiki|citation|health)|wiki.*(lint|health|quality)|health.*(check|wiki)", q):
        return {"action": "lint", "params": {}}

    # ── Reflect ──
    if _re.search(r"(run\s*)?reflect|analy[sz].*pattern|pattern.*analy[sz]|reflect.*wiki|wiki.*reflect", q):
        window = "last-10-ingests"
        m = _re.search(r"last.?(\d+)", q)
        if m:
            window = f"last-{m.group(1)}-ingests"
        return {"action": "reflect", "params": {"window": window}}

    # ── Detect New Sources ──
    if _re.search(r"(new|uncited|missing).{0,10}(source|file|raw)|check.*new.*source|any.*source.*ingest|source.*ingest", q):
        return {"action": "detect_sources", "params": {}}

    # ── Chinese/Korean fallback patterns (regex safety net for common phrases) ──
    # LLM classifier handles full semantics; these cover timeout/failure cases.
    zh_ko_map = {
        r"清理循环|循环运行|跑一次循环|维护循环|完整.*维护|运行.*维护|完整维护|维护执行|循环": "loop",
        r"检查.*健康|体检.*wiki|质量检查|运行.*lint|检查.*引用": "lint",
        r"修复.*问题|自动修复|fix.*问题": "lint_fix",
        r"模式分析|反思分析|运行.*反思|成察": "reflect",
        r"链接.*检查|检查.*链接|死链|断链|无效链接": "validate_links",
        r"未收录|未引用|新.*源|源文件.*没|新的.*source|引用.*没|引用.*源|列出.*源|列出.*引用|有没有.*源": "detect_sources",
        r"定时|每天|每周|周期|周期性|计划": "schedule_help",
        r"lint.*running|lint.*check|check.*lint": "lint",
        r"fix.*auto|auto.*fix": "lint_fix",
        r"link.*broken|broken.*link|validate.*link": "validate_links",
    }
    for pat, act in zh_ko_map.items():
        if _re.search(pat, q):
            return {"action": act, "params": {}}

    return {"action": "conversational", "params": {}}


def _execute_chat_action(action: str, params: dict, project: str | None) -> dict:
    """Execute a wiki operation detected from chat. Returns structured result."""
    import sys
    dashboard_dir = Path(__file__).resolve().parent
    if str(dashboard_dir) not in sys.path:
        sys.path.insert(0, str(dashboard_dir))

    try:
        import wiki_ops
    except ImportError:
        return {"ok": False, "error": "wiki_ops module not available", "action": action}

    proj_slug = project or ""

    if action == "lint":
        result = wiki_ops.op_lint(project=proj_slug)
        if result.get("ok"):
            summary = _summarize_lint_result(result)
            return {
                "ok": True, "action": "lint",
                "title": "Lint Complete",
                "summary": summary,
                "detail": result.get("output", "")[:1500],
                "suggestions": ["Run Lint Fix to auto-repair issues", "Run Reflect for pattern analysis"],
            }
        return {"ok": False, "action": "lint", "error": result.get("error", "Unknown error")}

    elif action == "lint_fix":
        result = wiki_ops.op_lint_fix(project=proj_slug)
        if result.get("ok"):
            return {
                "ok": True, "action": "lint_fix",
                "title": "Auto-Fix Applied",
                "summary": result.get("output", "")[:500],
                "suggestions": ["Run Lint to verify fixes", "Run Reflect next"],
            }
        return {"ok": False, "action": "lint_fix", "error": result.get("error", "Unknown error")}

    elif action == "reflect":
        result = wiki_ops.op_reflect(window=params.get("window", "last-10-ingests"), project=proj_slug)
        if result.get("ok"):
            return {
                "ok": True, "action": "reflect",
                "title": "Reflection Complete",
                "summary": result.get("output", "")[:1000],
                "suggestions": ["Run Lint to check citation health", "View updated wiki pages"],
            }
        return {"ok": False, "action": "reflect", "error": result.get("error", "Unknown error")}

    elif action == "validate_links":
        result = wiki_ops.op_validate_links(project=proj_slug)
        if result.get("ok"):
            total = result.get("total_links", 0)
            broken = result.get("broken_links", [])
            return {
                "ok": True, "action": "validate_links",
                "title": "Link Validation",
                "summary": f"Checked {total} links. Found {len(broken)} broken link(s).",
                "broken_links": broken[:10],
                "suggestions": ["Fix broken links manually", "Run Lint for more details"],
            }
        return {"ok": False, "action": "validate_links", "error": result.get("error", "Unknown error")}

    elif action == "detect_sources":
        new_sources = wiki_ops.detect_new_sources(project=proj_slug)
        uncited = [s for s in new_sources if not s.get("cited")]
        if uncited:
            source_list = "\n".join(f"  • `{s['path']}`" for s in uncited[:10])
            return {
                "ok": True, "action": "detect_sources",
                "title": f"Found {len(uncited)} Uncited Source(s)",
                "summary": f"{len(uncited)} source file(s) in raw/ have not been ingested into the wiki yet.",
                "sources": source_list,
                "suggestions": ["Run Loop with Ingest to process them", "View sources in the Ingest tab"],
            }
        return {
            "ok": True, "action": "detect_sources",
            "title": "All Sources Ingested",
            "summary": "All raw source files have been cited in wiki pages. No new sources to ingest.",
        }

    elif action == "loop":
        steps = params.get("steps", ["lint", "lint_fix", "reflect"])
        include_ingest = params.get("include_ingest", False)
        result = wiki_ops.run_loop(
            project=proj_slug, steps=steps, include_ingest=include_ingest,
            continue_on_error=True,
        )
        if result.get("ok"):
            lines = []
            for sr in result.get("steps_results", []):
                status_icon = "✓" if sr.get("status") == "ok" else "✗" if sr.get("status") == "failed" else "–"
                lines.append(f"  {status_icon} {sr['name']}: {sr['status']} ({sr.get('duration_sec', 0):.0f}s)")
            return {
                "ok": True, "action": "loop",
                "title": f"Wiki Loop Complete ({result.get('total_duration_sec', 0):.0f}s)",
                "summary": "Steps executed:\n" + "\n".join(lines),
                "suggestions": ["Run again to maintain wiki health", "Check graph for new connections"],
            }
        return {"ok": False, "action": "loop", "error": result.get("error", "Unknown error")}

    elif action == "schedule_help":
        detected = params.get("detected_action", "wiki operation")
        return {
            "ok": True, "action": "schedule_help",
            "title": "Scheduling",
            "summary": f"To schedule a periodic {detected}, use the Schedules tab in the dashboard.\n\n"
                       f"Examples:\n"
                       f"  • Daily lint at 3am: `0 3 * * *`\n"
                       f"  • Every 6 hours: `0 */6 * * *`\n"
                       f"  • Weekly on Monday: `0 9 * * 1`\n\n"
                       f"Or I can guide you through creating one via the dashboard API.",
            "suggestions": ["Open Schedules tab", "Run the operation now instead"],
        }

    return {"ok": False, "action": action, "error": f"Unknown action: {action}"}


def _summarize_lint_result(result: dict) -> str:
    """Create a short summary from a lint result."""
    output = result.get("output", "")
    critical = _re.findall(r"- \[ \] (.*)", output)
    if not critical:
        return "No critical issues found. Wiki is healthy!"
    crit = [c for c in critical if "critical" in c.lower() or "Critical" in output.split(c)[0][-50:]]
    if crit:
        return f"Found {len(critical)} issue(s). Top: " + crit[0][:80]
    return f"Found {len(critical)} issue(s) to review."


def do_assistant_chat(question, lang="en", history=None, project=None):
    """Dashboard helper chatbot — call Claude CLI with a short prompt.
    If project parameter is present, includes wiki context for that project.
    Wiki action commands are detected first and executed directly."""
    import os
    if not question or not question.strip():
        return {"ok": False, "error": "Empty question"}
    history = history or []

    # Step 1: Intent classification (regex → LLM fallback → CLI execution)
    cmd = _llm_classify_chat_intent(question)
    action_name = cmd.get("action", "")
    if action_name and action_name != "conversational":
        return _execute_chat_action(action_name, cmd.get("params", {}), project)

    # Build wiki context if project specified
    wiki_context = ""
    if project:
        try:
            proj = project_registry.get_project(project)
            wiki_dir = getattr(proj, "wiki_dir", None)
            if wiki_dir and wiki_dir.exists():
                parts = []
                idx = wiki_dir / "index.md"
                if idx.exists():
                    try:
                        parts.append("---INDEX---\n" + idx.read_text(encoding="utf-8")[:3000])
                    except Exception:
                        pass
                # Top 20 most recently modified pages as quick context
                md_files = []
                for root, dirs, files in os.walk(str(wiki_dir)):
                    for f in files:
                        if f.endswith(".md"):
                            fp = os.path.join(root, f)
                            try:
                                mt = os.path.getmtime(fp)
                                md_files.append((fp, mt))
                            except OSError:
                                pass
                md_files.sort(key=lambda x: x[1], reverse=True)
                for fp, _ in md_files[:20]:
                    rel = os.path.relpath(fp, str(wiki_dir))
                    try:
                        content = open(fp, encoding="utf-8").read(500)
                        parts.append(f"---PAGE:{rel}---\n{content}")
                    except Exception:
                        pass
                wiki_context = "\n\n".join(parts)
        except Exception as exc:
            wiki_context = f"(Error loading wiki context: {exc})"

    # Select context based on whether project is specified
    if wiki_context:
        ctx = ASSISTANT_CONTEXT_KB_QA.format(
            project_name=project,
            WIKI_CONTEXT=wiki_context[:5000]
        )
    elif lang == "ko":
        ctx = ASSISTANT_CONTEXT_KO
    elif lang == "zh":
        ctx = ASSISTANT_CONTEXT_ZH
    else:
        ctx = ASSISTANT_CONTEXT_EN

    hist_text = ""
    for h in history[-4:]:
        role = "User" if h.get("role") == "user" else "Assistant"
        hist_text += f"\n{role}: {h.get('content','')}"
    if lang == "zh":
        tail = "助手（请用中文，简短 2–4 句）："
    else:
        tail = "Assistant (short, 2-4 sentences):"
    prompt = f"{ctx}\n\nConversation so far:{hist_text}\n\nUser: {question}\n\n{tail}"
    # assistant does not read wiki/raw files, only generates answers — HTTP or CLI
    ok, ans, err = run_claude(prompt, timeout=60, cwd=str(PROJECT_ROOT), project=None, force_cli=False)
    return {"ok": ok, "answer": (ans or "").strip()[:2000], "error": err[:300] if not ok else ""}


# ─── Projects API (MP-03) ───
# Maintain legacy mode while introducing projects.json-based multi-project foundation.
# Existing do_*() still uses current WIKI_DIR/RAW_DIR constants (scoping in MP-07).

def list_projects_api():
    projects = [p.to_dict() for p in project_registry.list_projects()]
    active_slug = project_registry.get_active_slug()
    # also expose legacy info
    legacy = None
    if project_registry.LEGACY_WIKI.exists():
        try:
            legacy_proj = project_registry.get_project()
            if legacy_proj.is_legacy:
                legacy = legacy_proj.to_dict()
        except Exception:
            legacy = None
    return {
        "ok": True,
        "active": active_slug,
        "projects": projects,
        "legacy": legacy,
        "has_projects": project_registry.has_projects(),
    }


def get_active_project_api():
    try:
        p = project_registry.get_project()
        return {"ok": True, "project": p.to_dict()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_project_api(slug_hint, title, description, model, template):
    try:
        p = project_registry.create_project(
            slug_hint=slug_hint or title,
            title=title,
            description=description,
            model=model,
            template=template,
        )
        return {"ok": True, "project": p.to_dict()}
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def switch_project_api(slug):
    try:
        p = project_registry.switch_project(slug)
        return {"ok": True, "project": p.to_dict()}
    except KeyError as e:
        return {"ok": False, "error": str(e)}


def update_project_api(slug, **fields):
    # discard None values
    cleaned = {k: v for k, v in fields.items() if v is not None}
    try:
        p = project_registry.update_project_settings(slug, **cleaned)
        return {"ok": True, "project": p.to_dict()}
    except KeyError as e:
        return {"ok": False, "error": str(e)}
    except TypeError as e:
        return {"ok": False, "error": str(e)}


def delete_project_api(slug, confirm):
    return project_registry.delete_project(slug, confirm=confirm)


# ─── CRUD ───

def create_folder(name, parent="", project_slug=None):
    proj = project_registry.get_project(project_slug)
    proj.wiki_dir.mkdir(parents=True, exist_ok=True)
    base = proj.wiki_dir / parent if parent else proj.wiki_dir
    folder = base / name
    folder.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "project": proj.slug, "path": str(folder.relative_to(proj.wiki_dir))}


def create_page(title, page_type, folder="", content="", project_slug=None):
    if not title or not title.strip():
        return {"ok": False, "error": "Title is required"}
    proj = project_registry.get_project(project_slug)
    wiki_dir = proj.wiki_dir
    wiki_dir.mkdir(parents=True, exist_ok=True)
    slug = make_slug(title)
    base = wiki_dir / folder if folder else wiki_dir
    base.mkdir(parents=True, exist_ok=True)
    filepath = base / f"{slug}.md"
    today = datetime.now().strftime("%Y-%m-%d")
    body = content or f"# {title}\n\n<!-- Content will be added here -->"
    md = f"""---
title: "{title}"
type: {page_type}
created: {today}
updated: {today}
sources: []
tags: []
---

{body}
"""
    filepath.write_text(md, encoding="utf-8")
    return {"ok": True, "project": proj.slug, "filename": str(filepath.relative_to(wiki_dir))}


def update_page(filename, content, project_slug=None):
    proj = project_registry.get_project(project_slug)
    filepath = proj.wiki_dir / filename
    try:
        assert_writable(filepath)
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    if not filepath.exists():
        return {"ok": False, "error": "Page not found"}
    filepath.write_text(content, encoding="utf-8")
    return {"ok": True, "project": proj.slug}


def delete_page(filename, project_slug=None):
    proj = project_registry.get_project(project_slug)
    filepath = proj.wiki_dir / filename
    try:
        assert_writable(filepath)
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    if not filepath.exists():
        return {"ok": False, "error": "Page not found"}
    if filename in SYSTEM_PAGES:
        return {"ok": False, "error": "Cannot delete system page"}
    filepath.unlink()
    return {"ok": True, "project": proj.slug}


def merge_dashboard_settings(body):
    """Apply optional dashboard keys from POST body; persist SETTINGS."""
    if not isinstance(body, dict):
        return {"ok": False, "error": "expected JSON object"}
    if "cli_type" in body:
        ct = (body.get("cli_type") or "claude").strip().lower()
        if ct not in CLI_TYPES:
            return {"ok": False, "error": f"Unknown cli_type: {ct}"}
        SETTINGS["cli_type"] = ct
    if "claude_cli_binary" in body:
        SETTINGS["claude_cli_binary"] = (body.get("claude_cli_binary") or "claude").strip() or "claude"
    if "claude_cli_extra_args" in body:
        SETTINGS["claude_cli_extra_args"] = body.get("claude_cli_extra_args")
    if "ai_provider" in body:
        ap = (body.get("ai_provider") or "cli").strip().lower()
        if ap not in ("cli", "openai_compatible"):
            return {"ok": False, "error": "ai_provider must be cli or openai_compatible"}
        SETTINGS["ai_provider"] = ap
    if "openai_base_url" in body:
        SETTINGS["openai_base_url"] = (body.get("openai_base_url") or "").strip()
    if "openai_model" in body:
        SETTINGS["openai_model"] = (body.get("openai_model") or "").strip()
    if "openai_api_key" in body:
        key = body.get("openai_api_key")
        if isinstance(key, str) and key.strip():
            SETTINGS["openai_api_key"] = key.strip()
    if "cli_path_extra" in body:
        SETTINGS["cli_path_extra"] = body.get("cli_path_extra") if isinstance(body.get("cli_path_extra"), str) else ""
    if "http_temperature" in body:
        try:
            ht = float(body.get("http_temperature"))
            SETTINGS["http_temperature"] = max(0.0, min(2.0, ht))
        except (TypeError, ValueError):
            SETTINGS["http_temperature"] = 0.2
    if "http_max_tokens" in body:
        try:
            SETTINGS["http_max_tokens"] = max(0, int(body.get("http_max_tokens")))
        except (TypeError, ValueError):
            SETTINGS["http_max_tokens"] = 0
    if "active_ai_profile" in body:
        SETTINGS["active_ai_profile"] = (body.get("active_ai_profile") or "").strip()
    if "ai_profiles" in body and isinstance(body.get("ai_profiles"), dict):
        SETTINGS["ai_profiles"] = body["ai_profiles"]
    _save_settings(SETTINGS)
    # Active profile application handled by llm_provider via SETTINGS
    return {"ok": True}


def api_ai_test_connection():
    if not _openai_http_ready():
        return {"ok": False, "error": "OpenAI-compatible provider not fully configured."}
    ok, text, err = openai_chat_completion(
        [{"role": "user", "content": 'Reply with exactly "OK".'}],
        timeout=45,
    )
    return {"ok": ok, "preview": (text or "").strip()[:120], "error": err}


def api_cli_test():
    """Quick CLI probe — same resolution as ingest (PATH + cli_path_extra)."""
    exe = llm_provider.get_cli_executable(SETTINGS)
    env = _cli_subprocess_env()
    hints = []
    ct = SETTINGS.get("cli_type", "claude")
    cb = (SETTINGS.get("claude_cli_binary") or "").strip()
    if cb and os.path.sep not in cb:
        hints.append("Shell-only aliases are not visible here — use a wrapper script or absolute path.")
    try:
        r = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=15,
            env=env,
        )
        ver = (r.stdout or r.stderr or "").strip().split("\n")[0] if r.returncode == 0 else ""
        if r.returncode == 0:
            return {
                "ok": True,
                "resolved_executable": exe,
                "version_line": ver,
                "cli_type": ct,
                "effective_path_preview": (env.get("PATH") or "")[:240],
            }
        return {
            "ok": False,
            "resolved_executable": exe,
            "cli_type": ct,
            "error": (r.stderr or r.stdout or "")[:400],
            "hints": hints,
            "effective_path_preview": (env.get("PATH") or "")[:240],
        }
    except FileNotFoundError:
        extra = [
            "Add directories to cli_path_extra or use an absolute path to a real binary or wrapper script.",
            "If the command exists only as a shell alias, resolve it with `command -v <name>` and use that path.",
        ]
        return {
            "ok": False,
            "resolved_executable": exe,
            "cli_type": ct,
            "error": f"Executable not found: {SETTINGS.get('claude_cli_binary', 'claude')}",
            "hints": hints + extra,
            "effective_path_preview": (env.get("PATH") or "")[:240],
        }
    except Exception as e:
        return {"ok": False, "resolved_executable": exe, "cli_type": ct, "error": str(e)[:400], "hints": hints}


def api_ai_test():
    """Real end-to-end AI test — actually sends a prompt through configured provider."""
    # Simple prompt that should get a short response regardless of configuration
    prompt = "Reply with exactly 'OK' in one word. Nothing else."
    provider = SETTINGS.get("ai_provider", "cli")

    if provider == "openai_compatible" and _openai_http_ready():
        ok, text, err = openai_chat_completion([{"role": "user", "content": prompt}], timeout=30)
    else:
        ok, text, err = run_claude(prompt, timeout=30, project=None, force_cli=False)

    resp = (text or "").strip()[:500]
    result = {
        "ok": ok,
        "provider": provider,
        "response": resp,
        "valid": ok and len(resp) > 0,
    }
    if err:
        result["error"] = err[:300]
    # For CLI mode, also include CLI probe info
    if provider != "openai_compatible":
        try:
            cli_info = api_cli_test()
            result["cli_probe"] = cli_info
        except Exception:
            pass
    return result


def _iter_raw_project_files(proj):
    raw_dir = proj.raw_dir
    if not raw_dir.exists():
        return
    for f in sorted(raw_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.name.startswith("."):
            continue
        if "assets" in f.parts:
            continue
        yield f


def api_raw_list(project_slug=None):
    proj = _resolve_project(project_slug)
    raw_root = proj.raw_dir.resolve()
    items = []
    for f in _iter_raw_project_files(proj):
        rel = f.relative_to(raw_root).as_posix()
        st = f.stat()
        items.append({"path": rel, "size": st.st_size, "mtime": int(st.st_mtime)})
    return {"ok": True, "project": proj.slug, "items": items}


def api_raw_read(rel_path, project_slug=None):
    proj = _resolve_project(project_slug)
    raw_root = proj.raw_dir.resolve()
    rel = (rel_path or "").replace("\\", "/").strip().lstrip("/")
    if not rel or ".." in rel.split("/"):
        return {"ok": False, "error": "invalid path"}
    full = (proj.raw_dir / rel).resolve()
    try:
        full.relative_to(raw_root)
    except ValueError:
        return {"ok": False, "error": "path escapes raw directory"}
    if not full.exists():
        return {"ok": False, "error": "not found"}
    if not full.is_file():
        return {"ok": False, "error": "not a file"}
    try:
        raw_bytes = full.read_bytes()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    try:
        text = raw_bytes.decode("utf-8")
        binary = False
    except UnicodeDecodeError:
        text = ""
        binary = True
    return {
        "ok": True,
        "project": proj.slug,
        "path": rel,
        "text": text if not binary else "",
        "binary": binary,
        "size": len(raw_bytes),
    }


def api_raw_upload(filename, file_data, folder=None, project_slug=None):
    """Upload a file to raw/ directory.
    filename: original filename (will be sanitized)
    file_data: bytes
    folder: optional subfolder in raw/
    """
    proj = _resolve_project(project_slug)
    raw_root = proj.raw_dir.resolve()
    # Sanitize filename: remove path components
    import re
    safe_name = Path(filename).name
    # Replace dangerous characters but keep Unicode
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', safe_name)
    if not safe_name:
        safe_name = f"unnamed_{int(time.time())}"
    # Build target path
    target_dir = raw_root
    if folder:
        folder = folder.strip().lstrip("/")
        if ".." in folder.split("/"):
            return {"ok": False, "error": "invalid folder"}
        target_dir = raw_root / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    # Deduplicate filename if exists
    target_path = dedupe_raw_path(target_dir / safe_name)
    # Write file
    try:
        target_path.write_bytes(file_data)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Return relative path
    try:
        rel_path = target_path.relative_to(raw_root).as_posix()
    except ValueError:
        rel_path = target_path.name
    return {
        "ok": True,
        "project": proj.slug,
        "path": rel_path,
        "size": len(file_data),
        "name": target_path.name,
    }


# ─── HTTP Handler ───

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SCRIPT_DIR), **kw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query or "")
        q_project = (qs.get("project", [""])[0] or "").strip() or None
        qlang = (qs.get("lang", [""])[0] or "").strip()
        try:
            # unknown slug -> early 404
            if q_project is not None:
                try:
                    project_registry.get_project(q_project)
                except KeyError as e:
                    return self._json({"ok": False, "error": str(e)}, code=404)
            if path == "/api/status":
                return self._json(check_status())
            if path == "/api/projects":
                return self._json(list_projects_api())
            if path == "/api/projects/active":
                return self._json(get_active_project_api())
            if path == "/api/templates":
                names = project_registry.list_template_names()
                out = [{"name": "", "label": "generic", "folders": project_registry.recommended_folders("")}]
                out.extend({"name": n, "label": n, "folders": project_registry.recommended_folders(n)} for n in names)
                return self._json({"ok": True, "templates": out})
            if path == "/api/wiki":
                return self._json(build_wiki_data(q_project, ui_lang=_normalize_ui_lang(qlang)))
            if path == "/api/folders":
                return self._json(get_folder_tree(q_project))
            if path == "/api/hash":
                return self._json({"hash": wiki_hash(q_project)})
            if path == "/api/schema":
                proj = _resolve_project(q_project)
                content = proj.claude_md.read_text("utf-8") if proj.claude_md.exists() else ""
                return self._json({"ok": True, "project": proj.slug, "content": content})
            if path == "/api/history":
                return self._json(git_mgr.list_ingests())
            if path == "/api/provenance":
                proj = _resolve_project(q_project)
                return self._json(build_provenance_graph(proj.wiki_dir))
            if path == "/api/query-stats":
                proj = _resolve_project(q_project)
                return self._json(_get_query_stats(query_log=proj.query_log))
            if path == "/api/graph/build":
                proj = _resolve_project(q_project)
                return self._json(_graph_build_api(proj))
            if path == "/api/graph/stats":
                proj = _resolve_project(q_project)
                return self._json(_graph_stats_api(proj))
            if path == "/api/graph/god-nodes":
                proj = _resolve_project(q_project)
                top = int((qs.get("top_n", ["10"])[0] or "10"))
                return self._json(_graph_god_nodes_api(proj, top))
            if path == "/api/graph/community":
                proj = _resolve_project(q_project)
                return self._json(_graph_community_api(proj))
            if path == "/api/graph/shortest-path":
                proj = _resolve_project(q_project)
                src = (qs.get("source", [""])[0] or "").strip()
                tgt = (qs.get("target", [""])[0] or "").strip()
                return self._json(_graph_shortest_path_api(proj, src, tgt))
            if path == "/api/graph/neighbors":
                proj = _resolve_project(q_project)
                nid = (qs.get("node", [""])[0] or "").strip()
                return self._json(_graph_neighbors_api(proj, nid))
            if path == "/api/graph/step-path":
                proj = _resolve_project(q_project)
                step = (qs.get("step", [""])[0] or "").strip()
                return self._json(_graph_step_path_api(proj, step))
            if path == "/api/graph/insights":
                proj = _resolve_project(q_project)
                return self._json(_graph_insights_api(proj))
            if path == "/api/graph/export":
                proj = _resolve_project(q_project)
                fmt = (qs.get("format", ["json"])[0] or "json").strip()
                return self._json(_graph_export_api(proj, fmt))
            if path == "/api/graph/composite":
                proj = _resolve_project(q_project)
                return self._json(_graph_composite_api(proj))
            if path == "/api/graph/rebuild":
                proj = _resolve_project(q_project)
                return self._json(_graph_rebuild_api(proj))
            if path == "/api/graph/name-community":
                proj = _resolve_project(q_project)
                community_id = (qs.get("community_id", [""])[0] or "").strip()
                name = (qs.get("name", [""])[0] or "").strip()
                return self._json(_graph_name_community_api(proj, community_id, name))
            if path == "/api/graph/get-community":
                proj = _resolve_project(q_project)
                community_id = (qs.get("community_id", [""])[0] or "").strip()
                return self._json(_graph_get_community_api(proj, community_id))

            # ─── knowledge universe APIs ───
            if path == "/api/graph/universe":
                return self._json(_build_universe_graph())

            if path == "/api/graph/universe-config":
                if self.command == "POST":
                    try:
                        length = int(self.headers.get("Content-Length", 0))
                        body = self.rfile.read(length).decode("utf-8")
                        config = json.loads(body)
                        _save_universe_config(config)
                    except Exception as e:
                        return self._json({"ok": False, "error": str(e)})
                return self._json(_load_universe_config())

            if path == "/api/graph/join-universe":
                slug = (qs.get("slug", [""])[0] or "").strip()
                if not slug:
                    return self._json({"ok": False, "error": "Missing slug"})
                config = _load_universe_config()
                excluded = config.get("excluded_projects", [])
                if slug in excluded:
                    excluded.remove(slug)
                    config["excluded_projects"] = excluded
                pending = config.get("pending_confirmation", [])
                if slug in pending:
                    pending.remove(slug)
                    config["pending_confirmation"] = pending
                # Mark as known so it won't show up in changes detection again
                known = config.get("known_projects", [])
                if slug not in known:
                    known.append(slug)
                    config["known_projects"] = known
                # Calculate position
                positions = config.get("galaxy_positions", {})
                if slug not in positions:
                    proj_count = len([
                        p for p in project_registry.list_projects()
                        if p.slug not in excluded
                    ])
                    import math
                    angle = (proj_count - 1) * (2 * math.pi / max(proj_count, 7))
                    positions[slug] = {
                        "x": round(math.cos(angle) * 300, 1),
                        "y": round(math.sin(angle) * 300, 1),
                    }
                    config["galaxy_positions"] = positions
                _save_universe_config(config)
                return self._json({"ok": True, "project": slug, "position": positions.get(slug, {"x": 0, "y": 0})})

            if path == "/api/graph/leave-universe":
                slug = (qs.get("slug", [""])[0] or "").strip()
                if not slug:
                    return self._json({"ok": False, "error": "Missing slug"})
                config = _load_universe_config()
                excluded = config.get("excluded_projects", [])
                if slug not in excluded:
                    excluded.append(slug)
                    config["excluded_projects"] = excluded
                    _save_universe_config(config)
                return self._json({"ok": True, "project": slug})

            if path == "/api/graph/universe-changes":
                # Detect projects that may need confirmation
                config = _load_universe_config()
                excluded = set(config.get("excluded_projects", []))
                pending = config.get("pending_confirmation", [])
                known = set(config.get("known_projects", []))
                all_slugs = {p.slug for p in project_registry.list_projects()}
                # Only report projects NOT yet known (and not currently excluded/pending)
                new_slugs = [s for s in (all_slugs - known) if s not in excluded and s not in pending]
                pending_list = []
                for slug in pending:
                    for p in project_registry.list_projects():
                        if p.slug == slug:
                            pending_list.append({"slug": p.slug, "title": p.title})
                return self._json({
                    "ok": True,
                    "new": new_slugs,
                    "pending": pending_list,
                })

            if path == "/api/graph/universe-search":
                query = (qs.get("query", [""])[0] or "").strip()
                limit = int(qs.get("limit", ["20"])[0])
                if not query:
                    return self._json({"ok": False, "error": "Missing query"})
                universe_data = _build_universe_graph()
                nodes = universe_data["nodes"]
                q_lower = query.lower()
                results = []
                for n in nodes:
                    score = 0.0
                    context = ""
                    label_lower = n["label"].lower()
                    if q_lower in label_lower:
                        score = 1.0
                        context = "标题匹配"
                    elif any(q_lower in t.lower() for t in n.get("tags", [])):
                        score = 0.7
                        context = "标签匹配"
                    if score > 0:
                        results.append({"node": n, "score": score, "context": context})
                results.sort(key=lambda x: -x["score"])
                return self._json({
                    "ok": True,
                    "query": query,
                    "results": results[:limit],
                    "total_matches": len(results),
                })

            if path == "/api/graph/universe-shortest-path":
                src_id = (qs.get("source_id", [""])[0] or "").strip()
                tgt_id = (qs.get("target_id", [""])[0] or "").strip()
                src = (qs.get("source", [""])[0] or "").strip()
                tgt = (qs.get("target", [""])[0] or "").strip()
                if not src_id and not src:
                    return self._json({"ok": False, "error": "Missing source_id or source"})
                if not tgt_id and not tgt:
                    return self._json({"ok": False, "error": "Missing target_id or target"})
                return self._json(_universe_shortest_path_api(source=src or None, target=tgt or None, source_id=src_id or None, target_id=tgt_id or None))

            if path == "/api/graph/shortest-path-with-content":
                proj = _resolve_project(q_project)
                src = (qs.get("source", [""])[0] or "").strip()
                tgt = (qs.get("target", [""])[0] or "").strip()
                if not src or not tgt:
                    return self._json({"ok": False, "error": "Missing source or target"})
                return self._json(_shortest_path_with_content_api(proj, src, tgt))

            if path == "/api/graph/universe-shortest-path-with-content":
                src_id = (qs.get("source_id", [""])[0] or "").strip()
                tgt_id = (qs.get("target_id", [""])[0] or "").strip()
                src = (qs.get("source", [""])[0] or "").strip()
                tgt = (qs.get("target", [""])[0] or "").strip()
                if not src_id and not src:
                    return self._json({"ok": False, "error": "Missing source_id or source"})
                if not tgt_id and not tgt:
                    return self._json({"ok": False, "error": "Missing target_id or target"})
                return self._json(_universe_path_with_content_api(source=src or None, target=tgt or None, source_id=src_id or None, target_id=tgt_id or None))

            if path == "/api/graph/bridges":
                min_sim = float(qs.get("min_similarity", ["0.3"])[0])
                universe_data = _build_universe_graph()
                bridges = universe_data.get("bridges", [])
                filtered = [b for b in bridges if b.get("similarity", 0) >= min_sim]
                filtered.sort(key=lambda x: -x["similarity"])
                return self._json({"ok": True, "bridges": filtered, "count": len(filtered)})

            if path == "/api/index/status":
                proj = _resolve_project(q_project)
                return self._json(get_strategy(proj.wiki_dir))
            if path == "/api/raw/integrity":
                return self._json(check_raw_integrity())
            if path == "/api/raw/list":
                return self._json(api_raw_list(q_project))
            if path == "/api/raw/read":
                rp = (qs.get("path", [""])[0] or "").strip()
                return self._json(api_raw_read(rp, q_project))
            if path == "/api/raw/file":
                rp = (qs.get("path", [""])[0] or "").strip()
                try:
                    proj = project_registry.get_project(q_project)
                    raw_root = proj.raw_dir.resolve()
                    rel = (rp or "").replace("\\", "/").strip().lstrip("/")
                    if not rel or ".." in rel.split("/"):
                        self._send_error(400, "invalid path")
                        return
                    full = (proj.raw_dir / rel).resolve()
                    # Validate the path is within the raw directory
                    try:
                        full.relative_to(raw_root)
                    except ValueError:
                        self._send_error(403, "path escapes raw directory")
                        return
                    if not full.exists():
                        self._send_error(404, "not found")
                        return
                    if not full.is_file():
                        self._send_error(400, "not a file")
                        return
                    # Guess Content-Type based on extension
                    ext = full.suffix.lower()
                    content_types = {
                        ".pdf": "application/pdf",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".gif": "image/gif",
                        ".svg": "image/svg+xml",
                        ".txt": "text/plain; charset=utf-8",
                        ".md": "text/markdown; charset=utf-8",
                        ".html": "text/html; charset=utf-8",
                        ".htm": "text/html; charset=utf-8",
                        ".css": "text/css; charset=utf-8",
                        ".js": "application/javascript; charset=utf-8",
                        ".json": "application/json; charset=utf-8",
                    }
                    content_type = content_types.get(ext, "application/octet-stream")
                    # Read and send the file
                    file_bytes = full.read_bytes()
                    # Send response manually
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(file_bytes)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    # Encode filename for RFC 5987 (UTF-8 support)
                    encoded_filename = urllib.parse.quote(full.name, encoding='utf-8')
                    self.send_header("Content-Disposition", f'inline; filename*=UTF-8\'\'{encoded_filename}')
                    self.end_headers()
                    try:
                        self.wfile.write(file_bytes)
                    except:
                        pass
                    return
                except BrokenPipeError:
                    pass
                except Exception as e:
                    import traceback
                    print(f"[ERROR] serving raw file: {e}\n{traceback.format_exc()[:800]}")
                    self._send_error(500, str(e))
                return
            if path == "/api/claude/diagnose":
                return self._json(diagnose_claude())
            if path == "/api/review/list":
                return self._json(do_review_list(project_slug=q_project))
            if path == "/api/settings":
                proj = _resolve_project(q_project)
                cli_types_list = [{"id": k, "label": v.get("label", k), "default_binary": v.get("default_binary", ""), "wrapper_prefix": v.get("wrapper_prefix", "")} for k, v in CLI_TYPES.items()]
                return self._json({
                    "settings": _settings_for_response(),
                    "project_model": proj.model if not proj.is_legacy else SETTINGS.get("model", "default"),
                    "project_slug": proj.slug,
                    "models": AVAILABLE_MODELS,
                    "http_presets": HTTP_PRESETS,
                    "cli_types": cli_types_list,
                    "llm_ui": _build_llm_ui(),
                })
            if path == "/api/reflect/status":
                last = get_last_reflect_date(project_slug=q_project)
                days_ago = None
                if last:
                    try:
                        from datetime import timedelta
                        d = datetime.strptime(last, "%Y-%m-%d")
                        days_ago = (datetime.now() - d).days
                    except Exception:
                        pass
                return self._json({"last_date": last, "days_ago": days_ago})
            if path == "/api/schedules":
                schedules = _sched_load()[0]
                return self._json({"ok": True, "schedules": schedules})
            # API path but no match
            if path.startswith("/api/"):
                return self._json({"ok": False, "error": f"Unknown endpoint: {path}"}, code=404)
            # static file
            super().do_GET()
        except BrokenPipeError:
            # client disconnected — silently ignore
            pass
        except Exception as e:
            import traceback
            err_msg = f"{type(e).__name__}: {e}"
            print(f"[ERROR] GET {path}: {err_msg}\n{traceback.format_exc()[:1000]}")
            try:
                self._json({"ok": False, "error": err_msg, "endpoint": path}, code=500)
            except Exception:
                pass

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            # Check for file upload first
            content_type = self.headers.get("Content-Type", "")
            if path == "/api/raw/upload" and content_type.startswith("multipart/form-data"):
                fields, files = self._parse_multipart()
                p_slug = (fields.get("project") or "").strip() or None
                folder = (fields.get("folder") or "").strip() or None
                if "file" not in files:
                    return self._json({"ok": False, "error": "no file provided"})
                f = files["file"]
                return self._json(api_raw_upload(f["filename"], f["data"], folder=folder, project_slug=p_slug))
            # Regular JSON body for other endpoints
            body = self._read_body()

            # all endpoints use body.project (unknown slug raises KeyError from get_project)
            p_slug = (body.get("project") or "").strip() or None
            if path == "/api/ingest":
                return self._json(do_ingest(body.get("title", ""), body.get("content", ""), body.get("folder", ""), project_slug=p_slug))
            if path == "/api/query":
                return self._json(
                    do_query(
                        body.get("question", ""),
                        project_slug=p_slug,
                        lang=body.get("lang"),
                    )
                )
            if path == "/api/query/save":
                return self._json(do_query_save(body.get("title", ""), body.get("content", ""), project_slug=p_slug))
            if path == "/api/lint":
                return self._json(do_lint(project_slug=p_slug))
            if path == "/api/lint/fix":
                return self._json(do_lint_fix(project_slug=p_slug))
            if path == "/api/links/validate":
                return self._json(validate_links_api(project_slug=p_slug))
            if path == "/api/links/fix-batch":
                return self._json(fix_links_batch_api(
                    project_slug=p_slug,
                    auto_create=body.get("auto_create", False),
                    alias_map=body.get("alias_map", {}),
                ))
            if path == "/api/folder":
                return self._json(create_folder(body.get("name", ""), body.get("parent", ""), project_slug=p_slug))
            if path == "/api/page":
                return self._json(create_page(body.get("title", ""), body.get("type", "concept"), body.get("folder", ""), body.get("content", ""), project_slug=p_slug))
            if path == "/api/page/update":
                return self._json(update_page(body.get("filename", ""), body.get("content", ""), project_slug=p_slug))
            if path == "/api/page/delete":
                return self._json(delete_page(body.get("filename", ""), project_slug=p_slug))
            if path == "/api/schema":
                proj = project_registry.get_project(p_slug)
                proj.claude_md.write_text(body.get("content", ""), encoding="utf-8")
                return self._json({"ok": True, "project": proj.slug})
            if path == "/api/revert":
                return self._json(git_mgr.revert_ingest(body.get("commit_hash", "")))
            if path == "/api/provenance/fix":
                return self._json(do_fix_citations(body.get("page", ""), project_slug=p_slug))
            if path == "/api/reflect":
                return self._json(do_reflect(body.get("window", "last-10-ingests"), project_slug=p_slug))
            if path == "/api/write":
                return self._json(do_write(body.get("topic", ""), body.get("length", "medium"), body.get("style", "blog"), project_slug=p_slug))
            if path == "/api/compare":
                return self._json(do_compare(body.get("page_a", ""), body.get("page_b", ""), body.get("save_as", ""), project_slug=p_slug))
            if path == "/api/review/refresh":
                return self._json(do_review_refresh(body.get("filename", ""), project_slug=p_slug))
            if path == "/api/git/commit":
                msg = (body.get("message") or "").strip()
                if not msg:
                    return self._json({"ok": False, "error": "commit message required"})
                proj = _resolve_project(p_slug)
                hash_val = git_mgr.commit_generic(msg, project=proj)
                return self._json({"ok": True, "commit_hash": hash_val, "project": proj.slug})
            # ─── SSE Streaming Endpoints ───
            if path == "/api/lint/stream":
                return _handle_stream(self, stream_lint(project_slug=p_slug))
            if path == "/api/lint/fix/stream":
                return _handle_stream(self, stream_lint_fix(project_slug=p_slug))
            if path == "/api/reflect/stream":
                return _handle_stream(self, stream_reflect(body.get("window", "last-10-ingests"), project_slug=p_slug))
            if path == "/api/review/refresh/stream":
                return _handle_stream(self, stream_review_refresh(body.get("filename", ""), project_slug=p_slug))
            if path == "/api/provenance/fix/stream":
                return _handle_stream(self, stream_fix_citations(body.get("page", ""), project_slug=p_slug))
            if path == "/api/ingest/stream":
                return _handle_stream(self, stream_ingest(body.get("title", ""), body.get("content", ""), body.get("folder", ""), project_slug=p_slug))
            if path == "/api/write/stream":
                return _handle_stream(self, stream_write(body.get("topic", ""), body.get("length", "medium"), body.get("style", "blog"), project_slug=p_slug))
            if path == "/api/compare/stream":
                return _handle_stream(self, stream_compare(body.get("page_a", ""), body.get("page_b", ""), body.get("save_as", ""), project_slug=p_slug))
            if path == "/api/loop/stream":
                return _handle_stream(self, stream_loop(
                    steps=body.get("steps"), include_ingest=body.get("include_ingest", False),
                    reflect_window=body.get("reflect_window", "last-10-ingests"),
                    project_slug=p_slug, continue_on_error=body.get("continue_on_error", False),
                ))
            if path == "/api/slides":
                return self._json(do_slides(body.get("page", ""), project_slug=p_slug))
            if path == "/api/search":
                return self._json(do_search(body.get("query", ""), body.get("top_k", 10), project_slug=p_slug))
            if path == "/api/suggest/sources":
                return self._json(do_suggest_sources(project_slug=p_slug))
            if path == "/api/obsidian/register":
                return self._json(register_obsidian_vault())
            if path == "/api/assistant":
                return self._json(do_assistant_chat(
                    body.get("question", ""),
                    body.get("lang", "en"),
                    body.get("history", []),
                    body.get("project", None),
                ))
            if path == "/api/settings":
                _AI_KEYS = (
                    "cli_type", "claude_cli_binary", "claude_cli_extra_args", "cli_path_extra", "ai_provider",
                    "openai_base_url", "openai_model", "openai_api_key",
                    "http_temperature", "http_max_tokens",
                    "active_ai_profile", "ai_profiles",
                )
                if any(k in body for k in _AI_KEYS):
                    mr = merge_dashboard_settings(body)
                    if not mr.get("ok"):
                        return self._json(mr, code=400)
                if "model" not in body:
                    return self._json({
                        "ok": True,
                        "settings": _settings_for_response(),
                        "llm_ui": _build_llm_ui(),
                    })
                model = body.get("model", "default")
                valid = [m["id"] for m in AVAILABLE_MODELS]
                if model not in valid:
                    return self._json({"ok": False, "error": f"Unknown model: {model}"})
                proj = project_registry.get_project(p_slug)
                if proj.is_legacy:
                    SETTINGS["model"] = model
                    _save_settings(SETTINGS)
                    return self._json({"ok": True, "project": "", "settings": _settings_for_response(), "llm_ui": _build_llm_ui()})
                try:
                    updated = project_registry.update_project_settings(proj.slug, model=model)
                    return self._json({
                        "ok": True, "project": updated.slug, "model": updated.model,
                        "settings": _settings_for_response(),
                        "llm_ui": _build_llm_ui(),
                    })
                except ValueError as e:
                    return self._json({"ok": False, "error": str(e)})
            if path == "/api/ai/test":
                return self._json(api_ai_test())
            if path == "/api/cli/test":
                return self._json(api_cli_test())
            if path == "/api/index/rebuild":
                proj = project_registry.get_project(p_slug)
                result = rebuild_index(proj.wiki_dir)
                if result["ok"]:
                    git_mgr._stage_all(project=proj)
                    git_mgr._run("commit", "-m", f"index{git_mgr._slug_prefix(proj)}: rebuild ({result['mode']})")
                return self._json(result)

            # ─── Wiki Loop ───────────────────────────────────────────────
            if path == "/api/loop/run":
                return self._json(wiki_ops.run_loop(
                    project=p_slug,
                    steps=body.get("steps", ["lint", "lint_fix", "reflect"]),
                    include_ingest=body.get("include_ingest", False),
                    reflect_window=body.get("reflect_window", "last-10-ingests"),
                    continue_on_error=body.get("continue_on_error", False),
                ))

            # ─── Schedules ───────────────────────────────────────────────
            if path == "/api/schedules":
                # POST: create or update
                sched = body
                if not sched.get("id"):
                    import hashlib
                    sched["id"] = hashlib.md5(sched.get("name", "").encode()).hexdigest()[:8]
                schedules = _sched_load()[0]
                # Update if exists
                updated = False
                for i, s in enumerate(schedules):
                    if s.get("id") == sched["id"]:
                        schedules[i] = sched
                        updated = True
                        break
                if not updated:
                    schedules.append(sched)
                _save_sched_files(schedules)
                return self._json({"ok": True, "schedule": sched})

            if path.startswith("/api/schedules/") and self.command == "DELETE":
                sched_id = path.split("/api/schedules/")[-1].split("/")[0]
                schedules = _sched_load()[0]
                schedules = [s for s in schedules if s.get("id") != sched_id]
                _save_sched_files(schedules)
                return self._json({"ok": True})

            if path.startswith("/api/schedules/") and path.endswith("/run"):
                parts = path.split("/")
                sched_id = parts[-2]
                schedules = _sched_load()[0]
                sched = next((s for s in schedules if s.get("id") == sched_id), None)
                if not sched:
                    return self._json({"ok": False, "error": "schedule not found"}, code=404)
                return self._json(wiki_ops.run_loop(
                    project=sched.get("project", p_slug),
                    steps=sched.get("steps", ["lint"]),
                    include_ingest=sched.get("include_ingest", False),
                    reflect_window=sched.get("reflect_window", "last-10-ingests"),
                ))

            if path.startswith("/api/schedules/") and path.endswith("/toggle"):
                parts = path.split("/")
                sched_id = parts[-2]
                schedules = _sched_load()[0]
                for s in schedules:
                    if s.get("id") == sched_id:
                        s["enabled"] = not s.get("enabled", False)
                        break
                _save_sched_files(schedules)
                return self._json({"ok": True})

            if path == "/api/projects/create":
                return self._json(create_project_api(
                    body.get("slug", ""),
                    body.get("title", ""),
                    body.get("description", ""),
                    body.get("model", "default"),
                    body.get("template", ""),
                ))
            if path == "/api/projects/switch":
                return self._json(switch_project_api(body.get("slug", "")))
            if path == "/api/projects/update":
                return self._json(update_project_api(
                    body.get("slug", ""),
                    model=body.get("model"),
                    title=body.get("title"),
                    description=body.get("description"),
                ))
            if path == "/api/projects/delete":
                return self._json(delete_project_api(
                    body.get("slug", ""),
                    bool(body.get("confirm", False)),
                ))
            # ─── Knowledge Universe config (POST) ──────────────────────
            if path == "/api/graph/universe-config":
                try:
                    existing = _load_universe_config()
                    # Merge: only update keys provided in request body
                    for k, v in body.items():
                        existing[k] = v
                    _save_universe_config(existing)
                except Exception as e:
                    return self._json({"ok": False, "error": str(e)})
                return self._json(_load_universe_config())
            # unmatched API path
            return self._json({"ok": False, "error": f"Unknown endpoint: {path}"}, code=404)
        except BrokenPipeError:
            pass
        except Exception as e:
            import traceback
            err_msg = f"{type(e).__name__}: {e}"
            print(f"[ERROR] POST {path}: {err_msg}\n{traceback.format_exc()[:1000]}")
            try:
                self._json({"ok": False, "error": err_msg, "endpoint": path}, code=500)
            except Exception:
                pass

    def do_DELETE(self):
        """Handle DELETE requests by delegating to do_POST logic."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            body = {}
            # Reuse POST routing for DELETE (schedules, etc.)
            # ─── Schedules DELETE ──────────────────────────────────────
            if path.startswith("/api/schedules/"):
                sched_id = path.split("/api/schedules/")[-1].split("/")[0]
                schedules = SETTINGS.get("schedules", [])
                SETTINGS["schedules"] = [s for s in schedules if s.get("id") != sched_id]
                _save_settings(SETTINGS)
                return self._json({"ok": True})
            return self._json({"ok": False, "error": f"Unknown endpoint: {path}"}, code=404)
        except BrokenPipeError:
            pass
        except Exception as e:
            import traceback
            err_msg = f"{type(e).__name__}: {e}"
            print(f"[ERROR] DELETE {path}: {err_msg}\n{traceback.format_exc()[:1000]}")
            try:
                self._json({"ok": False, "error": err_msg, "endpoint": path}, code=500)
            except Exception:
                pass

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            text = raw.decode("utf-8").strip()
            if not text:
                return {}
            return json.loads(text)
        except Exception:
            return {}

    def _json(self, data, code=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            # minimal error response on serialization failure
            body = json.dumps({"ok": False, "error": f"serialization failed: {e}"}).encode("utf-8")
            code = 500
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _send_error(self, code, message):
        """Send a simple plain text error response."""
        try:
            body = message.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _parse_multipart(self):
        """Parse multipart/form-data, returns (fields dict, files dict).
        files: {name: {filename, content_type, data}}
        """
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            return {}, {}
        # Parse boundary
        import cgi
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
        }
        fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)
        fields = {}
        files = {}
        for key in fs.keys():
            item = fs[key]
            if item.filename:
                files[key] = {
                    "filename": item.filename,
                    "content_type": item.headers.get("Content-Type", "application/octet-stream"),
                    "data": item.file.read() if item.file else b"",
                }
            else:
                fields[key] = item.value if item.value else ""
        return fields, files


    def _sse_start(self):
        """Send SSE response headers."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def _sse_send(self, event_dict):
        """Send a single SSE event. Raises BrokenPipeError on disconnect."""
        data = _sse_data(event_dict).encode("utf-8")
        self.wfile.write(data)
        self.wfile.flush()

    def _sse_end(self):
        """Send final SSE marker to signal completion."""
        self._sse_send({"type": "__end__"})
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {args[0]}" if args else "")


import socket

class DualStackHTTPServer(HTTPServer):
    address_family = socket.AF_INET6
    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()

if __name__ == "__main__":
    from scheduler import WikiScheduler

    print(f"LLM Wiki Dashboard → http://localhost:{PORT}")
    print(f"Project: {PROJECT_ROOT}")
    print(f"Wiki:    {WIKI_DIR} ({sum(1 for _ in WIKI_DIR.rglob('*.md'))} pages)")

    scheduler = WikiScheduler(SETTINGS_FILE)
    scheduler.start()
    print("Scheduler started (checking every 60s)")

    server = DualStackHTTPServer(("::", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        scheduler.stop()
        server.server_close()
        print("Done.")
