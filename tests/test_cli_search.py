"""Tests for the search CLI commands."""

import json

import pytest
from click.testing import CliRunner

from envault.cli_search import search_group
from envault.vault import Vault

PASSWORD = "test-pass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "vault.json")
    v = Vault(path)
    v.set("DB_HOST", "localhost", PASSWORD)
    v.set("DB_PORT", "5432", PASSWORD)
    v.set("API_KEY", "my-secret", PASSWORD)
    return path


class TestKeysCmd:
    def test_lists_matching_keys(self, runner, vault_path):
        result = runner.invoke(search_group, ["keys", "DB_*", "--vault", vault_path])
        assert result.exit_code == 0
        assert "DB_HOST" in result.output
        assert "DB_PORT" in result.output
        assert "API_KEY" not in result.output

    def test_no_match_message(self, runner, vault_path):
        result = runner.invoke(search_group, ["keys", "MISSING_*", "--vault", vault_path])
        assert result.exit_code == 0
        assert "No matching keys found" in result.output

    def test_regex_flag(self, runner, vault_path):
        result = runner.invoke(
            search_group, ["keys", "^DB", "--regex", "--vault", vault_path]
        )
        assert result.exit_code == 0
        assert "DB_HOST" in result.output

    def test_invalid_regex_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(
            search_group, ["keys", "[bad", "--regex", "--vault", vault_path]
        )
        assert result.exit_code != 0


class TestSecretsCmd:
    def _invoke(self, runner, vault_path, *extra_args):
        return runner.invoke(
            search_group,
            ["secrets", *extra_args, "--vault", vault_path],
            input=PASSWORD + "\n",
        )

    def test_table_output_contains_key_and_value(self, runner, vault_path):
        result = self._invoke(runner, vault_path, "DB_*")
        assert result.exit_code == 0
        assert "DB_HOST" in result.output
        assert "localhost" in result.output

    def test_json_format(self, runner, vault_path):
        result = self._invoke(runner, vault_path, "DB_*", "--format", "json")
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["DB_HOST"] == "localhost"

    def test_keys_format(self, runner, vault_path):
        result = self._invoke(runner, vault_path, "API_*", "--format", "keys")
        assert result.exit_code == 0
        assert "API_KEY" in result.output
        assert "my-secret" not in result.output

    def test_no_match_message(self, runner, vault_path):
        result = self._invoke(runner, vault_path, "NOTHING_*")
        assert result.exit_code == 0
        assert "No matching secrets found" in result.output
