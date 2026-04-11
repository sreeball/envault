"""Profile management: named groups of secrets (e.g. dev, staging, prod)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def _profiles_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".profiles.json")


def _load_profiles(vault_path: Path) -> Dict[str, List[str]]:
    path = _profiles_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_profiles(vault_path: Path, data: Dict[str, List[str]]) -> None:
    _profiles_path(vault_path).write_text(json.dumps(data, indent=2))


def create_profile(vault_path: Path, profile: str) -> Dict[str, List[str]]:
    """Create an empty profile. Raises ProfileError if it already exists."""
    data = _load_profiles(vault_path)
    if profile in data:
        raise ProfileError(f"Profile '{profile}' already exists.")
    data[profile] = []
    _save_profiles(vault_path, data)
    return data


def assign_key(vault_path: Path, profile: str, key: str) -> List[str]:
    """Assign a vault key to a profile. Returns updated key list."""
    data = _load_profiles(vault_path)
    if profile not in data:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    if key not in data[profile]:
        data[profile].append(key)
        _save_profiles(vault_path, data)
    return data[profile]


def remove_key(vault_path: Path, profile: str, key: str) -> List[str]:
    """Remove a key from a profile. Returns updated key list."""
    data = _load_profiles(vault_path)
    if profile not in data:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    if key in data[profile]:
        data[profile].remove(key)
        _save_profiles(vault_path, data)
    return data[profile]


def list_profiles(vault_path: Path) -> List[str]:
    """Return all profile names."""
    return list(_load_profiles(vault_path).keys())


def get_profile_secrets(
    vault_path: Path, profile: str, password: str
) -> Dict[str, str]:
    """Decrypt and return all secrets belonging to a profile."""
    data = _load_profiles(vault_path)
    if profile not in data:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    vault = Vault(vault_path, password)
    result: Dict[str, str] = {}
    for key in data[profile]:
        try:
            result[key] = vault.get(key)
        except KeyError:
            pass  # key was deleted from vault but still referenced
    return result


def delete_profile(vault_path: Path, profile: str) -> None:
    """Delete a profile entirely."""
    data = _load_profiles(vault_path)
    if profile not in data:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    del data[profile]
    _save_profiles(vault_path, data)
