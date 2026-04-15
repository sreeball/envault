"""Forecast upcoming secret expirations and rotation needs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

FORECAST_FILE = ".envault_forecast.json"


class ForecastError(Exception):
    pass


@dataclass
class ForecastEntry:
    key: str
    event: str          # 'expiry' | 'rotation' | 'reminder'
    due_at: str
    days_remaining: int
    source: str         # which subsystem produced this entry
    note: str = ""


def _forecast_path(vault_path: str) -> Path:
    return Path(vault_path).parent / FORECAST_FILE


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_until(iso: str) -> int:
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = dt - _now()
        return max(int(delta.total_seconds() // 86400), 0)
    except Exception:
        return -1


def _load_sidecar(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def build_forecast(vault_path: str, horizon_days: int = 30) -> List[ForecastEntry]:
    """Scan TTL, reminder, and retention files; return entries due within horizon."""
    base = Path(vault_path).parent
    entries: List[ForecastEntry] = []

    # --- TTL ---
    ttl_data = _load_sidecar(base / ".envault_ttl.json")
    for key, info in ttl_data.items():
        expires_at = info.get("expires_at", "")
        days = _days_until(expires_at)
        if 0 <= days <= horizon_days:
            entries.append(ForecastEntry(
                key=key, event="expiry", due_at=expires_at,
                days_remaining=days, source="ttl",
                note=info.get("note", ""),
            ))

    # --- Reminders ---
    reminder_data = _load_sidecar(base / ".envault_reminders.json")
    for key, items in reminder_data.items():
        for item in (items if isinstance(items, list) else [items]):
            due_at = item.get("due_at", "")
            days = _days_until(due_at)
            if 0 <= days <= horizon_days:
                entries.append(ForecastEntry(
                    key=key, event="reminder", due_at=due_at,
                    days_remaining=days, source="reminder",
                    note=item.get("message", ""),
                ))

    # --- Retention ---
    retention_data = _load_sidecar(base / ".envault_retention.json")
    for key, info in retention_data.items():
        purge_after = info.get("purge_after", "")
        days = _days_until(purge_after)
        if 0 <= days <= horizon_days:
            entries.append(ForecastEntry(
                key=key, event="rotation", due_at=purge_after,
                days_remaining=days, source="retention",
                note=info.get("note", ""),
            ))

    entries.sort(key=lambda e: e.days_remaining)
    return entries


def summary(entries: List[ForecastEntry]) -> dict:
    """Return a count breakdown by event type."""
    counts: dict = {}
    for e in entries:
        counts[e.event] = counts.get(e.event, 0) + 1
    return {"total": len(entries), "by_event": counts}
