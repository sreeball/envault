"""Webhook notification support for envault vault events."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


class WebhookError(Exception):
    """Raised when a webhook operation fails."""


def _webhook_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_webhooks.json"


def _load_webhooks(vault_path: str) -> dict:
    p = _webhook_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_webhooks(vault_path: str, data: dict) -> None:
    _webhook_path(vault_path).write_text(json.dumps(data, indent=2))


def register_webhook(vault_path: str, name: str, url: str, events: list[str]) -> dict:
    """Register a webhook for one or more vault events."""
    if not url.startswith(("http://", "https://")):
        raise WebhookError(f"Invalid URL: {url!r}")
    if not events:
        raise WebhookError("At least one event must be specified.")
    data = _load_webhooks(vault_path)
    data[name] = {"url": url, "events": list(events)}
    _save_webhooks(vault_path, data)
    return data[name]


def unregister_webhook(vault_path: str, name: str) -> None:
    """Remove a registered webhook by name."""
    data = _load_webhooks(vault_path)
    if name not in data:
        raise WebhookError(f"Webhook {name!r} not found.")
    del data[name]
    _save_webhooks(vault_path, data)


def list_webhooks(vault_path: str) -> dict:
    """Return all registered webhooks."""
    return _load_webhooks(vault_path)


def fire_webhook(vault_path: str, event: str, payload: dict[str, Any]) -> list[str]:
    """Fire all webhooks registered for the given event. Returns list of fired URLs."""
    data = _load_webhooks(vault_path)
    fired: list[str] = []
    body = json.dumps({"event": event, **payload}).encode()
    for name, cfg in data.items():
        if event not in cfg.get("events", []):
            continue
        url = cfg["url"]
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                pass
        except urllib.error.URLError as exc:
            raise WebhookError(f"Webhook {name!r} to {url!r} failed: {exc}") from exc
        fired.append(url)
    return fired
