"""Tests for envault.endorsement."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.endorsement import (
    endorse,
    revoke,
    get_endorsements,
    list_endorsed_keys,
    EndorsementError,
)
from envault.cli_endorsement import endorsement_group


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    vp = tmp_path / "vault.db"
    vp.write_text("{}")
    return str(vp)


class TestEndorse:
    def test_creates_endorsements_file(self, vault_path):
        endorse(vault_path, "MY_KEY", "alice")
        path = Path(vault_path).parent / ".envault" / "endorsements.json"
        assert path.exists()

    def test_returns_entry_dict(self, vault_path):
        entry = endorse(vault_path, "MY_KEY", "alice", note="looks good")
        assert entry["endorser"] == "alice"
        assert entry["note"] == "looks good"
        assert "endorsed_at" in entry

    def test_accumulates_endorsements(self, vault_path):
        endorse(vault_path, "MY_KEY", "alice")
        endorse(vault_path, "MY_KEY", "bob")
        entries = get_endorsements(vault_path, "MY_KEY")
        assert len(entries) == 2
        endorsers = {e["endorser"] for e in entries}
        assert endorsers == {"alice", "bob"}

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(EndorsementError):
            endorse(vault_path, "", "alice")

    def test_raises_on_empty_endorser(self, vault_path):
        with pytest.raises(EndorsementError):
            endorse(vault_path, "MY_KEY", "")

    def test_empty_note_allowed(self, vault_path):
        entry = endorse(vault_path, "MY_KEY", "alice")
        assert entry["note"] == ""


class TestRevoke:
    def test_removes_endorsement(self, vault_path):
        endorse(vault_path, "MY_KEY", "alice")
        count = revoke(vault_path, "MY_KEY", "alice")
        assert count == 1
        assert get_endorsements(vault_path, "MY_KEY") == []

    def test_removes_only_matching_endorser(self, vault_path):
        endorse(vault_path, "MY_KEY", "alice")
        endorse(vault_path, "MY_KEY", "bob")
        revoke(vault_path, "MY_KEY", "alice")
        remaining = get_endorsements(vault_path, "MY_KEY")
        assert len(remaining) == 1
        assert remaining[0]["endorser"] == "bob"

    def test_returns_zero_when_none_found(self, vault_path):
        count = revoke(vault_path, "MISSING", "alice")
        assert count == 0


class TestListEndorsedKeys:
    def test_returns_endorsed_keys(self, vault_path):
        endorse(vault_path, "KEY_A", "alice")
        endorse(vault_path, "KEY_B", "bob")
        keys = list_endorsed_keys(vault_path)
        assert set(keys) == {"KEY_A", "KEY_B"}

    def test_excludes_revoked_keys(self, vault_path):
        endorse(vault_path, "KEY_A", "alice")
        revoke(vault_path, "KEY_A", "alice")
        assert list_endorsed_keys(vault_path) == []

    def test_empty_when_no_endorsements(self, vault_path):
        assert list_endorsed_keys(vault_path) == []


class TestCliEndorsement:
    @pytest.fixture()
    def runner(self):
        return CliRunner()

    def _invoke(self, runner, vault_path, *args):
        return runner.invoke(endorsement_group, [*args, vault_path] if args[0] == "keys" else [args[0], vault_path, *args[1:]])

    def test_add_cmd_exits_zero(self, runner, vault_path):
        result = runner.invoke(endorsement_group, ["add", vault_path, "MY_KEY", "alice"])
        assert result.exit_code == 0

    def test_add_cmd_output_contains_key(self, runner, vault_path):
        result = runner.invoke(endorsement_group, ["add", vault_path, "MY_KEY", "alice"])
        assert "MY_KEY" in result.output

    def test_list_cmd_shows_endorser(self, runner, vault_path):
        runner.invoke(endorsement_group, ["add", vault_path, "MY_KEY", "alice", "--note", "ok"])
        result = runner.invoke(endorsement_group, ["list", vault_path, "MY_KEY"])
        assert "alice" in result.output

    def test_list_cmd_no_endorsements_message(self, runner, vault_path):
        result = runner.invoke(endorsement_group, ["list", vault_path, "MISSING"])
        assert "No endorsements" in result.output

    def test_keys_cmd_lists_keys(self, runner, vault_path):
        runner.invoke(endorsement_group, ["add", vault_path, "MY_KEY", "alice"])
        result = runner.invoke(endorsement_group, ["keys", vault_path])
        assert "MY_KEY" in result.output
