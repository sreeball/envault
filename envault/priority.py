"""Priority management for vault keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

VALID_LEVELS = ("critical", "high", "normal", "low")


class PriorityError(Exception):
    pass


def _priority_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_priority.json"


def _load_priorities(vault_path: str) -> Dict[str, str]:
    p = _priority_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_priorities(vault_path: str, data: Dict[str, str]) -> None:
    _priority_path(vault_path).write_text(json.dumps(data, indent=2))


def set_priority(vault_path: str, key: str, level: str) -> Dict[str, str]:
    """Assign a priority level to a key."""
    if level not in VALID_LEVELS:
        raise PriorityError(
            f"Invalid priority '{level}'. Choose from: {', '.join(VALID_LEVELS)}"
        )
    data = _load_priorities(vault_path)
    data[key] = level
    _save_priorities(vault_path, data)
    return {"key": key, "priority": level}


def get_priority(vault_path: str, key: str) -> Optional[str]:
    """Return the priority level for a key, or None if unset."""
    return _load_priorities(vault_path).get(key)


def remove_priority(vault_path: str, key: str) -> None:
    """Remove the priority entry for a key."""
    data = _load_priorities(vault_path)
    if key not in data:
        raise PriorityError(f"No priority set for key '{key}'")
    del data[key]
    _save_priorities(vault_path, data)


def list_by_priority(vault_path: str, level: Optional[str] = None) -> List[Dict[str, str]]:
    """Return all keys with their priorities, optionally filtered by level."""
    data = _load_priorities(vault_path)
    results = [{"key": k, "priority": v} for k, v in data.items()]
    if level is not None:
        if level not in VALID_LEVELS:
            raise PriorityError(
                f"Invalid priority '{level}'. Choose from: {', '.join(VALID_LEVELS)}"
            )
        results = [r for r in results if r["priority"] == level]
    order = {lvl: i for i, lvl in enumerate(VALID_LEVELS)}
    results.sort(key=lambda r: order[r["priority"]])
    return results
