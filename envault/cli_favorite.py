"""CLI commands for managing favorite vault keys."""

from __future__ import annotations

import click

from .cli import get_vault
from .favorite import FavoriteError, add_favorite, is_favorite, list_favorites, remove_favorite


@click.group("favorite")
def favorite_group() -> None:
    """Manage favorite keys."""


@favorite_group.command("add")
@click.argument("vault_path")
@click.argument("key")
@click.option("--note", default="", help="Optional note for this favorite.")
def add_cmd(vault_path: str, key: str, note: str) -> None:
    """Mark KEY as a favorite in VAULT_PATH."""
    try:
        entry = add_favorite(vault_path, key, note=note)
        click.echo(f"Added '{entry['key']}' to favorites.")
        if entry["note"]:
            click.echo(f"Note: {entry['note']}")
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc)) from exc


@favorite_group.command("remove")
@click.argument("vault_path")
@click.argument("key")
def remove_cmd(vault_path: str, key: str) -> None:
    """Remove KEY from favorites."""
    try:
        remove_favorite(vault_path, key)
        click.echo(f"Removed '{key}' from favorites.")
    except FavoriteError as exc:
        raise click.ClickException(str(exc)) from exc


@favorite_group.command("list")
@click.argument("vault_path")
@click.option("--notes-only", is_flag=True, default=False, help="Only show favorites that have a note.")
def list_cmd(vault_path: str, notes_only: bool) -> None:
    """List all favorite keys in VAULT_PATH."""
    favs = list_favorites(vault_path)
    if notes_only:
        favs = [entry for entry in favs if entry.get("note")]
    if not favs:
        click.echo("No favorites set.")
        return
    for entry in favs:
        line = entry["key"]
        if entry.get("note"):
            line += f"  # {entry['note']}"
        click.echo(line)


@favorite_group.command("check")
@click.argument("vault_path")
@click.argument("key")
def check_cmd(vault_path: str, key: str) -> None:
    """Check whether KEY is a favorite."""
    if is_favorite(vault_path, key):
        click.echo(f"'{key}' is a favorite.")
    else:
        click.echo(f"'{key}' is NOT a favorite.")
