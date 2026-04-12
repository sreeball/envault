"""Tests for envault.lock"""

import pytest

from envault.lock import (
    LockError,
    assert_unlocked,
    is_locked,
    lock_info,
    lock_vault,
    unlock_vault,
)


@pytest.fixture()
def vault_path(tmp_path):
    vp = tmp_path / "vault.json"
    vp.write_text("{}")
    return str(vp)


class TestLockVault:
    def test_creates_lock_file(self, vault_path, tmp_path):
        lock_vault(vault_path)
        assert (tmp_path / "vault.lock").exists()

    def test_returns_entry_dict(self, vault_path):
        entry = lock_vault(vault_path)
        assert "locked_at" in entry
        assert "actor" in entry
        assert "reason" in entry

    def test_stores_reason(self, vault_path):
        entry = lock_vault(vault_path, reason="maintenance")
        assert entry["reason"] == "maintenance"

    def test_stores_actor(self, vault_path):
        entry = lock_vault(vault_path, actor="alice")
        assert entry["actor"] == "alice"

    def test_raises_if_already_locked(self, vault_path):
        lock_vault(vault_path)
        with pytest.raises(LockError, match="already locked"):
            lock_vault(vault_path)


class TestUnlockVault:
    def test_removes_lock_file(self, vault_path, tmp_path):
        lock_vault(vault_path)
        unlock_vault(vault_path)
        assert not (tmp_path / "vault.lock").exists()

    def test_returns_entry_with_unlocked_at(self, vault_path):
        lock_vault(vault_path)
        entry = unlock_vault(vault_path)
        assert "unlocked_at" in entry

    def test_raises_if_not_locked(self, vault_path):
        with pytest.raises(LockError, match="not locked"):
            unlock_vault(vault_path)


class TestIsLocked:
    def test_false_when_not_locked(self, vault_path):
        assert is_locked(vault_path) is False

    def test_true_when_locked(self, vault_path):
        lock_vault(vault_path)
        assert is_locked(vault_path) is True


class TestLockInfo:
    def test_none_when_not_locked(self, vault_path):
        assert lock_info(vault_path) is None

    def test_returns_dict_when_locked(self, vault_path):
        lock_vault(vault_path, reason="deploy", actor="ci")
        info = lock_info(vault_path)
        assert info["reason"] == "deploy"
        assert info["actor"] == "ci"


class TestAssertUnlocked:
    def test_passes_when_unlocked(self, vault_path):
        assert_unlocked(vault_path)  # should not raise

    def test_raises_when_locked(self, vault_path):
        lock_vault(vault_path, reason="freeze")
        with pytest.raises(LockError, match="freeze"):
            assert_unlocked(vault_path)
