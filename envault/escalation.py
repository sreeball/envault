"""Escalation rules: define conditions under which a key's alert is escalated."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EscalationError(Exception):
    """Raised when an escalation operation fails."""


def _escalation_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_escalation.json"


def _load_escalations(vault_path: str) -> dict[str, Any]:
    p = _escalation_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_escalations(vault_path: str, data: dict[str, Any]) -> None:
    _escalation_path(vault_path).write_text(json.dumps(data, indent=2))


def set_escalation(
    vault_path: str,
    key: str,
    level: str,
    contact: str,
    threshold: int = 1,
    note: str = "",
) -> dict[str, Any]:
    """Set an escalation rule for *key*.

    Args:
        vault_path: Path to the vault file.
        key: Secret key name.
        level: Escalation level, e.g. ``"warning"``, ``"critical"``.
        contact: Person or channel to notify.
        threshold: Number of occurrences before escalating.
        note: Optional free-text note.

    Returns:
        The stored escalation entry.
    """
    valid_levels = {"info", "warning", "critical", "emergency"}
    if level not in valid_levels:
        raise EscalationError(
            f"Invalid level '{level}'. Choose from {sorted(valid_levels)}."
        )
    if threshold < 1:
        raise EscalationError("threshold must be >= 1.")
    if not contact.strip():
        raise EscalationError("contact must not be empty.")

    data = _load_escalations(vault_path)
    entry: dict[str, Any] = {
        "level": level,
        "contact": contact,
        "threshold": threshold,
        "note": note,
    }
    data[key] = entry
    _save_escalations(vault_path, data)
    return entry


def get_escalation(vault_path: str, key: str) -> dict[str, Any] | None:
    """Return the escalation entry for *key*, or ``None`` if not set."""
    return _load_escalations(vault_path).get(key)


def remove_escalation(vault_path: str, key: str) -> None:
    """Remove the escalation rule for *key*."""
    data = _load_escalations(vault_path)
    if key not in data:
        raise EscalationError(f"No escalation rule for '{key}'.")
    del data[key]
    _save_escalations(vault_path, data)


def list_escalations(vault_path: str) -> dict[str, Any]:
    """Return all escalation rules."""
    return _load_escalations(vault_path)
