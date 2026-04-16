import json
from pathlib import Path

VALID_LEVELS = {"low", "medium", "high", "critical"}


class UrgencyError(Exception):
    pass


def _urgency_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_urgency.json"


def _load_urgency(vault_path: str) -> dict:
    p = _urgency_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_urgency(vault_path: str, data: dict) -> None:
    _urgency_path(vault_path).write_text(json.dumps(data, indent=2))


def set_urgency(vault_path: str, key: str, level: str, note: str = "") -> dict:
    if level not in VALID_LEVELS:
        raise UrgencyError(f"Invalid urgency level '{level}'. Must be one of {sorted(VALID_LEVELS)}.")
    data = _load_urgency(vault_path)
    entry = {"level": level, "note": note}
    data[key] = entry
    _save_urgency(vault_path, data)
    return entry


def get_urgency(vault_path: str, key: str) -> dict:
    data = _load_urgency(vault_path)
    if key not in data:
        raise UrgencyError(f"No urgency set for key '{key}'.")
    return data[key]


def remove_urgency(vault_path: str, key: str) -> None:
    data = _load_urgency(vault_path)
    if key not in data:
        raise UrgencyError(f"No urgency set for key '{key}'.")
    del data[key]
    _save_urgency(vault_path, data)


def list_urgency(vault_path: str) -> dict:
    return _load_urgency(vault_path)
