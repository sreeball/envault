"""Watch a vault file for changes and trigger hooks or callbacks."""

import time
import os
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when a watch operation fails."""


def _mtime(path: Path) -> float:
    """Return the modification time of a file, or 0.0 if it doesn't exist."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def watch(
    vault_path: Path,
    callback: Callable[[Path], None],
    interval: float = 1.0,
    timeout: Optional[float] = None,
) -> int:
    """Poll *vault_path* every *interval* seconds and call *callback* on change.

    Returns the number of change events detected.
    Stops after *timeout* seconds if provided, otherwise runs until interrupted.
    Raises WatchError if vault_path does not exist at start time.
    """
    if not vault_path.exists():
        raise WatchError(f"Vault file not found: {vault_path}")

    last_mtime = _mtime(vault_path)
    events = 0
    elapsed = 0.0

    try:
        while True:
            if timeout is not None and elapsed >= timeout:
                break
            time.sleep(interval)
            elapsed += interval
            current_mtime = _mtime(vault_path)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                events += 1
                callback(vault_path)
    except KeyboardInterrupt:
        pass

    return events


def watch_once(
    vault_path: Path,
    callback: Callable[[Path], None],
    interval: float = 0.5,
    timeout: float = 5.0,
) -> bool:
    """Wait for a single change event within *timeout* seconds.

    Returns True if a change was detected, False if timed out.
    """
    if not vault_path.exists():
        raise WatchError(f"Vault file not found: {vault_path}")

    last_mtime = _mtime(vault_path)
    elapsed = 0.0

    while elapsed < timeout:
        time.sleep(interval)
        elapsed += interval
        if _mtime(vault_path) != last_mtime:
            callback(vault_path)
            return True

    return False


def watch_until_deleted(
    vault_path: Path,
    callback: Callable[[Path], None],
    interval: float = 1.0,
    timeout: Optional[float] = None,
) -> int:
    """Poll *vault_path* and call *callback* on each change until the file is deleted.

    Returns the number of change events detected before deletion.
    Stops when the file no longer exists, after *timeout* seconds, or on interrupt.
    Raises WatchError if vault_path does not exist at start time.
    """
    if not vault_path.exists():
        raise WatchError(f"Vault file not found: {vault_path}")

    last_mtime = _mtime(vault_path)
    events = 0
    elapsed = 0.0

    try:
        while vault_path.exists():
            if timeout is not None and elapsed >= timeout:
                break
            time.sleep(interval)
            elapsed += interval
            current_mtime = _mtime(vault_path)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                events += 1
                callback(vault_path)
    except KeyboardInterrupt:
        pass

    return events
