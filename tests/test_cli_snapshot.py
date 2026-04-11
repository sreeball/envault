"""Tests for envault.cli_snapshot."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.snapshot import create_snapshot
from envault.cli_snapshot import snapshot_group

PASSWORD = "cli-test-pw"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "vault.db")
    v = Vault(path, PASSWORD)
    v.set("FOO", "bar")
    v.set("BAZ", "qux")
    return path


def _env(vault_path):
    return {"ENVAULT_VAULT": vault_path, "ENVAULT_PASSWORD": PASSWORD}


class TestCreateCmd:
    def test_creates_snapshot(self, runner, vault_path):
        result = runner.invoke(snapshot_group, ["create"], env=_env(vault_path))
        assert result.exit_code == 0
        assert "Snapshot created" in result.output

    def test_shows_secret_count(self, runner, vault_path):
        result = runner.invoke(snapshot_group, ["create"], env=_env(vault_path))
        assert "2 secrets" in result.output

    def test_label_appears_in_output(self, runner, vault_path):
        result = runner.invoke(
            snapshot_group, ["create", "--label", "my-label"], env=_env(vault_path)
        )
        assert "my-label" in result.output


class TestListCmd:
    def test_no_snapshots_message(self, runner, vault_path):
        result = runner.invoke(snapshot_group, ["list"], env=_env(vault_path))
        assert result.exit_code == 0
        assert "No snapshots found" in result.output

    def test_lists_created_snapshot(self, runner, vault_path):
        create_snapshot(vault_path, PASSWORD, label="v1")
        result = runner.invoke(snapshot_group, ["list"], env=_env(vault_path))
        assert "v1" in result.output
        assert "2 secrets" in result.output


class TestRestoreCmd:
    def test_restores_and_reports(self, runner, vault_path):
        snap = create_snapshot(vault_path, PASSWORD)
        Vault(vault_path, PASSWORD).set("FOO", "mutated")
        result = runner.invoke(
            snapshot_group, ["restore", snap["snapshot"]], env=_env(vault_path)
        )
        assert result.exit_code == 0
        assert "Restored 2 secrets" in result.output
        assert Vault(vault_path, PASSWORD).get("FOO") == "bar"

    def test_error_on_missing_file(self, runner, vault_path):
        result = runner.invoke(
            snapshot_group, ["restore", "/no/such/file.json"], env=_env(vault_path)
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "Error" in result.output


class TestDeleteCmd:
    def test_deletes_snapshot(self, runner, vault_path):
        snap = create_snapshot(vault_path, PASSWORD)
        result = runner.invoke(
            snapshot_group, ["delete", snap["snapshot"], "--yes"], env=_env(vault_path)
        )
        assert result.exit_code == 0
        assert not Path(snap["snapshot"]).exists()

    def test_error_on_missing_file(self, runner, vault_path):
        result = runner.invoke(
            snapshot_group, ["delete", "/no/such/snap.json", "--yes"], env=_env(vault_path)
        )
        assert result.exit_code != 0
