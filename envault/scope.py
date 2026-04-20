"""Scope management for envault — restrict keys to named scopes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class ScopeError(Exception):
    """Raised when a scope operation fails."""


def _scopes_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_scopes.json"


def _load_scopes(vault_path: str) -> Dict[str, List[str]]:
    p = _scopes_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_scopes(vault_path: str, data: Dict[str, List[str]]) -> None:
    _scopes_path(vault_path).write_text(json.dumps(data, indent=2))


def add_to_scope(vault_path: str, scope: str, key: str) -> Dict:
    """Add *key* to *scope*, creating the scope if needed."""
    if not scope:
        raise ScopeError("scope name must not be empty")
    if not key:
        raise ScopeError("key must not be empty")
    data = _load_scopes(vault_path)
    keys: List[str] = data.setdefault(scope, [])
    if key not in keys:
        keys.append(key)
    _save_scopes(vault_path, data)
    return {"scope": scope, "keys": keys}


def remove_from_scope(vault_path: str, scope: str, key: str) -> Dict:
    """Remove *key* from *scope*."""
    data = _load_scopes(vault_path)
    keys: List[str] = data.get(scope, [])
    if key not in keys:
        raise ScopeError(f"key '{key}' not found in scope '{scope}'")
    keys.remove(key)
    data[scope] = keys
    _save_scopes(vault_path, data)
    return {"scope": scope, "keys": keys}


def list_scopes(vault_path: str) -> Dict[str, List[str]]:
    """Return all scopes and their keys."""
    return _load_scopes(vault_path)


def keys_in_scope(vault_path: str, scope: str) -> List[str]:
    """Return all keys belonging to *scope*."""
    data = _load_scopes(vault_path)
    if scope not in data:
        raise ScopeError(f"scope '{scope}' does not exist")
    return list(data[scope])


def delete_scope(vault_path: str, scope: str) -> None:
    """Delete an entire scope."""
    data = _load_scopes(vault_path)
    if scope not in data:
        raise ScopeError(f"scope '{scope}' does not exist")
    del data[scope]
    _save_scopes(vault_path, data)
