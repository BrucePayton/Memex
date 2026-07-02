"""
AICC (AI Interaction Context Compression) session synthesis.

After each wiki operation, write a telegraphic summary to
wiki/sessions/<date>.md so the next agent session can quickly
recover context without re-reading the entire wiki.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def synthesize_session(
    wiki_dir: Path,
    operation: str,
    summary: str,
    files_changed: list[str] = None,
    next_steps: list[str] = None,
) -> Path:
    """Write a session synthesis file after a wiki operation.

    Format (telegraphic, compact):
    ```
    ## Operation: ingest
    - Changed: concepts/ai.md, entities/ml.md
    - Key decisions: Added Transformer entity, linked to Attention concept
    - Next: Review cascade-stale pages

    ## Technical Context
    - Wiki state: 12 pages, 5 communities
    - Last ingest: 2026-07-01
    ```
    """
    sessions_dir = wiki_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    session_file = sessions_dir / f"{today}.md"

    # Build telegraphic synthesis
    lines = [
        f"## Operation: {operation}",
        f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    if files_changed:
        lines.append(f"- Changed: {', '.join(files_changed[:15])}")
    if summary:
        lines.append(f"- Summary: {summary}")
    if next_steps:
        for step in next_steps:
            lines.append(f"- Next: {step}")

    lines.append("")
    content = "\n".join(lines)

    # Append to existing session file or create new
    if session_file.exists():
        existing = session_file.read_text(encoding="utf-8")
        content = existing + "\n---\n\n" + content

    session_file.write_text(content, encoding="utf-8")
    return session_file


def get_latest_session(wiki_dir: Path) -> Optional[str]:
    """Read the most recent session synthesis for context recovery.

    A new agent session should call this at startup to quickly
    understand what happened recently without reading log.md.
    """
    sessions_dir = wiki_dir / "sessions"
    if not sessions_dir.exists():
        return None

    files = sorted(sessions_dir.glob("*.md"), reverse=True)
    if not files:
        return None

    # Return last 3 sessions (most recent context)
    recent = []
    for f in files[:3]:
        recent.append(f"### {f.stem}\n\n{f.read_text(encoding='utf-8')[:2000]}")

    return "\n\n".join(recent)


def get_session_context_instruction(wiki_dir: Path) -> str:
    """Generate context-recovery instructions for the agent prompt.

    Call this at the start of any LLM prompt to provide recent context.
    """
    latest = get_latest_session(wiki_dir)
    if not latest:
        return ""

    return f"""## Recent Session Context

The following is a summary of recent wiki operations. Use this to understand
what has changed without re-reading the entire wiki.

{latest}

---
"""
