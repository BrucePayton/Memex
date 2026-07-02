#!/usr/bin/env python3
"""Regression tests for dashboard raw API path containment."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import server  # noqa: E402
import dashboard.project_registry as project_registry  # noqa: E402


class TestRawPathSafety(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.old_registry = project_registry.REGISTRY_FILE
        project_registry.REGISTRY_FILE = Path(self.td.name) / "missing-projects.json"

    def tearDown(self):
        project_registry.REGISTRY_FILE = self.old_registry
        self.td.cleanup()

    def test_traversal_blocked(self):
        out = server.api_raw_read("../../etc/passwd", None)
        self.assertFalse(out["ok"])

    def test_absolute_blocked(self):
        out = server.api_raw_read("/etc/passwd", None)
        self.assertFalse(out["ok"])

    def test_list_ok_shape(self):
        out = server.api_raw_list(None)
        self.assertTrue(out.get("ok"))
        self.assertIn("items", out)
        self.assertIsInstance(out["items"], list)


if __name__ == "__main__":
    unittest.main()
