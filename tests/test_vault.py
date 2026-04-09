"""Tests for the Vault module."""

import json
import pytest
from pathlib import Path

from envault.vault import Vault

PASSWORD = "supersecret"


@pytest.fixture
def vault(tmp_path):
    vault_file = tmp_path / ".envault"
    return Vault(vault_path=str(vault_file))


class TestVaultSet:
    def test_creates_vault_file(self, vault, tmp_path):
        vault.set("API_KEY", "abc123", PASSWORD)
        assert (tmp_path / ".envault").exists()

    def test_stores_encrypted_value(self, vault, tmp_path):
        vault.set("API_KEY", "abc123", PASSWORD)
        raw = json.loads((tmp_path / ".envault").read_text())
        assert "API_KEY" in raw
        assert raw["API_KEY"]["ciphertext"] != "abc123"

    def test_stores_salt_and_ciphertext(self, vault):
        vault.set("DB_URL", "postgres://localhost", PASSWORD)
        raw = vault._load_raw()
        assert "salt" in raw["DB_URL"]
        assert "ciphertext" in raw["DB_URL"]


class TestVaultGet:
    def test_retrieves_correct_value(self, vault):
        vault.set("SECRET", "myvalue", PASSWORD)
        assert vault.get("SECRET", PASSWORD) == "myvalue"

    def test_returns_none_for_missing_key(self, vault):
        assert vault.get("NONEXISTENT", PASSWORD) is None

    def test_wrong_password_raises(self, vault):
        vault.set("TOKEN", "tokenvalue", PASSWORD)
        with pytest.raises(Exception):
            vault.get("TOKEN", "wrongpassword")


class TestVaultDelete:
    def test_deletes_existing_key(self, vault):
        vault.set("TEMP_KEY", "tempval", PASSWORD)
        result = vault.delete("TEMP_KEY")
        assert result is True
        assert vault.get("TEMP_KEY", PASSWORD) is None

    def test_returns_false_for_missing_key(self, vault):
        assert vault.delete("DOES_NOT_EXIST") is False


class TestVaultListKeys:
    def test_empty_vault(self, vault):
        assert vault.list_keys() == []

    def test_lists_stored_keys(self, vault):
        vault.set("KEY_A", "val_a", PASSWORD)
        vault.set("KEY_B", "val_b", PASSWORD)
        keys = vault.list_keys()
        assert "KEY_A" in keys
        assert "KEY_B" in keys


class TestVaultExport:
    def test_export_returns_all_decrypted(self, vault):
        vault.set("VAR1", "value1", PASSWORD)
        vault.set("VAR2", "value2", PASSWORD)
        exported = vault.export(PASSWORD)
        assert exported == {"VAR1": "value1", "VAR2": "value2"}
