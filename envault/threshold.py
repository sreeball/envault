"""Threshold management for envault secrets.

Allows setting numeric thresholds on secret values with comparison operators.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

VALID_OPERATORS = ("lt", "lte", "gt", "gte", "eq", "ne")


class ThresholdError(Exception):
    """Raised when a threshold operation fails."""


def _threshold_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_thresholds.json"


def _load_thresholds(vault_path: str) -> Dict[str, Any]:
    p = _threshold_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_thresholds(vault_path: str, data: Dict[str, Any]) -> None:
    _threshold_path(vault_path).write_text(json.dumps(data, indent=2))


def set_threshold(
    vault_path: str,
    key: str,
    operator: str,
    value: float,
    note: str = "",
) -> Dict[str, Any]:
    """Set a numeric threshold on a secret key."""
    if operator not in VALID_OPERATORS:
        raise ThresholdError(
            f"Invalid operator '{operator}'. Must be one of: {', '.join(VALID_OPERATORS)}"
        )
    data = _load_thresholds(vault_path)
    entry = {"operator": operator, "value": value, "note": note}
    data[key] = entry
    _save_thresholds(vault_path, data)
    return entry


def get_threshold(vault_path: str, key: str) -> Optional[Dict[str, Any]]:
    """Return the threshold entry for *key*, or None if not set."""
    return _load_thresholds(vault_path).get(key)


def remove_threshold(vault_path: str, key: str) -> bool:
    """Remove the threshold for *key*. Returns True if it existed."""
    data = _load_thresholds(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_thresholds(vault_path, data)
    return True


def list_thresholds(vault_path: str) -> List[Dict[str, Any]]:
    """Return all threshold entries as a list of dicts with the key included."""
    data = _load_thresholds(vault_path)
    return [{"key": k, **v} for k, v in data.items()]


def check_threshold(vault_path: str, key: str, actual: float) -> bool:
    """Return True if *actual* satisfies the stored threshold for *key*."""
    entry = get_threshold(vault_path, key)
    if entry is None:
        raise ThresholdError(f"No threshold defined for key '{key}'")
    op, limit = entry["operator"], entry["value"]
    return {
        "lt": actual < limit,
        "lte": actual <= limit,
        "gt": actual > limit,
        "gte": actual >= limit,
        "eq": actual == limit,
        "ne": actual != limit,
    }[op]
