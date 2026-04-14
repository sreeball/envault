"""Tests for envault.cli_delegation."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_delegation import delegation_group
from envault.delegation import create_delegation, list_delegations


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.json"
    p.write_text("{}")
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(
        delegation_group,
        ["--vault", vault_path, *args],
        catch_exceptions=False,
    )


class TestCreateCmd:
    def test_creates_delegation(self, runner, vault_path):
        result = runner.invoke(
            delegation_group,
            ["create", "--vault", vault_path, "--password", "pw", "alice", "DB_URL"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Token" in result.output

    def test_shows_expiry(self, runner, vault_path):
        result = runner.invoke(
            delegation_group,
            ["create", "--vault", vault_path, "--password", "pw", "bob", "SECRET"],
            catch_exceptions=False,
        )
        assert "Expires" in result.output

    def test_empty_delegatee_fails(self, runner, vault_path):
        result = runner.invoke(
            delegation_group,
            ["create", "--vault", vault_path, "--password", "pw", "", "KEY"],
        )
        assert result.exit_code != 0


class TestRevokeCmd:
    def test_revokes_existing_token(self, runner, vault_path):
        entry = create_delegation(vault_path, "alice", ["A"])
        result = _invoke(runner, vault_path, "revoke", entry["token"])
        assert result.exit_code == 0
        assert "Revoked" in result.output

    def test_revoke_unknown_token_fails(self, runner, vault_path):
        result = runner.invoke(
            delegation_group,
            ["revoke", "--vault", vault_path, "no-such-token"],
        )
        assert result.exit_code != 0


class TestCheckCmd:
    def test_allowed_prints_allowed(self, runner, vault_path):
        entry = create_delegation(vault_path, "alice", ["DB_URL"])
        result = _invoke(runner, vault_path, "check", entry["token"], "DB_URL")
        assert result.exit_code == 0
        assert "allowed" in result.output

    def test_denied_exits_nonzero(self, runner, vault_path):
        entry = create_delegation(vault_path, "alice", ["DB_URL"])
        result = _invoke(runner, vault_path, "check", entry["token"], "OTHER")
        assert result.exit_code != 0
        assert "denied" in result.output


class TestListCmd:
    def test_no_delegations_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert "No delegations" in result.output

    def test_lists_delegations(self, runner, vault_path):
        create_delegation(vault_path, "alice", ["A", "B"])
        result = _invoke(runner, vault_path, "list")
        assert "alice" in result.output
