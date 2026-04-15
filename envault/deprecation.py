"""Mark vault keys as deprecated with optional replacement hints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class DeprecationError(Exception):
    pass


def _deprecations_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault" / "deprecations.json"


def _load_deprecations(vault_path: str) -> dict:
    p = _deprecations_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_deprecations(vault_path: str, data: dict) -> None:
    p = _deprecations_path(vault_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def deprecate_key(
    vault_path: str,
    key: str,
    reason: str,
    replacement: Optional[str] = None,
) -> dict:
    """Mark *key* as deprecated. Returns the stored entry."""
    if not key:
        raise DeprecationError("key must not be empty")
    if not reason:
        raise DeprecationError("reason must not be empty")

    data = _load_deprecations(vault_path)
    entry = {"reason": reason, "replacement": replacement}
    data[key] = entry
    _save_deprecations(vault_path, data)
    return entry


def undeprecate_key(vault_path: str, key: str) -> None:
    """Remove deprecation mark from *key*."""
    data = _load_deprecations(vault_path)
    if key not in data:
        raise DeprecationError(f"key '{key}' is not deprecated")
    del data[key]
    _save_deprecations(vault_path, data)


def get_deprecation(vault_path: str, key: str) -> Optional[dict]:
    """Return deprecation entry for *key*, or None if not deprecated."""
    return _load_deprecations(vault_path).get(key)


def list_deprecated(vault_path: str) -> dict:
    """Return all deprecated keys and their entries."""
    return _load_deprecations(vault_path)
