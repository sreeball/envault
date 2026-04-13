"""Soft-delete (recycle bin) for vault secrets."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RecycleError(Exception):
    """Raised when a recycle-bin operation fails."""


def _recycle_path(vault_path: str | Path) -> Path:
    return Path(vault_path).parent / ".recycle.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_bin(vault_path: str | Path) -> dict[str, Any]:
    p = _recycle_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_bin(vault_path: str | Path, data: dict[str, Any]) -> None:
    _recycle_path(vault_path).write_text(json.dumps(data, indent=2))


def soft_delete(vault_path: str | Path, key: str, encrypted_entry: dict) -> dict:
    """Move *key* into the recycle bin, preserving its encrypted payload."""
    bin_data = _load_bin(vault_path)
    if key in bin_data:
        raise RecycleError(f"Key '{key}' is already in the recycle bin.")
    entry = {
        "key": key,
        "deleted_at": _now_iso(),
        "payload": encrypted_entry,
    }
    bin_data[key] = entry
    _save_bin(vault_path, bin_data)
    return entry


def restore(vault_path: str | Path, key: str) -> dict:
    """Retrieve and remove *key* from the recycle bin."""
    bin_data = _load_bin(vault_path)
    if key not in bin_data:
        raise RecycleError(f"Key '{key}' not found in the recycle bin.")
    entry = bin_data.pop(key)
    _save_bin(vault_path, bin_data)
    return entry


def list_bin(vault_path: str | Path) -> list[dict]:
    """Return all entries currently in the recycle bin."""
    return list(_load_bin(vault_path).values())


def purge(vault_path: str | Path, key: str) -> None:
    """Permanently remove *key* from the recycle bin."""
    bin_data = _load_bin(vault_path)
    if key not in bin_data:
        raise RecycleError(f"Key '{key}' not found in the recycle bin.")
    del bin_data[key]
    _save_bin(vault_path, bin_data)


def purge_all(vault_path: str | Path) -> int:
    """Permanently remove every entry from the recycle bin. Returns count purged."""
    bin_data = _load_bin(vault_path)
    count = len(bin_data)
    _save_bin(vault_path, {})
    return count
