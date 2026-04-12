"""Quota management: enforce limits on the number of secrets in a vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envault.vault import Vault


class QuotaError(Exception):
    """Raised when a quota operation fails or a limit is exceeded."""


def _quota_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_quota.json"


def _load_quota(vault_path: str) -> dict:
    p = _quota_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_quota(vault_path: str, data: dict) -> None:
    _quota_path(vault_path).write_text(json.dumps(data, indent=2))


def set_quota(vault_path: str, max_secrets: int) -> dict:
    """Set the maximum number of secrets allowed in the vault."""
    if max_secrets < 1:
        raise QuotaError("max_secrets must be a positive integer")
    data = _load_quota(vault_path)
    data["max_secrets"] = max_secrets
    _save_quota(vault_path, data)
    return {"max_secrets": max_secrets}


def get_quota(vault_path: str) -> Optional[int]:
    """Return the configured quota, or None if not set."""
    data = _load_quota(vault_path)
    return data.get("max_secrets")


def remove_quota(vault_path: str) -> bool:
    """Remove the quota limit. Returns True if a quota existed."""
    data = _load_quota(vault_path)
    if "max_secrets" not in data:
        return False
    del data["max_secrets"]
    _save_quota(vault_path, data)
    return True


def check_quota(vault_path: str, password: str) -> dict:
    """Check current usage against the quota.

    Returns a dict with keys: max_secrets, current, remaining, exceeded.
    If no quota is set, max_secrets and remaining are None.
    """
    vault = Vault(vault_path, password)
    current = len(vault.keys())
    max_secrets = get_quota(vault_path)
    if max_secrets is None:
        return {"max_secrets": None, "current": current, "remaining": None, "exceeded": False}
    exceeded = current > max_secrets
    remaining = max(0, max_secrets - current)
    return {"max_secrets": max_secrets, "current": current, "remaining": remaining, "exceeded": exceeded}


def enforce_quota(vault_path: str, password: str) -> None:
    """Raise QuotaError if the vault currently exceeds its quota."""
    result = check_quota(vault_path, password)
    if result["exceeded"]:
        raise QuotaError(
            f"Vault exceeds quota: {result['current']} secrets stored, "
            f"limit is {result['max_secrets']}"
        )
