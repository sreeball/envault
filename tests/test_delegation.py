"""Tests for envault.delegation."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.delegation import (
    DelegationError,
    create_delegation,
    revoke_delegation,
    check_delegation,
    list_delegations,
    _delegation_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.json"
    p.write_text("{}")
    return str(p)


class TestCreateDelegation:
    def test_creates_delegation_file(self, vault_path):
        create_delegation(vault_path, "alice", ["DB_URL"])
        assert _delegation_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = create_delegation(vault_path, "alice", ["DB_URL"])
        assert entry["delegatee"] == "alice"
        assert entry["keys"] == ["DB_URL"]

    def test_token_is_uuid_string(self, vault_path):
        entry = create_delegation(vault_path, "alice", ["DB_URL"])
        assert isinstance(entry["token"], str)
        assert len(entry["token"]) == 36  # UUID4

    def test_expires_at_in_future(self, vault_path):
        from datetime import datetime, timezone
        entry = create_delegation(vault_path, "alice", ["DB_URL"], ttl_seconds=60)
        expires = datetime.fromisoformat(entry["expires_at"])
        assert expires > datetime.now(timezone.utc)

    def test_accumulates_delegations(self, vault_path):
        create_delegation(vault_path, "alice", ["A"])
        create_delegation(vault_path, "bob", ["B"])
        assert len(list_delegations(vault_path)) == 2

    def test_raises_on_empty_delegatee(self, vault_path):
        with pytest.raises(DelegationError, match="delegatee"):
            create_delegation(vault_path, "", ["DB_URL"])

    def test_raises_on_empty_keys(self, vault_path):
        with pytest.raises(DelegationError, match="key"):
            create_delegation(vault_path, "alice", [])

    def test_raises_on_non_positive_ttl(self, vault_path):
        with pytest.raises(DelegationError, match="ttl_seconds"):
            create_delegation(vault_path, "alice", ["X"], ttl_seconds=0)

    def test_note_stored(self, vault_path):
        entry = create_delegation(vault_path, "alice", ["X"], note="ci runner")
        assert entry["note"] == "ci runner"


class TestRevokeDelegation:
    def test_removes_entry(self, vault_path):
        entry = create_delegation(vault_path, "alice", ["A"])
        revoke_delegation(vault_path, entry["token"])
        assert list_delegations(vault_path) == []

    def test_raises_on_unknown_token(self, vault_path):
        with pytest.raises(DelegationError, match="not found"):
            revoke_delegation(vault_path, "no-such-token")


class TestCheckDelegation:
    def test_valid_token_and_key_returns_true(self, vault_path):
        entry = create_delegation(vault_path, "alice", ["DB_URL"])
        assert check_delegation(vault_path, entry["token"], "DB_URL") is True

    def test_wrong_key_returns_false(self, vault_path):
        entry = create_delegation(vault_path, "alice", ["DB_URL"])
        assert check_delegation(vault_path, entry["token"], "SECRET") is False

    def test_unknown_token_returns_false(self, vault_path):
        assert check_delegation(vault_path, "bad-token", "DB_URL") is False

    def test_expired_token_returns_false(self, vault_path):
        entry = create_delegation(vault_path, "alice", ["DB_URL"], ttl_seconds=1)
        time.sleep(1.05)
        assert check_delegation(vault_path, entry["token"], "DB_URL") is False
