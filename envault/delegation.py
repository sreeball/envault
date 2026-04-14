"""Delegation: grant time-limited, scoped access to specific vault keys."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional


class DelegationError(Exception):
    """Raised when a delegation operation fails."""


def _delegation_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_delegations.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_delegations(vault_path: str) -> dict:
    p = _delegation_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_delegations(vault_path: str, data: dict) -> None:
    _delegation_path(vault_path).write_text(json.dumps(data, indent=2))


def create_delegation(
    vault_path: str,
    delegatee: str,
    keys: List[str],
    ttl_seconds: int = 3600,
    note: str = "",
) -> dict:
    """Create a scoped delegation token for *delegatee* covering *keys*."""
    if not delegatee:
        raise DelegationError("delegatee must not be empty")
    if not keys:
        raise DelegationError("at least one key must be delegated")
    if ttl_seconds <= 0:
        raise DelegationError("ttl_seconds must be positive")

    token = str(uuid.uuid4())
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    ).isoformat()

    entry = {
        "token": token,
        "delegatee": delegatee,
        "keys": list(keys),
        "created_at": _now_iso(),
        "expires_at": expires_at,
        "note": note,
    }

    data = _load_delegations(vault_path)
    data[token] = entry
    _save_delegations(vault_path, data)
    return entry


def revoke_delegation(vault_path: str, token: str) -> None:
    """Revoke a delegation by token."""
    data = _load_delegations(vault_path)
    if token not in data:
        raise DelegationError(f"delegation token not found: {token}")
    del data[token]
    _save_delegations(vault_path, data)


def check_delegation(vault_path: str, token: str, key: str) -> bool:
    """Return True if *token* grants access to *key* and has not expired."""
    data = _load_delegations(vault_path)
    entry = data.get(token)
    if entry is None:
        return False
    expires_at = datetime.fromisoformat(entry["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return False
    return key in entry["keys"]


def list_delegations(vault_path: str) -> List[dict]:
    """Return all stored delegation entries."""
    return list(_load_delegations(vault_path).values())
