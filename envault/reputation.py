"""Key reputation scoring based on usage patterns and metadata health."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReputationError(Exception):
    pass


def _reputation_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_reputation.json"


def _load_reputation(vault_path: str) -> dict:
    p = _reputation_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_reputation(vault_path: str, data: dict) -> None:
    _reputation_path(vault_path).write_text(json.dumps(data, indent=2))


def _compute_score(factors: dict[str, Any]) -> int:
    """Compute a 0-100 reputation score from contributing factors."""
    score = 100
    if not factors.get("has_comment", False):
        score -= 10
    if not factors.get("has_label", False):
        score -= 10
    if factors.get("is_expired", False):
        score -= 40
    if factors.get("is_archived", False):
        score -= 20
    if not factors.get("has_schema", False):
        score -= 10
    if factors.get("is_readonly", False):
        score += 5
    return max(0, min(100, score))


def record_reputation(
    vault_path: str,
    key: str,
    factors: dict[str, Any],
) -> dict:
    """Record reputation entry for *key* derived from *factors*.

    Returns the stored entry dict.
    """
    if not key:
        raise ReputationError("key must not be empty")

    score = _compute_score(factors)
    entry = {"key": key, "score": score, "factors": factors}

    data = _load_reputation(vault_path)
    data[key] = entry
    _save_reputation(vault_path, data)
    return entry


def get_reputation(vault_path: str, key: str) -> dict:
    """Return the reputation entry for *key*, or raise ReputationError."""
    data = _load_reputation(vault_path)
    if key not in data:
        raise ReputationError(f"no reputation record for key '{key}'")
    return data[key]


def list_reputation(vault_path: str) -> list[dict]:
    """Return all reputation entries sorted by score ascending."""
    data = _load_reputation(vault_path)
    return sorted(data.values(), key=lambda e: e["score"])


def remove_reputation(vault_path: str, key: str) -> None:
    """Remove the reputation record for *key*."""
    data = _load_reputation(vault_path)
    if key not in data:
        raise ReputationError(f"no reputation record for key '{key}'")
    del data[key]
    _save_reputation(vault_path, data)
