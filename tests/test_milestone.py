"""Tests for envault.milestone."""
import pytest
from pathlib import Path
from envault.milestone import (
    MilestoneError,
    create_milestone,
    complete_milestone,
    delete_milestone,
    list_milestones,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    vp = tmp_path / "vault.db"
    vp.touch()
    return str(vp)


class TestCreateMilestone:
    def test_creates_milestones_file(self, vault_path):
        create_milestone(vault_path, "v1.0")
        ms_file = Path(vault_path).parent / ".envault" / "milestones.json"
        assert ms_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = create_milestone(vault_path, "v1.0", description="First release")
        assert entry["name"] == "v1.0"
        assert entry["description"] == "First release"
        assert entry["completed_at"] is None

    def test_id_is_uuid_string(self, vault_path):
        entry = create_milestone(vault_path, "v1.0")
        import uuid
        uuid.UUID(entry["id"])  # should not raise

    def test_due_date_stored(self, vault_path):
        entry = create_milestone(vault_path, "v1.0", due_date="2025-12-31T00:00:00+00:00")
        assert entry["due_date"] == "2025-12-31T00:00:00+00:00"

    def test_no_due_date_is_none(self, vault_path):
        entry = create_milestone(vault_path, "v1.0")
        assert entry["due_date"] is None

    def test_raises_on_duplicate(self, vault_path):
        create_milestone(vault_path, "v1.0")
        with pytest.raises(MilestoneError, match="already exists"):
            create_milestone(vault_path, "v1.0")

    def test_accumulates_milestones(self, vault_path):
        create_milestone(vault_path, "v1.0")
        create_milestone(vault_path, "v2.0")
        milestones = list_milestones(vault_path)
        names = [m["name"] for m in milestones]
        assert "v1.0" in names and "v2.0" in names


class TestCompleteMilestone:
    def test_sets_completed_at(self, vault_path):
        create_milestone(vault_path, "v1.0")
        entry = complete_milestone(vault_path, "v1.0")
        assert entry["completed_at"] is not None

    def test_raises_on_missing(self, vault_path):
        with pytest.raises(MilestoneError, match="not found"):
            complete_milestone(vault_path, "ghost")


class TestDeleteMilestone:
    def test_removes_entry(self, vault_path):
        create_milestone(vault_path, "v1.0")
        delete_milestone(vault_path, "v1.0")
        assert list_milestones(vault_path) == []

    def test_raises_on_missing(self, vault_path):
        with pytest.raises(MilestoneError, match="not found"):
            delete_milestone(vault_path, "ghost")


class TestListMilestones:
    def test_empty_when_no_file(self, vault_path):
        assert list_milestones(vault_path) == []

    def test_sorted_by_created_at(self, vault_path):
        create_milestone(vault_path, "alpha")
        create_milestone(vault_path, "beta")
        names = [m["name"] for m in list_milestones(vault_path)]
        assert names == ["alpha", "beta"]
