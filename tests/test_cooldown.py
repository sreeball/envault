"""Tests for envault.cooldown."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.cooldown import (
    CooldownError,
    _cooldown_path,
    is_cooling_down,
    list_cooldowns,
    remove_cooldown,
    set_cooldown,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.env")


class TestSetCooldown:
    def test_creates_cooldown_file(self, vault_path: str) -> None:
        set_cooldown(vault_path, "MY_KEY", 60)
        assert _cooldown_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path: str) -> None:
        entry = set_cooldown(vault_path, "MY_KEY", 30)
        assert entry["key"] == "MY_KEY"
        assert entry["seconds"] == 30
        assert "started_at" in entry
        assert "expires_at" in entry

    def test_stores_entry_in_file(self, vault_path: str) -> None:
        set_cooldown(vault_path, "DB_PASS", 120)
        data = json.loads(_cooldown_path(vault_path).read_text())
        assert "DB_PASS" in data
        assert data["DB_PASS"]["seconds"] == 120

    def test_overwrites_existing_entry(self, vault_path: str) -> None:
        set_cooldown(vault_path, "KEY", 10)
        set_cooldown(vault_path, "KEY", 999)
        data = json.loads(_cooldown_path(vault_path).read_text())
        assert data["KEY"]["seconds"] == 999

    def test_raises_on_zero_seconds(self, vault_path: str) -> None:
        with pytest.raises(CooldownError):
            set_cooldown(vault_path, "KEY", 0)

    def test_raises_on_negative_seconds(self, vault_path: str) -> None:
        with pytest.raises(CooldownError):
            set_cooldown(vault_path, "KEY", -5)


class TestIsCoolingDown:
    def test_true_within_window(self, vault_path: str) -> None:
        set_cooldown(vault_path, "KEY", 3600)
        assert is_cooling_down(vault_path, "KEY") is True

    def test_false_for_unknown_key(self, vault_path: str) -> None:
        assert is_cooling_down(vault_path, "MISSING") is False

    def test_false_after_expiry(self, vault_path: str) -> None:
        set_cooldown(vault_path, "KEY", 1)
        # Manually backdate the expiry
        p = _cooldown_path(vault_path)
        data = json.loads(p.read_text())
        data["KEY"]["expires_at"] = "2000-01-01T00:00:00+00:00"
        p.write_text(json.dumps(data))
        assert is_cooling_down(vault_path, "KEY") is False


class TestRemoveCooldown:
    def test_returns_true_when_removed(self, vault_path: str) -> None:
        set_cooldown(vault_path, "KEY", 60)
        assert remove_cooldown(vault_path, "KEY") is True

    def test_returns_false_when_not_found(self, vault_path: str) -> None:
        assert remove_cooldown(vault_path, "GHOST") is False

    def test_entry_no_longer_present(self, vault_path: str) -> None:
        set_cooldown(vault_path, "KEY", 60)
        remove_cooldown(vault_path, "KEY")
        data = json.loads(_cooldown_path(vault_path).read_text())
        assert "KEY" not in data


class TestListCooldowns:
    def test_empty_when_no_file(self, vault_path: str) -> None:
        assert list_cooldowns(vault_path) == []

    def test_returns_all_entries(self, vault_path: str) -> None:
        set_cooldown(vault_path, "A", 10)
        set_cooldown(vault_path, "B", 20)
        entries = list_cooldowns(vault_path)
        keys = {e["key"] for e in entries}
        assert keys == {"A", "B"}

    def test_active_flag_true_for_future(self, vault_path: str) -> None:
        set_cooldown(vault_path, "KEY", 3600)
        entries = list_cooldowns(vault_path)
        assert entries[0]["active"] is True

    def test_active_flag_false_for_past(self, vault_path: str) -> None:
        set_cooldown(vault_path, "KEY", 1)
        p = _cooldown_path(vault_path)
        data = json.loads(p.read_text())
        data["KEY"]["expires_at"] = "2000-01-01T00:00:00+00:00"
        p.write_text(json.dumps(data))
        entries = list_cooldowns(vault_path)
        assert entries[0]["active"] is False
