"""Tests for envault.sensitivity."""
import pytest
from pathlib import Path
from envault.sensitivity import (
    set_sensitivity,
    get_sensitivity,
    remove_sensitivity,
    list_sensitivity,
    keys_at_level,
    SensitivityError,
    _sensitivity_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetSensitivity:
    def test_creates_sensitivity_file(self, vault_path):
        set_sensitivity(vault_path, "DB_PASS", "secret")
        assert _sensitivity_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_sensitivity(vault_path, "API_KEY", "confidential", note="third-party")
        assert entry["level"] == "confidential"
        assert entry["note"] == "third-party"

    def test_stores_level_in_file(self, vault_path):
        set_sensitivity(vault_path, "TOKEN", "top-secret")
        entry = get_sensitivity(vault_path, "TOKEN")
        assert entry["level"] == "top-secret"

    def test_empty_note_allowed(self, vault_path):
        entry = set_sensitivity(vault_path, "HOST", "internal")
        assert entry["note"] == ""

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(SensitivityError, match="Invalid level"):
            set_sensitivity(vault_path, "X", "ultra-secret")

    def test_overwrites_existing_entry(self, vault_path):
        set_sensitivity(vault_path, "KEY", "public")
        set_sensitivity(vault_path, "KEY", "secret")
        assert get_sensitivity(vault_path, "KEY")["level"] == "secret"


class TestGetSensitivity:
    def test_returns_none_for_missing_key(self, vault_path):
        assert get_sensitivity(vault_path, "MISSING") is None

    def test_returns_entry_for_known_key(self, vault_path):
        set_sensitivity(vault_path, "DB", "confidential")
        result = get_sensitivity(vault_path, "DB")
        assert result is not None
        assert result["level"] == "confidential"


class TestRemoveSensitivity:
    def test_returns_true_when_removed(self, vault_path):
        set_sensitivity(vault_path, "K", "internal")
        assert remove_sensitivity(vault_path, "K") is True

    def test_returns_false_for_missing_key(self, vault_path):
        assert remove_sensitivity(vault_path, "GHOST") is False

    def test_key_no_longer_present_after_removal(self, vault_path):
        set_sensitivity(vault_path, "K", "secret")
        remove_sensitivity(vault_path, "K")
        assert get_sensitivity(vault_path, "K") is None


class TestListSensitivity:
    def test_returns_empty_dict_when_no_file(self, vault_path):
        assert list_sensitivity(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_sensitivity(vault_path, "A", "public")
        set_sensitivity(vault_path, "B", "secret")
        result = list_sensitivity(vault_path)
        assert set(result.keys()) == {"A", "B"}


class TestKeysAtLevel:
    def test_returns_matching_keys(self, vault_path):
        set_sensitivity(vault_path, "A", "secret")
        set_sensitivity(vault_path, "B", "public")
        set_sensitivity(vault_path, "C", "secret")
        assert sorted(keys_at_level(vault_path, "secret")) == ["A", "C"]

    def test_empty_list_when_no_match(self, vault_path):
        set_sensitivity(vault_path, "A", "public")
        assert keys_at_level(vault_path, "top-secret") == []

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(SensitivityError):
            keys_at_level(vault_path, "bogus")
