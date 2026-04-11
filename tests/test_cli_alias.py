"""Tests for envault.cli_alias."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli_alias import alias_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.enc")


def _invoke(runner, vault_path, *args):
    return runner.invoke(alias_group, [*args, "--vault", vault_path], catch_exceptions=False)


class TestAddCmd:
    def test_registers_alias(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "db", "DATABASE_URL")
        assert result.exit_code == 0
        assert "db" in result.output
        assert "DATABASE_URL" in result.output

    def test_duplicate_alias_shows_error(self, runner, vault_path):
        _invoke(runner, vault_path, "add", "db", "DATABASE_URL")
        result = runner.invoke(alias_group, ["add", "db", "OTHER", "--vault", vault_path])
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestRemoveCmd:
    def test_removes_alias(self, runner, vault_path):
        _invoke(runner, vault_path, "add", "db", "DATABASE_URL")
        result = _invoke(runner, vault_path, "remove", "db")
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_missing_alias_shows_error(self, runner, vault_path):
        result = runner.invoke(alias_group, ["remove", "ghost", "--vault", vault_path])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestResolveCmd:
    def test_resolves_known_alias(self, runner, vault_path):
        _invoke(runner, vault_path, "add", "db", "DATABASE_URL")
        result = _invoke(runner, vault_path, "resolve", "db")
        assert result.exit_code == 0
        assert "DATABASE_URL" in result.output

    def test_passthrough_unknown_name(self, runner, vault_path):
        result = _invoke(runner, vault_path, "resolve", "DATABASE_URL")
        assert result.exit_code == 0
        assert "DATABASE_URL" in result.output


class TestListCmd:
    def test_no_aliases_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No aliases" in result.output

    def test_lists_added_aliases(self, runner, vault_path):
        _invoke(runner, vault_path, "add", "db", "DATABASE_URL")
        _invoke(runner, vault_path, "add", "redis", "REDIS_URL")
        result = _invoke(runner, vault_path, "list")
        assert "db" in result.output
        assert "redis" in result.output
