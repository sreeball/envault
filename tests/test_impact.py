"""Tests for envault.impact."""
import pytest
from pathlib import Path
from envault.impact import (
    set_impact,
    get_impact,
    remove_impact,
    list_impact,
    keys_by_level,
    ImpactError,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetImpact:
    def test_creates_impact_file(self, vault_path):
        set_impact(vault_path, "DB_PASS", "critical")
        assert (Path(vault_path).parent / ".envault_impact.json").exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_impact(vault_path, "API_KEY", "high", note="External API")
        assert entry["level"] == "high"
        assert entry["note"] == "External API"

    def test_stores_level_in_file(self, vault_path):
        set_impact(vault_path, "TOKEN", "medium")
        entry = get_impact(vault_path, "TOKEN")
        assert entry["level"] == "medium"

    def test_empty_note_allowed(self, vault_path):
        entry = set_impact(vault_path, "X", "low")
        assert entry["note"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(ImpactError, match="Invalid level"):
            set_impact(vault_path, "X", "extreme")

    def test_overwrites_existing_entry(self, vault_path):
        set_impact(vault_path, "K", "low")
        set_impact(vault_path, "K", "critical", note="Updated")
        entry = get_impact(vault_path, "K")
        assert entry["level"] == "critical"
        assert entry["note"] == "Updated"


class TestGetImpact:
    def test_returns_none_when_not_set(self, vault_path):
        assert get_impact(vault_path, "MISSING") is None

    def test_returns_entry_when_set(self, vault_path):
        set_impact(vault_path, "DB_URL", "high")
        assert get_impact(vault_path, "DB_URL") is not None


class TestRemoveImpact:
    def test_returns_true_on_removal(self, vault_path):
        set_impact(vault_path, "K", "low")
        assert remove_impact(vault_path, "K") is True

    def test_returns_false_when_missing(self, vault_path):
        assert remove_impact(vault_path, "NOPE") is False

    def test_entry_gone_after_removal(self, vault_path):
        set_impact(vault_path, "K", "low")
        remove_impact(vault_path, "K")
        assert get_impact(vault_path, "K") is None


class TestListImpact:
    def test_empty_when_no_entries(self, vault_path):
        assert list_impact(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_impact(vault_path, "A", "low")
        set_impact(vault_path, "B", "critical")
        result = list_impact(vault_path)
        assert "A" in result and "B" in result


class TestKeysByLevel:
    def test_returns_matching_keys(self, vault_path):
        set_impact(vault_path, "A", "critical")
        set_impact(vault_path, "B", "low")
        set_impact(vault_path, "C", "critical")
        assert set(keys_by_level(vault_path, "critical")) == {"A", "C"}

    def test_empty_list_when_no_match(self, vault_path):
        set_impact(vault_path, "A", "low")
        assert keys_by_level(vault_path, "high") == []

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(ImpactError):
            keys_by_level(vault_path, "unknown")
