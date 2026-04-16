"""Tests for envault.memo."""

import pytest
from pathlib import Path
from envault.memo import add_memo, get_memos, clear_memos, list_all, MemoError


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.write_text("{}")
    return str(p)


class TestAddMemo:
    def test_creates_memo_file(self, vault_path):
        add_memo(vault_path, "MY_KEY", "remember this")
        memo_file = Path(vault_path).parent / ".envault_memos.json"
        assert memo_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = add_memo(vault_path, "MY_KEY", "hello")
        assert entry["text"] == "hello"
        assert "created_at" in entry

    def test_accumulates_memos(self, vault_path):
        add_memo(vault_path, "KEY", "first")
        add_memo(vault_path, "KEY", "second")
        memos = get_memos(vault_path, "KEY")
        assert len(memos) == 2
        assert memos[0]["text"] == "first"
        assert memos[1]["text"] == "second"

    def test_raises_on_empty_text(self, vault_path):
        with pytest.raises(MemoError):
            add_memo(vault_path, "KEY", "")

    def test_independent_keys(self, vault_path):
        add_memo(vault_path, "A", "note for a")
        add_memo(vault_path, "B", "note for b")
        assert len(get_memos(vault_path, "A")) == 1
        assert len(get_memos(vault_path, "B")) == 1


class TestGetMemos:
    def test_returns_empty_list_for_unknown_key(self, vault_path):
        assert get_memos(vault_path, "MISSING") == []

    def test_returns_memos_in_order(self, vault_path):
        for i in range(3):
            add_memo(vault_path, "K", f"msg {i}")
        memos = get_memos(vault_path, "K")
        assert [m["text"] for m in memos] == ["msg 0", "msg 1", "msg 2"]


class TestClearMemos:
    def test_returns_count_removed(self, vault_path):
        add_memo(vault_path, "K", "a")
        add_memo(vault_path, "K", "b")
        assert clear_memos(vault_path, "K") == 2

    def test_memos_gone_after_clear(self, vault_path):
        add_memo(vault_path, "K", "x")
        clear_memos(vault_path, "K")
        assert get_memos(vault_path, "K") == []

    def test_clear_nonexistent_returns_zero(self, vault_path):
        assert clear_memos(vault_path, "NOPE") == 0


class TestListAll:
    def test_empty_when_no_memos(self, vault_path):
        assert list_all(vault_path) == {}

    def test_returns_all_keys(self, vault_path):
        add_memo(vault_path, "A", "one")
        add_memo(vault_path, "B", "two")
        data = list_all(vault_path)
        assert set(data.keys()) == {"A", "B"}
