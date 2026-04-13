"""Tests for envault.cli_version."""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_version import version_group
from envault.version import record_version


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.env")


def _invoke(runner, vault_path, *args):
    return runner.invoke(version_group, ["--vault", vault_path, *args])


class TestListCmd:
    def test_no_history_message(self, runner, vault_path):
        result = runner.invoke(version_group, ["list", "--vault", vault_path, "MISSING"])
        assert result.exit_code == 0
        assert "No version history" in result.output

    def test_lists_versions(self, runner, vault_path):
        record_version(vault_path, "API_KEY", "abc")
        record_version(vault_path, "API_KEY", "xyz")
        result = runner.invoke(version_group, ["list", "--vault", vault_path, "API_KEY"])
        assert result.exit_code == 0
        assert "v1" in result.output
        assert "v2" in result.output

    def test_shows_actor(self, runner, vault_path):
        record_version(vault_path, "K", "val", actor="ci-bot")
        result = runner.invoke(version_group, ["list", "--vault", vault_path, "K"])
        assert "ci-bot" in result.output


class TestShowCmd:
    def test_shows_value_at_version(self, runner, vault_path):
        record_version(vault_path, "DB", "postgres://old")
        record_version(vault_path, "DB", "postgres://new")
        result = runner.invoke(version_group, ["show", "--vault", vault_path, "DB", "1"])
        assert result.exit_code == 0
        assert "postgres://old" in result.output

    def test_error_on_missing_key(self, runner, vault_path):
        result = runner.invoke(version_group, ["show", "--vault", vault_path, "GHOST", "1"])
        assert result.exit_code != 0
        assert "No version history" in result.output

    def test_error_on_out_of_range(self, runner, vault_path):
        record_version(vault_path, "K", "only")
        result = runner.invoke(version_group, ["show", "--vault", vault_path, "K", "99"])
        assert result.exit_code != 0
        assert "out of range" in result.output


class TestPurgeCmd:
    def test_purges_versions(self, runner, vault_path):
        record_version(vault_path, "K", "v1")
        record_version(vault_path, "K", "v2")
        result = runner.invoke(
            version_group,
            ["purge", "--vault", vault_path, "K"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "2" in result.output

    def test_purge_zero_for_unknown(self, runner, vault_path):
        result = runner.invoke(
            version_group,
            ["purge", "--vault", vault_path, "GHOST"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "0" in result.output
