"""Track and query the impact level of secrets within projects."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

VALID_LEVELS = ("low", "medium", "high", "critical")


class ImpactError(Exception):
    pass


def _impact_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_impact.json"


def _load_impact(vault_path: str) -> Dict[str, Any]:
    p = _impact_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_impact(vault_path: str, data: Dict[str, Any]) -> None:
    _impact_path(vault_path).write_text(json.dumps(data, indent=2))


def set_impact(vault_path: str, key: str, level: str, note: str = "") -> Dict[str, Any]:
    """Assign an impact level to a secret key."""
    if level not in VALID_LEVELS:
        raise ImpactError(f"Invalid level '{level}'. Choose from: {', '.join(VALID_LEVELS)}")
    data = _load_impact(vault_path)
    entry = {"level": level, "note": note}
    data[key] = entry
    _save_impact(vault_path, data)
    return entry


def get_impact(vault_path: str, key: str) -> Optional[Dict[str, Any]]:
    """Return the impact entry for a key, or None if not set."""
    return _load_impact(vault_path).get(key)


def remove_impact(vault_path: str, key: str) -> bool:
    """Remove the impact entry for a key. Returns True if removed."""
    data = _load_impact(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_impact(vault_path, data)
    return True


def list_impact(vault_path: str) -> Dict[str, Any]:
    """Return all impact entries."""
    return _load_impact(vault_path)


def keys_by_level(vault_path: str, level: str) -> list:
    """Return all keys with the given impact level."""
    if level not in VALID_LEVELS:
        raise ImpactError(f"Invalid level '{level}'. Choose from: {', '.join(VALID_LEVELS)}")
    data = _load_impact(vault_path)
    return [k for k, v in data.items() if v.get("level") == level]
