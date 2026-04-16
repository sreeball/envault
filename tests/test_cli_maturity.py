"""Tests for envault.cli_maturity."""
import pytest
from click.testing import CliRunner
from envault.cli_maturity import maturity_group
from envault.maturity import set_maturity


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


def _invoke(runner, vault_path, *args):
    return runner.invoke(maturity_group, [*args, vault_path] if args[0] in ("list",) else [args[0], vault_path, *args[1:]])


class TestSetCmd:
    def test_sets_maturity(self, runner, vault_path):
        result = runner.invoke(maturity_group, ["set", vault_path, "API_KEY", "stable"])
        assert result.exit_code == 0
        assert "stable" in result.output

    def test_sets_with_note(self, runner, vault_path):
        result = runner.invoke(maturity_group, ["set", vault_path, "API_KEY", "beta", "--note", "in review"])
        assert result.exit_code == 0

    def test_invalid_level_rejected(self, runner, vault_path):
        result = runner.invoke(maturity_group, ["set", vault_path, "API_KEY", "bogus"])
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_level(self, runner, vault_path):
        set_maturity(vault_path, "DB_PASS", "stable", note="ready")
        result = runner.invoke(maturity_group, ["get", vault_path, "DB_PASS"])
        assert result.exit_code == 0
        assert "stable" in result.output
        assert "ready" in result.output

    def test_not_set_message(self, runner, vault_path):
        result = runner.invoke(maturity_group, ["get", vault_path, "GHOST"])
        assert result.exit_code == 0
        assert "No maturity" in result.output


class TestRemoveCmd:
    def test_removes_entry(self, runner, vault_path):
        set_maturity(vault_path, "API_KEY", "stable")
        result = runner.invoke(maturity_group, ["remove", vault_path, "API_KEY"])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_not_found_message(self, runner, vault_path):
        result = runner.invoke(maturity_group, ["remove", vault_path, "GHOST"])
        assert result.exit_code == 0
        assert "No maturity entry" in result.output


class TestListCmd:
    def test_lists_all(self, runner, vault_path):
        set_maturity(vault_path, "A", "stable")
        set_maturity(vault_path, "B", "beta")
        result = runner.invoke(maturity_group, ["list", vault_path])
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" in result.output

    def test_filters_by_level(self, runner, vault_path):
        set_maturity(vault_path, "A", "stable")
        set_maturity(vault_path, "B", "beta")
        result = runner.invoke(maturity_group, ["list", vault_path, "--level", "stable"])
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" not in result.output

    def test_empty_message(self, runner, vault_path):
        result = runner.invoke(maturity_group, ["list", vault_path])
        assert result.exit_code == 0
        assert "No maturity" in result.output
