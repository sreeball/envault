"""Lint vault secrets for common issues: weak values, naming conventions, expiry."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from envault.vault import Vault
from envault.ttl import get_ttl, TTLError


class LintError(Exception):
    pass


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning' | 'info'
    message: str


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


_NAMING_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_WEAK_VALUES = {"password", "secret", "changeme", "12345", "admin", "test", ""}
_MIN_SECRET_LEN = 8


def _check_naming(key: str) -> LintIssue | None:
    if not _NAMING_RE.match(key):
        return LintIssue(key, "warning", f"Key '{key}' does not follow UPPER_SNAKE_CASE convention")
    return None


def _check_value(key: str, value: str) -> LintIssue | None:
    if value.strip().lower() in _WEAK_VALUES:
        return LintIssue(key, "error", f"Key '{key}' has a weak or empty value")
    if len(value) < _MIN_SECRET_LEN:
        return LintIssue(key, "warning", f"Key '{key}' value is shorter than {_MIN_SECRET_LEN} characters")
    return None


def _check_ttl(vault_path: str, key: str) -> LintIssue | None:
    try:
        entry = get_ttl(vault_path, key)
        if entry.get("expired"):
            return LintIssue(key, "error", f"Key '{key}' has an expired TTL")
    except TTLError:
        pass
    return None


def lint_vault(vault_path: str, password: str) -> LintResult:
    """Run all lint checks on every secret in the vault."""
    vault = Vault(vault_path, password)
    keys = vault.list()
    if not keys:
        return LintResult()

    result = LintResult()
    for key in keys:
        value = vault.get(key)

        for check in (_check_naming(key), _check_value(key, value), _check_ttl(vault_path, key)):
            if check is not None:
                result.issues.append(check)

    return result
