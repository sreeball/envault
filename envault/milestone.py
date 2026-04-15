"""Milestone tracking for vault secrets and projects."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


class MilestoneError(Exception):
    pass


def _milestones_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault" / "milestones.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_milestones(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_milestones(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def create_milestone(
    vault_path: str,
    name: str,
    description: str = "",
    due_date: str | None = None,
) -> dict[str, Any]:
    """Create a named milestone, optionally with a due date (ISO string)."""
    path = _milestones_path(vault_path)
    milestones = _load_milestones(path)
    if name in milestones:
        raise MilestoneError(f"Milestone '{name}' already exists.")
    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "created_at": _now_iso(),
        "due_date": due_date,
        "completed_at": None,
    }
    milestones[name] = entry
    _save_milestones(path, milestones)
    return entry


def complete_milestone(vault_path: str, name: str) -> dict[str, Any]:
    """Mark a milestone as completed."""
    path = _milestones_path(vault_path)
    milestones = _load_milestones(path)
    if name not in milestones:
        raise MilestoneError(f"Milestone '{name}' not found.")
    milestones[name]["completed_at"] = _now_iso()
    _save_milestones(path, milestones)
    return milestones[name]


def delete_milestone(vault_path: str, name: str) -> None:
    """Remove a milestone by name."""
    path = _milestones_path(vault_path)
    milestones = _load_milestones(path)
    if name not in milestones:
        raise MilestoneError(f"Milestone '{name}' not found.")
    del milestones[name]
    _save_milestones(path, milestones)


def list_milestones(vault_path: str) -> list[dict[str, Any]]:
    """Return all milestones sorted by creation date."""
    path = _milestones_path(vault_path)
    milestones = _load_milestones(path)
    return sorted(milestones.values(), key=lambda e: e["created_at"])
