"""Tests for envault.namespace."""

import pytest

from envault.namespace import (
    NamespaceError,
    add_to_namespace,
    delete_namespace,
    keys_in_namespace,
    list_namespaces,
    remove_from_namespace,
)


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


class TestAddToNamespace:
    def test_creates_namespace_file(self, vault_path, tmp_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        ns_file = tmp_path / ".envault_namespaces.json"
        assert ns_file.exists()

    def test_returns_namespace_dict(self, vault_path):
        result = add_to_namespace(vault_path, "app", "DB_URL")
        assert result["namespace"] == "app"
        assert "DB_URL" in result["keys"]

    def test_accumulates_keys(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        result = add_to_namespace(vault_path, "app", "SECRET_KEY")
        assert "DB_URL" in result["keys"]
        assert "SECRET_KEY" in result["keys"]

    def test_duplicate_key_not_added_twice(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        result = add_to_namespace(vault_path, "app", "DB_URL")
        assert result["keys"].count("DB_URL") == 1

    def test_raises_on_empty_namespace(self, vault_path):
        with pytest.raises(NamespaceError):
            add_to_namespace(vault_path, "", "DB_URL")

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(NamespaceError):
            add_to_namespace(vault_path, "app", "")

    def test_multiple_namespaces(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        add_to_namespace(vault_path, "worker", "QUEUE_URL")
        data = list_namespaces(vault_path)
        assert "app" in data
        assert "worker" in data


class TestRemoveFromNamespace:
    def test_removes_key(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        add_to_namespace(vault_path, "app", "SECRET_KEY")
        result = remove_from_namespace(vault_path, "app", "DB_URL")
        assert "DB_URL" not in result["keys"]

    def test_deletes_namespace_when_empty(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        remove_from_namespace(vault_path, "app", "DB_URL")
        data = list_namespaces(vault_path)
        assert "app" not in data

    def test_raises_on_missing_namespace(self, vault_path):
        with pytest.raises(NamespaceError):
            remove_from_namespace(vault_path, "ghost", "KEY")

    def test_raises_on_missing_key(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        with pytest.raises(NamespaceError):
            remove_from_namespace(vault_path, "app", "MISSING")


class TestListNamespaces:
    def test_empty_when_no_file(self, vault_path):
        assert list_namespaces(vault_path) == {}

    def test_returns_all_namespaces(self, vault_path):
        add_to_namespace(vault_path, "a", "K1")
        add_to_namespace(vault_path, "b", "K2")
        data = list_namespaces(vault_path)
        assert "a" in data
        assert "b" in data

    def test_returns_dict_type(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        result = list_namespaces(vault_path)
        assert isinstance(result, dict)


class TestKeysInNamespace:
    def test_returns_keys_for_namespace(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        add_to_namespace(vault_path, "app", "SECRET_KEY")
        keys = keys_in_namespace(vault_path, "app")
        assert "DB_URL" in keys
        assert "SECRET_KEY" in keys

    def test_raises_on_missing_namespace(self, vault_path):
        with pytest.raises(NamespaceError):
            keys_in_namespace(vault_path, "nonexistent")

    def test_returns_list_type(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        result = keys_in_namespace(vault_path, "app")
        assert isinstance(result, list)


class TestDeleteNamespace:
    def test_deletes_existing_namespace(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        delete_namespace(vault_path, "app")
        data = list_namespaces(vault_path)
        assert "app" not in data

    def test_raises_on_missing_namespace(self, vault_path):
        with pytest.raises(NamespaceError):
            delete_namespace(vault_path, "ghost")

    def test_does_not_affect_other_namespaces(self, vault_path):
        add_to_namespace(vault_path, "app", "DB_URL")
        add_to_namespace(vault_path, "worker", "QUEUE_URL")
        delete_namespace(vault_path, "app")
        data = list_namespaces(vault_path)
        assert "worker" in data
