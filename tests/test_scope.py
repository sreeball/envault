"""Tests for envault.scope."""

from __future__ import annotations

import json
import pytest

from envault.scope import (
    ScopeError,
    add_to_scope,
    delete_scope,
    keys_in_scope,
    list_scopes,
    remove_from_scope,
    _scopes_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestAddToScope:
    def test_creates_scopes_file(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        assert _scopes_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = add_to_scope(vault_path, "prod", "DB_URL")
        assert result["scope"] == "prod"
        assert "DB_URL" in result["keys"]

    def test_accumulates_keys(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        result = add_to_scope(vault_path, "prod", "API_KEY")
        assert "DB_URL" in result["keys"]
        assert "API_KEY" in result["keys"]

    def test_duplicate_key_not_added_twice(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        result = add_to_scope(vault_path, "prod", "DB_URL")
        assert result["keys"].count("DB_URL") == 1

    def test_raises_on_empty_scope(self, vault_path):
        with pytest.raises(ScopeError):
            add_to_scope(vault_path, "", "DB_URL")

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(ScopeError):
            add_to_scope(vault_path, "prod", "")

    def test_multiple_scopes_independent(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        add_to_scope(vault_path, "staging", "API_KEY")
        scopes = list_scopes(vault_path)
        assert "DB_URL" in scopes["prod"]
        assert "API_KEY" in scopes["staging"]
        assert "API_KEY" not in scopes["prod"]


class TestRemoveFromScope:
    def test_removes_key(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        result = remove_from_scope(vault_path, "prod", "DB_URL")
        assert "DB_URL" not in result["keys"]

    def test_raises_when_key_missing(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        with pytest.raises(ScopeError):
            remove_from_scope(vault_path, "prod", "MISSING")


class TestKeysInScope:
    def test_returns_keys(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        add_to_scope(vault_path, "prod", "SECRET")
        assert keys_in_scope(vault_path, "prod") == ["DB_URL", "SECRET"]

    def test_raises_on_missing_scope(self, vault_path):
        with pytest.raises(ScopeError):
            keys_in_scope(vault_path, "nonexistent")


class TestDeleteScope:
    def test_deletes_scope(self, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        delete_scope(vault_path, "prod")
        assert "prod" not in list_scopes(vault_path)

    def test_raises_on_missing_scope(self, vault_path):
        with pytest.raises(ScopeError):
            delete_scope(vault_path, "ghost")
