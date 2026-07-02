"""Shared wiki operation prompts and CLI executor.

Side-effect free: does NOT import server.py, does NOT trigger git init,
does NOT mutate global PATH.  All state is passed as parameters or read
from config files at call time.

Used by both dashboard/server.py and mcp-server/memex_mcp.py.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator

# ─── locate repo + bring dashboard/ onto sys.path ────────────────────────────

_OPS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = _OPS_ROOT.parent
DASHBOARD_DIR = _OPS_ROOT

# Ensure dashboard/ is on sys.path for project_registry, index_strategy imports
if str(DASHBOARD_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(DASHBOARD_DIR))

import project_registry  # noqa: E402
import llm_provider  # noqa: E402


def _resolve(project: str | None) -> project_registry.Project:
    slug = (project or "").strip() or None
    return project_registry.get_project(slug)


# ─── prompt builders ─────────────────────────────────────────────────────────


def build_ingest_prompt(
    title: str, content: str, folder: str = "", project: str = ""
) -> str:
    proj = _resolve(project)
    from index_strategy import get_index_instruction  # noqa: E402

    idx_inst = get_index_instruction(proj.wiki_dir)
    slug = make_slug(title)
    folder_inst = f" Place any new pages under wiki/{folder}/." if folder else ""
    report_rel = f"ingest-reports/{datetime.now().strftime('%Y-%m-%d-%H%M')}-{slug}.md"
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


def build_lint_prompt(project: str = "") -> str:
    proj = _resolve(project)
    from index_strategy import get_index_instruction  # noqa: E402

    idx_inst = get_index_instruction(proj.wiki_dir)
    today = datetime.now().strftime("%Y-%m-%d")
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


def build_lint_fix_prompt() -> str:
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


def build_reflect_prompt(window: str = "last-10-ingests", project: str = "") -> str:
    proj = _resolve(project)
    proj.reflect_reports.mkdir(parents=True, exist_ok=True)
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
(findings or "none")

Include parse markers before sections: SUGGESTED_PAGES:, SUGGESTED_SCHEMA:, SUGGESTED_SOURCES:, CONTRADICTION_REVIEW:"""


def build_write_prompt(
    topic: str, length: str = "medium", style: str = "blog", project: str = ""
) -> str:
    proj = _resolve(project)
    from index_strategy import get_index_instruction  # noqa: E402

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


def build_compare_prompt(
    page_a: str, page_b: str, save_as: str = "", project: str = ""
) -> str:
    return f"""Read wiki/{page_a} and wiki/{page_b}, then compare them.

Structure:
## Common ground
## Differences
## Relationship / implications

Include [^src-*] citations for claims; draw on sources from both pages."""


def build_loop_prompt(
    steps: list[str],
    include_ingest: bool,
    reflect_window: str,
    project: str = "",
) -> str:
    proj = _resolve(project)
    step_descriptions = {
        "lint": "Run full wiki lint audit per CLAUDE.md checklist",
        "lint_fix": "Auto-fix all lint issues found",
        "reflect": f"Run reflect analysis (window={reflect_window})",
        "validate_links": "Validate all wikilinks and repair broken references",
    }
    steps_desc = "\n".join(
        f"- {s}: {step_descriptions.get(s, s)}" for s in steps
    )
    ingest_note = "\n- ingest: Detect and ingest any new raw sources first" if include_ingest else ""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""You are running a wiki maintenance loop for project {proj.slug or "root"}.

Execute these steps in order. For each step:
1. Perform the operation
2. Summarize the result in 2-4 lines starting with "STEP_RESULT: <step_name>"
3. Move to the next step

Steps to execute:
{steps_desc}{ingest_note}

After all steps complete, provide a final summary starting with "LOOP_SUMMARY:" listing each step's status (ok/failed/skipped) and key findings.

