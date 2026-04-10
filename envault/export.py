"""Export vault secrets to various shell-compatible formats."""

from __future__ import annotations

from typing import Dict, Literal

ExportFormat = Literal["dotenv", "shell", "json"]


def export_dotenv(secrets: Dict[str, str]) -> str:
    """Export secrets as a .env file format.

    Args:
        secrets: Mapping of key -> plaintext value.

    Returns:
        A string with KEY=VALUE lines suitable for a .env file.
    """
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_shell(secrets: Dict[str, str]) -> str:
    """Export secrets as shell export statements.

    Args:
        secrets: Mapping of key -> plaintext value.

    Returns:
        A string with `export KEY=VALUE` lines.
    """
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_json(secrets: Dict[str, str]) -> str:
    """Export secrets as a JSON object.

    Args:
        secrets: Mapping of key -> plaintext value.

    Returns:
        A pretty-printed JSON string.
    """
    import json

    return json.dumps(secrets, indent=2, sort_keys=True) + "\n"


def export_secrets(secrets: Dict[str, str], fmt: ExportFormat = "dotenv") -> str:
    """Dispatch export to the requested format.

    Args:
        secrets: Mapping of key -> plaintext value.
        fmt: One of 'dotenv', 'shell', or 'json'.

    Returns:
        Formatted string.

    Raises:
        ValueError: If *fmt* is not a recognised format.
    """
    formatters = {
        "dotenv": export_dotenv,
        "shell": export_shell,
        "json": export_json,
    }
    if fmt not in formatters:
        raise ValueError(f"Unknown export format '{fmt}'. Choose from: {', '.join(formatters)}.")
    return formatters[fmt](secrets)
