"""Category management for vault secrets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class CategoryError(Exception):
    """Raised when a category operation fails."""


def _categories_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_categories.json"


def _load_categories(vault_path: str) -> Dict[str, List[str]]:
    p = _categories_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_categories(vault_path: str, data: Dict[str, List[str]]) -> None:
    _categories_path(vault_path).write_text(json.dumps(data, indent=2))


def assign_category(vault_path: str, key: str, category: str) -> Dict:
    """Assign *key* to *category*, creating the category if needed."""
    if not key:
        raise CategoryError("key must not be empty")
    if not category:
        raise CategoryError("category must not be empty")
    data = _load_categories(vault_path)
    data.setdefault(category, [])
    if key not in data[category]:
        data[category].append(key)
    _save_categories(vault_path, data)
    return {"category": category, "key": key, "members": data[category]}


def remove_from_category(vault_path: str, key: str, category: str) -> List[str]:
    """Remove *key* from *category*. Returns remaining members."""
    data = _load_categories(vault_path)
    if category not in data:
        raise CategoryError(f"category '{category}' does not exist")
    if key not in data[category]:
        raise CategoryError(f"key '{key}' is not in category '{category}'")
    data[category].remove(key)
    if not data[category]:
        del data[category]
    _save_categories(vault_path, data)
    return data.get(category, [])


def list_categories(vault_path: str) -> Dict[str, List[str]]:
    """Return all categories and their members."""
    return _load_categories(vault_path)


def keys_in_category(vault_path: str, category: str) -> List[str]:
    """Return all keys assigned to *category*."""
    data = _load_categories(vault_path)
    if category not in data:
        raise CategoryError(f"category '{category}' does not exist")
    return list(data[category])
