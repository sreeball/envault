"""Tests for envault.readonly module."""

import pytest

from envault.readonly import (
    ReadOnlyError,
    assert_writable,
    is_readonly,
    list_readonly,
    mark_readonly,
    unmark_readonly,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestMarkReadonly:
    def test_creates_readonly_file(self, vault_path, tmp_path):
        mark_readonly(vault_path, "API_KEY")
        assert (tmp_path / ".envault_readonly.json").exists()

    def test_returns_entry_dict(self, vault_path):
        entry = mark_readonly(vault_path, "API_KEY", reason="Do not change")
        assert entry["key"] == "API_KEY"
        assert entry["reason"] == "Do not change"

    def test_empty_reason_allowed(self, vault_path):
        entry = mark_readonly(vault_path, "DB_URL")
        assert entry["reason"] == ""

    def test_accumulates_keys(self, vault_path):
        mark_readonly(vault_path, "KEY_A")
        mark_readonly(vault_path, "KEY_B")
        entries = list_readonly(vault_path)
        keys = {e["key"] for e in entries}
        assert keys == {"KEY_A", "KEY_B"}

    def test_overwrite_existing(self, vault_path):
        mark_readonly(vault_path, "API_KEY", reason="first")
        mark_readonly(vault_path, "API_KEY", reason="updated")
        entries = list_readonly(vault_path)
        assert len(entries) == 1
        assert entries[0]["reason"] == "updated"


class TestUnmarkReadonly:
    def test_removes_key(self, vault_path):
        mark_readonly(vault_path, "API_KEY")
        unmark_readonly(vault_path, "API_KEY")
        assert not is_readonly(vault_path, "API_KEY")

    def test_raises_if_not_marked(self, vault_path):
        with pytest.raises(ReadOnlyError, match="not marked as read-only"):
            unmark_readonly(vault_path, "MISSING_KEY")

    def test_remaining_keys_unaffected(self, vault_path):
        """Unmarking one key should not affect other read-only keys."""
        mark_readonly(vault_path, "KEY_A")
        mark_readonly(vault_path, "KEY_B")
        unmark_readonly(vault_path, "KEY_A")
        assert not is_readonly(vault_path, "KEY_A")
        assert is_readonly(vault_path, "KEY_B")


class TestIsReadonly:
    def test_returns_true_when_marked(self, vault_path):
        mark_readonly(vault_path, "SECRET")
        assert is_readonly(vault_path, "SECRET") is True

    def test_returns_false_when_not_marked(self, vault_path):
        assert is_readonly(vault_path, "SECRET") is False

    def test_returns_false_on_empty_store(self, vault_path):
        assert is_readonly(vault_path, "ANY_KEY") is False


class TestAssertWritable:
    def test_passes_for_writable_key(self, vault_path):
        assert_writable(vault_path, "WRITABLE_KEY")  # should not raise

    def test_raises_for_readonly_key(self, vault_path):
        mark_readonly(vault_path, "LOCKED", reason="immutable")
        with pytest.raises(ReadOnlyError, match="read-only"):
            assert_writable(vault_path, "LOCKED")

    def test_error_includes_reason(self, vault_path):
        mark_readonly(vault_path, "LOCKED", reason="production secret")
        with pytest.raises(ReadOnlyError, match="production secret"):
            assert_writable(vault_path, "LOCKED")
