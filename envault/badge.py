"""Badge generation for vault secrets — produce status badges for keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BadgeError(Exception):
    """Raised when badge operations fail."""


BADGE_STYLES = {"flat", "flat-square", "plastic", "for-the-badge"}
BADGE_COLORS = {"green", "yellow", "red", "blue", "grey", "orange"}


def _badges_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_badges.json"


def _load_badges(vault_path: str) -> dict[str, Any]:
    p = _badges_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_badges(vault_path: str, data: dict[str, Any]) -> None:
    _badges_path(vault_path).write_text(json.dumps(data, indent=2))


def create_badge(
    vault_path: str,
    key: str,
    label: str,
    color: str = "blue",
    style: str = "flat",
) -> dict[str, Any]:
    """Register a badge definition for a secret key."""
    if color not in BADGE_COLORS:
        raise BadgeError(f"Invalid color '{color}'. Choose from: {sorted(BADGE_COLORS)}")
    if style not in BADGE_STYLES:
        raise BadgeError(f"Invalid style '{style}'. Choose from: {sorted(BADGE_STYLES)}")

    data = _load_badges(vault_path)
    entry: dict[str, Any] = {
        "key": key,
        "label": label,
        "color": color,
        "style": style,
    }
    data[key] = entry
    _save_badges(vault_path, data)
    return entry


def remove_badge(vault_path: str, key: str) -> None:
    """Remove a badge definition for the given key."""
    data = _load_badges(vault_path)
    if key not in data:
        raise BadgeError(f"No badge found for key '{key}'")
    del data[key]
    _save_badges(vault_path, data)


def get_badge(vault_path: str, key: str) -> dict[str, Any]:
    """Retrieve the badge definition for a key."""
    data = _load_badges(vault_path)
    if key not in data:
        raise BadgeError(f"No badge found for key '{key}'")
    return data[key]


def list_badges(vault_path: str) -> list[dict[str, Any]]:
    """Return all badge definitions."""
    return list(_load_badges(vault_path).values())
