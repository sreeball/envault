import pytest
from pathlib import Path
from envault.intensity import (
    set_intensity,
    get_intensity,
    remove_intensity,
    list_intensity,
    IntensityError,
    _intensity_path,
)


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.db")


class TestSetIntensity:
    def test_creates_intensity_file(self, vault_path):
        set_intensity(vault_path, "DB_PASS", "high")
        assert _intensity_path(vault_path).exists()

    def test_returns_entry_dict(self, vault_path):
        entry = set_intensity(vault_path, "DB_PASS", "high")
        assert entry["level"] == "high"
        assert entry["note"] == ""

    def test_stores_level_in_file(self, vault_path):
        set_intensity(vault_path, "API_KEY", "critical", note="very sensitive")
        entry = get_intensity(vault_path, "API_KEY")
        assert entry["level"] == "critical"
        assert entry["note"] == "very sensitive"

    def test_raises_on_invalid_level(self, vault_path):
        with pytest.raises(IntensityError, match="Invalid level"):
            set_intensity(vault_path, "KEY", "extreme")

    def test_all_valid_levels_accepted(self, vault_path):
        for level in ("low", "medium", "high", "critical"):
            entry = set_intensity(vault_path, f"KEY_{level}", level)
            assert entry["level"] == level

    def test_overwrites_existing(self, vault_path):
        set_intensity(vault_path, "DB_PASS", "low")
        set_intensity(vault_path, "DB_PASS", "critical")
        entry = get_intensity(vault_path, "DB_PASS")
        assert entry["level"] == "critical"


class TestGetIntensity:
    def test_raises_when_key_missing(self, vault_path):
        with pytest.raises(IntensityError, match="No intensity set"):
            get_intensity(vault_path, "MISSING")


class TestRemoveIntensity:
    def test_removes_entry(self, vault_path):
        set_intensity(vault_path, "KEY", "medium")
        remove_intensity(vault_path, "KEY")
        assert "KEY" not in list_intensity(vault_path)

    def test_raises_when_key_missing(self, vault_path):
        with pytest.raises(IntensityError, match="No intensity set"):
            remove_intensity(vault_path, "GHOST")


class TestListIntensity:
    def test_empty_when_no_file(self, vault_path):
        assert list_intensity(vault_path) == {}

    def test_returns_all_entries(self, vault_path):
        set_intensity(vault_path, "A", "low")
        set_intensity(vault_path, "B", "high")
        data = list_intensity(vault_path)
        assert set(data.keys()) == {"A", "B"}
