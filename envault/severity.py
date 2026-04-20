"""Severity levels for vault secrets."""

from __future__ import annotations

import json
from pathlib import Path

VALID_LEVELS = ("low", "medium", "high", "critical")


class SeverityError(Exception):
    """Raised when a severity operation fails."""


def _severity_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_severity.json"


def _load_severity(vault_path: str) -> dict:
    p = _severity_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_severity(vault_path: str, data: dict) -> None:
    _severity_path(vault_path).write_text(json.dumps(data, indent=2))


def set_severity(vault_path: str, key: str, level: str, note: str = "") -> dict:
    """Assign a severity level to a secret key."""
    if level not in VALID_LEVELS:
        raise SeverityError(
            f"Invalid severity level '{level}'. Choose from: {', '.join(VALID_LEVELS)}"
        )
    data = _load_severity(vault_path)
    entry = {"level": level, "note": note}
    data[key] = entry
    _save_severity(vault_path, data)
    return entry


def get_severity(vault_path: str, key: str) -> dict | None:
    """Return the severity entry for a key, or None if not set."""
    return _load_severity(vault_path).get(key)


def remove_severity(vault_path: str, key: str) -> bool:
    """Remove the severity entry for a key. Returns True if removed."""
    data = _load_severity(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_severity(vault_path, data)
    return True


def list_severity(vault_path: str) -> dict:
    """Return all severity entries."""
    return _load_severity(vault_path)
