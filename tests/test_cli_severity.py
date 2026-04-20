"""Tests for envault.cli_severity."""

import pytest
from click.testing import CliRunner

from envault.cli_severity import severity_group
from envault.severity import set_severity, get_severity


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


def _invoke(runner, vault_path, *args):
    return runner.invoke(severity_group, [*args, "--vault", vault_path])


class TestSetCmd:
    def test_sets_severity(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "DB_PASS", "high")
        assert result.exit_code == 0
        assert "high" in result.output

    def test_sets_severity_with_note(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "TOKEN", "critical", "--note", "Rotate soon")
        assert result.exit_code == 0
        entry = get_severity(vault_path, "TOKEN")
        assert entry["note"] == "Rotate soon"

    def test_invalid_level_fails(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "KEY", "extreme")
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_level(self, runner, vault_path):
        set_severity(vault_path, "API_KEY", "medium", note="")
        result = _invoke(runner, vault_path, "get", "API_KEY")
        assert result.exit_code == 0
        assert "medium" in result.output

    def test_shows_note_when_present(self, runner, vault_path):
        set_severity(vault_path, "API_KEY", "high", note="Very important")
        result = _invoke(runner, vault_path, "get", "API_KEY")
        assert "Very important" in result.output

    def test_missing_key_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "get", "GHOST")
        assert result.exit_code == 0
        assert "No severity" in result.output


class TestRemoveCmd:
    def test_removes_existing_key(self, runner, vault_path):
        set_severity(vault_path, "KEY", "low")
        result = _invoke(runner, vault_path, "remove", "KEY")
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_reports_missing_key(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "GHOST")
        assert result.exit_code == 0
        assert "No severity entry" in result.output


class TestListCmd:
    def test_lists_all_entries(self, runner, vault_path):
        set_severity(vault_path, "A", "low")
        set_severity(vault_path, "B", "critical")
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" in result.output

    def test_empty_message_when_none(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No severity entries" in result.output
