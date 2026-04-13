"""Retention policy management for vault secrets."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional


class RetentionError(Exception):
    """Raised when a retention operation fails."""


def _retention_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_retention.json"


def _load_retention(vault_path: str) -> dict:
    p = _retention_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_retention(vault_path: str, data: dict) -> None:
    _retention_path(vault_path).write_text(json.dumps(data, indent=2))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_retention(vault_path: str, key: str, days: int, note: str = "") -> dict:
    """Set a retention policy for *key* (max age in days)."""
    if days < 1:
        raise RetentionError("days must be >= 1")
    data = _load_retention(vault_path)
    entry = {
        "key": key,
        "days": days,
        "note": note,
        "set_at": _now_iso(),
        "purge_after": (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(),
    }
    data[key] = entry
    _save_retention(vault_path, data)
    return entry


def get_retention(vault_path: str, key: str) -> Optional[dict]:
    """Return the retention policy for *key*, or None if not set."""
    return _load_retention(vault_path).get(key)


def remove_retention(vault_path: str, key: str) -> bool:
    """Remove the retention policy for *key*. Returns True if removed."""
    data = _load_retention(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_retention(vault_path, data)
    return True


def list_retention(vault_path: str) -> list[dict]:
    """Return all retention policies sorted by purge_after."""
    data = _load_retention(vault_path)
    return sorted(data.values(), key=lambda e: e["purge_after"])


def list_due_for_purge(vault_path: str) -> list[dict]:
    """Return policies whose purge_after timestamp has passed."""
    now = datetime.now(timezone.utc).isoformat()
    return [e for e in list_retention(vault_path) if e["purge_after"] <= now]
