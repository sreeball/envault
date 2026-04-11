"""Access control: restrict which keys a given identity can read or write."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class AccessError(Exception):
    """Raised when an access-control operation fails."""


def _access_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".access.json")


def _load_acl(vault_path: str) -> Dict[str, Dict[str, List[str]]]:
    p = _access_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_acl(vault_path: str, acl: Dict[str, Dict[str, List[str]]]) -> None:
    _access_path(vault_path).write_text(json.dumps(acl, indent=2))


def grant(vault_path: str, identity: str, key: str, permission: str = "read") -> Dict:
    """Grant *identity* the given *permission* (read|write) on *key*."""
    if permission not in ("read", "write"):
        raise AccessError(f"Invalid permission '{permission}'; choose 'read' or 'write'.")
    acl = _load_acl(vault_path)
    entry = acl.setdefault(identity, {"read": [], "write": []})
    if key not in entry[permission]:
        entry[permission].append(key)
    _save_acl(vault_path, acl)
    return {"identity": identity, "key": key, "permission": permission}


def revoke(vault_path: str, identity: str, key: str, permission: str = "read") -> Dict:
    """Revoke *identity*'s *permission* on *key*."""
    if permission not in ("read", "write"):
        raise AccessError(f"Invalid permission '{permission}'; choose 'read' or 'write'.")
    acl = _load_acl(vault_path)
    entry = acl.get(identity, {})
    keys = entry.get(permission, [])
    if key not in keys:
        raise AccessError(f"Identity '{identity}' has no {permission} permission on '{key}'.")
    keys.remove(key)
    _save_acl(vault_path, acl)
    return {"identity": identity, "key": key, "permission": permission}


def can(vault_path: str, identity: str, key: str, permission: str = "read") -> bool:
    """Return True if *identity* holds *permission* on *key*."""
    acl = _load_acl(vault_path)
    return key in acl.get(identity, {}).get(permission, [])


def list_permissions(vault_path: str, identity: Optional[str] = None) -> Dict:
    """Return the full ACL, or only the entry for *identity*."""
    acl = _load_acl(vault_path)
    if identity is not None:
        return {identity: acl.get(identity, {"read": [], "write": []})}
    return acl
