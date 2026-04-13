"""Tests for envault.cli_sharing."""
import json
import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli_sharing import sharing_group
from envault.vault import Vault
from envault.sharing import share_key, _shares_path


PASSWORD = "vault-pw"
SHARE_PW = "share-pw"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    path = tmp_path / "vault.json"
    v = Vault(str(path), PASSWORD)
    v.set("DB_URL", "postgres://localhost")
    return path


def _invoke(runner, *args, input_text=""):
    return runner.invoke(sharing_group, list(args), input=input_text, catch_exceptions=False)


class TestRedeemCmd:
    def test_prints_decrypted_value(self, runner, vault_path):
        share_key(vault_path, "DB_URL", "postgres://localhost", "alice", SHARE_PW)
        result = runner.invoke(
            sharing_group,
            ["redeem", str(vault_path), "DB_URL", "alice", "--share-password", SHARE_PW],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "postgres://localhost" in result.output

    def test_error_on_wrong_password(self, runner, vault_path):
        share_key(vault_path, "DB_URL", "postgres://localhost", "alice", SHARE_PW)
        result = runner.invoke(
            sharing_group,
            ["redeem", str(vault_path), "DB_URL", "alice", "--share-password", "wrong"],
        )
        assert result.exit_code != 0 or "Error" in result.output

    def test_error_when_no_share_exists(self, runner, vault_path):
        result = runner.invoke(
            sharing_group,
            ["redeem", str(vault_path), "MISSING", "alice", "--share-password", SHARE_PW],
        )
        assert result.exit_code != 0 or "Error" in result.output


class TestRevokeCmd:
    def test_revokes_share(self, runner, vault_path):
        share_key(vault_path, "DB_URL", "postgres://localhost", "alice", SHARE_PW)
        result = runner.invoke(
            sharing_group,
            ["revoke", str(vault_path), "DB_URL", "alice"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Revoked" in result.output
        shares = json.loads(_shares_path(vault_path).read_text())
        assert "DB_URL" not in shares

    def test_no_shares_message(self, runner, vault_path):
        result = runner.invoke(
            sharing_group,
            ["revoke", str(vault_path), "MISSING", "alice"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "No shares found" in result.output


class TestListCmd:
    def test_no_shares_message(self, runner, vault_path):
        result = runner.invoke(
            sharing_group,
            ["list", str(vault_path)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "No shares" in result.output

    def test_lists_existing_shares(self, runner, vault_path):
        share_key(vault_path, "DB_URL", "postgres://localhost", "alice", SHARE_PW)
        result = runner.invoke(
            sharing_group,
            ["list", str(vault_path)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "DB_URL" in result.output
        assert "alice" in result.output
