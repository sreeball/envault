"""Cooldown periods for vault keys — prevent rapid re-use of secrets."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


class CooldownError(Exception):
    """Raised when a cooldown operation fails."""


def _cooldown_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_cooldown.json"


def _load_cooldowns(vault_path: str) -> dict:
    p = _cooldown_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_cooldowns(vault_path: str, data: dict) -> None:
    _cooldown_path(vault_path).write_text(json.dumps(data, indent=2))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_cooldown(vault_path: str, key: str, seconds: int) -> dict:
    """Register a cooldown period for *key* (in seconds)."""
    if seconds <= 0:
        raise CooldownError("seconds must be a positive integer")
    data = _load_cooldowns(vault_path)
    now = datetime.now(timezone.utc)
    entry = {
        "key": key,
        "seconds": seconds,
        "started_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=seconds)).isoformat(),
    }
    data[key] = entry
    _save_cooldowns(vault_path, data)
    return entry


def is_cooling_down(vault_path: str, key: str) -> bool:
    """Return True if *key* is currently within its cooldown window."""
    data = _load_cooldowns(vault_path)
    entry = data.get(key)
    if not entry:
        return False
    expires_at = datetime.fromisoformat(entry["expires_at"])
    return datetime.now(timezone.utc) < expires_at


def remove_cooldown(vault_path: str, key: str) -> bool:
    """Remove the cooldown for *key*. Returns True if it existed."""
    data = _load_cooldowns(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_cooldowns(vault_path, data)
    return True


def list_cooldowns(vault_path: str) -> list[dict]:
    """Return all cooldown entries, annotated with an 'active' flag."""
    data = _load_cooldowns(vault_path)
    now = datetime.now(timezone.utc)
    result = []
    for entry in data.values():
        expires_at = datetime.fromisoformat(entry["expires_at"])
        result.append({**entry, "active": now < expires_at})
    return result
