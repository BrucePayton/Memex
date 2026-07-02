"""Unit tests for cascade page updater."""

import pytest
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.maintenance.cascade import (
    CascadeUpdater, detect_changed_pages, STALE_THRESHOLD_DAYS,
)


class TestCascadeUpdater:
    def test_no_stale_pages_when_all_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            today = datetime.now().strftime("%Y-%m-%d")
            (wiki / "a.md").write_text(
                f"---\ntitle: A\ntype: concept\nlast_updated: {today}\n---\nSee [[b]]"
            )
            (wiki / "b.md").write_text(
                f"---\ntitle: B\ntype: entity\nlast_updated: {today}\n---\nContent"
            )
            updater = CascadeUpdater(wiki)
            stale = updater.cascade_check(["a.md"])
            assert len(stale) == 0

    def test_stale_page_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            today = datetime.now().strftime("%Y-%m-%d")
            old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            (wiki / "a.md").write_text(
                f"---\ntitle: A\ntype: concept\nlast_updated: {today}\n---\nSee [[b]]"
            )
            (wiki / "b.md").write_text(
                f"---\ntitle: B\ntype: entity\nlast_updated: {old_date}\n---\nContent"
            )
            updater = CascadeUpdater(wiki)
            stale = updater.cascade_check(["a.md"])
            assert len(stale) == 1
            assert stale[0]["path"] == "b.md"
            assert stale[0]["days_stale"] >= 60

    def test_multiple_stale_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            today = datetime.now().strftime("%Y-%m-%d")
            old_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            (wiki / "hub.md").write_text(
                f"---\ntitle: Hub\ntype: concept\nlast_updated: {today}\n---\nSee [[a]] and [[b]]"
            )
            (wiki / "a.md").write_text(
                f"---\ntitle: A\ntype: entity\nlast_updated: {old_date}\n---\nContent"
            )
            (wiki / "b.md").write_text(
                f"---\ntitle: B\ntype: entity\nlast_updated: {old_date}\n---\nContent"
            )
            updater = CascadeUpdater(wiki)
            stale = updater.cascade_check(["hub.md"])
            assert len(stale) == 2

    def test_custom_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            today = datetime.now().strftime("%Y-%m-%d")
            week_old = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            (wiki / "a.md").write_text(
                f"---\ntitle: A\ntype: concept\nlast_updated: {today}\n---\nSee [[b]]"
            )
            (wiki / "b.md").write_text(
                f"---\ntitle: B\ntype: entity\nlast_updated: {week_old}\n---\nContent"
            )
            # With threshold=5 days, 7-day-old page should be stale
            updater = CascadeUpdater(wiki, threshold_days=5)
            stale = updater.cascade_check(["a.md"])
            assert len(stale) == 1

    def test_stale_report_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            today = datetime.now().strftime("%Y-%m-%d")
            old_date = (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d")
            (wiki / "a.md").write_text(
                f"---\ntitle: Alpha\ntype: concept\nlast_updated: {today}\n---\nSee [[beta]]"
            )
            (wiki / "beta.md").write_text(
                f"---\ntitle: Beta\ntype: entity\nlast_updated: {old_date}\n---\nContent"
            )
            updater = CascadeUpdater(wiki)
            report = updater.get_stale_report(["a.md"])
            assert "Cascade Check" in report
            assert "Beta" in report
            assert "45 days ago" in report

    def test_missing_link_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            today = datetime.now().strftime("%Y-%m-%d")
            (wiki / "a.md").write_text(
                f"---\ntitle: A\ntype: concept\nlast_updated: {today}\n---\nSee [[nonexistent]]"
            )
            updater = CascadeUpdater(wiki)
            stale = updater.cascade_check(["a.md"])
            assert len(stale) == 0  # missing target, not stale


class TestDetectChangedPages:
    def test_new_page_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            (wiki / "old.md").write_text("---\ntitle: Old\ntype: concept\n---\nContent")
            snapshot = {}
            for md in wiki.rglob("*.md"):
                snapshot[str(md.relative_to(wiki))] = md.stat().st_mtime

            # Add new page
            (wiki / "new.md").write_text("---\ntitle: New\ntype: concept\n---\nContent")
            changed = detect_changed_pages(wiki, snapshot)
            assert "new.md" in changed
            assert "old.md" not in changed
