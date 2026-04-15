"""Secret rating — attach a star rating and optional review to a key."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List


class RatingError(Exception):
    """Raised when a rating operation fails."""


def _ratings_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_ratings.json"


def _load_ratings(vault_path: str) -> Dict[str, Any]:
    p = _ratings_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_ratings(vault_path: str, data: Dict[str, Any]) -> None:
    _ratings_path(vault_path).write_text(json.dumps(data, indent=2))


def rate_key(
    vault_path: str,
    key: str,
    stars: int,
    review: str = "",
) -> Dict[str, Any]:
    """Assign a 1-5 star rating (and optional review) to *key*."""
    if stars < 1 or stars > 5:
        raise RatingError(f"stars must be between 1 and 5, got {stars}")
    data = _load_ratings(vault_path)
    entry: Dict[str, Any] = {"key": key, "stars": stars, "review": review}
    data[key] = entry
    _save_ratings(vault_path, data)
    return entry


def get_rating(vault_path: str, key: str) -> Dict[str, Any]:
    """Return the rating entry for *key*, or raise RatingError if absent."""
    data = _load_ratings(vault_path)
    if key not in data:
        raise RatingError(f"no rating found for key '{key}'")
    return data[key]


def remove_rating(vault_path: str, key: str) -> None:
    """Remove the rating for *key* if it exists."""
    data = _load_ratings(vault_path)
    data.pop(key, None)
    _save_ratings(vault_path, data)


def list_ratings(vault_path: str) -> List[Dict[str, Any]]:
    """Return all rating entries sorted by stars descending."""
    data = _load_ratings(vault_path)
    return sorted(data.values(), key=lambda e: e["stars"], reverse=True)
