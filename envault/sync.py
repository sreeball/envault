"""Sync vault contents to/from a remote backend (file-based remote)."""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from envault.vault import Vault


class SyncError(Exception):
    """Raised when a sync operation fails."""


def push(vault: Vault, remote_path: str) -> int:
    """Push all vault entries to a remote path.

    Copies the raw vault JSON to *remote_path*, creating parent directories
    as needed.  Returns the number of keys pushed.
    """
    remote = Path(remote_path)
    remote.parent.mkdir(parents=True, exist_ok=True)

    raw = vault._load_raw()
    with open(remote, "w") as fh:
        json.dump(raw, fh, indent=2)

    return len(raw)


def pull(vault: Vault, remote_path: str, overwrite: bool = False) -> int:
    """Pull vault entries from a remote path into the local vault.

    Merges remote keys into the local vault.  Existing local keys are kept
    unless *overwrite* is ``True``.  Returns the number of keys imported.
    """
    remote = Path(remote_path)
    if not remote.exists():
        raise SyncError(f"Remote path does not exist: {remote_path}")

    with open(remote) as fh:
        remote_raw: dict = json.load(fh)

    local_raw = vault._load_raw()
    imported = 0
    for key, value in remote_raw.items():
        if key not in local_raw or overwrite:
            local_raw[key] = value
            imported += 1

    vault._save_raw(local_raw)
    return imported


def status(vault: Vault, remote_path: str) -> dict:
    """Return a diff-like status between local vault and remote.

    Returns a dict with keys ``only_local``, ``only_remote``, and ``common``.
    """
    remote = Path(remote_path)
    remote_raw: dict = {}
    if remote.exists():
        with open(remote) as fh:
            remote_raw = json.load(fh)

    local_raw = vault._load_raw()
    local_keys = set(local_raw)
    remote_keys = set(remote_raw)

    return {
        "only_local": sorted(local_keys - remote_keys),
        "only_remote": sorted(remote_keys - local_keys),
        "common": sorted(local_keys & remote_keys),
    }
