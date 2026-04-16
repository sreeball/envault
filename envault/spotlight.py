"""Spotlight: mark and retrieve featured/highlighted secrets."""

import json
from pathlib import Path

SPOTLIGHT_FILE = ".envault_spotlight.json"


class SpotlightError(Exception):
    pass


def _spotlight_path(vault_path: str) -> Path:
    return Path(vault_path).parent / SPOTLIGHT_FILE


def _load_spotlight(vault_path: str) -> dict:
    p = _spotlight_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_spotlight(vault_path: str, data: dict) -> None:
    _spotlight_path(vault_path).write_text(json.dumps(data, indent=2))


def highlight(vault_path: str, key: str, reason: str = "") -> dict:
    """Mark a key as highlighted/featured."""
    data = _load_spotlight(vault_path)
    entry = {"key": key, "reason": reason, "featured": True}
    data[key] = entry
    _save_spotlight(vault_path, data)
    return entry


def remove_highlight(vault_path: str, key: str) -> None:
    """Remove a key from the spotlight."""
    data = _load_spotlight(vault_path)
    if key not in data:
        raise SpotlightError(f"Key '{key}' is not highlighted.")
    del data[key]
    _save_spotlight(vault_path, data)


def get_highlighted(vault_path: str) -> dict:
    """Return all highlighted keys."""
    return _load_spotlight(vault_path)


def is_highlighted(vault_path: str, key: str) -> bool:
    """Check whether a key is currently highlighted."""
    return key in _load_spotlight(vault_path)
