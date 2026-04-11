"""Search and filter secrets within a vault."""

from __future__ import annotations

import fnmatch
import re
from typing import Dict, List, Optional

from envault.vault import Vault


class SearchError(Exception):
    """Raised when a search operation fails."""


def search(
    vault: Vault,
    password: str,
    pattern: str,
    *,
    regex: bool = False,
    keys_only: bool = False,
) -> Dict[str, str]:
    """Return secrets whose key (and optionally value) match *pattern*.

    Args:
        vault: The :class:`Vault` instance to search.
        password: Master password used to decrypt values.
        pattern: Glob pattern (default) or regular expression.
        regex: When *True* treat *pattern* as a regular expression.
        keys_only: When *True* only match against keys, not values.

    Returns:
        Mapping of matching key → plaintext value.
    """
    if not pattern:
        raise SearchError("Search pattern must not be empty.")

    all_keys: List[str] = vault.list_keys()
    results: Dict[str, str] = {}

    try:
        compiled = re.compile(pattern) if regex else None
    except re.error as exc:
        raise SearchError(f"Invalid regular expression: {exc}") from exc

    def _matches(text: str) -> bool:
        if regex:
            return bool(compiled.search(text))  # type: ignore[union-attr]
        return fnmatch.fnmatch(text, pattern)

    for key in all_keys:
        key_hit = _matches(key)
        if key_hit:
            results[key] = vault.get(key, password)
            continue
        if not keys_only:
            value: Optional[str] = vault.get(key, password)
            if value is not None and _matches(value):
                results[key] = value

    return results


def list_keys_matching(vault: Vault, pattern: str, *, regex: bool = False) -> List[str]:
    """Return keys that match *pattern* without decrypting values."""
    if not pattern:
        raise SearchError("Search pattern must not be empty.")

    all_keys: List[str] = vault.list_keys()

    try:
        compiled = re.compile(pattern) if regex else None
    except re.error as exc:
        raise SearchError(f"Invalid regular expression: {exc}") from exc

    if regex:
        return [k for k in all_keys if compiled.search(k)]  # type: ignore[union-attr]
    return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
