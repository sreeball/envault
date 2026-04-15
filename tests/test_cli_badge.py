"""Tests for envault.cli_badge."""

import pytest
from click.testing import CliRunner

from envault.badge import create_badge
from envault.cli_badge import badge_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.touch()
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(
        badge_group,
        ["--vault", vault_path, *args],
        catch_exceptions=False,
    )


class TestCreateCmd:
    def test_creates_badge(self, runner, vault_path):
        result = runner.invoke(
            badge_group,
            ["create", "API_KEY", "api key", "--vault", vault_path],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Badge created" in result.output

    def test_invalid_color_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(
            badge_group,
            ["create", "K", "label", "--color", "neon", "--vault", vault_path],
        )
        assert result.exit_code != 0

    def test_invalid_style_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(
            badge_group,
            ["create", "K", "label", "--style", "oval", "--vault", vault_path],
        )
        assert result.exit_code != 0


class TestGetCmd:
    def test_shows_badge(self, runner, vault_path):
        create_badge(vault_path, "DB_PASS", "db pass", color="red")
        result = runner.invoke(
            badge_group,
            ["get", "DB_PASS", "--vault", vault_path],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "db pass" in result.output
        assert "red" in result.output

    def test_missing_key_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(
            badge_group,
            ["get", "GHOST", "--vault", vault_path],
        )
        assert result.exit_code != 0


class TestRemoveCmd:
    def test_removes_badge(self, runner, vault_path):
        create_badge(vault_path, "TOKEN", "token")
        result = runner.invoke(
            badge_group,
            ["remove", "TOKEN", "--vault", vault_path],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_missing_key_exits_nonzero(self, runner, vault_path):
        result = runner.invoke(
            badge_group,
            ["remove", "GHOST", "--vault", vault_path],
        )
        assert result.exit_code != 0


class TestListCmd:
    def test_no_badges_message(self, runner, vault_path):
        result = runner.invoke(
            badge_group,
            ["list", "--vault", vault_path],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "No badges" in result.output

    def test_lists_all_badges(self, runner, vault_path):
        create_badge(vault_path, "A", "alpha")
        create_badge(vault_path, "B", "beta")
        result = runner.invoke(
            badge_group,
            ["list", "--vault", vault_path],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" in result.output
