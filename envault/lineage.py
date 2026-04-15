"""Track the lineage (origin/derivation chain) of secrets in a vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class LineageError(Exception):
    """Raised when a lineage operation fails."""


def _lineage_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault" / "lineage.json"


def _load_lineage(vault_path: str) -> Dict:
    path = _lineage_path(vault_path)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_lineage(vault_path: str, data: Dict) -> None:
    path = _lineage_path(vault_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_lineage(
    vault_path: str,
    key: str,
    derived_from: Optional[str] = None,
    source: Optional[str] = None,
    note: str = "",
) -> Dict:
    """Record the lineage of *key*.

    Parameters
    ----------
    vault_path:   path to the vault file
    key:          the secret key whose lineage is being recorded
    derived_from: another key in the same vault this key was derived from
    source:       free-form external source identifier (e.g. "aws/ssm/prod")
    note:         optional human-readable note
    """
    if derived_from is None and source is None:
        raise LineageError("At least one of derived_from or source must be provided.")

    data = _load_lineage(vault_path)
    entry: Dict = {"derived_from": derived_from, "source": source, "note": note}
    data[key] = entry
    _save_lineage(vault_path, data)
    return entry


def get_lineage(vault_path: str, key: str) -> Dict:
    """Return the lineage entry for *key*, or raise LineageError if absent."""
    data = _load_lineage(vault_path)
    if key not in data:
        raise LineageError(f"No lineage recorded for key '{key}'.")
    return data[key]


def remove_lineage(vault_path: str, key: str) -> None:
    """Remove the lineage record for *key*."""
    data = _load_lineage(vault_path)
    if key not in data:
        raise LineageError(f"No lineage recorded for key '{key}'.")
    del data[key]
    _save_lineage(vault_path, data)


def list_lineage(vault_path: str) -> Dict[str, Dict]:
    """Return all recorded lineage entries."""
    return _load_lineage(vault_path)


def ancestors(vault_path: str, key: str) -> List[str]:
    """Return the chain of ancestor keys for *key* (oldest last)."""
    data = _load_lineage(vault_path)
    chain: List[str] = []
    visited = set()
    current = key
    while True:
        entry = data.get(current)
        if entry is None:
            break
        parent = entry.get("derived_from")
        if parent is None or parent in visited:
            break
        chain.append(parent)
        visited.add(parent)
        current = parent
    return chain
