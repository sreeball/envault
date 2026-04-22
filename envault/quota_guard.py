"""quota_guard.py — Enforce vault-level and key-level write quotas before mutations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.quota import _load_quota, QuotaError
from envault.vault import Vault


class QuotaGuardError(Exception):
    """Raised when a quota would be exceeded."""


def _count_secrets(vault_path: Path) -> int:
    """Return the number of secrets currently stored in the vault."""
    v = Vault(vault_path, password="__probe__")
    try:
        raw = v._load_raw()
    except Exception:
        return 0
    return len(raw)


def check_vault_quota(vault_path: Path, adding: int = 1) -> None:
    """Raise QuotaGuardError if adding *adding* secrets would exceed the vault quota.

    Parameters
    ----------
    vault_path:
        Path to the vault file.
    adding:
        Number of new secrets about to be written (default 1).
    """
    quota = _load_quota(vault_path)
    max_secrets: Optional[int] = quota.get("max_secrets")
    if max_secrets is None:
        return  # no quota configured

    current = _count_secrets(vault_path)
    if current + adding > max_secrets:
        raise QuotaGuardError(
            f"Vault quota exceeded: {current} secrets stored, "
            f"max_secrets={max_secrets}, attempted to add {adding}."
        )


def check_key_quota(vault_path: Path, key: str, adding: int = 1) -> None:
    """Raise QuotaGuardError if a per-key write quota would be exceeded.

    Per-key quotas are stored under the ``keys`` mapping inside the quota
    file as ``{key: {"max_writes": N, "writes": M}}``.

    Parameters
    ----------
    vault_path:
        Path to the vault file.
    key:
        The secret key being written.
    adding:
        Number of writes about to be performed (default 1).
    """
    quota = _load_quota(vault_path)
    key_quotas: dict = quota.get("keys", {})
    entry = key_quotas.get(key)
    if entry is None:
        return  # no per-key quota

    max_writes: Optional[int] = entry.get("max_writes")
    if max_writes is None:
        return

    writes: int = entry.get("writes", 0)
    if writes + adding > max_writes:
        raise QuotaGuardError(
            f"Key quota exceeded for '{key}': {writes} writes recorded, "
            f"max_writes={max_writes}."
        )
