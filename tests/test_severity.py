"""Tests for envault.severity."""

import pytest

from envault.severity import (
    SeverityError,
    set_severity,
    get_severity,
    remove_severity,
    list_severity,
    _severity_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetSeverity:
    def test_creates_severity_file(self, vault_path):
        set_severity(vault_path, "DB_PASS", "high")
        assert _severity_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_severity(vault_path, "DB_PASS", "critical", note="Very sensitive")
        assert entry["level"] == "critical"
        assert entry["note"] == "Very sensitive"

    def test_stores_level_in_file(self, vault_path):
        set_severity(vault_path, "API_KEY", "medium")
        data = list_severity(vault_path)
        assert data["API_KEY"]["level"] == "medium"

    def test_empty_note_allowed(self, vault_path):
        entry = set_severity(vault_path, "TOKEN", "low")
        assert entry["note"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(SeverityError, match="Invalid severity level"):
            set_severity(vault_path, "KEY", "extreme")

    def test_overwrites_existing_entry(self, vault_path):
        set_severity(vault_path, "DB_PASS", "low")
        set_severity(vault_path, "DB_PASS", "critical")
        entry = get_severity(vault_path, "DB_PASS")
        assert entry["level"] == "critical"


class TestGetSeverity:
    def test_returns_none_for_unknown_key(self, vault_path):
        assert get_severity(vault_path, "MISSING") is None

    def test_returns_entry_for_known_key(self, vault_path):
        set_severity(vault_path, "SECRET", "high", note="handle with care")
        entry = get_severity(vault_path, "SECRET")
        assert entry is not None
        assert entry["level"] == "high"
        assert entry["note"] == "handle with care"


class TestRemoveSeverity:
    def test_returns_true_on_removal(self, vault_path):
        set_severity(vault_path, "KEY", "low")
        assert remove_severity(vault_path, "KEY") is True

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_severity(vault_path, "GHOST") is False

    def test_key_no_longer_present_after_removal(self, vault_path):
        set_severity(vault_path, "KEY", "medium")
        remove_severity(vault_path, "KEY")
        assert get_severity(vault_path, "KEY") is None


class TestListSeverity:
    def test_empty_when_no_entries(self, vault_path):
        assert list_severity(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_severity(vault_path, "A", "low")
        set_severity(vault_path, "B", "critical")
        data = list_severity(vault_path)
        assert set(data.keys()) == {"A", "B"}
