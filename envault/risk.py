"""Risk assessment for vault secrets."""
import json
from pathlib import Path
from typing import Optional


class RiskError(Exception):
    pass


VALID_LEVELS = ("low", "medium", "high", "critical")


def _risk_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ".envault_risk.json"


def _load_risk(vault_path: str) -> dict:
    p = _risk_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_risk(vault_path: str, data: dict) -> None:
    _risk_path(vault_path).write_text(json.dumps(data, indent=2))


def set_risk(vault_path: str, key: str, level: str, reason: str = "") -> dict:
    """Assign a risk level to a secret key."""
    if level not in VALID_LEVELS:
        raise RiskError(f"Invalid risk level '{level}'. Must be one of {VALID_LEVELS}.")
    data = _load_risk(vault_path)
    entry = {"level": level, "reason": reason}
    data[key] = entry
    _save_risk(vault_path, data)
    return entry


def get_risk(vault_path: str, key: str) -> Optional[dict]:
    """Return the risk entry for a key, or None if not set."""
    return _load_risk(vault_path).get(key)


def remove_risk(vault_path: str, key: str) -> bool:
    """Remove risk assessment for a key. Returns True if removed."""
    data = _load_risk(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_risk(vault_path, data)
    return True


def list_risk(vault_path: str) -> dict:
    """Return all risk assessments."""
    return _load_risk(vault_path)
