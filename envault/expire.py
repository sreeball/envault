"""Bulk expiry management for vault secrets."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envault.ttl import _ttl_path, _now


class ExpireError(Exception):
    """Raised when an expiry operation fails."""


def list_expired(vault_path: str) -> List[str]:
    """Return keys whose TTL has already elapsed."""
    ttl_file = _ttl_path(vault_path)
    if not Path(ttl_file).exists():
        return []
    with open(ttl_file) as fh:
        data: Dict = json.load(fh)
    now = _now()
    return [
        key
        for key, entry in data.items()
        if entry.get("expires_at") and entry["expires_at"] <= now
    ]


def list_expiring_soon(vault_path: str, within_seconds: int = 86400) -> List[str]:
    """Return keys that will expire within *within_seconds* from now."""
    if within_seconds < 0:
        raise ExpireError("within_seconds must be non-negative")
    ttl_file = _ttl_path(vault_path)
    if not Path(ttl_file).exists():
        return []
    with open(ttl_file) as fh:
        data: Dict = json.load(fh)
    now = _now()
    cutoff = datetime.fromtimestamp(
        datetime.fromisoformat(now).timestamp() + within_seconds,
        tz=timezone.utc,
    ).isoformat()
    return [
        key
        for key, entry in data.items()
        if entry.get("expires_at")
        and now <= entry["expires_at"] <= cutoff
    ]


def purge_expired(vault_path: str) -> List[str]:
    """Delete expired keys from the vault and TTL file.

    Returns the list of keys that were removed.
    """
    from envault.vault import Vault  # local import to avoid circularity

    expired = list_expired(vault_path)
    if not expired:
        return []

    ttl_file = _ttl_path(vault_path)
    with open(ttl_file) as fh:
        ttl_data: Dict = json.load(fh)

    # We don't have the password here, so we only remove from the TTL index
    # and leave the encrypted blob; callers that hold a Vault instance should
    # call vault.delete(key) themselves after purge_expired.
    for key in expired:
        ttl_data.pop(key, None)

    with open(ttl_file, "w") as fh:
        json.dump(ttl_data, fh, indent=2)

    return expired


def expiry_info(vault_path: str, key: str) -> Optional[Dict]:
    """Return the TTL entry for *key*, or None if no TTL is set."""
    ttl_file = _ttl_path(vault_path)
    if not Path(ttl_file).exists():
        return None
    with open(ttl_file) as fh:
        data: Dict = json.load(fh)
    return data.get(key)
