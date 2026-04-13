"""Mark vault keys as favorites for quick access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class FavoriteError(Exception):
    """Raised when a favorite operation fails."""


def _favorites_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_favorites.json"


def _load_favorites(vault_path: str) -> Dict[str, dict]:
    p = _favorites_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_favorites(vault_path: str, data: Dict[str, dict]) -> None:
    _favorites_path(vault_path).write_text(json.dumps(data, indent=2))


def add_favorite(vault_path: str, key: str, note: str = "") -> dict:
    """Mark *key* as a favorite, optionally with a note."""
    favs = _load_favorites(vault_path)
    entry = {"key": key, "note": note}
    favs[key] = entry
    _save_favorites(vault_path, favs)
    return entry


def remove_favorite(vault_path: str, key: str) -> None:
    """Remove *key* from favorites. Raises FavoriteError if not found."""
    favs = _load_favorites(vault_path)
    if key not in favs:
        raise FavoriteError(f"Key '{key}' is not a favorite.")
    del favs[key]
    _save_favorites(vault_path, favs)


def list_favorites(vault_path: str) -> List[dict]:
    """Return all favorites as a list of entry dicts."""
    return list(_load_favorites(vault_path).values())


def is_favorite(vault_path: str, key: str) -> bool:
    """Return True if *key* is currently marked as a favorite."""
    return key in _load_favorites(vault_path)
