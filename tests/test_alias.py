"""Tests for envault.alias."""

import pytest
from pathlib import Path

from envault.alias import (
    AliasError,
    add_alias,
    remove_alias,
    resolve,
    list_aliases,
    _aliases_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.enc")


class TestAddAlias:
    def test_creates_aliases_file(self, vault_path):
        add_alias(vault_path, "db", "DATABASE_URL")
        assert _aliases_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = add_alias(vault_path, "db", "DATABASE_URL")
        assert result == {"alias": "db", "key": "DATABASE_URL"}

    def test_accumulates_aliases(self, vault_path):
        add_alias(vault_path, "db", "DATABASE_URL")
        add_alias(vault_path, "redis", "REDIS_URL")
        aliases = list_aliases(vault_path)
        assert len(aliases) == 2

    def test_raises_on_duplicate(self, vault_path):
        add_alias(vault_path, "db", "DATABASE_URL")
        with pytest.raises(AliasError, match="already exists"):
            add_alias(vault_path, "db", "OTHER_KEY")


class TestRemoveAlias:
    def test_removes_alias(self, vault_path):
        add_alias(vault_path, "db", "DATABASE_URL")
        remove_alias(vault_path, "db")
        assert list_aliases(vault_path) == []

    def test_returns_removed_entry(self, vault_path):
        add_alias(vault_path, "db", "DATABASE_URL")
        result = remove_alias(vault_path, "db")
        assert result == {"alias": "db", "key": "DATABASE_URL"}

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(AliasError, match="not found"):
            remove_alias(vault_path, "missing")


class TestResolve:
    def test_returns_key_for_alias(self, vault_path):
        add_alias(vault_path, "db", "DATABASE_URL")
        assert resolve(vault_path, "db") == "DATABASE_URL"

    def test_returns_name_when_no_alias(self, vault_path):
        assert resolve(vault_path, "DATABASE_URL") == "DATABASE_URL"


class TestListAliases:
    def test_empty_when_no_file(self, vault_path):
        assert list_aliases(vault_path) == []

    def test_sorted_by_alias(self, vault_path):
        add_alias(vault_path, "z_key", "Z")
        add_alias(vault_path, "a_key", "A")
        names = [e["alias"] for e in list_aliases(vault_path)]
        assert names == ["a_key", "z_key"]
