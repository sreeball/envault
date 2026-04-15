"""Ownership tracking for vault secrets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class OwnershipError(Exception):
    """Raised when an ownership operation fails."""


def _ownership_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_ownership.json"


def _load_ownership(vault_path: str) -> Dict:
    p = _ownership_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_ownership(vault_path: str, data: Dict) -> None:
    _ownership_path(vault_path).write_text(json.dumps(data, indent=2))


def set_owner(vault_path: str, key: str, owner: str, team: Optional[str] = None) -> Dict:
    """Assign an owner (and optional team) to a secret key."""
    if not key:
        raise OwnershipError("key must not be empty")
    if not owner:
        raise OwnershipError("owner must not be empty")
    data = _load_ownership(vault_path)
    entry = {"owner": owner, "team": team}
    data[key] = entry
    _save_ownership(vault_path, data)
    return entry


def get_owner(vault_path: str, key: str) -> Dict:
    """Return ownership info for a key."""
    data = _load_ownership(vault_path)
    if key not in data:
        raise OwnershipError(f"no ownership record for '{key}'")
    return data[key]


def remove_owner(vault_path: str, key: str) -> None:
    """Remove ownership record for a key."""
    data = _load_ownership(vault_path)
    if key not in data:
        raise OwnershipError(f"no ownership record for '{key}'")
    del data[key]
    _save_ownership(vault_path, data)


def list_owned_by(vault_path: str, owner: str) -> List[str]:
    """Return all keys owned by the given owner."""
    data = _load_ownership(vault_path)
    return [k for k, v in data.items() if v.get("owner") == owner]


def list_all(vault_path: str) -> Dict:
    """Return the full ownership map."""
    return _load_ownership(vault_path)
