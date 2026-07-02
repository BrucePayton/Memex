#!/usr/bin/env python3
"""Regression tests for dashboard schedule CRUD helpers."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import dashboard.scheduler as scheduler  # noqa: E402
import server  # noqa: E402


class TestScheduleApi(unittest.TestCase):
    def test_upsert_toggle_delete_persist_to_same_settings_file(self):
        with tempfile.TemporaryDirectory() as td:
            settings_file = Path(td) / ".dashboard-settings.json"
            old_settings_file = scheduler.SETTINGS_FILE
            scheduler.SETTINGS_FILE = settings_file
            try:
                created = server.upsert_schedule_api({
                    "name": "Nightly lint",
                    "cron": "0 3 * * *",
                    "steps": ["lint"],
                    "enabled": True,
                })
                self.assertTrue(created["ok"])
                sched_id = created["schedule"]["id"]

                listed = server.list_schedules_api()
                self.assertEqual(len(listed["schedules"]), 1)
                self.assertTrue(listed["schedules"][0]["enabled"])

                toggled = server.toggle_schedule_api(sched_id)
                self.assertTrue(toggled["ok"])
                self.assertFalse(toggled["schedule"]["enabled"])

                persisted = json.loads(settings_file.read_text("utf-8"))
                self.assertEqual(len(persisted["schedules"]), 1)
                self.assertFalse(persisted["schedules"][0]["enabled"])

                deleted = server.delete_schedule_api(sched_id)
                self.assertTrue(deleted["ok"])

                persisted = json.loads(settings_file.read_text("utf-8"))
                self.assertEqual(persisted["schedules"], [])
            finally:
                scheduler.SETTINGS_FILE = old_settings_file

    def test_upsert_normalizes_enabled_bool(self):
        with tempfile.TemporaryDirectory() as td:
            settings_file = Path(td) / ".dashboard-settings.json"
            old_settings_file = scheduler.SETTINGS_FILE
            scheduler.SETTINGS_FILE = settings_file
            try:
                created = server.upsert_schedule_api({
                    "name": "Weekly reflect",
                    "cron": "0 9 * * 1",
                    "steps": ["reflect"],
                    "enabled": 1,
                })
                self.assertTrue(created["ok"])
                self.assertIs(created["schedule"]["enabled"], True)
            finally:
                scheduler.SETTINGS_FILE = old_settings_file


if __name__ == "__main__":
    unittest.main()
