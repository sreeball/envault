"""Key aliasing — map short names to full secret keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _aliases_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_aliases.json"


def _load_aliases(vault_path: str) -> Dict[str, str]:
    p = _aliases_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_aliases(vault_path: str, data: Dict[str, str]) -> None:
    _aliases_path(vault_path).write_text(json.dumps(data, indent=2))


def add_alias(vault_path: str, alias: str, key: str) -> Dict[str, str]:
    """Register *alias* as a short name for *key*."""
    data = _load_aliases(vault_path)
    if alias in data:
        raise AliasError(f"Alias '{alias}' already exists (points to '{data[alias]}'). Remove it first.")
    data[alias] = key
    _save_aliases(vault_path, data)
    return {"alias": alias, "key": key}


def remove_alias(vault_path: str, alias: str) -> Dict[str, str]:
    """Remove an existing alias."""
    data = _load_aliases(vault_path)
    if alias not in data:
        raise AliasError(f"Alias '{alias}' not found.")
    entry = {"alias": alias, "key": data.pop(alias)}
    _save_aliases(vault_path, data)
    return entry


def resolve(vault_path: str, name: str) -> str:
    """Return the canonical key for *name*, or *name* itself if not aliased."""
    return _load_aliases(vault_path).get(name, name)


def list_aliases(vault_path: str) -> List[Dict[str, str]]:
    """Return all alias→key mappings as a list of dicts."""
    data = _load_aliases(vault_path)
    return [{"alias": a, "key": k} for a, k in sorted(data.items())]
