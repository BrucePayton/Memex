#!/usr/bin/env python3
"""Regression tests for dashboard CLI-only settings and project scaffolding."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import server  # noqa: E402
import dashboard.project_registry as project_registry  # noqa: E402


class TestDashboardSettings(unittest.TestCase):
    def test_merge_dashboard_settings_persists_cli_fields_only(self):
        with tempfile.TemporaryDirectory() as td:
            settings_file = Path(td) / ".dashboard-settings.json"
            old_file = server.SETTINGS_FILE
            old_settings = dict(server.SETTINGS)
            server.SETTINGS_FILE = settings_file
            server.SETTINGS.clear()
            server.SETTINGS.update({
                "cli_type": "claude",
                "claude_cli_binary": "claude",
                "claude_cli_extra_args": [],
                "cli_path_extra": "",
            })
            try:
                out = server.merge_dashboard_settings({
                    "cli_type": "claw",
                    "claude_cli_binary": "/tmp/claw",
                    "claude_cli_extra_args": ["--dangerously-skip-permissions"],
                    "cli_path_extra": "/opt/homebrew/bin",
                })
                self.assertTrue(out["ok"])
                saved = json.loads(settings_file.read_text("utf-8"))
                self.assertEqual(saved["cli_type"], "claw")
                self.assertEqual(saved["claude_cli_binary"], "/tmp/claw")
                self.assertEqual(saved["claude_cli_extra_args"], ["--dangerously-skip-permissions"])
                self.assertEqual(saved["cli_path_extra"], "/opt/homebrew/bin")
                self.assertNotIn("ai_provider", saved)
                self.assertNotIn("openai_model", saved)
            finally:
                server.SETTINGS_FILE = old_file
                server.SETTINGS.clear()
                server.SETTINGS.update(old_settings)


class TestProjectScaffolding(unittest.TestCase):
    def test_create_project_does_not_persist_model_settings(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            templates_dir = base / "templates"
            projects_dir = base / "projects"
            templates_dir.mkdir()
            projects_dir.mkdir()
            (templates_dir / "CLAUDE.md").write_text("# Wiki\n", encoding="utf-8")

            old_registry = project_registry.REGISTRY_FILE
            old_projects = project_registry.PROJECTS_DIR
            old_templates = project_registry.TEMPLATES_DIR
            project_registry.REGISTRY_FILE = base / "projects.json"
            project_registry.PROJECTS_DIR = projects_dir
            project_registry.TEMPLATES_DIR = templates_dir
            try:
                proj = project_registry.create_project(
                    slug_hint="demo",
                    title="Demo Project",
                    description="",
                    template="",
                )
                settings = json.loads((proj.root / ".settings.json").read_text("utf-8"))
                registry = json.loads(project_registry.REGISTRY_FILE.read_text("utf-8"))
                self.assertEqual(settings, {})
                self.assertNotIn("model", registry["projects"][0])
            finally:
                project_registry.REGISTRY_FILE = old_registry
                project_registry.PROJECTS_DIR = old_projects
                project_registry.TEMPLATES_DIR = old_templates


if __name__ == "__main__":
    unittest.main()
