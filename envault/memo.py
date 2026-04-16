"""Short-lived memos attached to vault keys."""

import json
from pathlib import Path
from datetime import datetime, timezone


class MemoError(Exception):
    pass


def _memo_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_memos.json"


def _load_memos(vault_path: str) -> dict:
    p = _memo_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_memos(vault_path: str, data: dict) -> None:
    _memo_path(vault_path).write_text(json.dumps(data, indent=2))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_memo(vault_path: str, key: str, text: str) -> dict:
    """Attach a memo to a key."""
    if not text:
        raise MemoError("Memo text must not be empty.")
    data = _load_memos(vault_path)
    entry = {"text": text, "created_at": _now_iso()}
    data.setdefault(key, []).append(entry)
    _save_memos(vault_path, data)
    return entry


def get_memos(vault_path: str, key: str) -> list:
    """Return all memos for a key."""
    return _load_memos(vault_path).get(key, [])


def clear_memos(vault_path: str, key: str) -> int:
    """Remove all memos for a key. Returns count removed."""
    data = _load_memos(vault_path)
    removed = len(data.pop(key, []))
    _save_memos(vault_path, data)
    return removed


def list_all(vault_path: str) -> dict:
    """Return all memos grouped by key."""
    return _load_memos(vault_path)
