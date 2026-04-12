"""Reminders: schedule reminders to rotate or review secrets."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReminderError(Exception):
    pass


def _reminders_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_reminders.json"


def _load_reminders(vault_path: str) -> Dict[str, Any]:
    p = _reminders_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_reminders(vault_path: str, data: Dict[str, Any]) -> None:
    _reminders_path(vault_path).write_text(json.dumps(data, indent=2))


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def add_reminder(
    vault_path: str,
    key: str,
    message: str,
    days: int,
) -> Dict[str, Any]:
    """Schedule a reminder for *key* to fire after *days* days."""
    if days <= 0:
        raise ReminderError("days must be a positive integer")
    if not key:
        raise ReminderError("key must not be empty")

    data = _load_reminders(vault_path)
    due = (datetime.utcnow() + timedelta(days=days)).isoformat(timespec="seconds")
    entry: Dict[str, Any] = {
        "key": key,
        "message": message,
        "due_at": due,
        "created_at": _now_iso(),
        "fired": False,
    }
    data[key] = entry
    _save_reminders(vault_path, data)
    return entry


def remove_reminder(vault_path: str, key: str) -> None:
    data = _load_reminders(vault_path)
    if key not in data:
        raise ReminderError(f"No reminder for key '{key}'")
    del data[key]
    _save_reminders(vault_path, data)


def list_reminders(vault_path: str) -> List[Dict[str, Any]]:
    return list(_load_reminders(vault_path).values())


def due_reminders(vault_path: str) -> List[Dict[str, Any]]:
    """Return reminders whose due_at is <= now and have not been fired."""
    now = datetime.utcnow().isoformat(timespec="seconds")
    return [
        r for r in list_reminders(vault_path)
        if not r["fired"] and r["due_at"] <= now
    ]


def mark_fired(vault_path: str, key: str) -> Dict[str, Any]:
    data = _load_reminders(vault_path)
    if key not in data:
        raise ReminderError(f"No reminder for key '{key}'")
    data[key]["fired"] = True
    _save_reminders(vault_path, data)
    return data[key]
