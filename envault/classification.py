"""Secret classification levels for envault vaults."""

import json
from pathlib import Path
from typing import Dict, List, Optional

CLASSIFICATION_LEVELS = ["public", "internal", "confidential", "restricted", "top-secret"]


class ClassificationError(Exception):
    pass


def _classification_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_classification.json"


def _load_classifications(vault_path: str) -> Dict:
    p = _classification_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_classifications(vault_path: str, data: Dict) -> None:
    _classification_path(vault_path).write_text(json.dumps(data, indent=2))


def classify(vault_path: str, key: str, level: str, reason: str = "") -> Dict:
    """Assign a classification level to a secret key."""
    if level not in CLASSIFICATION_LEVELS:
        raise ClassificationError(
            f"Invalid level '{level}'. Choose from: {', '.join(CLASSIFICATION_LEVELS)}"
        )
    data = _load_classifications(vault_path)
    entry = {"level": level, "reason": reason}
    data[key] = entry
    _save_classifications(vault_path, data)
    return entry


def get_classification(vault_path: str, key: str) -> Optional[Dict]:
    """Return the classification entry for a key, or None."""
    data = _load_classifications(vault_path)
    return data.get(key)


def remove_classification(vault_path: str, key: str) -> bool:
    """Remove the classification for a key. Returns True if removed."""
    data = _load_classifications(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_classifications(vault_path, data)
    return True


def list_by_level(vault_path: str, level: str) -> List[str]:
    """Return all keys classified at the given level."""
    if level not in CLASSIFICATION_LEVELS:
        raise ClassificationError(
            f"Invalid level '{level}'. Choose from: {', '.join(CLASSIFICATION_LEVELS)}"
        )
    data = _load_classifications(vault_path)
    return [k for k, v in data.items() if v["level"] == level]


def all_classifications(vault_path: str) -> Dict:
    """Return the full classification map."""
    return _load_classifications(vault_path)
