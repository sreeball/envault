"""Tests for envault.cli_ownership."""
import pytest
from click.testing import CliRunner
from envault.cli_ownership import ownership_group
from envault.ownership import set_owner


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


def _invoke(runner, vault_path, *args):
    return runner.invoke(ownership_group, [*args, "--vault", vault_path])


class TestSetCmd:
    def test_sets_owner(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "DB_PASS", "alice")
        assert result.exit_code == 0
        assert "alice" in result.output

    def test_sets_owner_with_team(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "API_KEY", "bob", "--team", "backend")
        assert result.exit_code == 0
        assert "backend" in result.output

    def test_fails_on_empty_owner(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "KEY", "")
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_owner(self, runner, vault_path):
        set_owner(vault_path, "SECRET", "carol", team="ops")
        result = _invoke(runner, vault_path, "get", "SECRET")
        assert result.exit_code == 0
        assert "carol" in result.output
        assert "ops" in result.output

    def test_fails_on_missing_key(self, runner, vault_path):
        result = _invoke(runner, vault_path, "get", "GHOST")
        assert result.exit_code != 0
        assert "no ownership record" in result.output


class TestRemoveCmd:
    def test_removes_owner(self, runner, vault_path):
        set_owner(vault_path, "TOKEN", "dave")
        result = _invoke(runner, vault_path, "remove", "TOKEN")
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_fails_on_missing_key(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "NOPE")
        assert result.exit_code != 0


class TestListCmd:
    def test_lists_all_records(self, runner, vault_path):
        set_owner(vault_path, "A", "alice")
        set_owner(vault_path, "B", "bob")
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "alice" in result.output
        assert "bob" in result.output

    def test_filters_by_owner(self, runner, vault_path):
        set_owner(vault_path, "A", "alice")
        set_owner(vault_path, "B", "bob")
        result = _invoke(runner, vault_path, "list", "--owner", "alice")
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" not in result.output

    def test_empty_message_when_no_records(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No ownership records" in result.output
