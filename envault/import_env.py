"""Import environment variables from external sources into a vault."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Tuple


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env file and return a dict of key/value pairs."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        # Strip optional surrounding quotes
        for quote in ('"', "'"):
            if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
                value = value[1:-1]
                break
        result[key] = value
    return result


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a JSON object and return a dict of string key/value pairs."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object")
    return {str(k): str(v) for k, v in data.items()}


def import_from_file(path: str | Path, fmt: str = "dotenv") -> Dict[str, str]:
    """Read *path* and return parsed key/value pairs.

    Parameters
    ----------
    path:
        Path to the file to import.
    fmt:
        ``"dotenv"`` (default) or ``"json"``.
    """
    path = Path(path)
    if not path.exists():
        raise ImportError(f"File not found: {path}")
    text = path.read_text(encoding="utf-8")
    if fmt == "dotenv":
        return _parse_dotenv(text)
    if fmt == "json":
        return _parse_json(text)
    raise ImportError(f"Unknown format: {fmt!r}. Choose 'dotenv' or 'json'.")


def import_from_env(keys: list[str] | None = None) -> Dict[str, str]:
    """Capture variables from the current process environment.

    Parameters
    ----------
    keys:
        Explicit list of keys to capture.  If *None*, all variables are
        returned.
    """
    env = dict(os.environ)
    if keys is None:
        return env
    missing = [k for k in keys if k not in env]
    if missing:
        raise ImportError(f"Keys not found in environment: {missing}")
    return {k: env[k] for k in keys}


def load_into_vault(vault, secrets: Dict[str, str], password: str) -> Tuple[int, int]:
    """Store *secrets* into *vault*, returning (added, updated) counts."""
    added = updated = 0
    for key, value in secrets.items():
        try:
            vault.get(key, password)
            updated += 1
        except Exception:  # noqa: BLE001
            added += 1
        vault.set(key, value, password)
    return added, updated
