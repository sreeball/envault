import json
from pathlib import Path
from typing import Optional


class ConfidenceError(Exception):
    pass


VALID_LEVELS = ("low", "medium", "high")


def _confidence_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_confidence.json"


def _load_confidence(vault_path: str) -> dict:
    p = _confidence_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_confidence(vault_path: str, data: dict) -> None:
    _confidence_path(vault_path).write_text(json.dumps(data, indent=2))


def set_confidence(vault_path: str, key: str, level: str, note: str = "") -> dict:
    """Record a confidence level for a secret key."""
    if level not in VALID_LEVELS:
        raise ConfidenceError(f"Invalid level '{level}'. Must be one of {VALID_LEVELS}.")
    data = _load_confidence(vault_path)
    entry = {"level": level, "note": note}
    data[key] = entry
    _save_confidence(vault_path, data)
    return entry


def get_confidence(vault_path: str, key: str) -> Optional[dict]:
    """Return confidence entry for key, or None if not set."""
    return _load_confidence(vault_path).get(key)


def remove_confidence(vault_path: str, key: str) -> bool:
    """Remove confidence entry for key. Returns True if removed."""
    data = _load_confidence(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_confidence(vault_path, data)
    return True


def list_confidence(vault_path: str) -> dict:
    """Return all confidence entries."""
    return _load_confidence(vault_path)
