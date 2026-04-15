"""Tests for envault.deprecation."""

import pytest
from pathlib import Path

from envault.deprecation import (
    DeprecationError,
    deprecate_key,
    undeprecate_key,
    get_deprecation,
    list_deprecated,
    _deprecations_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


class TestDeprecateKey:
    def test_creates_deprecations_file(self, vault_path):
        deprecate_key(vault_path, "OLD_KEY", "no longer used")
        assert _deprecations_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = deprecate_key(vault_path, "OLD_KEY", "no longer used")
        assert entry["reason"] == "no longer used"
        assert entry["replacement"] is None

    def test_stores_replacement(self, vault_path):
        entry = deprecate_key(vault_path, "OLD_KEY", "renamed", replacement="NEW_KEY")
        assert entry["replacement"] == "NEW_KEY"

    def test_persists_to_disk(self, vault_path):
        deprecate_key(vault_path, "OLD_KEY", "gone")
        data = list_deprecated(vault_path)
        assert "OLD_KEY" in data

    def test_overwrites_existing_entry(self, vault_path):
        deprecate_key(vault_path, "OLD_KEY", "first reason")
        deprecate_key(vault_path, "OLD_KEY", "second reason")
        entry = get_deprecation(vault_path, "OLD_KEY")
        assert entry["reason"] == "second reason"

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(DeprecationError):
            deprecate_key(vault_path, "", "some reason")

    def test_raises_on_empty_reason(self, vault_path):
        with pytest.raises(DeprecationError):
            deprecate_key(vault_path, "OLD_KEY", "")


class TestUndeprecateKey:
    def test_removes_entry(self, vault_path):
        deprecate_key(vault_path, "OLD_KEY", "gone")
        undeprecate_key(vault_path, "OLD_KEY")
        assert get_deprecation(vault_path, "OLD_KEY") is None

    def test_raises_if_not_deprecated(self, vault_path):
        with pytest.raises(DeprecationError, match="not deprecated"):
            undeprecate_key(vault_path, "MISSING")


class TestGetDeprecation:
    def test_returns_none_for_unknown_key(self, vault_path):
        assert get_deprecation(vault_path, "UNKNOWN") is None

    def test_returns_entry_for_known_key(self, vault_path):
        deprecate_key(vault_path, "K", "old", replacement="K2")
        entry = get_deprecation(vault_path, "K")
        assert entry["reason"] == "old"
        assert entry["replacement"] == "K2"


class TestListDeprecated:
    def test_empty_when_no_file(self, vault_path):
        assert list_deprecated(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        deprecate_key(vault_path, "A", "reason A")
        deprecate_key(vault_path, "B", "reason B")
        result = list_deprecated(vault_path)
        assert set(result.keys()) == {"A", "B"}
