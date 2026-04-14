"""Workflow automation: chain multiple vault operations into named workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WorkflowError(Exception):
    pass


def _workflows_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_workflows.json"


def _load_workflows(vault_path: str) -> dict:
    p = _workflows_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_workflows(vault_path: str, data: dict) -> None:
    _workflows_path(vault_path).write_text(json.dumps(data, indent=2))


def create_workflow(vault_path: str, name: str, steps: list[str], description: str = "") -> dict:
    """Register a named workflow with an ordered list of CLI step strings."""
    if not name or not name.strip():
        raise WorkflowError("Workflow name must not be empty.")
    if not steps:
        raise WorkflowError("Workflow must contain at least one step.")
    data = _load_workflows(vault_path)
    if name in data:
        raise WorkflowError(f"Workflow '{name}' already exists.")
    entry: dict[str, Any] = {"name": name, "steps": steps, "description": description}
    data[name] = entry
    _save_workflows(vault_path, data)
    return entry


def delete_workflow(vault_path: str, name: str) -> None:
    data = _load_workflows(vault_path)
    if name not in data:
        raise WorkflowError(f"Workflow '{name}' not found.")
    del data[name]
    _save_workflows(vault_path, data)


def get_workflow(vault_path: str, name: str) -> dict:
    data = _load_workflows(vault_path)
    if name not in data:
        raise WorkflowError(f"Workflow '{name}' not found.")
    return data[name]


def list_workflows(vault_path: str) -> list[dict]:
    return list(_load_workflows(vault_path).values())
