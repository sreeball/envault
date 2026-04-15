"""Compliance tracking for vault secrets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ComplianceError(Exception):
    pass


def _compliance_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_compliance.json"


def _load_compliance(vault_path: str) -> dict:
    p = _compliance_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_compliance(vault_path: str, data: dict) -> None:
    _compliance_path(vault_path).write_text(json.dumps(data, indent=2))


def tag_compliant(
    vault_path: str,
    key: str,
    standard: str,
    control_id: str,
    note: str = "",
) -> dict:
    """Tag a secret key as compliant with a given standard and control."""
    if not standard:
        raise ComplianceError("standard must not be empty")
    if not control_id:
        raise ComplianceError("control_id must not be empty")

    data = _load_compliance(vault_path)
    if key not in data:
        data[key] = []

    entry: dict[str, Any] = {
        "standard": standard,
        "control_id": control_id,
        "note": note,
    }
    data[key].append(entry)
    _save_compliance(vault_path, data)
    return entry


def remove_compliance(vault_path: str, key: str, standard: str) -> list:
    """Remove all compliance entries for a key under a given standard."""
    data = _load_compliance(vault_path)
    if key not in data:
        raise ComplianceError(f"no compliance entries for key '{key}'")
    data[key] = [e for e in data[key] if e["standard"] != standard]
    _save_compliance(vault_path, data)
    return data[key]


def get_compliance(vault_path: str, key: str) -> list:
    """Return all compliance entries for a key."""
    data = _load_compliance(vault_path)
    return data.get(key, [])


def list_compliance(vault_path: str) -> dict:
    """Return the full compliance mapping."""
    return _load_compliance(vault_path)
