"""Tests for envault.visibility."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.visibility import (
    VisibilityError,
    apply_visibility,
    get_visibility,
    list_visibility,
    remove_visibility,
    set_visibility,
    _visibility_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.json"
    p.write_text("{}")
    return str(p)


class TestSetVisibility:
    def test_creates_visibility_file(self, vault_path: str) -> None:
        set_visibility(vault_path, "API_KEY", "masked")
        assert _visibility_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path: str) -> None:
        entry = set_visibility(vault_path, "TOKEN", "public")
        assert entry == {"key": "TOKEN", "visibility": "public"}

    def test_stores_level_in_file(self, vault_path: str) -> None:
        set_visibility(vault_path, "SECRET", "private")
        data = json.loads(_visibility_path(vault_path).read_text())
        assert data["SECRET"] == "private"

    def test_raises_on_invalid_level(self, vault_path: str) -> None:
        with pytest.raises(VisibilityError, match="Invalid visibility level"):
            set_visibility(vault_path, "KEY", "invisible")

    def test_overwrites_existing_level(self, vault_path: str) -> None:
        set_visibility(vault_path, "KEY", "public")
        set_visibility(vault_path, "KEY", "masked")
        data = json.loads(_visibility_path(vault_path).read_text())
        assert data["KEY"] == "masked"


class TestGetVisibility:
    def test_returns_private_by_default(self, vault_path: str) -> None:
        assert get_visibility(vault_path, "MISSING") == "private"

    def test_returns_set_level(self, vault_path: str) -> None:
        set_visibility(vault_path, "DB_PASS", "masked")
        assert get_visibility(vault_path, "DB_PASS") == "masked"


class TestRemoveVisibility:
    def test_returns_true_when_removed(self, vault_path: str) -> None:
        set_visibility(vault_path, "KEY", "public")
        assert remove_visibility(vault_path, "KEY") is True

    def test_returns_false_when_not_found(self, vault_path: str) -> None:
        assert remove_visibility(vault_path, "GHOST") is False

    def test_key_no_longer_in_file(self, vault_path: str) -> None:
        set_visibility(vault_path, "KEY", "public")
        remove_visibility(vault_path, "KEY")
        data = json.loads(_visibility_path(vault_path).read_text())
        assert "KEY" not in data


class TestListVisibility:
    def test_empty_when_no_settings(self, vault_path: str) -> None:
        assert list_visibility(vault_path) == []

    def test_returns_all_entries_sorted(self, vault_path: str) -> None:
        set_visibility(vault_path, "Z_KEY", "public")
        set_visibility(vault_path, "A_KEY", "masked")
        entries = list_visibility(vault_path)
        assert [e["key"] for e in entries] == ["A_KEY", "Z_KEY"]


class TestApplyVisibility:
    def test_public_returns_value(self) -> None:
        assert apply_visibility("K", "secret", "public") == "secret"

    def test_masked_returns_stars(self) -> None:
        assert apply_visibility("K", "secret", "masked") == "***"

    def test_private_returns_hidden(self) -> None:
        assert apply_visibility("K", "secret", "private") == "[hidden]"
