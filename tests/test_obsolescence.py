"""Tests for envault.obsolescence."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.obsolescence import (
    ObsolescenceError,
    mark_obsolete,
    unmark_obsolete,
    get_obsolescence,
    list_obsolete,
    _obsolescence_path,
)


@pytest.fixture
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.env"
    p.write_text("{}")
    return str(p)


class TestMarkObsolete:
    def test_creates_obsolescence_file(self, vault_path: str) -> None:
        mark_obsolete(vault_path, "OLD_KEY")
        assert _obsolescence_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path: str) -> None:
        entry = mark_obsolete(vault_path, "OLD_KEY")
        assert entry["key"] == "OLD_KEY"

    def test_stores_reason(self, vault_path: str) -> None:
        mark_obsolete(vault_path, "OLD_KEY", reason="No longer used")
        data = json.loads(_obsolescence_path(vault_path).read_text())
        assert data["OLD_KEY"]["reason"] == "No longer used"

    def test_stores_replacement(self, vault_path: str) -> None:
        mark_obsolete(vault_path, "OLD_KEY", replacement="NEW_KEY")
        data = json.loads(_obsolescence_path(vault_path).read_text())
        assert data["OLD_KEY"]["replacement"] == "NEW_KEY"

    def test_empty_reason_allowed(self, vault_path: str) -> None:
        entry = mark_obsolete(vault_path, "OLD_KEY")
        assert entry["reason"] == ""

    def test_none_replacement_allowed(self, vault_path: str) -> None:
        entry = mark_obsolete(vault_path, "OLD_KEY")
        assert entry["replacement"] is None

    def test_overwrites_existing_entry(self, vault_path: str) -> None:
        mark_obsolete(vault_path, "OLD_KEY", reason="first")
        mark_obsolete(vault_path, "OLD_KEY", reason="second")
        data = json.loads(_obsolescence_path(vault_path).read_text())
        assert data["OLD_KEY"]["reason"] == "second"


class TestUnmarkObsolete:
    def test_removes_entry(self, vault_path: str) -> None:
        mark_obsolete(vault_path, "OLD_KEY")
        unmark_obsolete(vault_path, "OLD_KEY")
        assert get_obsolescence(vault_path, "OLD_KEY") is None

    def test_raises_when_not_marked(self, vault_path: str) -> None:
        with pytest.raises(ObsolescenceError):
            unmark_obsolete(vault_path, "MISSING_KEY")


class TestGetObsolescence:
    def test_returns_none_when_absent(self, vault_path: str) -> None:
        assert get_obsolescence(vault_path, "UNKNOWN") is None

    def test_returns_entry_when_present(self, vault_path: str) -> None:
        mark_obsolete(vault_path, "OLD_KEY", reason="done")
        entry = get_obsolescence(vault_path, "OLD_KEY")
        assert entry is not None
        assert entry["reason"] == "done"


class TestListObsolete:
    def test_empty_when_no_file(self, vault_path: str) -> None:
        assert list_obsolete(vault_path) == {}

    def test_lists_all_marked_keys(self, vault_path: str) -> None:
        mark_obsolete(vault_path, "KEY_A")
        mark_obsolete(vault_path, "KEY_B")
        result = list_obsolete(vault_path)
        assert "KEY_A" in result
        assert "KEY_B" in result
