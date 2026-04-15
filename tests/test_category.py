"""Tests for envault.category."""
import json
import pytest
from pathlib import Path

from envault.category import (
    CategoryError,
    assign_category,
    remove_from_category,
    list_categories,
    keys_in_category,
    _categories_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestAssignCategory:
    def test_creates_categories_file(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        assert _categories_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = assign_category(vault_path, "DB_URL", "database")
        assert result["category"] == "database"
        assert result["key"] == "DB_URL"
        assert "DB_URL" in result["members"]

    def test_accumulates_keys_in_category(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        result = assign_category(vault_path, "DB_PASS", "database")
        assert "DB_URL" in result["members"]
        assert "DB_PASS" in result["members"]

    def test_multiple_categories(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        assign_category(vault_path, "API_KEY", "api")
        cats = list_categories(vault_path)
        assert "database" in cats
        assert "api" in cats

    def test_duplicate_key_not_added_twice(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        result = assign_category(vault_path, "DB_URL", "database")
        assert result["members"].count("DB_URL") == 1

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(CategoryError, match="key"):
            assign_category(vault_path, "", "database")

    def test_raises_on_empty_category(self, vault_path):
        with pytest.raises(CategoryError, match="category"):
            assign_category(vault_path, "DB_URL", "")


class TestRemoveFromCategory:
    def test_removes_key(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        assign_category(vault_path, "DB_PASS", "database")
        remaining = remove_from_category(vault_path, "DB_URL", "database")
        assert "DB_URL" not in remaining
        assert "DB_PASS" in remaining

    def test_deletes_empty_category(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        remove_from_category(vault_path, "DB_URL", "database")
        cats = list_categories(vault_path)
        assert "database" not in cats

    def test_raises_on_missing_category(self, vault_path):
        with pytest.raises(CategoryError, match="does not exist"):
            remove_from_category(vault_path, "DB_URL", "ghost")

    def test_raises_on_missing_key(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        with pytest.raises(CategoryError, match="not in category"):
            remove_from_category(vault_path, "MISSING", "database")


class TestKeysInCategory:
    def test_returns_keys(self, vault_path):
        assign_category(vault_path, "DB_URL", "database")
        assign_category(vault_path, "DB_PASS", "database")
        keys = keys_in_category(vault_path, "database")
        assert set(keys) == {"DB_URL", "DB_PASS"}

    def test_raises_on_missing_category(self, vault_path):
        with pytest.raises(CategoryError, match="does not exist"):
            keys_in_category(vault_path, "nope")

    def test_empty_vault_returns_empty_list_categories(self, vault_path):
        assert list_categories(vault_path) == {}
