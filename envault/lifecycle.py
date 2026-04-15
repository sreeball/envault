"""Lifecycle management for vault secrets (draft → active → deprecated → archived)."""

import json
from pathlib import Path
from typing import Optional

VALID_STATES = ("draft", "active", "deprecated", "archived")
VALID_TRANSITIONS = {
    "draft": ("active",),
    "active": ("deprecated", "archived"),
    "deprecated": ("archived",),
    "archived": (),
}


class LifecycleError(Exception):
    pass


def _lifecycle_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_lifecycle.json"


def _load_lifecycle(vault_path: str) -> dict:
    p = _lifecycle_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_lifecycle(vault_path: str, data: dict) -> None:
    _lifecycle_path(vault_path).write_text(json.dumps(data, indent=2))


def set_state(vault_path: str, key: str, state: str, note: Optional[str] = None) -> dict:
    """Set the lifecycle state of a key, enforcing valid transitions."""
    if state not in VALID_STATES:
        raise LifecycleError(f"Invalid state '{state}'. Choose from: {', '.join(VALID_STATES)}")

    data = _load_lifecycle(vault_path)
    current = data.get(key, {}).get("state", "draft")

    if state != current and state not in VALID_TRANSITIONS.get(current, ()):
        raise LifecycleError(
            f"Cannot transition '{key}' from '{current}' to '{state}'. "
            f"Allowed: {VALID_TRANSITIONS.get(current, ())}"
        )

    entry = {"state": state, "note": note or ""}
    data[key] = entry
    _save_lifecycle(vault_path, data)
    return entry


def get_state(vault_path: str, key: str) -> dict:
    """Return the lifecycle entry for a key, defaulting to 'draft'."""
    data = _load_lifecycle(vault_path)
    return data.get(key, {"state": "draft", "note": ""})


def remove_state(vault_path: str, key: str) -> bool:
    """Remove lifecycle tracking for a key. Returns True if removed."""
    data = _load_lifecycle(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_lifecycle(vault_path, data)
    return True


def list_states(vault_path: str) -> dict:
    """Return all tracked lifecycle states."""
    return _load_lifecycle(vault_path)
