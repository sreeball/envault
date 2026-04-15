"""Trigger management: register and fire event-based triggers on vault keys."""

import json
import subprocess
from pathlib import Path
from typing import Any


class TriggerError(Exception):
    pass


VALID_EVENTS = {"set", "delete", "rotate", "expire", "access"}


def _triggers_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_triggers.json"


def _load_triggers(vault_path: str) -> dict:
    p = _triggers_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_triggers(vault_path: str, data: dict) -> None:
    _triggers_path(vault_path).write_text(json.dumps(data, indent=2))


def add_trigger(vault_path: str, key: str, event: str, command: str) -> dict:
    """Register a shell command to run when *event* occurs on *key*."""
    if event not in VALID_EVENTS:
        raise TriggerError(f"Invalid event '{event}'. Choose from: {sorted(VALID_EVENTS)}")
    if not command.strip():
        raise TriggerError("Command must not be empty.")
    data = _load_triggers(vault_path)
    data.setdefault(key, {})
    data[key].setdefault(event, [])
    if command not in data[key][event]:
        data[key][event].append(command)
    _save_triggers(vault_path, data)
    return {"key": key, "event": event, "command": command}


def remove_trigger(vault_path: str, key: str, event: str, command: str) -> bool:
    """Remove a specific trigger command. Returns True if removed."""
    data = _load_triggers(vault_path)
    try:
        data[key][event].remove(command)
        if not data[key][event]:
            del data[key][event]
        if not data[key]:
            del data[key]
        _save_triggers(vault_path, data)
        return True
    except (KeyError, ValueError):
        return False


def fire_triggers(vault_path: str, key: str, event: str, context: dict[str, Any] | None = None) -> list[dict]:
    """Execute all commands registered for *key*/*event*. Returns results."""
    data = _load_triggers(vault_path)
    commands = data.get(key, {}).get(event, [])
    results = []
    env_extra = {"ENVAULT_KEY": key, "ENVAULT_EVENT": event}
    if context:
        for k, v in context.items():
            env_extra[f"ENVAULT_CTX_{k.upper()}"] = str(v)
    import os
    env = {**os.environ, **env_extra}
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
            results.append({"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()})
        except Exception as exc:
            results.append({"command": cmd, "returncode": -1, "stdout": "", "stderr": str(exc)})
    return results


def list_triggers(vault_path: str, key: str | None = None) -> dict:
    """Return triggers for a specific key or all keys."""
    data = _load_triggers(vault_path)
    if key is not None:
        return {key: data.get(key, {})}
    return data
