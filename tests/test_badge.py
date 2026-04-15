"""Tests for envault.badge."""

import pytest

from envault.badge import (
    BadgeError,
    create_badge,
    get_badge,
    list_badges,
    remove_badge,
    _badges_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.db"
    p.touch()
    return str(p)


class TestCreateBadge:
    def test_creates_badges_file(self, vault_path):
        create_badge(vault_path, "API_KEY", "api key")
        assert _badges_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = create_badge(vault_path, "API_KEY", "api key")
        assert entry["key"] == "API_KEY"
        assert entry["label"] == "api key"

    def test_default_color_and_style(self, vault_path):
        entry = create_badge(vault_path, "TOKEN", "token")
        assert entry["color"] == "blue"
        assert entry["style"] == "flat"

    def test_custom_color_and_style(self, vault_path):
        entry = create_badge(vault_path, "TOKEN", "token", color="green", style="plastic")
        assert entry["color"] == "green"
        assert entry["style"] == "plastic"

    def test_raises_on_invalid_color(self, vault_path):
        with pytest.raises(BadgeError, match="Invalid color"):
            create_badge(vault_path, "K", "label", color="purple")

    def test_raises_on_invalid_style(self, vault_path):
        with pytest.raises(BadgeError, match="Invalid style"):
            create_badge(vault_path, "K", "label", style="rounded")

    def test_overwrites_existing_badge(self, vault_path):
        create_badge(vault_path, "API_KEY", "old label", color="red")
        entry = create_badge(vault_path, "API_KEY", "new label", color="green")
        assert entry["label"] == "new label"
        assert entry["color"] == "green"


class TestGetBadge:
    def test_retrieves_stored_badge(self, vault_path):
        create_badge(vault_path, "DB_PASS", "db pass", color="orange")
        entry = get_badge(vault_path, "DB_PASS")
        assert entry["label"] == "db pass"
        assert entry["color"] == "orange"

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(BadgeError, match="No badge found"):
            get_badge(vault_path, "MISSING")


class TestRemoveBadge:
    def test_removes_badge(self, vault_path):
        create_badge(vault_path, "KEY", "key")
        remove_badge(vault_path, "KEY")
        with pytest.raises(BadgeError):
            get_badge(vault_path, "KEY")

    def test_raises_on_missing_key(self, vault_path):
        with pytest.raises(BadgeError, match="No badge found"):
            remove_badge(vault_path, "GHOST")


class TestListBadges:
    def test_empty_when_no_badges(self, vault_path):
        assert list_badges(vault_path) == []

    def test_returns_all_badges(self, vault_path):
        create_badge(vault_path, "A", "a")
        create_badge(vault_path, "B", "b")
        badges = list_badges(vault_path)
        keys = {b["key"] for b in badges}
        assert keys == {"A", "B"}
