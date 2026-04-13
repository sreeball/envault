"""Tests for envault.cli_rate_limit."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli_rate_limit import rate_limit_group
from envault.rate_limit import set_limit


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return p


def _invoke(runner, vault_path, *args):
    return runner.invoke(rate_limit_group, [str(vault_path)] + list(args))


class TestSetCmd:
    def test_sets_rate_limit(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "get", "10", "60")
        assert result.exit_code == 0
        assert "Rate limit set" in result.output

    def test_shows_operation_name(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "delete", "3", "30")
        assert "delete" in result.output

    def test_invalid_max_calls_shows_error(self, runner, vault_path):
        result = _invoke(runner, vault_path, "set", "get", "0", "60")
        assert result.exit_code != 0
        assert "Error" in result.output


class TestRemoveCmd:
    def test_removes_limit(self, runner, vault_path):
        set_limit(vault_path, "get", 5, 60)
        result = _invoke(runner, vault_path, "remove", "get")
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_error_when_not_configured(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "nonexistent")
        assert result.exit_code != 0
        assert "Error" in result.output


class TestListCmd:
    def test_no_limits_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No rate limits" in result.output

    def test_lists_configured_limits(self, runner, vault_path):
        set_limit(vault_path, "get", 10, 60)
        set_limit(vault_path, "set", 5, 30)
        result = _invoke(runner, vault_path, "list")
        assert "get" in result.output
        assert "set" in result.output


class TestCheckCmd:
    def test_no_limit_configured(self, runner, vault_path):
        result = _invoke(runner, vault_path, "check", "get")
        assert result.exit_code == 0
        assert "no rate limit" in result.output

    def test_shows_remaining_calls(self, runner, vault_path):
        set_limit(vault_path, "get", 5, 60)
        result = _invoke(runner, vault_path, "check", "get")
        assert result.exit_code == 0
        assert "remaining" in result.output

    def test_error_when_exceeded(self, runner, vault_path):
        set_limit(vault_path, "get", 1, 60)
        _invoke(runner, vault_path, "check", "get")  # consume the 1 allowed call
        result = _invoke(runner, vault_path, "check", "get")
        assert result.exit_code != 0
        assert "Error" in result.output
