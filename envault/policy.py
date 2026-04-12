"""Policy enforcement for vault secrets (required keys, value patterns, etc.)."""

import json
import re
from pathlib import Path
from typing import Any


class PolicyError(Exception):
    pass


def _policy_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_policies.json"


def _load_policies(vault_path: str) -> dict:
    p = _policy_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_policies(vault_path: str, data: dict) -> None:
    _policy_path(vault_path).write_text(json.dumps(data, indent=2))


def add_policy(vault_path: str, key: str, *, required: bool = False, pattern: str | None = None) -> dict:
    """Register a policy for a key."""
    policies = _load_policies(vault_path)
    entry: dict[str, Any] = {"required": required}
    if pattern is not None:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise PolicyError(f"Invalid regex pattern: {exc}") from exc
        entry["pattern"] = pattern
    policies[key] = entry
    _save_policies(vault_path, policies)
    return {"key": key, **entry}


def remove_policy(vault_path: str, key: str) -> None:
    """Remove the policy for a key."""
    policies = _load_policies(vault_path)
    if key not in policies:
        raise PolicyError(f"No policy found for key '{key}'")
    del policies[key]
    _save_policies(vault_path, policies)


def list_policies(vault_path: str) -> dict:
    """Return all registered policies."""
    return _load_policies(vault_path)


def enforce(vault_path: str, secrets: dict[str, str]) -> list[str]:
    """Check secrets against policies. Returns a list of violation messages."""
    policies = _load_policies(vault_path)
    violations: list[str] = []
    for key, rule in policies.items():
        if rule.get("required") and key not in secrets:
            violations.append(f"Required key '{key}' is missing.")
            continue
        if key in secrets and "pattern" in rule:
            if not re.fullmatch(rule["pattern"], secrets[key]):
                violations.append(
                    f"Key '{key}' value does not match pattern '{rule['pattern']}'."
                )
    return violations
