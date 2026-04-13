"""Tests for envault.retention."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.retention import (
    RetentionError,
    set_retention,
    get_retention,
    remove_retention,
    list_retention,
    list_due_for_purge,
    _retention_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestSetRetention:
    def test_creates_retention_file(self, vault_path):
        set_retention(vault_path, "API_KEY", 30)
        assert _retention_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_retention(vault_path, "API_KEY", 30)
        assert entry["key"] == "API_KEY"
        assert entry["days"] == 30

    def test_purge_after_is_in_the_future(self, vault_path):
        from datetime import datetime, timezone

        entry = set_retention(vault_path, "API_KEY", 10)
        now = datetime.now(timezone.utc).isoformat()
        assert entry["purge_after"] > now

    def test_note_stored(self, vault_path):
        entry = set_retention(vault_path, "API_KEY", 7, note="rotate weekly")
        assert entry["note"] == "rotate weekly"

    def test_empty_note_allowed(self, vault_path):
        entry = set_retention(vault_path, "API_KEY", 7)
        assert entry["note"] == ""

    def test_raises_on_zero_days(self, vault_path):
        with pytest.raises(RetentionError):
            set_retention(vault_path, "API_KEY", 0)

    def test_raises_on_negative_days(self, vault_path):
        with pytest.raises(RetentionError):
            set_retention(vault_path, "API_KEY", -5)

    def test_overwrites_existing_policy(self, vault_path):
        set_retention(vault_path, "API_KEY", 30)
        entry = set_retention(vault_path, "API_KEY", 90)
        assert entry["days"] == 90
        assert len(list_retention(vault_path)) == 1


class TestGetRetention:
    def test_returns_none_when_not_set(self, vault_path):
        assert get_retention(vault_path, "MISSING") is None

    def test_returns_entry_when_set(self, vault_path):
        set_retention(vault_path, "DB_PASS", 14)
        entry = get_retention(vault_path, "DB_PASS")
        assert entry is not None
        assert entry["key"] == "DB_PASS"


class TestRemoveRetention:
    def test_removes_existing_key(self, vault_path):
        set_retention(vault_path, "API_KEY", 30)
        result = remove_retention(vault_path, "API_KEY")
        assert result is True
        assert get_retention(vault_path, "API_KEY") is None

    def test_returns_false_for_missing_key(self, vault_path):
        assert remove_retention(vault_path, "NOPE") is False


class TestListRetention:
    def test_empty_when_no_policies(self, vault_path):
        assert list_retention(vault_path) == []

    def test_returns_all_entries(self, vault_path):
        set_retention(vault_path, "A", 10)
        set_retention(vault_path, "B", 5)
        entries = list_retention(vault_path)
        assert len(entries) == 2
        keys = {e["key"] for e in entries}
        assert keys == {"A", "B"}

    def test_sorted_by_purge_after(self, vault_path):
        set_retention(vault_path, "LONG", 90)
        set_retention(vault_path, "SHORT", 1)
        entries = list_retention(vault_path)
        assert entries[0]["key"] == "SHORT"


class TestListDueForPurge:
    def test_empty_when_nothing_expired(self, vault_path):
        set_retention(vault_path, "API_KEY", 30)
        assert list_due_for_purge(vault_path) == []

    def test_detects_manually_backdated_entry(self, vault_path):
        set_retention(vault_path, "OLD_KEY", 30)
        # Backdate the purge_after to the past
        rp = _retention_path(vault_path)
        data = json.loads(rp.read_text())
        data["OLD_KEY"]["purge_after"] = "2000-01-01T00:00:00+00:00"
        rp.write_text(json.dumps(data))
        due = list_due_for_purge(vault_path)
        assert len(due) == 1
        assert due[0]["key"] == "OLD_KEY"
