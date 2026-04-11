import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_access import access_group
from envault.vault import Vault

PASSWORD = "testpass"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    p = str(tmp_path / "vault.db")
    v = Vault(p, PASSWORD)
    v.set("DB_PASSWORD", "secret")
    v.set("API_KEY", "key123")
    return p


def _invoke(runner, vault_path, *args):
    return runner.invoke(
        access_group,
        ["--vault", vault_path, "--password", PASSWORD, *args],
        catch_exceptions=False,
    )


class TestGrantCmd:
    def test_grants_read_permission(self, runner, vault_path):
        result = runner.invoke(
            access_group,
            ["grant", "alice", "DB_PASSWORD"],
            obj={"vault_path": vault_path, "password": PASSWORD},
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Granted" in result.output

    def test_creates_access_file(self, runner, vault_path):
        runner.invoke(
            access_group,
            ["grant", "alice", "DB_PASSWORD"],
            obj={"vault_path": vault_path, "password": PASSWORD},
        )
        access_file = Path(vault_path).with_suffix(".access.json")
        assert access_file.exists()

    def test_grant_write_permission(self, runner, vault_path):
        result = runner.invoke(
            access_group,
            ["grant", "bob", "API_KEY", "--permission", "write"],
            obj={"vault_path": vault_path, "password": PASSWORD},
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "write" in result.output


class TestRevokeCmd:
    def test_revoke_removes_permission(self, runner, vault_path):
        runner.invoke(
            access_group,
            ["grant", "alice", "DB_PASSWORD"],
            obj={"vault_path": vault_path, "password": PASSWORD},
        )
        result = runner.invoke(
            access_group,
            ["revoke", "alice", "DB_PASSWORD"],
            obj={"vault_path": vault_path, "password": PASSWORD},
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Revoked" in result.output

    def test_revoke_nonexistent_shows_error(self, runner, vault_path):
        result = runner.invoke(
            access_group,
            ["revoke", "ghost", "MISSING"],
            obj={"vault_path": vault_path, "password": PASSWORD},
        )
        assert result.exit_code != 0


class TestCheckCmd:
    def test_allowed_after_grant(self, runner, vault_path):
        runner.invoke(
            access_group,
            ["grant", "alice", "DB_PASSWORD"],
            obj={"vault_path": vault_path, "password": PASSWORD},
        )
        result = runner.invoke(
            access_group,
            ["check", "alice", "DB_PASSWORD"],
            obj={"vault_path": vault_path, "password": PASSWORD},
            catch_exceptions=False,
        )
        assert "allowed" in result.output

    def test_denied_without_grant(self, runner, vault_path):
        result = runner.invoke(
            access_group,
            ["check", "nobody", "API_KEY"],
            obj={"vault_path": vault_path, "password": PASSWORD},
            catch_exceptions=False,
        )
        assert "denied" in result.output


class TestListCmd:
    def test_no_rules_message(self, runner, vault_path):
        result = runner.invoke(
            access_group,
            ["list"],
            obj={"vault_path": vault_path, "password": PASSWORD},
            catch_exceptions=False,
        )
        assert "No access rules" in result.output

    def test_lists_granted_permissions(self, runner, vault_path):
        runner.invoke(
            access_group,
            ["grant", "alice", "DB_PASSWORD"],
            obj={"vault_path": vault_path, "password": PASSWORD},
        )
        result = runner.invoke(
            access_group,
            ["list"],
            obj={"vault_path": vault_path, "password": PASSWORD},
            catch_exceptions=False,
        )
        assert "alice" in result.output
        assert "DB_PASSWORD" in result.output
