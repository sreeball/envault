"""Tests for envault.cli_lock"""

import pytest
from click.testing import CliRunner

from envault.cli_lock import lock_group
from envault.lock import lock_vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    vp = tmp_path / "vault.json"
    vp.write_text("{}")
    return str(vp)


def _invoke(runner, *args):
    return runner.invoke(lock_group, list(args))


class TestAcquireCmd:
    def test_locks_vault(self, runner, vault_path, tmp_path):
        result = _invoke(runner, "acquire", "--vault", vault_path)
        assert result.exit_code == 0
        assert (tmp_path / "vault.lock").exists()

    def test_success_message(self, runner, vault_path):
        result = _invoke(runner, "acquire", "--vault", vault_path)
        assert "locked" in result.output.lower()

    def test_reason_echoed(self, runner, vault_path):
        result = _invoke(runner, "acquire", "--vault", vault_path, "--reason", "deploy")
        assert "deploy" in result.output

    def test_error_when_already_locked(self, runner, vault_path):
        lock_vault(vault_path)
        result = _invoke(runner, "acquire", "--vault", vault_path)
        assert result.exit_code == 1
        assert "already locked" in result.output.lower()


class TestReleaseCmd:
    def test_unlocks_vault(self, runner, vault_path, tmp_path):
        lock_vault(vault_path)
        result = _invoke(runner, "release", "--vault", vault_path)
        assert result.exit_code == 0
        assert not (tmp_path / "vault.lock").exists()

    def test_success_message(self, runner, vault_path):
        lock_vault(vault_path)
        result = _invoke(runner, "release", "--vault", vault_path)
        assert "unlocked" in result.output.lower()

    def test_error_when_not_locked(self, runner, vault_path):
        result = _invoke(runner, "release", "--vault", vault_path)
        assert result.exit_code == 1
        assert "not locked" in result.output.lower()


class TestStatusCmd:
    def test_unlocked_message(self, runner, vault_path):
        result = _invoke(runner, "status", "--vault", vault_path)
        assert result.exit_code == 0
        assert "unlocked" in result.output.lower()

    def test_locked_message(self, runner, vault_path):
        lock_vault(vault_path, reason="freeze", actor="ci")
        result = _invoke(runner, "status", "--vault", vault_path)
        assert "locked" in result.output.lower()
        assert "freeze" in result.output
        assert "ci" in result.output
