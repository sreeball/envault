"""Trust scoring for vault keys based on metadata health."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TrustError(Exception):
    """Raised when a trust operation fails."""


TRUST_LEVELS = ("untrusted", "low", "medium", "high", "verified")


def _trust_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_trust.json"


def _load_trust(vault_path: str) -> dict:
    p = _trust_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_trust(vault_path: str, data: dict) -> None:
    _trust_path(vault_path).write_text(json.dumps(data, indent=2))


def _compute_level(score: int) -> str:
    if score >= 90:
        return "verified"
    if score >= 70:
        return "high"
    if score >= 50:
        return "medium"
    if score >= 25:
        return "low"
    return "untrusted"


def evaluate_trust(
    vault_path: str,
    key: str,
    *,
    has_comment: bool = False,
    has_label: bool = False,
    has_schema: bool = False,
    has_owner: bool = False,
    has_ttl: bool = False,
) -> dict[str, Any]:
    """Compute a trust score for *key* based on metadata factors.

    Returns a dict with ``score`` (0-100), ``level``, and ``factors``.
    """
    factors: dict[str, bool] = {
        "has_comment": has_comment,
        "has_label": has_label,
        "has_schema": has_schema,
        "has_owner": has_owner,
        "has_ttl": has_ttl,
    }
    weights = {
        "has_comment": 15,
        "has_label": 15,
        "has_schema": 30,
        "has_owner": 25,
        "has_ttl": 15,
    }
    score = sum(weights[k] for k, v in factors.items() if v)
    level = _compute_level(score)
    entry: dict[str, Any] = {"score": score, "level": level, "factors": factors}

    data = _load_trust(vault_path)
    data[key] = entry
    _save_trust(vault_path, data)
    return entry


def get_trust(vault_path: str, key: str) -> dict[str, Any]:
    """Return the stored trust entry for *key*, or raise TrustError."""
    data = _load_trust(vault_path)
    if key not in data:
        raise TrustError(f"No trust record for key: {key!r}")
    return data[key]


def list_trust(vault_path: str) -> dict[str, dict[str, Any]]:
    """Return all trust records."""
    return _load_trust(vault_path)


def remove_trust(vault_path: str, key: str) -> None:
    """Delete the trust record for *key*."""
    data = _load_trust(vault_path)
    if key not in data:
        raise TrustError(f"No trust record for key: {key!r}")
    del data[key]
    _save_trust(vault_path, data)
