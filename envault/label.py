"""Label management for vault secrets."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class LabelError(Exception):
    pass


def _labels_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_labels.json"


def _load_labels(vault_path: str) -> Dict[str, List[str]]:
    p = _labels_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_labels(vault_path: str, data: Dict[str, List[str]]) -> None:
    _labels_path(vault_path).write_text(json.dumps(data, indent=2))


def add_label(vault_path: str, key: str, label: str) -> List[str]:
    """Add a label to a secret key. Returns updated label list."""
    if not label.strip():
        raise LabelError("Label must not be empty.")
    data = _load_labels(vault_path)
    labels = data.get(key, [])
    if label not in labels:
        labels.append(label)
    data[key] = labels
    _save_labels(vault_path, data)
    return labels


def remove_label(vault_path: str, key: str, label: str) -> List[str]:
    """Remove a label from a secret key. Returns updated label list."""
    data = _load_labels(vault_path)
    labels = data.get(key, [])
    if label not in labels:
        raise LabelError(f"Label '{label}' not found on key '{key}'.")
    labels.remove(label)
    data[key] = labels
    _save_labels(vault_path, data)
    return labels


def get_labels(vault_path: str, key: str) -> List[str]:
    """Return all labels for a given key."""
    return _load_labels(vault_path).get(key, [])


def keys_with_label(vault_path: str, label: str) -> List[str]:
    """Return all keys that have a given label."""
    data = _load_labels(vault_path)
    return [k for k, labels in data.items() if label in labels]


def all_labels(vault_path: str) -> Dict[str, List[str]]:
    """Return the full label map."""
    return _load_labels(vault_path)
