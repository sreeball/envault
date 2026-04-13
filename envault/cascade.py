"""Cascade resolution: merge secrets from multiple vaults in priority order."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault


class CascadeError(Exception):
    """Raised when cascade resolution fails."""


def resolve(
    vault_paths: List[Path],
    password: str,
    *,
    keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Merge secrets from *vault_paths* in priority order (first path wins).

    Args:
        vault_paths: Ordered list of vault file paths; index 0 has highest priority.
        password: Shared decryption password used for every vault.
        keys: Optional allowlist of keys to include in the result.

    Returns:
        A plain-text dict of resolved key→value pairs.

    Raises:
        CascadeError: If any vault file does not exist or cannot be decrypted.
    """
    if not vault_paths:
        raise CascadeError("At least one vault path is required.")

    merged: Dict[str, str] = {}

    # Iterate in *reverse* so that higher-priority vaults overwrite lower ones.
    for path in reversed(vault_paths):
        if not Path(path).exists():
            raise CascadeError(f"Vault not found: {path}")
        try:
            vault = Vault(path, password)
            for key in vault.list():
                if keys is None or key in keys:
                    merged[key] = vault.get(key)
        except Exception as exc:
            raise CascadeError(f"Failed to read vault '{path}': {exc}") from exc

    return merged


def sources(
    vault_paths: List[Path],
    password: str,
    key: str,
) -> Optional[Path]:
    """Return the highest-priority vault path that contains *key*, or None."""
    for path in vault_paths:
        if not Path(path).exists():
            continue
        try:
            vault = Vault(path, password)
            if key in vault.list():
                return Path(path)
        except Exception:
            continue
    return None
