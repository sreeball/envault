"""Attach arbitrary metadata key-value pairs to vault secrets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class MetadataError(Exception):
    """Raised when a metadata operation fails."""


def _metadata_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_metadata.json"


def _load_metadata(vault_path: str) -> Dict[str, Dict[str, str]]:
    p = _metadata_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_metadata(vault_path: str, data: Dict[str, Dict[str, str]]) -> None:
    _metadata_path(vault_path).write_text(json.dumps(data, indent=2))


def set_meta(vault_path: str, key: str, field: str, value: str) -> Dict[str, str]:
    """Set a metadata field on *key*. Returns the updated metadata dict for that key."""
    if not field.strip():
        raise MetadataError("field name must not be empty")
    data = _load_metadata(vault_path)
    data.setdefault(key, {})[field] = value
    _save_metadata(vault_path, data)
    return dict(data[key])


def get_meta(vault_path: str, key: str) -> Dict[str, str]:
    """Return all metadata fields for *key*."""
    data = _load_metadata(vault_path)
    return dict(data.get(key, {}))


def remove_meta(vault_path: str, key: str, field: str) -> Dict[str, str]:
    """Remove a single metadata field from *key*. Returns remaining metadata."""
    data = _load_metadata(vault_path)
    if key not in data or field not in data[key]:
        raise MetadataError(f"field '{field}' not found on key '{key}'")
    del data[key][field]
    if not data[key]:
        del data[key]
    _save_metadata(vault_path, data)
    return dict(data.get(key, {}))


def list_meta(vault_path: str) -> Dict[str, Dict[str, str]]:
    """Return all metadata for all keys."""
    return dict(_load_metadata(vault_path))


def keys_with_field(vault_path: str, field: str) -> List[str]:
    """Return all secret keys that have *field* set."""
    data = _load_metadata(vault_path)
    return [k for k, fields in data.items() if field in fields]
