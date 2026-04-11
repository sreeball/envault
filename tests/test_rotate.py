"""Tests for envault.rotate."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.rotate import rotate, RotationError


OLD_PASSWORD = "old-secret"
NEW_PASSWORD = "new-secret"


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    path = tmp_path / "vault.json"
    v = Vault(path, OLD_PASSWORD)
    v.set("API_KEY", "abc123")
    v.set("DB_URL", "postgres://localhost/db")
    return path


class TestRotate:
    def test_returns_secret_count(self, vault_path: Path) -> None:
        count = rotate(vault_path, OLD_PASSWORD, NEW_PASSWORD)
        assert count == 2

    def test_old_password_no_longer_works(self, vault_path: Path) -> None:
        rotate(vault_path, OLD_PASSWORD, NEW_PASSWORD)
        old_vault = Vault(vault_path, OLD_PASSWORD)
        # Decryption with old password should fail or return garbage.
        with pytest.raises(Exception):
            old_vault.get("API_KEY")

    def test_new_password_decrypts_all_secrets(self, vault_path: Path) -> None:
        rotate(vault_path, OLD_PASSWORD, NEW_PASSWORD)
        new_vault = Vault(vault_path, NEW_PASSWORD)
        assert new_vault.get("API_KEY") == "abc123"
        assert new_vault.get("DB_URL") == "postgres://localhost/db"

    def test_salts_are_refreshed(self, vault_path: Path) -> None:
        before = json.loads(vault_path.read_text())
        rotate(vault_path, OLD_PASSWORD, NEW_PASSWORD)
        after = json.loads(vault_path.read_text())
        for key in ("API_KEY", "DB_URL"):
            assert before[key]["salt"] != after[key]["salt"], (
                f"Salt for '{key}' should be refreshed after rotation"
            )

    def test_wrong_old_password_raises_rotation_error(self, vault_path: Path) -> None:
        with pytest.raises(RotationError):
            rotate(vault_path, "wrong-password", NEW_PASSWORD)

    def test_empty_vault_rotates_zero_secrets(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.json"
        Vault(path, OLD_PASSWORD)  # creates empty vault file
        count = rotate(path, OLD_PASSWORD, NEW_PASSWORD)
        assert count == 0

    def test_audit_log_entry_created(self, vault_path: Path) -> None:
        from envault.audit import get_log
        rotate(vault_path, OLD_PASSWORD, NEW_PASSWORD)
        log = get_log(vault_path)
        assert any(entry["action"] == "rotate" for entry in log)
