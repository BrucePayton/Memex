"""Unit tests for worktree isolation."""

import pytest
import sys
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.maintenance.worktree import (
    WorktreeManager, run_maintenance_isolated, WorktreeError,
)


class TestWorktreeManager:
    def test_is_git_repo_detection(self):
        """Memex project root should be a git repo."""
        import os
        # Find Memex repo root
        repo_root = Path(__file__).parent.parent.parent
        mgr = WorktreeManager(repo_root)
        assert mgr.is_git_repo

    def test_non_git_dir_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = WorktreeManager(Path(tmp))
            assert not mgr.is_git_repo

    def test_cleanup_stale_worktrees(self):
        import os
        repo_root = Path(__file__).parent.parent.parent
        mgr = WorktreeManager(repo_root)
        # Should not raise
        mgr.cleanup_stale_worktrees()


class TestRunMaintenanceIsolated:
    def test_successful_operation_in_git_repo(self):
        """Run a simple operation in a worktree and verify it commits."""
        import os
        repo_root = Path(__file__).parent.parent.parent

        def simple_op(wt_root: Path) -> bool:
            # Create a test file in wiki/
            wiki = wt_root / "wiki"
            wiki.mkdir(exist_ok=True)
            test_file = wiki / "_worktree_test.md"
            test_file.write_text(
                "---\ntitle: Worktree Test\ntype: concept\n---\nTest content."
            )
            return True

        result = run_maintenance_isolated(repo_root, "test-op", simple_op)
        assert result["ok"]
        assert result["worktree_used"]

        # Cleanup: remove the test file from main repo
        test_file = repo_root / "wiki" / "_worktree_test.md"
        if test_file.exists():
            test_file.unlink()
            subprocess.run(
                ["git", "add", "wiki/_worktree_test.md"],
                cwd=str(repo_root), capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "cleanup: remove worktree test file"],
                cwd=str(repo_root), capture_output=True,
            )

    def test_failed_operation_discarded(self):
        """A failing operation should NOT leave changes in the main repo."""
        import os
        repo_root = Path(__file__).parent.parent.parent

        def failing_op(wt_root: Path) -> bool:
            return False  # Simulate failure

        result = run_maintenance_isolated(repo_root, "failing-op", failing_op)
        assert not result["ok"]
        assert result["worktree_used"]

    def test_exception_discarded(self):
        """An exception should be caught and worktree discarded."""
        import os
        repo_root = Path(__file__).parent.parent.parent

        def crashing_op(wt_root: Path) -> bool:
            raise RuntimeError("Simulated crash")

        result = run_maintenance_isolated(repo_root, "crash-op", crashing_op)
        assert not result["ok"]
        assert "Simulated crash" in result.get("error", "")

    def test_non_git_fallback(self):
        """When not in a git repo, should fall back to in-place execution."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "wiki").mkdir()

            def op(wt_root: Path) -> bool:
                (wt_root / "wiki" / "result.txt").write_text("done")
                return True

            result = run_maintenance_isolated(root, "test", op)
            assert result["ok"]
            assert not result["worktree_used"]  # No git, no worktree


class TestWorktreeError:
    def test_error_message(self):
        e = WorktreeError("test failure")
        assert "test failure" in str(e)
