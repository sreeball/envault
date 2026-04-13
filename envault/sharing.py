"""Secure secret sharing between vault users."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from envault.crypto import encrypt, decrypt, generate_salt, derive_key


class SharingError(Exception):
    """Raised when a sharing operation fails."""


def _shares_path(vault_path: str | Path) -> Path:
    return Path(vault_path).parent / ".envault_shares.json"


def _load_shares(vault_path: str | Path) -> dict:
    p = _shares_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_shares(vault_path: str | Path, data: dict) -> None:
    _shares_path(vault_path).write_text(json.dumps(data, indent=2))


def share_key(
    vault_path: str | Path,
    key: str,
    plaintext: str,
    recipient: str,
    shared_password: str,
    ttl_seconds: int = 86400,
) -> dict[str, Any]:
    """Encrypt *plaintext* with *shared_password* and store a share token."""
    if not key:
        raise SharingError("key must not be empty")
    if not recipient:
        raise SharingError("recipient must not be empty")
    if ttl_seconds <= 0:
        raise SharingError("ttl_seconds must be positive")

    salt = generate_salt()
    derived = derive_key(shared_password, salt)
    ciphertext = encrypt(derived, plaintext.encode())
    expires_at = time.time() + ttl_seconds

    entry: dict[str, Any] = {
        "recipient": recipient,
        "salt": salt.hex(),
        "ciphertext": ciphertext.hex(),
        "expires_at": expires_at,
    }

    shares = _load_shares(vault_path)
    shares.setdefault(key, []).append(entry)
    _save_shares(vault_path, shares)
    return entry


def redeem_share(
    vault_path: str | Path,
    key: str,
    recipient: str,
    shared_password: str,
) -> str:
    """Decrypt and return the shared value; raises *SharingError* on failure."""
    shares = _load_shares(vault_path)
    entries = shares.get(key, [])
    now = time.time()
    for entry in entries:
        if entry["recipient"] != recipient:
            continue
        if entry["expires_at"] < now:
            raise SharingError(f"share for '{key}' to '{recipient}' has expired")
        salt = bytes.fromhex(entry["salt"])
        ciphertext = bytes.fromhex(entry["ciphertext"])
        derived = derive_key(shared_password, salt)
        try:
            return decrypt(derived, ciphertext).decode()
        except Exception as exc:
            raise SharingError("invalid password or corrupted share") from exc
    raise SharingError(f"no active share found for key '{key}' and recipient '{recipient}'")


def revoke_share(vault_path: str | Path, key: str, recipient: str) -> int:
    """Remove all shares for *key*/*recipient*; returns count removed."""
    shares = _load_shares(vault_path)
    before = shares.get(key, [])
    after = [e for e in before if e["recipient"] != recipient]
    removed = len(before) - len(after)
    if after:
        shares[key] = after
    elif key in shares:
        del shares[key]
    _save_shares(vault_path, shares)
    return removed


def list_shares(vault_path: str | Path) -> dict[str, list[dict]]:
    """Return all current shares (including expired ones)."""
    return _load_shares(vault_path)
