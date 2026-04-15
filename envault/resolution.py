"""Resolution order and value lookup across multiple vaults or sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envault.vault import Vault


class ResolutionError(Exception):
    """Raised when resolution encounters an error."""


def _resolution_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_resolution.json"


def _load_resolution(vault_path: str) -> dict:
    p = _resolution_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_resolution(vault_path: str, data: dict) -> None:
    _resolution_path(vault_path).write_text(json.dumps(data, indent=2))


def set_resolution_order(vault_path: str, key: str, sources: list[str]) -> dict:
    """Define the ordered list of source vault paths to resolve *key* from."""
    if not sources:
        raise ResolutionError("sources list must not be empty")
    data = _load_resolution(vault_path)
    data[key] = {"sources": sources}
    _save_resolution(vault_path, data)
    return {"key": key, "sources": sources}


def get_resolution_order(vault_path: str, key: str) -> list[str]:
    """Return the resolution source order for *key*, or empty list if not set."""
    data = _load_resolution(vault_path)
    return data.get(key, {}).get("sources", [])


def remove_resolution(vault_path: str, key: str) -> bool:
    """Remove the resolution order entry for *key*. Returns True if removed."""
    data = _load_resolution(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_resolution(vault_path, data)
    return True


def resolve_value(vault_path: str, key: str, password: str) -> Any:
    """Resolve *key* by walking the configured source vaults in order.

    Falls back to the primary vault if no resolution order is configured.
    Raises ResolutionError if the key cannot be found in any source.
    """
    sources = get_resolution_order(vault_path, key)
    search_paths = sources if sources else [vault_path]

    for src in search_paths:
        try:
            v = Vault(src, password)
            value = v.get(key)
            if value is not None:
                return value
        except Exception:
            continue

    raise ResolutionError(f"key '{key}' could not be resolved from any source")


def list_resolution(vault_path: str) -> dict:
    """Return the full resolution order map."""
    return _load_resolution(vault_path)
