"""Tests for sync CLI commands."""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli import cli
import envault.cli_sync  # noqa: F401 – registers sync sub-commands


PASSWORD = "cli-sync-test"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


@pytest.fixture()
def remote_path(tmp_path):
    return str(tmp_path / "remote.json")


def seed_vault(runner, vault_path):
    """Populate vault with two keys via CLI."""
    for key, val in [("ALPHA", "one"), ("BETA", "two")]:
        runner.invoke(cli, ["set", key, val,
                            "--vault", vault_path,
                            "--password", PASSWORD])


class TestCliSyncPush:
    def test_push_creates_remote(self, runner, vault_path, remote_path):
        seed_vault(runner, vault_path)
        result = runner.invoke(cli, ["sync", "push", remote_path,
                                     "--vault", vault_path,
                                     "--password", PASSWORD])
        assert result.exit_code == 0
        assert Path(remote_path).exists()

    def test_push_reports_count(self, runner, vault_path, remote_path):
        seed_vault(runner, vault_path)
        result = runner.invoke(cli, ["sync", "push", remote_path,
                                     "--vault", vault_path,
                                     "--password", PASSWORD])
        assert "2" in result.output


class TestCliSyncPull:
    def test_pull_imports_keys(self, runner, vault_path, remote_path, tmp_path):
        seed_vault(runner, vault_path)
        runner.invoke(cli, ["sync", "push", remote_path,
                            "--vault", vault_path,
                            "--password", PASSWORD])
        new_vault = str(tmp_path / "new.json")
        result = runner.invoke(cli, ["sync", "pull", remote_path,
                                     "--vault", new_vault,
                                     "--password", PASSWORD])
        assert result.exit_code == 0
        assert "2" in result.output

    def test_pull_missing_remote_shows_error(self, runner, vault_path, remote_path):
        result = runner.invoke(cli, ["sync", "pull", remote_path,
                                     "--vault", vault_path,
                                     "--password", PASSWORD])
        assert result.exit_code != 0
        assert "Error" in result.output


class TestCliSyncStatus:
    def test_status_shows_only_local(self, runner, vault_path, remote_path):
        seed_vault(runner, vault_path)
        result = runner.invoke(cli, ["sync", "status", remote_path,
                                     "--vault", vault_path,
                                     "--password", PASSWORD])
        assert result.exit_code == 0
        assert "Only local" in result.output

    def test_status_shows_in_sync_after_push(self, runner, vault_path, remote_path):
        seed_vault(runner, vault_path)
        runner.invoke(cli, ["sync", "push", remote_path,
                            "--vault", vault_path,
                            "--password", PASSWORD])
        result = runner.invoke(cli, ["sync", "status", remote_path,
                                     "--vault", vault_path,
                                     "--password", PASSWORD])
        assert result.exit_code == 0
        assert "In sync" in result.output
