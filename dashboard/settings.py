"""
Thread-safe + process-safe configuration manager for Memex.

Protects .dashboard-settings.json from concurrent writes using:
- Memory layer: threading.RLock for per-process thread safety
- File layer: fcntl.flock (LOCK_EX) for cross-process safety
- Atomic writes: tmp file + fsync + os.replace

Usage:
    settings = SettingsManager("/path/to/.dashboard-settings.json")
    model = settings.get("model", "opus-4-7")
    settings.set("model", "sonnet-4-6")
"""

import json
import fcntl
import os
import threading
from typing import Any


class SettingsManager:
    """Thread-safe + process-safe singleton configuration manager."""

    _instance = None
    _class_lock = threading.RLock()

    def __new__(cls, filepath: str = None):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, filepath: str = None):
        if hasattr(self, '_initialized'):
            return
        if filepath is None:
            raise ValueError("filepath required for first SettingsManager initialization")
        self._filepath = filepath
        self._mem_lock = threading.RLock()
        self._data: dict = {}
        self._initialized = True
        if os.path.exists(filepath):
            self._load()
        else:
            self._data = {}

    # ─── Public API ───

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe read."""
        with self._mem_lock:
            return self._data.get(key, default)

    def get_all(self) -> dict:
        """Thread-safe full dict copy."""
        with self._mem_lock:
            return dict(self._data)

    def set(self, key: str, value: Any):
        """Thread-safe write with atomic file persistence."""
        with self._mem_lock:
            self._data[key] = value
        self._save()

    def update(self, updates: dict):
        """Thread-safe batch update with atomic file persistence."""
        with self._mem_lock:
            self._data.update(updates)
        self._save()

    def delete(self, key: str):
        """Thread-safe delete with atomic file persistence."""
        with self._mem_lock:
            self._data.pop(key, None)
        self._save()

    # ─── File I/O with locking ───

    def _load(self):
        """Read settings file with shared lock."""
        with self._mem_lock:
            try:
                with open(self._filepath, 'r') as f:
                    fcntl.flock(f, fcntl.LOCK_SH)
                    self._data = json.load(f)
                    fcntl.flock(f, fcntl.LOCK_UN)
            except (FileNotFoundError, json.JSONDecodeError):
                self._data = {}

    def _save(self):
        """Write settings file with exclusive lock + atomic replace.

        Blocks until exclusive lock is acquired (no timeout — ensures
        data is never lost, caller must ensure deadlock-free design).
        """
        tmp = self._filepath + '.tmp'
        with self._mem_lock:
            data_copy = dict(self._data)

        try:
            with open(tmp, 'w') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                json.dump(data_copy, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f, fcntl.LOCK_UN)
            os.replace(tmp, self._filepath)
        except Exception:
            # Clean up tmp on failure
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # ─── Convenience ───

    def __contains__(self, key: str) -> bool:
        with self._mem_lock:
            return key in self._data

    def __repr__(self) -> str:
        with self._mem_lock:
            keys = list(self._data.keys())
        return f"SettingsManager({len(keys)} keys)"
