"""Track dependencies between secrets (key A requires key B to exist)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class DependencyError(Exception):
    pass


def _deps_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_deps.json"


def _load_deps(vault_path: str) -> Dict[str, List[str]]:
    p = _deps_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_deps(vault_path: str, data: Dict[str, List[str]]) -> None:
    _deps_path(vault_path).write_text(json.dumps(data, indent=2))


def add_dependency(vault_path: str, key: str, depends_on: str) -> Dict[str, List[str]]:
    """Record that *key* depends on *depends_on*."""
    if key == depends_on:
        raise DependencyError("A key cannot depend on itself.")
    data = _load_deps(vault_path)
    deps = data.get(key, [])
    if depends_on in deps:
        raise DependencyError(f"Dependency '{depends_on}' already registered for '{key}'.")
    deps.append(depends_on)
    data[key] = deps
    _save_deps(vault_path, data)
    return {"key": key, "depends_on": deps}


def remove_dependency(vault_path: str, key: str, depends_on: str) -> List[str]:
    """Remove a specific dependency from *key*."""
    data = _load_deps(vault_path)
    deps = data.get(key, [])
    if depends_on not in deps:
        raise DependencyError(f"Dependency '{depends_on}' not found for '{key}'.")
    deps.remove(depends_on)
    if deps:
        data[key] = deps
    else:
        data.pop(key, None)
    _save_deps(vault_path, data)
    return deps


def get_dependencies(vault_path: str, key: str) -> List[str]:
    """Return the list of keys that *key* depends on."""
    return _load_deps(vault_path).get(key, [])


def check_satisfied(vault_path: str, present_keys: List[str]) -> Dict[str, List[str]]:
    """Return a mapping of keys whose dependencies are *not* satisfied."""
    data = _load_deps(vault_path)
    missing: Dict[str, List[str]] = {}
    present = set(present_keys)
    for key, deps in data.items():
        unmet = [d for d in deps if d not in present]
        if unmet:
            missing[key] = unmet
    return missing


def list_all(vault_path: str) -> Dict[str, List[str]]:
    """Return the full dependency map."""
    return _load_deps(vault_path)
