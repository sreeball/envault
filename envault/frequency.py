"""Track access frequency for vault keys."""

import json
from pathlib import Path
from datetime import datetime, timezone


class FrequencyError(Exception):
    pass


def _frequency_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_frequency.json"


def _load_frequency(vault_path: str) -> dict:
    p = _frequency_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_frequency(vault_path: str, data: dict) -> None:
    _frequency_path(vault_path).write_text(json.dumps(data, indent=2))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_access(vault_path: str, key: str) -> dict:
    """Increment access count for a key and record the last accessed time."""
    data = _load_frequency(vault_path)
    entry = data.get(key, {"count": 0, "first_accessed": _now_iso(), "last_accessed": None})
    entry["count"] += 1
    entry["last_accessed"] = _now_iso()
    data[key] = entry
    _save_frequency(vault_path, data)
    return dict(entry)


def get_frequency(vault_path: str, key: str) -> dict:
    """Return frequency stats for a key."""
    data = _load_frequency(vault_path)
    if key not in data:
        raise FrequencyError(f"No frequency data for key: {key!r}")
    return dict(data[key])


def reset_frequency(vault_path: str, key: str) -> None:
    """Reset frequency data for a key."""
    data = _load_frequency(vault_path)
    if key in data:
        del data[key]
        _save_frequency(vault_path, data)


def list_frequency(vault_path: str, top: int = 0) -> list:
    """Return all keys sorted by access count descending. If top>0, limit results."""
    data = _load_frequency(vault_path)
    entries = [
        {"key": k, **v} for k, v in data.items()
    ]
    entries.sort(key=lambda e: e["count"], reverse=True)
    return entries[:top] if top > 0 else entries
