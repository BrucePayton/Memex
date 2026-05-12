"""Background wiki maintenance scheduler.

Uses stdlib threading.Timer (no pip dependencies). Checks schedules every
60 seconds and fires matching cron expressions in daemon threads.

Results are appended to wiki/log.md and persisted in .dashboard-settings.json.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

_OPS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = _OPS_ROOT.parent
SETTINGS_FILE = PROJECT_ROOT / ".dashboard-settings.json"

# Lock for settings read/write (shared with dashboard handler)
_settings_lock = threading.Lock()


def _parse_cron_field(field: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single cron field into a set of matching values.

    Supports: * (any), N (exact), N-M (range), */N (step), N,M (list), N-M/S (range+step)
    """
    values: set[int] = set()
    for part in field.split(","):
        part = part.strip()
        if part == "*":
            values.update(range(min_val, max_val + 1))
        elif part.startswith("*/"):
            step = int(part[2:])
            values.update(range(min_val, max_val + 1, step))
        elif "-" in part:
            if "/" in part:
                range_part, step_str = part.split("/", 1)
                start, end = map(int, range_part.split("-", 1))
                step = int(step_str)
            else:
                start, end = map(int, part.split("-", 1))
                step = 1
            values.update(range(start, end + 1, step))
        else:
            values.add(int(part))
    return {v for v in values if min_val <= v <= max_val}


def cron_matches(cron_expr: str, dt: datetime | None = None) -> bool:
    """Check if a 5-field cron expression matches the given datetime.

    Fields: minute hour day-of-month month day-of-week
    """
    if dt is None:
        dt = datetime.now()
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False
    try:
        minutes = _parse_cron_field(parts[0], 0, 59)
        hours = _parse_cron_field(parts[1], 0, 23)
        doms = _parse_cron_field(parts[2], 1, 31)
        months = _parse_cron_field(parts[3], 1, 12)
        dows = _parse_cron_field(parts[4], 0, 6)  # 0=Monday in Python
    except (ValueError, IndexError):
        return False

    # Python weekday: Monday=0..Sunday=6; cron: Sunday=0..Saturday=6
    # Convert Python weekday to cron dow
    cron_dow = (dt.weekday() + 1) % 7

    return (
        dt.minute in minutes
        and dt.hour in hours
        and dt.day in doms
        and dt.month in months
        and cron_dow in dows
    )


def _load_schedules() -> tuple[list[dict], Path]:
    """Load schedules from settings file. Returns (list, settings_file_path)."""
    with _settings_lock:
        if not SETTINGS_FILE.exists():
            return [], SETTINGS_FILE
        try:
            data = json.loads(SETTINGS_FILE.read_text("utf-8"))
            return data.get("schedules", []), SETTINGS_FILE
        except Exception:
            return [], SETTINGS_FILE


def _save_schedules(schedules: list[dict]):
    """Save schedules to settings file."""
    with _settings_lock:
        data = {}
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text("utf-8"))
            except Exception:
                pass
        data["schedules"] = schedules
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_log(wiki_dir: Path, message: str):
    """Append an entry to wiki/log.md."""
    log_file = wiki_dir / "log.md"
    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n## [{today}] maintenance | Scheduled: {message}\nAuto-executed by scheduler.\n"

    with _settings_lock:
        if log_file.exists():
            text = log_file.read_text("utf-8")
        else:
            text = f"---\ntitle: Wiki Log\ntype: overview\nstatus: active\n---\n"
        text += entry
        log_file.write_text(text, encoding="utf-8")


def _run_schedule(sched: dict):
    """Execute a single schedule in a background thread."""
    try:
        # Import wiki_ops here to avoid circular imports
        import sys
        dashboard_dir = Path(__file__).resolve().parent
        if str(dashboard_dir) not in sys.path:
            sys.path.insert(0, str(dashboard_dir))
        import wiki_ops  # noqa: E402

        project = sched.get("project", "")
        steps = sched.get("steps", ["lint"])
        include_ingest = sched.get("include_ingest", False)
        reflect_window = sched.get("reflect_window", "last-10-ingests")

        result = wiki_ops.run_loop(
            project=project,
            steps=steps,
            include_ingest=include_ingest,
            reflect_window=reflect_window,
        )

        # Update last_run / last_status
        schedules = _load_schedules()[0]
        for s in schedules:
            if s.get("id") == sched["id"]:
                s["last_run"] = datetime.now().isoformat()
                s["last_status"] = "ok" if result.get("ok") else "failed"
                break
        _save_schedules(schedules)

        # Log to wiki/log.md
        import project_registry  # noqa: E402
        proj = project_registry.get_project(project or None)
        log_msg = f"{sched.get('name', sched['id'])} — {'OK' if result.get('ok') else 'FAILED'} (took {result.get('total_duration_sec', 0):.0f}s)"
        _append_log(proj.wiki_dir, log_msg)

    except Exception as e:
        # Log failure
        try:
            import project_registry  # noqa: E402
            proj = project_registry.get_project(sched.get("project", "") or None)
            _append_log(proj.wiki_dir, f"{sched.get('name', sched['id'])} — ERROR: {e}")
        except Exception:
            pass

        # Update status
        schedules = _load_schedules()[0]
        for s in schedules:
            if s.get("id") == sched["id"]:
                s["last_run"] = datetime.now().isoformat()
                s["last_status"] = f"error: {e}"
                break
        _save_schedules(schedules)


class WikiScheduler:
    """Background scheduler for wiki maintenance tasks.

    Checks all enabled schedules every `interval_sec` seconds and fires
    any whose cron expression matches the current minute.
    """

    def __init__(self, settings_file: Path | None = None, interval_sec: int = 60):
        if settings_file:
            global SETTINGS_FILE
            SETTINGS_FILE = settings_file
        self._interval = interval_sec
        self._running = False
        self._thread: threading.Thread | None = None
        self._fired_minutes: set[tuple[str, int, int, int, int]] = set()  # dedup

    def start(self):
        """Start the scheduler loop in a background daemon thread."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="wiki-scheduler")
        self._thread.start()

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                self._tick()
            except Exception:
                pass
            # Sleep in small increments to allow fast shutdown
            for _ in range(self._interval):
                if not self._running:
                    return
                time.sleep(1)

    def _tick(self):
        """Check and fire schedules that match the current minute."""
        now = datetime.now()
        current_key = (
            now.strftime("%Y-%m-%d"),
            now.hour,
            now.minute,
            now.day,
            now.month,
        )

        # Skip if already fired this minute
        if current_key in self._fired_minutes:
            return

        # Clean old fired keys (keep last hour)
        self._fired_minutes = {
            k for k in self._fired_minutes
            if (
                k[0] == now.strftime("%Y-%m-%d")
                or (datetime.now().minute - k[2]) < 60
            )
        }

        schedules = _load_schedules()[0]
        fired_any = False

        for sched in schedules:
            if not sched.get("enabled", False):
                continue
            cron = sched.get("cron", "").strip()
            if not cron:
                continue
            if cron_matches(cron, now):
                fired_any = True
                threading.Thread(
                    target=_run_schedule, args=(sched,), daemon=True,
                    name=f"schedule-{sched.get('id', 'unknown')}",
                ).start()

        if fired_any:
            self._fired_minutes.add(current_key)
