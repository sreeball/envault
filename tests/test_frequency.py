"""Tests for envault.frequency."""

import pytest
from pathlib import Path
from envault.frequency import (
    record_access, get_frequency, reset_frequency, list_frequency,
    FrequencyError, _frequency_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestRecordAccess:
    def test_creates_frequency_file(self, vault_path):
        record_access(vault_path, "MY_KEY")
        assert _frequency_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = record_access(vault_path, "MY_KEY")
        assert isinstance(entry, dict)
        assert entry["count"] == 1

    def test_increments_count(self, vault_path):
        record_access(vault_path, "MY_KEY")
        entry = record_access(vault_path, "MY_KEY")
        assert entry["count"] == 2

    def test_last_accessed_set(self, vault_path):
        entry = record_access(vault_path, "MY_KEY")
        assert entry["last_accessed"] is not None

    def test_first_accessed_set(self, vault_path):
        entry = record_access(vault_path, "MY_KEY")
        assert entry["first_accessed"] is not None

    def test_multiple_keys_tracked_independently(self, vault_path):
        record_access(vault_path, "A")
        record_access(vault_path, "A")
        record_access(vault_path, "B")
        assert get_frequency(vault_path, "A")["count"] == 2
        assert get_frequency(vault_path, "B")["count"] == 1


class TestGetFrequency:
    def test_raises_for_unknown_key(self, vault_path):
        with pytest.raises(FrequencyError):
            get_frequency(vault_path, "MISSING")

    def test_returns_correct_count(self, vault_path):
        record_access(vault_path, "K")
        record_access(vault_path, "K")
        assert get_frequency(vault_path, "K")["count"] == 2


class TestResetFrequency:
    def test_removes_key_data(self, vault_path):
        record_access(vault_path, "K")
        reset_frequency(vault_path, "K")
        with pytest.raises(FrequencyError):
            get_frequency(vault_path, "K")

    def test_no_error_for_missing_key(self, vault_path):
        reset_frequency(vault_path, "GHOST")  # should not raise


class TestListFrequency:
    def test_empty_returns_empty_list(self, vault_path):
        assert list_frequency(vault_path) == []

    def test_sorted_by_count_descending(self, vault_path):
        record_access(vault_path, "A")
        for _ in range(3):
            record_access(vault_path, "B")
        entries = list_frequency(vault_path)
        assert entries[0]["key"] == "B"
        assert entries[1]["key"] == "A"

    def test_top_limits_results(self, vault_path):
        for k in ["X", "Y", "Z"]:
            record_access(vault_path, k)
        assert len(list_frequency(vault_path, top=2)) == 2
