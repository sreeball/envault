"""Sentiment analysis for secret keys and values metadata."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

SENTIMENT_LEVELS = ("positive", "neutral", "negative")


class SentimentError(Exception):
    """Raised when a sentiment operation fails."""


def _sentiment_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_sentiment.json"


def _load_sentiment(vault_path: str) -> Dict:
    p = _sentiment_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_sentiment(vault_path: str, data: Dict) -> None:
    _sentiment_path(vault_path).write_text(json.dumps(data, indent=2))


def set_sentiment(
    vault_path: str,
    key: str,
    level: str,
    note: Optional[str] = None,
) -> Dict:
    """Assign a sentiment level to a key."""
    if level not in SENTIMENT_LEVELS:
        raise SentimentError(
            f"Invalid sentiment level '{level}'. Choose from: {', '.join(SENTIMENT_LEVELS)}"
        )
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        raise SentimentError(f"Invalid key name: '{key}'")

    data = _load_sentiment(vault_path)
    entry = {"key": key, "level": level, "note": note or ""}
    data[key] = entry
    _save_sentiment(vault_path, data)
    return entry


def get_sentiment(vault_path: str, key: str) -> Optional[Dict]:
    """Return the sentiment entry for a key, or None if unset."""
    return _load_sentiment(vault_path).get(key)


def remove_sentiment(vault_path: str, key: str) -> bool:
    """Remove the sentiment entry for a key. Returns True if removed."""
    data = _load_sentiment(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_sentiment(vault_path, data)
    return True


def list_sentiment(vault_path: str) -> List[Dict]:
    """Return all sentiment entries sorted by key."""
    data = _load_sentiment(vault_path)
    return [data[k] for k in sorted(data)]


def summary(vault_path: str) -> Dict[str, int]:
    """Return a count of each sentiment level."""
    counts: Dict[str, int] = {lvl: 0 for lvl in SENTIMENT_LEVELS}
    for entry in list_sentiment(vault_path):
        counts[entry["level"]] += 1
    return counts
