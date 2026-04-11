import pytest
from pathlib import Path
from envault.access import grant, revoke, can, list_permissions, AccessError


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "test.vault")


class TestGrant:
    def test_creates_access_file(self, vault_path):
        grant(vault_path, "alice", "DB_PASSWORD")
        access_file = Path(vault_path).with_suffix(".access.json")
        assert access_file.exists()

    def test_returns_entry_dict(self, vault_path):
        result = grant(vault_path, "alice", "DB_PASSWORD", "read")
        assert result == {"identity": "alice", "key": "DB_PASSWORD", "permission": "read"}

    def test_accumulates_keys(self, vault_path):
        grant(vault_path, "alice", "KEY_A")
        grant(vault_path, "alice", "KEY_B")
        perms = list_permissions(vault_path, "alice")
        assert "KEY_A" in perms["alice"]["read"]
        assert "KEY_B" in perms["alice"]["read"]

    def test_no_duplicate_keys(self, vault_path):
        grant(vault_path, "alice", "KEY_A")
        grant(vault_path, "alice", "KEY_A")
        perms = list_permissions(vault_path, "alice")
        assert perms["alice"]["read"].count("KEY_A") == 1

    def test_write_permission(self, vault_path):
        grant(vault_path, "bob", "SECRET", "write")
        assert can(vault_path, "bob", "SECRET", "write")

    def test_invalid_permission_raises(self, vault_path):
        with pytest.raises(AccessError, match="Invalid permission"):
            grant(vault_path, "alice", "KEY", "execute")


class TestRevoke:
    def test_revoke_removes_permission(self, vault_path):
        grant(vault_path, "alice", "DB_PASSWORD")
        revoke(vault_path, "alice", "DB_PASSWORD")
        assert not can(vault_path, "alice", "DB_PASSWORD")

    def test_revoke_returns_entry(self, vault_path):
        grant(vault_path, "alice", "KEY")
        result = revoke(vault_path, "alice", "KEY")
        assert result["identity"] == "alice"
        assert result["key"] == "KEY"

    def test_revoke_nonexistent_raises(self, vault_path):
        with pytest.raises(AccessError):
            revoke(vault_path, "alice", "MISSING_KEY")

    def test_revoke_invalid_permission_raises(self, vault_path):
        with pytest.raises(AccessError, match="Invalid permission"):
            revoke(vault_path, "alice", "KEY", "delete")


class TestCan:
    def test_returns_false_when_no_acl(self, vault_path):
        assert not can(vault_path, "unknown", "KEY")

    def test_returns_true_after_grant(self, vault_path):
        grant(vault_path, "carol", "API_KEY", "write")
        assert can(vault_path, "carol", "API_KEY", "write")

    def test_read_does_not_imply_write(self, vault_path):
        grant(vault_path, "carol", "API_KEY", "read")
        assert not can(vault_path, "carol", "API_KEY", "write")


class TestListPermissions:
    def test_empty_vault_returns_empty(self, vault_path):
        assert list_permissions(vault_path) == {}

    def test_returns_all_identities(self, vault_path):
        grant(vault_path, "alice", "A")
        grant(vault_path, "bob", "B")
        perms = list_permissions(vault_path)
        assert "alice" in perms
        assert "bob" in perms

    def test_filter_by_identity(self, vault_path):
        grant(vault_path, "alice", "A")
        grant(vault_path, "bob", "B")
        perms = list_permissions(vault_path, "alice")
        assert "bob" not in perms
        assert "alice" in perms
