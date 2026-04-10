"""Audit log for tracking vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_log(log_path: Path) -> List[dict]:
    if not log_path.exists():
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_log(log_path: Path, entries: List[dict]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")


def record(log_path: Path, action: str, key: str, actor: Optional[str] = None) -> dict:
    """Append an audit entry and return it."""
    entry = {
        "version": AUDIT_VERSION,
        "timestamp": _now_iso(),
        "action": action,
        "key": key,
        "actor": actor or os.environ.get("USER", "unknown"),
    }
    entries = _load_log(log_path)
    entries.append(entry)
    _save_log(log_path, entries)
    return entry


def get_log(log_path: Path) -> List[dict]:
    """Return all audit entries."""
    return _load_log(log_path)


def clear_log(log_path: Path) -> int:
    """Delete all audit entries. Returns number of entries removed."""
    entries = _load_log(log_path)
    count = len(entries)
    _save_log(log_path, [])
    return count
