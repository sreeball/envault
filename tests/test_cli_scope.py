"""Tests for envault.cli_scope."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_scope import scope_group
from envault.scope import add_to_scope


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


def _invoke(runner, vault_path, *args):
    return runner.invoke(scope_group, [*args, "--vault", vault_path])


class TestAddCmd:
    def test_adds_key_to_scope(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "prod", "DB_URL")
        assert result.exit_code == 0
        assert "prod" in result.output
        assert "DB_URL" in result.output

    def test_exits_nonzero_on_empty_scope(self, runner, vault_path):
        result = runner.invoke(scope_group, ["add", "", "DB_URL", "--vault", vault_path])
        assert result.exit_code != 0


class TestRemoveCmd:
    def test_removes_key(self, runner, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        result = _invoke(runner, vault_path, "remove", "prod", "DB_URL")
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_exits_nonzero_when_key_missing(self, runner, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        result = _invoke(runner, vault_path, "remove", "prod", "MISSING")
        assert result.exit_code != 0


class TestKeysCmd:
    def test_lists_keys(self, runner, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        add_to_scope(vault_path, "prod", "API_KEY")
        result = _invoke(runner, vault_path, "keys", "prod")
        assert result.exit_code == 0
        assert "DB_URL" in result.output
        assert "API_KEY" in result.output

    def test_empty_scope_message(self, runner, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        from envault.scope import remove_from_scope
        remove_from_scope(vault_path, "prod", "DB_URL")
        result = _invoke(runner, vault_path, "keys", "prod")
        assert result.exit_code == 0
        assert "empty" in result.output

    def test_exits_nonzero_on_missing_scope(self, runner, vault_path):
        result = _invoke(runner, vault_path, "keys", "ghost")
        assert result.exit_code != 0


class TestListCmd:
    def test_lists_all_scopes(self, runner, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        add_to_scope(vault_path, "staging", "API_KEY")
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "prod" in result.output
        assert "staging" in result.output

    def test_no_scopes_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No scopes" in result.output


class TestDeleteCmd:
    def test_deletes_scope(self, runner, vault_path):
        add_to_scope(vault_path, "prod", "DB_URL")
        result = _invoke(runner, vault_path, "delete", "prod")
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_exits_nonzero_on_missing_scope(self, runner, vault_path):
        result = _invoke(runner, vault_path, "delete", "ghost")
        assert result.exit_code != 0
