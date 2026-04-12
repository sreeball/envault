"""TTL (time-to-live) support for vault secrets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _ttl_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".ttl.json")


def set_ttl(vault_path: Path, key: str, seconds: int) -> dict:
    """Set a TTL for *key* in the vault at *vault_path*.

    Returns the stored TTL entry.
    """
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")

    path = _ttl_path(vault_path)
    data = _load(path)

    expires_at = _now().timestamp() + seconds
    entry = {"expires_at": expires_at}
    data[key] = entry
    _save(path, data)
    return entry


def get_ttl(vault_path: Path, key: str) -> Optional[dict]:
    """Return the TTL entry for *key*, or *None* if no TTL is set."""
    data = _load(_ttl_path(vault_path))
    return data.get(key)


def is_expired(vault_path: Path, key: str) -> bool:
    """Return True if *key* has an expired TTL."""
    entry = get_ttl(vault_path, key)
    if entry is None:
        return False
    return _now().timestamp() > entry["expires_at"]


def remaining_seconds(vault_path: Path, key: str) -> Optional[float]:
    """Return the number of seconds until *key* expires, or *None* if no TTL is set.

    Returns a negative value if the TTL has already expired.
    """
    entry = get_ttl(vault_path, key)
    if entry is None:
        return None
    return entry["expires_at"] - _now().timestamp()


def clear_ttl(vault_path: Path, key: str) -> bool:
    """Remove the TTL entry for *key*. Returns True if an entry existed."""
    path = _ttl_path(vault_path)
    data = _load(path)
    existed = key in data
    if existed:
        del data[key]
        _save(path, data)
    return existed


def purge_expired(vault_path: Path) -> list[str]:
    """Remove all expired TTL entries and return their keys."""
    path = _ttl_path(vault_path)
    data = _load(path)
    now = _now().timestamp()
    expired = [k for k, v in data.items() if now > v["expires_at"]]
    for k in expired:
        del data[k]
    if expired:
        _save(path, data)
    return expired


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))
