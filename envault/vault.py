"""Vault module for storing and retrieving encrypted environment variables."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import derive_key, generate_salt, encrypt, decrypt

DEFAULT_VAULT_FILE = ".envault"


class Vault:
    """Manages encrypted storage of environment variables."""

    def __init__(self, vault_path: str = DEFAULT_VAULT_FILE):
        self.vault_path = Path(vault_path)
        self._data: Dict = {}

    def _load_raw(self) -> Dict:
        """Load raw vault data from disk."""
        if not self.vault_path.exists():
            return {}
        with open(self.vault_path, "r") as f:
            return json.load(f)

    def _save_raw(self, data: Dict) -> None:
        """Persist raw vault data to disk."""
        with open(self.vault_path, "w") as f:
            json.dump(data, f, indent=2)

    def set(self, key: str, value: str, password: str) -> None:
        """Encrypt and store an environment variable."""
        salt = generate_salt()
        derived_key = derive_key(password, salt)
        ciphertext = encrypt(derived_key, value.encode())
        data = self._load_raw()
        data[key] = {
            "salt": salt.hex(),
            "ciphertext": ciphertext.hex(),
        }
        self._save_raw(data)

    def get(self, key: str, password: str) -> Optional[str]:
        """Retrieve and decrypt an environment variable."""
        data = self._load_raw()
        if key not in data:
            return None
        entry = data[key]
        salt = bytes.fromhex(entry["salt"])
        ciphertext = bytes.fromhex(entry["ciphertext"])
        derived_key = derive_key(password, salt)
        plaintext = decrypt(derived_key, ciphertext)
        return plaintext.decode()

    def delete(self, key: str) -> bool:
        """Remove an environment variable from the vault."""
        data = self._load_raw()
        if key not in data:
            return False
        del data[key]
        self._save_raw(data)
        return True

    def list_keys(self) -> list:
        """Return all stored variable names."""
        return list(self._load_raw().keys())

    def export(self, password: str) -> Dict[str, str]:
        """Decrypt and return all variables as a plain dict."""
        data = self._load_raw()
        result = {}
        for key in data:
            result[key] = self.get(key, password)
        return result
