"""Tests for envault.cli_import CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_import import import_file_cmd, import_env_cmd
from envault.vault import Vault

PASSWORD = "test-password"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "vault.json")


# ---------------------------------------------------------------------------
# import file
# ---------------------------------------------------------------------------

class TestImportFileCmd:
    def _invoke(self, runner, source, vault_path, fmt="dotenv"):
        return runner.invoke(
            import_file_cmd,
            [source, "--fmt", fmt, "--vault", vault_path, "--password", PASSWORD],
        )

    def test_imports_dotenv(self, runner, tmp_path, vault_path):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        result = self._invoke(runner, str(env_file), vault_path)
        assert result.exit_code == 0
        assert "2 secret(s)" in result.output
        assert "2 added" in result.output

    def test_imports_json(self, runner, tmp_path, vault_path):
        json_file = tmp_path / "secrets.json"
        json_file.write_text(json.dumps({"TOKEN": "abc"}))
        result = self._invoke(runner, str(json_file), vault_path, fmt="json")
        assert result.exit_code == 0
        assert "1 secret(s)" in result.output

    def test_values_retrievable_after_import(self, runner, tmp_path, vault_path):
        env_file = tmp_path / ".env"
        env_file.write_text("MYKEY=myvalue\n")
        self._invoke(runner, str(env_file), vault_path)
        vault = Vault(vault_path)
        assert vault.get("MYKEY", PASSWORD) == "myvalue"

    def test_updated_count_on_re_import(self, runner, tmp_path, vault_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=v1\n")
        self._invoke(runner, str(env_file), vault_path)
        env_file.write_text("KEY=v2\n")
        result = self._invoke(runner, str(env_file), vault_path)
        assert "1 updated" in result.output
        assert "0 added" in result.output

    def test_invalid_json_shows_error(self, runner, tmp_path, vault_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json")
        result = self._invoke(runner, str(bad_file), vault_path, fmt="json")
        assert result.exit_code != 0
        assert "Error" in result.output


# ---------------------------------------------------------------------------
# import env
# ---------------------------------------------------------------------------

class TestImportEnvCmd:
    def _invoke(self, runner, vault_path, *keys):
        args = list(keys) + ["--vault", vault_path, "--password", PASSWORD]
        return runner.invoke(import_env_cmd, args)

    def test_imports_specific_key(self, runner, vault_path, monkeypatch):
        monkeypatch.setenv("CLI_TEST_VAR", "hello")
        result = self._invoke(runner, vault_path, "CLI_TEST_VAR")
        assert result.exit_code == 0
        assert "1 secret(s)" in result.output
        vault = Vault(vault_path)
        assert vault.get("CLI_TEST_VAR", PASSWORD) == "hello"

    def test_missing_key_shows_error(self, runner, vault_path, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_XYZ", raising=False)
        result = self._invoke(runner, vault_path, "NONEXISTENT_XYZ")
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_no_keys_imports_all(self, runner, vault_path, monkeypatch):
        monkeypatch.setenv("SOME_UNIQUE_VAR", "42")
        result = self._invoke(runner, vault_path)
        assert result.exit_code == 0
        # Should import at least the one we set
        vault = Vault(vault_path)
        assert vault.get("SOME_UNIQUE_VAR", PASSWORD) == "42"
