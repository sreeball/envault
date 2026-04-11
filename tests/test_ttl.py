"""Tests for envault.ttl."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.ttl import (
    TTLError,
    clear_ttl,
    get_ttl,
    is_expired,
    purge_expired,
    set_ttl,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "test.vault"


class TestSetTTL:
    def test_creates_ttl_file(self, vault_path):
        set_ttl(vault_path, "MY_KEY", 60)
        ttl_file = vault_path.with_suffix(".ttl.json")
        assert ttl_file.exists()

    def test_returns_entry_with_expires_at(self, vault_path):
        entry = set_ttl(vault_path, "MY_KEY", 60)
        assert "expires_at" in entry

    def test_expires_at_is_in_the_future(self, vault_path):
        import time
        before = time.time()
        entry = set_ttl(vault_path, "MY_KEY", 60)
        assert entry["expires_at"] > before + 59

    def test_raises_on_zero_seconds(self, vault_path):
        with pytest.raises(TTLError):
            set_ttl(vault_path, "MY_KEY", 0)

    def test_raises_on_negative_seconds(self, vault_path):
        with pytest.raises(TTLError):
            set_ttl(vault_path, "MY_KEY", -10)

    def test_overwrites_existing_ttl(self, vault_path):
        set_ttl(vault_path, "MY_KEY", 30)
        set_ttl(vault_path, "MY_KEY", 120)
        entry = get_ttl(vault_path, "MY_KEY")
        assert entry["expires_at"] > time.time() + 100


class TestGetTTL:
    def test_returns_none_when_no_ttl(self, vault_path):
        assert get_ttl(vault_path, "MISSING") is None

    def test_returns_entry_after_set(self, vault_path):
        set_ttl(vault_path, "K", 60)
        assert get_ttl(vault_path, "K") is not None


class TestIsExpired:
    def test_not_expired_for_future_ttl(self, vault_path):
        set_ttl(vault_path, "K", 3600)
        assert is_expired(vault_path, "K") is False

    def test_not_expired_when_no_ttl_set(self, vault_path):
        assert is_expired(vault_path, "NO_TTL") is False

    def test_expired_for_past_ttl(self, vault_path):
        entry = set_ttl(vault_path, "K", 1)
        # Manually backdate the expiry
        from envault.ttl import _load, _save, _ttl_path
        data = _load(_ttl_path(vault_path))
        data["K"]["expires_at"] = time.time() - 1
        _save(_ttl_path(vault_path), data)
        assert is_expired(vault_path, "K") is True


class TestClearTTL:
    def test_returns_true_when_existed(self, vault_path):
        set_ttl(vault_path, "K", 60)
        assert clear_ttl(vault_path, "K") is True

    def test_returns_false_when_not_existed(self, vault_path):
        assert clear_ttl(vault_path, "GHOST") is False

    def test_removes_entry(self, vault_path):
        set_ttl(vault_path, "K", 60)
        clear_ttl(vault_path, "K")
        assert get_ttl(vault_path, "K") is None


class TestPurgeExpired:
    def test_returns_expired_keys(self, vault_path):
        from envault.ttl import _load, _save, _ttl_path
        set_ttl(vault_path, "OLD", 60)
        set_ttl(vault_path, "NEW", 60)
        data = _load(_ttl_path(vault_path))
        data["OLD"]["expires_at"] = time.time() - 1
        _save(_ttl_path(vault_path), data)
        expired = purge_expired(vault_path)
        assert expired == ["OLD"]

    def test_keeps_valid_entries(self, vault_path):
        set_ttl(vault_path, "KEEP", 3600)
        purge_expired(vault_path)
        assert get_ttl(vault_path, "KEEP") is not None

    def test_returns_empty_list_when_nothing_expired(self, vault_path):
        set_ttl(vault_path, "K", 3600)
        assert purge_expired(vault_path) == []
