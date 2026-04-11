"""Snapshot: save and restore point-in-time copies of a vault."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshots_dir(vault_path: str) -> Path:
    base = Path(vault_path).parent
    return base / ".envault_snapshots"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_snapshot(vault_path: str, password: str, label: str = "") -> Dict:
    """Dump all current secrets into a timestamped snapshot file.

    Returns a dict with snapshot metadata.
    """
    vault = Vault(vault_path, password)
    keys = vault.list()
    data: Dict[str, str] = {}
    for key in keys:
        data[key] = vault.get(key)

    snap_dir = _snapshots_dir(vault_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    ts = _now_iso()
    name = f"{ts}_{label}" if label else ts
    snap_file = snap_dir / f"{name}.json"

    payload = {"timestamp": ts, "label": label, "secrets": data}
    snap_file.write_text(json.dumps(payload, indent=2))

    return {"snapshot": str(snap_file), "timestamp": ts, "label": label, "count": len(data)}


def list_snapshots(vault_path: str) -> List[Dict]:
    """Return metadata for all snapshots, newest first."""
    snap_dir = _snapshots_dir(vault_path)
    if not snap_dir.exists():
        return []

    results = []
    for f in sorted(snap_dir.glob("*.json"), reverse=True):
        try:
            payload = json.loads(f.read_text())
            results.append({
                "file": str(f),
                "timestamp": payload.get("timestamp", ""),
                "label": payload.get("label", ""),
                "count": len(payload.get("secrets", {})),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return results


def restore_snapshot(vault_path: str, password: str, snapshot_file: str) -> Dict:
    """Overwrite vault secrets with those from *snapshot_file*.

    Returns a dict with restore metadata.
    """
    snap_path = Path(snapshot_file)
    if not snap_path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_file}")

    try:
        payload = json.loads(snap_path.read_text())
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Corrupt snapshot file: {exc}") from exc

    secrets: Dict[str, str] = payload.get("secrets", {})
    vault = Vault(vault_path, password)
    for key, value in secrets.items():
        vault.set(key, value)

    return {"restored": len(secrets), "from": snapshot_file}


def delete_snapshot(vault_path: str, snapshot_file: str) -> None:
    """Delete a snapshot file."""
    snap_path = Path(snapshot_file)
    if not snap_path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_file}")
    snap_path.unlink()
