"""Suppression: temporarily silence notifications or alerts for a vault key."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


class SuppressionError(Exception):
    """Raised when a suppression operation fails."""


def _suppression_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_suppression.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_suppressions(vault_path: str) -> dict:
    p = _suppression_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_suppressions(vault_path: str, data: dict) -> None:
    _suppression_path(vault_path).write_text(json.dumps(data, indent=2))


def suppress_key(
    vault_path: str,
    key: str,
    duration_seconds: int,
    reason: str = "",
) -> dict:
    """Suppress alerts for *key* for *duration_seconds* seconds."""
    if duration_seconds <= 0:
        raise SuppressionError("duration_seconds must be a positive integer")
    data = _load_suppressions(vault_path)
    suppressed_at = _now_iso()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
    ).isoformat()
    entry = {
        "suppressed_at": suppressed_at,
        "expires_at": expires_at,
        "duration_seconds": duration_seconds,
        "reason": reason,
    }
    data[key] = entry
    _save_suppressions(vault_path, data)
    return entry


def is_suppressed(vault_path: str, key: str) -> bool:
    """Return True if *key* is currently suppressed."""
    data = _load_suppressions(vault_path)
    if key not in data:
        return False
    expires_at = datetime.fromisoformat(data[key]["expires_at"])
    return datetime.now(timezone.utc) < expires_at


def remove_suppression(vault_path: str, key: str) -> None:
    """Remove any active suppression for *key*."""
    data = _load_suppressions(vault_path)
    data.pop(key, None)
    _save_suppressions(vault_path, data)


def list_suppressions(vault_path: str) -> dict:
    """Return all suppression entries (including expired ones)."""
    return _load_suppressions(vault_path)
