"""Sensitivity level management for vault keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

SENSITIVITY_LEVELS = ("public", "internal", "confidential", "secret", "top-secret")


class SensitivityError(Exception):
    pass


def _sensitivity_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_sensitivity.json"


def _load_sensitivity(vault_path: str) -> Dict:
    p = _sensitivity_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_sensitivity(vault_path: str, data: Dict) -> None:
    _sensitivity_path(vault_path).write_text(json.dumps(data, indent=2))


def set_sensitivity(vault_path: str, key: str, level: str, note: str = "") -> Dict:
    """Assign a sensitivity level to a key."""
    if level not in SENSITIVITY_LEVELS:
        raise SensitivityError(
            f"Invalid level '{level}'. Choose from: {', '.join(SENSITIVITY_LEVELS)}"
        )
    data = _load_sensitivity(vault_path)
    entry = {"level": level, "note": note}
    data[key] = entry
    _save_sensitivity(vault_path, data)
    return entry


def get_sensitivity(vault_path: str, key: str) -> Optional[Dict]:
    """Return the sensitivity entry for a key, or None."""
    return _load_sensitivity(vault_path).get(key)


def remove_sensitivity(vault_path: str, key: str) -> bool:
    """Remove sensitivity record for a key. Returns True if removed."""
    data = _load_sensitivity(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_sensitivity(vault_path, data)
    return True


def list_sensitivity(vault_path: str) -> Dict[str, Dict]:
    """Return all sensitivity records."""
    return _load_sensitivity(vault_path)


def keys_at_level(vault_path: str, level: str) -> List[str]:
    """Return all keys assigned the given sensitivity level."""
    if level not in SENSITIVITY_LEVELS:
        raise SensitivityError(
            f"Invalid level '{level}'. Choose from: {', '.join(SENSITIVITY_LEVELS)}"
        )
    data = _load_sensitivity(vault_path)
    return [k for k, v in data.items() if v["level"] == level]
