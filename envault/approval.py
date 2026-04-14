"""Approval workflow for sensitive vault operations."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional


class ApprovalError(Exception):
    """Raised when an approval operation fails."""


def _approvals_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_approvals.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_approvals(vault_path: str) -> dict:
    p = _approvals_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_approvals(vault_path: str, data: dict) -> None:
    _approvals_path(vault_path).write_text(json.dumps(data, indent=2))


def request_approval(
    vault_path: str,
    key: str,
    operation: str,
    requester: str,
    reason: str = "",
) -> dict:
    """Create a pending approval request for a vault operation."""
    if not operation:
        raise ApprovalError("operation must not be empty")
    if not requester:
        raise ApprovalError("requester must not be empty")

    data = _load_approvals(vault_path)
    token = str(uuid.uuid4())
    entry = {
        "token": token,
        "key": key,
        "operation": operation,
        "requester": requester,
        "reason": reason,
        "status": "pending",
        "requested_at": _now_iso(),
        "resolved_at": None,
        "resolver": None,
    }
    data[token] = entry
    _save_approvals(vault_path, data)
    return entry


def resolve_approval(
    vault_path: str,
    token: str,
    approved: bool,
    resolver: str,
) -> dict:
    """Approve or reject a pending request."""
    data = _load_approvals(vault_path)
    if token not in data:
        raise ApprovalError(f"approval token not found: {token}")
    entry = data[token]
    if entry["status"] != "pending":
        raise ApprovalError(f"approval already resolved with status: {entry['status']}")
    entry["status"] = "approved" if approved else "rejected"
    entry["resolved_at"] = _now_iso()
    entry["resolver"] = resolver
    _save_approvals(vault_path, data)
    return entry


def list_approvals(vault_path: str, status: Optional[str] = None) -> List[dict]:
    """List all approval requests, optionally filtered by status."""
    data = _load_approvals(vault_path)
    entries = list(data.values())
    if status:
        entries = [e for e in entries if e["status"] == status]
    return entries


def get_approval(vault_path: str, token: str) -> dict:
    """Retrieve a single approval request by token."""
    data = _load_approvals(vault_path)
    if token not in data:
        raise ApprovalError(f"approval token not found: {token}")
    return data[token]
