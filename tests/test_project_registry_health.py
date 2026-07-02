#!/usr/bin/env python3
"""Regression tests for project registry/storage drift handling."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import server  # noqa: E402
import dashboard.project_registry as project_registry  # noqa: E402


class ProjectRegistryHarness(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.base = Path(self.td.name)
        self.projects_dir = self.base / "projects"
        self.templates_dir = self.base / "templates"
        self.registry_file = self.base / "projects.json"
        self.projects_dir.mkdir()
        self.templates_dir.mkdir()
        (self.templates_dir / "CLAUDE.md").write_text("# Wiki\n", encoding="utf-8")

        self.old_registry = project_registry.REGISTRY_FILE
        self.old_projects = project_registry.PROJECTS_DIR
        self.old_templates = project_registry.TEMPLATES_DIR
        project_registry.REGISTRY_FILE = self.registry_file
        project_registry.PROJECTS_DIR = self.projects_dir
        project_registry.TEMPLATES_DIR = self.templates_dir

    def tearDown(self):
        project_registry.REGISTRY_FILE = self.old_registry
        project_registry.PROJECTS_DIR = self.old_projects
        project_registry.TEMPLATES_DIR = self.old_templates
        self.td.cleanup()

    def write_registry(self, *entries, active=None):
        data = {"version": 1, "active": active, "projects": list(entries)}
        self.registry_file.write_text(json.dumps(data), encoding="utf-8")


class TestProjectRegistryHealth(ProjectRegistryHarness):
    def test_registered_project_missing_on_disk_is_reported_and_rejected_in_strict_mode(self):
        self.write_registry(
            {
                "slug": "ghost",
                "title": "Ghost",
                "description": "",
                "created": "2026-07-02",
                "last_used": "2026-07-02",
                "template": "",
            },
            active="ghost",
        )

        proj = project_registry.get_project("ghost")
        self.assertEqual(project_registry.project_health(proj)["status"], "missing_on_disk")
        self.assertEqual(proj.to_dict()["health"]["status"], "missing_on_disk")
        with self.assertRaises(project_registry.ProjectStorageError):
            project_registry.get_project("ghost", require_storage=True)

    def test_create_page_does_not_recreate_missing_registered_project(self):
        self.write_registry(
            {
                "slug": "ghost",
                "title": "Ghost",
                "description": "",
                "created": "2026-07-02",
                "last_used": "2026-07-02",
                "template": "",
            },
            active="ghost",
        )

        with self.assertRaises(project_registry.ProjectStorageError):
            server.create_page("New Page", "concept", project_slug="ghost")
        self.assertFalse((self.projects_dir / "ghost").exists())

    def test_reconcile_reports_missing_registered_projects_and_moves_only_empty_orphans(self):
        self.write_registry(
            {
                "slug": "ghost",
                "title": "Ghost",
                "description": "",
                "created": "2026-07-02",
                "last_used": "2026-07-02",
                "template": "",
            },
            active="ghost",
        )
        empty_orphan = self.projects_dir / "empty-orphan"
        empty_orphan.mkdir()
        (empty_orphan / "wiki").mkdir()
        nonempty_orphan = self.projects_dir / "nonempty-orphan"
        nonempty_orphan.mkdir()
        (nonempty_orphan / "note.md").write_text("keep me", encoding="utf-8")

        dry = project_registry.reconcile_projects(apply=False)
        self.assertEqual(dry["missing_on_disk"][0]["slug"], "ghost")
        orphan_by_slug = {item["slug"]: item for item in dry["orphan_on_disk"]}
        self.assertTrue(orphan_by_slug["empty-orphan"]["empty"])
        self.assertFalse(orphan_by_slug["nonempty-orphan"]["empty"])

        applied = project_registry.reconcile_projects(apply=True)
        self.assertFalse(empty_orphan.exists())
        self.assertTrue(nonempty_orphan.exists())
        self.assertEqual(applied["moved"][0]["slug"], "empty-orphan")
        self.assertEqual(applied["orphan_on_disk"][0]["slug"], "nonempty-orphan")

    def test_create_project_scaffold_is_healthy(self):
        proj = project_registry.create_project(
            slug_hint="demo",
            title="Demo",
            description="",
            template="",
        )
        self.assertEqual(project_registry.project_health(proj)["status"], "ok")
        self.assertEqual(proj.to_dict()["health"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
