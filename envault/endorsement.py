"""Endorsement module — allow users to endorse secrets as verified/trusted."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


class EndorsementError(Exception):
    """Raised when an endorsement operation fails."""


def _endorsements_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault" / "endorsements.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_endorsements(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_endorsements(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def endorse(vault_path: str, key: str, endorser: str, note: str = "") -> dict:
    """Endorse a secret key as verified by the given endorser."""
    if not key:
        raise EndorsementError("key must not be empty")
    if not endorser:
        raise EndorsementError("endorser must not be empty")

    path = _endorsements_path(vault_path)
    data = _load_endorsements(path)

    entry = {
        "endorser": endorser,
        "note": note,
        "endorsed_at": _now_iso(),
    }
    data.setdefault(key, []).append(entry)
    _save_endorsements(path, data)
    return entry


def revoke(vault_path: str, key: str, endorser: str) -> int:
    """Remove all endorsements by the given endorser for a key. Returns removed count."""
    path = _endorsements_path(vault_path)
    data = _load_endorsements(path)
    original = data.get(key, [])
    updated = [e for e in original if e["endorser"] != endorser]
    removed = len(original) - len(updated)
    if updated:
        data[key] = updated
    elif key in data:
        del data[key]
    _save_endorsements(path, data)
    return removed


def get_endorsements(vault_path: str, key: str) -> list[dict[str, Any]]:
    """Return all endorsements for a given key."""
    path = _endorsements_path(vault_path)
    data = _load_endorsements(path)
    return data.get(key, [])


def list_endorsed_keys(vault_path: str) -> list[str]:
    """Return all keys that have at least one endorsement."""
    path = _endorsements_path(vault_path)
    data = _load_endorsements(path)
    return [k for k, v in data.items() if v]
