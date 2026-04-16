"""Tests for envault.maturity."""
import pytest
from pathlib import Path
from envault.maturity import (
    set_maturity, get_maturity, remove_maturity, list_maturity,
    keys_at_level, MaturityError, _maturity_path
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetMaturity:
    def test_creates_maturity_file(self, vault_path):
        set_maturity(vault_path, "API_KEY", "stable")
        assert _maturity_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_maturity(vault_path, "API_KEY", "stable")
        assert entry["level"] == "stable"

    def test_stores_note(self, vault_path):
        set_maturity(vault_path, "API_KEY", "beta", note="still testing")
        entry = get_maturity(vault_path, "API_KEY")
        assert entry["note"] == "still testing"

    def test_empty_note_allowed(self, vault_path):
        entry = set_maturity(vault_path, "API_KEY", "experimental")
        assert entry["note"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(MaturityError):
            set_maturity(vault_path, "API_KEY", "unknown")

    def test_overwrites_existing_entry(self, vault_path):
        set_maturity(vault_path, "API_KEY", "beta")
        set_maturity(vault_path, "API_KEY", "stable")
        entry = get_maturity(vault_path, "API_KEY")
        assert entry["level"] == "stable"


class TestGetMaturity:
    def test_returns_none_when_not_set(self, vault_path):
        assert get_maturity(vault_path, "MISSING") is None

    def test_returns_entry_when_set(self, vault_path):
        set_maturity(vault_path, "DB_PASS", "stable")
        assert get_maturity(vault_path, "DB_PASS") is not None


class TestRemoveMaturity:
    def test_removes_existing_key(self, vault_path):
        set_maturity(vault_path, "API_KEY", "stable")
        assert remove_maturity(vault_path, "API_KEY") is True
        assert get_maturity(vault_path, "API_KEY") is None

    def test_returns_false_when_not_found(self, vault_path):
        assert remove_maturity(vault_path, "GHOST") is False


class TestListMaturity:
    def test_returns_empty_when_none_set(self, vault_path):
        assert list_maturity(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_maturity(vault_path, "A", "stable")
        set_maturity(vault_path, "B", "beta")
        result = list_maturity(vault_path)
        assert set(result.keys()) == {"A", "B"}


class TestKeysAtLevel:
    def test_returns_matching_keys(self, vault_path):
        set_maturity(vault_path, "A", "stable")
        set_maturity(vault_path, "B", "beta")
        set_maturity(vault_path, "C", "stable")
        assert sorted(keys_at_level(vault_path, "stable")) == ["A", "C"]

    def test_empty_when_no_match(self, vault_path):
        set_maturity(vault_path, "A", "beta")
        assert keys_at_level(vault_path, "stable") == []

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(MaturityError):
            keys_at_level(vault_path, "nope")
