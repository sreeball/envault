"""Tests for envault.sharing."""
import time
import pytest
from pathlib import Path

from envault.sharing import (
    SharingError,
    share_key,
    redeem_share,
    revoke_share,
    list_shares,
    _shares_path,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "vault.json"


PASSWORD = "shared-secret-pw"


class TestShareKey:
    def test_creates_shares_file(self, vault_path):
        share_key(vault_path, "DB_URL", "postgres://localhost", "alice", PASSWORD)
        assert _shares_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = share_key(vault_path, "DB_URL", "postgres://localhost", "alice", PASSWORD)
        assert entry["recipient"] == "alice"
        assert "salt" in entry
        assert "ciphertext" in entry
        assert "expires_at" in entry

    def test_expires_at_in_future(self, vault_path):
        entry = share_key(vault_path, "K", "v", "bob", PASSWORD, ttl_seconds=3600)
        assert entry["expires_at"] > time.time()

    def test_accumulates_multiple_recipients(self, vault_path):
        share_key(vault_path, "K", "v", "alice", PASSWORD)
        share_key(vault_path, "K", "v", "bob", PASSWORD)
        shares = list_shares(vault_path)
        assert len(shares["K"]) == 2

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(SharingError, match="key"):
            share_key(vault_path, "", "v", "alice", PASSWORD)

    def test_raises_on_empty_recipient(self, vault_path):
        with pytest.raises(SharingError, match="recipient"):
            share_key(vault_path, "K", "v", "", PASSWORD)

    def test_raises_on_non_positive_ttl(self, vault_path):
        with pytest.raises(SharingError, match="ttl_seconds"):
            share_key(vault_path, "K", "v", "alice", PASSWORD, ttl_seconds=0)


class TestRedeemShare:
    def test_decrypts_correct_value(self, vault_path):
        share_key(vault_path, "API_KEY", "my-secret", "alice", PASSWORD)
        result = redeem_share(vault_path, "API_KEY", "alice", PASSWORD)
        assert result == "my-secret"

    def test_raises_on_wrong_password(self, vault_path):
        share_key(vault_path, "K", "v", "alice", PASSWORD)
        with pytest.raises(SharingError):
            redeem_share(vault_path, "K", "alice", "wrong-password")

    def test_raises_on_wrong_recipient(self, vault_path):
        share_key(vault_path, "K", "v", "alice", PASSWORD)
        with pytest.raises(SharingError, match="no active share"):
            redeem_share(vault_path, "K", "bob", PASSWORD)

    def test_raises_when_expired(self, vault_path):
        share_key(vault_path, "K", "v", "alice", PASSWORD, ttl_seconds=1)
        # Manually expire the entry
        import json
        p = _shares_path(vault_path)
        data = json.loads(p.read_text())
        data["K"][0]["expires_at"] = time.time() - 1
        p.write_text(json.dumps(data))
        with pytest.raises(SharingError, match="expired"):
            redeem_share(vault_path, "K", "alice", PASSWORD)

    def test_raises_when_no_shares(self, vault_path):
        with pytest.raises(SharingError, match="no active share"):
            redeem_share(vault_path, "MISSING", "alice", PASSWORD)


class TestRevokeShare:
    def test_removes_recipient_entry(self, vault_path):
        share_key(vault_path, "K", "v", "alice", PASSWORD)
        share_key(vault_path, "K", "v", "bob", PASSWORD)
        removed = revoke_share(vault_path, "K", "alice")
        assert removed == 1
        shares = list_shares(vault_path)
        recipients = [e["recipient"] for e in shares.get("K", [])]
        assert "alice" not in recipients
        assert "bob" in recipients

    def test_removes_key_when_no_shares_left(self, vault_path):
        share_key(vault_path, "K", "v", "alice", PASSWORD)
        revoke_share(vault_path, "K", "alice")
        assert "K" not in list_shares(vault_path)

    def test_returns_zero_when_not_found(self, vault_path):
        removed = revoke_share(vault_path, "MISSING", "alice")
        assert removed == 0
