"""Consent management for environment variable access."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class ConsentError(Exception):
    pass


def _consent_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_consent.json"


def _load_consents(vault_path: str) -> Dict:
    p = _consent_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_consents(vault_path: str, data: Dict) -> None:
    _consent_path(vault_path).write_text(json.dumps(data, indent=2))


def grant_consent(vault_path: str, key: str, actor: str, purpose: str, note: str = "") -> Dict:
    """Record that an actor has consented to access a key for a given purpose."""
    if not key:
        raise ConsentError("key must not be empty")
    if not actor:
        raise ConsentError("actor must not be empty")
    if not purpose:
        raise ConsentError("purpose must not be empty")

    data = _load_consents(vault_path)
    if key not in data:
        data[key] = []

    entry = {"actor": actor, "purpose": purpose, "note": note}
    # Avoid duplicates for same actor+purpose
    for existing in data[key]:
        if existing["actor"] == actor and existing["purpose"] == purpose:
            existing["note"] = note
            _save_consents(vault_path, data)
            return existing

    data[key].append(entry)
    _save_consents(vault_path, data)
    return entry


def revoke_consent(vault_path: str, key: str, actor: str, purpose: Optional[str] = None) -> int:
    """Revoke consent for an actor on a key. Returns number of entries removed."""
    data = _load_consents(vault_path)
    if key not in data:
        return 0

    before = len(data[key])
    if purpose:
        data[key] = [e for e in data[key] if not (e["actor"] == actor and e["purpose"] == purpose)]
    else:
        data[key] = [e for e in data[key] if e["actor"] != actor]

    removed = before - len(data[key])
    if not data[key]:
        del data[key]
    _save_consents(vault_path, data)
    return removed


def get_consents(vault_path: str, key: str) -> List[Dict]:
    """Return all consent entries for a key."""
    data = _load_consents(vault_path)
    return data.get(key, [])


def has_consent(vault_path: str, key: str, actor: str, purpose: str) -> bool:
    """Check whether a specific actor has consented for a given purpose."""
    for entry in get_consents(vault_path, key):
        if entry["actor"] == actor and entry["purpose"] == purpose:
            return True
    return False


def list_all_consents(vault_path: str) -> Dict:
    """Return the full consent registry."""
    return _load_consents(vault_path)
