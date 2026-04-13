"""CLI commands for visibility control."""

from __future__ import annotations

import click

from .visibility import (
    VISIBILITY_LEVELS,
    VisibilityError,
    get_visibility,
    list_visibility,
    remove_visibility,
    set_visibility,
)


@click.group("visibility")
def visibility_group() -> None:
    """Control the visibility of secrets (public / private / masked)."""


@visibility_group.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("level", type=click.Choice(VISIBILITY_LEVELS))
def set_cmd(vault_path: str, key: str, level: str) -> None:
    """Set the visibility LEVEL for KEY in VAULT_PATH."""
    try:
        entry = set_visibility(vault_path, key, level)
        click.echo(f"Set '{entry['key']}' visibility to '{entry['visibility']}'.")
    except VisibilityError as exc:
        raise click.ClickException(str(exc)) from exc


@visibility_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path: str, key: str) -> None:
    """Show the visibility level for KEY in VAULT_PATH."""
    level = get_visibility(vault_path, key)
    click.echo(f"{key}: {level}")


@visibility_group.command("remove")
@click.argument("vault_path")
@click.argument("key")
def remove_cmd(vault_path: str, key: str) -> None:
    """Remove explicit visibility setting for KEY (reverts to default 'private')."""
    removed = remove_visibility(vault_path, key)
    if removed:
        click.echo(f"Visibility setting removed for '{key}'.")
    else:
        click.echo(f"No explicit visibility setting found for '{key}'.")


@visibility_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path: str) -> None:
    """List all keys with an explicit visibility level in VAULT_PATH."""
    entries = list_visibility(vault_path)
    if not entries:
        click.echo("No explicit visibility settings found.")
        return
    for entry in entries:
        click.echo(f"{entry['key']}: {entry['visibility']}")
