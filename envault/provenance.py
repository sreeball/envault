"""Track the origin and source provenance of secrets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ProvenanceError(Exception):
    pass


def _provenance_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_provenance.json"


def _load_provenance(vault_path: str) -> Dict[str, Any]:
    p = _provenance_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_provenance(vault_path: str, data: Dict[str, Any]) -> None:
    _provenance_path(vault_path).write_text(json.dumps(data, indent=2))


def set_provenance(
    vault_path: str,
    key: str,
    source: str,
    *,
    author: Optional[str] = None,
    url: Optional[str] = None,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """Record the provenance (origin) of a secret key."""
    if not key:
        raise ProvenanceError("key must not be empty")
    if not source:
        raise ProvenanceError("source must not be empty")
    data = _load_provenance(vault_path)
    entry: Dict[str, Any] = {"source": source}
    if author is not None:
        entry["author"] = author
    if url is not None:
        entry["url"] = url
    if note is not None:
        entry["note"] = note
    data[key] = entry
    _save_provenance(vault_path, data)
    return entry


def get_provenance(vault_path: str, key: str) -> Dict[str, Any]:
    """Return the provenance record for a key, or raise ProvenanceError."""
    data = _load_provenance(vault_path)
    if key not in data:
        raise ProvenanceError(f"no provenance recorded for '{key}'")
    return data[key]


def remove_provenance(vault_path: str, key: str) -> None:
    """Delete the provenance record for a key."""
    data = _load_provenance(vault_path)
    if key not in data:
        raise ProvenanceError(f"no provenance recorded for '{key}'")
    del data[key]
    _save_provenance(vault_path, data)


def list_provenance(vault_path: str) -> Dict[str, Any]:
    """Return all provenance records."""
    return _load_provenance(vault_path)
