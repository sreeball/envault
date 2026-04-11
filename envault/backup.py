"""Backup and restore vault files to/from a local archive directory."""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


class BackupError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _backups_dir(vault_path: str) -> Path:
    vp = Path(vault_path)
    return vp.parent / ".envault_backups"


def create_backup(vault_path: str, label: str = "") -> dict:
    """Copy the vault file into the backups directory and return metadata."""
    vp = Path(vault_path)
    if not vp.exists():
        raise BackupError(f"Vault file not found: {vault_path}")

    backups_dir = _backups_dir(vault_path)
    backups_dir.mkdir(exist_ok=True)

    ts = _now_iso()
    slug = f"_{label}" if label else ""
    filename = f"backup_{ts}{slug}.json"
    dest = backups_dir / filename

    shutil.copy2(vp, dest)

    meta = {"timestamp": ts, "label": label, "filename": filename, "path": str(dest)}
    return meta


def list_backups(vault_path: str) -> list:
    """Return a sorted list of backup metadata dicts (oldest first)."""
    backups_dir = _backups_dir(vault_path)
    if not backups_dir.exists():
        return []

    entries = []
    for f in sorted(backups_dir.glob("backup_*.json")):
        parts = f.stem.split("_", 2)  # ['backup', timestamp, label?]
        ts = parts[1] if len(parts) > 1 else ""
        label = parts[2] if len(parts) > 2 else ""
        entries.append({"timestamp": ts, "label": label, "filename": f.name, "path": str(f)})
    return entries


def restore_backup(vault_path: str, filename: str) -> None:
    """Overwrite the vault file with the contents of the named backup."""
    backups_dir = _backups_dir(vault_path)
    src = backups_dir / filename
    if not src.exists():
        raise BackupError(f"Backup not found: {filename}")
    shutil.copy2(src, vault_path)


def delete_backup(vault_path: str, filename: str) -> None:
    """Remove a backup file from the backups directory."""
    backups_dir = _backups_dir(vault_path)
    target = backups_dir / filename
    if not target.exists():
        raise BackupError(f"Backup not found: {filename}")
    target.unlink()
