"""Tests for envault.profiles."""

import json
from pathlib import Path

import pytest

from envault.profiles import (
    ProfileError,
    assign_key,
    create_profile,
    delete_profile,
    get_profile_secrets,
    list_profiles,
    remove_key,
    _profiles_path,
)
from envault.vault import Vault


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    path = tmp_path / "vault.json"
    v = Vault(path, "s3cret")
    v.set("DB_URL", "postgres://localhost/mydb")
    v.set("API_KEY", "abc123")
    v.set("DEBUG", "true")
    return path


class TestCreateProfile:
    def test_creates_profiles_file(self, vault_path):
        create_profile(vault_path, "dev")
        assert _profiles_path(vault_path).exists()

    def test_returns_profile_dict(self, vault_path):
        result = create_profile(vault_path, "dev")
        assert "dev" in result
        assert result["dev"] == []

    def test_raises_on_duplicate(self, vault_path):
        create_profile(vault_path, "dev")
        with pytest.raises(ProfileError, match="already exists"):
            create_profile(vault_path, "dev")

    def test_multiple_profiles(self, vault_path):
        create_profile(vault_path, "dev")
        create_profile(vault_path, "prod")
        assert set(list_profiles(vault_path)) == {"dev", "prod"}


class TestAssignKey:
    def test_adds_key_to_profile(self, vault_path):
        create_profile(vault_path, "dev")
        keys = assign_key(vault_path, "dev", "DB_URL")
        assert "DB_URL" in keys

    def test_idempotent(self, vault_path):
        create_profile(vault_path, "dev")
        assign_key(vault_path, "dev", "DB_URL")
        keys = assign_key(vault_path, "dev", "DB_URL")
        assert keys.count("DB_URL") == 1

    def test_raises_for_missing_profile(self, vault_path):
        with pytest.raises(ProfileError, match="does not exist"):
            assign_key(vault_path, "ghost", "DB_URL")


class TestRemoveKey:
    def test_removes_key(self, vault_path):
        create_profile(vault_path, "dev")
        assign_key(vault_path, "dev", "DB_URL")
        keys = remove_key(vault_path, "dev", "DB_URL")
        assert "DB_URL" not in keys

    def test_noop_if_key_absent(self, vault_path):
        create_profile(vault_path, "dev")
        keys = remove_key(vault_path, "dev", "NONEXISTENT")
        assert keys == []


class TestGetProfileSecrets:
    def test_decrypts_assigned_keys(self, vault_path):
        create_profile(vault_path, "dev")
        assign_key(vault_path, "dev", "DB_URL")
        assign_key(vault_path, "dev", "API_KEY")
        secrets = get_profile_secrets(vault_path, "dev", "s3cret")
        assert secrets["DB_URL"] == "postgres://localhost/mydb"
        assert secrets["API_KEY"] == "abc123"

    def test_skips_deleted_vault_keys(self, vault_path):
        create_profile(vault_path, "dev")
        assign_key(vault_path, "dev", "GONE")
        secrets = get_profile_secrets(vault_path, "dev", "s3cret")
        assert "GONE" not in secrets

    def test_raises_for_missing_profile(self, vault_path):
        with pytest.raises(ProfileError):
            get_profile_secrets(vault_path, "nope", "s3cret")


class TestDeleteProfile:
    def test_removes_profile(self, vault_path):
        create_profile(vault_path, "dev")
        delete_profile(vault_path, "dev")
        assert "dev" not in list_profiles(vault_path)

    def test_raises_for_missing_profile(self, vault_path):
        with pytest.raises(ProfileError):
            delete_profile(vault_path, "ghost")
