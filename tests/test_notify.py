"""Tests for envault.notify."""

import json
import sys
from pathlib import Path

import pytest

from envault.notify import (
    NotifyError,
    fire,
    list_subscriptions,
    subscribe,
    unsubscribe,
    _notify_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestSubscribe:
    def test_creates_notify_file(self, vault_path):
        subscribe(vault_path, "set", "echo hello")
        assert _notify_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        result = subscribe(vault_path, "set", "echo hello")
        assert result["event"] == "set"
        assert result["command"] == "echo hello"
        assert "echo hello" in result["all"]

    def test_accumulates_commands(self, vault_path):
        subscribe(vault_path, "set", "echo a")
        result = subscribe(vault_path, "set", "echo b")
        assert "echo a" in result["all"]
        assert "echo b" in result["all"]

    def test_no_duplicate_commands(self, vault_path):
        subscribe(vault_path, "set", "echo a")
        result = subscribe(vault_path, "set", "echo a")
        assert result["all"].count("echo a") == 1

    def test_multiple_events(self, vault_path):
        subscribe(vault_path, "set", "echo a")
        subscribe(vault_path, "delete", "echo b")
        subs = list_subscriptions(vault_path)
        assert "set" in subs
        assert "delete" in subs


class TestUnsubscribe:
    def test_removes_command(self, vault_path):
        subscribe(vault_path, "set", "echo a")
        remaining = unsubscribe(vault_path, "set", "echo a")
        assert "echo a" not in remaining

    def test_raises_when_not_subscribed(self, vault_path):
        with pytest.raises(NotifyError):
            unsubscribe(vault_path, "set", "echo missing")


class TestFire:
    def test_returns_results_list(self, vault_path):
        subscribe(vault_path, "set", f"{sys.executable} -c 'print(1)'")
        results = fire(vault_path, "set")
        assert isinstance(results, list)
        assert len(results) == 1

    def test_returncode_zero_on_success(self, vault_path):
        subscribe(vault_path, "rotate", f"{sys.executable} -c 'import sys; sys.exit(0)'")
        results = fire(vault_path, "rotate")
        assert results[0]["returncode"] == 0

    def test_context_passed_as_env(self, vault_path):
        subscribe(vault_path, "set", f"{sys.executable} -c 'import os,sys; print(os.environ[\"ENVAULT_KEY\"])'")
        results = fire(vault_path, "set", context={"key": "MY_SECRET"})
        assert results[0]["stdout"] == "MY_SECRET"

    def test_no_handlers_returns_empty(self, vault_path):
        results = fire(vault_path, "nonexistent_event")
        assert results == []


class TestListSubscriptions:
    def test_empty_when_no_file(self, vault_path):
        assert list_subscriptions(vault_path) == {}

    def test_reflects_subscriptions(self, vault_path):
        subscribe(vault_path, "set", "echo x")
        subs = list_subscriptions(vault_path)
        assert "set" in subs
        assert "echo x" in subs["set"]
