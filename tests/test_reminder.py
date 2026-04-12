"""Tests for envault.reminder."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from envault.reminder import (
    ReminderError,
    add_reminder,
    due_reminders,
    list_reminders,
    mark_fired,
    remove_reminder,
    _reminders_path,
)


@pytest.fixture()
def vault_path(tmp_path):
    p = tmp_path / "vault.enc"
    p.touch()
    return str(p)


class TestAddReminder:
    def test_creates_reminders_file(self, vault_path):
        add_reminder(vault_path, "DB_PASS", "rotate this", days=7)
        assert _reminders_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = add_reminder(vault_path, "API_KEY", "review", days=30)
        assert entry["key"] == "API_KEY"
        assert entry["message"] == "review"
        assert entry["fired"] is False
        assert "due_at" in entry
        assert "created_at" in entry

    def test_due_at_is_in_the_future(self, vault_path):
        entry = add_reminder(vault_path, "X", "msg", days=5)
        due = datetime.fromisoformat(entry["due_at"])
        assert due > datetime.utcnow()

    def test_raises_on_zero_days(self, vault_path):
        with pytest.raises(ReminderError, match="positive"):
            add_reminder(vault_path, "X", "msg", days=0)

    def test_raises_on_negative_days(self, vault_path):
        with pytest.raises(ReminderError):
            add_reminder(vault_path, "X", "msg", days=-1)

    def test_raises_on_empty_key(self, vault_path):
        with pytest.raises(ReminderError, match="empty"):
            add_reminder(vault_path, "", "msg", days=1)

    def test_overwrites_existing_reminder(self, vault_path):
        add_reminder(vault_path, "K", "first", days=1)
        add_reminder(vault_path, "K", "second", days=2)
        reminders = list_reminders(vault_path)
        assert len(reminders) == 1
        assert reminders[0]["message"] == "second"


class TestListReminders:
    def test_empty_when_no_file(self, vault_path):
        assert list_reminders(vault_path) == []

    def test_returns_all_entries(self, vault_path):
        add_reminder(vault_path, "A", "a", days=1)
        add_reminder(vault_path, "B", "b", days=2)
        keys = {r["key"] for r in list_reminders(vault_path)}
        assert keys == {"A", "B"}


class TestRemoveReminder:
    def test_removes_entry(self, vault_path):
        add_reminder(vault_path, "DEL", "bye", days=1)
        remove_reminder(vault_path, "DEL")
        assert list_reminders(vault_path) == []

    def test_raises_if_not_found(self, vault_path):
        with pytest.raises(ReminderError, match="No reminder"):
            remove_reminder(vault_path, "GHOST")


class TestDueReminders:
    def test_no_due_when_future(self, vault_path):
        add_reminder(vault_path, "FUTURE", "later", days=10)
        assert due_reminders(vault_path) == []

    def test_detects_overdue_entry(self, vault_path):
        add_reminder(vault_path, "PAST", "overdue", days=1)
        # Manually backdate the due_at
        p = _reminders_path(vault_path)
        data = json.loads(p.read_text())
        data["PAST"]["due_at"] = "2000-01-01T00:00:00"
        p.write_text(json.dumps(data))
        assert len(due_reminders(vault_path)) == 1

    def test_fired_reminders_excluded(self, vault_path):
        add_reminder(vault_path, "OLD", "done", days=1)
        p = _reminders_path(vault_path)
        data = json.loads(p.read_text())
        data["OLD"]["due_at"] = "2000-01-01T00:00:00"
        data["OLD"]["fired"] = True
        p.write_text(json.dumps(data))
        assert due_reminders(vault_path) == []


class TestMarkFired:
    def test_sets_fired_true(self, vault_path):
        add_reminder(vault_path, "Z", "fire me", days=1)
        entry = mark_fired(vault_path, "Z")
        assert entry["fired"] is True

    def test_raises_if_not_found(self, vault_path):
        with pytest.raises(ReminderError):
            mark_fired(vault_path, "MISSING")
