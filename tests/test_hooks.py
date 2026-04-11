"""Tests for envault.hooks."""

import json
from pathlib import Path

import pytest

from envault.hooks import (
    HookError,
    _hooks_path,
    fire,
    list_hooks,
    register_hook,
    unregister_hook,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_text("{}")
    return p


class TestRegisterHook:
    def test_creates_hooks_file(self, vault_path):
        register_hook(vault_path, "post_set", "echo hello")
        assert _hooks_path(vault_path).exists()

    def test_returns_hook_dict(self, vault_path):
        result = register_hook(vault_path, "post_set", "echo hello")
        assert "post_set" in result
        assert "echo hello" in result["post_set"]

    def test_accumulates_commands(self, vault_path):
        register_hook(vault_path, "post_set", "echo a")
        register_hook(vault_path, "post_set", "echo b")
        hooks = list_hooks(vault_path)
        assert hooks["post_set"] == ["echo a", "echo b"]

    def test_no_duplicate_commands(self, vault_path):
        register_hook(vault_path, "post_set", "echo a")
        register_hook(vault_path, "post_set", "echo a")
        hooks = list_hooks(vault_path)
        assert hooks["post_set"].count("echo a") == 1

    def test_multiple_events(self, vault_path):
        register_hook(vault_path, "pre_set", "echo pre")
        register_hook(vault_path, "post_set", "echo post")
        hooks = list_hooks(vault_path)
        assert "pre_set" in hooks
        assert "post_set" in hooks

    def test_raises_on_unknown_event(self, vault_path):
        with pytest.raises(HookError, match="Unknown event"):
            register_hook(vault_path, "on_explode", "echo boom")


class TestUnregisterHook:
    def test_removes_command(self, vault_path):
        register_hook(vault_path, "post_set", "echo a")
        unregister_hook(vault_path, "post_set", "echo a")
        hooks = list_hooks(vault_path)
        assert "post_set" not in hooks

    def test_raises_if_not_found(self, vault_path):
        with pytest.raises(HookError, match="not found"):
            unregister_hook(vault_path, "post_set", "echo missing")

    def test_leaves_other_commands(self, vault_path):
        register_hook(vault_path, "post_set", "echo a")
        register_hook(vault_path, "post_set", "echo b")
        unregister_hook(vault_path, "post_set", "echo a")
        hooks = list_hooks(vault_path)
        assert hooks["post_set"] == ["echo b"]


class TestListHooks:
    def test_empty_when_no_file(self, vault_path):
        assert list_hooks(vault_path) == {}

    def test_returns_all_events(self, vault_path):
        register_hook(vault_path, "pre_get", "echo x")
        register_hook(vault_path, "post_delete", "echo y")
        hooks = list_hooks(vault_path)
        assert set(hooks.keys()) == {"pre_get", "post_delete"}


class TestFire:
    def test_returns_list_of_commands(self, vault_path):
        register_hook(vault_path, "post_set", "true")
        result = fire(vault_path, "post_set")
        assert result == ["true"]

    def test_returns_empty_for_unregistered_event(self, vault_path):
        result = fire(vault_path, "pre_set")
        assert result == []
