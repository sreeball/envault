"""Rate limiting for vault operations."""

import json
import time
from pathlib import Path
from typing import Dict, Optional


class RateLimitError(Exception):
    """Raised when a rate limit is exceeded or configuration is invalid."""


def _rate_limit_path(vault_path: Path) -> Path:
    return vault_path.parent / ".envault_rate_limits.json"


def _load_limits(vault_path: Path) -> Dict:
    path = _rate_limit_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_limits(vault_path: Path, data: Dict) -> None:
    _rate_limit_path(vault_path).write_text(json.dumps(data, indent=2))


def set_limit(vault_path: Path, operation: str, max_calls: int, window_seconds: int) -> Dict:
    """Configure a rate limit for a vault operation."""
    if max_calls <= 0:
        raise RateLimitError("max_calls must be a positive integer")
    if window_seconds <= 0:
        raise RateLimitError("window_seconds must be a positive integer")

    data = _load_limits(vault_path)
    entry = {
        "operation": operation,
        "max_calls": max_calls,
        "window_seconds": window_seconds,
        "calls": [],
    }
    data[operation] = entry
    _save_limits(vault_path, data)
    return entry


def check_and_record(vault_path: Path, operation: str) -> Dict:
    """Check if an operation is within its rate limit, then record the call."""
    data = _load_limits(vault_path)
    if operation not in data:
        # No limit configured — allow freely
        return {"allowed": True, "remaining": None, "limit": None}

    entry = data[operation]
    now = time.time()
    window = entry["window_seconds"]
    calls = [t for t in entry.get("calls", []) if now - t < window]

    if len(calls) >= entry["max_calls"]:
        raise RateLimitError(
            f"Rate limit exceeded for '{operation}': "
            f"{entry['max_calls']} calls per {window}s"
        )

    calls.append(now)
    entry["calls"] = calls
    data[operation] = entry
    _save_limits(vault_path, data)

    remaining = entry["max_calls"] - len(calls)
    return {"allowed": True, "remaining": remaining, "limit": entry["max_calls"]}


def remove_limit(vault_path: Path, operation: str) -> None:
    """Remove a rate limit for an operation."""
    data = _load_limits(vault_path)
    if operation not in data:
        raise RateLimitError(f"No rate limit configured for '{operation}'")
    del data[operation]
    _save_limits(vault_path, data)


def list_limits(vault_path: Path) -> Dict:
    """Return all configured rate limits."""
    data = _load_limits(vault_path)
    return {
        op: {k: v for k, v in cfg.items() if k != "calls"}
        for op, cfg in data.items()
    }
