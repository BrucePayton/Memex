"""
Git worktree isolation for safe automatic wiki maintenance.

When automatic maintenance (lint_fix, cascade refresh, schema evolution)
needs to write wiki files, it operates in a temporary Git worktree.
Successful changes are committed and merged; failed operations are
discarded without touching the main working tree.

Inspired by RightMemory's isolated worktree write pattern.
"""

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional


class WorktreeError(Exception):
    """Worktree operation failed."""


class WorktreeManager:
    """Manage isolated Git worktrees for safe automatic maintenance."""

    WORKTREE_PREFIX = "memex-auto-"

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self._active_worktree: Optional[Path] = None
        self._branch_name: Optional[str] = None

    @property
    def is_git_repo(self) -> bool:
        """Check if repo_root is inside a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True, text=True, timeout=5,
                cwd=str(self.repo_root),
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _run_git(self, *args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a git command, raising WorktreeError on failure."""
        cmd = ["git"] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30,
            cwd=str(cwd or self.repo_root),
        )
        if result.returncode != 0:
            raise WorktreeError(
                f"git {' '.join(args)} failed: {result.stderr.strip()}"
            )
        return result

    def _current_branch(self) -> str:
        """Get current branch name."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(self.repo_root),
        )
        return result.stdout.strip()

    @contextmanager
    def isolated_worktree(self, operation_name: str = "maintenance"):
        """Context manager for isolated worktree operations.

        Usage:
            with worktree_mgr.isolated_worktree("lint_fix") as wt_path:
                # Run maintenance in wt_path (a copy of the repo)
                result = do_maintenance(wt_path)
                if not result.success:
                    raise WorktreeError("maintenance failed")

        On successful exit: changes are committed and merged.
        On exception: worktree is discarded.
        """
        if not self.is_git_repo:
            # Fallback: run in-place (no git available)
            yield self.repo_root
            return

        unique_id = uuid.uuid4().hex[:8]
        self._branch_name = f"{self.WORKTREE_PREFIX}{operation_name}-{unique_id}"
        wt_path = self.repo_root.parent / f".worktrees/{self._branch_name}"

        try:
            # Ensure we start from a clean base (stash any local changes)
            base_branch = self._current_branch()

            # Create worktree on a new branch from HEAD
            self._run_git("worktree", "add", "-b", self._branch_name,
                         str(wt_path), "HEAD")

            self._active_worktree = wt_path

            # Yield the isolated worktree path for the caller to operate on
            yield wt_path

            # Success: commit and merge back
            self._merge_back(base_branch)

        except Exception:
            # Failure: discard worktree
            self._discard()
            raise
        finally:
            self._active_worktree = None
            self._branch_name = None

    def _merge_back(self, target_branch: str):
        """Commit worktree changes and merge back to target branch."""
        if not self._active_worktree or not self._active_worktree.exists():
            return

        wt = self._active_worktree

        # Check if there are actual changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            cwd=str(wt),
        )

        if status.stdout.strip():
            # Stage all wiki changes
            self._run_git("add", "wiki/", cwd=wt)

            # Commit with conventional commit message
            op_name = self._branch_name.replace(self.WORKTREE_PREFIX, "") if self._branch_name else "maintenance"
            self._run_git(
                "commit", "-m",
                f"auto({op_name}): automated wiki maintenance [worktree]",
                cwd=wt,
            )

            # Switch back to target branch and merge
            self._run_git("checkout", target_branch, cwd=str(self.repo_root))
            self._run_git(
                "merge", self._branch_name,
                "--strategy", "ort",
                "-m", f"merge({op_name}): apply automated maintenance",
                cwd=str(self.repo_root),
            )

    def _discard(self):
        """Remove the worktree and its branch, discarding all changes."""
        if self._active_worktree and self._active_worktree.exists():
            try:
                self._run_git(
                    "worktree", "remove", "--force",
                    str(self._active_worktree),
                )
            except WorktreeError:
                # Last resort: manual cleanup
                shutil.rmtree(str(self._active_worktree), ignore_errors=True)

        # Prune the worktree branch
        if self._branch_name:
            try:
                self._run_git("worktree", "prune")
            except WorktreeError:
                pass

    def cleanup_stale_worktrees(self):
        """Remove any stale worktrees from previous failed operations."""
        worktrees_dir = self.repo_root.parent / ".worktrees"
        if not worktrees_dir.exists():
            return

        try:
            self._run_git("worktree", "prune")
        except WorktreeError:
            pass

        # Remove any leftover directories
        for d in worktrees_dir.iterdir():
            if d.is_dir() and d.name.startswith(self.WORKTREE_PREFIX):
                shutil.rmtree(str(d), ignore_errors=True)


def run_maintenance_isolated(
    repo_root: Path,
    operation_name: str,
    operation: Callable[[Path], bool],
) -> dict:
    """Run a maintenance operation in an isolated worktree.

    Args:
        repo_root: root of the git repository
        operation_name: human-readable name for the commit message
        operation: callable that takes a Path (worktree root) and returns
                   True on success, False on failure

    Returns:
        {ok, worktree_used, operation, error (if any)}
    """
    mgr = WorktreeManager(repo_root)

    if not mgr.is_git_repo:
        # Run in-place without isolation
        try:
            success = operation(repo_root)
            return {"ok": success, "worktree_used": False, "operation": operation_name}
        except Exception as e:
            return {"ok": False, "worktree_used": False, "operation": operation_name, "error": str(e)}

    try:
        with mgr.isolated_worktree(operation_name) as wt_path:
            success = operation(wt_path)
            if not success:
                raise WorktreeError(f"Operation '{operation_name}' returned False")
        return {"ok": True, "worktree_used": True, "operation": operation_name}
    except Exception as e:
        return {"ok": False, "worktree_used": True, "operation": operation_name, "error": str(e)}
