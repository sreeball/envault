"""Tests for envault.staleness module."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from envault import staleness as sl


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


class TestRecordUpdate:
    def test_creates_staleness_file(self, vault_path):
        sl.record_update(vault_path, "DB_PASSWORD")
        assert sl._staleness_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = sl.record_update(vault_path, "API_KEY")
        assert entry["key"] == "API_KEY"
        assert "last_updated" in entry

    def test_stores_entry_in_file(self, vault_path):
        sl.record_update(vault_path, "SECRET")
        data = json.loads(sl._staleness_path(vault_path).read_text())
        assert "SECRET" in data

    def test_overwrites_existing_record(self, vault_path):
        sl.record_update(vault_path, "KEY")
        e1 = sl.record_update(vault_path, "KEY")
        data = json.loads(sl._staleness_path(vault_path).read_text())
        assert len([k for k in data if k == "KEY"]) == 1


class TestGetStaleness:
    def test_returns_none_fields_for_unknown_key(self, vault_path):
        info = sl.get_staleness(vault_path, "MISSING")
        assert info["last_updated"] is None
        assert info["age_days"] is None
        assert info["stale"] is None

    def test_fresh_key_not_stale(self, vault_path):
        sl.record_update(vault_path, "FRESH_KEY")
        info = sl.get_staleness(vault_path, "FRESH_KEY", max_age_days=90)
        assert info["stale"] is False
        assert info["age_days"] == 0

    def test_old_key_is_stale(self, vault_path):
        sl.record_update(vault_path, "OLD_KEY")
        # Manually backdate the record
        data = json.loads(sl._staleness_path(vault_path).read_text())
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        data["OLD_KEY"]["last_updated"] = old_date
        sl._staleness_path(vault_path).write_text(json.dumps(data))

        info = sl.get_staleness(vault_path, "OLD_KEY", max_age_days=90)
        assert info["stale"] is True
        assert info["age_days"] >= 100


class TestListStale:
    def test_empty_when_no_file(self, vault_path):
        assert sl.list_stale(vault_path) == []

    def test_returns_only_stale_keys(self, vault_path):
        sl.record_update(vault_path, "FRESH")
        sl.record_update(vault_path, "OLD")
        data = json.loads(sl._staleness_path(vault_path).read_text())
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        data["OLD"]["last_updated"] = old_date
        sl._staleness_path(vault_path).write_text(json.dumps(data))

        stale = sl.list_stale(vault_path, max_age_days=90)
        assert len(stale) == 1
        assert stale[0]["key"] == "OLD"


class TestRemoveRecord:
    def test_removes_existing_key(self, vault_path):
        sl.record_update(vault_path, "TO_REMOVE")
        result = sl.remove_record(vault_path, "TO_REMOVE")
        assert result is True
        data = json.loads(sl._staleness_path(vault_path).read_text())
        assert "TO_REMOVE" not in data

    def test_returns_false_for_missing_key(self, vault_path):
        result = sl.remove_record(vault_path, "NONEXISTENT")
        assert result is False
