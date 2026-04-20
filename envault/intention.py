"""Track the intended purpose or use-case for a secret key."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class IntentionError(Exception):
    """Raised when an intention operation fails."""


def _intentions_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault" / "intentions.json"


def _load_intentions(vault_path: str) -> Dict[str, dict]:
    path = _intentions_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_intentions(vault_path: str, data: Dict[str, dict]) -> None:
    path = _intentions_path(vault_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def set_intention(
    vault_path: str,
    key: str,
    purpose: str,
    owner: Optional[str] = None,
    note: Optional[str] = None,
) -> dict:
    """Record the intended purpose for *key*."""
    if not purpose.strip():
        raise IntentionError("purpose must not be empty")

    data = _load_intentions(vault_path)
    entry = {
        "key": key,
        "purpose": purpose,
        "owner": owner or "",
        "note": note or "",
    }
    data[key] = entry
    _save_intentions(vault_path, data)
    return entry


def get_intention(vault_path: str, key: str) -> Optional[dict]:
    """Return the intention entry for *key*, or None if not set."""
    return _load_intentions(vault_path).get(key)


def remove_intention(vault_path: str, key: str) -> bool:
    """Remove the intention for *key*. Returns True if it existed."""
    data = _load_intentions(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_intentions(vault_path, data)
    return True


def list_intentions(vault_path: str) -> Dict[str, dict]:
    """Return all intention entries."""
    return _load_intentions(vault_path)
