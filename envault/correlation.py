"""Track correlations (relationships) between secret keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class CorrelationError(Exception):
    """Raised when a correlation operation fails."""


def _correlations_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_correlations.json"


def _load_correlations(vault_path: str) -> Dict[str, List[str]]:
    p = _correlations_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_correlations(vault_path: str, data: Dict[str, List[str]]) -> None:
    _correlations_path(vault_path).write_text(json.dumps(data, indent=2))


def link(vault_path: str, key: str, related_key: str) -> Dict[str, List[str]]:
    """Record that *key* and *related_key* are correlated.

    The relationship is stored bidirectionally.
    """
    if key == related_key:
        raise CorrelationError("A key cannot be correlated with itself.")
    data = _load_correlations(vault_path)
    for a, b in ((key, related_key), (related_key, key)):
        data.setdefault(a, [])
        if b not in data[a]:
            data[a].append(b)
    _save_correlations(vault_path, data)
    return {"key": key, "related_key": related_key, "all_related": data[key]}


def unlink(vault_path: str, key: str, related_key: str) -> List[str]:
    """Remove the correlation between *key* and *related_key*."""
    data = _load_correlations(vault_path)
    changed = False
    for a, b in ((key, related_key), (related_key, key)):
        if a in data and b in data[a]:
            data[a].remove(b)
            changed = True
    if not changed:
        raise CorrelationError(f"No correlation found between '{key}' and '{related_key}'.")
    _save_correlations(vault_path, data)
    return data.get(key, [])


def get_related(vault_path: str, key: str) -> List[str]:
    """Return all keys correlated with *key*."""
    data = _load_correlations(vault_path)
    return data.get(key, [])


def all_correlations(vault_path: str) -> Dict[str, List[str]]:
    """Return the full correlations map."""
    return _load_correlations(vault_path)
