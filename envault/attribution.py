"""Track attribution (creator/modifier) metadata for vault keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class AttributionError(Exception):
    """Raised when an attribution operation fails."""


def _attribution_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault" / "attribution.json"


def _load_attribution(vault_path: str) -> Dict:
    p = _attribution_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_attribution(vault_path: str, data: Dict) -> None:
    p = _attribution_path(vault_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def set_attribution(
    vault_path: str,
    key: str,
    actor: str,
    *,
    team: Optional[str] = None,
    note: Optional[str] = None,
) -> Dict:
    """Record who is responsible for a given key."""
    if not key:
        raise AttributionError("key must not be empty")
    if not actor:
        raise AttributionError("actor must not be empty")

    data = _load_attribution(vault_path)
    entry = {"actor": actor, "team": team or "", "note": note or ""}
    data[key] = entry
    _save_attribution(vault_path, data)
    return entry


def get_attribution(vault_path: str, key: str) -> Optional[Dict]:
    """Return attribution entry for *key*, or None if not set."""
    data = _load_attribution(vault_path)
    return data.get(key)


def remove_attribution(vault_path: str, key: str) -> bool:
    """Remove attribution for *key*. Returns True if removed, False if absent."""
    data = _load_attribution(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_attribution(vault_path, data)
    return True


def list_attributions(vault_path: str) -> List[Dict]:
    """Return all attribution entries as a list of dicts with 'key' included."""
    data = _load_attribution(vault_path)
    return [{"key": k, **v} for k, v in data.items()]
