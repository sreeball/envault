import json
from pathlib import Path

INTENSITY_LEVELS = {"low", "medium", "high", "critical"}


class IntensityError(Exception):
    pass


def _intensity_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_intensity.json"


def _load_intensity(vault_path: str) -> dict:
    p = _intensity_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_intensity(vault_path: str, data: dict) -> None:
    _intensity_path(vault_path).write_text(json.dumps(data, indent=2))


def set_intensity(vault_path: str, key: str, level: str, note: str = "") -> dict:
    if level not in INTENSITY_LEVELS:
        raise IntensityError(f"Invalid level '{level}'. Must be one of {sorted(INTENSITY_LEVELS)}.")
    data = _load_intensity(vault_path)
    entry = {"level": level, "note": note}
    data[key] = entry
    _save_intensity(vault_path, data)
    return entry


def get_intensity(vault_path: str, key: str) -> dict:
    data = _load_intensity(vault_path)
    if key not in data:
        raise IntensityError(f"No intensity set for key '{key}'.")
    return data[key]


def remove_intensity(vault_path: str, key: str) -> None:
    data = _load_intensity(vault_path)
    if key not in data:
        raise IntensityError(f"No intensity set for key '{key}'.")
    del data[key]
    _save_intensity(vault_path, data)


def list_intensity(vault_path: str) -> dict:
    return _load_intensity(vault_path)
