"""Notification hooks for vault events (set, delete, rotate, etc.)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

NOTIFY_FILENAME = ".envault_notify.json"


class NotifyError(Exception):
    """Raised when a notification operation fails."""


def _notify_path(vault_path: str) -> Path:
    return Path(vault_path).parent / NOTIFY_FILENAME


def _load_config(vault_path: str) -> dict:
    p = _notify_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_config(vault_path: str, config: dict) -> None:
    _notify_path(vault_path).write_text(json.dumps(config, indent=2))


def subscribe(vault_path: str, event: str, command: str) -> dict:
    """Register *command* to run when *event* is fired.

    Returns the updated subscription entry.
    """
    config = _load_config(vault_path)
    subscribers = config.setdefault("subscribers", {})
    handlers = subscribers.setdefault(event, [])
    if command not in handlers:
        handlers.append(command)
    _save_config(vault_path, config)
    return {"event": event, "command": command, "all": handlers}


def unsubscribe(vault_path: str, event: str, command: str) -> list[str]:
    """Remove *command* from the handlers for *event*."""
    config = _load_config(vault_path)
    handlers: list = config.get("subscribers", {}).get(event, [])
    if command not in handlers:
        raise NotifyError(f"Command not subscribed to event '{event}': {command}")
    handlers.remove(command)
    _save_config(vault_path, config)
    return handlers


def fire(vault_path: str, event: str, context: dict[str, Any] | None = None) -> list[dict]:
    """Fire all handlers registered for *event*.

    Each handler command is executed via the shell.  *context* values are
    passed as environment variables prefixed with ``ENVAULT_``.

    Returns a list of result dicts with ``command``, ``returncode`` and
    ``stdout`` keys.
    """
    import os

    config = _load_config(vault_path)
    handlers: list[str] = config.get("subscribers", {}).get(event, [])
    env = {**os.environ}
    if context:
        for k, v in context.items():
            env[f"ENVAULT_{k.upper()}"] = str(v)
    env["ENVAULT_EVENT"] = event

    results = []
    for cmd in handlers:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
        results.append({"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout.strip()})
    return results


def list_subscriptions(vault_path: str) -> dict[str, list[str]]:
    """Return all event → [commands] mappings."""
    return _load_config(vault_path).get("subscribers", {})
