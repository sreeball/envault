"""Visibility control for vault secrets (public / private / masked)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

VISIBILITY_LEVELS = ("public", "private", "masked")


class VisibilityError(Exception):
    """Raised when a visibility operation fails."""


def _visibility_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_visibility.json"


def _load_visibility(vault_path: str) -> Dict[str, str]:
    p = _visibility_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_visibility(vault_path: str, data: Dict[str, str]) -> None:
    _visibility_path(vault_path).write_text(json.dumps(data, indent=2))


def set_visibility(vault_path: str, key: str, level: str) -> Dict[str, str]:
    """Set the visibility level for *key*. Returns the updated entry."""
    if level not in VISIBILITY_LEVELS:
        raise VisibilityError(
            f"Invalid visibility level '{level}'. Choose from: {VISIBILITY_LEVELS}"
        )
    data = _load_visibility(vault_path)
    data[key] = level
    _save_visibility(vault_path, data)
    return {"key": key, "visibility": level}


def get_visibility(vault_path: str, key: str) -> str:
    """Return the visibility level for *key* (defaults to 'private')."""
    data = _load_visibility(vault_path)
    return data.get(key, "private")


def remove_visibility(vault_path: str, key: str) -> bool:
    """Remove explicit visibility setting for *key*. Returns True if removed."""
    data = _load_visibility(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_visibility(vault_path, data)
    return True


def list_visibility(vault_path: str) -> List[Dict[str, str]]:
    """Return all keys with an explicit visibility level."""
    data = _load_visibility(vault_path)
    return [{"key": k, "visibility": v} for k, v in sorted(data.items())]


def apply_visibility(key: str, value: str, level: str) -> str:
    """Return *value* transformed according to *level* for display purposes."""
    if level == "public":
        return value
    if level == "masked":
        return "***"
    # private
    return "[hidden]"
