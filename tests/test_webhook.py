"""Tests for envault.webhook."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.webhook import (
    register_webhook,
    unregister_webhook,
    list_webhooks,
    fire_webhook,
    WebhookError,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.enc"
    p.write_text("{}")
    return str(p)


class TestRegisterWebhook:
    def test_creates_webhook_file(self, vault_path):
        register_webhook(vault_path, "ci", "https://example.com/hook", ["set"])
        hooks_file = Path(vault_path).parent / ".envault_webhooks.json"
        assert hooks_file.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = register_webhook(vault_path, "ci", "https://example.com/hook", ["set", "delete"])
        assert entry["url"] == "https://example.com/hook"
        assert "set" in entry["events"]
        assert "delete" in entry["events"]

    def test_accumulates_webhooks(self, vault_path):
        register_webhook(vault_path, "a", "https://a.com/h", ["set"])
        register_webhook(vault_path, "b", "https://b.com/h", ["delete"])
        data = list_webhooks(vault_path)
        assert "a" in data and "b" in data

    def test_raises_on_invalid_url(self, vault_path):
        with pytest.raises(WebhookError, match="Invalid URL"):
            register_webhook(vault_path, "bad", "ftp://nope.com", ["set"])

    def test_raises_on_empty_events(self, vault_path):
        with pytest.raises(WebhookError, match="At least one event"):
            register_webhook(vault_path, "empty", "https://ok.com/h", [])


class TestUnregisterWebhook:
    def test_removes_webhook(self, vault_path):
        register_webhook(vault_path, "ci", "https://example.com/hook", ["set"])
        unregister_webhook(vault_path, "ci")
        assert "ci" not in list_webhooks(vault_path)

    def test_raises_on_missing_name(self, vault_path):
        with pytest.raises(WebhookError, match="not found"):
            unregister_webhook(vault_path, "ghost")


class TestListWebhooks:
    def test_empty_when_no_file(self, vault_path):
        assert list_webhooks(vault_path) == {}

    def test_returns_all_registered(self, vault_path):
        register_webhook(vault_path, "x", "https://x.io/h", ["set"])
        result = list_webhooks(vault_path)
        assert "x" in result


class TestFireWebhook:
    def test_fires_matching_event(self, vault_path):
        register_webhook(vault_path, "ci", "https://example.com/hook", ["set"])
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            fired = fire_webhook(vault_path, "set", {"key": "FOO"})
        assert "https://example.com/hook" in fired
        mock_open.assert_called_once()

    def test_skips_non_matching_event(self, vault_path):
        register_webhook(vault_path, "ci", "https://example.com/hook", ["delete"])
        with patch("urllib.request.urlopen") as mock_open:
            fired = fire_webhook(vault_path, "set", {"key": "FOO"})
        assert fired == []
        mock_open.assert_not_called()

    def test_raises_on_connection_error(self, vault_path):
        import urllib.error
        register_webhook(vault_path, "ci", "https://example.com/hook", ["set"])
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            with pytest.raises(WebhookError, match="failed"):
                fire_webhook(vault_path, "set", {"key": "BAR"})
