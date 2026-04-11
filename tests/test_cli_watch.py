"""Tests for envault.cli_watch."""

import time
import threading
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_watch import watch_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text('{}')
    return p


class TestStartCmd:
    def test_exits_cleanly_on_timeout(self, runner, vault_path):
        result = runner.invoke(
            watch_group,
            ["start", "--vault", str(vault_path), "--interval", "0.1", "--timeout", "0.3"],
        )
        assert result.exit_code == 0
        assert "Watch ended" in result.output

    def test_reports_zero_changes_when_idle(self, runner, vault_path):
        result = runner.invoke(
            watch_group,
            ["start", "--vault", str(vault_path), "--interval", "0.1", "--timeout", "0.3"],
        )
        assert "0 change(s)" in result.output

    def test_reports_change_count(self, runner, vault_path):
        def _mutate():
            time.sleep(0.15)
            vault_path.write_text('{"x": 1}')

        t = threading.Thread(target=_mutate, daemon=True)
        t.start()
        result = runner.invoke(
            watch_group,
            ["start", "--vault", str(vault_path), "--interval", "0.05", "--timeout", "0.6"],
        )
        assert result.exit_code == 0
        assert "change(s) detected" in result.output

    def test_error_on_missing_vault(self, runner, tmp_path):
        missing = tmp_path / "nope.db"
        result = runner.invoke(
            watch_group,
            ["start", "--vault", str(missing), "--interval", "0.1", "--timeout", "0.2"],
        )
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_watching_message_shown(self, runner, vault_path):
        result = runner.invoke(
            watch_group,
            ["start", "--vault", str(vault_path), "--interval", "0.1", "--timeout", "0.2"],
        )
        assert "Watching" in result.output
