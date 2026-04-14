"""Tests for envault.cli_workflow."""

import pytest
from click.testing import CliRunner

from envault.cli_workflow import workflow_group
from envault.workflow import create_workflow


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


def _invoke(runner, vault_path, *args):
    return runner.invoke(workflow_group, [*args, "--vault", vault_path])


class TestCreateCmd:
    def test_creates_workflow(self, runner, vault_path):
        result = _invoke(runner, vault_path, "create", "deploy", "set KEY val", "sync push")
        assert result.exit_code == 0
        assert "deploy" in result.output
        assert "2 step" in result.output

    def test_with_description(self, runner, vault_path):
        result = _invoke(runner, vault_path, "create", "ci", "sync push", "--description", "CI flow")
        assert result.exit_code == 0

    def test_duplicate_fails(self, runner, vault_path):
        _invoke(runner, vault_path, "create", "deploy", "step1")
        result = _invoke(runner, vault_path, "create", "deploy", "step2")
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestDeleteCmd:
    def test_deletes_workflow(self, runner, vault_path):
        create_workflow(vault_path, "deploy", ["step1"])
        result = _invoke(runner, vault_path, "delete", "deploy")
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_missing_workflow_fails(self, runner, vault_path):
        result = _invoke(runner, vault_path, "delete", "ghost")
        assert result.exit_code != 0
        assert "not found" in result.output


class TestShowCmd:
    def test_shows_steps(self, runner, vault_path):
        create_workflow(vault_path, "deploy", ["set KEY val", "sync push"], description="Deploy flow")
        result = _invoke(runner, vault_path, "show", "deploy")
        assert result.exit_code == 0
        assert "set KEY val" in result.output
        assert "sync push" in result.output
        assert "Deploy flow" in result.output

    def test_missing_workflow_fails(self, runner, vault_path):
        result = _invoke(runner, vault_path, "show", "ghost")
        assert result.exit_code != 0


class TestListCmd:
    def test_no_workflows_message(self, runner, vault_path):
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "No workflows" in result.output

    def test_lists_registered_workflows(self, runner, vault_path):
        create_workflow(vault_path, "a", ["step1"])
        create_workflow(vault_path, "b", ["step2", "step3"])
        result = _invoke(runner, vault_path, "list")
        assert result.exit_code == 0
        assert "a" in result.output
        assert "b" in result.output
