"""Tests for envault.favorite."""

from __future__ import annotations

import pytest

from envault.favorite import (
    FavoriteError,
    add_favorite,
    is_favorite,
    list_favorites,
    remove_favorite,
    _favorites_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


class TestAddFavorite:
    def test_creates_favorites_file(self, vault_path):
        add_favorite(vault_path, "DB_URL")
        assert _favorites_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = add_favorite(vault_path, "API_KEY", note="primary key")
        assert entry["key"] == "API_KEY"
        assert entry["note"] == "primary key"

    def test_empty_note_allowed(self, vault_path):
        entry = add_favorite(vault_path, "SECRET")
        assert entry["note"] == ""

    def test_accumulates_favorites(self, vault_path):
        add_favorite(vault_path, "KEY_A")
        add_favorite(vault_path, "KEY_B")
        favs = list_favorites(vault_path)
        keys = [f["key"] for f in favs]
        assert "KEY_A" in keys
        assert "KEY_B" in keys

    def test_overwrite_existing_favorite(self, vault_path):
        add_favorite(vault_path, "KEY_A", note="old")
        add_favorite(vault_path, "KEY_A", note="new")
        favs = list_favorites(vault_path)
        entries = [f for f in favs if f["key"] == "KEY_A"]
        assert len(entries) == 1
        assert entries[0]["note"] == "new"


class TestRemoveFavorite:
    def test_removes_existing_favorite(self, vault_path):
        add_favorite(vault_path, "DB_URL")
        remove_favorite(vault_path, "DB_URL")
        assert not is_favorite(vault_path, "DB_URL")

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(FavoriteError, match="not a favorite"):
            remove_favorite(vault_path, "MISSING_KEY")


class TestListFavorites:
    def test_empty_when_no_file(self, vault_path):
        assert list_favorites(vault_path) == []

    def test_returns_all_entries(self, vault_path):
        add_favorite(vault_path, "A")
        add_favorite(vault_path, "B")
        assert len(list_favorites(vault_path)) == 2


class TestIsFavorite:
    def test_true_for_added_key(self, vault_path):
        add_favorite(vault_path, "MY_KEY")
        assert is_favorite(vault_path, "MY_KEY") is True

    def test_false_for_missing_key(self, vault_path):
        assert is_favorite(vault_path, "GHOST") is False

    def test_false_after_removal(self, vault_path):
        add_favorite(vault_path, "TEMP")
        remove_favorite(vault_path, "TEMP")
        assert is_favorite(vault_path, "TEMP") is False
