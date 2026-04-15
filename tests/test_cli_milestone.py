"""Tests for envault.cli_milestone."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from envault.cli_milestone import milestone_group
from envault.milestone import create_milestone


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    vp = tmp_path / "vault.db"
    vp.touch()
    return str(vp)


def _invoke(runner, vault_path, *args):
    return runner.invoke(milestone_group, [*args, "-v", vault_path])


class TestCreateCmd:
    def test_creates_milestone(self, runner, vault_path):
        result = _invoke(runner, vault_path, "create", "v1.0")
        assert result.exit_code == 0
        assert "v1.0" in result.output

    def test_with_description(self, runner, vault_path):
        result = _invoke(runner, vault_path, "create", "v1.0", "-d", "Launch")
        assert result.exit_code == 0

    def test_with_due_date(self, runner, vault_path):
        result = _invoke(runner, vault_path, "create", "v1.0", "--due", "2025-12-31")
        assert result.exit_code == 0

    def test_duplicate_exits_nonzero(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "v1.0")
        result = _invoke(runner, vault_path, "create", "v1.0")
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestCompleteCmd:
    def test_completes_milestone(self, runner, vault_path):
        create_milestone(vault_path, "v1.0")
        result = _invoke(runner, vault_path, "complete", "v1.0")
        assert result.exit_code == 0
        assert "completed at" in result.output

    def test_missing_exits_nonzero(self, runner, vault_path):
        result = _invoke(runner, vault_path, "complete", "ghost")
        assert result.exit_code != 0


class TestDeleteCmd:
    def test_deletes_milestone(self, runner, vault_path):
        create_milestone(vault_path, "v1.0")
        result = _invoke(runner, vault_path, "delete", "v1.0")
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_missing_exits_nonzero(self, runner, vault_path):
        result = _invoke(runner, vault_path, "delete", "ghost")
        assert result.exit_code != 0


class TestListCmd:
    def test_no_milestones_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No milestones" in result.output

    def test_lists_milestones(self, runner, vault_path):
        create_milestone(vault_path, "v1.0", description="First")
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "v1.0" in result.output

    def test_shows_open_status(self, runner, vault_path):
        create_milestone(vault_path, "v1.0")
        result = _invoke(runner, vault_path, "list")
        assert "open" in result.output
