"""Tests for envault.ownership."""
import pytest
from pathlib import Path
from envault.ownership import (
    OwnershipError,
    set_owner,
    get_owner,
    remove_owner,
    list_owned_by,
    list_all,
    _ownership_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetOwner:
    def test_creates_ownership_file(self, vault_path):
        set_owner(vault_path, "DB_PASS", "alice")
        assert _ownership_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_owner(vault_path, "DB_PASS", "alice")
        assert entry["owner"] == "alice"
        assert entry["team"] is None

    def test_stores_team(self, vault_path):
        entry = set_owner(vault_path, "API_KEY", "bob", team="backend")
        assert entry["team"] == "backend"

    def test_overwrites_existing_owner(self, vault_path):
        set_owner(vault_path, "DB_PASS", "alice")
        set_owner(vault_path, "DB_PASS", "charlie")
        assert get_owner(vault_path, "DB_PASS")["owner"] == "charlie"

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(OwnershipError):
            set_owner(vault_path, "", "alice")

    def test_raises_on_empty_owner(self, vault_path):
        with pytest.raises(OwnershipError):
            set_owner(vault_path, "DB_PASS", "")


class TestGetOwner:
    def test_returns_correct_entry(self, vault_path):
        set_owner(vault_path, "SECRET", "dave", team="ops")
        entry = get_owner(vault_path, "SECRET")
        assert entry["owner"] == "dave"
        assert entry["team"] == "ops"

    def test_raises_for_missing_key(self, vault_path):
        with pytest.raises(OwnershipError, match="no ownership record"):
            get_owner(vault_path, "MISSING")


class TestRemoveOwner:
    def test_removes_entry(self, vault_path):
        set_owner(vault_path, "TOKEN", "eve")
        remove_owner(vault_path, "TOKEN")
        assert "TOKEN" not in list_all(vault_path)

    def test_raises_for_missing_key(self, vault_path):
        with pytest.raises(OwnershipError):
            remove_owner(vault_path, "GHOST")


class TestListOwnedBy:
    def test_returns_keys_for_owner(self, vault_path):
        set_owner(vault_path, "A", "alice")
        set_owner(vault_path, "B", "bob")
        set_owner(vault_path, "C", "alice")
        assert sorted(list_owned_by(vault_path, "alice")) == ["A", "C"]

    def test_returns_empty_when_no_match(self, vault_path):
        set_owner(vault_path, "X", "alice")
        assert list_owned_by(vault_path, "nobody") == []


class TestListAll:
    def test_returns_full_map(self, vault_path):
        set_owner(vault_path, "K1", "alice")
        set_owner(vault_path, "K2", "bob", team="infra")
        data = list_all(vault_path)
        assert "K1" in data and "K2" in data

    def test_empty_vault_returns_empty_dict(self, vault_path):
        assert list_all(vault_path) == {}
