"""Namespace support for grouping secrets under logical prefixes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class NamespaceError(Exception):
    """Raised when a namespace operation fails."""


def _ns_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_namespaces.json"


def _load_ns(vault_path: str) -> Dict[str, List[str]]:
    p = _ns_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_ns(vault_path: str, data: Dict[str, List[str]]) -> None:
    _ns_path(vault_path).write_text(json.dumps(data, indent=2))


def add_to_namespace(vault_path: str, namespace: str, key: str) -> Dict:
    """Add *key* to *namespace*. Creates the namespace if it doesn't exist."""
    if not namespace:
        raise NamespaceError("Namespace name must not be empty.")
    if not key:
        raise NamespaceError("Key must not be empty.")
    data = _load_ns(vault_path)
    keys = data.setdefault(namespace, [])
    if key not in keys:
        keys.append(key)
    _save_ns(vault_path, data)
    return {"namespace": namespace, "keys": list(keys)}


def remove_from_namespace(vault_path: str, namespace: str, key: str) -> Dict:
    """Remove *key* from *namespace*."""
    data = _load_ns(vault_path)
    if namespace not in data:
        raise NamespaceError(f"Namespace '{namespace}' does not exist.")
    if key not in data[namespace]:
        raise NamespaceError(f"Key '{key}' not in namespace '{namespace}'.")
    data[namespace].remove(key)
    if not data[namespace]:
        del data[namespace]
    _save_ns(vault_path, data)
    return {"namespace": namespace, "keys": data.get(namespace, [])}


def list_namespaces(vault_path: str) -> Dict[str, List[str]]:
    """Return all namespaces and their keys."""
    return _load_ns(vault_path)


def keys_in_namespace(vault_path: str, namespace: str) -> List[str]:
    """Return the keys belonging to *namespace*."""
    data = _load_ns(vault_path)
    if namespace not in data:
        raise NamespaceError(f"Namespace '{namespace}' does not exist.")
    return list(data[namespace])


def delete_namespace(vault_path: str, namespace: str) -> None:
    """Delete an entire namespace (does not delete the underlying secrets)."""
    data = _load_ns(vault_path)
    if namespace not in data:
        raise NamespaceError(f"Namespace '{namespace}' does not exist.")
    del data[namespace]
    _save_ns(vault_path, data)
