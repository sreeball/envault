"""Vault locking: temporarily lock a vault to prevent reads and writes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class LockError(Exception):
    """Raised when a locking operation fails."""


def _lock_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".lock")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def lock_vault(vault_path: str, reason: str = "", actor: str = "user") -> dict:
    """Lock a vault. Raises LockError if already locked."""
    lp = _lock_path(vault_path)
    if lp.exists():
        info = json.loads(lp.read_text())
        raise LockError(
            f"Vault is already locked since {info['locked_at']} by {info['actor']}"
        )
    entry = {
        "locked_at": _now_iso(),
        "actor": actor,
        "reason": reason,
    }
    lp.write_text(json.dumps(entry, indent=2))
    return entry


def unlock_vault(vault_path: str) -> dict:
    """Unlock a vault. Raises LockError if not locked."""
    lp = _lock_path(vault_path)
    if not lp.exists():
        raise LockError("Vault is not locked.")
    entry = json.loads(lp.read_text())
    lp.unlink()
    entry["unlocked_at"] = _now_iso()
    return entry


def is_locked(vault_path: str) -> bool:
    """Return True if the vault is currently locked."""
    return _lock_path(vault_path).exists()


def lock_info(vault_path: str) -> Optional[dict]:
    """Return lock metadata or None if not locked."""
    lp = _lock_path(vault_path)
    if not lp.exists():
        return None
    return json.loads(lp.read_text())


def assert_unlocked(vault_path: str) -> None:
    """Raise LockError if the vault is locked."""
    info = lock_info(vault_path)
    if info is not None:
        raise LockError(
            f"Vault is locked (reason: {info.get('reason') or 'none'}, "
            f"locked_at: {info['locked_at']})"
        )
