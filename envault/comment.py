"""Per-key comments/annotations for vault secrets."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class CommentError(Exception):
    pass


def _comments_path(vault_path: str) -> Path:
    p = Path(vault_path)
    return p.parent / (p.stem + ".comments.json")


def _load_comments(vault_path: str) -> Dict[str, List[str]]:
    cp = _comments_path(vault_path)
    if not cp.exists():
        return {}
    with cp.open() as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise CommentError(f"Failed to parse comments file '{cp}': {e}") from e


def _save_comments(vault_path: str, data: Dict[str, List[str]]) -> None:
    cp = _comments_path(vault_path)
    with cp.open("w") as f:
        json.dump(data, f, indent=2)


def add_comment(vault_path: str, key: str, comment: str) -> List[str]:
    """Append a comment to the given key. Returns updated comment list."""
    if not comment.strip():
        raise CommentError("Comment must not be empty.")
    data = _load_comments(vault_path)
    data.setdefault(key, []).append(comment.strip())
    _save_comments(vault_path, data)
    return data[key]


def get_comments(vault_path: str, key: str) -> List[str]:
    """Return all comments for a key."""
    data = _load_comments(vault_path)
    return data.get(key, [])


def remove_comments(vault_path: str, key: str) -> None:
    """Remove all comments for a key."""
    data = _load_comments(vault_path)
    if key not in data:
        raise CommentError(f"No comments found for key: {key}")
    del data[key]
    _save_comments(vault_path, data)


def list_commented_keys(vault_path: str) -> Dict[str, List[str]]:
    """Return a mapping of all keys that have comments."""
    return dict(_load_comments(vault_path))
