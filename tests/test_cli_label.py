"""Tests for envault.cli_label CLI commands."""

import pytest
from click.testing import CliRunner
from envault.cli_label import label_group
from envault.label import add_label


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


def _invoke(runner, vault_path, *args):
    return runner.invoke(label_group, [*args, "--vault", vault_path])


class TestAddCmd:
    def test_adds_label(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "DB_URL", "database")
        assert result.exit_code == 0
        assert "database" in result.output

    def test_empty_label_fails(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "DB_URL", "  ")
        assert result.exit_code != 0


class TestRemoveCmd:
    def test_removes_label(self, runner, vault_path):
        add_label(vault_path, "DB_URL", "database")
        result = _invoke(runner, vault_path, "remove", "DB_URL", "database")
        assert result.exit_code == 0
        assert "database" not in result.output or "(none)" in result.output

    def test_missing_label_fails(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "DB_URL", "ghost")
        assert result.exit_code != 0
        assert "Error" in result.output


class TestListCmd:
    def test_lists_labels(self, runner, vault_path):
        add_label(vault_path, "API_KEY", "external")
        add_label(vault_path, "API_KEY", "sensitive")
        result = _invoke(runner, vault_path, "list", "API_KEY")
        assert result.exit_code == 0
        assert "external" in result.output
        assert "sensitive" in result.output

    def test_no_labels_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list", "UNKNOWN")
        assert result.exit_code == 0
        assert "No labels" in result.output


class TestFindCmd:
    def test_finds_keys_by_label(self, runner, vault_path):
        add_label(vault_path, "DB_URL", "production")
        add_label(vault_path, "API_KEY", "production")
        result = _invoke(runner, vault_path, "find", "production")
        assert result.exit_code == 0
        assert "DB_URL" in result.output
        assert "API_KEY" in result.output

    def test_no_match_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "find", "nolabel")
        assert result.exit_code == 0
        assert "No keys found" in result.output


class TestAllCmd:
    def test_shows_all_labels(self, runner, vault_path):
        add_label(vault_path, "DB_URL", "database")
        add_label(vault_path, "API_KEY", "external")
        result = _invoke(runner, vault_path, "all")
        assert result.exit_code == 0
        assert "DB_URL" in result.output
        assert "API_KEY" in result.output

    def test_empty_message_when_no_labels(self, runner, vault_path):
        result = _invoke(runner, vault_path, "all")
        assert result.exit_code == 0
        assert "No labels defined" in result.output
