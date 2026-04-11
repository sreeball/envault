"""Tag management for vault secrets — assign, remove, and filter by tags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class TagError(Exception):
    """Raised when a tag operation fails."""


def _tags_path(vault_path: str) -> Path:
    p = Path(vault_path)
    return p.parent / (p.stem + ".tags.json")


def _load_tags(vault_path: str) -> Dict[str, List[str]]:
    path = _tags_path(vault_path)
    if not path.exists():
        return {}
    with path.open("r") as fh:
        return json.load(fh)


def _save_tags(vault_path: str, data: Dict[str, List[str]]) -> None:
    path = _tags_path(vault_path)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def add_tag(vault_path: str, key: str, tag: str) -> List[str]:
    """Add *tag* to *key*. Returns the updated tag list for that key."""
    if not tag:
        raise TagError("Tag must not be empty.")
    data = _load_tags(vault_path)
    tags = data.get(key, [])
    if tag not in tags:
        tags.append(tag)
    data[key] = tags
    _save_tags(vault_path, data)
    return tags


def remove_tag(vault_path: str, key: str, tag: str) -> List[str]:
    """Remove *tag* from *key*. Returns the updated tag list."""
    data = _load_tags(vault_path)
    tags = data.get(key, [])
    if tag not in tags:
        raise TagError(f"Tag '{tag}' not found on key '{key}'.")
    tags.remove(tag)
    data[key] = tags
    _save_tags(vault_path, data)
    return tags


def get_tags(vault_path: str, key: str) -> List[str]:
    """Return all tags assigned to *key*."""
    return _load_tags(vault_path).get(key, [])


def keys_by_tag(vault_path: str, tag: str) -> List[str]:
    """Return all keys that have *tag* assigned."""
    data = _load_tags(vault_path)
    return [k for k, tags in data.items() if tag in tags]


def all_tags(vault_path: str) -> Dict[str, List[str]]:
    """Return the full tag mapping {key: [tags]} for the vault."""
    return _load_tags(vault_path)
