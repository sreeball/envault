"""Watermark support: embed and verify hidden metadata in vault secrets."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

WATERMARK_SUFFIX = ".__wm__"


class WatermarkError(Exception):
    """Raised when a watermark operation fails."""


def _watermark_path(vault_path: str) -> pathlib.Path:
    return pathlib.Path(vault_path).with_suffix(".watermarks.json")


def _load_watermarks(vault_path: str) -> dict[str, Any]:
    p = _watermark_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_watermarks(vault_path: str, data: dict[str, Any]) -> None:
    _watermark_path(vault_path).write_text(json.dumps(data, indent=2))


def _digest(value: str, owner: str) -> str:
    """Produce a short deterministic fingerprint for (value, owner)."""
    raw = f"{owner}:{value}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def embed(vault_path: str, key: str, value: str, owner: str) -> dict[str, Any]:
    """Record a watermark fingerprint for *key* / *value* attributed to *owner*.

    Returns the stored watermark entry.
    """
    if not key:
        raise WatermarkError("key must not be empty")
    if not owner:
        raise WatermarkError("owner must not be empty")

    data = _load_watermarks(vault_path)
    entry: dict[str, Any] = {
        "key": key,
        "owner": owner,
        "fingerprint": _digest(value, owner),
    }
    data[key] = entry
    _save_watermarks(vault_path, data)
    return entry


def verify(vault_path: str, key: str, value: str) -> bool:
    """Return True when the stored fingerprint matches *value*.

    Raises WatermarkError if no watermark has been recorded for *key*.
    """
    data = _load_watermarks(vault_path)
    if key not in data:
        raise WatermarkError(f"no watermark recorded for key '{key}'")
    entry = data[key]
    expected = _digest(value, entry["owner"])
    return entry["fingerprint"] == expected


def get_watermark(vault_path: str, key: str) -> dict[str, Any]:
    """Return the watermark entry for *key* or raise WatermarkError."""
    data = _load_watermarks(vault_path)
    if key not in data:
        raise WatermarkError(f"no watermark recorded for key '{key}'")
    return data[key]


def remove(vault_path: str, key: str) -> None:
    """Delete the watermark for *key* if present."""
    data = _load_watermarks(vault_path)
    data.pop(key, None)
    _save_watermarks(vault_path, data)


def list_watermarks(vault_path: str) -> list[dict[str, Any]]:
    """Return all recorded watermark entries."""
    return list(_load_watermarks(vault_path).values())
