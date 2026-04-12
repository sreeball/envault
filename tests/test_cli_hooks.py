"""Tests for envault.cli_hooks."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_hooks import hooks_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "test.vault"
    p.write_text("{}")
    return str(p)


def _add(runner, vault_path, event, command):
    return runner.invoke(hooks_group, ["add", "--vault", vault_path, event, command])


def _remove(runner, vault_path, event, command):
    return runner.invoke(hooks_group, ["remove", "--vault", vault_path, event, command])


class TestAddCmd:
    def test_registers_hook(self, runner, vault_path):
        result = _add(runner, vault_path, "post_set", "echo hi")
        assert result.exit_code == 0
        assert "Hook registered" in result.output

    def test_output_contains_event_and_command(self, runner, vault_path):
        result = _add(runner, vault_path, "pre_get", "logger info")
        assert "pre_get" in result.output
        assert "logger info" in result.output

    def test_unknown_event_fails(self, runner, vault_path):
        result = _add(runner, vault_path, "on_magic", "echo boom")
        assert result.exit_code != 0
        assert "Unknown event" in result.output


class TestRemoveCmd:
    def test_removes_hook(self, runner, vault_path):
        _add(runner, vault_path, "post_set", "echo hi")
        result = _remove(runner, vault_path, "post_set", "echo hi")
        assert result.exit_code == 0
        assert "Hook removed" in result.output

    def test_remove_nonexistent_fails(self, runner, vault_path):
        result = _remove(runner, vault_path, "post_set", "echo ghost")
        assert result.exit_code != 0
        assert "not found" in result.output


class TestListCmd:
    def test_empty_message_when_no_hooks(self, runner, vault_path):
        result = runner.invoke(hooks_group, ["list", "--vault", vault_path])
        assert result.exit_code == 0
        assert "No hooks" in result.output

    def test_lists_registered_hooks(self, runner, vault_path):
        _add(runner, vault_path, "post_set", "echo a")
        _add(runner, vault_path, "pre_get", "echo b")
        result = runner.invoke(hooks_group, ["list", "--vault", vault_path])
        assert "post_set" in result.output
        assert "pre_get" in result.output


class TestFireCmd:
    def test_fires_registered_hooks(self, runner, vault_path):
        _add(runner, vault_path, "post_set", "true")
        result = runner.invoke(hooks_group, ["fire", "--vault", vault_path, "post_set"])
        assert result.exit_code == 0
        assert "Fired 1 hook" in result.output

    def test_no_hooks_message(self, runner, vault_path):
        result = runner.invoke(hooks_group, ["fire", "--vault", vault_path, "pre_set"])
        assert result.exit_code == 0
        assert "No hooks" in result.output
