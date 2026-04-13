"""Checksum tracking for vault secrets.

Stores a SHA-256 digest for each secret value so that out-of-band
modifications (e.g. direct file edits) can be detected.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional


class ChecksumError(Exception):
    """Raised when a checksum operation fails."""


def _checksum_path(vault_path: str) -> Path:
    p = Path(vault_path)
    return p.parent / (p.stem + ".checksums.json")


def _load_checksums(vault_path: str) -> Dict[str, str]:
    path = _checksum_path(vault_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ChecksumError(f"Corrupt checksum file: {exc}") from exc


def _save_checksums(vault_path: str, data: Dict[str, str]) -> None:
    _checksum_path(vault_path).write_text(json.dumps(data, indent=2))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def record_checksum(vault_path: str, key: str, value: str) -> str:
    """Store a checksum for *key* derived from *value*. Returns the digest."""
    data = _load_checksums(vault_path)
    digest = _digest(value)
    data[key] = digest
    _save_checksums(vault_path, data)
    return digest


def verify_checksum(vault_path: str, key: str, value: str) -> bool:
    """Return True if the stored checksum matches *value*."""
    data = _load_checksums(vault_path)
    if key not in data:
        raise ChecksumError(f"No checksum recorded for key '{key}'")
    return data[key] == _digest(value)


def remove_checksum(vault_path: str, key: str) -> None:
    """Delete the checksum entry for *key* (no-op if absent)."""
    data = _load_checksums(vault_path)
    data.pop(key, None)
    _save_checksums(vault_path, data)


def list_checksums(vault_path: str) -> Dict[str, str]:
    """Return a mapping of key → digest for all tracked secrets."""
    return _load_checksums(vault_path)


def get_checksum(vault_path: str, key: str) -> Optional[str]:
    """Return the stored digest for *key*, or None if not tracked."""
    return _load_checksums(vault_path).get(key)
