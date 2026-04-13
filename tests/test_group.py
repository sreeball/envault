import pytest
from pathlib import Path
from envault.group import (
    GroupError,
    create_group,
    add_key_to_group,
    remove_key_from_group,
    delete_group,
    list_groups,
    get_group,
    _groups_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestCreateGroup:
    def test_creates_groups_file(self, vault_path):
        create_group(vault_path, "backend")
        assert _groups_path(vault_path).exists()

    def test_returns_group_dict(self, vault_path):
        result = create_group(vault_path, "backend")
        assert result == {"backend": []}

    def test_raises_on_duplicate(self, vault_path):
        create_group(vault_path, "backend")
        with pytest.raises(GroupError, match="already exists"):
            create_group(vault_path, "backend")

    def test_multiple_groups_coexist(self, vault_path):
        create_group(vault_path, "backend")
        create_group(vault_path, "frontend")
        groups = list_groups(vault_path)
        assert "backend" in groups
        assert "frontend" in groups


class TestAddKeyToGroup:
    def test_adds_key(self, vault_path):
        create_group(vault_path, "backend")
        result = add_key_to_group(vault_path, "backend", "DB_URL")
        assert "DB_URL" in result["backend"]

    def test_accumulates_keys(self, vault_path):
        create_group(vault_path, "backend")
        add_key_to_group(vault_path, "backend", "DB_URL")
        add_key_to_group(vault_path, "backend", "API_KEY")
        keys = get_group(vault_path, "backend")
        assert "DB_URL" in keys
        assert "API_KEY" in keys

    def test_no_duplicate_keys(self, vault_path):
        create_group(vault_path, "backend")
        add_key_to_group(vault_path, "backend", "DB_URL")
        add_key_to_group(vault_path, "backend", "DB_URL")
        keys = get_group(vault_path, "backend")
        assert keys.count("DB_URL") == 1

    def test_raises_for_missing_group(self, vault_path):
        with pytest.raises(GroupError, match="does not exist"):
            add_key_to_group(vault_path, "ghost", "KEY")


class TestRemoveKeyFromGroup:
    def test_removes_key(self, vault_path):
        create_group(vault_path, "backend")
        add_key_to_group(vault_path, "backend", "DB_URL")
        result = remove_key_from_group(vault_path, "backend", "DB_URL")
        assert "DB_URL" not in result["backend"]

    def test_noop_for_missing_key(self, vault_path):
        create_group(vault_path, "backend")
        result = remove_key_from_group(vault_path, "backend", "MISSING")
        assert result["backend"] == []

    def test_raises_for_missing_group(self, vault_path):
        with pytest.raises(GroupError):
            remove_key_from_group(vault_path, "ghost", "KEY")


class TestDeleteGroup:
    def test_deletes_group(self, vault_path):
        create_group(vault_path, "backend")
        delete_group(vault_path, "backend")
        assert "backend" not in list_groups(vault_path)

    def test_raises_for_missing_group(self, vault_path):
        with pytest.raises(GroupError):
            delete_group(vault_path, "ghost")


class TestGetGroup:
    def test_returns_keys(self, vault_path):
        create_group(vault_path, "backend")
        add_key_to_group(vault_path, "backend", "DB_URL")
        assert get_group(vault_path, "backend") == ["DB_URL"]

    def test_raises_for_missing_group(self, vault_path):
        with pytest.raises(GroupError):
            get_group(vault_path, "ghost")
