"""Maturity tracking for vault secrets."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Optional

MATURITY_LEVELS = ("experimental", "beta", "stable", "deprecated")


class MaturityError(Exception):
    pass


def _maturity_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".maturity.json"


def _load_maturity(vault_path: str) -> Dict[str, Any]:
    p = _maturity_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_maturity(vault_path: str, data: Dict[str, Any]) -> None:
    _maturity_path(vault_path).write_text(json.dumps(data, indent=2))


def set_maturity(vault_path: str, key: str, level: str, note: str = "") -> Dict[str, Any]:
    """Set the maturity level for a secret key."""
    if level not in MATURITY_LEVELS:
        raise MaturityError(f"Invalid level '{level}'. Choose from: {MATURITY_LEVELS}")
    data = _load_maturity(vault_path)
    entry = {"level": level, "note": note}
    data[key] = entry
    _save_maturity(vault_path, data)
    return entry


def get_maturity(vault_path: str, key: str) -> Optional[Dict[str, Any]]:
    """Get the maturity entry for a key, or None if not set."""
    return _load_maturity(vault_path).get(key)


def remove_maturity(vault_path: str, key: str) -> bool:
    """Remove maturity entry for a key. Returns True if removed."""
    data = _load_maturity(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_maturity(vault_path, data)
    return True


def list_maturity(vault_path: str) -> Dict[str, Any]:
    """Return all maturity entries."""
    return _load_maturity(vault_path)


def keys_at_level(vault_path: str, level: str) -> list:
    """Return all keys at a given maturity level."""
    if level not in MATURITY_LEVELS:
        raise MaturityError(f"Invalid level '{level}'. Choose from: {MATURITY_LEVELS}")
    data = _load_maturity(vault_path)
    return [k for k, v in data.items() if v["level"] == level]
