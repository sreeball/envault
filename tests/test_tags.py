"""Tests for envault.tags"""

import json
import pytest
from pathlib import Path

from envault.tags import (
    TagError,
    add_tag,
    remove_tag,
    get_tags,
    keys_by_tag,
    all_tags,
    _tags_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.vault")


class TestAddTag:
    def test_creates_tags_file(self, vault_path):
        add_tag(vault_path, "DB_URL", "database")
        assert _tags_path(vault_path).exists()

    def test_returns_tag_list(self, vault_path):
        result = add_tag(vault_path, "DB_URL", "database")
        assert result == ["database"]

    def test_accumulates_tags(self, vault_path):
        add_tag(vault_path, "DB_URL", "database")
        result = add_tag(vault_path, "DB_URL", "production")
        assert "database" in result
        assert "production" in result

    def test_duplicate_tag_not_added(self, vault_path):
        add_tag(vault_path, "DB_URL", "database")
        result = add_tag(vault_path, "DB_URL", "database")
        assert result.count("database") == 1

    def test_empty_tag_raises(self, vault_path):
        with pytest.raises(TagError):
            add_tag(vault_path, "DB_URL", "")


class TestRemoveTag:
    def test_removes_existing_tag(self, vault_path):
        add_tag(vault_path, "API_KEY", "sensitive")
        result = remove_tag(vault_path, "API_KEY", "sensitive")
        assert "sensitive" not in result

    def test_missing_tag_raises(self, vault_path):
        with pytest.raises(TagError, match="not found"):
            remove_tag(vault_path, "API_KEY", "ghost")


class TestGetTags:
    def test_returns_empty_for_unknown_key(self, vault_path):
        assert get_tags(vault_path, "MISSING") == []

    def test_returns_assigned_tags(self, vault_path):
        add_tag(vault_path, "SECRET", "alpha")
        add_tag(vault_path, "SECRET", "beta")
        assert get_tags(vault_path, "SECRET") == ["alpha", "beta"]


class TestKeysByTag:
    def test_returns_keys_with_tag(self, vault_path):
        add_tag(vault_path, "DB_URL", "prod")
        add_tag(vault_path, "API_KEY", "prod")
        add_tag(vault_path, "SECRET", "dev")
        result = keys_by_tag(vault_path, "prod")
        assert set(result) == {"DB_URL", "API_KEY"}

    def test_no_match_returns_empty(self, vault_path):
        assert keys_by_tag(vault_path, "nonexistent") == []


class TestAllTags:
    def test_returns_full_mapping(self, vault_path):
        add_tag(vault_path, "X", "t1")
        add_tag(vault_path, "Y", "t2")
        mapping = all_tags(vault_path)
        assert mapping["X"] == ["t1"]
        assert mapping["Y"] == ["t2"]

    def test_empty_vault_returns_empty_dict(self, vault_path):
        assert all_tags(vault_path) == {}
