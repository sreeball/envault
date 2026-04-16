"""Track and report staleness of secrets based on last-modified time."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

STALENESS_FILE = ".envault_staleness.json"


class StalenessError(Exception):
    pass


def _staleness_path(vault_path: str) -> Path:
    return Path(vault_path).parent / STALENESS_FILE


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_staleness(vault_path: str) -> dict:
    p = _staleness_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_staleness(vault_path: str, data: dict) -> None:
    _staleness_path(vault_path).write_text(json.dumps(data, indent=2))


def record_update(vault_path: str, key: str) -> dict:
    """Record that a key was just updated."""
    data = _load_staleness(vault_path)
    entry = {"key": key, "last_updated": _now_iso()}
    data[key] = entry
    _save_staleness(vault_path, data)
    return entry


def get_staleness(vault_path: str, key: str, max_age_days: int = 90) -> dict:
    """Return staleness info for a key."""
    data = _load_staleness(vault_path)
    if key not in data:
        return {"key": key, "stale": None, "last_updated": None, "age_days": None}
    last_updated = datetime.fromisoformat(data[key]["last_updated"])
    now = datetime.now(timezone.utc)
    age = (now - last_updated).days
    return {
        "key": key,
        "last_updated": data[key]["last_updated"],
        "age_days": age,
        "stale": age > max_age_days,
    }


def list_stale(vault_path: str, max_age_days: int = 90) -> list:
    """Return all keys older than max_age_days."""
    data = _load_staleness(vault_path)
    now = datetime.now(timezone.utc)
    stale = []
    for key, entry in data.items():
        last_updated = datetime.fromisoformat(entry["last_updated"])
        age = (now - last_updated).days
        if age > max_age_days:
            stale.append({"key": key, "last_updated": entry["last_updated"], "age_days": age})
    return stale


def remove_record(vault_path: str, key: str) -> bool:
    """Remove staleness record for a key. Returns True if removed."""
    data = _load_staleness(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_staleness(vault_path, data)
    return True
