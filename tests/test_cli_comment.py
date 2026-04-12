"""Tests for envault.cli_comment CLI commands."""

import pytest
from click.testing import CliRunner

from envault.cli_comment import comment_group
from envault.comment import add_comment


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "test.vault")


def _invoke(runner, vault_path, *args):
    return runner.invoke(comment_group, [*args, "--vault", vault_path])


class TestAddCmd:
    def test_adds_comment(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "DB_PASS", "Production password")
        assert result.exit_code == 0
        assert "Comment added" in result.output

    def test_shows_total_count(self, runner, vault_path):
        _invoke(runner, vault_path, "add", "KEY", "first")
        result = _invoke(runner, vault_path, "add", "KEY", "second")
        assert "Total comments: 2" in result.output

    def test_empty_comment_fails(self, runner, vault_path):
        result = _invoke(runner, vault_path, "add", "KEY", "   ")
        assert result.exit_code != 0
        assert "Error" in result.output


class TestGetCmd:
    def test_shows_comments(self, runner, vault_path):
        add_comment(vault_path, "API_KEY", "Used by billing service")
        result = _invoke(runner, vault_path, "get", "API_KEY")
        assert result.exit_code == 0
        assert "Used by billing service" in result.output

    def test_no_comments_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "get", "UNKNOWN")
        assert result.exit_code == 0
        assert "No comments" in result.output

    def test_shows_numbered_list(self, runner, vault_path):
        add_comment(vault_path, "K", "alpha")
        add_comment(vault_path, "K", "beta")
        result = _invoke(runner, vault_path, "get", "K")
        assert "1." in result.output
        assert "2." in result.output


class TestRemoveCmd:
    def test_removes_comments(self, runner, vault_path):
        add_comment(vault_path, "KEY", "some note")
        result = _invoke(runner, vault_path, "remove", "KEY")
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_error_on_missing_key(self, runner, vault_path):
        result = _invoke(runner, vault_path, "remove", "GHOST")
        assert result.exit_code != 0


class TestListCmd:
    def test_no_comments_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No comments" in result.output

    def test_lists_annotated_keys(self, runner, vault_path):
        add_comment(vault_path, "A", "note a")
        add_comment(vault_path, "B", "note b")
        result = _invoke(runner, vault_path, "list")
        assert "A" in result.output
        assert "B" in result.output

    def test_shows_comment_text(self, runner, vault_path):
        add_comment(vault_path, "TOKEN", "my annotation")
        result = _invoke(runner, vault_path, "list")
        assert "my annotation" in result.output
