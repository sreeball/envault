"""Tests for envault.cli_quota."""

import pytest
from click.testing import CliRunner

from envault.cli_quota import quota_group
from envault.vault import Vault
from envault.quota import set_quota


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / "test.vault")


def _seed(vault_path, password="pw", keys=None):
    v = Vault(vault_path, password)
    for k in (keys or []):
        v.set(k, f"val_{k}")


def _invoke(runner, *args):
    return runner.invoke(quota_group, list(args), catch_exceptions=False)


# ---------------------------------------------------------------------------
# set command
# ---------------------------------------------------------------------------

class TestSetCmd:
    def test_sets_quota_successfully(self, runner, vault_path):
        result = _invoke(runner, "set", "--vault", vault_path, "--max", "10")
        assert result.exit_code == 0
        assert "max_secrets=10" in result.output

    def test_error_on_zero_max(self, runner, vault_path):
        result = runner.invoke(quota_group, ["set", "--vault", vault_path, "--max", "0"])
        assert result.exit_code != 0

    def test_overwrites_previous_quota(self, runner, vault_path):
        _invoke(runner, "set", "--vault", vault_path, "--max", "5")
        result = _invoke(runner, "set", "--vault", vault_path, "--max", "15")
        assert "max_secrets=15" in result.output


# ---------------------------------------------------------------------------
# get command
# ---------------------------------------------------------------------------

class TestGetCmd:
    def test_reports_no_quota_when_unset(self, runner, vault_path):
        result = _invoke(runner, "get", "--vault", vault_path)
        assert result.exit_code == 0
        assert "No quota" in result.output

    def test_reports_configured_quota(self, runner, vault_path):
        set_quota(vault_path, 8)
        result = _invoke(runner, "get", "--vault", vault_path)
        assert "8" in result.output


# ---------------------------------------------------------------------------
# remove command
# ---------------------------------------------------------------------------

class TestRemoveCmd:
    def test_removes_existing_quota(self, runner, vault_path):
        set_quota(vault_path, 5)
        result = _invoke(runner, "remove", "--vault", vault_path)
        assert result.exit_code == 0
        assert "removed" in result.output.lower()

    def test_message_when_no_quota_set(self, runner, vault_path):
        result = _invoke(runner, "remove", "--vault", vault_path)
        assert result.exit_code == 0
        assert "No quota" in result.output


# ---------------------------------------------------------------------------
# check command
# ---------------------------------------------------------------------------

class TestCheckCmd:
    def test_shows_current_count_no_quota(self, runner, vault_path):
        _seed(vault_path, keys=["A", "B"])
        result = runner.invoke(
            quota_group,
            ["check", "--vault", vault_path, "--password", "pw"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "2" in result.output
        assert "not set" in result.output

    def test_shows_ok_status_within_limit(self, runner, vault_path):
        _seed(vault_path, keys=["A"])
        set_quota(vault_path, 5)
        result = runner.invoke(
            quota_group,
            ["check", "--vault", vault_path, "--password", "pw"],
            catch_exceptions=False,
        )
        assert "OK" in result.output

    def test_shows_exceeded_status(self, runner, vault_path):
        _seed(vault_path, keys=["A", "B", "C"])
        set_quota(vault_path, 2)
        result = runner.invoke(
            quota_group,
            ["check", "--vault", vault_path, "--password", "pw"],
            catch_exceptions=False,
        )
        assert "EXCEEDED" in result.output
