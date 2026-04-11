"""Compare two vaults or a vault against a dotenv file and report differences."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, NamedTuple

from envault.vault import Vault
from envault.import_env import _parse_dotenv


class DiffError(Exception):
    """Raised when a diff operation fails."""


class DiffEntry(NamedTuple):
    key: str
    status: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    left_value: str | None
    right_value: str | None


def _vault_to_dict(vault_path: Path, password: str) -> Dict[str, str]:
    """Decrypt all secrets from a vault into a plain dict."""
    v = Vault(vault_path, password)
    keys = v.list()
    return {k: v.get(k) for k in keys}


def diff_vaults(
    left_path: Path,
    left_password: str,
    right_path: Path,
    right_password: str,
) -> List[DiffEntry]:
    """Return the diff between two vaults."""
    left = _vault_to_dict(left_path, left_password)
    right = _vault_to_dict(right_path, right_password)
    return _compute_diff(left, right)


def diff_vault_dotenv(
    vault_path: Path,
    password: str,
    dotenv_path: Path,
) -> List[DiffEntry]:
    """Return the diff between a vault and a .env file."""
    vault_data = _vault_to_dict(vault_path, password)
    try:
        dotenv_text = dotenv_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DiffError(f"Cannot read dotenv file: {exc}") from exc
    dotenv_data = _parse_dotenv(dotenv_text)
    return _compute_diff(vault_data, dotenv_data)


def _compute_diff(
    left: Dict[str, str],
    right: Dict[str, str],
) -> List[DiffEntry]:
    """Core diff logic — compares two plain dicts."""
    entries: List[DiffEntry] = []
    all_keys = sorted(set(left) | set(right))
    for key in all_keys:
        lv = left.get(key)
        rv = right.get(key)
        if lv is None:
            status = "added"
        elif rv is None:
            status = "removed"
        elif lv != rv:
            status = "changed"
        else:
            status = "unchanged"
        entries.append(DiffEntry(key=key, status=status, left_value=lv, right_value=rv))
    return entries
