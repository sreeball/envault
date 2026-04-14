"""Tests for envault.workflow."""

import pytest

from envault.workflow import (
    WorkflowError,
    create_workflow,
    delete_workflow,
    get_workflow,
    list_workflows,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


class TestCreateWorkflow:
    def test_creates_workflows_file(self, vault_path, tmp_path):
        create_workflow(vault_path, "deploy", ["set KEY val", "sync push"])
        assert (tmp_path / ".envault_workflows.json").exists()

    def test_returns_entry_dict(self, vault_path):
        entry = create_workflow(vault_path, "deploy", ["set KEY val"])
        assert entry["name"] == "deploy"
        assert entry["steps"] == ["set KEY val"]

    def test_stores_description(self, vault_path):
        entry = create_workflow(vault_path, "ci", ["sync push"], description="CI pipeline")
        assert entry["description"] == "CI pipeline"

    def test_empty_description_allowed(self, vault_path):
        entry = create_workflow(vault_path, "ci", ["sync push"])
        assert entry["description"] == ""

    def test_raises_on_duplicate(self, vault_path):
        create_workflow(vault_path, "deploy", ["set KEY val"])
        with pytest.raises(WorkflowError, match="already exists"):
            create_workflow(vault_path, "deploy", ["set KEY val2"])

    def test_raises_on_empty_name(self, vault_path):
        with pytest.raises(WorkflowError, match="empty"):
            create_workflow(vault_path, "", ["set KEY val"])

    def test_raises_on_empty_steps(self, vault_path):
        with pytest.raises(WorkflowError, match="at least one step"):
            create_workflow(vault_path, "deploy", [])


class TestGetWorkflow:
    def test_returns_existing_workflow(self, vault_path):
        create_workflow(vault_path, "deploy", ["set KEY val", "sync push"])
        w = get_workflow(vault_path, "deploy")
        assert w["name"] == "deploy"

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(WorkflowError, match="not found"):
            get_workflow(vault_path, "missing")


class TestDeleteWorkflow:
    def test_removes_workflow(self, vault_path):
        create_workflow(vault_path, "deploy", ["set KEY val"])
        delete_workflow(vault_path, "deploy")
        assert list_workflows(vault_path) == []

    def test_raises_when_not_found(self, vault_path):
        with pytest.raises(WorkflowError, match="not found"):
            delete_workflow(vault_path, "ghost")


class TestListWorkflows:
    def test_empty_when_no_file(self, vault_path):
        assert list_workflows(vault_path) == []

    def test_lists_all_workflows(self, vault_path):
        create_workflow(vault_path, "a", ["step1"])
        create_workflow(vault_path, "b", ["step2"])
        names = [w["name"] for w in list_workflows(vault_path)]
        assert sorted(names) == ["a", "b"]
