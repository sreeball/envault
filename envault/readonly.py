"""Read-only mode management for vault keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class ReadOnlyError(Exception):
    """Raised when a read-only constraint is violated."""


def _readonly_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_readonly.json"


def _load_readonly(vault_path: str) -> Dict[str, dict]:
    p = _readonly_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_readonly(vault_path: str, data: Dict[str, dict]) -> None:
    _readonly_path(vault_path).write_text(json.dumps(data, indent=2))


def mark_readonly(vault_path: str, key: str, reason: str = "") -> dict:
    """Mark a key as read-only, preventing modification or deletion."""
    data = _load_readonly(vault_path)
    entry = {"key": key, "reason": reason}
    data[key] = entry
    _save_readonly(vault_path, data)
    return entry


def unmark_readonly(vault_path: str, key: str) -> None:
    """Remove read-only protection from a key."""
    data = _load_readonly(vault_path)
    if key not in data:
        raise ReadOnlyError(f"Key '{key}' is not marked as read-only.")
    del data[key]
    _save_readonly(vault_path, data)


def is_readonly(vault_path: str, key: str) -> bool:
    """Return True if the key is marked as read-only."""
    return key in _load_readonly(vault_path)


def list_readonly(vault_path: str) -> List[dict]:
    """Return all read-only entries."""
    return list(_load_readonly(vault_path).values())


def assert_writable(vault_path: str, key: str) -> None:
    """Raise ReadOnlyError if the key is read-only."""
    data = _load_readonly(vault_path)
    if key in data:
        reason = data[key].get("reason", "")
        msg = f"Key '{key}' is read-only."
        if reason:
            msg += f" Reason: {reason}"
        raise ReadOnlyError(msg)
