"""Pre/post hooks for vault operations (set, get, delete)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

HOOK_EVENTS = ("pre_set", "post_set", "pre_get", "post_get", "pre_delete", "post_delete")


class HookError(Exception):
    pass


def _hooks_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".hooks.json")


def _load_hooks(vault_path: Path) -> Dict[str, List[str]]:
    p = _hooks_path(vault_path)
    if not p.exists():
        return {}
    with p.open() as f:
        return json.load(f)


def _save_hooks(vault_path: Path, data: Dict[str, List[str]]) -> None:
    p = _hooks_path(vault_path)
    with p.open("w") as f:
        json.dump(data, f, indent=2)


def register_hook(vault_path: Path, event: str, command: str) -> Dict[str, List[str]]:
    """Register a shell command to run on *event*."""
    if event not in HOOK_EVENTS:
        raise HookError(f"Unknown event '{event}'. Valid events: {HOOK_EVENTS}")
    data = _load_hooks(vault_path)
    data.setdefault(event, [])
    if command not in data[event]:
        data[event].append(command)
    _save_hooks(vault_path, data)
    return data


def unregister_hook(vault_path: Path, event: str, command: str) -> Dict[str, List[str]]:
    """Remove a previously registered hook command."""
    data = _load_hooks(vault_path)
    cmds = data.get(event, [])
    if command not in cmds:
        raise HookError(f"Hook '{command}' not found for event '{event}'")
    cmds.remove(command)
    if not cmds:
        data.pop(event, None)
    _save_hooks(vault_path, data)
    return data


def list_hooks(vault_path: Path) -> Dict[str, List[str]]:
    """Return all registered hooks keyed by event."""
    return _load_hooks(vault_path)


def fire(vault_path: Path, event: str, env: Optional[Dict[str, str]] = None) -> List[str]:
    """Run all commands registered for *event*. Returns list of commands executed."""
    data = _load_hooks(vault_path)
    commands = data.get(event, [])
    merged_env = {**os.environ, **(env or {})}
    for cmd in commands:
        ret = os.system(  # noqa: S605
            cmd
        ) if not env else __import__("subprocess").run(
            cmd, shell=True, env=merged_env  # noqa: S602
        ).returncode
        _ = ret  # we fire-and-forget; callers may inspect logs
    return commands
