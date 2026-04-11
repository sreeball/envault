"""Tests for envault.audit module."""

import json
import pytest
from pathlib import Path

from envault.audit import record, get_log, clear_log


@pytest.fixture
def log_path(tmp_path) -> Path:
    return tmp_path / "audit.json"


@pytest.fixture
def populated_log(log_path):
    """A log file pre-populated with three entries for reuse across tests."""
    record(log_path, "set", "A")
    record(log_path, "set", "B")
    record(log_path, "delete", "A")
    return log_path


class TestRecord:
    def test_creates_log_file(self, log_path):
        record(log_path, "set", "MY_KEY")
        assert log_path.exists()

    def test_returns_entry_dict(self, log_path):
        entry = record(log_path, "set", "MY_KEY")
        assert isinstance(entry, dict)
        assert entry["action"] == "set"
        assert entry["key"] == "MY_KEY"

    def test_entry_has_timestamp(self, log_path):
        entry = record(log_path, "set", "MY_KEY")
        assert "timestamp" in entry
        assert entry["timestamp"].endswith("+00:00")

    def test_entry_has_version(self, log_path):
        entry = record(log_path, "set", "MY_KEY")
        assert entry["version"] == 1

    def test_custom_actor(self, log_path):
        entry = record(log_path, "delete", "SECRET", actor="alice")
        assert entry["actor"] == "alice"

    def test_appends_multiple_entries(self, populated_log):
        entries = get_log(populated_log)
        assert len(entries) == 3

    def test_log_is_valid_json(self, log_path):
        record(log_path, "set", "X")
        with open(log_path) as f:
            data = json.load(f)
        assert isinstance(data, list)


class TestGetLog:
    def test_empty_when_no_file(self, log_path):
        assert get_log(log_path) == []

    def test_returns_all_entries(self, log_path):
        record(log_path, "set", "K1")
        record(log_path, "get", "K1")
        entries = get_log(log_path)
        assert len(entries) == 2
        assert entries[0]["action"] == "set"
        assert entries[1]["action"] == "get"

    def test_entries_are_ordered_chronologically(self, populated_log):
        """Entries should be returned in insertion order (oldest first)."""
        entries = get_log(populated_log)
        timestamps = [e["timestamp"] for e in entries]
        assert timestamps == sorted(timestamps)


class TestClearLog:
    def test_returns_count_of_removed_entries(self, log_path):
        record(log_path, "set", "A")
        record(log_path, "set", "B")
        count = clear_log(log_path)
        assert count == 2

    def test_log_empty_after_clear(self, log_path):
        record(log_path, "set", "A")
        clear_log(log_path)
        assert get_log(log_path) == []

    def test_clear_on_missing_file_returns_zero(self, log_path):
        count = clear_log(log_path)
        assert count == 0
