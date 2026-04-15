"""Anomaly detection for vault access and value patterns."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AnomalyError(Exception):
    pass


def _anomaly_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_anomalies.json"


def _load_anomalies(vault_path: str) -> dict:
    p = _anomaly_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_anomalies(vault_path: str, data: dict) -> None:
    _anomaly_path(vault_path).write_text(json.dumps(data, indent=2))


def record_anomaly(
    vault_path: str,
    key: str,
    anomaly_type: str,
    detail: str = "",
    severity: str = "medium",
) -> dict:
    """Record an anomaly event for a key."""
    valid_severities = {"low", "medium", "high", "critical"}
    if severity not in valid_severities:
        raise AnomalyError(
            f"Invalid severity '{severity}'. Choose from: {sorted(valid_severities)}"
        )

    data = _load_anomalies(vault_path)
    if key not in data:
        data[key] = []

    entry: dict[str, Any] = {
        "type": anomaly_type,
        "detail": detail,
        "severity": severity,
    }
    data[key].append(entry)
    _save_anomalies(vault_path, data)
    return entry


def list_anomalies(vault_path: str, key: str) -> list:
    """Return all recorded anomalies for a key."""
    data = _load_anomalies(vault_path)
    return data.get(key, [])


def clear_anomalies(vault_path: str, key: str) -> int:
    """Remove all anomalies for a key. Returns count removed."""
    data = _load_anomalies(vault_path)
    removed = len(data.pop(key, []))
    _save_anomalies(vault_path, data)
    return removed


def summary(vault_path: str) -> dict:
    """Return a mapping of key -> anomaly count for all keys with anomalies."""
    data = _load_anomalies(vault_path)
    return {k: len(v) for k, v in data.items() if v}
