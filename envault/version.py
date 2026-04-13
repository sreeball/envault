"""Version tracking for vault files and secrets."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class VersionError(Exception):
    """Raised when a version operation fails."""


def _versions_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_versions.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_versions(vault_path: str) -> dict:
    path = _versions_path(vault_path)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_versions(vault_path: str, data: dict) -> None:
    path = _versions_path(vault_path)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def record_version(vault_path: str, key: str, value: str, actor: str = "user") -> dict:
    """Record a new version entry for *key* with the given plaintext *value*."""
    data = _load_versions(vault_path)
    entries = data.get(key, [])
    version_number = len(entries) + 1
    entry: dict[str, Any] = {
        "version": version_number,
        "value": value,
        "actor": actor,
        "recorded_at": _now_iso(),
    }
    entries.append(entry)
    data[key] = entries
    _save_versions(vault_path, data)
    return entry


def get_versions(vault_path: str, key: str) -> list[dict]:
    """Return all recorded versions for *key*, oldest first."""
    data = _load_versions(vault_path)
    return data.get(key, [])


def rollback(vault_path: str, key: str, version: int) -> dict:
    """Return the version entry for *key* at the given 1-based *version* number."""
    entries = get_versions(vault_path, key)
    if not entries:
        raise VersionError(f"No version history for key '{key}'")
    if version < 1 or version > len(entries):
        raise VersionError(
            f"Version {version} out of range (1–{len(entries)}) for key '{key}'"
        )
    return entries[version - 1]


def purge_versions(vault_path: str, key: str) -> int:
    """Delete all version history for *key*. Returns number of entries removed."""
    data = _load_versions(vault_path)
    removed = len(data.pop(key, []))
    _save_versions(vault_path, data)
    return removed
