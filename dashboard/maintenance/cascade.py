"""
Cascade page updater for Memex.

When a page is ingested or updated, automatically detect connected pages
that have gone stale (>30 days since last update) and trigger lightweight
refreshes. Inspired by llm-wiki-newsroom's cascading update mechanism.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..models import parse_fm, extract_links, WIKILINK_RE


STALE_THRESHOLD_DAYS = 30
DATE_FMT = "%Y-%m-%d"


class CascadeUpdater:
    """Detect stale connected pages and prepare refresh candidates.

    After an ingest/update, call cascade_check() to find pages that:
    1. Are linked FROM the new/updated pages (outgoing wikilinks)
    2. Have last_updated > STALE_THRESHOLD_DAYS ago

    These stale pages may contain outdated information that should be
    refreshed now that new source material has been ingested.
    """

    def __init__(self, wiki_dir: Path, threshold_days: int = STALE_THRESHOLD_DAYS):
        self.wiki_dir = wiki_dir
        self.threshold_days = threshold_days

    def cascade_check(self, changed_pages: list[str]) -> list[dict]:
        """Check outgoing links from changed pages for stale targets.

        Args:
            changed_pages: list of wiki-relative paths (e.g., ['concepts/ai.md'])

        Returns:
            [{path, title, last_updated, days_stale, linked_from}]
            sorted by days_stale descending (most stale first)
        """
        stale_candidates: dict[str, dict] = {}  # path -> info

        for page_path in changed_pages:
            md = self.wiki_dir / page_path
            if not md.exists():
                continue

            text = md.read_text(encoding="utf-8")
            meta, body = parse_fm(text)
            links = extract_links(body)

            for link_target in links:
                if link_target in stale_candidates:
                    continue  # already found via another page

                target_md = self.wiki_dir / link_target
                if not target_md.exists():
                    continue

                target_text = target_md.read_text(encoding="utf-8")
                target_meta, _ = parse_fm(target_text)
                last_updated = target_meta.get("last_updated", "")

                if not last_updated:
                    continue

                try:
                    updated_dt = datetime.strptime(last_updated, DATE_FMT)
                except ValueError:
                    continue

                days_stale = (datetime.now() - updated_dt).days
                if days_stale >= self.threshold_days:
                    stale_candidates[link_target] = {
                        "path": link_target,
                        "title": target_meta.get("title", link_target),
                        "last_updated": last_updated,
                        "days_stale": days_stale,
                        "linked_from": page_path,
                    }

        return sorted(
            stale_candidates.values(),
            key=lambda x: x["days_stale"],
            reverse=True,
        )

    def get_stale_report(self, changed_pages: list[str]) -> str:
        """Generate a human-readable stale page report for the ingest prompt."""
        stale = self.cascade_check(changed_pages)
        if not stale:
            return ""

        lines = [
            "\n## Cascade Check: Stale Connected Pages\n",
            f"The following {len(stale)} pages are linked from the updated pages "
            f"and have not been updated in ≥{self.threshold_days} days. "
            f"Consider reviewing them for consistency with the new information.\n",
        ]
        for s in stale[:10]:  # Top 10
            lines.append(
                f"- **{s['title']}** (`{s['path']}`) — "
                f"last updated {s['last_updated']} ({s['days_stale']} days ago), "
                f"linked from `{s['linked_from']}`"
            )
        if len(stale) > 10:
            lines.append(f"\n... and {len(stale) - 10} more stale pages.")

        return "\n".join(lines)


def detect_changed_pages(
    wiki_dir: Path,
    before_snapshot: dict[str, float],
) -> list[str]:
    """Compare current wiki state against a previous mtime snapshot.

    Returns list of page paths that were added or modified.
    Useful for determining cascade scope after a batch of ingests.
    """
    changed = []
    if not wiki_dir.exists():
        return changed

    for md in wiki_dir.rglob("*.md"):
        rel = str(md.relative_to(wiki_dir))
        current_mtime = md.stat().st_mtime
        if rel not in before_snapshot or before_snapshot[rel] != current_mtime:
            changed.append(rel)

    return changed
