"""Key rotation: re-encrypt all vault secrets under a new master password."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from envault.crypto import derive_key, generate_salt, encrypt, decrypt
from envault.vault import Vault
from envault.audit import record


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate(vault_path: "Path", old_password: str, new_password: str) -> int:
    """Re-encrypt every secret in *vault_path* using *new_password*.

    Returns the number of secrets that were rotated.
    Raises RotationError if the old password cannot decrypt any entry.
    """
    vault = Vault(vault_path, old_password)

    # Verify we can read all keys before writing anything.
    try:
        keys = vault.list()
        plaintext_values: dict[str, str] = {}
        for key in keys:
            value = vault.get(key)
            if value is None:
                raise RotationError(f"Could not decrypt key '{key}' with the provided old password.")
            plaintext_values[key] = value
    except Exception as exc:
        raise RotationError(f"Rotation aborted — could not read vault: {exc}") from exc

    # Load raw data so we can rewrite entries in place.
    raw = vault._load_raw()

    new_key = derive_key(new_password, generate_salt())  # derive once for validation
    # Each secret gets its own fresh salt for forward secrecy.
    for secret_key, plaintext in plaintext_values.items():
        salt = generate_salt()
        derived = derive_key(new_password, salt)
        ciphertext = encrypt(derived, plaintext)
        raw[secret_key] = {
            "salt": salt.hex(),
            "ciphertext": ciphertext.hex(),
        }

    vault._save_raw(raw)

    count = len(plaintext_values)
    record(vault_path, "rotate", f"Rotated {count} secret(s) to new master password")
    return count