Today: {today}"""


# ─── CLI execution ───────────────────────────────────────────────────────────


def run_wiki_operation(
    prompt: str,
    project: str = "",
    timeout: int | None = None,
    settings: dict | None = None,
) -> tuple[bool, str, str]:
    """Run a wiki operation via unified LLM provider (CLI by default for tool-based ops).

    Returns (ok, stdout, stderr).
    """
    if settings is None:
        settings = llm_provider.load_settings()
    proj = _resolve(project)
    return llm_provider.run(
        prompt=prompt,
        settings=settings,
        project=proj,
        timeout=timeout,
        force_cli=True,  # wiki ops always need tool use
    )


# ─── helper: git operations (minimal, no GitManager dependency) ──────────────


def _git_stage_all(proj, settings: dict | None = None):
    """Stage project changes for git commit."""
    cwd = str(PROJECT_ROOT)
    if proj.is_legacy:
        for p in ["wiki", "raw", "ingest-reports", "reflect-reports"]:
            if (PROJECT_ROOT / p).exists():
                subprocess.run(["git", "add", f"{p}/"], cwd=cwd, capture_output=True)
    else:
        base = str(proj.root.relative_to(PROJECT_ROOT))
        for sub in ("wiki", "raw", "ingest-reports", "reflect-reports", ".settings.json", "query-log.jsonl", "CLAUDE.md"):
            if (proj.root / sub).exists():
                subprocess.run(["git", "add", f"{base}/{sub}"], cwd=cwd, capture_output=True)
        if project_registry.REGISTRY_FILE.exists():
            subprocess.run(["git", "add", "projects.json"], cwd=cwd, capture_output=True)


def _git_commit(message: str, proj) -> dict:
    """Stage and commit. Returns {ok, hash, files}."""
    cwd = str(PROJECT_ROOT)
    _git_stage_all(proj)
    status = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=cwd, capture_output=True, text=True,
    )
    files = [f for f in status.stdout.strip().split("\n") if f]
    if not files:
        return {"ok": True, "no_op": True, "hash": None, "files": []}
    r = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=cwd, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return {"ok": False, "error": (r.stderr or r.stdout)[:500]}
    log = subprocess.run(
        ["git", "log", "-1", "--format=%H"],
        cwd=cwd, capture_output=True, text=True,
    )
    return {"ok": True, "hash": log.stdout.strip(), "files": files}


# ─── slug + link helpers (imported from shared dashboard.models) ──────────────────

from dashboard.models import (
    make_slug, parse_fm, extract_links, extract_citations,
    FRONTMATTER_RE, WIKILINK_RE, resolve_wikilink_target,
)
# ─── detect_new_sources ─────────────────────────────────────────────────────


def detect_new_sources(project: str = "") -> list[dict]:
    """Check raw/ for source files that haven't been cited in any wiki page.

    Returns list of {path, slug, cited} dicts.
    """
    proj = _resolve(project)
    results: list[dict] = []
    if not proj.raw_dir.exists():
        return results

    # Build set of known src slugs from wiki pages
    cited_slugs: set[str] = set()
    if proj.wiki_dir.exists():
        for md in proj.wiki_dir.rglob("*.md"):
            try:
                text = md.read_text("utf-8")
                _, body = parse_fm(text)
                for ref in re.findall(r"\[\^src-([^\]]+)\]", body):
                    cited_slugs.add(ref.strip())
            except Exception:
                pass

    for f in sorted(proj.raw_dir.rglob("*")):
        if not f.is_file() or f.name.startswith(".") or "assets" in f.parts:
            continue
        slug = f.stem
        results.append({
            "path": str(f.relative_to(proj.raw_dir)),
            "slug": slug,
            "cited": slug in cited_slugs or f"src-{slug}" in cited_slugs,
        })

    return results


# ─── _collect_reflect_context (mirrors server.py) ────────────────────────────


def _collect_reflect_context(
    window: str, project: project_registry.Project | None = None
) -> dict:
    if project is None:
        project = _resolve(None)
    ingest_dir = project.ingest_reports
    qlog_file = project.query_log if hasattr(project, "query_log") and project.query_log else PROJECT_ROOT / "query-log.jsonl"

    log_file = project.wiki_dir / "log.md"
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

    if window == "last-10-ingests":
        reports = reports[:10]
    elif window == "last-week":
        from datetime import timedelta

        cutoff = (datetime.now() - timedelta(days=7)).isoformat()[:10]
        reports = [r for r in reports if r["name"][:10] >= cutoff]

    return {
        "log_text": log_text[-3000:],
        "reports": reports[:20],
        "low_ratio_queries": low_ratio_queries[:10],
    }


# ─── validate_links (mirrors server.py validate_links_api) ───────────────────


def validate_links(project: str = "") -> dict:
    """Scan all wiki pages for broken links, orphan references, missing citations."""
    proj = _resolve(project)
    wiki_dir = proj.wiki_dir
    issues = {
        "broken_links": [],
        "self_broken": [],
        "orphan_references": [],
        "missing_citations": [],
        "summary": {},
    }
    pages = _scan_wiki_pages(wiki_dir)
    known_filenames = set(pages.keys())
    slug_map = {}
    for fn in known_filenames:
        slug_map[fn.replace("/", "-").lower()] = fn
        slug_map[fn.replace("/", "_").lower()] = fn
        slug_map[fn.lower().replace(".md", "")] = fn

    citation_re = re.compile(r"\[\^src-[a-zA-Z0-9_-]+\]")

    total_claims = 0
    cited_claims = 0
    for fn, info in pages.items():
        content = info["content"]
        matches = WIKILINK_RE.findall(content)
        for target in matches:
            target_lower = target.strip().lower()
            target_slug = target_lower.replace(" ", "-")
            matched = False
            if (target_slug + ".md") in known_filenames:
                matched = True
            elif target_slug in slug_map:
                matched = True
            if not matched:
                resolved = resolve_wikilink_target(
                    target_slug, known_filenames, title_hint=info.get("title", ""))
                if resolved:
                    matched = True
            if not matched:
                issues["broken_links"].append({
                    "from_page": fn,
                    "target": target.strip(),
                    "hint": f"No matching page found. Consider creating [[{target.strip()}]] or removing the link.",
                })
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("---") or line.startswith("-"):
                continue
            claim_indicators = ["is", "are", "was", "the", "this", "that"]
            has_claim_hint = any(ind in line.lower() for ind in claim_indicators)
            if has_claim_hint and len(line) > 30 and "[^" not in line and not line.startswith(">") and not line.startswith("*"):
                total_claims += 1
                if citation_re.search(line):
                    cited_claims += 1

    issues["missing_citations"] = [] if cited_claims / max(total_claims, 1) > 0.8 else [
        f"{total_claims - cited_claims}/{total_claims} potentially uncited claims detected"
    ]

    summary = {
        "total_pages": len(pages),
        "broken_link_count": len(issues["broken_links"]),
        "citation_health": f"{cited_claims}/{total_claims}" if total_claims else "N/A",
        "critical": len(issues["broken_links"]) > 5,
    }
    issues["summary"] = summary
    return {"ok": True, "project": proj.slug, "issues": issues, "summary": summary}


def _scan_wiki_pages(wiki_dir: Path) -> dict:
    pages = {}
    if not wiki_dir or not wiki_dir.exists():
        return pages
    for f in sorted(wiki_dir.rglob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
            title_match = re.search(r'^title:\s*["\']?(.+?)["\']?$', content, re.M)
            title = title_match.group(1).strip() if title_match else f.stem.replace("-", " ").title()
            rel = f.relative_to(wiki_dir)
            pages[rel.as_posix()] = {"content": content, "title": title, "path": str(f)}
        except Exception:
            pass
    return pages


# ─── run_loop ────────────────────────────────────────────────────────────────

# Map of step name → (prompt_builder, commit_message, has_progress_callback)
_STEP_HANDLERS: dict[str, dict] = {
    "ingest": {"label": "Ingest", "commit_msg": "loop(ingest): auto-ingest new sources"},
    "lint": {"label": "Lint", "commit_msg": "loop(lint): lint audit"},
    "lint_fix": {"label": "Lint Fix", "commit_msg": "loop(lint_fix): auto-fix lint issues"},
    "reflect": {"label": "Reflect", "commit_msg": "loop(reflect): reflect analysis"},
    "validate_links": {"label": "Validate Links", "commit_msg": "loop(validate_links): link validation"},
}

_PROMPT_BUILDERS = {
    "lint": build_lint_prompt,
    "lint_fix": lambda project="": build_lint_fix_prompt(),
    "reflect": build_reflect_prompt,
    "validate_links": lambda project="": "",  # handled specially below
}


def run_loop(
    project: str = "",
    steps: list[str] | None = None,
    include_ingest: bool = False,
    reflect_window: str = "last-10-ingests",
    continue_on_error: bool = False,
    on_progress: Callable[[dict], None] | None = None,
) -> dict:
    """Execute wiki maintenance loop steps sequentially.

    Args:
        project: Project slug.
        steps: List of step names to execute. Default: ["lint", "lint_fix", "reflect"].
        include_ingest: Whether to ingest new sources first.
        reflect_window: Window for reflect analysis.
        continue_on_error: Whether to continue after a step fails.
        on_progress: Optional callback for progress events.

    Returns:
        {ok, project, steps_results, total_duration_sec}
    """
    if steps is None:
        steps = ["lint", "lint_fix", "reflect"]

    proj = _resolve(project)
    start_time = time.monotonic()
    step_results: list[dict] = []

    def _emit(evt: dict) -> None:
        if on_progress:
            on_progress(evt)

    # Step 0: ingest if requested
    if include_ingest:
        _emit({"type": "step_start", "step": "ingest", "label": "Ingest"})
        new_sources = detect_new_sources(project)
        uncited = [s for s in new_sources if not s["cited"]]
        if uncited:
            step_start = time.monotonic()
            all_ok = True
            outputs = []
            for src in uncited:
                raw_file = proj.raw_dir / src["path"]
                try:
                    content = raw_file.read_text("utf-8")
                except Exception as e:
                    outputs.append(f"Failed to read {src['path']}: {e}")
                    continue
                prompt = build_ingest_prompt(
                    title=src["slug"], content=content, project=project
                )
                ok, out, err = run_wiki_operation(prompt, project)
                outputs.append(f"{'ok' if ok else 'fail'} {src['path']}: {out[:200]}")
                if not ok:
                    all_ok = False
                    if not continue_on_error:
                        break

            dur = round(time.monotonic() - step_start, 1)
            result = {
                "name": "ingest",
                "status": "ok" if all_ok else "failed",
                "duration_sec": dur,
                "summary": "\n".join(outputs[:20]),
                "sources_processed": len(uncited),
            }
            step_results.append(result)
            _emit({"type": "step_done", "step": "ingest", **result})
        else:
            result = {"name": "ingest", "status": "skipped", "reason": "no_new_sources", "duration_sec": 0, "summary": "All sources already cited."}
            step_results.append(result)
            _emit({"type": "step_done", "step": "ingest", **result})

    # Main steps
    for step_name in steps:
        handler = _STEP_HANDLERS.get(step_name)
        if not handler:
            step_results.append({
                "name": step_name, "status": "skipped",
                "reason": f"unknown step: {step_name}", "duration_sec": 0, "summary": "",
            })
            _emit({"type": "step_done", "step": step_name, "status": "skipped",
                    "reason": f"unknown step: {step_name}"})
            continue

        _emit({"type": "step_start", "step": step_name, "label": handler["label"]})
        step_start = time.monotonic()

        try:
            if step_name == "validate_links":
                result_data = validate_links(project)
                ok = result_data.get("ok", False)
                out = json.dumps(result_data.get("summary", {}), ensure_ascii=False)
                err = ""
            else:
                builder = _PROMPT_BUILDERS.get(step_name)
                if builder is None:
                    step_results.append({
                        "name": step_name, "status": "skipped",
                        "reason": f"no prompt builder for: {step_name}", "duration_sec": 0,
                    })
                    _emit({"type": "step_done", "step": step_name, "status": "skipped"})
                    continue
                if step_name == "reflect":
                    prompt = builder(window=reflect_window, project=project)
                else:
                    prompt = builder(project=project)
                ok, out, err = run_wiki_operation(prompt, project)

            dur = round(time.monotonic() - step_start, 1)

            # Git commit on success
            commit_hash = None
            if ok:
                try:
                    c = _git_commit(handler["commit_msg"], proj)
                    commit_hash = c.get("hash")
                except Exception:
                    pass

            # Extract summary
            summary = out[:500] if out else ""
            if step_name == "lint" and "Lint Report" in out:
                # Extract just the report header
                m = re.search(r"## Lint Report.*?(?=### |$)", out, re.DOTALL)
                if m:
                    summary = m.group(0).strip()[:500]

            result = {
                "name": step_name,
                "status": "ok" if ok else "failed",
                "duration_sec": dur,
                "summary": summary,
                "error": err[:200] if err else "",
                "commit_hash": commit_hash,
            }
        except Exception as e:
            dur = round(time.monotonic() - step_start, 1)
            result = {
                "name": step_name, "status": "failed",
                "duration_sec": dur, "summary": f"Exception: {e}", "error": str(e)[:200],
            }

        step_results.append(result)
        _emit({"type": "step_done", "step": step_name, **result})

        if not result["status"] == "ok" and not continue_on_error:
            _emit({"type": "loop_aborted", "reason": f"Step {step_name} failed"})
            break

    total = round(time.monotonic() - start_time, 1)
    all_ok = all(r["status"] in ("ok", "skipped") for r in step_results)
    _emit({"type": "loop_done", "ok": all_ok, "total_duration_sec": total})

    return {
        "ok": all_ok,
        "project": proj.slug,
        "steps": step_results,
        "total_duration_sec": total,
    }


# ─── individual operation wrappers (for MCP tools) ───────────────────────────


def op_ingest(title: str, content: str, folder: str = "", project: str = "") -> dict:
    prompt = build_ingest_prompt(title, content, folder, project)
    ok, out, err = run_wiki_operation(prompt, project)
    proj = _resolve(project)
    if ok:
        _git_commit(f"ingest: {title}", proj)
    return {"ok": ok, "project": proj.slug, "output": out, "error": err}


def op_lint(project: str = "") -> dict:
    prompt = build_lint_prompt(project)
    ok, out, err = run_wiki_operation(prompt, project)
    proj = _resolve(project)
    if ok:
        _git_commit("lint: audit", proj)
    return {"ok": ok, "project": proj.slug, "report": out, "error": err}


def op_lint_fix(project: str = "") -> dict:
    prompt = build_lint_fix_prompt()
    ok, out, err = run_wiki_operation(prompt, project)
    proj = _resolve(project)
    if ok:
        _git_commit("lint: auto-fix", proj)
    return {"ok": ok, "project": proj.slug, "result": out, "error": err}


def op_reflect(window: str = "last-10-ingests", project: str = "") -> dict:
    prompt = build_reflect_prompt(window, project)
    ok, out, err = run_wiki_operation(prompt, project)
    proj = _resolve(project)
    if ok:
        today = datetime.now().strftime("%Y-%m-%d")
        _git_commit(f"reflect: {today} ({window})", proj)
    return {"ok": ok, "project": proj.slug, "report": out, "error": err}


def op_compare(page_a: str, page_b: str, save_as: str = "", project: str = "") -> dict:
    prompt = build_compare_prompt(page_a, page_b, save_as, project)
    ok, out, err = run_wiki_operation(prompt, project)
    proj = _resolve(project)
    return {"ok": ok, "project": proj.slug, "result": out, "error": err}


def op_write(topic: str, length: str = "medium", style: str = "blog", project: str = "") -> dict:
    prompt = build_write_prompt(topic, length, style, project)
    ok, out, err = run_wiki_operation(prompt, project)
    proj = _resolve(project)
    return {"ok": ok, "project": proj.slug, "result": out, "error": err}


def op_validate_links(project: str = "") -> dict:
    return validate_links(project)
