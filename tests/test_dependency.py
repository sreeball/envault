"""Tests for envault.dependency."""

import pytest

from envault.dependency import (
    DependencyError,
    add_dependency,
    check_satisfied,
    get_dependencies,
    list_all,
    remove_dependency,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestAddDependency:
    def test_creates_deps_file(self, vault_path, tmp_path):
        add_dependency(vault_path, "DB_URL", "DB_HOST")
        assert (tmp_path / ".envault_deps.json").exists()

    def test_returns_entry_dict(self, vault_path):
        result = add_dependency(vault_path, "DB_URL", "DB_HOST")
        assert result["key"] == "DB_URL"
        assert "DB_HOST" in result["depends_on"]

    def test_accumulates_dependencies(self, vault_path):
        add_dependency(vault_path, "DB_URL", "DB_HOST")
        result = add_dependency(vault_path, "DB_URL", "DB_PORT")
        assert set(result["depends_on"]) == {"DB_HOST", "DB_PORT"}

    def test_raises_on_self_dependency(self, vault_path):
        with pytest.raises(DependencyError, match="itself"):
            add_dependency(vault_path, "KEY", "KEY")

    def test_raises_on_duplicate(self, vault_path):
        add_dependency(vault_path, "DB_URL", "DB_HOST")
        with pytest.raises(DependencyError, match="already registered"):
            add_dependency(vault_path, "DB_URL", "DB_HOST")


class TestRemoveDependency:
    def test_removes_existing_dependency(self, vault_path):
        add_dependency(vault_path, "DB_URL", "DB_HOST")
        add_dependency(vault_path, "DB_URL", "DB_PORT")
        remaining = remove_dependency(vault_path, "DB_URL", "DB_HOST")
        assert "DB_HOST" not in remaining
        assert "DB_PORT" in remaining

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(DependencyError, match="not found"):
            remove_dependency(vault_path, "DB_URL", "DB_HOST")

    def test_cleans_up_empty_key(self, vault_path):
        add_dependency(vault_path, "DB_URL", "DB_HOST")
        remove_dependency(vault_path, "DB_URL", "DB_HOST")
        assert "DB_URL" not in list_all(vault_path)


class TestGetDependencies:
    def test_returns_empty_list_for_unknown_key(self, vault_path):
        assert get_dependencies(vault_path, "UNKNOWN") == []

    def test_returns_registered_deps(self, vault_path):
        add_dependency(vault_path, "APP_URL", "APP_HOST")
        assert get_dependencies(vault_path, "APP_URL") == ["APP_HOST"]


class TestCheckSatisfied:
    def test_all_satisfied_returns_empty(self, vault_path):
        add_dependency(vault_path, "DB_URL", "DB_HOST")
        result = check_satisfied(vault_path, ["DB_URL", "DB_HOST"])
        assert result == {}

    def test_missing_dep_reported(self, vault_path):
        add_dependency(vault_path, "DB_URL", "DB_HOST")
        result = check_satisfied(vault_path, ["DB_URL"])
        assert "DB_URL" in result
        assert "DB_HOST" in result["DB_URL"]

    def test_no_deps_file_returns_empty(self, vault_path):
        assert check_satisfied(vault_path, ["ANY_KEY"]) == {}
