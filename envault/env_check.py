"""Check vault secrets against the current environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from envault.vault import Vault


class EnvCheckError(Exception):
    """Raised when an env-check operation fails."""


@dataclass
class CheckResult:
    missing: List[str] = field(default_factory=list)
    present: List[str] = field(default_factory=list)
    mismatched: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.mismatched

    def summary(self) -> str:
        lines = []
        for key in self.present:
            lines.append(f"  [ok]       {key}")
        for key in self.missing:
            lines.append(f"  [missing]  {key}")
        for key in self.mismatched:
            lines.append(f"  [mismatch] {key}")
        return "\n".join(lines)


def check_env(
    vault_path: str,
    password: str,
    *,
    compare_values: bool = False,
) -> CheckResult:
    """Compare vault keys (and optionally values) against os.environ.

    Parameters
    ----------
    vault_path:
        Path to the vault file.
    password:
        Master password used to decrypt the vault.
    compare_values:
        When True, also check that the environment value matches the
        decrypted vault value; mismatches are recorded separately.

    Returns
    -------
    CheckResult
        Dataclass with *missing*, *present*, and *mismatched* key lists.
    """
    vault = Vault(vault_path, password)
    keys = vault.keys()

    if not keys:
        return CheckResult()

    result = CheckResult()
    for key in keys:
        env_val = os.environ.get(key)
        if env_val is None:
            result.missing.append(key)
        elif compare_values:
            vault_val = vault.get(key)
            if vault_val != env_val:
                result.mismatched.append(key)
            else:
                result.present.append(key)
        else:
            result.present.append(key)

    return result
