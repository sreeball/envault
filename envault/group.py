"""Group secrets together under a named group for bulk operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class GroupError(Exception):
    pass


def _groups_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_groups.json"


def _load_groups(vault_path: str) -> Dict[str, List[str]]:
    p = _groups_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_groups(vault_path: str, data: Dict[str, List[str]]) -> None:
    _groups_path(vault_path).write_text(json.dumps(data, indent=2))


def create_group(vault_path: str, group: str) -> Dict[str, List[str]]:
    """Create an empty group. Raises GroupError if it already exists."""
    data = _load_groups(vault_path)
    if group in data:
        raise GroupError(f"Group '{group}' already exists.")
    data[group] = []
    _save_groups(vault_path, data)
    return {group: data[group]}


def add_key_to_group(vault_path: str, group: str, key: str) -> Dict[str, List[str]]:
    """Add a key to an existing group."""
    data = _load_groups(vault_path)
    if group not in data:
        raise GroupError(f"Group '{group}' does not exist.")
    if key not in data[group]:
        data[group].append(key)
    _save_groups(vault_path, data)
    return {group: data[group]}


def remove_key_from_group(vault_path: str, group: str, key: str) -> Dict[str, List[str]]:
    """Remove a key from a group."""
    data = _load_groups(vault_path)
    if group not in data:
        raise GroupError(f"Group '{group}' does not exist.")
    data[group] = [k for k in data[group] if k != key]
    _save_groups(vault_path, data)
    return {group: data[group]}


def delete_group(vault_path: str, group: str) -> None:
    """Delete a group entirely."""
    data = _load_groups(vault_path)
    if group not in data:
        raise GroupError(f"Group '{group}' does not exist.")
    del data[group]
    _save_groups(vault_path, data)


def list_groups(vault_path: str) -> Dict[str, List[str]]:
    """Return all groups and their keys."""
    return _load_groups(vault_path)


def get_group(vault_path: str, group: str) -> List[str]:
    """Return the keys in a group."""
    data = _load_groups(vault_path)
    if group not in data:
        raise GroupError(f"Group '{group}' does not exist.")
    return data[group]
