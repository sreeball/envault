"""Capacity tracking for vault secrets — record and query usage limits per key."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional


class CapacityError(Exception):
    """Raised when a capacity operation fails."""


def _capacity_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_capacity.json"


def _load_capacity(vault_path: str) -> Dict[str, Any]:
    path = _capacity_path(vault_path)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_capacity(vault_path: str, data: Dict[str, Any]) -> None:
    path = _capacity_path(vault_path)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_capacity(
    vault_path: str,
    key: str,
    max_length: int,
    note: str = "",
) -> Dict[str, Any]:
    """Record a maximum-length capacity constraint for *key*.

    Args:
        vault_path: Path to the vault file.
        key: Secret key name.
        max_length: Maximum allowed value length (characters). Must be >= 1.
        note: Optional human-readable note.

    Returns:
        The stored capacity entry.

    Raises:
        CapacityError: If *max_length* is less than 1.
    """
    if max_length < 1:
        raise CapacityError("max_length must be at least 1")

    data = _load_capacity(vault_path)
    entry: Dict[str, Any] = {
        "key": key,
        "max_length": max_length,
        "note": note,
    }
    data[key] = entry
    _save_capacity(vault_path, data)
    return entry


def get_capacity(vault_path: str, key: str) -> Optional[Dict[str, Any]]:
    """Return the capacity entry for *key*, or ``None`` if not set."""
    return _load_capacity(vault_path).get(key)


def remove_capacity(vault_path: str, key: str) -> bool:
    """Remove the capacity entry for *key*. Returns ``True`` if removed."""
    data = _load_capacity(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_capacity(vault_path, data)
    return True


def list_capacity(vault_path: str) -> Dict[str, Any]:
    """Return all capacity entries keyed by secret name."""
    return _load_capacity(vault_path)
