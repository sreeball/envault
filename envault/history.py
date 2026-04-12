"""Track a change history log per secret key in the vault."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HistoryError(Exception):
    """Raised when a history operation fails."""


def _history_path(vault_path: str | Path) -> Path:
    return Path(vault_path).parent / ".envault_history.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_history(vault_path: str | Path) -> dict[str, list[dict]]:
    path = _history_path(vault_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise HistoryError(f"Failed to load history: {exc}") from exc


def _save_history(vault_path: str | Path, data: dict) -> None:
    path = _history_path(vault_path)
    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise HistoryError(f"Failed to save history: {exc}") from exc


def record_change(
    vault_path: str | Path,
    key: str,
    action: str,
    actor: str = "user",
    note: str = "",
) -> dict[str, Any]:
    """Append a change entry for *key* and return the new entry.

    Parameters
    ----------
    vault_path: path to the vault file.
    key:        the secret key that changed.
    action:     one of 'set', 'delete', 'rotate', 'import'.
    actor:      who or what triggered the change (default 'user').
    note:       optional free-text annotation.
    """
    valid_actions = {"set", "delete", "rotate", "import"}
    if action not in valid_actions:
        raise HistoryError(f"Invalid action '{action}'. Must be one of {valid_actions}.")

    data = _load_history(vault_path)
    entry: dict[str, Any] = {
        "action": action,
        "actor": actor,
        "timestamp": _now_iso(),
        "note": note,
    }
    data.setdefault(key, []).append(entry)
    _save_history(vault_path, data)
    return entry


def get_history(vault_path: str | Path, key: str) -> list[dict]:
    """Return all recorded changes for *key*, oldest first."""
    data = _load_history(vault_path)
    return list(data.get(key, []))


def clear_history(vault_path: str | Path, key: str) -> int:
    """Remove all history entries for *key*. Returns the number of entries removed."""
    data = _load_history(vault_path)
    removed = len(data.pop(key, []))
    _save_history(vault_path, data)
    return removed


def all_keys_with_history(vault_path: str | Path) -> list[str]:
    """Return a sorted list of keys that have at least one history entry."""
    return sorted(_load_history(vault_path).keys())
