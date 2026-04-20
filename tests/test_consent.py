"""Tests for envault.consent."""
import pytest
from pathlib import Path
from envault.consent import (
    ConsentError,
    grant_consent,
    revoke_consent,
    get_consents,
    has_consent,
    list_all_consents,
    _consent_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    p = tmp_path / "vault.db"
    p.touch()
    return str(p)


class TestGrantConsent:
    def test_creates_consent_file(self, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        assert _consent_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = grant_consent(vault_path, "API_KEY", "alice", "analytics")
        assert entry["actor"] == "alice"
        assert entry["purpose"] == "analytics"

    def test_empty_note_allowed(self, vault_path):
        entry = grant_consent(vault_path, "API_KEY", "alice", "analytics")
        assert entry["note"] == ""

    def test_custom_note_stored(self, vault_path):
        entry = grant_consent(vault_path, "API_KEY", "alice", "analytics", note="GDPR")
        assert entry["note"] == "GDPR"

    def test_accumulates_entries(self, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        grant_consent(vault_path, "API_KEY", "bob", "reporting")
        consents = get_consents(vault_path, "API_KEY")
        assert len(consents) == 2

    def test_deduplicates_same_actor_and_purpose(self, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics", note="first")
        grant_consent(vault_path, "API_KEY", "alice", "analytics", note="second")
        consents = get_consents(vault_path, "API_KEY")
        assert len(consents) == 1
        assert consents[0]["note"] == "second"

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(ConsentError):
            grant_consent(vault_path, "", "alice", "analytics")

    def test_raises_on_empty_actor(self, vault_path):
        with pytest.raises(ConsentError):
            grant_consent(vault_path, "API_KEY", "", "analytics")

    def test_raises_on_empty_purpose(self, vault_path):
        with pytest.raises(ConsentError):
            grant_consent(vault_path, "API_KEY", "alice", "")


class TestRevokeConsent:
    def test_removes_specific_actor_and_purpose(self, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        removed = revoke_consent(vault_path, "API_KEY", "alice", "analytics")
        assert removed == 1
        assert not has_consent(vault_path, "API_KEY", "alice", "analytics")

    def test_removes_all_entries_for_actor_when_no_purpose(self, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        grant_consent(vault_path, "API_KEY", "alice", "reporting")
        removed = revoke_consent(vault_path, "API_KEY", "alice")
        assert removed == 2

    def test_returns_zero_when_key_missing(self, vault_path):
        assert revoke_consent(vault_path, "MISSING", "alice") == 0

    def test_cleans_up_empty_key_entry(self, vault_path):
        grant_consent(vault_path, "API_KEY", "alice", "analytics")
        revoke_consent(vault_path, "API_KEY", "alice")
        assert list_all_consents(vault_path) == {}


class TestHasConsent:
    def test_true_when_granted(self, vault_path):
        grant_consent(vault_path, "DB_PASS", "carol", "backup")
        assert has_consent(vault_path, "DB_PASS", "carol", "backup") is True

    def test_false_when_not_granted(self, vault_path):
        assert has_consent(vault_path, "DB_PASS", "carol", "backup") is False

    def test_false_after_revoke(self, vault_path):
        grant_consent(vault_path, "DB_PASS", "carol", "backup")
        revoke_consent(vault_path, "DB_PASS", "carol", "backup")
        assert has_consent(vault_path, "DB_PASS", "carol", "backup") is False
