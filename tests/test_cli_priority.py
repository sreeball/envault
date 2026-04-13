"""Tests for envault.cli_priority."""
import pytest
from click.testing import CliRunner

from envault.cli_priority import priority_group
from envault.priority import set_priority


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(priority_group, ["--vault", vault_path, *args])


class TestSetCmd:
    def test_sets_priority(self, runner, vault_path):
        result = runner.invoke(priority_group, ["set", "API_KEY", "high", "--vault", vault_path])
        assert result.exit_code == 0
        assert "high" in result.output

    def test_invalid_level_rejected(self, runner, vault_path):
        result = runner.invoke(priority_group, ["set", "API_KEY", "urgent", "--vault", vault_path])
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_level(self, runner, vault_path):
        set_priority(vault_path, "DB_PASS", "critical")
        result = runner.invoke(priority_group, ["get", "DB_PASS", "--vault", vault_path])
        assert result.exit_code == 0
        assert "critical" in result.output

    def test_missing_key_message(self, runner, vault_path):
        result = runner.invoke(priority_group, ["get", "GHOST", "--vault", vault_path])
        assert result.exit_code == 0
        assert "No priority" in result.output


class TestRemoveCmd:
    def test_removes_priority(self, runner, vault_path):
        set_priority(vault_path, "TOKEN", "low")
        result = runner.invoke(priority_group, ["remove", "TOKEN", "--vault", vault_path])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_error_on_missing_key(self, runner, vault_path):
        result = runner.invoke(priority_group, ["remove", "GHOST", "--vault", vault_path])
        assert result.exit_code == 1


class TestListCmd:
    def test_lists_all_entries(self, runner, vault_path):
        set_priority(vault_path, "A", "high")
        set_priority(vault_path, "B", "low")
        result = runner.invoke(priority_group, ["list", "--vault", vault_path])
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" in result.output

    def test_filter_by_level(self, runner, vault_path):
        set_priority(vault_path, "A", "high")
        set_priority(vault_path, "B", "low")
        result = runner.invoke(priority_group, ["list", "--vault", vault_path, "--level", "high"])
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" not in result.output

    def test_empty_message_when_no_priorities(self, runner, vault_path):
        result = runner.invoke(priority_group, ["list", "--vault", vault_path])
        assert result.exit_code == 0
        assert "No priorities" in result.output
