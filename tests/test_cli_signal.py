"""Tests for envault.cli_signal CLI commands."""
import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_signal import signal_group
from envault.signal import emit_signal


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(signal_group, [*args, vault_path] if args[0] in ("list",) else [args[0], vault_path, *args[1:]])


class TestEmitCmd:
    def test_emits_signal(self, runner, vault_path):
        result = runner.invoke(signal_group, ["emit", vault_path, "API_KEY", "on_change"])
        assert result.exit_code == 0
        assert "on_change" in result.output

    def test_emits_with_payload(self, runner, vault_path):
        result = runner.invoke(signal_group, ["emit", vault_path, "API_KEY", "on_rotate", "--payload", "ctx"])
        assert result.exit_code == 0

    def test_error_on_empty_key(self, runner, vault_path):
        result = runner.invoke(signal_group, ["emit", vault_path, "", "on_change"])
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_signals(self, runner, vault_path):
        emit_signal(vault_path, "DB_PASS", "on_expire", "some_payload")
        result = runner.invoke(signal_group, ["get", vault_path, "DB_PASS"])
        assert result.exit_code == 0
        assert "on_expire" in result.output
        assert "some_payload" in result.output

    def test_no_signals_message(self, runner, vault_path):
        result = runner.invoke(signal_group, ["get", vault_path, "GHOST"])
        assert result.exit_code == 0
        assert "No signals" in result.output


class TestClearCmd:
    def test_clears_signals(self, runner, vault_path):
        emit_signal(vault_path, "KEY", "on_change")
        result = runner.invoke(signal_group, ["clear", vault_path, "KEY"])
        assert result.exit_code == 0
        assert "1" in result.output

    def test_zero_when_no_signals(self, runner, vault_path):
        result = runner.invoke(signal_group, ["clear", vault_path, "MISSING"])
        assert "0" in result.output


class TestListCmd:
    def test_lists_keys_with_signals(self, runner, vault_path):
        emit_signal(vault_path, "A", "on_change")
        emit_signal(vault_path, "B", "on_expire")
        result = runner.invoke(signal_group, ["list", vault_path])
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" in result.output

    def test_no_signals_message(self, runner, vault_path):
        result = runner.invoke(signal_group, ["list", vault_path])
        assert "No signals" in result.output
