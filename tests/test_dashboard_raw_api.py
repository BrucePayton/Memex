#!/usr/bin/env python3
"""Regression tests for dashboard raw API path containment."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import server  # noqa: E402


class TestRawPathSafety(unittest.TestCase):
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
