"""Pin secrets to specific versions, preventing accidental overwrites."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class PinError(Exception):
    pass


def _pins_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_pins.json"


def _load_pins(vault_path: str) -> Dict[str, str]:
    p = _pins_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_pins(vault_path: str, pins: Dict[str, str]) -> None:
    _pins_path(vault_path).write_text(json.dumps(pins, indent=2))


def pin_key(vault_path: str, key: str, reason: str = "") -> Dict[str, str]:
    """Pin *key* so it cannot be overwritten until unpinned.

    Returns the updated pin entry.
    """
    pins = _load_pins(vault_path)
    pins[key] = reason
    _save_pins(vault_path, pins)
    return {"key": key, "reason": reason}


def unpin_key(vault_path: str, key: str) -> None:
    """Remove the pin on *key*.

    Raises PinError if the key is not pinned.
    """
    pins = _load_pins(vault_path)
    if key not in pins:
        raise PinError(f"Key '{key}' is not pinned.")
    del pins[key]
    _save_pins(vault_path, pins)


def is_pinned(vault_path: str, key: str) -> bool:
    """Return True if *key* is currently pinned."""
    return key in _load_pins(vault_path)


def list_pins(vault_path: str) -> List[Dict[str, str]]:
    """Return all pinned keys with their reasons."""
    pins = _load_pins(vault_path)
    return [{"key": k, "reason": v} for k, v in pins.items()]


def assert_not_pinned(vault_path: str, key: str) -> None:
    """Raise PinError if *key* is pinned (used by Vault.set / Vault.delete)."""
    if is_pinned(vault_path, key):
        reason = _load_pins(vault_path)[key]
        msg = f"Key '{key}' is pinned and cannot be modified."
        if reason:
            msg += f" Reason: {reason}"
        raise PinError(msg)
