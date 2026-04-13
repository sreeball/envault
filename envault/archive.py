"""Archive (soft-delete) secrets in a vault, with restore support."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


def _archive_path(vault_path: str) -> Path:
    base = Path(vault_path)
    return base.parent / (base.stem + ".archive.json")


def _load_archive(vault_path: str) -> Dict[str, Any]:
    path = _archive_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_archive(vault_path: str, data: Dict[str, Any]) -> None:
    _archive_path(vault_path).write_text(json.dumps(data, indent=2))


def archive_key(vault_path: str, key: str, entry: Dict[str, Any]) -> Dict[str, Any]:
    """Move *entry* for *key* into the archive store."""
    if not key:
        raise ArchiveError("key must not be empty")
    data = _load_archive(vault_path)
    if key in data:
        raise ArchiveError(f"key '{key}' is already archived")
    data[key] = entry
    _save_archive(vault_path, data)
    return {"key": key, "archived": True, "entry": entry}


def restore_key(vault_path: str, key: str) -> Dict[str, Any]:
    """Remove *key* from the archive and return its stored entry."""
    data = _load_archive(vault_path)
    if key not in data:
        raise ArchiveError(f"key '{key}' is not in the archive")
    entry = data.pop(key)
    _save_archive(vault_path, data)
    return {"key": key, "restored": True, "entry": entry}


def list_archived(vault_path: str) -> List[str]:
    """Return a list of all archived keys."""
    return list(_load_archive(vault_path).keys())


def purge_archived(vault_path: str, key: Optional[str] = None) -> int:
    """Permanently delete archived entries.  If *key* is given, delete only that key.

    Returns the number of entries removed.
    """
    data = _load_archive(vault_path)
    if key is not None:
        if key not in data:
            raise ArchiveError(f"key '{key}' is not in the archive")
        del data[key]
        count = 1
    else:
        count = len(data)
        data = {}
    _save_archive(vault_path, data)
    return count
