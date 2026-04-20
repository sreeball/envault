"""Track obsolescence status for vault keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ObsolescenceError(Exception):
    pass


def _obsolescence_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault" / "obsolescence.json"


def _load_obsolescence(vault_path: str) -> Dict[str, Any]:
    p = _obsolescence_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_obsolescence(vault_path: str, data: Dict[str, Any]) -> None:
    p = _obsolescence_path(vault_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def mark_obsolete(
    vault_path: str,
    key: str,
    reason: str = "",
    replacement: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark a key as obsolete with an optional reason and replacement key."""
    data = _load_obsolescence(vault_path)
    entry: Dict[str, Any] = {
        "key": key,
        "reason": reason,
        "replacement": replacement,
    }
    data[key] = entry
    _save_obsolescence(vault_path, data)
    return entry


def unmark_obsolete(vault_path: str, key: str) -> None:
    """Remove the obsolescence mark from a key."""
    data = _load_obsolescence(vault_path)
    if key not in data:
        raise ObsolescenceError(f"Key '{key}' is not marked as obsolete.")
    del data[key]
    _save_obsolescence(vault_path, data)


def get_obsolescence(vault_path: str, key: str) -> Optional[Dict[str, Any]]:
    """Return the obsolescence entry for a key, or None if not marked."""
    data = _load_obsolescence(vault_path)
    return data.get(key)


def list_obsolete(vault_path: str) -> Dict[str, Any]:
    """Return all obsolete key entries."""
    return _load_obsolescence(vault_path)
