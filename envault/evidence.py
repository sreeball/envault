"""Evidence module: attach proof/evidence entries to vault keys."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


class EvidenceError(Exception):
    pass


def _evidence_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_evidence.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_evidence(vault_path: str) -> dict:
    p = _evidence_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_evidence(vault_path: str, data: dict) -> None:
    _evidence_path(vault_path).write_text(json.dumps(data, indent=2))


def attach(
    vault_path: str,
    key: str,
    description: str,
    source: str = "",
    evidence_type: str = "note",
) -> dict[str, Any]:
    """Attach an evidence entry to a vault key."""
    if not key:
        raise EvidenceError("key must not be empty")
    if not description:
        raise EvidenceError("description must not be empty")

    data = _load_evidence(vault_path)
    entries = data.get(key, [])

    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "type": evidence_type,
        "description": description,
        "source": source,
        "attached_at": _now_iso(),
    }
    entries.append(entry)
    data[key] = entries
    _save_evidence(vault_path, data)
    return entry


def detach(vault_path: str, key: str, evidence_id: str) -> bool:
    """Remove a specific evidence entry by id. Returns True if removed."""
    data = _load_evidence(vault_path)
    entries = data.get(key, [])
    new_entries = [e for e in entries if e["id"] != evidence_id]
    if len(new_entries) == len(entries):
        return False
    data[key] = new_entries
    _save_evidence(vault_path, data)
    return True


def list_evidence(vault_path: str, key: str) -> list[dict]:
    """Return all evidence entries for a key."""
    data = _load_evidence(vault_path)
    return data.get(key, [])


def clear_evidence(vault_path: str, key: str) -> int:
    """Remove all evidence for a key. Returns count removed."""
    data = _load_evidence(vault_path)
    count = len(data.get(key, []))
    data[key] = []
    _save_evidence(vault_path, data)
    return count
