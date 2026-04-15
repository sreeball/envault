"""Tests for envault.forecast."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.forecast import build_forecast, summary, ForecastEntry


@pytest.fixture()
def vault_path(tmp_path):
    vp = tmp_path / "vault.enc"
    vp.write_bytes(b"")
    return str(vp)


def _iso_future(days: int) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=days)
    return dt.isoformat()


def _write_ttl(vault_path: str, data: dict):
    p = Path(vault_path).parent / ".envault_ttl.json"
    p.write_text(json.dumps(data))


def _write_reminders(vault_path: str, data: dict):
    p = Path(vault_path).parent / ".envault_reminders.json"
    p.write_text(json.dumps(data))


def _write_retention(vault_path: str, data: dict):
    p = Path(vault_path).parent / ".envault_retention.json"
    p.write_text(json.dumps(data))


class TestBuildForecast:
    def test_empty_when_no_sidecar_files(self, vault_path):
        assert build_forecast(vault_path) == []

    def test_picks_up_ttl_expiry(self, vault_path):
        _write_ttl(vault_path, {"API_KEY": {"expires_at": _iso_future(5), "note": ""}})
        entries = build_forecast(vault_path, horizon_days=30)
        assert len(entries) == 1
        assert entries[0].key == "API_KEY"
        assert entries[0].event == "expiry"
        assert entries[0].source == "ttl"

    def test_excludes_ttl_beyond_horizon(self, vault_path):
        _write_ttl(vault_path, {"API_KEY": {"expires_at": _iso_future(60), "note": ""}})
        entries = build_forecast(vault_path, horizon_days=30)
        assert entries == []

    def test_picks_up_reminder(self, vault_path):
        _write_reminders(vault_path, {
            "DB_PASS": [{"due_at": _iso_future(3), "message": "rotate soon"}]
        })
        entries = build_forecast(vault_path, horizon_days=30)
        assert len(entries) == 1
        assert entries[0].event == "reminder"
        assert entries[0].note == "rotate soon"

    def test_picks_up_retention(self, vault_path):
        _write_retention(vault_path, {
            "OLD_KEY": {"purge_after": _iso_future(10), "note": "scheduled purge"}
        })
        entries = build_forecast(vault_path, horizon_days=30)
        assert len(entries) == 1
        assert entries[0].event == "rotation"
        assert entries[0].source == "retention"

    def test_sorted_by_days_remaining(self, vault_path):
        _write_ttl(vault_path, {
            "KEY_A": {"expires_at": _iso_future(20), "note": ""},
            "KEY_B": {"expires_at": _iso_future(2), "note": ""},
        })
        entries = build_forecast(vault_path, horizon_days=30)
        assert entries[0].key == "KEY_B"
        assert entries[1].key == "KEY_A"

    def test_multiple_sources_combined(self, vault_path):
        _write_ttl(vault_path, {"A": {"expires_at": _iso_future(1), "note": ""}})
        _write_reminders(vault_path, {"B": [{"due_at": _iso_future(2), "message": ""}]})
        _write_retention(vault_path, {"C": {"purge_after": _iso_future(3), "note": ""}})
        entries = build_forecast(vault_path, horizon_days=30)
        assert len(entries) == 3


class TestSummary:
    def test_empty_entries(self):
        s = summary([])
        assert s["total"] == 0
        assert s["by_event"] == {}

    def test_counts_by_event(self, vault_path):
        entries = [
            ForecastEntry("A", "expiry", "", 1, "ttl"),
            ForecastEntry("B", "expiry", "", 2, "ttl"),
            ForecastEntry("C", "reminder", "", 3, "reminder"),
        ]
        s = summary(entries)
        assert s["total"] == 3
        assert s["by_event"]["expiry"] == 2
        assert s["by_event"]["reminder"] == 1
