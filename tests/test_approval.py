"""Tests for envault.approval."""

import pytest
from pathlib import Path

from envault.approval import (
    ApprovalError,
    request_approval,
    resolve_approval,
    list_approvals,
    get_approval,
)


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.json"
    p.write_text("{}")
    return str(p)


class TestRequestApproval:
    def test_creates_approvals_file(self, vault_path):
        request_approval(vault_path, "DB_PASS", "delete", "alice")
        approvals_file = Path(vault_path).parent / ".envault_approvals.json"
        assert approvals_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = request_approval(vault_path, "DB_PASS", "delete", "alice")
        assert entry["key"] == "DB_PASS"
        assert entry["operation"] == "delete"
        assert entry["requester"] == "alice"
        assert entry["status"] == "pending"

    def test_token_is_uuid_string(self, vault_path):
        entry = request_approval(vault_path, "API_KEY", "rotate", "bob")
        import uuid
        uuid.UUID(entry["token"])  # raises if invalid

    def test_stores_reason(self, vault_path):
        entry = request_approval(vault_path, "X", "set", "carol", reason="urgent")
        assert entry["reason"] == "urgent"

    def test_empty_reason_allowed(self, vault_path):
        entry = request_approval(vault_path, "X", "set", "carol")
        assert entry["reason"] == ""

    def test_raises_on_empty_operation(self, vault_path):
        with pytest.raises(ApprovalError, match="operation"):
            request_approval(vault_path, "X", "", "alice")

    def test_raises_on_empty_requester(self, vault_path):
        with pytest.raises(ApprovalError, match="requester"):
            request_approval(vault_path, "X", "delete", "")

    def test_accumulates_requests(self, vault_path):
        request_approval(vault_path, "A", "delete", "alice")
        request_approval(vault_path, "B", "rotate", "bob")
        entries = list_approvals(vault_path)
        assert len(entries) == 2


class TestResolveApproval:
    def test_approve_sets_status(self, vault_path):
        entry = request_approval(vault_path, "K", "delete", "alice")
        resolved = resolve_approval(vault_path, entry["token"], True, "manager")
        assert resolved["status"] == "approved"
        assert resolved["resolver"] == "manager"

    def test_reject_sets_status(self, vault_path):
        entry = request_approval(vault_path, "K", "delete", "alice")
        resolved = resolve_approval(vault_path, entry["token"], False, "manager")
        assert resolved["status"] == "rejected"

    def test_resolved_at_is_set(self, vault_path):
        entry = request_approval(vault_path, "K", "delete", "alice")
        resolved = resolve_approval(vault_path, entry["token"], True, "manager")
        assert resolved["resolved_at"] is not None

    def test_raises_on_unknown_token(self, vault_path):
        with pytest.raises(ApprovalError, match="not found"):
            resolve_approval(vault_path, "bad-token", True, "manager")

    def test_raises_on_double_resolve(self, vault_path):
        entry = request_approval(vault_path, "K", "delete", "alice")
        resolve_approval(vault_path, entry["token"], True, "manager")
        with pytest.raises(ApprovalError, match="already resolved"):
            resolve_approval(vault_path, entry["token"], False, "manager")


class TestListApprovals:
    def test_filter_by_status(self, vault_path):
        e1 = request_approval(vault_path, "A", "delete", "alice")
        e2 = request_approval(vault_path, "B", "rotate", "bob")
        resolve_approval(vault_path, e1["token"], True, "mgr")
        pending = list_approvals(vault_path, status="pending")
        assert len(pending) == 1
        assert pending[0]["token"] == e2["token"]

    def test_no_filter_returns_all(self, vault_path):
        request_approval(vault_path, "A", "delete", "alice")
        request_approval(vault_path, "B", "set", "bob")
        assert len(list_approvals(vault_path)) == 2


class TestGetApproval:
    def test_retrieves_by_token(self, vault_path):
        entry = request_approval(vault_path, "DB", "delete", "alice")
        fetched = get_approval(vault_path, entry["token"])
        assert fetched["key"] == "DB"

    def test_raises_on_missing_token(self, vault_path):
        with pytest.raises(ApprovalError, match="not found"):
            get_approval(vault_path, "no-such-token")
