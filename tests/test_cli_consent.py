"""Tests for envault.cli_consent."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from envault.cli_consent import consent_group
from envault.consent import grant_consent


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.db"
    p.touch()
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(consent_group, [*args, "--vault", vault_path])


class TestGrantCmd:
    def test_grants_consent(self, runner, vault_path):
        result = _invoke(runner, vault_path, "grant", "API_KEY", "alice", "analytics")
        assert result.exit_code == 0
        assert "Consent granted" in result.output

    def test_shows_note_when_provided(self, runner, vault_path):
        result = _invoke(runner, vault_path, "grant", "API_KEY", "alice", "analytics", "--note", "GDPR")
        assert result.exit_code == 0
        assert "GDPR" in result.output

    def test_fails_on_empty_key(self, runner, vault_path):
        result = runner.invoke(consent_group, ["grant", "", "alice", "analytics", "--vault", vault_path])
        assert result.exit_code != 0


class TestRevokeCmd:
    def test_revokes_consent(self, runner, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        result = _invoke(runner, vault_path, "revoke", "API_KEY", "alice")
        assert result.exit_code == 0
        assert "Revoked 1" in result.output

    def test_revokes_specific_purpose(self, runner, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        grant_consent(vault_path, "API_KEY", "alice", "reporting")
        result = _invoke(runner, vault_path, "revoke", "API_KEY", "alice", "--purpose", "analytics")
        assert result.exit_code == 0
        assert "Revoked 1" in result.output

    def test_reports_nothing_removed(self, runner, vault_path):
        result = _invoke(runner, vault_path, "revoke", "MISSING", "alice")
        assert result.exit_code == 0
        assert "No matching" in result.output


class TestCheckCmd:
    def test_exits_zero_when_granted(self, runner, vault_path):
        grant_consent(vault_path, "DB_PASS", "bob", "backup")
        result = _invoke(runner, vault_path, "check", "DB_PASS", "bob", "backup")
        assert result.exit_code == 0
        assert "GRANTED" in result.output

    def test_exits_nonzero_when_denied(self, runner, vault_path):
        result = _invoke(runner, vault_path, "check", "DB_PASS", "bob", "backup")
        assert result.exit_code != 0
        assert "DENIED" in result.output


class TestListCmd:
    def test_lists_entries_for_key(self, runner, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        result = _invoke(runner, vault_path, "list", "API_KEY")
        assert result.exit_code == 0
        assert "alice" in result.output
        assert "analytics" in result.output

    def test_no_entries_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list", "MISSING")
        assert result.exit_code == 0
        assert "No consent entries" in result.output

    def test_lists_all_when_no_key(self, runner, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        grant_consent(vault_path, "DB_PASS", "bob", "backup")
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "alice" in result.output
        assert "bob" in result.output

    def test_empty_registry_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No consent entries recorded" in result.output
