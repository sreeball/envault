"""Signal: attach named signals to vault keys for event-driven workflows."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class SignalError(Exception):
    pass


def _signals_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_signals.json"


def _load_signals(vault_path: str) -> Dict:
    p = _signals_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_signals(vault_path: str, data: Dict) -> None:
    _signals_path(vault_path).write_text(json.dumps(data, indent=2))


def emit_signal(vault_path: str, key: str, signal: str, payload: Optional[str] = None) -> Dict:
    """Attach a named signal to a key."""
    if not key:
        raise SignalError("key must not be empty")
    if not signal:
        raise SignalError("signal name must not be empty")
    data = _load_signals(vault_path)
    entry = {"signal": signal, "payload": payload or ""}
    data.setdefault(key, []).append(entry)
    _save_signals(vault_path, data)
    return entry


def get_signals(vault_path: str, key: str) -> List[Dict]:
    """Return all signals recorded for a key."""
    data = _load_signals(vault_path)
    return data.get(key, [])


def clear_signals(vault_path: str, key: str) -> int:
    """Remove all signals for a key. Returns count removed."""
    data = _load_signals(vault_path)
    removed = len(data.pop(key, []))
    _save_signals(vault_path, data)
    return removed


def list_all(vault_path: str) -> Dict:
    """Return full signals mapping."""
    return _load_signals(vault_path)
